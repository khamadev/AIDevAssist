"""Dispatches lifecycle-stage events to registered agents, in order."""

from collections import defaultdict
from typing import Any, Callable

AgentFn = Callable[..., dict]

AGENT_REGISTRY: dict[str, list[AgentFn]] = defaultdict(list)

_bootstrapped = False


def register(stage: str, fn: AgentFn) -> None:
    AGENT_REGISTRY[stage].append(fn)


def dispatch(stage: str, target: str, **context: Any) -> list[dict]:
    """Run every agent registered for `stage`, in registration order.

    Each agent receives `upstream_results` — the results of agents that ran
    earlier *in this same dispatch call* (same process, same stage). This
    does NOT carry across separate hook invocations — e.g. pre-commit and
    post-commit are different processes entirely, so an agent that needs
    input from a different stage must read/write it via a state file
    instead (see documentation.py's use of `.ai-test-tool/last_run_*.json`,
    written by cli.py after each dispatch).

    An agent raising an exception does NOT abort the rest of the dispatch,
    and does NOT block the git operation that triggered it — it's reported
    as a crash (`passed: None`, distinct from a real `passed: False`
    finding) so it's visible without letting one broken agent (e.g.
    still-buggy code from a teammate's tool) take down the whole team's
    commit/push workflow.
    """
    results: list[dict] = []
    for fn in AGENT_REGISTRY.get(stage, []):
        try:
            result = fn(target=target, stage=stage, upstream_results=results, **context)
        except Exception as exc:  # noqa: BLE001 - must never crash the hook chain
            result = {
                "agent": _agent_name(fn),
                "stage": stage,
                "summary": f"Agent crashed: {exc}",
                "passed": None,
                "details": {"error": repr(exc)},
            }
        results.append(result)
    return results


def _agent_name(fn: AgentFn) -> str:
    module = getattr(fn, "__module__", "unknown")
    return module.rsplit(".", 1)[-1]


def bootstrap() -> None:
    """Register built-in agents, then load teammate-provided plugins.

    Safe to call more than once — only registers agents the first time.
    """
    global _bootstrapped
    if _bootstrapped:
        return

    from .agents import documentation, notification, plugins

    register("post-commit", documentation.run)
    register("on-save", notification.run)

    plugins.load()

    _bootstrapped = True


def reset() -> None:
    """Clear the registry. Intended for tests, not normal use."""
    global _bootstrapped
    AGENT_REGISTRY.clear()
    _bootstrapped = False
