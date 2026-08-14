"""Documentation agent: logs what changed and why after each commit."""

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from ..exclusions import is_excluded
from .contracts import AgentReport

CHANGELOG_FILENAME = "CHANGELOG.md"
STATE_DIR = ".ai-test-tool"


def run(target: str, stage: str = "post-commit", **context) -> dict:
    target_path = Path(target).resolve()

    commit = _get_last_commit_info(target_path)
    diff_summary = _get_last_commit_diff(target_path)
    # pre-commit and post-commit are separate hook invocations (separate
    # processes), so we can't rely on in-memory results from one reaching
    # the other — read the pre-commit stage's saved state instead.
    reasoning = _extract_reasoning(target_path)

    entry = _format_entry(commit, diff_summary, reasoning)
    _append_to_changelog(target_path, entry)

    report = AgentReport(
        agent="documentation",
        stage=stage,
        summary=f"Logged commit {commit['hash'][:7]} to {CHANGELOG_FILENAME}",
    )
    return report.to_dict()


def write_baseline(target: str) -> dict:
    """Log an initial snapshot before any agent has touched the repo.

    Intended to be run once, manually, at the start of the project — not
    part of the normal hook-driven dispatch.
    """
    target_path = Path(target).resolve()
    function_count, test_count = _count_functions_and_tests(target_path)

    entry = (
        f"## {_now()} — Baseline\n"
        f"- Functions found: {function_count}\n"
        f"- Existing tests: {test_count}\n"
        f"- AI-modified files so far: 0\n"
    )
    _append_to_changelog(target_path, entry)

    return AgentReport(
        agent="documentation",
        stage="post-commit",
        summary=f"Wrote baseline: {function_count} functions, {test_count} tests",
    ).to_dict()


def _get_last_commit_info(target_path: Path) -> dict:
    result = subprocess.run(
        ["git", "log", "-1", "--pretty=format:%H%n%an%n%ad%n%s"],
        cwd=target_path,
        capture_output=True,
        text=True,
        check=True,
    )
    lines = result.stdout.splitlines()
    return {
        "hash": lines[0] if len(lines) > 0 else "unknown",
        "author": lines[1] if len(lines) > 1 else "unknown",
        "date": lines[2] if len(lines) > 2 else _now(),
        "subject": lines[3] if len(lines) > 3 else "(no subject)",
    }


def _get_last_commit_diff(target_path: Path) -> str:
    has_parent = subprocess.run(
        ["git", "rev-parse", "HEAD~1"],
        cwd=target_path,
        capture_output=True,
        text=True,
    ).returncode == 0

    if has_parent:
        result = subprocess.run(
            ["git", "diff", "HEAD~1", "HEAD", "--stat"],
            cwd=target_path,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip()

    # First commit in the repo — nothing to diff against, list files instead.
    result = subprocess.run(
        ["git", "show", "--stat", "--pretty=format:", "HEAD"],
        cwd=target_path,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _extract_reasoning(target_path: Path) -> str | None:
    """Pull a human-readable reason out of the pre-commit stage's saved state.

    The pre-commit hook writes its dispatch results to
    `.ai-test-tool/last_run_pre-commit.json` (see cli.py) before the commit
    completes; post-commit (a separate process) reads it back here.
    """
    state_file = target_path / STATE_DIR / "last_run_pre-commit.json"
    if not state_file.exists():
        return None

    try:
        results = json.loads(state_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None

    notes = [
        r["details"]["notes"]
        for r in results
        if isinstance(r, dict) and r.get("details", {}).get("notes")
    ]
    return "; ".join(notes) if notes else None


def _format_entry(commit: dict, diff_summary: str, reasoning: str | None) -> str:
    lines = [
        f"## {commit['date']} — {commit['subject']}",
        f"- Commit: `{commit['hash'][:7]}`",
        f"- Author: {commit['author']}",
    ]
    if reasoning:
        lines.append(f"- Why: {reasoning}")
    lines.append("- Changes:")
    lines.append("```")
    lines.append(diff_summary or "(no diff available)")
    lines.append("```")
    return "\n".join(lines) + "\n"


def _append_to_changelog(target_path: Path, entry: str) -> None:
    changelog_path = target_path / CHANGELOG_FILENAME
    existing = (
        changelog_path.read_text(encoding="utf-8")
        if changelog_path.exists()
        else "# Changelog\n\n"
    )
    changelog_path.write_text(existing + entry + "\n", encoding="utf-8")


def _count_functions_and_tests(target_path: Path) -> tuple[int, int]:
    import ast

    function_count = 0
    for py_file in target_path.rglob("*.py"):
        if is_excluded(py_file) or py_file.name.startswith("test_"):
            continue
        try:
            tree = ast.parse(py_file.read_text(encoding="utf-8"))
        except (SyntaxError, UnicodeDecodeError):
            continue
        function_count += sum(
            1 for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)
        )

    test_count = 0
    for py_file in target_path.rglob("test_*.py"):
        if is_excluded(py_file):
            continue
        try:
            tree = ast.parse(py_file.read_text(encoding="utf-8"))
        except (SyntaxError, UnicodeDecodeError):
            continue
        test_count += sum(
            1
            for node in ast.walk(tree)
            if isinstance(node, ast.FunctionDef) and node.name.startswith("test_")
        )

    return function_count, test_count


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
