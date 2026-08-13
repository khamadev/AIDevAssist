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
