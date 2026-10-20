from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Callable

from videos_rodoviarios.core.models import RoadAnalysis

Progress = Callable[[float, str], None]


def _find_unreal_editor() -> Path | None:
    explicit = os.environ.get("VIDEO_RODOVIARIO_UNREAL_EXE")
    if explicit:
        path = Path(explicit).expanduser()
        if path.exists():
            return path

    for name in ("UnrealEditor-Cmd.exe", "UnrealEditor.exe"):
        found = shutil.which(name)
        if found:
            return Path(found)

    roots = [
        Path(os.environ.get("PROGRAMFILES", r"C:\Program Files")) / "Epic Games",
        Path(os.environ.get("PROGRAMFILES(X86)", r"C:\Program Files (x86)")) / "Epic Games",
    ]
    candidates: list[Path] = []
    for root in roots:
        if not root.exists():
            continue
        for engine in root.glob("UE_5.*"):
            for binary in (
                engine / "Engine/Binaries/Win64/UnrealEditor-Cmd.exe",
                engine / "Engine/Binaries/Win64/UnrealEditor.exe",
            ):
                if binary.exists():
                    candidates.append(binary)
    return sorted(candidates, reverse=True)[0] if candidates else None


def _project_path() -> Path | None:
    explicit = os.environ.get("VIDEO_RODOVIARIO_UNREAL_PROJECT")
    if explicit:
        path = Path(explicit).expanduser()
        if path.exists():
            return path

    here = Path(__file__).resolve()
    candidates = [
        here.parents[3] / "unreal" / "VideoRodoviario.uproject",
        here.parents[2] / "unreal" / "VideoRodoviario.uproject",
        Path.cwd() / "unreal" / "VideoRodoviario.uproject",
    ]
    return next((p for p in candidates if p.exists()), None)


def _script_path(project: Path) -> Path:
    explicit = os.environ.get("VIDEO_RODOVIARIO_UNREAL_SCRIPT")
    if explicit:
        return Path(explicit).expanduser()
    return project.parent / "Content" / "Python" / "render_road_video.py"


def _write_manifest(
    analysis: RoadAnalysis,
    output: Path,
    *,
    width: int,
    height: int,
    fps: int,
    duration_s: int,
    imagery: bool,
) -> Path:
    payload = {
        "schema": 1,
        "output": str(output.resolve()),
        "video": {
            "width": int(width),
            "height": int(height),
            "fps": int(fps),
            "duration_s": int(duration_s),
            "imagery": bool(imagery),
        },
        "road": analysis.to_dict(),
    }
    cache_dir = Path(tempfile.gettempdir()) / "videos_rodoviarios" / "unreal"
    cache_dir.mkdir(parents=True, exist_ok=True)
    manifest = cache_dir / "render_manifest.json"
    manifest.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest


def is_available() -> tuple[bool, str]:
    editor = _find_unreal_editor()
    if editor is None:
        return False, "Unreal Engine 5 não encontrado."
    project = _project_path()
    if project is None:
        return False, "Projeto Unreal VideoRodoviario.uproject não encontrado."
    script = _script_path(project)
    if not script.exists():
        return False, f"Script Unreal não encontrado: {script}"
    return True, f"Unreal disponível: {editor}"


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
    del zoom  # O Unreal/Cesium controla LOD dinamicamente.
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    editor = _find_unreal_editor()
    project = _project_path()
    if editor is None or project is None:
        missing = "Unreal Engine 5" if editor is None else "projeto Unreal"
        raise RuntimeError(
            f"Backend Unreal selecionado, mas {missing} não foi encontrado. "
            "Defina VIDEO_RODOVIARIO_UNREAL_EXE e VIDEO_RODOVIARIO_UNREAL_PROJECT."
        )
    script = _script_path(project)
    if not script.exists():
        raise RuntimeError(f"Script de renderização Unreal ausente: {script}")

    if progress:
        progress(0.03, "Preparando cena Unreal/Cesium…")
    manifest = _write_manifest(
        analysis,
        output,
        width=width,
        height=height,
        fps=fps,
        duration_s=duration_s,
        imagery=imagery,
    )

    env = os.environ.copy()
    env["VIDEO_RODOVIARIO_MANIFEST"] = str(manifest)
    cmd = [
        str(editor),
        str(project),
        "-Unattended",
        "-NoSplash",
        "-NoSound",
        "-RenderOffscreen",
        f'-ExecutePythonScript="{script}"',
    ]
    if progress:
        progress(0.08, "Unreal iniciado; construindo geometria e terreno…")

    completed = subprocess.run(
        cmd,
        env=env,
        cwd=str(project.parent),
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        tail = (completed.stderr or completed.stdout or "")[-4000:]
        raise RuntimeError(f"Unreal encerrou com código {completed.returncode}.\n{tail}")

    if not output.exists() or output.stat().st_size < 1000:
        raise RuntimeError("O Unreal terminou, mas não produziu um MP4 válido.")
    if progress:
        progress(1.0, f"Vídeo Unreal concluído: {output.name}")
    return output
