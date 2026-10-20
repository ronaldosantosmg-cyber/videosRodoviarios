from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Callable

from videos_rodoviarios.core.models import RoadAnalysis

Progress = Callable[[float, str], None]


def _runtime_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[3]


def _find_unreal_executable() -> Path:
    configured = os.environ.get("VIDEOS_RODOVIARIOS_UNREAL_EXE", "").strip()
    if configured:
        candidate = Path(configured)
        if candidate.exists():
            return candidate

    root = os.environ.get("UNREAL_ENGINE_ROOT", "").strip()
    if root:
        candidate = Path(root) / "Engine" / "Binaries" / "Win64" / "UnrealEditor-Cmd.exe"
        if candidate.exists():
            return candidate

    program_files = Path(os.environ.get("ProgramFiles", r"C:\Program Files"))
    epic = program_files / "Epic Games"
    if epic.exists():
        candidates = sorted(epic.glob("UE_*/Engine/Binaries/Win64/UnrealEditor-Cmd.exe"), reverse=True)
        if candidates:
            return candidates[0]

    raise RuntimeError(
        "Unreal Engine não encontrado. Instale/configure o Unreal Engine ou defina "
        "VIDEOS_RODOVIARIOS_UNREAL_EXE apontando para UnrealEditor-Cmd.exe."
    )


def _find_project() -> Path:
    configured = os.environ.get("VIDEOS_RODOVIARIOS_UNREAL_PROJECT", "").strip()
    if configured:
        candidate = Path(configured)
        if candidate.exists():
            return candidate

    candidates = [
        _runtime_root() / "unreal" / "VideosRodoviarios.uproject",
        Path(__file__).resolve().parents[3] / "unreal" / "VideosRodoviarios.uproject",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate

    raise RuntimeError(
        "Projeto Unreal/Cesium não encontrado. O pacote deve conter unreal/VideosRodoviarios.uproject."
    )


def _write_job(
    analysis: RoadAnalysis,
    output: Path,
    *,
    width: int,
    height: int,
    fps: int,
    duration_s: int,
    zoom: int,
    imagery: bool,
) -> Path:
    job = output.with_suffix(".unreal-job.json")
    payload = {
        "schema": 1,
        "analysis": analysis.to_dict(),
        "video": {
            "output": str(output.resolve()),
            "width": int(width),
            "height": int(height),
            "fps": int(fps),
            "duration_s": int(duration_s),
            "zoom": int(zoom),
            "imagery": bool(imagery),
        },
    }
    job.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return job


def render_video(
    analysis: RoadAnalysis,
    output_path: str | Path,
    *,
    width: int = 1280,
    height: int = 720,
    fps: int = 24,
    duration_s: int = 45,
    zoom: int = 17,
    imagery: bool = True,
    progress: Progress | None = None,
) -> Path:
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    if progress:
        progress(0.03, "Preparando cena Unreal/Cesium...")

    unreal_exe = _find_unreal_executable()
    project = _find_project()
    script = project.parent / "Scripts" / "render_scene.py"
    if not script.exists():
        raise RuntimeError(f"Script de automação Unreal não encontrado: {script}")

    job = _write_job(
        analysis,
        output,
        width=width,
        height=height,
        fps=fps,
        duration_s=duration_s,
        zoom=zoom,
        imagery=imagery,
    )

    if progress:
        progress(0.10, "Iniciando Unreal/Cesium...")

    env = os.environ.copy()
    env["VIDEOS_RODOVIARIOS_JOB"] = str(job.resolve())
    command = [
        str(unreal_exe),
        str(project),
        "-Unattended",
        "-NoSplash",
        "-NoSound",
        f"-ExecutePythonScript={script}",
    ]

    process = subprocess.Popen(
        command,
        cwd=str(project.parent),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    assert process.stdout is not None
    for line in process.stdout:
        text = line.strip()
        if text.startswith("VR_PROGRESS:") and progress:
            try:
                _, raw_fraction, message = text.split(":", 2)
                progress(max(0.10, min(0.98, float(raw_fraction))), message.strip())
            except Exception:
                pass

    return_code = process.wait()
    if return_code != 0:
        raise RuntimeError(f"Unreal Engine encerrou com código {return_code}.")

    if not output.exists() or output.stat().st_size < 1000:
        raise RuntimeError("O Unreal/Cesium não produziu um MP4 válido.")

    if progress:
        progress(1.0, f"Vídeo Unreal/Cesium concluído: {output.name}")
    return output
