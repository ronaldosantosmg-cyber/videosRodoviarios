from __future__ import annotations

import re

_PATTERNS = [
    re.compile(r"\b(?:KM\s*)?(\d{1,4})\s*\+\s*(\d{1,3})(?:[,.](\d+))?\b", re.I),
    re.compile(r"\bKM\s*(\d{1,4})[,.](\d{3})\b", re.I),
    re.compile(r"\bKM\s*(\d{1,4})\b", re.I),
]


def parse_station(text: str) -> float | None:
    cleaned = text.replace("\\P", " ").replace("\n", " ")
    m = _PATTERNS[0].search(cleaned)
    if m:
        km = int(m.group(1))
        metres = int(m.group(2))
        frac = float(f"0.{m.group(3)}") if m.group(3) else 0.0
        return km * 1000.0 + metres + frac
    m = _PATTERNS[1].search(cleaned)
    if m:
        return int(m.group(1)) * 1000.0 + int(m.group(2))
    m = _PATTERNS[2].search(cleaned)
    if m:
        return int(m.group(1)) * 1000.0
    return None


def format_station(value_m: float | None) -> str | None:
    if value_m is None:
        return None
    km = int(value_m // 1000)
    metres = value_m - km * 1000
    if abs(metres - round(metres)) < 1e-6:
        return f"{km}+{int(round(metres)):03d}"
    return f"{km}+{metres:06.2f}".replace(".", ",")
