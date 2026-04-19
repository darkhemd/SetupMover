from __future__ import annotations

import os
from pathlib import Path

# ── Dateipfade ─────────────────────────────────────────────────────────────
# IRACING_SETUP_MANAGER_CONFIG_DIR überlagert das Home-Verzeichnis (Portable-Modus).
_env = os.environ.get("IRACING_SETUP_MANAGER_CONFIG_DIR", "")
_config_dir: Path = Path(_env).expanduser() if _env else Path.home()

CONFIG_FILE    = _config_dir / ".iracing_setup_manager.json"
ALIAS_FILE     = _config_dir / ".iracing_aliases.json"
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
WATCH_INTERVAL_MS:      int = 5_000
