"""Directory names to skip when scanning or watching a target repo.

Shared by documentation.py, reliability.py, and cli.py's watch command so
this list only needs to be maintained in one place. Previously each of
these kept its own copy and they'd quietly drifted out of sync.
"""

from pathlib import Path

EXCLUDED_DIR_NAMES = {
    ".venv",
    "venv",
    "__pycache__",
    "site-packages",
    ".git",
    "ai-test-tool",
    "node_modules",
}


def is_excluded(path: Path) -> bool:
    return any(part in EXCLUDED_DIR_NAMES for part in path.parts)
