"""Notification/UX agent: flags immediately when a save breaks a test."""

import subprocess
import sys
from pathlib import Path

from .contracts import AgentReport

# Tracks the last known pass/fail state per target repo, so we only notify
# on a state *change* rather than on every single save while still broken.
_last_state: dict[str, bool] = {}


def run(target: str, stage: str = "on-save", changed_file: str | None = None, **context) -> dict:
    target_path = Path(target).resolve()

    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "--no-header"],
        cwd=target_path,
        capture_output=True,
        text=True,
    )

    # Exit code 5 = "no tests collected" — a neutral state, not a failure.
    passed = result.returncode in (0, 5)

    key = str(target_path)
    previous = _last_state.get(key)
    state_changed = previous is None or previous != passed
    _last_state[key] = passed

    if not passed and state_changed:
        _notify_break(changed_file, result.stdout)
    elif passed and previous is False:
        _notify_fixed(changed_file)

    summary = "Tests passing" if passed else "Tests are FAILING after this change"
    return AgentReport(
        agent="notification",
        stage=stage,
        summary=summary,
        passed=passed,
        details={"changed_file": changed_file},
    ).to_dict()


def _notify_break(changed_file: str | None, output: str) -> None:
    print("\n" + "=" * 60)
    label = f" to {changed_file}" if changed_file else ""
    print(f"⚠  Change{label} broke existing tests!")
    print(output[-1500:])
    print("=" * 60 + "\n")


def _notify_fixed(changed_file: str | None) -> None:
    label = f" ({changed_file})" if changed_file else ""
    print(f"✅ Tests are passing again{label}.\n")
