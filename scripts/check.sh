#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ ! -x .venv/bin/python ]]; then
  echo 'Missing .venv. Run: bash scripts/bootstrap.sh' >&2
  exit 2
fi

PYTHON=.venv/bin/python

"$PYTHON" -m ruff check .
"$PYTHON" -m mypy src/specforge_gate
"$PYTHON" -m pytest --cov=specforge_gate --cov-branch --cov-report=term-missing --cov-fail-under=85

rm -rf dist build .venv-smoke
"$PYTHON" -m build
"$PYTHON" -m twine check dist/*

"$PYTHON" -m venv .venv-smoke
wheel="$(find dist -maxdepth 1 -name '*.whl' -print -quit)"
if [[ -z "$wheel" ]]; then
  echo 'Built wheel not found.' >&2
  exit 2
fi

.venv-smoke/bin/python -m pip install "${wheel}[api]"
.venv-smoke/bin/specgate --help
.venv-smoke/bin/python -c "from specforge_gate.api import app; assert app.title == 'SpecForge Gate API'; assert any(route.path == '/' for route in app.routes)"
.venv-smoke/bin/python -c "from specforge_gate.ai import AIRequest, AIResponseFormat; request = AIRequest('system', 'user'); assert request.response_format is AIResponseFormat.TEXT"
.venv-smoke/bin/python -c "from specforge_gate.ai import OllamaProvider; provider = OllamaProvider(model='smoke-model'); assert provider.provider_id == 'ollama'; assert provider.model == 'smoke-model'"
.venv-smoke/bin/python -c "from specforge_gate.ai import OpenAICompatibleProvider; provider = OpenAICompatibleProvider(model='smoke-model', base_url='http://127.0.0.1:1234/v1'); assert provider.provider_id == 'openai-compatible'; assert provider.model == 'smoke-model'"
.venv-smoke/bin/python -c "from specforge_gate.ai import analyze_contradictions; assert callable(analyze_contradictions)"
.venv-smoke/bin/python -c "from specforge_gate.ai import draft_improved_specification; assert callable(draft_improved_specification)"

set +e
.venv-smoke/bin/specgate check examples/bad/export-task.md --format json >/dev/null 2>&1
status=$?
set -e

if [[ "$status" -ne 1 ]]; then
  echo "Expected exit code 1 for bad example, got $status." >&2
  exit 2
fi

echo 'All checks passed.'
