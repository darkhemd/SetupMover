from __future__ import annotations

from pathlib import Path

# ── Dateipfade ─────────────────────────────────────────────────────────────
CONFIG_FILE    = Path.home() / ".iracing_setup_manager.json"
ALIAS_FILE     = Path.home() / ".iracing_aliases.json"
DEFAULT_SOURCE = str(Path.home() / "Documents" / "iRacing" / "setups_incoming")
DEFAULT_DEST   = str(Path.home() / "Documents" / "iRacing" / "setups")

# ── Einstellbare Konstanten ─────────────────────────────────────────────────
HISTORY_MAX_ITEMS:      int = 8
RENAME_VERSION_LIMIT:   int = 10_000
AUTOCOMPLETE_HIDE_MS:   int = 120
AUTOCOMPLETE_MAX_SHOWN: int = 9
WINDOW_GEOMETRY:        str = "980x780"
WINDOW_MIN_W:           int = 880
WINDOW_MIN_H:           int = 680
BACKUP_KEEP_MAX:        int = 5
