"""Tests für reine Logik (ohne GUI-Lauf)."""
from __future__ import annotations

from pathlib import Path

import pytest

import iracing_setup_manager as ism


def test_detect_format_format_b():
    stem = "VRS_26S2_RS3Gen2_Spa_GP_Q_Race"
    car, track, season = ism.detect_format(stem)
    assert car == "RS3Gen2"
    assert track == "Spa"
    assert season == "26S2"


def test_detect_format_format_a():
    # parts[2] darf kein Großbuchstabe enthalten, sonst wird Format C angenommen
    stem = "VRS_Spa_26s2_audir8_Q"
    car, track, season = ism.detect_format(stem)
    assert car == "audir8"
    assert track == "Spa"
    assert season == "26s2"


def test_detect_format_format_c_camelcase():
    stem = "VRS_26S2_RS3Gen2_Spa_Q_Race"
    car, track, season = ism.detect_format(stem)
    assert car == "RS3Gen2"
    assert track == "Spa"


def test_detect_format_unknown():
    assert ism.detect_format("too_short") == (None, None, None)


def test_stem_format_label():
    assert ism.stem_format_label("a_b_c_d_e") == "A"
    assert ism.stem_format_label("VRS_26S2_RS3Gen2_Spa_Q") == "C"
    assert ism.stem_format_label("a_b_c_d_e_f") == "B"


@pytest.mark.parametrize(
    "mode,expected_suffix",
    [
        ("none", Path("bmwm4gt3")),
        ("season", Path("bmwm4gt3/26S2")),
        ("track", Path("bmwm4gt3/Spa")),
        ("both", Path("bmwm4gt3/26S2/Spa")),
    ],
)
def test_build_dest_path(mode: str, expected_suffix: Path):
    dest = Path("/tmp/iracing_setups")
    got = ism.build_dest_path(dest, "bmwm4gt3", "Spa", mode, "26S2")
    assert got == dest / expected_suffix


def test_plan_sto_operations_ready(tmp_path: Path):
    dest = tmp_path / "setups"
    dest.mkdir()
    src = tmp_path / "in"
    src.mkdir()
    f = src / "VRS_26S2_RS3Gen2_Spa_Q_Race.sto"
    f.write_text("x", encoding="utf-8")
    aliases = {"RS3Gen2": "audirs3lmsgen2"}
    plan = ism.plan_sto_operations(
        dest,
        [(f.name, f.resolve())],
        aliases,
        "none",
        "26S2",
    )
    assert len(plan) == 1
    assert plan[0].ready
    assert plan[0].iracing_folder == "audirs3lmsgen2"
    assert plan[0].dest_file == dest / "audirs3lmsgen2" / f.name


def test_plan_sto_operations_no_alias(tmp_path: Path):
    dest = tmp_path / "setups"
    dest.mkdir()
    src = tmp_path / "in"
    src.mkdir()
    f = src / "VRS_26S2_UnknownCar_Spa_Q_Race.sto"
    f.write_text("x", encoding="utf-8")
    plan = ism.plan_sto_operations(dest, [(f.name, f.resolve())], {}, "none", "26S2")
    assert len(plan) == 1
    assert plan[0].status == "no_alias"


def test_plan_sto_operations_duplicate_basename(tmp_path: Path):
    dest = tmp_path / "setups"
    dest.mkdir()
    src = tmp_path / "in"
    src.mkdir()
    (src / "a").mkdir()
    (src / "b").mkdir()
    name = "VRS_26S2_RS3Gen2_Spa_Q_Race.sto"
    f1 = src / "a" / name
    f2 = src / "b" / name
    f1.write_text("1", encoding="utf-8")
    f2.write_text("2", encoding="utf-8")
    sources = sorted(
        [
            (f1.relative_to(src).as_posix(), f1.resolve()),
            (f2.relative_to(src).as_posix(), f2.resolve()),
        ],
        key=lambda t: t[0].lower(),
    )
    aliases = {"RS3Gen2": "audirs3lmsgen2"}
    plan = ism.plan_sto_operations(dest, sources, aliases, "none", "26S2")
    assert len(plan) == 2
    dup = [e for e in plan if e.status == "duplicate_name"]
    assert len(dup) == 1
    assert sum(1 for e in plan if e.ready) == 1


def test_merge_path_history():
    h: list[str] = []
    ism.merge_path_history(h, "/a")
    ism.merge_path_history(h, "/b")
    ism.merge_path_history(h, "/a")
    assert h == ["/a", "/b"]


def test_dest_looks_like_setups_root(tmp_path: Path):
    assert ism.dest_looks_like_setups_root(tmp_path) is False
    good = tmp_path / "setups_like"
    good.mkdir()
    (good / "bmwm4gt3").mkdir()
    assert ism.dest_looks_like_setups_root(good) is True


def test_pick_rename_destination(tmp_path: Path):
    f = tmp_path / "x.sto"
    f.write_text("1", encoding="utf-8")
    alt = ism.pick_rename_destination(f)
    assert alt == tmp_path / "x_v2.sto"
    assert not alt.exists()


def test_collect_sto_sources_flat(tmp_path: Path):
    src = tmp_path / "s"
    src.mkdir()
    (src / "a.sto").write_text("x", encoding="utf-8")
    (src / "b.txt").write_text("y", encoding="utf-8")
    out = ism.collect_sto_sources(src, False)
    assert len(out) == 1
    assert out[0][0] == "a.sto"


def test_collect_sto_sources_recursive(tmp_path: Path):
    src = tmp_path / "s"
    src.mkdir()
    sub = src / "u"
    sub.mkdir()
    (sub / "c.sto").write_text("x", encoding="utf-8")
    out = ism.collect_sto_sources(src, True)
    assert len(out) == 1
    assert out[0][0] == "u/c.sto"


def test_load_aliases_json_file(tmp_path: Path):
    p = tmp_path / "a.json"
    p.write_text(
        '[{"alias": "X", "folder": "bmwm4gt3", "note": ""}]',
        encoding="utf-8",
    )
    d = ism.load_aliases_json_file(p)
    assert d == {"X": "bmwm4gt3"}
