from __future__ import annotations

import math
import os
import urllib.request
from io import BytesIO
from pathlib import Path
from typing import Callable

import imageio_ffmpeg
from PIL import Image, ImageDraw, ImageFont
from pyproj import CRS, Transformer
from shapely.geometry import LineString

from videos_rodoviarios.core.models import GeometryEntity, RoadAnalysis
from videos_rodoviarios.geometry.stationing import format_station
from videos_rodoviarios.paths import SUPPORT_DIR

Progress = Callable[[float, str], None]
TILE_SIZE = 256

QMS_PROVIDERS: dict[str, str] = {
    "esri_world_imagery": "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
    "osm_standard": "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
    "carto_light": "https://a.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png",
}
DEFAULT_PROVIDER = "esri_world_imagery"


def _font(size: int, bold: bool = False):
    candidates = [
        "C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _utm_transformer(analysis: RoadAnalysis) -> Transformer | None:
    ctx = analysis.kml_context
    if not ctx or not ctx.utm_zone or not ctx.hemisphere:
        return None
    south = ctx.hemisphere.lower().startswith("s")
    crs = CRS.from_dict(
        {"proj": "utm", "zone": ctx.utm_zone, "south": south, "datum": "WGS84", "units": "m"}
    )
    return Transformer.from_crs(crs, "EPSG:4326", always_xy=True)


def _lonlat_to_world_px(lon: float, lat: float, zoom: int) -> tuple[float, float]:
    lat = max(-85.05112878, min(85.05112878, lat))
    scale = TILE_SIZE * (2**zoom)
    x = (lon + 180.0) / 360.0 * scale
    sin_lat = math.sin(math.radians(lat))
    y = (0.5 - math.log((1 + sin_lat) / (1 - sin_lat)) / (4 * math.pi)) * scale
    return x, y


def _world_px_to_tile(x: float, y: float) -> tuple[int, int]:
    return int(math.floor(x / TILE_SIZE)), int(math.floor(y / TILE_SIZE))


class TileCache:
    """Cache de tiles XYZ em memória e em disco para render repetível e rápido."""

    def __init__(self, provider: str | None = None):
        requested = provider or os.environ.get("VIDEOS_RODOVIARIOS_TILE_PROVIDER", DEFAULT_PROVIDER)
        self.provider = requested if requested in QMS_PROVIDERS else DEFAULT_PROVIDER
        self.url_template = QMS_PROVIDERS[self.provider]
        self.memory: dict[tuple[int, int, int], Image.Image] = {}
        self.root = SUPPORT_DIR / "cache_tiles" / self.provider
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, z: int, x: int, y: int) -> Path:
        return self.root / str(z) / str(x) / f"{y}.jpg"

    def get(self, z: int, x: int, y: int) -> Image.Image:
        n = 2**z
        x %= n
        if y < 0 or y >= n:
            return Image.new("RGB", (TILE_SIZE, TILE_SIZE), (64, 69, 73))
        key = (z, x, y)
        if key in self.memory:
            return self.memory[key]

        path = self._path(z, x, y)
        if path.exists():
            try:
                image = Image.open(path).convert("RGB")
                self.memory[key] = image
                return image
            except OSError:
                path.unlink(missing_ok=True)

        url = self.url_template.format(z=z, x=x, y=y)
        request = urllib.request.Request(
            url,
            headers={"User-Agent": "VideosRodoviarios/REV02 (+portable-road-renderer)"},
        )
        try:
            with urllib.request.urlopen(request, timeout=15) as response:
                image = Image.open(BytesIO(response.read())).convert("RGB")
            if image.size != (TILE_SIZE, TILE_SIZE):
                image = image.resize((TILE_SIZE, TILE_SIZE), Image.Resampling.LANCZOS)
            path.parent.mkdir(parents=True, exist_ok=True)
            image.save(path, "JPEG", quality=92, subsampling=0)
        except Exception:
            image = Image.new("RGB", (TILE_SIZE, TILE_SIZE), (72, 78, 82))
        self.memory[key] = image
        if len(self.memory) > 512:
            self.memory.pop(next(iter(self.memory)))
        return image


def _background(
    cache: TileCache,
    cx: float,
    cy: float,
    width: int,
    height: int,
    zoom: int,
    imagery: bool,
) -> Image.Image:
    """Gera fundo contínuo em um único mosaico, evitando linhas entre tiles."""
    if not imagery:
        return Image.new("RGB", (width, height), (47, 54, 58))

    left = cx - width / 2
    top = cy - height / 2
    right = cx + width / 2
    bottom = cy + height / 2

    tx0, ty0 = _world_px_to_tile(left, top)
    tx1, ty1 = _world_px_to_tile(right, bottom)
    cols = tx1 - tx0 + 1
    rows = ty1 - ty0 + 1
    mosaic = Image.new("RGB", (cols * TILE_SIZE, rows * TILE_SIZE), (60, 65, 70))

    for row, ty in enumerate(range(ty0, ty1 + 1)):
        for col, tx in enumerate(range(tx0, tx1 + 1)):
            tile = cache.get(zoom, tx, ty)
            mosaic.paste(tile, (col * TILE_SIZE, row * TILE_SIZE))

    origin_x = tx0 * TILE_SIZE
    origin_y = ty0 * TILE_SIZE
    offset_x = left - origin_x
    offset_y = top - origin_y
    pad = 2
    crop_box = (
        max(0, int(math.floor(offset_x)) - pad),
        max(0, int(math.floor(offset_y)) - pad),
        min(mosaic.width, int(math.ceil(offset_x + width)) + pad),
        min(mosaic.height, int(math.ceil(offset_y + height)) + pad),
    )
    cropped = mosaic.crop(crop_box)
    target_w = width + 2 * pad
    target_h = height + 2 * pad
    if cropped.size != (target_w, target_h):
        cropped = cropped.resize((target_w, target_h), Image.Resampling.BICUBIC)
    return cropped.crop((pad, pad, pad + width, pad + height))


