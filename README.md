# OpsCollector-CLI

> **Capture Once. Report Everywhere.**

OpsCollector-CLI is a portable, offline-first operations collector for Windows. It helps IT and operations teams consolidate daily BAU activity, incidents, changes, OKR progress, and related evidence into a structured local SQLite database — then export it for reporting.

---

## Overview

OpsCollector-CLI is built for Indonesian-market operations teams who need fast, structured data capture without relying on networked ticketing tools. It captures operational data at the source and generates reports, exports, and audits from a single, self-contained package.

The architecture separates CLI presentation from business logic and repositories, so future web or API surfaces can reuse the same backend without re-implementing rules.

## Features

- **Master data**: reusable reference lists (activities, categories, people, departments, statuses, etc.).
- **Daily BAU**: log routine operational work with duration, status, and ownership.
- **OKR tracking**: record progress per Key Result with value, gap, risk, and action plan.
- **Incident logging**: capture incidents with severity, root cause, resolution, and MTTR.
- **Change management**: log changes and maintenance windows with type, schedule, and outcome.
- **Evidence repository**: attach files and images with year/month storage and metadata.
- **Search**: single-query search across BAU, OKR, incidents, and changes.
- **Dashboard**: terminal-based summary and weekly trend views.
- **Excel import/export**: generate templates, preview, import, and export XLSX reports.
- **Backup / Restore**: full backup of database, config, and exports; selective restores.

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Runtime | Python 3.11+ |
| CLI framework | Typer |
| Terminal UI | Rich |
| Persistence | SQLite via SQLAlchemy 2 |
| Documents | openpyxl, python-docx, reportlab |
| Images | Pillow |
| File monitoring | watchdog |
| Configuration | JSON + Pydantic |

---

## Directory Structure

```
D:\My Works\opscollector-cli\
├── app/
│   ├── cli/            # Typer command modules
│   │   ├── master_cmd.py
│   │   ├── bau_cmd.py
│   │   ├── okr_cmd.py
│   │   ├── incident_cmd.py
│   │   ├── change_cmd.py
│   │   ├── evidence_cmd.py
│   │   ├── search_cmd.py
│   │   ├── dashboard_cmd.py
│   │   ├── excel_cmd.py
│   │   └── backup_cmd.py
│   ├── services/       # Business logic
│   ├── database/       # Repository + SQLAlchemy models
│   ├── templates/      # Excel/export templates
│   └── __init__.py
├── database/           # SQLite database files
├── evidence/           # Binary evidence storage (YYYY/MM subfolders)
├── export/             # Generated Excel/PDF/DOCX exports
├── backup/             # Timestamped backup archives
├── logs/               # Runtime logs
├── docs/               # Additional documentation
├── tests/              # Pytest suite
├── .venv/              # Isolated Python environment
├── config.json         # App configuration
├── main.py             # Typer application entry point
├── opscollector.cmd    # Windows launcher
├── requirements.txt    # Python dependencies
├── setup.ps1           # One-time setup
├── update.ps1          # Dependency + schema update
└── README.md
```

---

## System Requirements

- Windows 10/11
- PowerShell 5.1 or newer
- Python **3.11+**
- Internet access on first run for dependency download

---

## Installation

From the project root, run:

```powershell
powershell -ExecutionPolicy Bypass -File .\setup.ps1
```

`setup.ps1` will:

1. Verify Python availability.
2. Create `.venv` if missing.
3. Upgrade `pip`.
4. Install dependencies from `requirements.txt`.
5. Create required folders: `database`, `evidence`, `export`, `backup`, `logs`, `docs`, `app\templates`.
6. Initialise the SQLite database.
7. Create `opscollector.cmd` if it does not exist.

After setup you can launch the CLI using:

```powershell
.\opscollector.cmd
```

or

```powershell
.\.venv\Scripts\python.exe main.py --help
```

---

## Updating

To upgrade dependencies and refresh the database schema:

```powershell
.\update.ps1
```

`update.ps1` runs `pip install --upgrade -r requirements.txt` and re-runs `init_db`, which is safe to call repeatedly.

---

## Usage

### Global options

```powershell
.\opscollector.cmd --help
.\opscollector.cmd --version
```

### Master data

List master entity types:

```powershell
.\opscollector.cmd master types
```

List all records of an entity:

```powershell
.\opscollector.cmd master list status
.\opscollector.cmd master list person
```

Add a master record:

```powershell
.\opscollector.cmd master add status --name "In Progress" --desc "Work is ongoing"
```

Remove a master record:

```powershell
.\opscollector.cmd master rm status 3
```

### Daily BAU

Add a BAU record:

