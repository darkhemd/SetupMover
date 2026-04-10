#!/usr/bin/env python3
"""
iRacing Setup Manager
Format A (5 Teile): Anbieter_Strecke_Season_Fahrzeug_Setuptyp
Format B (6 Teile): Anbieter_Season_Fahrzeug_Strecke_Sessiontyp_Setupstil
"""

from __future__ import annotations
import argparse
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os, shutil, json, subprocess, sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

# ── Dateipfade ─────────────────────────────────────────────────────────────────
CONFIG_FILE = Path.home() / ".iracing_setup_manager.json"
ALIAS_FILE  = Path.home() / ".iracing_aliases.json"

DEFAULT_SOURCE = str(Path.home() / "Documents" / "iRacing" / "setups_incoming")
DEFAULT_DEST   = str(Path.home() / "Documents" / "iRacing" / "setups")

# ── iRacing Fahrzeugordner ─────────────────────────────────────────────────────
IRACING_FOLDERS = sorted([
    "acuraarx06gtp","acuransxevo22gt3","amvantageevogt3","amvantagegt4",
    "audir8lmsevo2gt3","audirs3lms","audirs3lmsgen2","bmwlmdh","bmwm2csr",
    "bmwm4evogt4","bmwm4gt3","bmwm4gt4","bmwm8gte","c8rvettegte","cadillacctsvr",
    "cadillacvseriesrgtp","chevyvettez06rgt3","crosscartn11","dallaradw12",
    "dallarap217","dirtmicrosprint nonwinged","dirtmicrosprint nonwinged outlaw",
    "dirtmicrosprint winged","dirtmicrosprint winged outlaw","dirtministock",
    "dirtstreetstock","dirtumpmod","ferrari296gt3","ferrari488gte","ferrari499p",
    "fordgt2017","fordmustanggt3","fordmustanggt4","formulair04","formulavee",
    "hondacivictyper","hyundaielantracn7","hyundaivelostern","jettatdi","kiaoptima",
    "lamborghinievogt3","legends dirtford34c","legends ford34c","legends ford34c rookie",
    "ligierjsp320","mclaren570sgt4","mclaren720sgt3","mercedesamgevogt3","mercedesamggt4",
    "ministock","mx5 cup","mx5 mx52016","mx5 roadster","porsche718gt4","porsche963gtp",
    "porsche991rsr","porsche9922cup","porsche992cup","porsche992rgt3","protrucks pro2lite",
    "radical sr8","raygr22","renaultcliocup","solstice","solstice rookie","specracer",
    "stockcarbrasil corolla","stockcarbrasil cruze","streetstock",
    "supercars chevycamarogen3","supercars fordmustanggen3","toyotagr86",
    "trucks silverado","vwbeetlegrc","vwbeetlegrc lite",
])
IRACING_FOLDERS_SET = frozenset(IRACING_FOLDERS)

# ── Farben & Fonts ─────────────────────────────────────────────────────────────
ACCENT    = "#E8323C"
BG_DARK   = "#1A1A1A"
BG_MID    = "#242424"
BG_PANEL  = "#2C2C2C"
BG_INPUT  = "#333333"
BG_ROW_A  = "#2C2C2C"
BG_ROW_B  = "#282828"
BG_SEL    = "#3A2020"
BG_DROP   = "#222222"
FG_MAIN   = "#EFEFEF"
FG_DIM    = "#777777"
FG_HEAD   = "#BBBBBB"
BORDER    = "#3A3A3A"
GREEN     = "#4CAF79"
YELLOW    = "#E8A832"
FONT_MONO = ("Consolas", 9)
FONT_UI   = ("Segoe UI", 9)
FONT_BOLD = ("Segoe UI", 9, "bold")
FONT_SM   = ("Segoe UI", 8)
FONT_H    = ("Segoe UI", 8, "bold")

COL_ALIAS  = 0
COL_FOLDER = 1
COL_NOTE   = 2
COL_VALID  = 3

# Spaltenbreiten (Alias / iRacing Ordner / Notiz / Valid-Status)
COL_WIDTHS = [180, 340, 140, 28]
COL_HEADS  = ["Alias (im Dateinamen)", "iRacing Ordner", "Notiz", ""]


# ── Format-Erkennung ───────────────────────────────────────────────────────────
def detect_format(stem: str):
    """
    Erkennt drei Setup-Dateinamenschemata:
    - Format A (5 Teile):  Anbieter_Strecke_Season_Fahrzeug_Setuptyp
    - Format B (6+ Teile): Anbieter_Season_Fahrzeug_Strecke_Sessiontyp_Setupstil
    - Format C (5 Teile):  Anbieter_Season_Fahrzeug_Strecke_Setuptyp (VRS-Style)
    
    Rückgabe: (car, track, season) oder (None, None, None)
    """
    parts = stem.split("_")
    
    # Format B (6+ Teile): Anbieter_Season_Fahrzeug_Strecke_...
    if len(parts) >= 6:
        return parts[2], parts[3], parts[1]
    
    # Format A oder C (5 Teile)
    if len(parts) == 5:
        # Format C (VRS-Stil): Anbieter_Season_Fahrzeug_Strecke_Setuptyp
        # Erkennungsmerkmal: part[2] ist ein bekanntes Alias (z.B. RS3Gen2)
        # oder part[2] enthält Großbuchstaben (CamelCase wie RS3Gen2, BMWm4GT3)
        car_candidate = parts[2]
        if car_candidate and any(c.isupper() for c in car_candidate):
            # Wahrscheinlich Format C (CamelCase-Alias)
            return parts[2], parts[3], parts[1]
        
        # Fallback: Format A (legacy)
        return parts[3], parts[1], parts[2]
    
    return None, None, None


def stem_format_label(stem: str) -> str:
    """Format-Kürzel passend zu detect_format (A / B / C / ?)."""
    parts = stem.split("_")
    if len(parts) >= 6:
        return "B"
    if len(parts) == 5:
        car_candidate = parts[2]
        if car_candidate and any(c.isupper() for c in car_candidate):
            return "C"
        return "A"
    return "?"


def build_dest_path(dest_base: Path, folder: str, track: str, mode: str, season: str) -> Path:
    """Zielverzeichnis unterhalb von dest_base (iRacing-Fahrzeugordner + Unterordner-Modus)."""
    base = dest_base / folder
    s = season.strip()
    if mode == "season":
        return base / s
    if mode == "track":
        return base / track
    if mode == "both":
        return base / s / track
    return base


@dataclass(frozen=True)
class StoPlanEntry:
    """Ergebnis der Planung für eine .sto-Datei (Scan / Kopieren)."""
    rel_display: str
    src_file: Path
    stem: str
    car: str | None
    track: str | None
    season: str | None
    iracing_folder: str | None
    dest_dir: Path | None
    dest_file: Path | None
    status: str
    format_label: str
    detail: str = ""

    @property
    def ready(self) -> bool:
        return self.status == "ready"


