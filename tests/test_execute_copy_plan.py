"""Filesystem-Tests für execute_copy_plan (ohne GUI)."""
from __future__ import annotations

from pathlib import Path

import pytest

from core.planner import CopyResult, StoPlanEntry, execute_copy_plan


def _entry(src_dir: Path, dest_dir: Path, filename: str = "VRS_26S2_RS3Gen2_Spa_Q.sto") -> StoPlanEntry:
    src_file = src_dir / filename
    src_file.write_text("setup-data", encoding="utf-8")
    return StoPlanEntry(
        rel_display=filename,
        src_file=src_file,
        stem=src_file.stem,
        car="RS3Gen2",
        track="Spa",
        season="26S2",
        iracing_folder="audirs3lmsgen2",
        dest_dir=dest_dir,
        dest_file=dest_dir / filename,
        status="ready",
        format_label="C",
    )


def _not_ready(src_dir: Path) -> StoPlanEntry:
    return StoPlanEntry(
        rel_display="bad.sto",
        src_file=src_dir / "bad.sto",
        stem="bad",
        car=None, track=None, season=None, iracing_folder=None,
        dest_dir=None, dest_file=None,
        status="bad_format", format_label="?",
    )


@pytest.fixture()
def dirs(tmp_path: Path):
    src = tmp_path / "src"
    dest = tmp_path / "dest"
    src.mkdir()
    dest.mkdir()
    return src, dest


def test_dry_run_writes_no_files(dirs):
    src, dest = dirs
    e = _entry(src, dest)
    ok, skip, ow, err = execute_copy_plan([e], moving=False, dry=True, collision="overwrite", backup=False)
    assert (ok, skip, ow, err) == (1, 0, 0, 0)
    assert not e.dest_file.exists()
    assert e.src_file.exists()


def test_copy_creates_file(dirs):
    src, dest = dirs
    e = _entry(src, dest)
    ok, skip, ow, err = execute_copy_plan([e], moving=False, dry=False, collision="overwrite", backup=False)
    assert (ok, err) == (1, 0)
    assert e.dest_file.exists()
    assert e.src_file.exists()


def test_move_removes_source(dirs):
    src, dest = dirs
    e = _entry(src, dest)
    execute_copy_plan([e], moving=True, dry=False, collision="overwrite", backup=False)
    assert e.dest_file.exists()
    assert not e.src_file.exists()


def test_overwrite_creates_backup(dirs):
    src, dest = dirs
    e = _entry(src, dest)
    e.dest_file.write_text("old-content", encoding="utf-8")
    execute_copy_plan([e], moving=False, dry=False, collision="overwrite", backup=True)
    bak_files = list(dest.glob(f"{e.dest_file.stem}_*.bak{e.dest_file.suffix}"))
    assert len(bak_files) == 1
    assert bak_files[0].read_text(encoding="utf-8") == "old-content"
    assert e.dest_file.read_text(encoding="utf-8") == "setup-data"


def test_skip_collision_preserves_original(dirs):
    src, dest = dirs
    e = _entry(src, dest)
    e.dest_file.write_text("old", encoding="utf-8")
    ok, skip, ow, err = execute_copy_plan([e], moving=False, dry=False, collision="skip", backup=False)
    assert ok == 0
    assert e.dest_file.read_text(encoding="utf-8") == "old"


def test_rename_collision_keeps_both(dirs):
    src, dest = dirs
    e = _entry(src, dest)
    e.dest_file.write_text("old", encoding="utf-8")
    results: list[CopyResult] = []
    execute_copy_plan([e], moving=False, dry=False, collision="rename", backup=False, on_result=results.append)
    assert len(results) == 1
    assert results[0].outcome == "renamed"
    assert results[0].final_dest is not None
    assert results[0].final_dest.exists()
    assert e.dest_file.read_text(encoding="utf-8") == "old"


def test_not_ready_entry_is_skipped(dirs):
    src, dest = dirs
    e = _not_ready(src)
    ok, skip, ow, err = execute_copy_plan([e], moving=False, dry=False, collision="overwrite", backup=False)
    assert ok == 0 and skip == 1 and err == 0


def test_on_result_callback_called(dirs):
    src, dest = dirs
    e = _entry(src, dest)
    results: list[CopyResult] = []
    execute_copy_plan([e], moving=False, dry=False, collision="overwrite", backup=False, on_result=results.append)
    assert len(results) == 1
    assert results[0].outcome == "ok"
    assert results[0].final_dest == e.dest_file


def test_backup_retention_prunes_old(dirs):
    from core.config import BACKUP_KEEP_MAX
    src, dest = dirs
    e = _entry(src, dest)
    # Erstelle mehr Backups als BACKUP_KEEP_MAX erlaubt
    for i in range(BACKUP_KEEP_MAX + 2):
        old_bak = dest / f"{e.dest_file.stem}_{i:08d}_000000.bak{e.dest_file.suffix}"
        old_bak.write_text("old", encoding="utf-8")
    e.dest_file.write_text("overwrite-me", encoding="utf-8")
    execute_copy_plan([e], moving=False, dry=False, collision="overwrite", backup=True)
    remaining = list(dest.glob(f"{e.dest_file.stem}_*.bak{e.dest_file.suffix}"))
    assert len(remaining) <= BACKUP_KEEP_MAX
