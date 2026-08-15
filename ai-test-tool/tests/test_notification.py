from pathlib import Path

from ai_test_tool.agents import notification


def _write_passing_test(repo: Path) -> None:
    (repo / "test_ok.py").write_text(
        "def test_ok():\n    assert True\n", encoding="utf-8"
    )


def _write_failing_test(repo: Path) -> None:
    (repo / "test_broken.py").write_text(
        "def test_broken():\n    assert False\n", encoding="utf-8"
    )


def test_run_reports_passed_true_when_tests_pass(tmp_path: Path):
    notification._last_state.clear()
    _write_passing_test(tmp_path)

    result = notification.run(target=str(tmp_path), stage="on-save", changed_file="test_ok.py")

    assert result["passed"] is True
    assert result["agent"] == "notification"


def test_run_reports_passed_true_when_no_tests_exist(tmp_path: Path):
    notification._last_state.clear()

    result = notification.run(target=str(tmp_path), stage="on-save", changed_file="x.py")

    assert result["passed"] is True


def test_run_reports_passed_false_when_a_test_fails(tmp_path: Path):
    notification._last_state.clear()
    _write_failing_test(tmp_path)

    result = notification.run(target=str(tmp_path), stage="on-save", changed_file="test_broken.py")

    assert result["passed"] is False


def test_run_notifies_only_on_state_change(tmp_path: Path, capsys):
    notification._last_state.clear()
    _write_failing_test(tmp_path)

    notification.run(target=str(tmp_path), stage="on-save", changed_file="test_broken.py")
    first_output = capsys.readouterr().out
    assert "broke existing tests" in first_output

    notification.run(target=str(tmp_path), stage="on-save", changed_file="test_broken.py")
    second_output = capsys.readouterr().out
    assert "broke existing tests" not in second_output