def plan_sto_operations(
    dest_base: Path,
    sto_sources: list[tuple[str, Path]],
    aliases: dict[str, str],
    mode: str,
    season: str,
) -> list[StoPlanEntry]:
    """
    Plant alle Operationen. sto_sources: (Anzeigepfad, absolute Quelldatei).
    Ziel-Dateiname ist immer der Basisname (flach), auch bei rekursivem Scan.
    """
    seen_basenames: set[str] = set()
    out: list[StoPlanEntry] = []
    for rel_display, src_abs in sorted(sto_sources, key=lambda t: t[0].replace("\\", "/").lower()):
        stem = src_abs.stem
        fname = src_abs.name
        key = fname.lower()
        duplicate = key in seen_basenames
        if not duplicate:
            seen_basenames.add(key)

        car, track, season_parsed = detect_format(stem)
        fmt = stem_format_label(stem)

        if duplicate:
            out.append(
                StoPlanEntry(
                    rel_display=rel_display,
                    src_file=src_abs,
                    stem=stem,
                    car=car,
                    track=track,
                    season=season_parsed,
                    iracing_folder=None,
                    dest_dir=None,
                    dest_file=None,
                    status="duplicate_name",
                    format_label=fmt,
                    detail="Doppelter Dateiname (flaches Ziel)",
                )
            )
            continue

        if car is None:
            out.append(
                StoPlanEntry(
                    rel_display=rel_display,
                    src_file=src_abs,
                    stem=stem,
                    car=None,
                    track=None,
                    season=None,
                    iracing_folder=None,
                    dest_dir=None,
                    dest_file=None,
                    status="bad_format",
                    format_label=fmt,
                    detail="Unbekanntes Namensschema",
                )
            )
            continue

        folder = aliases.get(car)
        if not folder:
            out.append(
                StoPlanEntry(
                    rel_display=rel_display,
                    src_file=src_abs,
                    stem=stem,
                    car=car,
                    track=track,
                    season=season_parsed,
                    iracing_folder=None,
                    dest_dir=None,
                    dest_file=None,
                    status="no_alias",
                    format_label=fmt,
                    detail=f"Kein Alias für „{car}“",
                )
            )
            continue

        dest_dir = build_dest_path(dest_base, folder, track or "", mode, season)
        dest_file = dest_dir / fname
        out.append(
            StoPlanEntry(
                rel_display=rel_display,
                src_file=src_abs,
                stem=stem,
                car=car,
                track=track,
                season=season_parsed,
                iracing_folder=folder,
                dest_dir=dest_dir,
                dest_file=dest_file,
                status="ready",
                format_label=fmt,
                detail="",
            )
        )
    return out


def open_path_in_file_manager(path: Path) -> None:
    """Öffnet einen Ordner im System-Dateimanager."""
    path = path.resolve()
    if not path.is_dir():
        path = path.parent
    if sys.platform == "win32":
        os.startfile(path)  # type: ignore[attr-defined, unused-ignore]
    elif sys.platform == "darwin":
        subprocess.run(["open", str(path)], check=False)
    else:
        subprocess.run(["xdg-open", str(path)], check=False)


def merge_path_history(hist: list[str], path: str, max_n: int = 8) -> None:
    """Aktuellen Pfad an den Anfang der Historie setzen (ohne Duplikate)."""
    p = (path or "").strip()
    if not p:
        return
    if p in hist:
        hist.remove(p)
    hist.insert(0, p)
    del hist[max_n:]


def dest_looks_like_setups_root(path: Path) -> bool:
    """Heuristik: mindestens ein direkter Unterordner ist ein bekannter iRacing-Fahrzeugordner."""
    if not path.is_dir():
        return False
    try:
        for child in path.iterdir():
            if child.is_dir() and child.name in IRACING_FOLDERS_SET:
                return True
    except OSError:
        return False
    return False


def pick_rename_destination(dest_file: Path) -> Path:
    """Freier Zielpfad mit _v2, _v3, … vor dem Dateityp, falls dest_file existiert."""
    if not dest_file.exists():
        return dest_file
    stem, suf = dest_file.stem, dest_file.suffix
    parent = dest_file.parent
    for i in range(2, 10000):
        c = parent / f"{stem}_v{i}{suf}"
        if not c.exists():
            return c
    return dest_file


def collect_sto_sources(src: Path, recursive: bool) -> list[tuple[str, Path]]:
    """Sammelt .sto-Dateien: (relativer Anzeigepfad, absolute Path)."""
    base = src.resolve()
    out: list[tuple[str, Path]] = []
    if recursive:
        for p in sorted(base.rglob("*.sto"), key=lambda x: str(x).lower()):
            out.append((p.relative_to(base).as_posix(), p))
    else:
        for p in sorted(base.iterdir(), key=lambda x: x.name.lower()):
            if p.is_file() and p.suffix.lower() == ".sto":
                out.append((p.name, p))
    return out


def load_aliases_json_file(path: Path) -> dict[str, str]:
    """Liest Alias-JSON (Liste von {alias, folder, note?}) in ein Lookup-Dict."""
    if not path.exists():
        return {}
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
        return {}
    if not isinstance(data, list):
        return {}
    out: dict[str, str] = {}
    for row in data:
        if not isinstance(row, dict):
            continue
        a = str(row.get("alias", "")).strip()
        fo = str(row.get("folder", "")).strip()
        if a and fo:
            out[a] = fo
    return out


def run_cli() -> int:
    parser = argparse.ArgumentParser(
        description="iRacing Setup Manager — Headless-Scan (keine GUI).",
    )
    parser.add_argument("--scan", action="store_true", help="Setup-Dateien planen und nach stdout melden")
    parser.add_argument("--source", type=str, required=True, help="Quellordner mit .sto")
    parser.add_argument("--dest", type=str, default="", help="iRacing setups-Stammordner (Standard: wie in der App)")
    parser.add_argument("--mode", choices=("none", "season", "track", "both"), default="none")
    parser.add_argument("--season", type=str, default="26S2")
    parser.add_argument("--recursive", action="store_true")
    parser.add_argument(
        "--aliases-file",
        type=str,
        default=str(ALIAS_FILE),
        help="JSON mit Aliassen (wie ~/.iracing_aliases.json)",
    )
    args = parser.parse_args()
    if not args.scan:
        parser.error("Derzeit nur --scan unterstützt. Beispiel: --scan --source /pfad/zu/setups")
    src = Path(args.source).expanduser()
    if not src.is_dir():
        print(f"Quelle ist kein Ordner: {src}", file=sys.stderr)
        return 1
    dest_s = args.dest.strip() or DEFAULT_DEST
    dest_base = Path(dest_s).expanduser().resolve()
    aliases = load_aliases_json_file(Path(args.aliases_file).expanduser())
    sources = collect_sto_sources(src, args.recursive)
    if not sources:
        print("Keine .sto-Dateien gefunden.")
        return 0
    plan = plan_sto_operations(dest_base, sources, aliases, args.mode, args.season)
    n_ok = sum(1 for e in plan if e.ready)
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


# ── Autocomplete-Entry ─────────────────────────────────────────────────────────
class AutoEntry(tk.Frame):
    def __init__(self, parent, textvariable, choices, width=None, **kw):
        super().__init__(parent, bg=BG_PANEL, **kw)
        self.var     = textvariable
        self.choices = choices
        self._pop    = None
        self._lb     = None
        ekw = dict(bg=BG_INPUT, fg=FG_MAIN, insertbackground=FG_MAIN,
                   relief="flat", font=FONT_UI, bd=4)
        if width:
            ekw["width"] = width
        self.entry = tk.Entry(self, textvariable=self.var, **ekw)
        self.entry.pack(fill=tk.X, expand=True)
        self.var.trace_add("write", self._on_write)
        self.entry.bind("<FocusOut>", lambda _: self.after(120, self._hide))
        self.entry.bind("<Escape>",   lambda _: self._hide())
        self.entry.bind("<Down>",     self._focus_lb)
        self.entry.bind("<Return>",   lambda _: self._hide())

    def _on_write(self, *_):
        q = self.var.get().strip().lower()
        matches = [c for c in self.choices if q in c] if q else []
        if matches: self._show(matches)
        else:       self._hide()

    def _show(self, matches):
        if self._pop: self._pop.destroy()
        x = self.entry.winfo_rootx()
        y = self.entry.winfo_rooty() + self.entry.winfo_height()
        w = max(self.entry.winfo_width(), 240)
        h = min(len(matches), 9) * 20 + 4
        self._pop = tk.Toplevel(self); self._pop.wm_overrideredirect(True)
        self._pop.wm_geometry(f"{w}x{h}+{x}+{y}")
        self._pop.configure(bg=BORDER)
        self._lb = tk.Listbox(self._pop, bg=BG_DROP, fg=FG_MAIN,
                              selectbackground=ACCENT, selectforeground="white",
                              relief="flat", font=FONT_MONO, bd=0,
                              highlightthickness=0, activestyle="none")
        self._lb.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)
        for m in matches: self._lb.insert(tk.END, m)
        self._lb.bind("<ButtonRelease-1>", self._pick)
        self._lb.bind("<Return>",          self._pick)
        self._lb.bind("<Escape>",          lambda _: self._hide())
        self._lb.bind("<FocusOut>",        lambda _: self.after(120, self._hide))

    def _pick(self, *_):
        if self._lb:
            sel = self._lb.curselection()
            if sel: self.var.set(self._lb.get(sel[0]))
        self._hide()

    def _focus_lb(self, *_):
        if self._lb: self._lb.focus_set(); self._lb.selection_set(0)

    def _hide(self, *_):
        if self._pop: self._pop.destroy(); self._pop = None; self._lb = None


