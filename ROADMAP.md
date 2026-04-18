# iRacing Setup Manager – Roadmap & Verbesserungsplan

Dieses Dokument sammelt Ideen und einen priorisierten Plan, wie das Projekt weiterentwickelt und verbessert werden kann. Es dient als dauerhafte Referenz – Punkte können ergänzt, verschoben oder abgehakt werden.

Letzte Aktualisierung: 2026-04-18

---

## Überblick: Aktueller Stand

- **Umfang:** Single-File Python/Tkinter GUI ([iracing_setup_manager.py](iracing_setup_manager.py), ~1514 Zeilen)
- **Tests:** Pytest vorhanden ([tests/test_iracing_setup_manager.py](tests/test_iracing_setup_manager.py)) – nur reine Logik-Tests, keine GUI
- **Build/Release:** GitHub Actions Workflow für Windows `.exe` via PyInstaller ([.github/workflows/release.yml](.github/workflows/release.yml))
- **Persistenz:** `~/.iracing_setup_manager.json` + `~/.iracing_aliases.json`
- **Formate:** A / B / C (VRS-Stil) werden erkannt
- **Plattformen:** Primär Windows, Code ist cross-platform-freundlich geschrieben

---

## 1. Code-Qualität & Architektur

### 1.1 Modularisierung (High Priority)
Die ~1500 Zeilen in einer Datei werden unübersichtlich. Aufteilen in Module:

- `core/` – reine Logik (formats, planning, filesystem)
  - `formats.py` → `detect_format`, `stem_format_label`
  - `planner.py` → `StoPlanEntry`, `plan_sto_operations`
  - `paths.py` → `build_dest_path`, `pick_rename_destination`, `collect_sto_sources`
  - `config.py` → Laden/Speichern Config + Aliases
- `gui/` – Tkinter Views
  - `app.py` → Haupt-App
  - `tab_copy.py` → Setup-Kopieren Tab
  - `tab_alias.py` → Alias-Editor Tab
  - `theme.py` → Farben/Fonts (derzeit oben in der Datei)
- `data/` – Statische Daten
  - `iracing_folders.py` → `IRACING_FOLDERS` Liste

**Nutzen:** Tests leichter, Refactoring sicherer, neue Features fokussierter.

### 1.2 Type-Hints & Statische Analyse
- Durchgängige Typisierung prüfen (läuft schon gut, aber nicht komplett)
- `mypy --strict` oder `pyright` in CI einbinden
- `ruff` für Linting + Formatting (schneller & moderner als `flake8`+`black`)

### 1.3 iRacing-Ordnerliste aktualisierbar machen
Die Liste `IRACING_FOLDERS` ist hardcoded und veraltet schnell (iRacing bringt ~4× jährlich neue Autos).
- Als externe JSON/YAML-Datei auslagern
- Optional: Auto-Scan des iRacing-Setups-Ordners als Quelle der Wahrheit
- Update-Check Funktion (z. B. gebundelte Liste + User-Override)

### 1.4 Logging statt `print`/GUI-Log mischen
- `logging` Modul einsetzen, mehrere Handler (GUI + optional Datei)
- Log-Level einstellbar (DEBUG/INFO)
- Debug-Log-Datei neben Config speichern für Support-Fälle

---

## 2. Features

### 2.1 Setup-Verwaltung (Medium Priority)
- **Undo:** Letzte Copy/Move-Operation rückgängig machen (Journal in JSON persistieren)
- **Dry-Run-Toggle:** Explizit sichtbar im UI statt nur via Scan
- **Duplikat-Strategien auswählbar:** überschreiben / `_v2` / überspringen / nach Timestamp entscheiden
- **Setup-Historie:** Welche Setups wurden wann wohin kopiert? (SQLite oder JSONL)

### 2.2 Erweiterte Format-Erkennung
- Heuristik für Format C weniger anfällig machen (derzeit: CamelCase-Check)
- User-definierbare Regex-Patterns für firmenspezifische Benennungen
- "Alias vorschlagen" bei unbekanntem Auto (Fuzzy-Match auf `IRACING_FOLDERS`)

### 2.3 Alias-Editor Verbesserungen
- Import/Export Alias-Sets (JSON teilen zwischen Nutzern)
- Bulk-Edit / Suchen-Ersetzen
- Versionierung: Alias-Datei als Historie speichern
- Validierung von Ordnern beim Start (fehlende iRacing-Ordner markieren)

### 2.4 Weitere Quellen
- Mehrere Quellordner gleichzeitig
- Watch-Mode: Quellordner beobachten, neue `.sto` automatisch einsortieren
- Integration mit Download-Ordnern (auto-scan `~/Downloads` nach `.sto`)

### 2.5 Integration mit iRacing-Ökosystem
- Session-Info aus iRacing Telemetrie? (ambitiös)
- Link zu Garage61 / VRS / iRacing-Guide je Setup (URL-Template)

---

## 3. UX & GUI

### 3.1 Konsistenz & Polish
- Keyboard-Shortcuts dokumentieren + anzeigen (F5 = Scan, Ctrl+C/V = Copy/Move, etc.)
- Statusbar mit Fortschritt bei größeren Operationen
- Tooltips bei allen Buttons und Feldern
- Dark/Light-Theme-Umschalter (aktuell nur dark)

