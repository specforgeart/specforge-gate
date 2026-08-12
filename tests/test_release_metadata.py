from __future__ import annotations

import tomllib
from pathlib import Path

from specforge_gate import __version__

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_VERSION = "0.3.1"


def _project() -> dict[str, object]:
    with (ROOT / "pyproject.toml").open("rb") as handle:
        return tomllib.load(handle)


def test_release_version_and_packaging_metadata_are_consistent() -> None:
    data = _project()
    project = data["project"]
    build_system = data["build-system"]

    assert project["version"] == EXPECTED_VERSION
    assert __version__ == EXPECTED_VERSION
    assert project["license"] == "MIT"
    assert project["license-files"] == ["LICENSE"]

    classifiers = project["classifiers"]
    assert "Development Status :: 3 - Alpha" in classifiers
    assert "Programming Language :: Python :: 3.13" in classifiers
    assert not any(item.startswith("License ::") for item in classifiers)

    build_requires = build_system["requires"]
    assert "setuptools>=77.0.3" in build_requires


def test_changelog_records_current_release_and_keeps_unreleased_section() -> None:
    text = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")

    unreleased = text.index("## Unreleased")
    release = text.index("## 0.3.1 - 2026-08-12")

    assert unreleased < release
    assert "Windows console encodings" in text


def test_release_workflow_enforces_tag_main_checks_and_checksums() -> None:
    text = (ROOT / ".github/workflows/release.yml").read_text(encoding="utf-8")

    assert '- "v*"' in text
    assert 'expected = f"v{data[\'project\'][\'version\']}"' in text
    assert 'git merge-base --is-ancestor "$GITHUB_SHA" origin/main' in text
    assert "bash scripts/check.sh" in text
    assert "sha256sum *.whl *.tar.gz > SHA256SUMS" in text
    assert "gh release create" in text
    assert "--verify-tag" in text


def test_public_release_docs_do_not_expose_stale_pre_alpha_metadata() -> None:
    root_files = (
        ROOT / "README.md",
        ROOT / "CONTRIBUTING.md",
        ROOT / "SECURITY.md",
    )
    doc_files = tuple(sorted((ROOT / "docs").rglob("*.md")))
    combined = "\n".join(
        path.read_text(encoding="utf-8") for path in (*root_files, *doc_files)
    )

    assert "0.1.0a1" not in combined
    assert "pre-alpha implementation" not in combined
    assert "provisional until public repository creation" not in combined
    assert "AI UI controls remain a separate roadmap item" not in combined
    assert "it is not invoked by the CLI, REST API, web UI" not in combined
    assert "Product-surface AI controls remain separate future work" not in combined

    release_doc = (ROOT / "docs/release.md").read_text(encoding="utf-8")
    assert "specforge_gate-0.3.1-py3-none-any.whl" in release_doc
    assert "specforge_gate-0.3.1.tar.gz" in release_doc
    assert "SHA256SUMS" in release_doc
