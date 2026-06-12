$ErrorActionPreference = "Stop"

Set-Location (Split-Path -Parent $PSScriptRoot)

if (-not (Test-Path ".\config.json")) {
    Copy-Item ".\config.example.json" ".\config.json"
    Write-Host "Created config.json from config.example.json"
}

if (-not (Test-Path ".\profile.json")) {
    Copy-Item ".\profile.example.json" ".\profile.json"
    Write-Host "Created profile.json from profile.example.json"
}

$pythonCommand = $null

if (Get-Command py -ErrorAction SilentlyContinue) {
    $pythonCommand = "py"
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    $pythonCommand = "python"
} else {
    throw "Python was not found. Install Python 3.11+ or make sure the Python launcher 'py' is available."
}

& $pythonCommand -m venv .venv

$venvPython = ".\.venv\Scripts\python.exe"

if (-not (Test-Path $venvPython)) {
    throw "The virtual environment was not created successfully. Try running: py -m venv .venv"
}

& $venvPython -m pip install --upgrade pip
& $venvPython -m pip install -r requirements.txt

Write-Host ""
Write-Host "Setup complete."
Write-Host "Next: add your Gmail OAuth file to secrets\credentials.json, then edit config.json."
