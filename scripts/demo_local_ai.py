"""Cross-platform end-to-end local Ollama demo for SpecForge Gate."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any
from urllib import error, parse
from urllib import request as urlrequest

_DEFAULT_BASE_URL = "http://127.0.0.1:11434"
_DEFAULT_MODEL = "qwen3:8b"
_DEFAULT_TIMEOUT_SECONDS = 60.0
_MAX_TAGS_BYTES = 2 * 1024 * 1024


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run the deterministic gate and then an explicit advisory AI review "
            "through a local Ollama endpoint."
        )
    )
    parser.add_argument(
        "--model",
        default=_DEFAULT_MODEL,
        help=f"Ollama model name (default: {_DEFAULT_MODEL}).",
    )
    parser.add_argument(
        "--base-url",
        default=_DEFAULT_BASE_URL,
        help=f"Ollama origin (default: {_DEFAULT_BASE_URL}).",
    )
    parser.add_argument(
        "--file",
        type=Path,
        default=Path("examples/ai/local-provider-demo.md"),
        help="Specification file relative to the repository root or an absolute path.",
    )
    parser.add_argument(
        "--format",
        choices=("text", "json", "markdown"),
        default="text",
        help="AI review output format.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=_DEFAULT_TIMEOUT_SECONDS,
        help="Positive provider/preflight timeout in seconds.",
    )
    return parser


def _normalize_origin(value: str) -> str:
    normalized = value.strip().rstrip("/")
    parsed = parse.urlsplit(normalized)
    try:
        _ = parsed.port
    except ValueError as exc:
        raise ValueError("Ollama base URL contains an invalid port.") from exc

    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.netloc
        or parsed.username is not None
        or parsed.password is not None
        or parsed.path not in {"", "/"}
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError(
            "Ollama base URL must be an http(s) origin without credentials, path, "
            "query, or fragment."
        )
    return normalized


def _validate_timeout(value: float) -> float:
    if value <= 0 or value == float("inf") or value != value:
        raise ValueError("Timeout must be a positive finite number.")
    return value


def _read_json_response(http_request: urlrequest.Request, timeout: float) -> Any:
    with urlrequest.urlopen(http_request, timeout=timeout) as response:
        raw = response.read(_MAX_TAGS_BYTES + 1)
    if len(raw) > _MAX_TAGS_BYTES:
        raise ValueError("Ollama model-list response is too large.")
    try:
        return json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("Ollama model-list response is not valid JSON.") from exc


def _available_models(base_url: str, timeout: float) -> set[str]:
    http_request = urlrequest.Request(
        f"{base_url}/api/tags",
        headers={"Accept": "application/json"},
        method="GET",
    )
    try:
        payload = _read_json_response(http_request, timeout)
    except (error.URLError, TimeoutError) as exc:
        raise ValueError(f"Ollama is unavailable at {base_url}.") from exc

    if not isinstance(payload, dict) or not isinstance(payload.get("models"), list):
        raise ValueError("Ollama model-list response has an unexpected shape.")

    names: set[str] = set()
    for item in payload["models"]:
        if not isinstance(item, dict):
            continue
        for field in ("name", "model"):
            value = item.get(field)
            if isinstance(value, str) and value.strip():
                names.add(value.strip())
    return names


def _run_cli(arguments: list[str], *, env: dict[str, str], cwd: Path) -> int:
    completed = subprocess.run(
        [sys.executable, "-m", "specforge_gate.cli", *arguments],
        cwd=cwd,
        env=env,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        check=False,
    )
    if completed.stdout:
        print(completed.stdout, end="")
    if completed.stderr:
        print(completed.stderr, end="", file=sys.stderr)
    return completed.returncode


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = Path(__file__).resolve().parents[1]

    try:
        base_url = _normalize_origin(args.base_url)
        timeout = _validate_timeout(args.timeout)
    except ValueError as exc:
        print(f"demo: {exc}", file=sys.stderr)
        return 2

    model = args.model.strip()
    if not model:
        print("demo: --model must not be empty.", file=sys.stderr)
        return 2

    specification = args.file
    if not specification.is_absolute():
        specification = root / specification
    specification = specification.resolve()
    if not specification.is_file():
        print(f"demo: specification file not found: {specification}", file=sys.stderr)
        return 2

    try:
        models = _available_models(base_url, timeout)
    except ValueError as exc:
        print(f"demo: {exc}", file=sys.stderr)
        print("demo: start Ollama and retry.", file=sys.stderr)
        return 2

    if model not in models:
        print(f"demo: Ollama model is not installed: {model}", file=sys.stderr)
        print(f"demo: run `ollama pull {model}` and retry.", file=sys.stderr)
        return 2

    env = os.environ.copy()
    env["SPECFORGE_AI_PROVIDER"] = "ollama"
    env["SPECFORGE_AI_MODEL"] = model
    env["SPECFORGE_AI_BASE_URL"] = base_url
    env["SPECFORGE_AI_TIMEOUT_SECONDS"] = str(timeout)

    print("== Deterministic gate (no provider call) ==")
    deterministic_exit = _run_cli(
        ["check", str(specification), "--fail-on", "none"],
        env=env,
        cwd=root,
    )
    if deterministic_exit != 0:
        return deterministic_exit

    print()
    print("== Advisory AI review via Ollama ==")
    return _run_cli(
        [
            "ai-review",
            str(specification),
            "--format",
            args.format,
            "--fail-on",
            "none",
        ],
        env=env,
        cwd=root,
    )


if __name__ == "__main__":
    raise SystemExit(main())
