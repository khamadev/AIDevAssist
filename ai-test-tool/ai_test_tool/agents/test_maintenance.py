"""Test maintenance agent: scans source files for untested functions and
writes tests for them using the AI model.

Two entry points, two deliberately different scopes:

- `run()` — scoped to the current change (staged files at commit time, or
  the single saved file on-save). Wired into git hooks. Grading every
  untested function in the entire codebase on every commit would make
  commits slow and expensive in proportion to repo size, not to the size
  of the actual change — so this never looks beyond what's actually being
  committed.
- `scan_repository()` — every non-excluded .py file in the target repo,
  no matter what changed. Wired into `init` (see cli.py`_run_init`) and
  intended for a one-time, human-observed pass over an existing codebase
  that hasn't had this tool running against it from the start. Never wired
  into a git hook — same cost/latency reasoning as above, just at repo
  scale instead of commit scale.

Both share the same generation core (`_build_report`); they differ only in
which files they look at and how many functions they'll generate for
before stopping.
"""

import ast
from dataclasses import asdict
from pathlib import Path

from .. import ai_client, secret_redaction
from ..exclusions import is_excluded
from .contracts import AgentReport, TestMaintenanceResult

# Caps how many functions get sent to the model in one dispatch. A single
# commit touching a large file could otherwise turn a git hook into a long,
# expensive burst of API calls — this keeps worst-case hook latency bounded
# and predictable rather than proportional to however much code changed.
MAX_FUNCTIONS_PER_RUN = 5

# A full-repository scan is expected to find more untested functions than a
# single commit ever would, and is run once at `init` time rather than on
# every commit — so a higher cap is appropriate, but still a cap: an
# unbounded scan on a large, long-unmaintained codebase could otherwise
# mean dozens of API calls and a very long-running `init`, with no visible
# progress until it finally finishes.
MAX_FUNCTIONS_PER_FULL_SCAN = 25


def run(target: str, stage: str, **context) -> dict:
    target_path = Path(target).resolve()
    source_files = _source_files_to_scan(target_path, context)
    return _build_report(target_path, source_files, MAX_FUNCTIONS_PER_RUN, stage)


def scan_repository(target: str, stage: str = "init", **context) -> dict:
    """Full-repository scan — every non-excluded .py file, not just the
    current change. See module docstring for why this is a distinct entry
    point rather than a mode of `run()`.
    """
    target_path = Path(target).resolve()
    source_files = _all_source_files(target_path)
    return _build_report(target_path, source_files, MAX_FUNCTIONS_PER_FULL_SCAN, stage)


def _build_report(
    target_path: Path, source_files: list[Path], max_functions: int, stage: str
) -> dict:
    if not source_files:
        return AgentReport(
            agent="test-maintenance",
            stage=stage,
            summary="No source files to scan",
            passed=True,
            details={"generated": [], "skipped": [], "coverage_gaps": []},
        ).to_dict()

    generated: list[dict] = []
    skipped: list[dict] = []
    coverage_gaps: list[str] = []
    ai_unavailable_reason: str | None = None

    for source_file in source_files:
        functions = _extract_public_functions(source_file)
        if not functions:
            continue

        test_file = _test_file_for(source_file, target_path)
        tested = _tested_functions(test_file, _module_dotted_path(source_file, target_path))
        untested = sorted(functions - tested)

        for function_name in untested:
            qualified = f"{source_file.relative_to(target_path)}::{function_name}"
            coverage_gaps.append(qualified)

            if len(generated) + len(skipped) >= max_functions:
                skipped.append({"function": qualified, "reason": "per-run cap reached"})
                continue

            if ai_unavailable_reason:
                skipped.append({"function": qualified, "reason": ai_unavailable_reason})
                continue

            module_path = _module_dotted_path(source_file, target_path)
            try:
                test_code, secrets_redacted = _generate_test(
                    source_file, function_name, module_path
                )
            except ai_client.AIUnavailable as exc:
                ai_unavailable_reason = str(exc)
                skipped.append({"function": qualified, "reason": ai_unavailable_reason})
                continue

            _append_test_to_file(test_file, function_name, module_path, test_code)
            generated.append(
                {
                    "file": str(source_file.relative_to(target_path)),
                    "function": function_name,
                    "test_path": str(test_file.relative_to(target_path)),
                    "secrets_redacted": secrets_redacted,
                }
            )

    result = TestMaintenanceResult(
        generated=generated,
        skipped=skipped,
        coverage_gaps=coverage_gaps,
    )

    summary = _summarize(generated, skipped, coverage_gaps)
    # Several functions can land in the same test file (e.g. two untested
    # functions in one module) — dedupe here so reliability.py doesn't
    # verify the same file twice for one dispatch.
    unique_test_paths = list(dict.fromkeys(g["test_path"] for g in generated))
    report = AgentReport(
        agent="test-maintenance",
        stage=stage,
        summary=summary,
        passed=len(skipped) == 0,
        details={
            **asdict(result),
            "generated_test_paths": unique_test_paths,
        },
    )
    return report.to_dict()


