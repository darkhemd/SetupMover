from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable, Literal

from core.config import BACKUP_KEEP_MAX
from core.formats import detect_format, stem_format_label
from core.paths import build_dest_path, pick_rename_destination

CollisionPolicy = Literal["overwrite", "skip", "rename"]


@dataclass(frozen=True)
class StoPlanEntry:
    """Ergebnis der Planung für eine .sto-Datei (Scan / Kopieren)."""
    rel_display: str
    src_file: Path
    stem: str
    car: str | None
    track: str | None
    season: str | None
    iracing_folder: str | None
    dest_dir: Path | None
    dest_file: Path | None
    status: str
    format_label: str
    detail: str = ""

    @property
    def ready(self) -> bool:
        return self.status == "ready"


@dataclass
class CopyResult:
    entry: StoPlanEntry
    outcome: Literal["ok", "overwritten", "renamed", "skipped", "error", "dry"]
    final_dest: Path | None
    error: Exception | None = None


def plan_sto_operations(
    dest_base: Path,
    sto_sources: list[tuple[str, Path]],
    aliases: dict[str, str],
    mode: str,
    season: str,
) -> list[StoPlanEntry]:
    """
    Plant alle Operationen. sto_sources: (Anzeigepfad, absolute Quelldatei).
    Ziel-Dateiname ist immer der Basisname (flach), auch bei rekursivem Scan.
    """
    seen_basenames: set[str] = set()
    out: list[StoPlanEntry] = []
    for rel_display, src_abs in sorted(sto_sources, key=lambda t: t[0].replace("\\", "/").lower()):
        stem = src_abs.stem
        fname = src_abs.name
        key = fname.lower()
        duplicate = key in seen_basenames
        if not duplicate:
            seen_basenames.add(key)

        car, track, season_parsed = detect_format(stem)
        fmt = stem_format_label(stem)

        if duplicate:
            out.append(StoPlanEntry(
                rel_display=rel_display, src_file=src_abs, stem=stem,
                car=car, track=track, season=season_parsed,
                iracing_folder=None, dest_dir=None, dest_file=None,
                status="duplicate_name", format_label=fmt,
                detail="Doppelter Dateiname (flaches Ziel)",
            ))
            continue

        if car is None:
            out.append(StoPlanEntry(
                rel_display=rel_display, src_file=src_abs, stem=stem,
                car=None, track=None, season=None,
                iracing_folder=None, dest_dir=None, dest_file=None,
                status="bad_format", format_label=fmt,
                detail="Unbekanntes Namensschema",
            ))
            continue

        folder = aliases.get(car)
        if not folder:
            out.append(StoPlanEntry(
                rel_display=rel_display, src_file=src_abs, stem=stem,
                car=car, track=track, season=season_parsed,
                iracing_folder=None, dest_dir=None, dest_file=None,
                status="no_alias", format_label=fmt,
                detail=f"Kein Alias für \u201e{car}\u201c",
            ))
            continue

        dest_dir = build_dest_path(dest_base, folder, track or "", mode, season)
        dest_file = dest_dir / fname
        out.append(StoPlanEntry(
            rel_display=rel_display, src_file=src_abs, stem=stem,
            car=car, track=track, season=season_parsed,
            iracing_folder=folder, dest_dir=dest_dir, dest_file=dest_file,
            status="ready", format_label=fmt, detail="",
        ))
    return out


def _prune_backups(dest_file: Path) -> None:
    """Löscht älteste Backups wenn mehr als BACKUP_KEEP_MAX vorhanden."""
    pattern = f"{dest_file.stem}_*.bak{dest_file.suffix}"
    baks = sorted(dest_file.parent.glob(pattern))
    for old in baks[:-BACKUP_KEEP_MAX]:
        try:
            old.unlink()
        except OSError:
            pass


def execute_copy_plan(
    plan: list[StoPlanEntry],
    moving: bool,
    dry: bool,
    collision: CollisionPolicy,
    backup: bool,
    on_result: Callable[[CopyResult], None] | None = None,
) -> tuple[int, int, int, int]:
    """
    Führt Copy/Move für alle ready-Einträge aus.

    Rückgabe: (ok, skipped, overwritten, errors)
    Der on_result-Callback erlaubt der GUI schrittweise Log-Updates ohne
    dass diese Funktion tkinter kennen muss.
    """
    ok = skipped = overwritten = errors = 0

    for e in plan:
        if not e.ready:
            skipped += 1
            if on_result:
                on_result(CopyResult(e, "skipped", None))
            continue

        assert e.dest_dir is not None
        assert e.dest_file is not None
        src_file = e.src_file
        dest_file = e.dest_file

        try:
            if dry:
                ok += 1
                if on_result:
                    on_result(CopyResult(e, "dry", dest_file))
                continue

            dest_file.parent.mkdir(parents=True, exist_ok=True)
            final_dest = dest_file
            outcome: Literal["ok", "overwritten", "renamed", "skipped", "error", "dry"] = "ok"

            if dest_file.exists():
                if collision == "skip":
                    skipped += 1
                    if on_result:
                        on_result(CopyResult(e, "skipped", dest_file))
                    continue
                elif collision == "rename":
                    final_dest = pick_rename_destination(dest_file)
                    outcome = "renamed"
                else:
                    if backup:
                        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                        bak = dest_file.with_name(f"{dest_file.stem}_{ts}.bak{dest_file.suffix}")
                        shutil.copy2(str(dest_file), str(bak))
                        _prune_backups(dest_file)
                    outcome = "overwritten"
                    overwritten += 1

            if moving:
                shutil.move(str(src_file), str(final_dest))
            else:
                shutil.copy2(str(src_file), str(final_dest))

            if outcome == "ok":
                ok += 1
            elif outcome == "renamed":
                ok += 1

            if on_result:
                on_result(CopyResult(e, outcome, final_dest))

        except Exception as exc:
            errors += 1
            if on_result:
                on_result(CopyResult(e, "error", None, error=exc))

    return ok, skipped, overwritten, errors


def load_aliases_json_file(path: Path) -> dict[str, str]:
    """Liest Alias-JSON (Liste von {alias, folder, note?}) in ein Lookup-Dict."""
    if not path.exists():
        return {}
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
        return {}
    if not isinstance(data, list):
        return {}
    out: dict[str, str] = {}
    for row in data:
        if not isinstance(row, dict):
            continue
        a = str(row.get("alias", "")).strip()
        fo = str(row.get("folder", "")).strip()
        if a and fo:
            out[a] = fo
    return out
