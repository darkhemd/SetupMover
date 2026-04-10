# Release erstellen (VSCode + GitHub Actions)

Diese Anleitung erstellt automatisch eine Windows-`.exe` und hängt sie an einen GitHub Release.

## Voraussetzung (einmalig)

- Workflow-Datei ist im Repo vorhanden: `.github/workflows/release.yml`
- Änderungen sind committed und nach GitHub gepusht.

## Release auslösen

Im VSCode-Terminal:

```bash
git add .
git commit -m "Prepare release"
git push

git tag v1.0.0
git push origin v1.0.0
```

## Was dann automatisch passiert

Beim Tag-Push (`v*`) startet GitHub Actions:

1. Windows-Runner wird gestartet
2. Python + Dependencies werden installiert
3. `pyinstaller "iRacing Setup Manager.spec"` wird ausgeführt
4. GitHub Release wird erstellt
5. Asset wird hochgeladen: `dist/iRacing Setup Manager.exe`

## Ergebnis prüfen

1. GitHub Repository öffnen
2. Tab **Actions**: Workflow-Lauf muss grün sein
3. Tab **Releases**: Release öffnen
4. Prüfen, ob `iRacing Setup Manager.exe` als Asset vorhanden ist

## Häufige Fehler

1. Tag existiert schon: neue Version verwenden, z. B. `v1.0.1`
2. Build schlägt fehl: Action-Log öffnen und fehlendes Paket in `requirements.txt` ergänzen
3. Falscher Tag-Name: Der Workflow reagiert nur auf Tags mit `v` (z. B. `v2.3.0`)
