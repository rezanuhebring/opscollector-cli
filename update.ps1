<#
.SYNOPSIS
Update dependencies and re-initialise database schema for OpsCollector-CLI.

.DESCRIPTION
Activates the project .venv and runs pip install --upgrade -r requirements.txt,
then re-runs init_db which is idempotent.
#>

param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Push-Location $ScriptRoot

$venvPython = Join-Path $ScriptRoot ".venv\Scripts\python.exe"

Write-Host ""
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "  OpsCollector-CLI Update" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""

if (-not (Test-Path $venvPython)) {
    Write-Host "[!] Virtual environment not found at $venvPython" -ForegroundColor Red
    Write-Host "    Run .\setup.ps1 first." -ForegroundColor Red
    exit 1
}

Write-Host "[*] Upgrading pip..." -ForegroundColor Yellow
& $venvPython -m pip install --upgrade pip | Out-Null

Write-Host "[*] Upgrading dependencies..." -ForegroundColor Yellow
if (-not (Test-Path (Join-Path $ScriptRoot "requirements.txt"))) {
    Write-Host "[!] requirements.txt not found." -ForegroundColor Red
    exit 1
}
& $venvPython -m pip install --upgrade -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Host "[!] Dependency upgrade failed." -ForegroundColor Red
    exit 1
}
Write-Host "[+] Dependencies up to date." -ForegroundColor Green

Write-Host "[*] Re-initialising database (idempotent)..." -ForegroundColor Yellow
$initScript = @'
from app.database.db import init_db
init_db()
'@
& $venvPython -c $initScript
if ($LASTEXITCODE -ne 0) {
    Write-Host "[!] Database initialisation failed." -ForegroundColor Red
    exit 1
}
Write-Host "[+] Database ready." -ForegroundColor Green

Write-Host ""
Write-Host "Update complete." -ForegroundColor Green
Write-Host "Run .\opscollector.cmd or $venvPython main.py --help" -ForegroundColor Gray

Pop-Location
exit 0
