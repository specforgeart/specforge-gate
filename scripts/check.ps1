[CmdletBinding()]
param()

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

$PythonPath = ".venv\Scripts\python.exe"
if (-not (Test-Path $PythonPath)) {
    throw "Missing .venv. Run .\scripts\bootstrap.ps1 first."
}
$Python = (Resolve-Path $PythonPath).Path

Invoke-Step "Ruff" { & $Python -m ruff check . }
Invoke-Step "MyPy" { & $Python -m mypy src/specforge_gate }
Invoke-Step "Pytest with coverage" {
    & $Python -m pytest --cov=specforge_gate --cov-branch --cov-report=term-missing --cov-fail-under=85
}

Remove-Item dist, build -Recurse -Force -ErrorAction SilentlyContinue
Invoke-Step "Build wheel and source distribution" { & $Python -m build }

$Artifacts = @(Get-ChildItem "dist\*" -File)
if ($Artifacts.Count -eq 0) {
    throw "Build artifacts were not found."
}
Invoke-Step "Validate package metadata" { & $Python -m twine check @($Artifacts.FullName) }

Remove-Item .venv-smoke -Recurse -Force -ErrorAction SilentlyContinue
Invoke-Step "Create clean smoke-test environment" { & $Python -m venv .venv-smoke }

$SmokePython = (Resolve-Path ".venv-smoke\Scripts\python.exe").Path
$Wheel = Get-ChildItem "dist\*.whl" -File | Select-Object -First 1
if (-not $Wheel) {
    throw "Built wheel was not found."
}

$WheelWithApi = "$($Wheel.FullName)[api]"
Invoke-Step "Install built wheel with API extra" { & $SmokePython -m pip install $WheelWithApi }
$Specgate = (Resolve-Path ".venv-smoke\Scripts\specgate.exe").Path
Invoke-Step "Smoke-test CLI help" { & $Specgate --help }
Invoke-Step "Smoke-test REST API import" {
    & $SmokePython -c "from specforge_gate.api import app; assert app.title == 'SpecForge Gate API'"
}

& $Specgate check ".\examples\bad\export-task.md" --format json *> $null
$BadExampleExitCode = $LASTEXITCODE
if ($BadExampleExitCode -ne 1) {
    throw "Expected exit code 1 for the bad example, got $BadExampleExitCode."
}

Write-Host "All checks passed." -ForegroundColor Green
exit 0
