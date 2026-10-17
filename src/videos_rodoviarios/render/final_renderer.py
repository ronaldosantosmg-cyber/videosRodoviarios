from __future__ import annotations

from pathlib import Path
from typing import Callable

import imageio_ffmpeg

from videos_rodoviarios.core.models import RoadAnalysis
from videos_rodoviarios.render.video_renderer import (
    TileCache,
    _background,
    _draw_scene,
    _entity_world_points,
    _find_centerline,
    _local_to_world,
    _lonlat_to_world_px,
    _sample_line,
    _utm_transformer,
)

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
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    width += width % 2
    height += height % 2

    center = _find_centerline(analysis)
    transformer = _utm_transformer(analysis)
    if imagery and transformer is None:
        imagery = False
        if progress:
            progress(0.01, "Sem georreferenciamento UTM confiável; usando fundo técnico.")

    center_world = _local_to_world(center.points, transformer, zoom)
    world_entities = [
        (
            entity,
            _entity_world_points(entity, transformer, zoom)
            if transformer
            else _local_to_world(entity.points, None, zoom),
        )
        for entity in analysis.entities
    ]
    world_texts: list[tuple[str, float, float]] = []
    for text in analysis.texts:
        if transformer:
            lon, lat = transformer.transform(text.x, text.y)
            wx, wy = _lonlat_to_world_px(lon, lat, zoom)
        else:
            wx, wy = text.x * 0.8, -text.y * 0.8
        world_texts.append((text.text, wx, wy))

    total_frames = max(2, int(fps * duration_s))
    route_samples = _sample_line(center_world, total_frames)
    cache = TileCache()

    writer = imageio_ffmpeg.write_frames(
        str(output),
        (width, height),
        pix_fmt_in="rgb24",
        pix_fmt_out="yuv420p",
        fps=fps,
        codec="libx264",
        quality=7,
        macro_block_size=2,
        ffmpeg_log_level="error",
        output_params=["-movflags", "+faststart"],
    )
    writer.send(None)
    try:
        for index, (cx, cy) in enumerate(route_samples):
            frame = _background(cache, cx, cy, width, height, zoom, imagery)
            _draw_scene(
                frame,
                analysis,
                (cx, cy),
                world_entities,
                world_texts,
                center_world,
                index,
                route_samples,
                width,
                height,
            )
            writer.send(frame.tobytes())
            if progress and (index % max(1, fps // 2) == 0 or index == total_frames - 1):
                fraction = (index + 1) / total_frames
                progress(fraction, f"Renderizando vídeo: {int(fraction * 100)}%")
    finally:
        writer.close()

    if not output.exists() or output.stat().st_size < 1000:
        raise RuntimeError("O codificador não produziu um MP4 válido.")
    if progress:
        progress(1.0, f"Vídeo concluído: {output.name}")
    return output
