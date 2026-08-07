from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]


def _yaml(path: str) -> dict[str, Any]:
    return yaml.safe_load((ROOT / path).read_text(encoding="utf-8"))


def test_dockerfile_is_multi_stage_non_root_and_health_checked() -> None:
    text = (ROOT / "Dockerfile").read_text(encoding="utf-8")

    assert text.count("FROM python:3.12-slim-bookworm") == 2
    assert " AS builder" in text
    assert " AS runtime" in text
    assert "python -m build --wheel --outdir /dist" in text
    assert '"${wheel}[api]"' in text
    assert "USER 10001:10001" in text
    assert "EXPOSE 8000" in text
    assert "HEALTHCHECK" in text
    assert "http://127.0.0.1:8000/healthz" in text
    assert '"--no-access-log"' in text
    assert "apt-get" not in text


def test_compose_defaults_to_loopback_and_hardened_runtime() -> None:
    compose = _yaml("compose.yaml")
    assert set(compose) == {"services"}
    service = compose["services"]["specforge-gate"]

    assert service["build"] == {"context": ".", "dockerfile": "Dockerfile"}
    assert service["image"] == "specforge-gate:local"
    assert service["ports"] == ["127.0.0.1:${SPECFORGE_PORT:-8000}:8000"]
    assert service["read_only"] is True
    assert service["tmpfs"] == ["/tmp:size=16m,mode=1777"]
    assert service["cap_drop"] == ["ALL"]
    assert service["security_opt"] == ["no-new-privileges:true"]
    assert service["init"] is True
    assert "volumes" not in service
    assert "privileged" not in service


def test_dockerignore_keeps_build_context_small_and_private() -> None:
    ignored = set((ROOT / ".dockerignore").read_text(encoding="utf-8").splitlines())
    for item in {".git", ".github", ".venv", ".venv-smoke", "tests", "docs", "examples"}:
        assert item in ignored


def test_docker_dependabot_update_is_enabled() -> None:
    config = _yaml(".github/dependabot.yml")
    docker = [item for item in config["updates"] if item["package-ecosystem"] == "docker"]
    assert len(docker) == 1
    assert docker[0]["directory"] == "/"
    assert docker[0]["schedule"]["interval"] == "weekly"


def test_container_documentation_preserves_product_boundary() -> None:
    text = (ROOT / "docs/container.md").read_text(encoding="utf-8")
    assert "docker compose up --build -d --wait" in text
    assert "127.0.0.1" in text
    assert "non-root" in text
    assert "read-only root filesystem" in text
    assert "no-new-privileges" in text
    assert "does not add authentication" in text
    assert "database" in text
    assert "reverse proxy" in text
