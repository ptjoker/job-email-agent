$ErrorActionPreference = "Stop"

Set-Location (Split-Path -Parent $PSScriptRoot)

$python = ".\.venv\Scripts\python.exe"

if (-not (Test-Path $python)) {
    throw "The local Python environment was not found. Run .\scripts\setup.ps1 first."
}

& $python .\src\prepare_application.py @args

