from __future__ import annotations

from html import escape
from pathlib import Path

from videos_rodoviarios.core.models import RoadAnalysis

COLORS = {"center": "#f59e0b", "edge": "#475569", "cut": "#ef4444", "fill": "#22c55e", "marking": "#f8fafc", "domain": "#06b6d4", "water": "#3b82f6", "rail": "#111827", "oae": "#a855f7", "other": "#94a3b8"}


def write_svg_preview(analysis: RoadAnalysis, path: str | Path, width: int = 1600, height: int = 900) -> Path:
    all_points = [p for e in analysis.entities for p in e.points]
    if not all_points:
        raise ValueError("Sem pontos para gerar prévia.")
    xs = [p[0] for p in all_points]
    ys = [p[1] for p in all_points]
    minx, maxx = min(xs), max(xs)
    miny, maxy = min(ys), max(ys)
    dx, dy = max(maxx - minx, 1.0), max(maxy - miny, 1.0)
    pad = 40.0
    scale = min((width - 2 * pad) / dx, (height - 2 * pad) / dy)

    def xy(p):
        x = pad + (p[0] - minx) * scale
        y = height - pad - (p[1] - miny) * scale
        return x, y

    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">', '<rect width="100%" height="100%" fill="#0f172a"/>']
    order = {"domain": 0, "cut": 1, "fill": 1, "edge": 2, "center": 3, "marking": 4, "water": 1, "rail": 2, "oae": 4, "other": 0}
    for e in sorted(analysis.entities, key=lambda v: order.get(v.category, 0)):
        pts = " ".join(f"{x:.2f},{y:.2f}" for x, y in map(xy, e.points))
        color = COLORS.get(e.category, COLORS["other"])
        width_px = 2.6 if e.category in {"cut", "fill", "center", "marking"} else 1.4
        dash = ' stroke-dasharray="9 7"' if e.category == "marking" else ""
        parts.append(f'<polyline points="{pts}" fill="none" stroke="{color}" stroke-width="{width_px}" stroke-linecap="round" stroke-linejoin="round"{dash}><title>{escape(e.layer)} · {e.category}</title></polyline>')
    parts.append('</svg>')
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(parts), encoding="utf-8")
    return out
