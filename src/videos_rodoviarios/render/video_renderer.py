from __future__ import annotations

import math
import urllib.request
from collections import OrderedDict
from pathlib import Path
from typing import Callable

import imageio_ffmpeg
from PIL import Image, ImageDraw, ImageFont
from pyproj import CRS, Transformer
from shapely.geometry import LineString

from videos_rodoviarios.core.models import GeometryEntity, RoadAnalysis
from videos_rodoviarios.geometry.stationing import format_station

Progress = Callable[[float, str], None]
TILE_SIZE = 256
ESRI_URL = "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"


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
    crs = CRS.from_dict({"proj": "utm", "zone": ctx.utm_zone, "south": south, "datum": "WGS84", "units": "m"})
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
    def __init__(self, max_items: int = 256):
        self.max_items = max_items
        self.cache: OrderedDict[tuple[int, int, int], Image.Image] = OrderedDict()

    def get(self, z: int, x: int, y: int) -> Image.Image:
        key = (z, x, y)
        if key in self.cache:
            image = self.cache.pop(key)
            self.cache[key] = image
            return image
        image = self._download(z, x, y)
        self.cache[key] = image
        while len(self.cache) > self.max_items:
            self.cache.popitem(last=False)
        return image

    def _download(self, z: int, x: int, y: int) -> Image.Image:
        n = 2**z
        x %= n
        if y < 0 or y >= n:
            return Image.new("RGB", (TILE_SIZE, TILE_SIZE), (60, 65, 70))
        url = ESRI_URL.format(z=z, x=x, y=y)
        request = urllib.request.Request(url, headers={"User-Agent": "VideosRodoviarios/1.0"})
        try:
            with urllib.request.urlopen(request, timeout=12) as response:
                from io import BytesIO

                return Image.open(BytesIO(response.read())).convert("RGB")
        except Exception:
            return Image.new("RGB", (TILE_SIZE, TILE_SIZE), (72, 78, 82))


def _find_centerline(analysis: RoadAnalysis) -> GeometryEntity:
    if analysis.main_centerline_handle:
        for entity in analysis.entities:
            if entity.handle == analysis.main_centerline_handle:
                return entity
    return max(analysis.entities, key=lambda e: LineString(e.points).length if len(e.points) >= 2 else 0.0)


def _sample_line(points: list[tuple[float, float]], count: int) -> list[tuple[float, float]]:
    line = LineString(points)
    if line.length <= 0:
        return [points[0]] * count
    return [(line.interpolate(line.length * i / max(1, count - 1)).x, line.interpolate(line.length * i / max(1, count - 1)).y) for i in range(count)]


def _tangent(points: list[tuple[float, float]], idx: int) -> tuple[float, float]:
    a = points[max(0, idx - 1)]
    b = points[min(len(points) - 1, idx + 1)]
    dx, dy = b[0] - a[0], b[1] - a[1]
    length = math.hypot(dx, dy) or 1.0
    return dx / length, dy / length


def _entity_world_points(entity: GeometryEntity, transformer: Transformer | None, zoom: int) -> list[tuple[float, float]]:
    if transformer is None:
        return entity.points
    out = []
    for x, y in entity.points:
        lon, lat = transformer.transform(x, y)
        out.append(_lonlat_to_world_px(lon, lat, zoom))
    return out


def _local_to_world(points: list[tuple[float, float]], transformer: Transformer | None, zoom: int) -> list[tuple[float, float]]:
    if transformer is None:
        # Fallback keeps geometry usable without imagery/georeference.
        scale = 0.8
        return [(x * scale, -y * scale) for x, y in points]
    out = []
    for x, y in points:
        lon, lat = transformer.transform(x, y)
        out.append(_lonlat_to_world_px(lon, lat, zoom))
    return out


