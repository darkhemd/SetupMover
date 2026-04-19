from __future__ import annotations

import tkinter as tk
import traceback
from pathlib import Path
from tkinter import ttk

from core.config import AUTOCOMPLETE_HIDE_MS, AUTOCOMPLETE_MAX_SHOWN
from gui.theme import (
    ACCENT,
    BG_DARK,
    BG_DROP,
    BG_INPUT,
    BG_MID,
    BG_PANEL,
    BORDER,
    FG_DIM,
    FG_HEAD,
    FG_MAIN,
    FONT_BOLD,
    FONT_MONO,
    FONT_UI,
)


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
        self.entry.bind("<FocusOut>", lambda _: self.after(AUTOCOMPLETE_HIDE_MS, self._hide))
        self.entry.bind("<Escape>",   lambda _: self._hide())
        self.entry.bind("<Down>",     self._focus_lb)
        self.entry.bind("<Return>",   lambda _: self._hide())

    def _on_write(self, *_):
        q = self.var.get().strip().lower()
        matches = [c for c in self.choices if q in c] if q else []
        if matches:
            self._show(matches)
        else:
            self._hide()

    def _show(self, matches):
        if self._pop:
            self._pop.destroy()
        x = self.entry.winfo_rootx()
        y = self.entry.winfo_rooty() + self.entry.winfo_height()
        w = max(self.entry.winfo_width(), 240)
        h = min(len(matches), AUTOCOMPLETE_MAX_SHOWN) * 20 + 4
        self._pop = tk.Toplevel(self)
        self._pop.wm_overrideredirect(True)
        self._pop.wm_geometry(f"{w}x{h}+{x}+{y}")
        self._pop.configure(bg=BORDER)
        self._lb = tk.Listbox(
            self._pop, bg=BG_DROP, fg=FG_MAIN,
            selectbackground=ACCENT, selectforeground="white",
            relief="flat", font=FONT_MONO, bd=0,
            highlightthickness=0, activestyle="none",
        )
        self._lb.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)
        for m in matches:
            self._lb.insert(tk.END, m)
        self._lb.bind("<ButtonRelease-1>", self._pick)
        self._lb.bind("<Return>",          self._pick)
        self._lb.bind("<Escape>",          lambda _: self._hide())
        self._lb.bind("<FocusOut>",        lambda _: self.after(AUTOCOMPLETE_HIDE_MS, self._hide))

    def _pick(self, *_):
        if self._lb:
            sel = self._lb.curselection()
            if sel:
                self.var.set(self._lb.get(sel[0]))
        self._hide()

    def _focus_lb(self, *_):
        if self._lb:
            self._lb.focus_set()
            self._lb.selection_set(0)

    def _hide(self, *_):
        if self._pop:
            self._pop.destroy()
            self._pop = None
            self._lb = None