# ── Alias-Datenspeicher ────────────────────────────────────────────────────────
class AliasStore:
    """Lädt/Speichert Aliase aus ~/.iracing_aliases.json."""

    def __init__(self):
        self.data: list[dict] = []
        self.load()

    def load(self):
        if ALIAS_FILE.exists():
            try:
                with open(ALIAS_FILE, encoding="utf-8") as f:
                    self.data = json.load(f)
            except Exception:
                pass
        if not self.data:
            self.data = [dict(d) for d in DEFAULT_ALIASES]
            self.save()

    def save(self):
        with open(ALIAS_FILE, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)

    def as_dict(self) -> dict[str, str]:
        """Alias → Ordner Lookup-Dict."""
        return {row["alias"]: row["folder"] for row in self.data if row.get("alias")}


# ── Alias-Editor Tab ───────────────────────────────────────────────────────────
class AliasEditor(tk.Frame):
    """
    Tabellen-Editor für persistente Auto-Aliase.
    Jede Zeile: Alias | iRacing-Ordner (Autocomplete) | Notiz | Gültig
    """

    def __init__(self, parent, store: AliasStore, **kw):
        super().__init__(parent, bg=BG_DARK, **kw)
        self.store      = store
        self._rows: list[dict] = []   # {"alias","folder","note","widgets":{}}
        self._filter_var = tk.StringVar()
        self._filter_var.trace_add("write", self._apply_filter)
        self._sel_row: int | None = None
        self._unsaved = False
        self._build()
        self._load_rows()

    # ── Layout ────────────────────────────────────────────────────────────────
    def _build(self):
        # Toolbar
        tb = tk.Frame(self, bg=BG_MID, pady=5, padx=8)
        tb.pack(fill=tk.X)
        self._tbtn(tb, "+ Alias hinzufügen", self._add_row).pack(side=tk.LEFT, padx=(0,4))
        self._tbtn(tb, "− Markierte löschen", self._delete_selected, danger=True).pack(side=tk.LEFT, padx=(0,12))
        self._tbtn(tb, "↑ Nach oben",  lambda: self._move(-1)).pack(side=tk.LEFT, padx=(0,4))
        self._tbtn(tb, "↓ Nach unten", lambda: self._move( 1)).pack(side=tk.LEFT, padx=(0,12))
        self._tbtn(tb, "💾 Speichern", self._save, primary=True).pack(side=tk.LEFT)
        self._tbtn(tb, "Export JSON…", self._export_aliases).pack(side=tk.LEFT, padx=(12, 4))
        self._tbtn(tb, "Import JSON…", self._import_aliases).pack(side=tk.LEFT, padx=(0, 4))

        self._save_lbl = tk.Label(tb, text="", bg=BG_MID, fg=FG_DIM, font=FONT_SM)
        self._save_lbl.pack(side=tk.LEFT, padx=8)

        # Filter
        tk.Label(tb, text="Filter:", bg=BG_MID, fg=FG_HEAD, font=FONT_UI).pack(side=tk.RIGHT, padx=(8,2))
        tk.Entry(tb, textvariable=self._filter_var, width=18,
                 bg=BG_INPUT, fg=FG_MAIN, insertbackground=FG_MAIN,
                 relief="flat", font=FONT_UI, bd=4).pack(side=tk.RIGHT)

        # Tabellen-Header
        hdr = tk.Frame(self, bg=BG_MID)
        hdr.pack(fill=tk.X, padx=0, pady=(4,0))
        # Checkbox-Platzhalter
        tk.Label(hdr, text="", bg=BG_MID, width=3).pack(side=tk.LEFT)
        tk.Label(hdr, text="#",  bg=BG_MID, fg=FG_DIM, font=FONT_H,
                 width=3, anchor="center").pack(side=tk.LEFT)
        for txt, w in zip(COL_HEADS, COL_WIDTHS):
            tk.Label(hdr, text=txt, bg=BG_MID, fg=FG_HEAD, font=FONT_H,
                     width=w//7, anchor="w", padx=4, pady=3).pack(side=tk.LEFT)

        # Scrollbarer Tabellenbereich
        wrap = tk.Frame(self, bg=BG_DARK)
        wrap.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)

        self.canvas = tk.Canvas(wrap, bg=BG_DARK, highlightthickness=0)
        vsb = ttk.Scrollbar(wrap, orient="vertical", command=self.canvas.yview)
        self.table  = tk.Frame(self.canvas, bg=BG_DARK)
        self._canvas_win = self.canvas.create_window((0,0), window=self.table, anchor="nw")
        self.canvas.configure(yscrollcommand=vsb.set)
        self.table.bind("<Configure>", lambda _:
            self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda e:
            self.canvas.itemconfig(self._canvas_win, width=e.width))
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.bind_all("<MouseWheel>", lambda e:
            self.canvas.yview_scroll(int(-1*e.delta/120), "units"))

        # Statusleiste
        self._status = tk.Label(self, text="", bg=BG_MID, fg=FG_DIM, font=FONT_SM,
                                anchor="w", padx=8, pady=3)
        self._status.pack(fill=tk.X, side=tk.BOTTOM)

    def _tbtn(self, p, txt, cmd, primary=False, danger=False):
        bg = ACCENT if danger else (GREEN if primary else BG_INPUT)
        return tk.Button(p, text=txt, command=cmd, bg=bg, fg="white",
                         relief="flat", font=FONT_SM, padx=8, pady=4,
                         activebackground=BORDER, activeforeground="white", cursor="hand2")

    # ── Daten ─────────────────────────────────────────────────────────────────
    def _load_rows(self):
        for r in self.store.data:
            self._append_row(r.get("alias",""), r.get("folder",""), r.get("note",""))
        self._refresh_numbers()
        self._update_status()

    def get_alias_dict(self) -> dict[str, str]:
        return {r["alias_var"].get().strip(): r["folder_var"].get().strip()
                for r in self._rows
                if r["alias_var"].get().strip() and r["folder_var"].get().strip()}

    def _collect(self) -> list[dict]:
        return [{"alias":  r["alias_var"].get().strip(),
                 "folder": r["folder_var"].get().strip(),
                 "note":   r["note_var"].get().strip()}
                for r in self._rows]

    def _save(self):
        self.store.data = self._collect()
        self.store.save()
        self._unsaved = False
        self._save_lbl.config(text="✓ gespeichert", fg=GREEN)
        self.after(2500, lambda: self._save_lbl.config(text=""))
        self._update_status()

    def _export_aliases(self):
        path = filedialog.asksaveasfilename(
            parent=self,
            title="Aliase exportieren",
            defaultextension=".json",
            filetypes=[("JSON", "*.json"), ("Alle", "*.*")],
        )
        if not path:
            return
        data = self._collect()
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except OSError as e:
            messagebox.showerror("Export", f"Schreiben fehlgeschlagen:\n{e}")
            return
        messagebox.showinfo("Export", f"{len(data)} Einträge nach\n{path}\ngeschrieben.")

    def _import_aliases(self):
        path = filedialog.askopenfilename(
            parent=self,
            title="Aliase importieren",
            filetypes=[("JSON", "*.json"), ("Alle", "*.*")],
        )
        if not path:
            return
        try:
            with open(path, encoding="utf-8") as f:
                raw = json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            messagebox.showerror("Import", f"Datei konnte nicht gelesen werden:\n{e}")
            return
        if not isinstance(raw, list):
            messagebox.showerror("Import", "Erwartet: JSON-Array von Objekten mit alias, folder, note.")
            return
        rows: list[dict] = []
        for i, item in enumerate(raw):
            if not isinstance(item, dict):
                messagebox.showerror("Import", f"Eintrag {i+1} ist kein Objekt.")
                return
            rows.append({
                "alias": str(item.get("alias", "")).strip(),
                "folder": str(item.get("folder", "")).strip(),
                "note": str(item.get("note", "")).strip(),
            })
        if not rows:
            messagebox.showinfo("Import", "Keine Einträge in der Datei.")
            return
        ans = messagebox.askyesnocancel(
            "Import",
            f"{len(rows)} Einträge gefunden.\n\n"
            "Ja = Tabelle ersetzen\nNein = anhängen\nAbbrechen = nichts tun",
        )
        if ans is None:
            return
        if ans:
            for r in list(self._rows):
                r["frame"].destroy()
            self._rows.clear()
        for row in rows:
            self._append_row(row["alias"], row["folder"], row["note"])
        self._refresh_numbers()
        self._update_status()
        self._mark_unsaved()
        self.canvas.update_idletasks()
        self.canvas.yview_moveto(1.0)

    def _mark_unsaved(self, *_):
        if not self._unsaved:
            self._unsaved = True
            self._save_lbl.config(text="● nicht gespeichert", fg=YELLOW)

    # ── Zeilen-Verwaltung ─────────────────────────────────────────────────────
    def _append_row(self, alias="", folder="", note=""):
        idx   = len(self._rows)
        bg    = BG_ROW_A if idx % 2 == 0 else BG_ROW_B
        frame = tk.Frame(self.table, bg=bg, pady=1)
        frame.pack(fill=tk.X, pady=0)

        alias_var  = tk.StringVar(value=alias)
        folder_var = tk.StringVar(value=folder)
        note_var   = tk.StringVar(value=note)
        sel_var    = tk.BooleanVar(value=False)

        # Zeilenhöhe für besser lesbare Eingabe
        row_ipady = 4

        # Checkbox
        cb = tk.Checkbutton(frame, variable=sel_var, bg=bg,
                            activebackground=bg, selectcolor=BG_INPUT,
                            relief="flat", bd=0, fg="white",
                            activeforeground="white", font=FONT_BOLD)
        cb.pack(side=tk.LEFT, padx=(4,0))

        # Zeilennummer
        num_lbl = tk.Label(frame, text=str(idx+1), bg=bg, fg=FG_DIM,
                           font=FONT_SM, width=3, anchor="center")
        num_lbl.pack(side=tk.LEFT)

        ekw = dict(bg=BG_INPUT, fg=FG_MAIN, insertbackground=FG_MAIN,
                   relief="flat", font=FONT_UI, bd=3)

        # Alias
        alias_e = tk.Entry(frame, textvariable=alias_var, width=COL_WIDTHS[0]//7, **ekw)
        alias_e.pack(side=tk.LEFT, padx=2, pady=2, ipady=row_ipady)

        # Ordner (Autocomplete)
        folder_frame = tk.Frame(frame, bg=bg, width=COL_WIDTHS[1], height=30)
        folder_frame.pack(side=tk.LEFT, padx=2, pady=2)
        folder_frame.pack_propagate(False)
        folder_ae = AutoEntry(folder_frame, folder_var, IRACING_FOLDERS)
        folder_ae.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)

        # Notiz
        note_e = tk.Entry(frame, textvariable=note_var, width=COL_WIDTHS[2]//7, **ekw)
        note_e.pack(side=tk.LEFT, padx=2, pady=2, ipady=row_ipady)

        # Gültigkeits-Indikator
        valid_lbl = tk.Label(frame, text="", bg=bg, font=FONT_SM, width=2)
        valid_lbl.pack(side=tk.LEFT, padx=(0,4))

        def upd_valid(*_):
            v = folder_var.get().strip()
            if v in IRACING_FOLDERS: valid_lbl.config(text="✓", fg=GREEN)
            elif v:                  valid_lbl.config(text="?", fg=YELLOW)
            else:                    valid_lbl.config(text="",  fg=FG_DIM)

        folder_var.trace_add("write", upd_valid)
        alias_var.trace_add("write",  self._mark_unsaved)
        folder_var.trace_add("write", self._mark_unsaved)
        note_var.trace_add("write",   self._mark_unsaved)
        upd_valid()

        row = {
            "frame": frame, "bg": bg,
            "alias_var": alias_var, "folder_var": folder_var, "note_var": note_var,
            "sel_var": sel_var, "num_lbl": num_lbl, "valid_lbl": valid_lbl,
        }
        self._rows.append(row)
        return row

    def _add_row(self):
        self._append_row()
        self._refresh_numbers()
        self._update_status()
        self._mark_unsaved()
        # Scroll to bottom
        self.canvas.update_idletasks()
        self.canvas.yview_moveto(1.0)

    def _delete_selected(self):
        to_del = [r for r in self._rows if r["sel_var"].get()]
        if not to_del:
            messagebox.showinfo("Hinweis", "Keine Zeilen markiert (Checkbox links).")
            return
        if not messagebox.askyesno("Löschen", f"{len(to_del)} Alias(e) wirklich löschen?"):
            return
        for r in to_del:
            r["frame"].destroy()
            self._rows.remove(r)
        self._refresh_numbers()
        self._update_status()
        self._mark_unsaved()

    def _move(self, direction: int):
        selected = [i for i, r in enumerate(self._rows) if r["sel_var"].get()]
        if not selected: return
        if direction == -1 and selected[0] == 0: return
        if direction ==  1 and selected[-1] == len(self._rows)-1: return
        for i in (selected if direction == 1 else reversed(selected)):
            j = i + direction
            self._rows[i], self._rows[j] = self._rows[j], self._rows[i]
        # Neuaufbau der Frames in richtiger Reihenfolge
        for r in self._rows:
            r["frame"].pack_forget()
        for r in self._rows:
            r["frame"].pack(fill=tk.X)
        self._refresh_numbers()
        self._mark_unsaved()

    def _refresh_numbers(self):
        for i, r in enumerate(self._rows):
            r["num_lbl"].config(text=str(i+1))
            bg = BG_ROW_A if i % 2 == 0 else BG_ROW_B
            r["frame"].config(bg=bg)
            r["bg"] = bg

    def _apply_filter(self, *_):
        q = self._filter_var.get().strip().lower()
        for r in self._rows:
            alias  = r["alias_var"].get().lower()
            folder = r["folder_var"].get().lower()
            note   = r["note_var"].get().lower()
            show   = not q or q in alias or q in folder or q in note
            if show: r["frame"].pack(fill=tk.X)
            else:    r["frame"].pack_forget()

    def _update_status(self):
        total   = len(self._rows)
        valid   = sum(1 for r in self._rows if r["folder_var"].get().strip() in IRACING_FOLDERS)
        invalid = sum(1 for r in self._rows if r["folder_var"].get().strip()
                      and r["folder_var"].get().strip() not in IRACING_FOLDERS)
        parts = [f"{total} Aliase  ·  {valid} ✓ gültig"]
        if invalid: parts.append(f"  {invalid} ⚠ unbekannter Ordner")
        self._status.config(text="  ".join(parts))


# ── Kopier-Tab ─────────────────────────────────────────────────────────────────
class CopyTab(tk.Frame):
    def __init__(self, parent, alias_editor: AliasEditor, **kw):
        super().__init__(parent, bg=BG_DARK, **kw)
        self.alias_editor = alias_editor
        self.source_var = tk.StringVar()
        self.dest_var   = tk.StringVar()
        self.mode_var   = tk.StringVar(value="none")
        self.season_var = tk.StringVar()
        self.move_var   = tk.BooleanVar(value=False)
        self.recursive_var = tk.BooleanVar(value=False)
        self.dry_run_var = tk.BooleanVar(value=False)
        self.backup_var = tk.BooleanVar(value=True)
        self.collision_var = tk.StringVar(value="overwrite")
        self._source_history: list[str] = []
        self._dest_history: list[str] = []
        self._source_combo: ttk.Combobox | None = None
        self._dest_combo: ttk.Combobox | None = None
        self._last_plan: list[StoPlanEntry] = []
        self._build()

    def _build(self):
        pad = dict(padx=10, pady=5)

        # Verzeichnisse
        self._sec("VERZEICHNISSE").pack(fill=tk.X, **pad)
        df = tk.Frame(self, bg=BG_PANEL, pady=8, padx=8)
        df.pack(fill=tk.X, padx=10, pady=(0,6))
        self._dir_row_combo(df, "Quelle  (neue Setups):", self.source_var, self._browse_src, "source")
        self._dir_row_combo(df, "Ziel      (iRacing Setups):", self.dest_var, self._browse_dst, "dest")

        cf = tk.Frame(self, bg=BG_PANEL, padx=10, pady=8)
        cf.pack(fill=tk.X, padx=10, pady=(0, 6))
        self._sec("BEI VORHANDENEM ZIEL (GLEICHER DATEINAME)", cf).pack(anchor="w", pady=(0, 4))
        cr = tk.Frame(cf, bg=BG_PANEL)
        cr.pack(anchor="w")
        for lbl, val in [
            ("Überschreiben", "overwrite"),
            ("Überspringen", "skip"),
            ("Umbenennen (_v2 …)", "rename"),
        ]:
            ttk.Radiobutton(
                cr, text=lbl, variable=self.collision_var, value=val,
            ).pack(side=tk.LEFT, padx=(0, 12))

        # Modus + Season
        mid = tk.Frame(self, bg=BG_DARK)
        mid.pack(fill=tk.X, **pad)

        mp = tk.Frame(mid, bg=BG_PANEL, padx=12, pady=8)
        mp.pack(side=tk.LEFT, fill=tk.Y, padx=(0,8))
        self._sec("UNTERORDNER-MODUS", mp).pack(anchor="w", pady=(0,6))
        for lbl, val in [("Kein Unterordner","none"),("Season","season"),
                          ("Strecke","track"),("Season  +  Strecke","both")]:
            ttk.Radiobutton(mp, text=lbl, variable=self.mode_var,
                            value=val, command=self._upd_season).pack(anchor="w", pady=2)

        sp = tk.Frame(mid, bg=BG_PANEL, padx=12, pady=8)
        sp.pack(side=tk.LEFT, fill=tk.Y)
        self._sec("SEASON-NAME", sp).pack(anchor="w", pady=(0,6))
        self.season_entry = tk.Entry(sp, textvariable=self.season_var, width=14,
                                     bg=BG_INPUT, fg=FG_MAIN, insertbackground=FG_MAIN,
                                     relief="flat", font=("Segoe UI",11,"bold"), bd=6)
        self.season_entry.pack(anchor="w")
        tk.Label(sp, text="z.B. 26S2, 26S3 …",
                 bg=BG_PANEL, fg=FG_DIM, font=FONT_SM).pack(anchor="w", pady=(4,0))

        # Aktions-Leiste
        ab = tk.Frame(self, bg=BG_MID, pady=6, padx=10)
        ab.pack(fill=tk.X)
        self._abtn(ab, "🔍  Scannen", self._scan, ACCENT).pack(side=tk.LEFT, padx=(0,6))
        self._abtn(ab, "➕  Fehlende Aliase", self._alias_assistant, BG_INPUT).pack(
            side=tk.LEFT, padx=(0, 6),
        )

        self._exec_btn = self._abtn(ab, "📋  Kopieren", self._copy, GREEN)
        self._exec_btn.pack(side=tk.LEFT, padx=(0,12))

        # Kopieren / Verschieben Toggle
        toggle_frame = tk.Frame(ab, bg=BG_MID)
        toggle_frame.pack(side=tk.LEFT)
        tk.Label(toggle_frame, text="Modus:", bg=BG_MID, fg=FG_HEAD,
                 font=FONT_SM).pack(side=tk.LEFT, padx=(0,6))
        for lbl, val in [("Kopieren", False), ("Verschieben", True)]:
            ttk.Radiobutton(toggle_frame, text=lbl, variable=self.move_var,
                            value=val, command=self._upd_exec_btn).pack(side=tk.LEFT, padx=(0,4))

        opt = tk.Frame(ab, bg=BG_MID)
        opt.pack(side=tk.LEFT, padx=(16, 0))
        tk.Checkbutton(
            opt, text="Rekursiv scannen", variable=self.recursive_var,
            bg=BG_MID, fg=FG_MAIN, selectcolor=BG_INPUT, activebackground=BG_MID,
            activeforeground=FG_MAIN, font=FONT_SM,
        ).pack(side=tk.LEFT, padx=(0, 8))
        tk.Checkbutton(
            opt, text="Nur Vorschau (Dry-Run)", variable=self.dry_run_var,
            bg=BG_MID, fg=FG_MAIN, selectcolor=BG_INPUT, activebackground=BG_MID,
            activeforeground=FG_MAIN, font=FONT_SM,
        ).pack(side=tk.LEFT, padx=(0, 8))
        tk.Checkbutton(
            opt, text="Backup vor Überschreiben", variable=self.backup_var,
            bg=BG_MID, fg=FG_MAIN, selectcolor=BG_INPUT, activebackground=BG_MID,
            activeforeground=FG_MAIN, font=FONT_SM,
        ).pack(side=tk.LEFT, padx=(0, 4))

        tk.Label(ab, text="Aliase aus Editor-Tab", bg=BG_MID,
                 fg=FG_DIM, font=FONT_SM).pack(side=tk.RIGHT, padx=8)

        # Ergebnis-Tabelle + Log
        self._sec("ERGEBNIS").pack(fill=tk.X, padx=10, pady=(8, 2))
        paned = tk.PanedWindow(self, orient=tk.VERTICAL, bg=BG_DARK, sashwidth=5,
                               sashrelief=tk.FLAT, bd=0)
        paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 4))

        twrap = tk.Frame(paned, bg=BG_DARK)
        cols = ("status", "file", "fmt", "car", "folder", "dest")
        self._results_tree = ttk.Treeview(
            twrap, columns=cols, show="headings", height=8, style="Copy.Treeview",
        )
        headings = [
            ("status", "Status", 100),
            ("file", "Datei", 220),
            ("fmt", "Fmt", 36),
            ("car", "Auto (Alias)", 120),
            ("folder", "iRacing-Ordner", 140),
            ("dest", "Zielpfad", 360),
        ]
        for cid, text, w in headings:
            self._results_tree.heading(cid, text=text)
            self._results_tree.column(cid, width=w, minwidth=40, stretch=(cid == "dest"))
        tvsb = ttk.Scrollbar(twrap, orient="vertical", command=self._results_tree.yview)
        thsb = ttk.Scrollbar(twrap, orient="horizontal", command=self._results_tree.xview)
        self._results_tree.configure(yscrollcommand=tvsb.set, xscrollcommand=thsb.set)
        self._results_tree.grid(row=0, column=0, sticky="nsew")
        tvsb.grid(row=0, column=1, sticky="ns")
        thsb.grid(row=1, column=0, sticky="ew")
        twrap.grid_rowconfigure(0, weight=1)
        twrap.grid_columnconfigure(0, weight=1)
        self._results_tree.bind("<Double-1>", self._on_results_double_click)
        self._results_tree.tag_configure("ready", foreground=GREEN)
        self._results_tree.tag_configure("warn", foreground=YELLOW)
        self._results_tree.tag_configure("err", foreground=ACCENT)
        self._results_tree.tag_configure("dim", foreground=FG_DIM)
        paned.add(twrap, minsize=100)

        lw = tk.Frame(paned, bg=BG_MID)
        tk.Label(lw, text="LOG", bg=BG_MID, fg=ACCENT,
                 font=("Segoe UI", 8, "bold")).pack(fill=tk.X, padx=6, pady=(4, 2))
        self.log = tk.Text(lw, bg=BG_MID, fg=FG_MAIN, font=FONT_MONO,
                           relief="flat", state=tk.DISABLED, wrap="none",
                           insertbackground=FG_MAIN, selectbackground=BORDER)
        self.log.tag_configure("ok",    foreground=GREEN)
        self.log.tag_configure("warn",  foreground=YELLOW)
        self.log.tag_configure("error", foreground=ACCENT)
        self.log.tag_configure("dim",   foreground=FG_DIM)
        self.log.tag_configure("head",  foreground=FG_HEAD)
        vsb = ttk.Scrollbar(lw, orient="vertical",   command=self.log.yview)
        hsb = ttk.Scrollbar(lw, orient="horizontal", command=self.log.xview)
        self.log.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        vsb.pack(side=tk.RIGHT,  fill=tk.Y)
        hsb.pack(side=tk.BOTTOM, fill=tk.X)
        self.log.pack(fill=tk.BOTH, expand=True)
        paned.add(lw, minsize=120)

    # ── Widgets ───────────────────────────────────────────────────────────────
    def _sec(self, txt, parent=None):
        p = parent or self
        bg = p["bg"] if hasattr(p,"keys") else BG_DARK
        return tk.Label(p, text=txt, bg=bg, fg=ACCENT, font=("Segoe UI",8,"bold"))

    def _dir_row_combo(self, p, lbl, var, cmd, which: str):
        row = tk.Frame(p, bg=BG_PANEL)
        row.pack(fill=tk.X, pady=3)
        tk.Label(row, text=lbl, bg=BG_PANEL, fg=FG_HEAD,
                 font=FONT_UI, width=26, anchor="w").pack(side=tk.LEFT)
        combo = ttk.Combobox(
            row,
            textvariable=var,
            values=[],
            style="Dark.TCombobox",
            font=FONT_UI,
        )
        combo.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=6)
        tk.Button(row, text="  …  ", command=cmd, bg=BG_INPUT, fg=FG_MAIN,
                  relief="flat", font=FONT_UI, activebackground=BORDER,
                  activeforeground=FG_MAIN, cursor="hand2").pack(side=tk.LEFT)
        if which == "source":
            self._source_combo = combo
        else:
            self._dest_combo = combo

    def _sync_history_combos(self) -> None:
        if self._source_combo is not None:
            self._source_combo["values"] = self._source_history
        if self._dest_combo is not None:
            self._dest_combo["values"] = self._dest_history

    def merge_recent_paths_for_save(self) -> None:
        merge_path_history(self._source_history, self.source_var.get())
        merge_path_history(self._dest_history, self.dest_var.get())
        self._sync_history_combos()

    def _abtn(self, p, txt, cmd, bg):
        return tk.Button(p, text=txt, command=cmd, bg=bg, fg="white",
                         relief="flat", font=FONT_BOLD, padx=14, pady=5,
                         activebackground=BORDER, activeforeground="white", cursor="hand2")

    def _browse_src(self):
        d = filedialog.askdirectory(initialdir=self.source_var.get() or str(Path.home()))
        if d:
            self.source_var.set(d)
            merge_path_history(self._source_history, d)
            self._sync_history_combos()

    def _browse_dst(self):
        d = filedialog.askdirectory(initialdir=self.dest_var.get() or str(Path.home()))
        if d:
            self.dest_var.set(d)
            merge_path_history(self._dest_history, d)
            self._sync_history_combos()

    def _upd_exec_btn(self):
        if self.move_var.get():
            self._exec_btn.config(text="✂  Verschieben", bg=YELLOW)
        else:
            self._exec_btn.config(text="📋  Kopieren", bg=GREEN)

    def _upd_season(self):
        state = tk.NORMAL if self.mode_var.get() in ("season","both") else tk.DISABLED
        self.season_entry.config(state=state,
                                 fg=FG_MAIN if state == tk.NORMAL else FG_DIM)

    # ── Log ───────────────────────────────────────────────────────────────────
    def _wlog(self, msg, tag=""):
        self.log.config(state=tk.NORMAL)
        self.log.insert(tk.END, msg+"\n", tag)
        self.log.see(tk.END)
        self.log.config(state=tk.DISABLED)

    def _clear_log(self):
        self.log.config(state=tk.NORMAL)
        self.log.delete(1.0, tk.END)
        self.log.config(state=tk.DISABLED)

    # ── Pfad-Logik ────────────────────────────────────────────────────────────
    def _build_dest(self, folder, track, mode) -> Path:
        return build_dest_path(
            Path(self.dest_var.get()), folder, track, mode, self.season_var.get(),
        )

    def _build_dest_resolved(self, dest_base: Path, folder, track, mode) -> Path:
        return build_dest_path(dest_base, folder, track, mode, self.season_var.get())

    def _get_sto_sources(self) -> list[tuple[str, Path]] | None:
        """(Anzeigepfad, absolute Path). None bei fehlendem Quellordner (Dialog bereits gezeigt)."""
        src = self.source_var.get()
        if not os.path.isdir(src):
            messagebox.showerror("Fehler", f"Quellverzeichnis nicht gefunden:\n{src}")
            return None
        return collect_sto_sources(Path(src), self.recursive_var.get())

    def _status_display(self, status: str) -> str:
        return {
            "ready": "bereit",
            "bad_format": "Format?",
            "no_alias": "kein Alias",
            "duplicate_name": "doppelt",
        }.get(status, status)

    def _fill_results_tree(self, entries: list[StoPlanEntry]) -> None:
        self._results_tree.delete(*self._results_tree.get_children())
        for i, e in enumerate(entries):
            car = e.car or "—"
            folder = e.iracing_folder or "—"
            dest = str(e.dest_file) if e.dest_file else (e.detail or "—")
            if e.ready:
                tag = "ready"
            elif e.status == "bad_format":
                tag = "err"
            else:
                tag = "warn"
            self._results_tree.insert(
                "",
                tk.END,
                iid=str(i),
                values=(
                    self._status_display(e.status),
                    e.rel_display,
                    e.format_label,
                    car,
                    folder,
                    dest,
                ),
                tags=(tag,),
            )

    def _on_results_double_click(self, _event=None) -> None:
        sel = self._results_tree.selection()
        if not sel:
            return
        try:
            idx = int(sel[0])
        except ValueError:
            return
        if idx < 0 or idx >= len(self._last_plan):
            return
        e = self._last_plan[idx]
        target = e.dest_file if e.dest_file else e.src_file
        try:
            open_path_in_file_manager(target)
        except OSError:
            pass

    def _compute_plan(self, require_dest_exists: bool) -> list[StoPlanEntry] | None:
        sources = self._get_sto_sources()
        if sources is None:
            return None
        if not sources:
            self._last_plan = []
            return []
        dest_base = Path(self.dest_var.get()).resolve()
        if require_dest_exists and not dest_base.exists():
            messagebox.showerror("Fehler", f"Zielverzeichnis existiert nicht:\n{dest_base}")
            return None
        aliases = self.alias_editor.get_alias_dict()
        plan = plan_sto_operations(
            dest_base, sources, aliases, self.mode_var.get(), self.season_var.get(),
        )
        self._last_plan = plan
        return plan

    def _backup_file_if_needed(self, dest_file: Path) -> None:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        bak = dest_file.parent / f"{dest_file.name}.{ts}.bak"
        shutil.copy2(dest_file, bak)

    def _validate(self) -> bool:
        if self.mode_var.get() in ("season", "both") and not self.season_var.get().strip():
            messagebox.showerror("Fehler", "Bitte Season-Name eingeben.")
            return False
        return True

    def _confirm_dest_root(self, dest_base: Path) -> bool:
        if not dest_base.exists():
            return True
        if dest_looks_like_setups_root(dest_base):
            return True
        return messagebox.askokcancel(
            "Ziel prüfen",
            "Unter dem Ziel wurden keine bekannten iRacing-Fahrzeugordner gefunden.\n"
            "Erwartet wird meist der Ordner „setups“ mit Unterordnern wie „bmwm4gt3“ usw.\n\n"
            "Trotzdem kopieren bzw. verschieben?",
            icon="warning",
        )

    def _alias_assistant(self) -> None:
        cars_ordered: list[str] = []
        seen: set[str] = set()
        for e in self._last_plan:
            if e.status == "no_alias" and e.car and e.car not in seen:
                seen.add(e.car)
                cars_ordered.append(e.car)
        if not cars_ordered:
            messagebox.showinfo(
                "Fehlende Aliase",
                "Zuerst „Scannen“ ausführen — oder es gibt keine fehlenden Aliase im Plan.",
            )
            return
        existing = self.alias_editor.get_alias_dict()
        added = 0
        for car in cars_ordered:
            if car in existing:
                continue
            self.alias_editor._append_row(car, "", "Scan")
            added += 1
        if added == 0:
            messagebox.showinfo(
                "Fehlende Aliase",
                "Alle erkannten Fahrzeug-Aliase sind bereits mit Ordner eingetragen.",
            )
            return
        self.alias_editor._refresh_numbers()
        self.alias_editor._update_status()
        self.alias_editor._mark_unsaved()
        self.alias_editor.canvas.update_idletasks()
        self.alias_editor.canvas.yview_moveto(1.0)
        self.master.select(self.alias_editor)
        messagebox.showinfo(
            "Fehlende Aliase",
            f"{added} neue Zeile(n) im Alias-Editor.\n"
            "Bitte iRacing-Ordner zuweisen und speichern.",
        )

    # ── Aktionen ──────────────────────────────────────────────────────────────
    def _scan(self):
        if not self._validate():
            return
        self._clear_log()
        plan = self._compute_plan(require_dest_exists=False)
        if plan is None:
            return
        self._fill_results_tree(plan)
        if not plan:
            self._wlog("Keine .sto Dateien gefunden.", "warn")
            return
        aliases = self.alias_editor.get_alias_dict()
        self._wlog(
            f"━━  Scan  ·  {len(plan)} Datei(en)  ·  {len(aliases)} Aliase geladen  ━━",
            "head",
        )
        n_ready = sum(1 for e in plan if e.ready)
        n_skip = len(plan) - n_ready
        for e in plan:
            if e.ready:
                self._wlog(f"  ✓  [Fmt-{e.format_label}]  {e.rel_display}", "ok")
                self._wlog(
                    f"       {e.car} → {e.iracing_folder}   "
                    f"Strecke: {e.track}   Season: {e.season}",
                    "dim",
                )
                self._wlog(f"       → {e.dest_file}", "dim")
            elif e.status == "bad_format":
                self._wlog(f"  ⚠  Unbekanntes Format: {e.rel_display}", "warn")
            elif e.status == "no_alias":
                self._wlog(
                    f"  ⚠  Kein Alias für '{e.car}': {e.rel_display}",
                    "warn",
                )
            else:
                self._wlog(f"  ⚠  {e.detail}: {e.rel_display}", "warn")
        self._wlog(f"\n  → {n_ready} bereit  ·  {n_skip} übersprungen", "head")

    def _copy(self):
        if not self._validate():
            return
        self._clear_log()
        plan = self._compute_plan(require_dest_exists=True)
        if plan is None:
            return
        self._fill_results_tree(plan)
        if not plan:
            self._wlog("Keine .sto Dateien gefunden.", "warn")
            return

        moving = self.move_var.get()
        dry = self.dry_run_var.get()
        aliases = self.alias_editor.get_alias_dict()
        src_base = Path(self.source_var.get()).resolve()
        dest_base = Path(self.dest_var.get()).resolve()
        ready_entries = [e for e in plan if e.ready]

        if moving and not dry and not messagebox.askyesno(
            "Verschieben bestätigen",
            f"{len(ready_entries)} Datei(en) werden aus dem Quellordner entfernt.\n\nFortfahren?",
        ):
            return

        if not dry and not self._confirm_dest_root(dest_base):
            return

        verb = "Verschieben" if moving else "Kopieren"
        if dry:
            verb = "Vorschau (" + verb + ")"
        self._wlog(f"━━  {verb}  ·  {len(aliases)} Aliase aktiv  ━━", "head")
        self._wlog(f"  Quelle: {src_base}", "dim")
        self._wlog(f"  Ziel:   {dest_base}", "dim")
        if dry:
            self._wlog("  (Dry-Run: keine Dateien geändert)", "head")

        ok = skip = ow = coll_skip = 0
        collision = self.collision_var.get()
        for e in plan:
            if not e.ready:
                if e.status == "bad_format":
                    self._wlog(f"  ⚠  Unbekanntes Format: {e.rel_display}", "warn")
                elif e.status == "no_alias":
                    self._wlog(
                        f"  ⚠  Kein Alias für '{e.car}' — im Alias-Editor eintragen: {e.rel_display}",
                        "warn",
                    )
                else:
                    self._wlog(f"  ⚠  {e.detail}: {e.rel_display}", "warn")
                skip += 1
                continue

            src_file = e.src_file
            dest_file = e.dest_file
            assert dest_file is not None
            existed = dest_file.exists()
            final_dest = dest_file

            if existed and collision == "skip":
                if dry:
                    self._wlog(f"  ◌  {e.rel_display}", "warn")
                    self._wlog("       übersprungen — Ziel existiert bereits", "dim")
                else:
                    self._wlog(f"  ◌  {e.rel_display}  (übersprungen, Ziel existiert)", "warn")
                coll_skip += 1
                continue

            if existed and collision == "rename":
                final_dest = pick_rename_destination(dest_file)

            if dry:
                self._wlog(f"  ◇  {e.rel_display}", "ok")
                self._wlog(f"       → {final_dest}", "dim")
                if existed and collision == "overwrite":
                    self._wlog("       (würde überschreiben)", "warn")
                    ow += 1
                elif existed and collision == "rename" and final_dest != dest_file:
                    self._wlog("       (neuer Name wegen Kollision)", "dim")
                ok += 1
                continue

            try:
                os.makedirs(final_dest.parent, exist_ok=True)
                if existed and collision == "overwrite" and self.backup_var.get():
                    self._backup_file_if_needed(dest_file)
                if moving:
                    shutil.move(str(src_file), str(final_dest))
                else:
                    shutil.copy2(str(src_file), str(final_dest))
                if not final_dest.exists():
                    raise FileNotFoundError(
                        f"Datei nach der Operation nicht vorhanden: {final_dest}",
                    )
                overwritten = existed and collision == "overwrite"
                renamed = existed and collision == "rename" and final_dest != dest_file
                icon = "✂" if moving else ("♻" if overwritten else ("⎘" if renamed else "✓"))
                tag = "warn" if overwritten else "ok"
                self._wlog(f"  {icon}  {e.rel_display}", tag)
                self._wlog(f"       → {final_dest}", "dim")
                ok += 1
                if overwritten:
                    ow += 1
            except Exception as ex:
                self._wlog(f"  ✗  {e.rel_display}: {ex}", "error")
                skip += 1

        verb_past = "verschoben" if moving else "kopiert"
        tail = f"{skip} übersprungen"
        if coll_skip:
            tail += f"  ·  {coll_skip} Kollision übersprungen"
        if dry:
            self._wlog(f"\n  → {ok} geplant  ({ow} Überschreiben)  ·  {tail}", "head")
            messagebox.showinfo(
                "Dry-Run",
                f"{ok} Operation(en) würden ausgeführt.\n"
                f"{ow} würden ein vorhandenes Ziel überschreiben.\n"
                f"{coll_skip} wegen „Überspringen“ bei Kollision.\n"
                f"{skip} wegen Format/Alias/Duplikat.",
            )
        else:
            self._wlog(
                f"\n  → {ok} {verb_past}  ({ow} überschrieben)  ·  {tail}",
                "head",
            )


