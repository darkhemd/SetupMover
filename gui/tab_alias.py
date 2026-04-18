from __future__ import annotations

import json
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from core.config import ALIAS_FILE
from data.default_aliases import DEFAULT_ALIASES
from data.iracing_folders import IRACING_FOLDERS, IRACING_FOLDERS_SET
from gui.theme import (
    ACCENT,
    BG_DARK,
    BG_INPUT,
    BG_MID,
    BG_ROW_A,
    BG_ROW_B,
    BORDER,
    COL_HEADS,
    COL_WIDTHS,
    FG_DIM,
    FG_HEAD,
    FG_MAIN,
    FONT_BOLD,
    FONT_H,
    FONT_SM,
    FONT_UI,
    GREEN,
    YELLOW,
)
from gui.widgets import AutoEntry


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


class AliasEditor(tk.Frame):
    """
    Tabellen-Editor für persistente Auto-Aliase.
    Jede Zeile: Alias | iRacing-Ordner (Autocomplete) | Notiz | Gültig
    """

    def __init__(self, parent, store: AliasStore, **kw):
        super().__init__(parent, bg=BG_DARK, **kw)
        self.store       = store
        self._rows: list[dict] = []
        self._filter_var = tk.StringVar()
        self._filter_var.trace_add("write", self._apply_filter)
        self._unsaved = False
        self._build()
        self._load_rows()

    # ── Layout ────────────────────────────────────────────────────────────────
    def _build(self):
        tb = tk.Frame(self, bg=BG_MID, pady=5, padx=8)
        tb.pack(fill=tk.X)
        self._tbtn(tb, "+ Alias hinzufügen", self._add_row).pack(side=tk.LEFT, padx=(0, 4))
        self._tbtn(tb, "− Markierte löschen", self._delete_selected, danger=True).pack(side=tk.LEFT, padx=(0, 12))
        self._tbtn(tb, "↑ Nach oben",  lambda: self._move(-1)).pack(side=tk.LEFT, padx=(0, 4))
        self._tbtn(tb, "↓ Nach unten", lambda: self._move(1)).pack(side=tk.LEFT, padx=(0, 12))
        self._tbtn(tb, "💾 Speichern", self._save, primary=True).pack(side=tk.LEFT)
        self._tbtn(tb, "Export JSON…", self._export_aliases).pack(side=tk.LEFT, padx=(12, 4))
        self._tbtn(tb, "Import JSON…", self._import_aliases).pack(side=tk.LEFT, padx=(0, 4))

        self._save_lbl = tk.Label(tb, text="", bg=BG_MID, fg=FG_DIM, font=FONT_SM)
        self._save_lbl.pack(side=tk.LEFT, padx=8)

        tk.Label(tb, text="Filter:", bg=BG_MID, fg=FG_HEAD, font=FONT_UI).pack(side=tk.RIGHT, padx=(8, 2))
        tk.Entry(tb, textvariable=self._filter_var, width=18,
                 bg=BG_INPUT, fg=FG_MAIN, insertbackground=FG_MAIN,
                 relief="flat", font=FONT_UI, bd=4).pack(side=tk.RIGHT)

        hdr = tk.Frame(self, bg=BG_MID)
        hdr.pack(fill=tk.X, padx=0, pady=(4, 0))
        tk.Label(hdr, text="", bg=BG_MID, width=3).pack(side=tk.LEFT)
        tk.Label(hdr, text="#", bg=BG_MID, fg=FG_DIM, font=FONT_H,
                 width=3, anchor="center").pack(side=tk.LEFT)
        for txt, w in zip(COL_HEADS, COL_WIDTHS):
            tk.Label(hdr, text=txt, bg=BG_MID, fg=FG_HEAD, font=FONT_H,
                     width=w // 7, anchor="w", padx=4, pady=3).pack(side=tk.LEFT)

        wrap = tk.Frame(self, bg=BG_DARK)
        wrap.pack(fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(wrap, bg=BG_DARK, highlightthickness=0)
        vsb = ttk.Scrollbar(wrap, orient="vertical", command=self.canvas.yview)
        self.table = tk.Frame(self.canvas, bg=BG_DARK)
        self._canvas_win = self.canvas.create_window((0, 0), window=self.table, anchor="nw")
        self.canvas.configure(yscrollcommand=vsb.set)
        self.table.bind("<Configure>", lambda _:
            self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda e:
            self.canvas.itemconfig(self._canvas_win, width=e.width))
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.bind_all("<MouseWheel>", lambda e:
            self.canvas.yview_scroll(int(-1 * e.delta / 120), "units"))

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
            self._append_row(r.get("alias", ""), r.get("folder", ""), r.get("note", ""))
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
            parent=self, title="Aliase exportieren",
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
            parent=self, title="Aliase importieren",
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
                messagebox.showerror("Import", f"Eintrag {i + 1} ist kein Objekt.")
                return
            rows.append({
                "alias":  str(item.get("alias",  "")).strip(),
                "folder": str(item.get("folder", "")).strip(),
                "note":   str(item.get("note",   "")).strip(),
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
        idx = len(self._rows)
        bg = BG_ROW_A if idx % 2 == 0 else BG_ROW_B
        frame = tk.Frame(self.table, bg=bg, pady=1)
        frame.pack(fill=tk.X, pady=0)

        alias_var  = tk.StringVar(value=alias)
        folder_var = tk.StringVar(value=folder)
        note_var   = tk.StringVar(value=note)
        sel_var    = tk.BooleanVar(value=False)

        cb = tk.Checkbutton(frame, variable=sel_var, bg=bg,
                            activebackground=bg, selectcolor=BG_INPUT,
                            relief="flat", bd=0, fg="white",
                            activeforeground="white", font=FONT_BOLD)
        cb.pack(side=tk.LEFT, padx=(4, 0))

        num_lbl = tk.Label(frame, text=str(idx + 1), bg=bg, fg=FG_DIM,
                           font=FONT_SM, width=3, anchor="center")
        num_lbl.pack(side=tk.LEFT)

        ekw = dict(bg=BG_INPUT, fg=FG_MAIN, insertbackground=FG_MAIN,
                   relief="flat", font=FONT_UI, bd=3)

        alias_e = tk.Entry(frame, textvariable=alias_var, width=COL_WIDTHS[0] // 7, **ekw)
        alias_e.pack(side=tk.LEFT, padx=2, pady=2, ipady=4)

        folder_frame = tk.Frame(frame, bg=bg, width=COL_WIDTHS[1], height=30)
        folder_frame.pack(side=tk.LEFT, padx=2, pady=2)
        folder_frame.pack_propagate(False)
        folder_ae = AutoEntry(folder_frame, folder_var, IRACING_FOLDERS)
        folder_ae.pack(fill=tk.BOTH, expand=True)

        note_e = tk.Entry(frame, textvariable=note_var, width=COL_WIDTHS[2] // 7, **ekw)
        note_e.pack(side=tk.LEFT, padx=2, pady=2, ipady=4)

        valid_lbl = tk.Label(frame, text="", bg=bg, font=FONT_SM, width=2)
        valid_lbl.pack(side=tk.LEFT, padx=(0, 4))

        def upd_valid(*_):
            v = folder_var.get().strip()
            if v in IRACING_FOLDERS_SET:
                valid_lbl.config(text="✓", fg=GREEN)
            elif v:
                valid_lbl.config(text="?", fg=YELLOW)
            else:
                valid_lbl.config(text="", fg=FG_DIM)

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
        if not selected:
            return
        if direction == -1 and selected[0] == 0:
            return
        if direction == 1 and selected[-1] == len(self._rows) - 1:
            return
        for i in (selected if direction == 1 else reversed(selected)):
            j = i + direction
            self._rows[i], self._rows[j] = self._rows[j], self._rows[i]
        for r in self._rows:
            r["frame"].pack_forget()
        for r in self._rows:
            r["frame"].pack(fill=tk.X)
        self._refresh_numbers()
        self._mark_unsaved()

    def _refresh_numbers(self):
        for i, r in enumerate(self._rows):
            r["num_lbl"].config(text=str(i + 1))
            bg = BG_ROW_A if i % 2 == 0 else BG_ROW_B
            r["frame"].config(bg=bg)
            r["bg"] = bg

    def _apply_filter(self, *_):
        q = self._filter_var.get().strip().lower()
        for r in self._rows:
            show = (not q
                    or q in r["alias_var"].get().lower()
                    or q in r["folder_var"].get().lower()
                    or q in r["note_var"].get().lower())
            if show:
                r["frame"].pack(fill=tk.X)
            else:
                r["frame"].pack_forget()

    def _update_status(self):
        total   = len(self._rows)
        valid   = sum(1 for r in self._rows if r["folder_var"].get().strip() in IRACING_FOLDERS_SET)
        invalid = sum(1 for r in self._rows
                      if r["folder_var"].get().strip()
                      and r["folder_var"].get().strip() not in IRACING_FOLDERS_SET)
        parts = [f"{total} Aliase  ·  {valid} ✓ gültig"]
        if invalid:
            parts.append(f"  {invalid} ⚠ unbekannter Ordner")
        self._status.config(text="  ".join(parts))
