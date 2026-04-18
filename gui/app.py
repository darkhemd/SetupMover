from __future__ import annotations

import json
import tkinter as tk
from tkinter import messagebox, ttk

from core.config import (
    CONFIG_FILE,
    DEFAULT_DEST,
    DEFAULT_SOURCE,
    WINDOW_GEOMETRY,
    WINDOW_MIN_H,
    WINDOW_MIN_W,
)
from gui.tab_alias import AliasEditor, AliasStore
from gui.tab_copy import CopyTab
from gui.theme import (
    ACCENT,
    BG_DARK,
    BG_INPUT,
    BG_MID,
    BG_PANEL,
    BG_SEL,
    FG_DIM,
    FG_HEAD,
    FG_MAIN,
    FONT_BOLD,
    FONT_SM,
    FONT_UI,
)


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("iRacing Setup Manager")
        self.configure(bg=BG_DARK)
        self.minsize(WINDOW_MIN_W, WINDOW_MIN_H)
        self.geometry(WINDOW_GEOMETRY)

        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TScrollbar", background=BG_INPUT, troughcolor=BG_DARK, bordercolor=BG_DARK)
        style.configure("TRadiobutton", background=BG_PANEL, foreground=FG_MAIN,
                        font=FONT_UI, focuscolor=BG_PANEL)
        style.map("TRadiobutton", background=[("active", BG_PANEL)])
        style.configure("Dark.TNotebook",     background=BG_DARK, borderwidth=0)
        style.configure("Dark.TNotebook.Tab", background=BG_MID, foreground=FG_DIM,
                        font=FONT_BOLD, padding=[14, 6], borderwidth=0)
        style.map("Dark.TNotebook.Tab",
                  background=[("selected", BG_PANEL), ("active", BG_INPUT)],
                  foreground=[("selected", FG_MAIN),  ("active", FG_MAIN)])
        style.configure("Copy.Treeview",
                        background=BG_MID, foreground=FG_MAIN,
                        fieldbackground=BG_MID, font=FONT_SM)
        style.configure("Copy.Treeview.Heading", background=BG_PANEL, foreground=FG_HEAD)
        style.map("Copy.Treeview", background=[("selected", BG_SEL)])
        style.configure("Dark.TCombobox",
                        fieldbackground=BG_INPUT, background=BG_INPUT,
                        foreground=FG_MAIN, arrowcolor=FG_MAIN)
        style.map("Dark.TCombobox", fieldbackground=[("readonly", BG_INPUT)])

        self._build()
        self._load_config()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build(self):
        tb = tk.Frame(self, bg=BG_MID)
        tb.pack(fill=tk.X)
        tk.Label(tb, text="  ⬛  ", bg=ACCENT, fg="white",
                 font=("Segoe UI", 13, "bold"), pady=6).pack(side=tk.LEFT)
        tk.Label(tb, text="iRacing Setup Manager", bg=BG_MID, fg=FG_MAIN,
                 font=("Segoe UI", 12, "bold"), pady=8, padx=10).pack(side=tk.LEFT)
        tk.Label(tb, text="Format A & B  ·  .sto",
                 bg=BG_MID, fg=FG_DIM, font=FONT_SM, pady=8).pack(side=tk.LEFT)

        self.nb = ttk.Notebook(self, style="Dark.TNotebook")
        self.nb.pack(fill=tk.BOTH, expand=True)

        self.store     = AliasStore()
        self.alias_tab = AliasEditor(self.nb, self.store)
        self.copy_tab  = CopyTab(self.nb, self.alias_tab)

        self.nb.add(self.copy_tab,  text="  📋  Setup Kopieren  ")
        self.nb.add(self.alias_tab, text="  🏎  Alias Editor  ")

    def _load_config(self):
        cfg = {}
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, encoding="utf-8") as f:
                    raw = json.load(f)
                if not isinstance(raw, dict):
                    raise ValueError("Kein JSON-Objekt")
                cfg = raw
            except json.JSONDecodeError as exc:
                messagebox.showwarning(
                    "Konfiguration fehlerhaft",
                    f"Konfigurationsdatei konnte nicht gelesen werden:\n{CONFIG_FILE}\n\n{exc}\n\nStandardwerte werden verwendet.",
                )
            except ValueError as exc:
                messagebox.showwarning(
                    "Konfiguration fehlerhaft",
                    f"Ungültiges Format in:\n{CONFIG_FILE}\n\n{exc}\n\nStandardwerte werden verwendet.",
                )
            except OSError as exc:
                messagebox.showwarning(
                    "Konfiguration nicht lesbar",
                    f"{CONFIG_FILE}\n\n{exc}",
                )
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
            "source":         self.copy_tab.source_var.get(),
            "dest":           self.copy_tab.dest_var.get(),
            "mode":           self.copy_tab.mode_var.get(),
            "season":         self.copy_tab.season_var.get(),
            "move":           self.copy_tab.move_var.get(),
            "recursive":      self.copy_tab.recursive_var.get(),
            "dry_run":        self.copy_tab.dry_run_var.get(),
            "backup":         self.copy_tab.backup_var.get(),
            "collision":      self.copy_tab.collision_var.get(),
            "source_history": self.copy_tab._source_history,
            "dest_history":   self.copy_tab._dest_history,
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
            if ans is None:
                return
            if ans:
                self.alias_tab._save()
        self._save_config()
        self.destroy()
