from __future__ import annotations

import re
import unicodedata


def _norm(value: str) -> str:
    value = unicodedata.normalize("NFKD", value)
    value = "".join(c for c in value if not unicodedata.combining(c))
    return re.sub(r"[^A-Z0-9]+", "_", value.upper()).strip("_")


RULES: list[tuple[str, tuple[str, ...]]] = [
    ("cut", ("CORTE", "CUT", "OFFSET_CORTE", "OFF_CORTE", "TALUDE_CORTE", "HCORTE")),
    ("fill", ("ATERRO", "FILL", "OFFSET_ATERRO", "OFF_ATERRO", "TALUDE_ATERRO", "HATERRO")),
    ("domain", ("FAIXA_DOMINIO", "DOMINIO", "RIGHT_OF_WAY", "ROW")),
    ("marking", ("SINALIZACAO_HORIZONTAL", "SINAL_HORIZONTAL", "MARKING", "PINTURA", "FAIXA_CONTINUA", "FAIXA_TRACEJADA", "LINHA_BORDO")),
    ("center", ("EIXO", "CENTERLINE", "CENTER", "ALIGNMENT", "ALINHAMENTO", "HZ_EIXO")),
    ("edge", ("BORDO", "EDGE", "PAVIM", "PLATAFORMA", "ACOSTAMENTO", "CANTEIRO", "NEWJERSEY", "PAVEXIST", "PAVPROJ")),
    ("water", ("HIDRO", "RIO", "CORREGO", "RIBEIRAO", "DRENAGEM_NATURAL", "WATER")),
    ("rail", ("FERROVIA", "FERROV", "RAIL", "TRILHO", "EFVM")),
    ("oae", ("OAE", "PONTE", "VIADUTO", "VIAD", "TUNEL", "PASSARELA")),
]


def classify_layer(layer: str) -> str:
    key = _norm(layer)
    for category, tokens in RULES:
        if any(token in key for token in tokens):
            return category
    if "FAIXA" in key and "DOMINIO" not in key:
        return "marking"
    return "other"
