from pathlib import Path

from ai_test_tool.agents import notification


def _write_passing_test(repo: Path) -> None:
    (repo / "test_ok.py").write_text(
        "def test_ok():\n    assert True\n", encoding="utf-8"
    )


def _write_failing_test(repo: Path) -> None:
    (repo / "test_broken.py").write_text(
        "def test_broken():\n    assert 1 + 1 == 3\n", encoding="utf-8"
    )


def test_run_reports_passed_true_when_tests_pass(tmp_path: Path):
    _write_passing_test(tmp_path)

    result = notification.run(target=str(tmp_path), stage="on-save", changed_file="test_ok.py")

    assert result["passed"] is True
    assert result["agent"] == "notification"


def test_run_reports_passed_true_when_no_tests_exist(tmp_path: Path):
    result = notification.run(target=str(tmp_path), stage="on-save", changed_file="x.py")

    assert result["passed"] is True


def test_run_reports_passed_false_when_a_test_fails(tmp_path: Path):
    _write_failing_test(tmp_path)

    result = notification.run(target=str(tmp_path), stage="on-save", changed_file="test_broken.py")

    assert result["passed"] is False


def test_run_reports_every_save_not_just_state_changes(tmp_path: Path, capsys):
    """Every Ctrl+S should print something — not just the first failure."""
    _write_failing_test(tmp_path)

    notification.run(target=str(tmp_path), stage="on-save", changed_file="test_broken.py")
    first_output = capsys.readouterr().out
    assert "broke existing tests" in first_output

    # Same still-broken state, saved again — must still report, not go quiet.
    notification.run(target=str(tmp_path), stage="on-save", changed_file="test_broken.py")
    second_output = capsys.readouterr().out
    assert "broke existing tests" in second_output


def test_run_reports_passing_save_with_pass_marker(tmp_path: Path, capsys):
    _write_passing_test(tmp_path)

    notification.run(target=str(tmp_path), stage="on-save", changed_file="test_ok.py")

    output = capsys.readouterr().out
    assert "[PASS]" in output


def test_run_includes_failing_test_names_and_reasons_in_details(tmp_path: Path):
    _write_failing_test(tmp_path)

    result = notification.run(target=str(tmp_path), stage="on-save", changed_file="test_broken.py")

    failed_tests = result["details"]["failed_tests"]
    assert len(failed_tests) == 1
    test_id, reason = failed_tests[0]
    assert "test_broken" in test_id
    assert reason  # non-empty — should include the assertion reason


def test_run_prints_failing_test_names_and_reasons(tmp_path: Path, capsys):
    _write_failing_test(tmp_path)

    notification.run(target=str(tmp_path), stage="on-save", changed_file="test_broken.py")

    output = capsys.readouterr().out
    assert "test_broken" in output
