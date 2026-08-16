from ai_test_tool.cli import _print_failure_reason


def test_prints_per_file_notes_when_present(capsys):
    result = {
        "agent": "reliability",
        "summary": "2/2 tests reliable",
        "passed": False,
        "details": {
            "notes": "Missing AI-generated disclosure marker (EU AI Act Art. 50)",
            "files": [
                {"test_path": "tests/test_a.py", "notes": "Missing AI-generated disclosure marker (EU AI Act Art. 50)"},
                {"test_path": "tests/test_b.py", "notes": ""},
            ],
        },
    }

    _print_failure_reason(result)

    output = capsys.readouterr().out
    assert "tests/test_a.py" in output
    assert "Missing AI-generated disclosure marker" in output
    assert "tests/test_b.py" not in output


def test_falls_back_to_top_level_notes_when_no_per_file_notes(capsys):
    result = {
        "agent": "reliability",
        "summary": "Not reliable",
        "passed": False,
        "details": {"notes": "Test contains no assertions"},
    }

    _print_failure_reason(result)

    output = capsys.readouterr().out
    assert "Test contains no assertions" in output


def test_prints_nothing_when_no_notes_available(capsys):
    result = {"agent": "reliability", "summary": "Not reliable", "passed": False, "details": {}}

    _print_failure_reason(result)

    output = capsys.readouterr().out
    assert output == ""
