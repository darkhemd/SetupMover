# Architecture

## Layer Overview

```
┌────────────────────────────────────────────────────┐
│                     gui/                           │
│  app.py   tab_copy.py   tab_alias.py              │
│  widgets.py   theme.py                            │
├────────────────────────────────────────────────────┤
│                    core/                           │
│  config.py   formats.py   paths.py   planner.py  │
├────────────────────────────────────────────────────┤
│                    data/                           │
│  default_aliases.py   iracing_folders.py          │
└────────────────────────────────────────────────────┘
```

**Dependency rule:** `core/` imports only stdlib and `data/` — never `gui/`. `gui/` imports from `core/` and `data/`, never the reverse.

## Module Responsibilities

| Module | Responsibility |
|--------|----------------|
| `core/formats.py` | Filename parsing: `_classify`, `detect_format`, `stem_format_label`, `parse_sto_header` |
| `core/paths.py` | File discovery (`collect_sto_sources`), path computation (`build_dest_path`), OS integration |
| `core/planner.py` | Plan generation (`plan_sto_operations`) and execution (`execute_copy_plan`), alias loading |
| `core/config.py` | App-wide constants; reads `IRACING_SETUP_MANAGER_CONFIG_DIR` env var for portable mode |
| `data/iracing_folders.py` | Static list/set of known iRacing vehicle folder names |
| `data/default_aliases.py` | Seed aliases loaded on first run |
| `gui/app.py` | `App(tk.Tk)` — main window, config load/save, mousewheel routing |
| `gui/tab_copy.py` | Copy/scan tab: source/dest selection, plan display, watch mode |
| `gui/tab_alias.py` | Alias editor tab: table UI, import/export |
| `gui/widgets.py` | Reusable widgets: `AutoEntry`, `ErrorDialog`, `PreviewDialog` |
| `gui/theme.py` | Color and font constants |

## Entry Points

- `iracing_setup_manager.py:main()` — dispatches to GUI or CLI; pre-parses `--config-dir`
- `cli.py:run_cli()` — headless scan via argparse
- `gui/app.py:App` — tkinter main window

## Where Does New Code Go?

- **New file format?** → `core/formats.py`
- **New path/discovery logic?** → `core/paths.py`
- **New copy/plan logic?** → `core/planner.py`
- **New reusable widget?** → `gui/widgets.py`
- **New iRacing folder names?** → `data/iracing_folders.py`
- **New app-wide constant?** → `core/config.py`

## Portable Mode

Set the environment variable `IRACING_SETUP_MANAGER_CONFIG_DIR` to redirect config and alias files away from `~`:

```sh
IRACING_SETUP_MANAGER_CONFIG_DIR=/path/to/usb iracing-setup-manager
```

Or use the CLI flag (GUI and CLI):

```sh
iracing-setup-manager --config-dir /path/to/usb
```