### 3.2 Accessibility
- Schriftgröße skalierbar (oder System-DPI respektieren)
- Farbkontraste gegen WCAG prüfen
- Screen-Reader freundliche Labels

### 3.3 Fehlerkommunikation
- Klare Fehlermeldungen mit Handlungsanweisung
- "Kopieren, aber 2 Warnungen" – Warnungen zusammenfassen statt pro Datei
- Notifications am Ende großer Operationen

---

## 4. Tests

### 4.1 Coverage erhöhen
- Aktuelle Tests nur für `detect_format` + `build_dest_path`
- Noch fehlend:
  - `plan_sto_operations` – Happy Path, duplicate_name, no_alias, bad_format
  - `collect_sto_sources` – flach vs. rekursiv
  - `merge_path_history` – Edge Cases
  - `pick_rename_destination` – Kollisionen
  - `load_aliases_json_file` – fehlerhafte JSONs
- Ziel: >80% Coverage auf `core/`-Modulen

### 4.2 GUI-Tests
- Smoke-Test: App startet ohne Crash (subprocess + `--help` oder headless tkinter)
- `pytest-tk` oder händisch gemockte Events
- Snapshot-Tests für Dialog-Strukturen

### 4.3 Integration-Tests
- Temp-Verzeichnisse mit echten `.sto`-Dummies + Ende-zu-Ende Copy/Move prüfen
- Windows-specific Path-Verhalten im CI abdecken

---

## 5. CI/CD

### 5.1 Erweiterter Workflow
- Tests bei jedem Push/PR laufen lassen (nicht nur beim Tag)
- Lint-Stufe (ruff) vor Build
- Coverage-Report als Artefakt
- Matrix: Python 3.11 / 3.12 / 3.13

### 5.2 Release Automatisierung
- Changelog aus Commit-Messages generieren (conventional commits → `git-cliff`)
- Version aus Git-Tag direkt ins Binary einbrennen (sichtbar im About-Dialog)
- Notarization/Signing für Windows (SmartScreen-Warnung entfernen, langfristig)
- macOS + Linux Builds ergänzen (auch wenn iRacing primär Win ist)

### 5.3 Distribution
- Portable Version + Installer (Inno Setup oder NSIS)
- Optional: Chocolatey / Winget Paket
- Auto-Update-Check (gegen GitHub Releases API)

---

## 6. Dokumentation

### 6.1 README-Ergänzungen
- Screenshots pro Feature (Unterordner-Modi, Alias-Editor)
- Kurze GIFs/MP4 für Workflows
- FAQ: häufige Probleme (Pfade, Berechtigungen, doppelte Namen)

### 6.2 Weitere Docs
- `CONTRIBUTING.md` – Setup der Dev-Umgebung
- `CHANGELOG.md` – Versionshistorie
- Architektur-Skizze (1 Seite), was wo passiert
- User-Manual als eigene Datei oder GitHub Pages

### 6.3 In-App Hilfe
- `?`-Button pro Tab mit Kurzerklärung
- "Erste Schritte"-Dialog beim ersten Start

---

## 7. Maintenance / Refactoring

### 7.1 Altlasten
- Doppelte Konstanten konsolidieren (z. B. `COL_*`-Indices)
- Magic Numbers in benannte Konstanten
- Inline-Kommentare reduzieren, Code sprechender machen

### 7.2 Abhängigkeiten
- `requirements.txt` und `requirements-dev.txt` in `pyproject.toml` zusammenführen
- `uv` oder `hatch` als moderner Projekt-Manager

### 7.3 Plattform-Kompatibilität
- Linux/macOS-Support getestet? (Pfade mit Path, scheint OK)
- Zeichensatz-Probleme bei Umlauten in Alias/Notiz prüfen
- Backup-Funktion für die Config-Dateien

---

## Priorisierte Nächste Schritte (Vorschlag)

Eine mögliche Reihenfolge, wenn begrenzt Zeit zur Verfügung steht:

1. **Tests ausbauen** (§4.1) – sichert alle folgenden Änderungen ab
2. **CI erweitern** (§5.1) – Tests + Lint bei jedem Push
3. **Modularisierung** (§1.1) – erst dann sind Feature-Arbeiten sicher
4. **iRacing-Ordnerliste extrahieren** (§1.3) – niedrig-hängende Frucht, hoher Nutzwert
5. **Undo + Historie** (§2.1) – häufigster User-Wunsch bei File-Movern
6. **Watch-Mode** (§2.4) – echter Workflow-Booster
7. **Auto-Update-Check** (§5.3) – hebt Wahrnehmung als "gepflegtes Tool"

---

## Offene Fragen / zu klären

- Soll das Tool auch `.olsetup`, `.rpy` o. ä. unterstützen?
- Gibt es Nutzer außerhalb von Windows? (beeinflusst Cross-Platform-Aufwand)
- Soll es einen "Headless"-CLI-Modus geben für Power-User / Automation?
- Monetarisierung/Spende vs. reines Hobby-Projekt?

---

## Änderungshistorie dieses Dokuments

- 2026-04-18: Erstfassung
