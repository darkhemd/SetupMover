from __future__ import annotations

from typing import Literal

FormatLabel = Literal["A", "B", "C", "?"]


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
