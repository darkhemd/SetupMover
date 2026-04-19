#!/usr/bin/env python3
"""
iRacing Setup Manager
Format A (5 Teile): Anbieter_Strecke_Season_Fahrzeug_Setuptyp
Format B (6 Teile): Anbieter_Season_Fahrzeug_Strecke_Sessiontyp_Setupstil
"""

from __future__ import annotations

import os


def main() -> None:
    # Pre-parse --config-dir before any project imports so that core.config
    # reads the env var on its first import (lazy import below).
    import argparse
    pre = argparse.ArgumentParser(add_help=False)
    pre.add_argument("--config-dir", dest="config_dir", default=None)
    known, rest = pre.parse_known_args()
    if known.config_dir:
        os.environ.setdefault("IRACING_SETUP_MANAGER_CONFIG_DIR", known.config_dir)

    if rest:
        from cli import run_cli
        raise SystemExit(run_cli())
    from gui.app import App
    App().mainloop()


if __name__ == "__main__":
    main()
