# Product Requirements Document (PRD)

# OpsCollector-CLI

### Capture Once. Report Everywhere.

**Version:** 1.0 (MVP)
**Status:** Ready for Development

---

# 1. Executive Summary

**OpsCollector-CLI** adalah aplikasi **portable berbasis Command Line Interface (CLI)** yang berfungsi sebagai **Operational Data Collection Platform** untuk tim IT.

Aplikasi ini dirancang untuk mencatat seluruh aktivitas operasional harian dalam satu tempat sehingga data dapat digunakan kembali untuk berbagai kebutuhan seperti:

* BAU Reporting
* OKR Progress Tracking
* Incident Management
* Change & Maintenance Log
* Evidence Repository
* Audit Support
* Dashboard
* Management Reporting
* Excel Import & Export

OpsCollector-CLI merupakan **fase pertama** dari roadmap digitalisasi operasional IT dan akan menjadi sumber data utama bagi aplikasi **OKR & BAU Enterprise** di masa depan.

---

# 2. Product Vision

**Capture operational data once and reuse it everywhere.**

OpsCollector-CLI menghilangkan pencatatan berulang dengan menjadikan satu input sebagai sumber data untuk berbagai laporan dan kebutuhan operasional.

---

# 3. Objectives

Membangun aplikasi yang memenuhi prinsip berikut:

* Portable (cukup copy folder)
* Tidak memerlukan database server
* Tidak memerlukan instalasi aplikasi tambahan selain Python
* Mudah dijalankan melalui PowerShell atau Command Prompt
* Mendukung penyimpanan evidence pada shared storage
* Mendukung import dan export Excel
* Siap dikembangkan menjadi backend aplikasi web

---

# 4. Technology Stack

## Core

* Python 3.13

## CLI

* Typer
* Rich

## Database

* SQLite
* SQLAlchemy

## Excel

* openpyxl

## Word

* python-docx

## PDF

* reportlab

## Image

* Pillow

## File Monitoring

* watchdog

## Configuration

* pydantic
* JSON

---

# 5. Deployment Model

Distribusi aplikasi menggunakan struktur berikut:

```text
opscollector-cli/
│
├── app/
├── database/
├── evidence/
├── export/
├── backup/
├── logs/
├── tests/
├── docs/
├── .venv/
├── setup.ps1
├── update.ps1
├── requirements.txt
├── config.json
├── main.py
├── README.md
└── opscollector.cmd
```

Instalasi dilakukan satu kali menggunakan:

```powershell
.\setup.ps1
```

Setup wajib melakukan:

* Membuat virtual environment (`.venv`)
* Menginstal seluruh dependency
* Membuat struktur folder
* Membuat database SQLite
* Menjalankan konfigurasi awal
* Membuat shortcut (`opscollector.cmd`)

Setelah instalasi selesai, pengguna cukup menjalankan:

```powershell
opscollector
```

atau

```powershell
.\opscollector.cmd
```

---

# 6. Functional Modules

## Master Data

* Objective
* Key Result
* BAU Category
* BAU Activity
* Incident Category
* Change Category
* Evidence Category
* Department
* PIC
* Priority
* Status

---

## Daily BAU

Mencatat aktivitas operasional harian beserta status, durasi, catatan, dan evidence.

---

## OKR Progress

Mencatat progres Key Result, capaian, gap, risiko, isu, dan rencana tindak lanjut.

---

## Incident Log

Mencatat insiden operasional beserta severity, root cause, resolution, PIC, dan evidence.

---

## Change & Maintenance Log

Mencatat aktivitas perubahan sistem dan preventive maintenance.

---

## Evidence Repository

Mendukung penyimpanan file:

* PNG
* JPG
* PDF
* DOCX
* XLSX
* TXT
* LOG
* ZIP

Fitur:

* Copy otomatis ke repository
* Rename otomatis
* Metadata otomatis
* Relasi ke BAU, OKR, Incident, atau Change

---

## Search

Pencarian berdasarkan:

* Tanggal
* Objective
* KR
* BAU
* Incident
* Change
* PIC
* Status
* Keyword
* Evidence

---

## Dashboard

Menampilkan ringkasan:

* Progress Objective
* Progress KR
* BAU Completion
* Incident Summary
* Outstanding Activity
* Evidence Count
* Weekly Trend

Menggunakan Rich Console.

---

## Excel Import

Harus mendukung import:

* Master Data
* Daily BAU
* OKR Progress
* Incident
* Change Log
* Evidence Metadata

Fitur wajib:

* Preview Data
* Validation
* Duplicate Detection
* Rollback jika gagal
* Template Excel standar

---

## Excel Export

Harus dapat menghasilkan:

* Daily BAU Report
* Weekly OKR Report
* Incident Report
* Evidence Register
* Summary Dashboard
* Management Report

Format:

* XLSX

---

## Backup & Restore

Backup meliputi:

* Database SQLite
* Config
* Metadata
* Export

Restore:

* Full Restore
* Selective Restore

---

# 7. Development Standards

Arsitektur wajib menggunakan:

```text
CLI
    │
Service Layer
    │
Repository Layer
    │
SQLite
```

Business logic **tidak boleh** berada pada layer CLI.

Seluruh konfigurasi harus berasal dari `config.json`.

Gunakan:

* Type Hints
* Logging
* Exception Handling
* Transaction Management
* Unit Test
* SOLID Principles

---

# 8. Non Functional Requirements

* Startup kurang dari 3 detik.
* Windows 11 compatible.
* Offline First.
* Portable.
* Tidak membutuhkan database server.
* Tidak membutuhkan Docker.
* Tidak membutuhkan PostgreSQL.
* Seluruh dependency dikelola oleh `setup.ps1`.
* Mendukung minimal RAM 4 GB.

---

# 9. Acceptance Criteria

Aplikasi dinyatakan selesai apabila:

* Dapat digunakan setelah menjalankan `setup.ps1`.
* Seluruh dependency Python terinstal otomatis.
* Menggunakan SQLite sebagai database.
* Mendukung import dan export Excel.
* Evidence tersimpan dengan struktur folder yang konsisten.
* Dashboard CLI berjalan dengan baik.
* Backup dan restore berhasil.
* Struktur proyek modular dan siap digunakan kembali pada aplikasi web.

---

# 10. Future Roadmap

## Version 1.0

* CLI
* SQLite
* BAU
* OKR
* Incident
* Change
* Evidence
* Dashboard
* Excel Import
* Excel Export

## Version 2.0

* SharePoint Integration
* Auto Upload Evidence
* Reminder
* Notification
* Dashboard HTML

## Version 3.0

* REST API
* Web Application
* Microsoft 365 Login
* Power BI Integration
* AI Assistant

---

# 11. Product Philosophy

**OpsCollector-CLI** adalah aplikasi **Offline-First, Portable, Modular, dan Enterprise-Ready**.

Setiap fitur harus dirancang agar **business logic dapat digunakan kembali** pada aplikasi web di masa depan tanpa perlu penulisan ulang. Antarmuka CLI hanyalah media interaksi; seluruh logika bisnis harus tetap independen dan mudah diintegrasikan dengan API atau UI lain.
