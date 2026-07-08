# OpsCollector-CLI — Product Idea & Roadmap

> Capture Once. Report Everywhere.

## Concept
A portable, offline-first CLI operational data collection platform for IT teams.
Single input becomes the source of truth for BAU, OKR, Incident, Change reports,
evidence, audits, and dashboards.

## Why
Eliminates repeated manual logging. One capture, many reports.

## Architecture (non-negotiable)
```
CLI (Typer + Rich)
   -> Service Layer (business logic, reusable)
      -> Repository Layer (data access)
         -> SQLite
```
Business logic never lives in the CLI. All config from `config.json`.
Logic must be reusable by a future web/API backend.

## Stack
Python 3.11+ · Typer · Rich · SQLAlchemy 2.0 · openpyxl · python-docx ·
reportlab · Pillow · watchdog · pydantic · SQLite.

## MVP Modules (v1.0)
- Master Data (Objective, Key Result, BAU/Incident/Change/Evidence categories,
  Department, PIC, Priority, Status)
- Daily BAU, OKR Progress, Incident Log, Change & Maintenance Log
- Evidence Repository (auto copy/rename/metadata, link to any entity)
- Search (date, entity, PIC, status, keyword)
- Dashboard (Rich console summaries + weekly trend)
- Excel Import (preview/validate/dedup/rollback) & Export (6 XLSX reports)
- Backup & Restore (full + selective)
- File watcher (auto-ingest from shared folder)

## Roadmap
- v2.0: SharePoint, auto-upload, reminders, notifications, HTML dashboard
- v3.0: REST API, web app, M365 login, Power BI, AI assistant

## Status
v1.0 MVP implemented and verified (CLI, services, DB, Excel, evidence, backup, watch).
