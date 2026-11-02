from __future__ import annotations

import os
from pathlib import Path
from typing import Callable

from videos_rodoviarios.core.models import RoadAnalysis
from videos_rodoviarios.render.final_renderer import render_video as render_legacy
from videos_rodoviarios.render.unreal_renderer import is_available as unreal_available
from videos_rodoviarios.render.unreal_renderer import render_video as render_unreal

Progress = Callable[[float, str], None]


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
    """Seleciona o motor de vídeo sem alterar a interface pública do aplicativo.

    VIDEO_RODOVIARIO_RENDERER:
      - unreal: exige Unreal/Cesium configurado e falha claramente se ausente.
      - legacy: força o renderer Python/FFmpeg anterior.
      - auto (padrão): prioriza Unreal e usa legacy somente se a instalação ainda não estiver pronta.
    """
    mode = os.environ.get("VIDEO_RODOVIARIO_RENDERER", "auto").strip().lower()
    common = dict(
        width=width,
        height=height,
        fps=fps,
        duration_s=duration_s,
        zoom=zoom,
        imagery=imagery,
        progress=progress,
    )

    if mode not in {"auto", "unreal", "legacy"}:
        raise RuntimeError(
            "VIDEO_RODOVIARIO_RENDERER deve ser 'auto', 'unreal' ou 'legacy'."
        )

    if mode == "legacy":
        if progress:
            progress(0.0, "Motor compatível Python/FFmpeg selecionado.")
        return render_legacy(analysis, output_path, **common)

    available, detail = unreal_available()
    if available:
        if progress:
            progress(0.0, f"Motor Unreal/Cesium selecionado. {detail}")
        return render_unreal(analysis, output_path, **common)

    if mode == "unreal":
        raise RuntimeError(detail)

    if progress:
        progress(
            0.0,
            "Unreal/Cesium ainda não está disponível nesta máquina; "
            f"usando compatibilidade temporária. {detail}",
        )
    return render_legacy(analysis, output_path, **common)
