"""Extension point for agents (test-maintenance, reliability).

Both `test_maintenance.py` and `reliability.py` are implemented — see
`.claude/agents/test-maintenance.md` and `.claude/agents/reliability.md`
for their specs. `_load_test_maintenance()` and `_load_reliability()`
still fail gracefully (do nothing) if either module is ever removed or
renamed, so a partially-set-up checkout degrades rather than crashing.

To plug a new agent in:

1. Add a module here, e.g. `ai_test_tool/agents/test_maintenance.py`, that
   exposes `run(target: str, stage: str, **context) -> dict` matching the
   contract in `contracts.py`.
2. Register it below, against the stage(s) it should run for.

Nothing else in the orchestrator needs to change — this is the one file
that couples the orchestrator to teammate-provided code.
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
