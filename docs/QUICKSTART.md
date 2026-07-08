# Quick Start — OpsCollector-CLI

**Capture Once. Report Everywhere.**

## 1. Install (one time)

```powershell
powershell -ExecutionPolicy Bypass -File .\setup.ps1
```

This creates `.venv`, installs dependencies, builds the folder structure, and
initialises the SQLite database with seeded statuses/priorities.

## 2. Run

```powershell
opscollector          # or
.\opscollector.cmd
```

## 3. Common commands

```powershell
# Master data
python main.py master add department --name "IT Ops"
python main.py master add pic --name "Budi" --department 1
python main.py master list status

# Daily BAU
python main.py bau add --date 2026-07-08 --title "Server patch" --status 4
python main.py bau list

# OKR / Incident / Change
python main.py incident add --date 2026-07-08 --title "DB slow" --severity High
python main.py change add --date 2026-07-08 --title "FW upgrade" --type Maintenance

# Evidence
python main.py evidence add C:\path\to\file.png --entity bau --entity-id 1

# Dashboard
python main.py dashboard show
python main.py dashboard weekly

# Search
python main.py search run --kw "patch" --from 2026-07-01

# Excel
python main.py excel templates
python main.py excel import file.xlsx daily_bau
python main.py excel export management

# Backup / Restore
python main.py backup create --label daily
python main.py backup restore backup-YYYYMMDD-HHMMSS-daily

# Auto-ingest (watchdog)
python main.py watch start \\shared\evidence-drop
```

## 4. Where data lives

- Database: `database/opscollector.db` (SQLite, portable)
- Evidence: `evidence/YYYY/MM/<uuid>.<ext>`
- Exports: `export/*.xlsx`
- Backups: `backup/backup-<stamp>-<label>/`

All configuration is in `config.json` at the project root.
