[CmdletBinding()]
param([switch]$SkipHooks)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

function Invoke-Step {
    param([string]$Label, [scriptblock]$Command)
    Write-Host "-> $Label" -ForegroundColor Cyan
    & $Command
    if ($LASTEXITCODE -ne 0) {
        throw "$Label failed with exit code $LASTEXITCODE."
    }
}

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    throw "The 'python' command was not found in PATH."
}

Invoke-Step "Check Python >= 3.11" {
    python -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)"
}

if (-not (Test-Path ".venv\Scripts\python.exe")) {
    Invoke-Step "Create .venv" { python -m venv .venv }
}

$Python = (Resolve-Path ".venv\Scripts\python.exe").Path
Invoke-Step "Upgrade pip" { & $Python -m pip install --upgrade pip }
Invoke-Step "Install project and development dependencies" { & $Python -m pip install -e ".[dev]" }

if (-not $SkipHooks) {
    Invoke-Step "Install pre-commit hook" { & $Python -m pre_commit install }
}

Write-Host "Environment ready: $Root\.venv" -ForegroundColor Green
