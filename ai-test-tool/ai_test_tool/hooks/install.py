"""Copies hook templates into a target repo's .git/hooks/."""

import shutil
import stat
import sys
from pathlib import Path

HOOK_NAMES = ["pre-commit", "post-commit", "pre-push", "post-merge"]

# Every template contains this line — used to detect "this is one of ours"
# vs. a hook a developer already had, so re-running init is safe to repeat
# but never silently clobbers someone else's existing hook.
_OWNERSHIP_MARKER = "Installed by ai-test-tool"

# Templates don't hardcode a path to ai-test-tool or assume a bare `python`
# on PATH has it installed — both break the moment this tool is moved
# somewhere other than a fixed relative location. Instead, each template
# has this placeholder, substituted at install time with the absolute path
# to the interpreter `init` was actually run with (i.e. the one that has
# `ai_test_tool` and its dependencies installed) — see
# hooks/pre-commit.template for the full reasoning.
_PYTHON_PLACEHOLDER = "{{PYTHON_EXE}}"


def install_hooks(target: str) -> None:
    target_path = Path(target).resolve()
    git_hooks_dir = target_path / ".git" / "hooks"

    if not git_hooks_dir.exists():
        raise SystemExit(
            f"No .git/hooks directory found at {git_hooks_dir} — "
            f"is {target_path} a git repository?"
        )

    templates_dir = Path(__file__).parent
    python_exe = sys.executable

    for name in HOOK_NAMES:
        src = templates_dir / f"{name}.template"
        dest = git_hooks_dir / name
        _back_up_foreign_hook(dest)
        template_text = src.read_text(encoding="utf-8")
        dest.write_text(
            template_text.replace(_PYTHON_PLACEHOLDER, python_exe),
            encoding="utf-8",
            newline="\n",  # hooks run through Git Bash even on Windows — keep LF
        )
        dest.chmod(dest.stat().st_mode | stat.S_IEXEC)
        print(f"Installed {name} hook -> {dest}")

    print(
        f"\nDone. Hooks now call ai-test-tool automatically on commit/push/merge, "
        f"using {python_exe}."
    )


def _back_up_foreign_hook(dest: Path) -> None:
    """Back up an existing hook that isn't already one of ours.

    Re-running `init` should be safe and idempotent (just re-installs our
    own hooks), but a developer's own pre-existing hook must never be
    silently destroyed.
    """
    if not dest.exists():
        return

    try:
        existing_content = dest.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        existing_content = ""

    if _OWNERSHIP_MARKER in existing_content:
        return

    backup_path = dest.with_name(dest.name + ".bak")
    shutil.copy(dest, backup_path)
    print(f"Existing {dest.name} hook was not ours — backed up to {backup_path}")
