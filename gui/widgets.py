from __future__ import annotations

import tkinter as tk

from core.config import AUTOCOMPLETE_HIDE_MS, AUTOCOMPLETE_MAX_SHOWN
from gui.theme import ACCENT, BG_DROP, BG_INPUT, BG_PANEL, BORDER, FG_MAIN, FONT_MONO, FONT_UI


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