```powershell
.\opscollector.cmd bau add --date 2026-07-08 --title "Patch apply" --status 4 --duration 30 --notes "Tested after patch"
```

List BAU records:

```powershell
.\opscollector.cmd bau list --from 2026-07-01 --to 2026-07-31 --status 4 --limit 50
```

Show a single BAU record:

```powershell
.\opscollector.cmd bau show 12
```

Remove a BAU record:

```powershell
.\opscollector.cmd bau rm 12
```

### OKR progress

Add OKR progress:

```powershell
.\opscollector.cmd okr add --kr 1 --date 2026-07-08 --value 0.65 --gap 0.35 --progress 65 --achievement "API v2 deployed" --risk "None" --issue "None" --action "Start UAT next week"
```

List OKR progress:

```powershell
.\opscollector.cmd okr list --kr 1 --limit 50
```

### Incident logging

Add an incident:

```powershell
.\opscollector.cmd incident add --date 2026-07-08 --title "DB latency spike" --cat 2 --severity High --res-min 45 --status 2
```

List incidents:

```powershell
.\opscollector.cmd incident list --from 2026-07-01 --to 2026-07-31 --severity High --limit 50
```

### Change management

Add a change:

```powershell
.\opscollector.cmd change add --date 2026-07-08 --title "DNS migration" --cat 1 --type Change --status 3 --start 2026-07-09 22:00 --end 2026-07-10 02:00
```

List changes:

```powershell
.\opscollector.cmd change list --from 2026-07-01 --to 2026-07-31 --type Change --limit 50
```

### Evidence repository

Attach a file as evidence:

```powershell
.\opscollector.cmd evidence add "C:\Users\ops\screenshot.png" --title "Login error" --cat 1 --by "ops" --entity incident --entity-id 1
```

List evidence:

```powershell
.\opscollector.cmd evidence list --entity incident --entity-id 1 --limit 50
```

Get the stored path of evidence:

```powershell
.\opscollector.cmd evidence path 7
```

Remove evidence but keep the file:

```powershell
.\opscollector.cmd evidence rm 7 --keep-file
```

### Search

Search across modules:

```powershell
.\opscollector.cmd search run --kw "latency" --from 2026-07-01 --status 2 --type incident --type bau
```

### Dashboard

Show operational summary:

```powershell
.\opscollector.cmd dashboard show
```

Weekly trend:

```powershell
.\opscollector.cmd dashboard weekly --weeks 6
```

Objective progress:

```powershell
.\opscollector.cmd dashboard objectives
```

### Excel import/export

Generate import templates:

```powershell
.\opscollector.cmd excel templates --out .\export\templates
```

Preview an Excel file:

```powershell
.\opscollector.cmd excel preview ".\export\daily_bau.xlsx" --sheet "Sheet1"
```

Import data from Excel:

```powershell
.\opscollector.cmd excel import ".\export\daily_bau.xlsx" daily_bau --skip-dup
```

Export a report:

```powershell
.\opscollector.cmd excel export bau --out .\export\bau_report.xlsx
.\opscollector.cmd excel export management --out .\export\management.xlsx
```

### Backup and restore

Create a backup:

```powershell
.\opscollector.cmd backup create --label "pre-migration"
```

List backups:

```powershell
.\opscollector.cmd backup list
```

Restore from a backup:

```powershell
.\opscollector.cmd backup restore "20260101_120000" --only database --only export
```

---

## Architecture

```
CLI (main.py, app/cli/*.py)
    ↓
Services (app/services/*_service.py)
    ↓
Repositories (app/database/*_repo.py)
    ↓
SQLite via SQLAlchemy
```

- **CLI**: Typer commands only. No business logic in CLI modules.
- **Services**: orchestrates rules, transformations, and formatting.
- **Repositories**: SQL queries and data access.
- **Database**: initialized via `init_db()` and self-contained in `database/`.

This separation keeps business logic reusable for future web or API interfaces without rewriting domain logic.

---

## Evidence Storage

Evidence files are stored under `evidence/` in year/month folders, for example:

```
evidence\
└── 2026\
    └── 07\
        └── 20260708104522_incident-1_screenshot.png
```

Files are copied into the repository and referenced by database record. Use `evidence path <id>` to retrieve the absolute path.

---

## Notes

- Configuration lives in `config.json` at the project root.
- Logs are written to `logs/`.
- The application is offline-first; no internet connection is required after setup.
- Activate the virtual environment manually if needed: `.\.venv\Scripts\Activate.ps1`

---

## License

MIT License — see `LICENSE` for details.

Copyright (c) OpsCollector-CLI contributors.