def _background(cache: TileCache, cx: float, cy: float, width: int, height: int, zoom: int, imagery: bool) -> Image.Image:
    if not imagery:
        return Image.new("RGB", (width, height), (47, 54, 58))
    left = cx - width / 2
    top = cy - height / 2
    tx0, ty0 = _world_px_to_tile(left, top)
    tx1, ty1 = _world_px_to_tile(cx + width / 2, cy + height / 2)
    canvas = Image.new("RGB", (width, height), (60, 65, 70))
    for ty in range(ty0, ty1 + 1):
        for tx in range(tx0, tx1 + 1):
            tile = cache.get(zoom, tx, ty)
            px = int(tx * TILE_SIZE - left)
            py = int(ty * TILE_SIZE - top)
            canvas.paste(tile, (px, py))
    return canvas


def _draw_polyline(draw: ImageDraw.ImageDraw, pts: list[tuple[float, float]], cx: float, cy: float, width: int, height: int, fill, line_width: int):
    screen = [(x - cx + width / 2, y - cy + height / 2) for x, y in pts]
    if len(screen) >= 2:
        draw.line(screen, fill=fill, width=line_width, joint="curve")


def _draw_scene(frame: Image.Image, analysis: RoadAnalysis, center_world: tuple[float, float], world_entities: list[tuple[GeometryEntity, list[tuple[float, float]]]], world_texts: list[tuple[str, float, float]], road_world: list[tuple[float, float]], idx: int, route_samples: list[tuple[float, float]], width: int, height: int):
    draw = ImageDraw.Draw(frame, "RGBA")
    cx, cy = center_world

    # Dim imagery slightly so engineering overlays stay legible.
    draw.rectangle((0, 0, width, height), fill=(0, 0, 0, 34))

    # Designed pavement first.
    _draw_polyline(draw, road_world, cx, cy, width, height, (48, 50, 53, 235), 34)
    _draw_polyline(draw, road_world, cx, cy, width, height, (90, 93, 96, 235), 26)

    palette = {
        "cut": ((220, 54, 48, 230), 5),
        "fill": ((45, 170, 78, 230), 5),
        "marking": ((255, 255, 255, 245), 3),
        "edge": ((245, 245, 245, 220), 3),
        "domain": ((255, 196, 0, 215), 3),
        "water": ((30, 144, 255, 220), 4),
        "rail": ((200, 200, 200, 220), 3),
        "oae": ((255, 144, 38, 230), 6),
        "center": ((255, 214, 0, 210), 2),
    }
    for entity, pts in world_entities:
        style = palette.get(entity.category)
        if style:
            _draw_polyline(draw, pts, cx, cy, width, height, style[0], style[1])

    # Lane center marking to improve road realism when no dedicated layer is present.
    _draw_polyline(draw, road_world, cx, cy, width, height, (255, 232, 0, 220), 2)

    # Moving traffic: multiple vehicles, both directions, kept on route.
    vehicle_font = _font(13, True)
    for j, phase in enumerate((0.05, 0.22, 0.42, 0.63, 0.82)):
        pos = (idx / max(1, len(route_samples) - 1) + phase) % 1.0
        vi = min(len(route_samples) - 1, int(pos * (len(route_samples) - 1)))
        vx, vy = route_samples[vi]
        sx, sy = vx - cx + width / 2, vy - cy + height / 2
        if -30 <= sx <= width + 30 and -30 <= sy <= height + 30:
            color = (244, 244, 244, 245) if j % 2 == 0 else (35, 110, 205, 245)
            draw.rounded_rectangle((sx - 8, sy - 4, sx + 8, sy + 4), radius=3, fill=color, outline=(20, 20, 20, 220), width=1)
            if j == 0:
                draw.text((sx + 11, sy - 8), "fluxo", font=vehicle_font, fill=(255, 255, 255, 220))

    # Stable callouts near the route; actual text coordinates become anchors.
    label_font = _font(17, True)
    small_font = _font(14)
    occupied: list[tuple[int, int, int, int]] = []
    shown = 0
    for text, wx, wy in world_texts:
        sx, sy = wx - cx + width / 2, wy - cy + height / 2
        if not (80 <= sx <= width - 80 and 90 <= sy <= height - 80):
            continue
        if shown >= 6:
            break
        label = text.strip().replace("\\P", " ")[:44]
        if len(label) < 3:
            continue
        bx = int(min(width - 280, max(12, sx + (38 if sx < width / 2 else -260))))
        by = int(min(height - 70, max(72, sy - 28)))
        rect = (bx, by, bx + 250, by + 48)
        if any(not (rect[2] < r[0] or rect[0] > r[2] or rect[3] < r[1] or rect[1] > r[3]) for r in occupied):
            continue
        occupied.append(rect)
        anchor_x = bx if bx > sx else bx + 250
        anchor_y = by + 24
        draw.line((sx, sy, anchor_x, anchor_y), fill=(255, 255, 255, 225), width=2)
        draw.ellipse((sx - 3, sy - 3, sx + 3, sy + 3), fill=(255, 214, 0, 255))
        draw.rounded_rectangle(rect, radius=7, fill=(15, 22, 28, 220), outline=(255, 255, 255, 170), width=1)
        draw.text((bx + 10, by + 7), label, font=small_font, fill=(255, 255, 255, 255))
        shown += 1

    # Executive header and progress.
    draw.rectangle((0, 0, width, 64), fill=(9, 17, 24, 232))
    title_font = _font(24, True)
    subtitle_font = _font(15)
    km0 = format_station(analysis.km_start_m) or "início"
    km1 = format_station(analysis.km_end_m) or "fim"
    draw.text((22, 10), "VÍDEOS RODOVIÁRIOS · APRESENTAÇÃO TÉCNICA", font=title_font, fill=(255, 255, 255, 255))
    draw.text((22, 39), f"{km0} → {km1}  |  extensão {analysis.extension_m / 1000:.3f} km", font=subtitle_font, fill=(210, 220, 228, 255))
    progress = idx / max(1, len(route_samples) - 1)
    draw.rectangle((0, height - 9, width, height), fill=(10, 15, 20, 220))
    draw.rectangle((0, height - 9, int(width * progress), height), fill=(255, 205, 40, 245))


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
    if width % 2:
        width += 1
    if height % 2:
        height += 1

    center = _find_centerline(analysis)
    transformer = _utm_transformer(analysis)
    if imagery and transformer is None:
        imagery = False
        if progress:
            progress(0.01, "KMZ sem referência UTM suficiente; usando fundo técnico.")

    center_world = _local_to_world(center.points, transformer, zoom)
    world_entities = [(entity, _entity_world_points(entity, transformer, zoom) if transformer else _local_to_world(entity.points, None, zoom)) for entity in analysis.entities]
    world_texts = []
    for text in analysis.texts:
        if transformer:
            lon, lat = transformer.transform(text.x, text.y)
            wx, wy = _lonlat_to_world_px(lon, lat, zoom)
        else:
            wx, wy = text.x * 0.8, -text.y * 0.8
        world_texts.append((text.text, wx, wy))

    total_frames = max(48, int(fps * duration_s))
    route_samples = _sample_line(center_world, total_frames)
    cache = TileCache()
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    cmd = [
        ffmpeg,
        "-y",
        "-f",
        "rawvideo",
        "-vcodec",
        "rawvideo",
        "-pix_fmt",
        "rgb24",
        "-s",
        f"{width}x{height}",
        "-r",
        str(fps),
        "-i",
        "-",
        "-an",
        "-c:v",
        "libx264",
        "-preset",
        "medium",
        "-crf",
        "19",
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        str(output),
    ]

    import subprocess

    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    assert proc.stdin is not None
    try:
        for i, (cx, cy) in enumerate(route_samples):
            frame = _background(cache, cx, cy, width, height, zoom, imagery)
            _draw_scene(frame, analysis, (cx, cy), world_entities, world_texts, center_world, i, route_samples, width, height)
            proc.stdin.write(frame.tobytes())
            if progress and (i % max(1, fps // 2) == 0 or i == total_frames - 1):
                progress((i + 1) / total_frames, f"Renderizando vídeo: {int((i + 1) * 100 / total_frames)}%")
        proc.stdin.close()
        code = proc.wait()
        if code != 0:
            err = proc.stderr.read().decode("utf-8", errors="ignore") if proc.stderr else ""
            raise RuntimeError(f"FFmpeg falhou ao gerar o MP4. {err[-1200:]}")
    except Exception:
        try:
            proc.kill()
        except Exception:
            pass
        raise
    if progress:
        progress(1.0, f"Vídeo concluído: {output.name}")
    return output
