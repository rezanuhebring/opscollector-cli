<#
.SYNOPSIS
One-time setup for OpsCollector-CLI.

.DESCRIPTION
Creates the .venv, installs dependencies, structures folders, seeds the SQLite
database, and writes the opscollector.cmd launcher if missing.
#>

param (
    [switch]$Force
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# ── helpers ──────────────────────────────────────────────────────────────────
function Write-Banner {
    param([string]$Text)
    $bar = "=" * 70
    Write-Host ""
    Write-Host $bar -ForegroundColor Cyan
    Write-Host $Text -ForegroundColor Cyan
    Write-Host $bar -ForegroundColor Cyan
    Write-Host ""
}

function Write-Step {
    param([string]$Text)
    Write-Host "[*] $Text" -ForegroundColor Yellow
}

function Write-Success {
    param([string]$Text)
    Write-Host "[+] $Text" -ForegroundColor Green
}

function Write-Fail {
    param([string]$Text)
    Write-Host "[!] $Text" -ForegroundColor Red
}

# ── script root / paths ──────────────────────────────────────────────────────
$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Push-Location $ScriptRoot

Write-Banner "OpsCollector-CLI Setup"

# ── Python check ─────────────────────────────────────────────────────────────
Write-Step "Checking Python availability (>= 3.11 recommended)..."
$pythonCmd = $null
try {
    $pythonCmd = Get-Command python -ErrorAction Stop
} catch {
    Write-Fail "Python not found on PATH. Install Python >= 3.11 and retry."
    exit 1
}

$pyVersionRaw = & python --version 2>&1
$pyVersionRaw = $pyVersionRaw -replace 'Python ', ''
$pyMajor = [int]($pyVersionRaw.Split('.')[0])

if ($pyMajor -lt 3) {
    Write-Fail "Python 3 required; found $pyVersionRaw."
    exit 1
}

Write-Success "Found Python $pyVersionRaw ($($pythonCmd.Source))"

# ── virtual environment ──────────────────────────────────────────────────────
$venvDir = Join-Path $ScriptRoot ".venv"
$venvPython = Join-Path $venvDir "Scripts\python.exe"

Write-Step "Virtual environment path: $venvDir"

if (-not (Test-Path $venvPython)) {
    if (Test-Path $venvDir) {
        Write-Fail ".venv exists but $venvPython is missing. Remove .venv and rerun."
        exit 1
    }
    Write-Step "Creating virtual environment..."
    python -m venv .venv
    if (-not (Test-Path $venvPython)) {
        Write-Fail "Failed to create virtual environment."
        exit 1
    }
    Write-Success "Virtual environment created."
} else {
    Write-Success "Virtual environment already exists."
}

# ── pip bootstrap & dependencies ─────────────────────────────────────────────
Write-Step "Upgrading pip..."
& $venvPython -m pip install --upgrade pip | Out-Null

Write-Step "Installing dependencies from requirements.txt..."
if (-not (Test-Path (Join-Path $ScriptRoot "requirements.txt"))) {
    Write-Fail "requirements.txt not found in project root."
    exit 1
}
& $venvPython -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Fail "Dependency installation failed."
    exit 1
}
Write-Success "Dependencies installed."

# ── folder structure ─────────────────────────────────────────────────────────
Write-Step "Creating required folder structure..."
$folders = @(
    "database",
    "evidence",
    "export",
    "backup",
    "logs",
    "docs",
    "app\templates"
)

foreach ($f in $folders) {
    New-Item -ItemType Directory -Path $f -Force | Out-Null
}
Write-Success "Folders ensured: $($folders -join ', ')"

# ── database seed ─────────────────────────────────────────────────────────────
Write-Step "Initialising database..."
$initScript = @'
from app.database.db import init_db
init_db()
'@

& $venvPython -c $initScript
if ($LASTEXITCODE -ne 0) {
    Write-Fail "Database initialisation failed."
    exit 1
}
Write-Success "Database initialised."

# ── launcher ─────────────────────────────────────────────────────────────────
$launcherPath = Join-Path $ScriptRoot "opscollector.cmd"

if (-not (Test-Path $launcherPath) -or $Force) {
    Write-Step "Creating opscollector.cmd launcher..."
    $launcherContent = @'
@echo off
REM OpsCollector-CLI launcher
REM Runs the application using the bundled virtual environment.
cd /d "%~dp0"
".venv\Scripts\python.exe" main.py %*
'@
    Set-Content -Path $launcherPath -Value $launcherContent -Encoding ASCII
    Write-Success "Launcher written to $launcherPath"
} else {
    Write-Success "Launcher already exists: $launcherPath"
}

# ── done ─────────────────────────────────────────────────────────────────────
Write-Banner "Setup Complete"
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Green
Write-Host "  - Run: .\opscollector.cmd"
Write-Host "  - Or:    $venvPython main.py --help"
Write-Host ""

Pop-Location
exit 0
