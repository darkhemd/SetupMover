"""Property-based Tests für core.formats.

Generiert randomisierte Token-Listen und Stems, prüft Invarianten der
Klassifikation und der detect_format-Rückgabe.
"""
from __future__ import annotations

from hypothesis import given
from hypothesis import strategies as st

from core.formats import _classify, detect_format, stem_format_label

VALID_LABELS = {"A", "B", "C", "?"}

# Tokens ohne "_" (sonst zerlegt der Split anders als erwartet) und nicht leer
_token = st.text(
    alphabet=st.characters(
        whitelist_categories=("Lu", "Ll", "Nd"),
        max_codepoint=127,
    ),
    min_size=1,
    max_size=20,
)
_parts = st.lists(_token, min_size=0, max_size=10)


@given(_parts)
def test_classify_returns_known_label(parts):
    label = _classify(parts)
    assert label in VALID_LABELS


@given(_parts)
def test_classify_length_rules(parts):
    label = _classify(parts)
    if len(parts) >= 6:
        assert label == "B"
    elif len(parts) == 5:
        assert label in ("A", "C")
    else:
        assert label == "?"


@given(_parts)
def test_classify_format_c_requires_uppercase_in_part2(parts):
    label = _classify(parts)
    if label == "C":
        assert any(c.isupper() for c in parts[2])
    if label == "A":
        # Format A wenn 5 Teile, parts[2] aber keine Großbuchstaben enthält
        assert len(parts) == 5
        assert not any(c.isupper() for c in parts[2])


@given(_parts)
def test_classify_idempotent(parts):
    assert _classify(parts) == _classify(list(parts))


@given(_parts)
def test_detect_format_consistent_with_classify(parts):
    stem = "_".join(parts)
    # Wenn der Stem keine Underscores enthält oder Tokens leer wären,
    # kann split anders zurückkommen — daher klassifizieren wir auf split-Basis.
    split_parts = stem.split("_")
    label = _classify(split_parts)
    car, track, season = detect_format(stem)
    if label == "?":
        assert (car, track, season) == (None, None, None)
    elif label == "A":
        assert (car, track, season) == (split_parts[3], split_parts[1], split_parts[2])
    else:  # B oder C
        assert (car, track, season) == (split_parts[2], split_parts[3], split_parts[1])


@given(_parts)
def test_detect_format_idempotent(parts):
    stem = "_".join(parts)
    assert detect_format(stem) == detect_format(stem)


@given(_parts)
def test_stem_format_label_matches_classify(parts):
    stem = "_".join(parts)
    assert stem_format_label(stem) == _classify(stem.split("_"))


def test_known_format_a_example():
    # Anbieter_Strecke_Season_Fahrzeug_Setuptyp — parts[2] ohne Großbuchstaben
    car, track, season = detect_format("acme_spa_26s2_audirs3_qualy")
    assert (car, track, season) == ("audirs3", "spa", "26s2")


def test_known_format_b_example():
    # 6+ Teile
    car, track, season = detect_format("vrs_26S2_RS3Gen2_Spa_Q_safe")
    assert (car, track, season) == ("RS3Gen2", "Spa", "26S2")


def test_known_format_c_example():
    # VRS-Style: parts[2] mit Großbuchstaben
    car, track, season = detect_format("VRS_26S2_RS3Gen2_Spa_Q")
    assert (car, track, season) == ("RS3Gen2", "Spa", "26S2")
