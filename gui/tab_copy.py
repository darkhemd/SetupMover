from __future__ import annotations

import os
import shutil
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import TYPE_CHECKING

from core.config import BACKUP_KEEP_MAX
from core.paths import (
    collect_sto_sources,
    dest_looks_like_setups_root,
    merge_path_history,
    open_path_in_file_manager,
    pick_rename_destination,
)
from core.planner import StoPlanEntry, plan_sto_operations
from gui.theme import (
    ACCENT,
    BG_DARK,
    BG_INPUT,
    BG_MID,
    BG_PANEL,
    BG_SEL,
    BORDER,
    FG_DIM,
    FG_HEAD,
    FG_MAIN,
    FONT_BOLD,
    FONT_MONO,
    FONT_SM,
    FONT_UI,
    GREEN,
    YELLOW,
)

if TYPE_CHECKING:
    from gui.tab_alias import AliasEditor


class CopyTab(tk.Frame):
    def __init__(self, parent, alias_editor: AliasEditor, **kw):
        super().__init__(parent, bg=BG_DARK, **kw)
        self.alias_editor = alias_editor
        self.source_var    = tk.StringVar()
        self.dest_var      = tk.StringVar()
        self.mode_var      = tk.StringVar(value="none")
        self.season_var    = tk.StringVar()
        self.move_var      = tk.BooleanVar(value=False)
        self.recursive_var = tk.BooleanVar(value=False)
        self.dry_run_var   = tk.BooleanVar(value=False)
        self.backup_var    = tk.BooleanVar(value=True)
        self.collision_var = tk.StringVar(value="overwrite")
        self._source_history: list[str] = []
        self._dest_history:   list[str] = []
        self._source_combo: ttk.Combobox | None = None
        self._dest_combo:   ttk.Combobox | None = None
        self._last_plan: list[StoPlanEntry] = []
        self._build()

    def _build(self):
        pad = dict(padx=10, pady=5)

        self._sec("VERZEICHNISSE").pack(fill=tk.X, **pad)
        df = tk.Frame(self, bg=BG_PANEL, pady=8, padx=8)
        df.pack(fill=tk.X, padx=10, pady=(0, 6))
        self._dir_row_combo(df, "Quelle  (neue Setups):", self.source_var, self._browse_src, "source")
        self._dir_row_combo(df, "Ziel      (iRacing Setups):", self.dest_var, self._browse_dst, "dest")

        cf = tk.Frame(self, bg=BG_PANEL, padx=10, pady=8)
        cf.pack(fill=tk.X, padx=10, pady=(0, 6))
        self._sec("BEI VORHANDENEM ZIEL (GLEICHER DATEINAME)", cf).pack(anchor="w", pady=(0, 4))
        cr = tk.Frame(cf, bg=BG_PANEL)
        cr.pack(anchor="w")
        for lbl, val in [("Überschreiben", "overwrite"), ("Überspringen", "skip"), ("Umbenennen (_v2 …)", "rename")]:
            ttk.Radiobutton(cr, text=lbl, variable=self.collision_var, value=val).pack(side=tk.LEFT, padx=(0, 12))

        mid = tk.Frame(self, bg=BG_DARK)
        mid.pack(fill=tk.X, **pad)

        mp = tk.Frame(mid, bg=BG_PANEL, padx=12, pady=8)
        mp.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 8))
        self._sec("UNTERORDNER-MODUS", mp).pack(anchor="w", pady=(0, 6))
        for lbl, val in [("Kein Unterordner", "none"), ("Season", "season"),
                          ("Strecke", "track"), ("Season  +  Strecke", "both")]:
            ttk.Radiobutton(mp, text=lbl, variable=self.mode_var,
                            value=val, command=self._upd_season).pack(anchor="w", pady=2)

        sp = tk.Frame(mid, bg=BG_PANEL, padx=12, pady=8)
        sp.pack(side=tk.LEFT, fill=tk.Y)
        self._sec("SEASON-NAME", sp).pack(anchor="w", pady=(0, 6))
        self.season_entry = tk.Entry(sp, textvariable=self.season_var, width=14,
                                     bg=BG_INPUT, fg=FG_MAIN, insertbackground=FG_MAIN,
                                     relief="flat", font=("Segoe UI", 11, "bold"), bd=6)
        self.season_entry.pack(anchor="w")
        tk.Label(sp, text="z.B. 26S2, 26S3 …", bg=BG_PANEL, fg=FG_DIM, font=FONT_SM).pack(anchor="w", pady=(4, 0))

        ab = tk.Frame(self, bg=BG_MID, pady=6, padx=10)
        ab.pack(fill=tk.X)
        self._abtn(ab, "🔍  Scannen", self._scan, ACCENT).pack(side=tk.LEFT, padx=(0, 6))
        self._abtn(ab, "➕  Fehlende Aliase", self._alias_assistant, BG_INPUT).pack(side=tk.LEFT, padx=(0, 6))

        self._exec_btn = self._abtn(ab, "📋  Kopieren", self._copy, GREEN)
        self._exec_btn.pack(side=tk.LEFT, padx=(0, 12))

        toggle_frame = tk.Frame(ab, bg=BG_MID)
        toggle_frame.pack(side=tk.LEFT)
        tk.Label(toggle_frame, text="Modus:", bg=BG_MID, fg=FG_HEAD, font=FONT_SM).pack(side=tk.LEFT, padx=(0, 6))
        for lbl, val in [("Kopieren", False), ("Verschieben", True)]:
            ttk.Radiobutton(toggle_frame, text=lbl, variable=self.move_var,
                            value=val, command=self._upd_exec_btn).pack(side=tk.LEFT, padx=(0, 4))

        opt = tk.Frame(ab, bg=BG_MID)
        opt.pack(side=tk.LEFT, padx=(16, 0))
        for text, var in [
            ("Rekursiv scannen", self.recursive_var),
            ("Nur Vorschau (Dry-Run)", self.dry_run_var),
            ("Backup vor Überschreiben", self.backup_var),
        ]:
            tk.Checkbutton(opt, text=text, variable=var,
                           bg=BG_MID, fg=FG_MAIN, selectcolor=BG_INPUT,
                           activebackground=BG_MID, activeforeground=FG_MAIN,
                           font=FONT_SM).pack(side=tk.LEFT, padx=(0, 8))

        tk.Label(ab, text="Aliase aus Editor-Tab", bg=BG_MID, fg=FG_DIM, font=FONT_SM).pack(side=tk.RIGHT, padx=8)

        self._sec("ERGEBNIS").pack(fill=tk.X, padx=10, pady=(8, 2))
        self._status_lbl = tk.Label(self, text="", bg=BG_DARK, fg=FG_DIM, font=FONT_SM, anchor="w")
        self._status_lbl.pack(fill=tk.X, padx=14, pady=(0, 3))
        paned = tk.PanedWindow(self, orient=tk.VERTICAL, bg=BG_DARK, sashwidth=5, sashrelief=tk.FLAT, bd=0)
        paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 4))

        twrap = tk.Frame(paned, bg=BG_DARK)
        cols = ("status", "file", "fmt", "car", "folder", "dest")
        self._results_tree = ttk.Treeview(twrap, columns=cols, show="headings", height=8, style="Copy.Treeview")
        for cid, text, w in [
            ("status", "Status", 100), ("file", "Datei", 220), ("fmt", "Fmt", 36),
            ("car", "Auto (Alias)", 120), ("folder", "iRacing-Ordner", 140), ("dest", "Zielpfad", 360),
        ]:
            self._results_tree.heading(cid, text=text)
            self._results_tree.column(cid, width=w, minwidth=40, stretch=(cid == "dest"))
        tvsb = ttk.Scrollbar(twrap, orient="vertical",   command=self._results_tree.yview)
        thsb = ttk.Scrollbar(twrap, orient="horizontal", command=self._results_tree.xview)
        self._results_tree.configure(yscrollcommand=tvsb.set, xscrollcommand=thsb.set)
        self._results_tree.grid(row=0, column=0, sticky="nsew")
        tvsb.grid(row=0, column=1, sticky="ns")
        thsb.grid(row=1, column=0, sticky="ew")
        twrap.grid_rowconfigure(0, weight=1)
        twrap.grid_columnconfigure(0, weight=1)
        self._results_tree.bind("<Double-1>", self._on_results_double_click)
        self._results_tree.tag_configure("ready", foreground=GREEN)
        self._results_tree.tag_configure("warn",  foreground=YELLOW)
        self._results_tree.tag_configure("err",   foreground=ACCENT)
        self._results_tree.tag_configure("dim",   foreground=FG_DIM)
        paned.add(twrap, minsize=100)

        lw = tk.Frame(paned, bg=BG_MID)
        tk.Label(lw, text="LOG", bg=BG_MID, fg=ACCENT, font=("Segoe UI", 8, "bold")).pack(fill=tk.X, padx=6, pady=(4, 2))
        self.log = tk.Text(lw, bg=BG_MID, fg=FG_MAIN, font=FONT_MONO,
                           relief="flat", state=tk.DISABLED, wrap="none",
                           insertbackground=FG_MAIN, selectbackground=BG_SEL)
        for tag, color in [("ok", GREEN), ("warn", YELLOW), ("error", ACCENT), ("dim", FG_DIM), ("head", FG_HEAD)]:
            self.log.tag_configure(tag, foreground=color)
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
        bg = p["bg"] if hasattr(p, "keys") else BG_DARK
        return tk.Label(p, text=txt, bg=bg, fg=ACCENT, font=("Segoe UI", 8, "bold"))

    def _dir_row_combo(self, p, lbl, var, cmd, which: str):
        row = tk.Frame(p, bg=BG_PANEL)
        row.pack(fill=tk.X, pady=3)
        tk.Label(row, text=lbl, bg=BG_PANEL, fg=FG_HEAD,
                 font=FONT_UI, width=26, anchor="w").pack(side=tk.LEFT)
        combo = ttk.Combobox(row, textvariable=var, values=[], style="Dark.TCombobox", font=FONT_UI)
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
        state = tk.NORMAL if self.mode_var.get() in ("season", "both") else tk.DISABLED
        self.season_entry.config(state=state, fg=FG_MAIN if state == tk.NORMAL else FG_DIM)

    def _set_status_scan(self, plan: list[StoPlanEntry]) -> None:
        n_ready   = sum(1 for e in plan if e.ready)
        n_alias   = sum(1 for e in plan if e.status == "no_alias")
        n_fmt     = sum(1 for e in plan if e.status == "bad_format")
        n_dup     = sum(1 for e in plan if e.status == "duplicate_name")
        parts = [f"{len(plan)} Dateien", f"{n_ready} bereit"]
        if n_alias:
            parts.append(f"{n_alias} kein Alias")
        if n_fmt:
            parts.append(f"{n_fmt} Format?")
        if n_dup:
            parts.append(f"{n_dup} doppelt")
        perfect = n_ready == len(plan)
        self._status_lbl.config(
            text="  \U0001f4ca  " + "  \u00b7  ".join(parts),
            fg=GREEN if perfect else YELLOW,
        )

    def _set_status_copy(self, ok: int, skipped: int, moving: bool, dry: bool) -> None:
        verb = "verschoben" if moving else ("geplant" if dry else "kopiert")
        parts = [f"{ok} {verb}"]
        if skipped:
            parts.append(f"{skipped} \u00fcbersprungen")
        self._status_lbl.config(
            text="  \u2714  " + "  \u00b7  ".join(parts),
            fg=GREEN if not skipped else YELLOW,
        )

    # ── Log ───────────────────────────────────────────────────────────────────
    def _wlog(self, msg, tag=""):
        self.log.config(state=tk.NORMAL)
        self.log.insert(tk.END, msg + "\n", tag)
        self.log.see(tk.END)
        self.log.config(state=tk.DISABLED)

    def _clear_log(self):
        self.log.config(state=tk.NORMAL)
        self.log.delete(1.0, tk.END)
        self.log.config(state=tk.DISABLED)

    # ── Pfad-Logik ────────────────────────────────────────────────────────────
    def _get_sto_sources(self) -> list[tuple[str, Path]] | None:
        src = self.source_var.get()
        if not os.path.isdir(src):
            messagebox.showerror("Fehler", f"Quellverzeichnis nicht gefunden:\n{src}")
            return None
        return collect_sto_sources(Path(src), self.recursive_var.get())

    def _status_display(self, status: str) -> str:
        return {"ready": "bereit", "bad_format": "Format?",
                "no_alias": "kein Alias", "duplicate_name": "doppelt"}.get(status, status)

    def _fill_results_tree(self, entries: list[StoPlanEntry]) -> None:
        self._results_tree.delete(*self._results_tree.get_children())
        for i, e in enumerate(entries):
            dest = str(e.dest_file) if e.dest_file else (e.detail or "—")
            tag = "ready" if e.ready else ("err" if e.status == "bad_format" else "warn")
            self._results_tree.insert("", tk.END, iid=str(i),
                values=(self._status_display(e.status), e.rel_display, e.format_label,
                        e.car or "—", e.iracing_folder or "—", dest),
                tags=(tag,))

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
        try:
            open_path_in_file_manager(e.dest_file if e.dest_file else e.src_file)
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
        plan = plan_sto_operations(
            dest_base, sources, self.alias_editor.get_alias_dict(),
            self.mode_var.get(), self.season_var.get(),
        )
        self._last_plan = plan
        return plan

    def _backup_file_if_needed(self, dest_file: Path) -> None:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        bak = dest_file.parent / f"{dest_file.name}.{ts}.bak"
        shutil.copy2(dest_file, bak)
        baks = sorted(dest_file.parent.glob(f"{dest_file.name}.*.bak"))
        for old in baks[:-BACKUP_KEEP_MAX]:
            try:
                old.unlink()
            except OSError:
                pass

    def _validate(self) -> bool:
        if self.mode_var.get() in ("season", "both") and not self.season_var.get().strip():
            messagebox.showerror("Fehler", "Bitte Season-Name eingeben.")
            return False
        return True

    def _confirm_dest_root(self, dest_base: Path) -> bool:
        if not dest_base.exists() or dest_looks_like_setups_root(dest_base):
            return True
        return messagebox.askokcancel(
            "Ziel prüfen",
            "Unter dem Ziel wurden keine bekannten iRacing-Fahrzeugordner gefunden.\n"
            'Erwartet wird meist der Ordner \u201esetups\u201c mit Unterordnern wie \u201ebmwm4gt3\u201c usw.\n\n'
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
                'Zuerst \u201eScannen\u201c ausführen \u2014 oder es gibt keine fehlenden Aliase im Plan.',
            )
            return
        existing = self.alias_editor.get_alias_dict()
        added = 0
        for car in cars_ordered:
            if car not in existing:
                self.alias_editor._append_row(car, "", "Scan")
                added += 1
        if added == 0:
            messagebox.showinfo("Fehlende Aliase",
                                "Alle erkannten Fahrzeug-Aliase sind bereits mit Ordner eingetragen.")
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
        self._wlog(f"━━  Scan  ·  {len(plan)} Datei(en)  ·  {len(aliases)} Aliase geladen  ━━", "head")
        n_ready = sum(1 for e in plan if e.ready)
        n_skip  = len(plan) - n_ready
        for e in plan:
            if e.ready:
                self._wlog(f"  ✓  [Fmt-{e.format_label}]  {e.rel_display}", "ok")
                self._wlog(f"       {e.car} → {e.iracing_folder}   Strecke: {e.track}   Season: {e.season}", "dim")
                self._wlog(f"       → {e.dest_file}", "dim")
            elif e.status == "bad_format":
                self._wlog(f"  ⚠  Unbekanntes Format: {e.rel_display}", "warn")
            elif e.status == "no_alias":
                self._wlog(f"  ⚠  Kein Alias für '{e.car}': {e.rel_display}", "warn")
            else:
                self._wlog(f"  ⚠  {e.detail}: {e.rel_display}", "warn")
        self._wlog(f"\n  → {n_ready} bereit  ·  {n_skip} übersprungen", "head")
        self._set_status_scan(plan)

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

        moving    = self.move_var.get()
        dry       = self.dry_run_var.get()
        collision = self.collision_var.get()
        aliases   = self.alias_editor.get_alias_dict()
        src_base  = Path(self.source_var.get()).resolve()
        dest_base = Path(self.dest_var.get()).resolve()
        ready_entries = [e for e in plan if e.ready]

        if moving and not dry and not messagebox.askyesno(
            "Verschieben bestätigen",
            f"{len(ready_entries)} Datei(en) werden aus dem Quellordner entfernt.\n\nFortfahren?",
        ):
            return
        if not dry and not self._confirm_dest_root(dest_base):
            return

        verb = ("Vorschau (" + ("Verschieben" if moving else "Kopieren") + ")") if dry else ("Verschieben" if moving else "Kopieren")
        self._wlog(f"━━  {verb}  ·  {len(aliases)} Aliase aktiv  ━━", "head")
        self._wlog(f"  Quelle: {src_base}", "dim")
        self._wlog(f"  Ziel:   {dest_base}", "dim")
        if dry:
            self._wlog("  (Dry-Run: keine Dateien geändert)", "head")

        ok = skip = ow = coll_skip = 0
        for e in plan:
            if not e.ready:
                if e.status == "bad_format":
                    self._wlog(f"  ⚠  Unbekanntes Format: {e.rel_display}", "warn")
                elif e.status == "no_alias":
                    self._wlog(f"  ⚠  Kein Alias für '{e.car}' — im Alias-Editor eintragen: {e.rel_display}", "warn")
                else:
                    self._wlog(f"  ⚠  {e.detail}: {e.rel_display}", "warn")
                skip += 1
                continue

            src_file  = e.src_file
            dest_file = e.dest_file
            assert dest_file is not None
            existed    = dest_file.exists()
            final_dest = dest_file

            if existed and collision == "skip":
                msg = "übersprungen — Ziel existiert bereits"
                if dry:
                    self._wlog(f"  ◌  {e.rel_display}", "warn")
                    self._wlog(f"       {msg}", "dim")
                else:
                    self._wlog(f"  ◌  {e.rel_display}  ({msg})", "warn")
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
                    raise FileNotFoundError(f"Datei nach der Operation nicht vorhanden: {final_dest}")
                overwritten = existed and collision == "overwrite"
                renamed     = existed and collision == "rename" and final_dest != dest_file
                icon = "✂" if moving else ("♻" if overwritten else ("⎘" if renamed else "✓"))
                self._wlog(f"  {icon}  {e.rel_display}", "warn" if overwritten else "ok")
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
            messagebox.showinfo("Dry-Run",
                f"{ok} Operation(en) würden ausgeführt.\n"
                f"{ow} würden ein vorhandenes Ziel überschreiben.\n"
                f'{coll_skip} wegen \u201e\u00dcberspringen\u201c bei Kollision.\n'
                f"{skip} wegen Format/Alias/Duplikat.")
        else:
            self._wlog(f"\n  → {ok} {verb_past}  ({ow} überschrieben)  ·  {tail}", "head")
        self._set_status_copy(ok, skip + coll_skip, moving, dry)
