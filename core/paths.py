from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from core.config import HISTORY_MAX_ITEMS, RENAME_VERSION_LIMIT
from data.iracing_folders import IRACING_FOLDERS_SET


def build_dest_path(dest_base: Path, folder: str, track: str, mode: str, season: str) -> Path:
    """Zielverzeichnis unterhalb von dest_base (iRacing-Fahrzeugordner + Unterordner-Modus)."""
    base = dest_base / folder
    s = season.strip()
    if mode == "season":
        return base / s
    if mode == "track":
        return base / track
    if mode == "both":
        return base / s / track
    return base


def pick_rename_destination(dest_file: Path) -> Path:
    """Freier Zielpfad mit _v2, _v3, … vor dem Dateityp, falls dest_file existiert."""
    if not dest_file.exists():
        return dest_file
    stem, suf = dest_file.stem, dest_file.suffix
    parent = dest_file.parent
    for i in range(2, RENAME_VERSION_LIMIT):
        c = parent / f"{stem}_v{i}{suf}"
        if not c.exists():
            return c
    return dest_file


def collect_sto_sources(src: Path, recursive: bool) -> list[tuple[str, Path]]:
    """Sammelt .sto-Dateien: (relativer Anzeigepfad, absolute Path)."""
    base = src.resolve()
    out: list[tuple[str, Path]] = []
    if recursive:
        for p in sorted(base.rglob("*.sto"), key=lambda x: str(x).lower()):
            out.append((p.relative_to(base).as_posix(), p))
    else:
        for p in sorted(base.iterdir(), key=lambda x: x.name.lower()):
            if p.is_file() and p.suffix.lower() == ".sto":
                out.append((p.name, p))
    return out


def open_path_in_file_manager(path: Path) -> None:
    """Öffnet einen Ordner im System-Dateimanager."""
    path = path.resolve()
    if not path.is_dir():
        path = path.parent
    if sys.platform == "win32":
        os.startfile(path)  # type: ignore[attr-defined]
    elif sys.platform == "darwin":
        subprocess.run(["open", str(path)], check=False)
    else:
        subprocess.run(["xdg-open", str(path)], check=False)


def merge_path_history(hist: list[str], path: str, max_n: int = HISTORY_MAX_ITEMS) -> None:
    """Aktuellen Pfad an den Anfang der Historie setzen (ohne Duplikate)."""
    p = (path or "").strip()
    if not p:
        return
    if p in hist:
        hist.remove(p)
    hist.insert(0, p)
    del hist[max_n:]


def dest_looks_like_setups_root(path: Path) -> bool:
    """Heuristik: mindestens ein direkter Unterordner ist ein bekannter iRacing-Fahrzeugordner."""
    if not path.is_dir():
        return False
    try:
        for child in path.iterdir():
            if child.is_dir() and child.name in IRACING_FOLDERS_SET:
                return True
    except OSError:
        return False
    return False
