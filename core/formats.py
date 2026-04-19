from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Literal

FormatLabel = Literal["A", "B", "C", "?"]

_CAR_TAGS   = frozenset({"car", "carid", "carpath", "carname", "vehicle"})
_TRACK_TAGS = frozenset({"track", "trackid", "trackpath", "trackname", "circuit"})


def _classify(parts: list[str]) -> FormatLabel:
    """Einzige Quelle der Wahrheit für Format-Klassifizierung."""
    if len(parts) >= 6:
        return "B"
    if len(parts) == 5:
        return "C" if (parts[2] and any(c.isupper() for c in parts[2])) else "A"
    return "?"


def detect_format(stem: str) -> tuple[str | None, str | None, str | None]:
    """
    Erkennt drei Setup-Dateinamenschemata.

    - Format A (5 Teile):  Anbieter_Strecke_Season_Fahrzeug_Setuptyp
    - Format B (6+ Teile): Anbieter_Season_Fahrzeug_Strecke_Sessiontyp_Setupstil
    - Format C (5 Teile):  Anbieter_Season_Fahrzeug_Strecke_Setuptyp (VRS-Style)

    Rückgabe: (car, track, season) oder (None, None, None)
    """
    parts = stem.split("_")
    label = _classify(parts)
    if label in ("B", "C"):
        return parts[2], parts[3], parts[1]
    if label == "A":
        return parts[3], parts[1], parts[2]
    return None, None, None


def stem_format_label(stem: str) -> FormatLabel:
    """Format-Kürzel passend zu detect_format (A / B / C / ?)."""
    return _classify(stem.split("_"))


def parse_sto_header(path: Path) -> tuple[str, str | None, str | None]:
    """
    Liest erste 50 Zeilen der .sto-Datei für die Vorschau.

    Versucht XML zu parsen und bekannte Car-/Track-Tags zu extrahieren.
    Rückgabe: (roher Text, car oder None, track oder None).
    """
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
        raw = "\n".join(text.splitlines()[:50])
    except OSError:
        return "", None, None

    car: str | None = None
    track: str | None = None
    stripped = raw.strip()
    if stripped.startswith("<"):
        root: ET.Element | None = None
        try:
            root = ET.fromstring(stripped)
        except ET.ParseError:
            try:
                root = ET.fromstring(f"<_root>{stripped}</_root>")
            except ET.ParseError:
                pass
        if root is not None:
            for elem in root.iter():
                tag_l = elem.tag.lower()
                val = (elem.text or "").strip() or None
                for attr_n, attr_v in elem.attrib.items():
                    an = attr_n.lower()
                    if an in _CAR_TAGS:
                        car = car or attr_v or None
                    elif an in _TRACK_TAGS:
                        track = track or attr_v or None
                if tag_l in _CAR_TAGS:
                    car = car or val
                elif tag_l in _TRACK_TAGS:
                    track = track or val
    return raw, car, track
