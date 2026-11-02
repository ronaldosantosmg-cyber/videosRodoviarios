from __future__ import annotations

import sys
from pathlib import Path


def app_root() -> Path:
    """Return the portable application root (folder containing the EXE when frozen)."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[2]


ROOT_DIR = app_root()
TEXTURES_DIR = ROOT_DIR / "texturas"
SAVED_DIR = ROOT_DIR / "projetos_salvos"
DATABASE_DIR = ROOT_DIR / "banco_dados"
SUPPORT_DIR = ROOT_DIR / "apoio"


def ensure_app_dirs() -> None:
    for path in (TEXTURES_DIR, SAVED_DIR, DATABASE_DIR, SUPPORT_DIR):
        path.mkdir(parents=True, exist_ok=True)


def settings_path() -> Path:
    ensure_app_dirs()
    return DATABASE_DIR / "config.json"