def _find_centerline(analysis: RoadAnalysis) -> GeometryEntity:
    if analysis.main_centerline_handle:
        for entity in analysis.entities:
            if entity.handle == analysis.main_centerline_handle:
                return entity
    return max(
        analysis.entities,
        key=lambda e: LineString(e.points).length if len(e.points) >= 2 else 0.0,
    )


def _sample_line(points: list[tuple[float, float]], count: int) -> list[tuple[float, float]]:
    line = LineString(points)
    if line.length <= 0:
        return [points[0]] * count
    return [
        (
            line.interpolate(line.length * i / max(1, count - 1)).x,
            line.interpolate(line.length * i / max(1, count - 1)).y,
        )
        for i in range(count)
    ]


def _to_world(
    points: list[tuple[float, float]], transformer: Transformer | None, zoom: int
) -> list[tuple[float, float]]:
    if transformer is None:
        return [(x * 0.8, -y * 0.8) for x, y in points]
    out: list[tuple[float, float]] = []
    for x, y in points:
        lon, lat = transformer.transform(x, y)
        out.append(_lonlat_to_world_px(lon, lat, zoom))
    return out


def _draw_polyline(
    draw: ImageDraw.ImageDraw,
    pts: list[tuple[float, float]],
    cx: float,
    cy: float,
    width: int,
    height: int,
    fill,
    line_width: int,
) -> None:
    screen = [(x - cx + width / 2, y - cy + height / 2) for x, y in pts]
    if len(screen) >= 2:
        draw.line(screen, fill=fill, width=line_width, joint="curve")


def _draw_scene(
    frame: Image.Image,
    analysis: RoadAnalysis,
    center: tuple[float, float],
    world_entities: list[tuple[GeometryEntity, list[tuple[float, float]]]],
    road_world: list[tuple[float, float]],
    frame_index: int,
    total_frames: int,
) -> None:
    width, height = frame.size
    cx, cy = center
    draw = ImageDraw.Draw(frame, "RGBA")
    draw.rectangle((0, 0, width, height), fill=(0, 0, 0, 24))

    _draw_polyline(draw, road_world, cx, cy, width, height, (55, 57, 60, 235), 34)
    _draw_polyline(draw, road_world, cx, cy, width, height, (95, 98, 101, 235), 26)

    palette = {
        "cut": ((224, 82, 76, 225), 5),
        "fill": ((88, 190, 112, 225), 5),
        "marking": ((255, 255, 255, 245), 3),
        "edge": ((250, 250, 250, 235), 3),
        "domain": ((255, 202, 56, 220), 3),
        "water": ((62, 157, 230, 220), 4),
        "rail": ((210, 210, 210, 220), 3),
        "oae": ((255, 153, 58, 230), 6),
        "center": ((255, 224, 72, 225), 2),
    }
    for entity, pts in world_entities:
        style = palette.get(entity.category)
        if style:
            _draw_polyline(draw, pts, cx, cy, width, height, style[0], style[1])

    _draw_polyline(draw, road_world, cx, cy, width, height, (255, 232, 0, 225), 2)

    draw.rectangle((0, 0, width, 64), fill=(9, 17, 24, 226))
    title_font = _font(24, True)
    subtitle_font = _font(15)
    km0 = format_station(analysis.km_start_m) or "início"
    km1 = format_station(analysis.km_end_m) or "fim"
    draw.text((22, 10), "VÍDEOS RODOVIÁRIOS · REV02", font=title_font, fill=(255, 255, 255, 255))
    draw.text(
        (22, 39),
        f"{km0} → {km1}  |  extensão {analysis.extension_m / 1000:.3f} km  |  fundo QMS",
        font=subtitle_font,
        fill=(215, 224, 231, 255),
    )
    progress = frame_index / max(1, total_frames - 1)
    draw.rectangle((0, height - 8, width, height), fill=(10, 15, 20, 220))
    draw.rectangle((0, height - 8, int(width * progress), height), fill=(255, 205, 40, 245))


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

    centerline = _find_centerline(analysis)
    transformer = _utm_transformer(analysis)
    if imagery and transformer is None:
        imagery = False
        if progress:
            progress(0.01, "Sem referência UTM suficiente; usando fundo técnico.")

    center_world = _to_world(centerline.points, transformer, zoom)
    world_entities = [
        (entity, _to_world(entity.points, transformer, zoom))
        for entity in analysis.entities
        if getattr(entity, "visible_in_output", True)
    ]

    total_frames = max(2, int(fps * duration_s))
    route_samples = _sample_line(center_world, total_frames)
    cache = TileCache()
    if progress and imagery:
        progress(0.01, f"Fundo QMS: {cache.provider}; cache local e mosaico contínuo ativos.")

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
        for i, (cx, cy) in enumerate(route_samples):
            frame = _background(cache, cx, cy, width, height, zoom, imagery)
            _draw_scene(frame, analysis, (cx, cy), world_entities, center_world, i, total_frames)
            writer.send(frame.tobytes())
            if progress and (i % max(1, fps // 2) == 0 or i == total_frames - 1):
                progress(
                    (i + 1) / total_frames,
                    f"Renderizando vídeo: {int((i + 1) * 100 / total_frames)}%",
                )
    finally:
        writer.close()

    if not output.exists() or output.stat().st_size < 1000:
        raise RuntimeError("O codificador não produziu um MP4 válido.")
    if progress:
        progress(1.0, f"Vídeo concluído: {output.name}")
    return output