def _summarize(generated: list[dict], skipped: list[dict], coverage_gaps: list[str]) -> str:
    if not coverage_gaps:
        return "No untested functions found in changed files"
    parts = [f"Generated {len(generated)} test(s) for {len(coverage_gaps)} untested function(s)"]
    redacted_count = sum(1 for g in generated if g.get("secrets_redacted"))
    if redacted_count:
        # Visible in the same place a human override shows up (cli.py's
        # printed summary, then the changelog) — a secret being redacted is
        # exactly the kind of thing that shouldn't be discoverable only by
        # reading source code after the fact.
        parts.append(f"secrets redacted before sending to AI in {redacted_count} function(s)")
    if skipped:
        parts.append(f"{len(skipped)} skipped ({skipped[0]['reason']})")
    return "; ".join(parts)


def _source_files_to_scan(target_path: Path, context: dict) -> list[Path]:
    """Which non-test .py files changed in this dispatch.

    Prefers an explicit `changed_file` from context (the on-save stage
    passes exactly the file that was just saved); otherwise falls back to
    whatever is staged for the current commit.
    """
    changed_file = context.get("changed_file")
    if changed_file:
        candidate = Path(changed_file)
        if not candidate.is_absolute():
            candidate = target_path / candidate
        return [candidate] if _is_scannable_source(candidate) else []

    return _staged_source_files(target_path)


def _staged_source_files(target_path: Path) -> list[Path]:
    import subprocess

    try:
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
            cwd=target_path,
            capture_output=True,
            text=True,
            check=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return []

    matches = []
    for line in result.stdout.splitlines():
        candidate = target_path / line.strip()
        if _is_scannable_source(candidate):
            matches.append(candidate)
    return matches


def _all_source_files(target_path: Path) -> list[Path]:
    """Every non-excluded, non-test .py file under the target repo —
    the full-scan equivalent of `_staged_source_files`. Sorted for
    deterministic ordering: filesystem walk order isn't guaranteed
    consistent across platforms, and this drives which functions get
    generated for first when the full-scan cap is hit.
    """
    return sorted(p for p in target_path.rglob("*.py") if _is_scannable_source(p))


def _is_scannable_source(path: Path) -> bool:
    return (
        path.suffix == ".py"
        and not path.name.startswith("test_")
        and path.exists()
        and not is_excluded(path)
    )


