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
