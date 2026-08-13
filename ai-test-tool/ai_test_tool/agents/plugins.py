"""Extension point for teammates' agents (test-maintenance, reliability).

These agents live in different AI tools (Copilot, ChatGPT) and are not part
of this initial scaffold. To plug one in:

1. Add a module here, e.g. `ai_test_tool/agents/test_maintenance.py`, that
   exposes `run(target: str, stage: str, **context) -> dict` matching the
   contract in `contracts.py`.
2. Register it below, against the stage(s) it should run for.

Nothing else in the orchestrator needs to change — this is the one file
that couples the orchestrator to teammate-provided code, and it fails
gracefully (does nothing) if a module hasn't been added yet.
"""

from .. import orchestrator


def load() -> None:
    _load_test_maintenance()
    _load_reliability()


def _load_test_maintenance() -> None:
    try:
        from . import test_maintenance
    except ImportError:
        return
    orchestrator.register("pre-commit", test_maintenance.run)


def _load_reliability() -> None:
    try:
        from . import reliability
    except ImportError:
        return
    # Reliability judges test-maintenance's output, so it must be registered
    # after it for pre-commit — dict/list ordering in orchestrator.py
    # preserves registration order, so this function running after
    # _load_test_maintenance() is what guarantees that.
    orchestrator.register("pre-commit", reliability.run)
    orchestrator.register("pre-push", reliability.run)