def _extract_public_functions(source_file: Path) -> set[str]:
    """Top-level function names, excluding underscore-prefixed helpers.

    A leading underscore is this codebase's own convention for "private,
    internal helper" (see e.g. poi.py, reliability.py) — those are
    implementation details exercised indirectly through the public
    functions that call them, not things that need their own direct test.
    """
    try:
        tree = ast.parse(source_file.read_text(encoding="utf-8"))
    except (OSError, SyntaxError, UnicodeDecodeError):
        return set()

    return {
        node.name
        for node in ast.iter_child_nodes(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and not node.name.startswith("_")
    }


def _tested_functions(test_file: Path, module_dotted_path: str) -> set[str]:
    """Function names imported from this module anywhere in its test file.

    Same heuristic reliability.py's predecessor used: a test that doesn't
    import the function under a matching name isn't recognized as covering
    it, even if it happens to test equivalent behavior some other way. That
    trade-off favors occasionally regenerating a test that already exists
    (harmless — the function still gets the same, or better, coverage) over
    silently skipping a function that genuinely has none.
    """
    if not test_file.exists():
        return set()
    try:
        tree = ast.parse(test_file.read_text(encoding="utf-8"))
    except (OSError, SyntaxError, UnicodeDecodeError):
        return set()

    tested = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == module_dotted_path:
            tested.update(alias.name for alias in node.names)
    return tested


def _module_dotted_path(source_file: Path, target_path: Path) -> str:
    relative = source_file.relative_to(target_path).with_suffix("")
    return ".".join(relative.parts)


def _test_file_for(source_file: Path, target_path: Path) -> Path:
    return target_path / "tests" / f"test_{source_file.stem}.py"


def _generate_test(source_file: Path, function_name: str, module_path: str) -> tuple[str, bool]:
    """Returns (generated test code, whether a likely secret was redacted
    from the function's source before it was sent to the model).
    """
    function_source = _function_source(source_file, function_name)
    # Defense in depth: redact before this ever leaves the process, not
    # after — see secret_redaction.py. A hardcoded credential in the
    # function under test must never reach the prompt, even if it would
    # have made for a more "realistic" generated test.
    function_source, secrets_redacted = secret_redaction.redact(function_source)

    prompt = (
        "Write pytest test functions for the Python function below. "
        "Requirements:\n"
        f"- Import it as: from {module_path} import {function_name}\n"
        "- Cover the normal case, at least one edge case, and error "
        "handling if the function can raise.\n"
        "- Use plain `assert` statements, not a testing framework's "
        "custom assertion helpers.\n"
        "- Some values below may already read as [REDACTED] — that is "
        "expected, treat it as an opaque placeholder string, not a bug.\n"
        "- Return ONLY the Python test code — no markdown fences, no "
        "prose before or after.\n\n"
        f"```python\n{function_source}\n```"
    )
    raw = ai_client.generate(prompt)
    return _strip_code_fences(raw), secrets_redacted


def _function_source(source_file: Path, function_name: str) -> str:
    tree = ast.parse(source_file.read_text(encoding="utf-8"))
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == function_name:
            segment = ast.get_source_segment(source_file.read_text(encoding="utf-8"), node)
            if segment:
                return segment
    return f"def {function_name}(...): ..."  # pragma: no cover — should be unreachable


def _strip_code_fences(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith("```"):
        lines = stripped.splitlines()
        lines = lines[1:]  # drop opening ```python or ```
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        stripped = "\n".join(lines)
    return stripped


def _append_test_to_file(
    test_file: Path, function_name: str, module_path: str, test_code: str
) -> None:
    """Append AI-generated test code to `test_file`, adding the AI
    disclosure marker required by the reliability agent's EU AI Act
    Article 50 check.

    The import is inserted here rather than trusted from the model's own
    output — the prompt asks for it, but correctness of the generated file
    shouldn't depend on the model actually following that instruction. A
    duplicate import line across multiple generated blocks in the same
    file is harmless in Python, just redundant.
    """
    marker = "# AI-generated by ai-test-tool"
    import_line = f"from {module_path} import {function_name}"
    block = f"\n\n{import_line}\n{test_code}\n"

    if not test_file.exists():
        test_file.write_text(f"{marker}\nimport pytest\n{block}", encoding="utf-8")
        return

    existing = _existing_content(test_file)
    if marker not in existing:
        block = f"\n\n{marker}{block}"

    with test_file.open("a", encoding="utf-8") as f:
        f.write(block)


def _existing_content(test_file: Path) -> str:
    return test_file.read_text(encoding="utf-8") if test_file.exists() else ""
