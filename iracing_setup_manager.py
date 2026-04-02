#!/usr/bin/env python3
"""
iRacing Setup Manager
Format A (5 Teile): Anbieter_Strecke_Season_Fahrzeug_Setuptyp
Format B (6 Teile): Anbieter_Season_Fahrzeug_Strecke_Sessiontyp_Setupstil
"""

from __future__ import annotations
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os, shutil, json
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
# Ordner-Spalte wurde vergrößert, damit lange Einträge gut lesbar sind.
COL_WIDTHS = [180, 340, 140, 28]
COL_HEADS  = ["Alias (im Dateinamen)", "iRacing Ordner", "Notiz", ""]


# ── Format-Erkennung ───────────────────────────────────────────────────────────
def detect_format(stem: str):
    parts = stem.split("_")
    if len(parts) == 5:   return parts[3], parts[1], parts[2]
    if len(parts) >= 6:   return parts[2], parts[3], parts[1]
    return None, None, None


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
                return
            except Exception:
                pass
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
        self._filter_var.trace_add("write", lambda *_: self._apply_filter())
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

        # Zeilenhöhe für besser lesbare Eingabe (nicht mehr zu flach)
        row_ipady = 4

        # Checkbox
        cb = tk.Checkbutton(frame, variable=sel_var, bg=bg,
                            activebackground=bg, selectcolor=BG_INPUT,
                            relief="flat", bd=0)
        cb.pack(side=tk.LEFT, padx=(4,0))

        # Zeilennummer
        num_lbl = tk.Label(frame, text=str(idx+1), bg=bg, fg=FG_DIM,
                           font=FONT_SM, width=3, anchor="center")
        num_lbl.pack(side=tk.LEFT)

        ekw = dict(bg=BG_INPUT, fg=FG_MAIN, insertbackground=FG_MAIN,
                   relief="flat", font=FONT_UI, bd=3)

        # Alias
        alias_e = tk.Entry(frame, textvariable=alias_var, width=COL_WIDTHS[0]//7, **ekw)
        alias_e.pack(side=tk.LEFT, padx=2, pady=2, ipady=3)

        # Ordner (Autocomplete)
        folder_frame = tk.Frame(frame, bg=bg, width=COL_WIDTHS[1], height=30)
        folder_frame.pack(side=tk.LEFT, padx=2, pady=2)
        folder_frame.pack_propagate(False)
        folder_ae = AutoEntry(folder_frame, folder_var, IRACING_FOLDERS)
        folder_ae.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)

        # Notiz
        note_e = tk.Entry(frame, textvariable=note_var, width=COL_WIDTHS[2]//7, **ekw)
        note_e.pack(side=tk.LEFT, padx=2, pady=2, ipady=3)

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

    def _apply_filter(self):
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
        self._build()

    def _build(self):
        pad = dict(padx=10, pady=5)

        # Verzeichnisse
        self._sec("VERZEICHNISSE").pack(fill=tk.X, **pad)
        df = tk.Frame(self, bg=BG_PANEL, pady=8, padx=8)
        df.pack(fill=tk.X, padx=10, pady=(0,6))
        self._dir_row(df, "Quelle  (neue Setups):",      self.source_var, self._browse_src)
        self._dir_row(df, "Ziel      (iRacing Setups):", self.dest_var,   self._browse_dst)

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

        tk.Label(ab, text="Aliase aus Editor-Tab", bg=BG_MID,
                 fg=FG_DIM, font=FONT_SM).pack(side=tk.RIGHT, padx=8)

        # Log
        self._sec("LOG").pack(fill=tk.X, padx=10, pady=(8,2))
        lw = tk.Frame(self, bg=BG_MID)
        lw.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0,10))
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

    # ── Widgets ───────────────────────────────────────────────────────────────
    def _sec(self, txt, parent=None):
        p = parent or self
        bg = p["bg"] if hasattr(p,"keys") else BG_DARK
        return tk.Label(p, text=txt, bg=bg, fg=ACCENT, font=("Segoe UI",8,"bold"))

    def _dir_row(self, p, lbl, var, cmd):
        row = tk.Frame(p, bg=BG_PANEL)
        row.pack(fill=tk.X, pady=3)
        tk.Label(row, text=lbl, bg=BG_PANEL, fg=FG_HEAD,
                 font=FONT_UI, width=26, anchor="w").pack(side=tk.LEFT)
        tk.Entry(row, textvariable=var, bg=BG_INPUT, fg=FG_MAIN,
                 insertbackground=FG_MAIN, relief="flat", font=FONT_UI, bd=4
                 ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=6)
        tk.Button(row, text="  …  ", command=cmd, bg=BG_INPUT, fg=FG_MAIN,
                  relief="flat", font=FONT_UI, activebackground=BORDER,
                  activeforeground=FG_MAIN, cursor="hand2").pack(side=tk.LEFT)

    def _abtn(self, p, txt, cmd, bg):
        return tk.Button(p, text=txt, command=cmd, bg=bg, fg="white",
                         relief="flat", font=FONT_BOLD, padx=14, pady=5,
                         activebackground=BORDER, activeforeground="white", cursor="hand2")

    def _browse_src(self):
        d = filedialog.askdirectory(initialdir=self.source_var.get() or str(Path.home()))
        if d: self.source_var.set(d)

    def _browse_dst(self):
        d = filedialog.askdirectory(initialdir=self.dest_var.get() or str(Path.home()))
        if d: self.dest_var.set(d)

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
        base = Path(self.dest_var.get()) / folder
        s    = self.season_var.get().strip()
        if   mode == "season": return base / s
        elif mode == "track":  return base / track
        elif mode == "both":   return base / s / track
        return base

    def _build_dest_resolved(self, dest_base: Path, folder, track, mode) -> Path:
        """Wie _build_dest aber mit bereits aufgelöstem dest_base-Pfad."""
        base = dest_base / folder
        s    = self.season_var.get().strip()
        if   mode == "season": return base / s
        elif mode == "track":  return base / track
        elif mode == "both":   return base / s / track
        return base

    def _get_files(self) -> list[str]:
        src = self.source_var.get()
        if not os.path.isdir(src):
            messagebox.showerror("Fehler", f"Quellverzeichnis nicht gefunden:\n{src}")
            return []
        return [f for f in os.listdir(src) if f.lower().endswith(".sto")]

    def _validate(self) -> bool:
        if self.mode_var.get() in ("season","both") and not self.season_var.get().strip():
            messagebox.showerror("Fehler", "Bitte Season-Name eingeben.")
            return False
        return True

    # ── Aktionen ──────────────────────────────────────────────────────────────
    def _scan(self):
        if not self._validate(): return
        self._clear_log()
        files = self._get_files()
        if not files:
            self._wlog("Keine .sto Dateien gefunden.", "warn"); return
        aliases = self.alias_editor.get_alias_dict()
        mode    = self.mode_var.get()
        self._wlog(f"━━  Scan  ·  {len(files)} Datei(en)  ·  {len(aliases)} Aliase geladen  ━━", "head")
        ok = skip = 0
        for fname in sorted(files):
            stem = Path(fname).stem
            car, track, season = detect_format(stem)
            if car is None:
                self._wlog(f"  ⚠  Unbekanntes Format: {fname}", "warn"); skip += 1; continue
            folder = aliases.get(car)
            if not folder:
                self._wlog(f"  ⚠  Kein Alias für '{car}': {fname}", "warn"); skip += 1; continue
            fmt  = "A" if len(stem.split("_"))==5 else "B"
            dest = self._build_dest(folder, track, mode)
            self._wlog(f"  ✓  [Fmt-{fmt}]  {fname}", "ok")
            self._wlog(f"       {car} → {folder}   Strecke: {track}   Season: {season}", "dim")
            self._wlog(f"       → {dest}", "dim")
            ok += 1
        self._wlog(f"\n  → {ok} bereit  ·  {skip} übersprungen", "head")

    def _copy(self):
        if not self._validate(): return
        self._clear_log()
        files = self._get_files()
        if not files:
            self._wlog("Keine .sto Dateien gefunden.", "warn"); return
        moving   = self.move_var.get()
        aliases  = self.alias_editor.get_alias_dict()
        mode     = self.mode_var.get()
        src_base = Path(self.source_var.get()).resolve()
        dest_base = Path(self.dest_var.get()).resolve()
        if not dest_base.exists():
            self._wlog(f"  ✗  Zielverzeichnis existiert nicht: {dest_base}", "error"); return
        if moving and not messagebox.askyesno(
                "Verschieben bestätigen",
                f"{len(files)} Datei(en) werden aus dem Quellordner entfernt.\n\nFortfahren?"):
            return
        verb = "Verschieben" if moving else "Kopieren"
        self._wlog(f"━━  {verb}  ·  {len(aliases)} Aliase aktiv  ━━", "head")
        self._wlog(f"  Quelle: {src_base}", "dim")
        self._wlog(f"  Ziel:   {dest_base}", "dim")
        ok = skip = ow = 0
        for fname in sorted(files):
            stem = Path(fname).stem
            car, track, season = detect_format(stem)
            if car is None:
                self._wlog(f"  ⚠  Unbekanntes Format: {fname}", "warn"); skip += 1; continue
            folder = aliases.get(car)
            if not folder:
                self._wlog(f"  ⚠  Kein Alias für '{car}' — im Alias-Editor eintragen: {fname}", "warn")
                skip += 1; continue
            dest_dir  = self._build_dest_resolved(dest_base, folder, track, mode)
            src_file  = src_base / fname
            dest_file = dest_dir / fname
            existed   = dest_file.exists()
            try:
                os.makedirs(dest_dir, exist_ok=True)
                if moving:
                    shutil.move(str(src_file), str(dest_file))
                else:
                    shutil.copy2(str(src_file), str(dest_file))
                # Verify the file actually arrived
                if not dest_file.exists():
                    raise FileNotFoundError(f"Datei nach der Operation nicht vorhanden: {dest_file}")
                icon = "✂" if moving else ("♻" if existed else "✓")
                self._wlog(f"  {icon}  {fname}", "warn" if existed else "ok")
                self._wlog(f"       → {dest_file}", "dim")
                ok += 1
                if existed: ow += 1
            except Exception as e:
                self._wlog(f"  ✗  {fname}: {e}", "error"); skip += 1
        verb_past = "verschoben" if moving else "kopiert"
        self._wlog(f"\n  → {ok} {verb_past}  ({ow} überschrieben)  ·  {skip} übersprungen", "head")


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
        self.copy_tab._upd_season()
        self.copy_tab._upd_exec_btn()

    def _save_config(self):
        cfg = {
            "source": self.copy_tab.source_var.get(),
            "dest":   self.copy_tab.dest_var.get(),
            "mode":   self.copy_tab.mode_var.get(),
            "season": self.copy_tab.season_var.get(),
            "move":   self.copy_tab.move_var.get(),
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


if __name__ == "__main__":
    App().mainloop()