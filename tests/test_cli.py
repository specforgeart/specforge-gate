from pathlib import Path

from specforge_gate.cli import main


def test_cli_returns_one_for_errors(tmp_path: Path, capsys: object) -> None:
    path = tmp_path / "task.md"
    path.write_text("# Task\n\nDo it fast.\n", encoding="utf-8")
    assert main(["check", str(path)]) == 1


def test_cli_json_output(tmp_path: Path, capsys: object) -> None:
    path = tmp_path / "task.md"
    path.write_text("# Task\n", encoding="utf-8")
    assert main(["check", str(path), "--format", "json", "--fail-on", "none"]) == 0


def test_cli_accepts_multiple_explicit_files(tmp_path: Path, capsys: object) -> None:
    first = tmp_path / "first.md"
    second = tmp_path / "second.md"
    first.write_text("# Task\n", encoding="utf-8")
    second.write_text("# Task\n\nDo it fast.\n", encoding="utf-8")

    assert main(["check", str(second), str(first), "--format", "json", "--fail-on", "none"]) == 0

    output = capsys.readouterr().out
    assert '"files": 2' in output
    assert str(first) in output
    assert str(second) in output


def test_cli_directory_check_applies_exclude_to_discovered_files(
    tmp_path: Path, monkeypatch: object, capsys: object
) -> None:
    config = tmp_path / ".specgate.yml"
    config.write_text('version: 1\nexclude:\n  - "docs/archive/**"\n', encoding="utf-8")
    docs = tmp_path / "docs"
    archive = docs / "archive"
    archive.mkdir(parents=True)
    checked = docs / "task.md"
    excluded = archive / "old.md"
    checked.write_text("# Task\n", encoding="utf-8")
    excluded.write_text("# Old\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    assert main(["check", str(docs), "--format", "json", "--fail-on", "none"]) == 0

    output = capsys.readouterr().out
    assert str(checked) in output
    assert str(excluded) not in output
    assert '"files": 1' in output


def test_cli_directory_check_analyzes_non_excluded_files(
    tmp_path: Path, monkeypatch: object, capsys: object
) -> None:
    config = tmp_path / ".specgate.yml"
    config.write_text('version: 1\nexclude:\n  - "docs/archive/**"\n', encoding="utf-8")
    docs = tmp_path / "docs"
    docs.mkdir()
    task = docs / "task.md"
    task.write_text("# Task\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    assert main(["check", str(docs), "--format", "json"]) == 1

    output = capsys.readouterr().out
    assert str(task) in output
    assert '"errors": 3' in output
