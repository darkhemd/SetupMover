from __future__ import annotations

import argparse
import sys
from pathlib import Path

from core.config import ALIAS_FILE, DEFAULT_DEST
from core.paths import collect_sto_sources
from core.planner import load_aliases_json_file, plan_sto_operations


def run_cli() -> int:
    parser = argparse.ArgumentParser(
        description="iRacing Setup Manager — Headless-Scan (keine GUI).",
    )
    parser.add_argument("--scan", action="store_true", help="Setup-Dateien planen und nach stdout melden")
    parser.add_argument("--source", type=str, required=True, help="Quellordner mit .sto")
    parser.add_argument("--dest", type=str, default="", help="iRacing setups-Stammordner")
    parser.add_argument("--mode", choices=("none", "season", "track", "both"), default="none")
    parser.add_argument("--season", type=str, default="26S2")
    parser.add_argument("--recursive", action="store_true")
    parser.add_argument("--aliases-file", type=str, default=str(ALIAS_FILE),
                        help="JSON mit Aliassen (wie ~/.iracing_aliases.json)")
    args = parser.parse_args()
    if not args.scan:
        parser.error("Derzeit nur --scan unterstützt. Beispiel: --scan --source /pfad/zu/setups")
    src = Path(args.source).expanduser()
    if not src.is_dir():
        print(f"Quelle ist kein Ordner: {src}", file=sys.stderr)
        return 1
    dest_base = Path(args.dest.strip() or DEFAULT_DEST).expanduser().resolve()
    aliases   = load_aliases_json_file(Path(args.aliases_file).expanduser())
    sources   = collect_sto_sources(src, args.recursive)
    if not sources:
        print("Keine .sto-Dateien gefunden.")
        return 0
    plan  = plan_sto_operations(dest_base, sources, aliases, args.mode, args.season)
    n_ok  = sum(1 for e in plan if e.ready)
    n_bad = len(plan) - n_ok
    print(f"Quelle: {src.resolve()}")
    print(f"Ziel:   {dest_base}")
    print(f"Dateien: {len(plan)}  ·  bereit: {n_ok}  ·  übersprungen: {n_bad}")
    print()
    for e in plan:
        if e.ready:
            print(f"  OK   [{e.format_label}] {e.rel_display}")
            print(f"       → {e.dest_file}")
        else:
            print(f"  SKIP [{e.status}] {e.rel_display} — {e.detail or e.status}")
    return 0
