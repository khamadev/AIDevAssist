"""Resolves which Python interpreter to use for running pytest against a
target repo.

`sys.executable` (the interpreter running ai-test-tool itself) is the wrong
default here: ai-test-tool and the repo it operates on are typically two
separate virtual environments (that's exactly our own setup — `ai-test-tool/
.venv` vs `travel-planner/.venv`). Using the tool's own interpreter means
every check silently depends on the target's dependencies happening to also
be installed wherever ai-test-tool happens to be running from, which is not
a safe assumption and fails with a confusing "No module named pytest"
instead of a real test result.
"""

import sys
from pathlib import Path


def resolve_python(target_path: Path) -> str:
    """Prefer the target repo's own `.venv`, fall back to this process's
    interpreter if the target has none.
    """
    venv_dir = target_path / ".venv"

    windows_python = venv_dir / "Scripts" / "python.exe"
    if windows_python.exists():
        return str(windows_python)

    unix_python = venv_dir / "bin" / "python"
    if unix_python.exists():
        return str(unix_python)

    return sys.executable
