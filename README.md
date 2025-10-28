
# Scalper Journal – Streamlit + GitHub (no servers, no webhooks)

Ein extrem einfaches **Streamlit**-Journal, das deine Trades direkt als CSV ins **GitHub-Repo** schreibt
(mittels GitHub Contents API). Kein FastAPI, keine Datenbanken, nur **Streamlit + GitHub**.

## Features
- Minimaler Input (Entry/SL/TP), **R:R automatisch** und korrekt
- Journal-Ansicht mit Filter
- KPIs (P/L, Winrate, Ø R:R) + CSV-Download
- **Persistenz über GitHub**: `data/journal.csv` wird per Commit aktualisiert
- Optional: Screenshot-Upload → wird als Datei in `data/screenshots/` in dein Repo committet

## Grenzen (wichtig)
- **Keine TradingView-Webhooks** (Streamlit Cloud kann keine externen POSTs empfangen).
- Import von TradingView: kopiere Infos manuell oder nutze CSV-Import (optional Ausbaustufe).

## Quickstart (lokal)
```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

## Deployment auf Streamlit Community Cloud
1. Dieses Projekt in ein **öffentliches GitHub-Repo** pushen.
2. Auf https://share.streamlit.io → **New app** → dein Repo wählen.
3. Unter **Secrets** eintragen:
```
GITHUB_TOKEN = <Personal Access Token mit repo-Rechten>
REPO_OWNER   = <dein Nutzername oder Orga>
REPO_NAME    = <Repo-Name>
BRANCH       = main
```
4. App starten. Alle Einträge landen als Commits in `data/journal.csv` (und Screenshots in `data/screenshots/`).

## Sicherheit
- Token liegt nur in Streamlit **Secrets** (nicht im Code, nicht im Repo).
- Commits werden mit „Scalper Journal Bot“ Message erstellt.

Viel Spaß! 🔥
