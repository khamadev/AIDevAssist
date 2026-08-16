"""Notification/UX agent: reports pass/fail on every save, immediately."""

import os
import re
import subprocess
import sys
from pathlib import Path

from .contracts import AgentReport


def run(target: str, stage: str = "on-save", changed_file: str | None = None, **context) -> dict:
    target_path = Path(target).resolve()

    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "--no-header"],
        cwd=target_path,
        capture_output=True,
        text=True,
        # Without a real terminal, pytest defaults to an 80-column width
        # and truncates one-line failure reasons (e.g. to "asse...") —
        # forcing a wide COLUMNS keeps the "why" actually readable.
        env={**os.environ, "COLUMNS": "200"},
    )

    # Exit code 5 = "no tests collected" — a neutral state, not a failure.
    passed = result.returncode in (0, 5)
    output = result.stdout + result.stderr
    failed_tests = _extract_failed_tests(output)

    if passed:
        _report_pass(changed_file, output)
    else:
        _report_fail(changed_file, output, failed_tests)

    summary = "Tests passing" if passed else "Tests are FAILING after this change"
    return AgentReport(
        agent="notification",
        stage=stage,
        summary=summary,
        passed=passed,
        details={"changed_file": changed_file, "failed_tests": failed_tests},
    ).to_dict()


def _report_pass(changed_file: str | None, output: str) -> None:
    # ASCII "-" only, not an em dash — same Windows cp1252 console
    # encoding issue as the emoji markers this replaced.
    label = f" - {changed_file}" if changed_file else ""
    count = _extract_passed_count(output)
    print(f"[PASS]{label} ({count})")


def _report_fail(changed_file: str | None, output: str, failed_tests: list[tuple[str, str]]) -> None:
    # Plain ASCII only — emoji can raise UnicodeEncodeError on a Windows
    # console using a non-UTF-8 codepage (cp1252 is still a common
    # default), which would silently kill this print mid-call with no
    # visible error, since it runs inside the watchdog observer's thread.
    print("\n" + "=" * 60)
    label = f" to {changed_file}" if changed_file else ""
    print(f"[FAIL] Change{label} broke existing tests!")
    if failed_tests:
        for test_id, reason in failed_tests:
            print(f"  - {test_id}: {reason}" if reason else f"  - {test_id}")
    else:
        # No parseable "FAILED ..." lines — likely a collection error
        # (syntax error, import error) rather than a normal assertion
        # failure. Fall back to raw output so nothing is hidden.
        print(output[-1500:])
    print("=" * 60 + "\n")


def _extract_failed_tests(output: str) -> list[tuple[str, str]]:
    """Parse pytest's "short test summary info" lines, e.g.

        FAILED tests/test_x.py::test_y - AssertionError: assert 1 == 2

    into (test_id, reason) pairs.
    """
    failed = []
    for line in output.splitlines():
        if not line.startswith("FAILED "):
            continue
        rest = line[len("FAILED "):]
        if " - " in rest:
            test_id, reason = rest.split(" - ", 1)
        else:
            test_id, reason = rest, ""
        failed.append((test_id.strip(), reason.strip()))
    return failed


def _extract_passed_count(output: str) -> str:
    match = re.search(r"(\d+ passed[^\n]*)", output)
    return match.group(1) if match else "no tests collected"
