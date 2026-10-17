from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from videos_rodoviarios.core.models import RoadAnalysis


def write_analysis_json(analysis: RoadAnalysis, path: str | Path) -> Path:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(asdict(analysis), ensure_ascii=False, indent=2), encoding="utf-8")
    return out
