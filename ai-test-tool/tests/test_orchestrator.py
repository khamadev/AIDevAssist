from ai_test_tool import orchestrator


def test_register_and_dispatch_calls_registered_agent():
    calls = []

    def fake_agent(target, stage, **context):
        calls.append((target, stage))
        return {"agent": "fake", "stage": stage, "summary": "ok", "passed": True}

    orchestrator.register("post-commit", fake_agent)
    results = orchestrator.dispatch("post-commit", target="some/path")

    assert calls == [("some/path", "post-commit")]
    assert results[0]["agent"] == "fake"


def test_dispatch_runs_agents_in_registration_order():
    order = []

    def first(target, stage, **context):
        order.append("first")
        return {"agent": "first", "stage": stage, "summary": "ok"}

    def second(target, stage, **context):
        order.append("second")
        return {"agent": "second", "stage": stage, "summary": "ok"}

    orchestrator.register("pre-commit", first)
    orchestrator.register("pre-commit", second)
    orchestrator.dispatch("pre-commit", target=".")

    assert order == ["first", "second"]


def test_dispatch_passes_upstream_results_to_later_agents():
    def first(target, stage, **context):
        return {"agent": "first", "stage": stage, "summary": "ok"}

    def second(target, stage, upstream_results, **context):
        assert len(upstream_results) == 1
        assert upstream_results[0]["agent"] == "first"
        return {"agent": "second", "stage": stage, "summary": "ok"}

    orchestrator.register("pre-commit", first)
    orchestrator.register("pre-commit", second)
    orchestrator.dispatch("pre-commit", target=".")


def test_dispatch_on_stage_with_no_registered_agents_returns_empty():
    results = orchestrator.dispatch("pre-push", target=".")
    assert results == []


def test_bootstrap_registers_documentation_and_notification():
    orchestrator.bootstrap()
    assert len(orchestrator.AGENT_REGISTRY["post-commit"]) == 1
    assert len(orchestrator.AGENT_REGISTRY["on-save"]) == 1


def test_bootstrap_is_idempotent():
    orchestrator.bootstrap()
    orchestrator.bootstrap()
    assert len(orchestrator.AGENT_REGISTRY["post-commit"]) == 1


def test_bootstrap_picks_up_reliability_plugin():
    orchestrator.bootstrap()
    assert len(orchestrator.AGENT_REGISTRY["pre-commit"]) >= 1
    assert len(orchestrator.AGENT_REGISTRY["pre-push"]) >= 1


def test_bootstrap_registers_full_scan_and_reliability_for_init_in_order():
    orchestrator.bootstrap()
    registered = orchestrator.AGENT_REGISTRY["init"]
    assert len(registered) == 2
    # test-maintenance's full-repo scan must run before reliability, the
    # same ordering guarantee pre-commit relies on — reliability verifies
    # what scan_repository just generated via upstream_results.
    assert registered[0].__module__.endswith("test_maintenance")
    assert registered[1].__module__.endswith("reliability")


def test_dispatch_does_not_crash_when_an_agent_raises():
    def broken_agent(target, stage, **context):
        raise RuntimeError("boom")

    orchestrator.register("pre-commit", broken_agent)
    results = orchestrator.dispatch("pre-commit", target=".")

    assert len(results) == 1
    assert results[0]["agent"] == "test_orchestrator"
    assert "boom" in results[0]["summary"]
    # A crash is reported distinctly from a real failed finding — must not
    # be treated the same as `passed: False`, which would block commits.
    assert results[0]["passed"] is None


def test_dispatch_continues_running_later_agents_after_a_crash():
    order = []

    def broken_agent(target, stage, **context):
        order.append("broken")
        raise RuntimeError("boom")

    def later_agent(target, stage, **context):
        order.append("later")
        return {"agent": "later", "stage": stage, "summary": "ok", "passed": True}

    orchestrator.register("pre-commit", broken_agent)
    orchestrator.register("pre-commit", later_agent)
    results = orchestrator.dispatch("pre-commit", target=".")

    assert order == ["broken", "later"]
    assert len(results) == 2
    assert results[1]["agent"] == "later"


def test_crash_report_does_not_count_as_a_blocking_failure():
    """Mirrors cli.py's `failed = any(r.get('passed') is False ...)` check —
    a crash (passed: None) must not be conflated with a real failure."""

    def broken_agent(target, stage, **context):
        raise RuntimeError("boom")

    orchestrator.register("pre-commit", broken_agent)
    results = orchestrator.dispatch("pre-commit", target=".")

    failed = any(r.get("passed") is False for r in results)
    assert failed is False
