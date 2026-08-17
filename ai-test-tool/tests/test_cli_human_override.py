import json

import pytest

from ai_test_tool import cli, orchestrator


def _failing_results():
    return [
        {
            "agent": "reliability",
            "stage": "pre-commit",
            "summary": "Not reliable",
            "passed": False,
            "details": {"notes": "Test contains no assertions"},
        }
    ]


def _patch_dispatch(monkeypatch, results):
    monkeypatch.setattr(orchestrator, "bootstrap", lambda: None)
    monkeypatch.setattr(orchestrator, "dispatch", lambda *a, **k: results)


def test_blocking_result_exits_nonzero_without_override(monkeypatch, tmp_path, capsys):
    _patch_dispatch(monkeypatch, _failing_results())
    monkeypatch.delenv("AI_TEST_TOOL_OVERRIDE", raising=False)

    with pytest.raises(SystemExit) as exc:
        cli._run_orchestrate("pre-commit", str(tmp_path), None)

    assert exc.value.code == 1
    assert "overridden" not in capsys.readouterr().out


def test_blocking_result_exits_zero_with_override(monkeypatch, tmp_path, capsys):
    _patch_dispatch(monkeypatch, _failing_results())
    monkeypatch.setenv("AI_TEST_TOOL_OVERRIDE", "1")

    with pytest.raises(SystemExit) as exc:
        cli._run_orchestrate("pre-commit", str(tmp_path), None)

    assert exc.value.code == 0
    output = capsys.readouterr().out
    assert "overridden" in output
    assert "human takes responsibility" in output


def test_override_is_recorded_in_state_for_the_changelog(monkeypatch, tmp_path):
    _patch_dispatch(monkeypatch, _failing_results())
    monkeypatch.setenv("AI_TEST_TOOL_OVERRIDE", "1")

    with pytest.raises(SystemExit):
        cli._run_orchestrate("pre-commit", str(tmp_path), None)

    state_file = tmp_path / ".ai-test-tool" / "last_run_pre-commit.json"
    payload = json.loads(state_file.read_text(encoding="utf-8"))
    assert payload["human_override"] is True


def test_override_env_var_has_no_effect_when_nothing_failed(monkeypatch, tmp_path, capsys):
    passing = [{**_failing_results()[0], "passed": True}]
    _patch_dispatch(monkeypatch, passing)
    monkeypatch.setenv("AI_TEST_TOOL_OVERRIDE", "1")

    with pytest.raises(SystemExit) as exc:
        cli._run_orchestrate("pre-commit", str(tmp_path), None)

    assert exc.value.code == 0
    assert "overridden" not in capsys.readouterr().out