# ── Haupt-App ──────────────────────────────────────────────────────────────────
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("iRacing Setup Manager")
        self.configure(bg=BG_DARK)
        self.minsize(880, 680)
        self.geometry("980x780")

        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TScrollbar", background=BG_INPUT, troughcolor=BG_DARK, bordercolor=BG_DARK)
        style.configure("TRadiobutton", background=BG_PANEL, foreground=FG_MAIN,
                        font=FONT_UI, focuscolor=BG_PANEL)
        style.map("TRadiobutton", background=[("active", BG_PANEL)])
        style.configure("Dark.TNotebook",         background=BG_DARK, borderwidth=0)
        style.configure("Dark.TNotebook.Tab",     background=BG_MID,  foreground=FG_DIM,
                        font=FONT_BOLD, padding=[14,6], borderwidth=0)
        style.map("Dark.TNotebook.Tab",
                  background=[("selected", BG_PANEL), ("active", BG_INPUT)],
                  foreground=[("selected", FG_MAIN),  ("active", FG_MAIN)])
        style.configure(
            "Copy.Treeview",
            background=BG_MID,
            foreground=FG_MAIN,
            fieldbackground=BG_MID,
            font=FONT_SM,
        )
        style.configure("Copy.Treeview.Heading", background=BG_PANEL, foreground=FG_HEAD)
        style.map("Copy.Treeview", background=[("selected", BG_SEL)])
        style.configure(
            "Dark.TCombobox",
            fieldbackground=BG_INPUT,
            background=BG_INPUT,
            foreground=FG_MAIN,
            arrowcolor=FG_MAIN,
        )
        style.map("Dark.TCombobox", fieldbackground=[("readonly", BG_INPUT)])

        self._build()
        self._load_config()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build(self):
        # Titelleiste
        tb = tk.Frame(self, bg=BG_MID)
        tb.pack(fill=tk.X)
        tk.Label(tb, text="  ⬛  ", bg=ACCENT, fg="white",
                 font=("Segoe UI",13,"bold"), pady=6).pack(side=tk.LEFT)
        tk.Label(tb, text="iRacing Setup Manager", bg=BG_MID, fg=FG_MAIN,
                 font=("Segoe UI",12,"bold"), pady=8, padx=10).pack(side=tk.LEFT)
        tk.Label(tb, text="Format A & B  ·  .sto",
                 bg=BG_MID, fg=FG_DIM, font=FONT_SM, pady=8).pack(side=tk.LEFT)

        # Notebook
        self.nb = ttk.Notebook(self, style="Dark.TNotebook")
        self.nb.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)

        self.store  = AliasStore()
        self.alias_tab = AliasEditor(self.nb, self.store)
        self.copy_tab  = CopyTab(self.nb, self.alias_tab)

        self.nb.add(self.copy_tab,  text="  📋  Setup Kopieren  ")
        self.nb.add(self.alias_tab, text="  🏎  Alias Editor  ")

    # ── Config (nur Copy-Tab-Einstellungen) ────────────────────────────────────
    def _load_config(self):
        cfg = {}
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, encoding="utf-8") as f:
                    cfg = json.load(f)
            except Exception:
                pass
        self.copy_tab.source_var.set(cfg.get("source", DEFAULT_SOURCE))
        self.copy_tab.dest_var.set(cfg.get("dest",     DEFAULT_DEST))
        self.copy_tab.mode_var.set(cfg.get("mode",     "none"))
        self.copy_tab.season_var.set(cfg.get("season", "26S2"))
        self.copy_tab.move_var.set(cfg.get("move",     False))
        self.copy_tab.recursive_var.set(cfg.get("recursive", False))
        self.copy_tab.dry_run_var.set(cfg.get("dry_run", False))
        self.copy_tab.backup_var.set(cfg.get("backup", True))
        sh = cfg.get("source_history", [])
        if isinstance(sh, list):
            self.copy_tab._source_history = [str(x) for x in sh if isinstance(x, str)][:8]
        dh = cfg.get("dest_history", [])
        if isinstance(dh, list):
            self.copy_tab._dest_history = [str(x) for x in dh if isinstance(x, str)][:8]
        col = cfg.get("collision", "overwrite")
        if col in ("overwrite", "skip", "rename"):
            self.copy_tab.collision_var.set(col)
        self.copy_tab._sync_history_combos()
        self.copy_tab._upd_season()
        self.copy_tab._upd_exec_btn()

    def _save_config(self):
        self.copy_tab.merge_recent_paths_for_save()
        cfg = {
            "source": self.copy_tab.source_var.get(),
            "dest":   self.copy_tab.dest_var.get(),
            "mode":   self.copy_tab.mode_var.get(),
            "season": self.copy_tab.season_var.get(),
            "move":   self.copy_tab.move_var.get(),
            "recursive": self.copy_tab.recursive_var.get(),
            "dry_run": self.copy_tab.dry_run_var.get(),
            "backup": self.copy_tab.backup_var.get(),
            "collision": self.copy_tab.collision_var.get(),
            "source_history": self.copy_tab._source_history,
            "dest_history": self.copy_tab._dest_history,
        }
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(cfg, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    def _on_close(self):
        if self.alias_tab._unsaved:
            ans = messagebox.askyesnocancel(
                "Nicht gespeichert",
                "Im Alias-Editor gibt es ungespeicherte Änderungen.\n\nJetzt speichern?")
            if ans is None:   return          # Abbrechen
            if ans:           self.alias_tab._save()
        self._save_config()
        self.destroy()


# Starter-Aliase
DEFAULT_ALIASES: list[dict] = [
    {"alias": "AudiTCRGen2",    "folder": "audirs3lmsgen2",     "note": "HYMO/SimuCube"},
    {"alias": "RS3Gen2",        "folder": "audirs3lmsgen2",     "note": "VRS"},
    {"alias": "AudiR8",         "folder": "audir8lmsevo2gt3",   "note": ""},
    {"alias": "GR86",           "folder": "toyotagr86",         "note": ""},
    {"alias": "MX5Cup",         "folder": "mx5 cup",            "note": ""},
    {"alias": "Ferrari296",     "folder": "ferrari296gt3",      "note": ""},
    {"alias": "Ferrari488",     "folder": "ferrari488gte",      "note": ""},
    {"alias": "Ferrari499",     "folder": "ferrari499p",        "note": ""},
    {"alias": "McLaren720",     "folder": "mclaren720sgt3",     "note": ""},
    {"alias": "McLaren570",     "folder": "mclaren570sgt4",     "note": ""},
    {"alias": "Porsche992GT3",  "folder": "porsche992rgt3",     "note": ""},
    {"alias": "Porsche992Cup",  "folder": "porsche992cup",      "note": ""},
    {"alias": "Porsche9922Cup", "folder": "porsche9922cup",     "note": ""},
    {"alias": "Porsche963",     "folder": "porsche963gtp",      "note": ""},
    {"alias": "BMWM4GT3",       "folder": "bmwm4gt3",           "note": ""},
    {"alias": "BMWM4GT4",       "folder": "bmwm4gt4",           "note": ""},
    {"alias": "BMWM4EvoGT4",    "folder": "bmwm4evogt4",        "note": ""},
    {"alias": "BMWM8GTE",       "folder": "bmwm8gte",           "note": ""},
    {"alias": "MercedesAMGGT3", "folder": "mercedesamgevogt3",  "note": ""},
    {"alias": "MercedesAMGGT4", "folder": "mercedesamggt4",     "note": ""},
    {"alias": "LamborghiniGT3", "folder": "lamborghinievogt3",  "note": ""},
    {"alias": "AcuraGTP",       "folder": "acuraarx06gtp",      "note": ""},
    {"alias": "AcuraNSX",       "folder": "acuransxevo22gt3",   "note": ""},
    {"alias": "CadillacGTP",    "folder": "cadillacvseriesrgtp","note": ""},
    {"alias": "FordMustangGT3", "folder": "fordmustanggt3",     "note": ""},
    {"alias": "FordMustangGT4", "folder": "fordmustanggt4",     "note": ""},
    {"alias": "Corvette",       "folder": "c8rvettegte",        "note": ""},
    {"alias": "CorvetteZ06",    "folder": "chevyvettez06rgt3",  "note": ""},
    {"alias": "HondaCivic",     "folder": "hondacivictyper",    "note": ""},
    {"alias": "HyundaiElantra", "folder": "hyundaielantracn7",  "note": ""},
]

if __name__ == "__main__":
    if len(sys.argv) > 1:
        raise SystemExit(run_cli())
    App().mainloop()