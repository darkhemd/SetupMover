"""CLI-Smoke-Tests für run_cli()."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from cli import run_cli


def _argv(*args: str) -> list[str]:
    return ["prog", *args]


def test_scan_empty_dir(tmp_path: Path, capsys):
    with patch("sys.argv", _argv("--scan", "--source", str(tmp_path))):
        rc = run_cli()
    assert rc == 0
    assert "Keine .sto" in capsys.readouterr().out


def test_scan_with_sto_file(tmp_path: Path, capsys):
    (tmp_path / "VRS_26S2_RS3Gen2_Spa_Q.sto").write_text("x", encoding="utf-8")
    with patch("sys.argv", _argv("--scan", "--source", str(tmp_path))):
        rc = run_cli()
    assert rc == 0
    out = capsys.readouterr().out
    assert "VRS_26S2_RS3Gen2_Spa_Q.sto" in out


def test_scan_missing_source(tmp_path: Path, capsys):
    nonexistent = tmp_path / "nope"
    with patch("sys.argv", _argv("--scan", "--source", str(nonexistent))):
        rc = run_cli()
    assert rc == 1


def test_scan_with_alias_file(tmp_path: Path, capsys):
    (tmp_path / "VRS_26S2_RS3Gen2_Spa_Q.sto").write_text("x", encoding="utf-8")
    alias_file = tmp_path / "aliases.json"
    alias_file.write_text(
        json.dumps([{"alias": "RS3Gen2", "folder": "audirs3lmsgen2"}]),
        encoding="utf-8",
    )
    with patch("sys.argv", _argv("--scan", "--source", str(tmp_path), "--aliases-file", str(alias_file))):
        rc = run_cli()
    assert rc == 0
    out = capsys.readouterr().out
    assert "bereit: 1" in out


def test_scan_shows_skip_for_unknown_car(tmp_path: Path, capsys):
    (tmp_path / "VRS_26S2_UnknownCar_Spa_Q.sto").write_text("x", encoding="utf-8")
    with patch("sys.argv", _argv("--scan", "--source", str(tmp_path))):
        run_cli()
    out = capsys.readouterr().out
    assert "SKIP" in out or "\u00fcbersprungen: 1" in out
