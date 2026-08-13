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
    """
    results: list[dict] = []
    for fn in AGENT_REGISTRY.get(stage, []):
        result = fn(target=target, stage=stage, upstream_results=results, **context)
        results.append(result)
    return results


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