class ErrorDialog(tk.Toplevel):
    """Modaler Fehlerdialog mit Pfad-Kontext, Detail-Toggle und Kopier-Button."""

    def __init__(
        self,
        parent: tk.Misc,
        title: str,
        message: str,
        *,
        path: str | None = None,
        exc: BaseException | None = None,
    ):
        super().__init__(parent)
        self.title(title)
        self.configure(bg=BG_DARK)
        self.transient(parent.winfo_toplevel())
        self.resizable(True, True)
        self.minsize(420, 160)

        self._title = title
        self._message = message
        self._path = path
        self._traceback = (
            "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
            if exc is not None
            else None
        )

        outer = tk.Frame(self, bg=BG_DARK, padx=14, pady=12)
        outer.pack(fill=tk.BOTH, expand=True)

        tk.Label(
            outer, text=title, bg=BG_DARK, fg=ACCENT,
            font=("Segoe UI", 11, "bold"), anchor="w",
        ).pack(fill=tk.X, pady=(0, 6))

        tk.Message(
            outer, text=message, bg=BG_DARK, fg=FG_MAIN,
            font=FONT_UI, width=520, anchor="w", justify="left",
        ).pack(fill=tk.X, pady=(0, 6))

        if path:
            pf = tk.Frame(outer, bg=BG_PANEL, padx=8, pady=4)
            pf.pack(fill=tk.X, pady=(0, 6))
            tk.Label(
                pf, text="Pfad:", bg=BG_PANEL, fg=FG_DIM, font=FONT_UI,
            ).pack(anchor="w")
            path_entry = tk.Entry(
                pf, bg=BG_INPUT, fg=FG_MAIN, font=FONT_MONO,
                relief="flat", bd=4, readonlybackground=BG_INPUT,
            )
            path_entry.insert(0, path)
            path_entry.config(state="readonly")
            path_entry.pack(fill=tk.X, pady=(2, 0))

        self._details_frame: tk.Frame | None = None
        self._details_toggle: tk.Button | None = None
        if self._traceback:
            self._details_toggle = tk.Button(
                outer, text="Details ▸", command=self._toggle_details,
                bg=BG_MID, fg=FG_MAIN, relief="flat", font=FONT_UI,
                activebackground=BORDER, activeforeground=FG_MAIN, cursor="hand2",
                anchor="w", padx=8, pady=2, bd=0,
            )
            self._details_toggle.pack(fill=tk.X, pady=(0, 6))

        btns = tk.Frame(outer, bg=BG_DARK)
        btns.pack(fill=tk.X, pady=(8, 0))
        tk.Button(
            btns, text="Kopieren", command=self._copy_to_clipboard,
            bg=BG_MID, fg=FG_MAIN, relief="flat", font=FONT_BOLD,
            activebackground=BORDER, activeforeground=FG_MAIN,
            padx=14, pady=5, cursor="hand2",
        ).pack(side=tk.LEFT)
        tk.Button(
            btns, text="Schließen", command=self.destroy,
            bg=ACCENT, fg="white", relief="flat", font=FONT_BOLD,
            activebackground=BORDER, activeforeground="white",
            padx=14, pady=5, cursor="hand2",
        ).pack(side=tk.RIGHT)

        self.bind("<Escape>", lambda _: self.destroy())
        self.update_idletasks()
        self._center_on_parent(parent)
        self.grab_set()
        self.focus_set()
        self.wait_window(self)

    def _toggle_details(self) -> None:
        if self._details_frame is None:
            self._details_frame = tk.Frame(self, bg=BG_DARK, padx=14, pady=(0, 12))
            self._details_frame.pack(fill=tk.BOTH, expand=True)
            txt = tk.Text(
                self._details_frame, bg=BG_PANEL, fg=FG_MAIN, font=FONT_MONO,
                relief="flat", bd=4, height=10, wrap="none",
            )
            txt.insert("1.0", self._traceback or "")
            txt.config(state="disabled")
            sb = tk.Scrollbar(self._details_frame, orient="vertical", command=txt.yview)
            txt.configure(yscrollcommand=sb.set)
            txt.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            sb.pack(side=tk.RIGHT, fill=tk.Y)
            if self._details_toggle is not None:
                self._details_toggle.config(text="Details ▾")
        else:
            self._details_frame.destroy()
            self._details_frame = None
            if self._details_toggle is not None:
                self._details_toggle.config(text="Details ▸")

    def _copy_to_clipboard(self) -> None:
        parts = [self._title, "", self._message]
        if self._path:
            parts += ["", f"Pfad: {self._path}"]
        if self._traceback:
            parts += ["", self._traceback]
        text = "\n".join(parts)
        self.clipboard_clear()
        self.clipboard_append(text)

    def _center_on_parent(self, parent: tk.Misc) -> None:
        try:
            top = parent.winfo_toplevel()
            top.update_idletasks()
            px, py = top.winfo_rootx(), top.winfo_rooty()
            pw, ph = top.winfo_width(), top.winfo_height()
            w, h = self.winfo_width(), self.winfo_height()
            x = px + max(0, (pw - w) // 2)
            y = py + max(0, (ph - h) // 3)
            self.geometry(f"+{x}+{y}")
        except tk.TclError:
            pass


class PreviewDialog(tk.Toplevel):
    """Zeigt Inhalt einer .sto-Datei (erste 50 Zeilen + XML-Metadaten)."""

    def __init__(
        self,
        parent: tk.Misc,
        path: Path,
        *,
        fmt: str | None = None,
        car: str | None = None,
        track: str | None = None,
        season: str | None = None,
    ):
        super().__init__(parent)
        self.title(f"Vorschau — {path.name}")
        self.configure(bg=BG_DARK)
        self.transient(parent.winfo_toplevel())
        self.resizable(True, True)
        self.minsize(560, 420)

        from core.formats import parse_sto_header
        raw, car_xml, track_xml = parse_sto_header(path)

        outer = tk.Frame(self, bg=BG_DARK, padx=14, pady=12)
        outer.pack(fill=tk.BOTH, expand=True)

        tk.Label(outer, text=path.name, bg=BG_DARK, fg=ACCENT,
                 font=("Segoe UI", 11, "bold"), anchor="w").pack(fill=tk.X, pady=(0, 4))

        pf = tk.Frame(outer, bg=BG_MID, padx=8, pady=6)
        pf.pack(fill=tk.X, pady=(0, 6))
        tk.Label(pf, text="Pfad:", bg=BG_MID, fg=FG_DIM, font=FONT_UI).pack(anchor="w")
        path_e = tk.Entry(pf, bg=BG_INPUT, fg=FG_MAIN, font=FONT_MONO,
                          relief="flat", bd=4, readonlybackground=BG_INPUT)
        path_e.insert(0, str(path))
        path_e.config(state="readonly")
        path_e.pack(fill=tk.X, pady=(2, 0))

        meta: list[str] = []
        if fmt:
            meta.append(f"Format {fmt}")
        if car or car_xml:
            meta.append(f"Auto: {car or car_xml}")
        if track or track_xml:
            meta.append(f"Strecke: {track or track_xml}")
        if season:
            meta.append(f"Season: {season}")
        if meta:
            tk.Label(outer, text="  ·  ".join(meta), bg=BG_DARK, fg=FG_HEAD,
                     font=FONT_UI, anchor="w").pack(fill=tk.X, pady=(0, 6))

        tf = tk.Frame(outer, bg=BG_DARK)
        tf.pack(fill=tk.BOTH, expand=True)
        txt = tk.Text(tf, bg=BG_MID, fg=FG_MAIN, font=FONT_MONO,
                      relief="flat", bd=4, wrap="none", height=20)
        vsb = ttk.Scrollbar(tf, orient="vertical", command=txt.yview)
        txt.configure(yscrollcommand=vsb.set)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        txt.pack(fill=tk.BOTH, expand=True)
        hsb = ttk.Scrollbar(outer, orient="horizontal", command=txt.xview)
        txt.configure(xscrollcommand=hsb.set)
        hsb.pack(fill=tk.X, pady=(2, 0))

        txt.insert("1.0", raw if raw else "(Datei konnte nicht gelesen werden)")
        txt.config(state="disabled")

        btns = tk.Frame(outer, bg=BG_DARK)
        btns.pack(fill=tk.X, pady=(10, 0))
        tk.Button(btns, text="Schließen", command=self.destroy,
                  bg=ACCENT, fg="white", relief="flat", font=FONT_BOLD,
                  activebackground=BORDER, activeforeground="white",
                  padx=14, pady=5, cursor="hand2").pack(side=tk.RIGHT)

        self.bind("<Escape>", lambda _: self.destroy())
        self.update_idletasks()
        self._center_on_parent(parent)
        self.focus_set()

    def _center_on_parent(self, parent: tk.Misc) -> None:
        try:
            top = parent.winfo_toplevel()
            top.update_idletasks()
            px, py = top.winfo_rootx(), top.winfo_rooty()
            pw, ph = top.winfo_width(), top.winfo_height()
            w, h = self.winfo_width(), self.winfo_height()
            x = px + max(0, (pw - w) // 2)
            y = py + max(0, (ph - h) // 3)
            self.geometry(f"+{x}+{y}")
        except tk.TclError:
            pass
