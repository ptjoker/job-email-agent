$ErrorActionPreference = "Stop"

Set-Location (Split-Path -Parent $PSScriptRoot)

$python = ".\.venv\Scripts\python.exe"

if (-not (Test-Path $python)) {
    throw "The local Python environment was not found. Run .\scripts\setup.ps1 from the job-email-agent folder first."
}

& $python .\src\job_email_agent.py --dry-run @args
