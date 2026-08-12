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
    $PytestBaseTemp = Join-Path $env:TEMP ("specforge-pytest-" + [guid]::NewGuid().ToString("N"))
    try {
        & $Python -m pytest --basetemp $PytestBaseTemp --cov=specforge_gate --cov-branch --cov-report=term-missing --cov-fail-under=85
    }
    finally {
        Remove-Item $PytestBaseTemp -Recurse -Force -ErrorAction SilentlyContinue
    }
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
    & $SmokePython -c "from specforge_gate.api import app; assert app.title == 'SpecForge Gate API'; assert any(route.path == '/' for route in app.routes)"
}
Invoke-Step "Smoke-test AI provider contract import" {
    & $SmokePython -c "from specforge_gate.ai import AIRequest, AIResponseFormat; request = AIRequest('system', 'user'); assert request.response_format is AIResponseFormat.TEXT"
}
Invoke-Step "Smoke-test Ollama adapter import" {
    & $SmokePython -c "from specforge_gate.ai import OllamaProvider; provider = OllamaProvider(model='smoke-model'); assert provider.provider_id == 'ollama'; assert provider.model == 'smoke-model'"
}
Invoke-Step "Smoke-test OpenAI-compatible adapter import" {
    & $SmokePython -c "from specforge_gate.ai import OpenAICompatibleProvider; provider = OpenAICompatibleProvider(model='smoke-model', base_url='http://127.0.0.1:1234/v1'); assert provider.provider_id == 'openai-compatible'; assert provider.model == 'smoke-model'"
}
Invoke-Step "Smoke-test contradiction-analysis import" {
    & $SmokePython -c "from specforge_gate.ai import analyze_contradictions; assert callable(analyze_contradictions)"
}
Invoke-Step "Smoke-test improved-spec draft import" {
    & $SmokePython -c "from specforge_gate.ai import draft_improved_specification; assert callable(draft_improved_specification)"
}
Invoke-Step "Smoke-test AI runtime configuration" {
    & $SmokePython -c "from specforge_gate.ai.runtime import provider_from_environment; provider = provider_from_environment({'SPECFORGE_AI_PROVIDER':'ollama','SPECFORGE_AI_MODEL':'smoke-model'}); assert provider is not None; assert provider.provider_id == 'ollama'"
}
Invoke-Step "Smoke-test AI API routes" {
    & $SmokePython -c "from specforge_gate.api import app; paths = {route.path for route in app.routes}; assert '/v1/ai/status' in paths; assert '/v1/ai/review' in paths"
}

& $Specgate check ".\examples\bad\export-task.md" --format json *> $null
$BadExampleExitCode = $LASTEXITCODE
if ($BadExampleExitCode -ne 1) {
    throw "Expected exit code 1 for the bad example, got $BadExampleExitCode."
}

Write-Host "All checks passed." -ForegroundColor Green
exit 0
