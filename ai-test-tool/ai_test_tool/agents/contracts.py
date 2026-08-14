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
    """Expected shape of the `details` field from the test-maintenance agent."""

    file: str
    function: str
    generated_test_path: str | None
    status: Literal["generated", "updated", "skipped", "no_change_needed"]


@dataclass
class ReliabilityResult:
    """Expected shape of the `details` field from the reliability agent."""

    test_path: str
    executed: bool
    is_meaningful: bool
    classification: Literal["reliable", "needs_improvement", "not_reliable"]
    # EU AI Act, Article 50 — was this AI-generated test disclosed as such?
    is_compliant: bool
    notes: str = ""
