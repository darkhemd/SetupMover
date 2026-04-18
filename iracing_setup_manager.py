#!/usr/bin/env python3
"""
iRacing Setup Manager
Format A (5 Teile): Anbieter_Strecke_Season_Fahrzeug_Setuptyp
Format B (6 Teile): Anbieter_Season_Fahrzeug_Strecke_Sessiontyp_Setupstil
"""

from __future__ import annotations

import sys


def main() -> None:
    if len(sys.argv) > 1:
        from cli import run_cli
        raise SystemExit(run_cli())
    from gui.app import App
    App().mainloop()


if __name__ == "__main__":
    main()
