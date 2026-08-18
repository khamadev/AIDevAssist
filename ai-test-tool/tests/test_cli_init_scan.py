from ai_test_tool import cli, orchestrator


def _tm_result(generated):
    return {
        "agent": "test-maintenance",
        "stage": "init",
        "summary": f"Generated {len(generated)} test(s)",
        "passed": True,
        "details": {"generated": generated, "skipped": [], "coverage_gaps": []},
    }


def _rel_result(passed=True):
    return {
        "agent": "reliability",
        "stage": "init",
        "summary": "1/1 tests reliable",
        "passed": passed,
        "details": {"classification": "reliable", "is_compliant": True},
    }


def test_init_installs_hooks(monkeypatch, tmp_path):
    installed = []
    monkeypatch.setattr(cli, "install_hooks", lambda target: installed.append(target))
    monkeypatch.setattr(orchestrator, "bootstrap", lambda: None)
    monkeypatch.setattr(orchestrator, "dispatch", lambda *a, **k: [])

    cli._run_init(str(tmp_path), skip_scan=False)

    assert installed == [str(tmp_path)]


def test_init_skip_scan_installs_hooks_but_never_dispatches(monkeypatch, tmp_path):
    monkeypatch.setattr(cli, "install_hooks", lambda target: None)
    dispatch_calls = []
    monkeypatch.setattr(orchestrator, "dispatch", lambda *a, **k: dispatch_calls.append((a, k)))

    cli._run_init(str(tmp_path), skip_scan=True)

    assert dispatch_calls == []


def test_init_without_skip_scan_dispatches_the_init_stage(monkeypatch, tmp_path):
    monkeypatch.setattr(cli, "install_hooks", lambda target: None)
    monkeypatch.setattr(orchestrator, "bootstrap", lambda: None)
    dispatch_calls = []

    def _fake_dispatch(stage, **kwargs):
        dispatch_calls.append((stage, kwargs))
        return [_tm_result([]), _rel_result()]

    monkeypatch.setattr(orchestrator, "dispatch", _fake_dispatch)

    cli._run_init(str(tmp_path), skip_scan=False)

    assert len(dispatch_calls) == 1
    stage, kwargs = dispatch_calls[0]
    assert stage == "init"
    assert kwargs["target"] == str(tmp_path)


def test_init_prints_agent_summaries(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(cli, "install_hooks", lambda target: None)
    monkeypatch.setattr(orchestrator, "bootstrap", lambda: None)
    monkeypatch.setattr(
        orchestrator, "dispatch", lambda *a, **k: [_tm_result([]), _rel_result()]
    )

    cli._run_init(str(tmp_path), skip_scan=False)

    output = capsys.readouterr().out
    assert "[test-maintenance]" in output
    assert "[reliability]" in output


def test_init_prints_review_hint_when_tests_were_generated(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(cli, "install_hooks", lambda target: None)
    monkeypatch.setattr(orchestrator, "bootstrap", lambda: None)
    generated = [{"file": "app/a.py", "function": "a", "test_path": "tests/test_a.py"}]
    monkeypatch.setattr(
        orchestrator, "dispatch", lambda *a, **k: [_tm_result(generated), _rel_result()]
    )

    cli._run_init(str(tmp_path), skip_scan=False)

    output = capsys.readouterr().out
    assert "review" in output.lower()
    assert "git add" in output


def test_init_does_not_print_review_hint_when_nothing_generated(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(cli, "install_hooks", lambda target: None)
    monkeypatch.setattr(orchestrator, "bootstrap", lambda: None)
    monkeypatch.setattr(
        orchestrator, "dispatch", lambda *a, **k: [_tm_result([]), _rel_result()]
    )

    cli._run_init(str(tmp_path), skip_scan=False)

    output = capsys.readouterr().out
    assert "git add" not in output
