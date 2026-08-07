from specforge_gate import document


def test_heading_regex_uses_linear_security_shape() -> None:
    assert document._HEADING_RE.pattern == r"^(#{1,6})\s(.+)$"


def test_heading_parser_preserves_whitespace_semantics() -> None:
    parsed = document.Document.parse(
        "#  Goal  \n"
        "Body.\n"
        "##\tExpected result\t\n"
        "Value.\n"
        "#  \n"
    )

    assert [(section.title, section.line, section.body) for section in parsed.sections] == [
        ("Goal", 1, "Body."),
        ("Expected result", 3, "Value."),
        ("", 5, ""),
    ]


def test_heading_parser_handles_large_uncontrolled_whitespace_run() -> None:
    parsed = document.Document.parse("#" + (" " * 100_000) + "Goal   \nBody.\n")

    assert len(parsed.sections) == 1
    assert parsed.sections[0].title == "Goal"
    assert parsed.sections[0].body == "Body."
