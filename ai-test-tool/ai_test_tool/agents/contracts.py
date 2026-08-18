"""Shared input/output contract for every agent in ai-test-tool.

Every agent — whether built-in (documentation, notification) or provided by
a teammate via a different AI tool (test-maintenance, reliability) — must
expose a callable matching this signature:

    def run(target: str, stage: str, **context) -> dict:
        ...

`target` is the filesystem path to the repo being acted on (never assume a
specific repo). `stage` is one of the Stage values below. `context` carries
whatever the orchestrator passes through (e.g. `changed_file` for on-save).

The returned dict should follow the AgentReport shape: enough for the
orchestrator to print a one-line summary and for other agents (notably
documentation) to record *why* something happened, not just that it did.
"""

from dataclasses import dataclass, field
from typing import Any, Literal

Stage = Literal["pre-commit", "post-commit", "pre-push", "on-save"]


@dataclass
class AgentReport:
    agent: str
    stage: Stage
    summary: str
    passed: bool | None = None
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent": self.agent,
            "stage": self.stage,
            "summary": self.summary,
            "passed": self.passed,
            "details": self.details,
        }


@dataclass
class TestMaintenanceResult:
    """Expected shape of the `details` field from the test-maintenance agent.

    `generated` is one entry per function a test was actually written for:
    `{"file": ..., "function": ..., "test_path": ...}`. `skipped` is one
    entry per untested function that was found but not generated for
    (e.g. the AI model was unavailable, or the per-run cap was hit):
    `{"function": "path/to/file.py::function_name", "reason": ...}`.
    `coverage_gaps` lists every untested function found in this dispatch's
    changed files, generated or not — `"path/to/file.py::function_name"`
    for each.

    The agent also mirrors `generated`'s test paths into
    `generated_test_paths` (plain list of strings) at the top level of
    `details`, since that's the field reliability.py and cli.py's
    `_stage_generated_files` already know how to read.
    """

    # Tells pytest not to try collecting this as a test class — its name
    # happens to match pytest's default `Test*` discovery pattern, which
    # otherwise produces a harmless but noisy collection warning.
    __test__ = False

    generated: list[dict[str, str]] = field(default_factory=list)
    skipped: list[dict[str, str]] = field(default_factory=list)
    coverage_gaps: list[str] = field(default_factory=list)


@dataclass
class ReliabilityResult:
    """Expected shape of the `details` field from the reliability agent.

    When more than one test file is verified in a single run, the top-level
    fields here are an aggregate (worst classification wins; is_compliant
    is true only if every file is compliant) and `files` holds the full
    per-file breakdown — see reliability.py's `_aggregate`.
    """

    test_path: str
    executed: bool
    is_meaningful: bool
    classification: Literal["reliable", "needs_improvement", "not_reliable"]
    # EU AI Act, Article 50 — was this AI-generated test disclosed as such?
    is_compliant: bool
    # True if the test references code that doesn't exist (hallucinated
    # functions/attributes), as opposed to a legitimate assertion failure.
    is_hallucinated: bool = False
    notes: str = ""
    files: list[dict[str, Any]] = field(default_factory=list)
