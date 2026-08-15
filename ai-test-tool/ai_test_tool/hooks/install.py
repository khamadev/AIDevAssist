"""Copies hook templates into a target repo's .git/hooks/."""

import shutil
import stat
from pathlib import Path

HOOK_NAMES = ["pre-commit", "post-commit", "pre-push", "post-merge"]

# Every template contains this line — used to detect "this is one of ours"
# vs. a hook a developer already had, so re-running init is safe to repeat
# but never silently clobbers someone else's existing hook.
_OWNERSHIP_MARKER = "Installed by ai-test-tool"


def install_hooks(target: str) -> None:
    target_path = Path(target).resolve()
    git_hooks_dir = target_path / ".git" / "hooks"

    if not git_hooks_dir.exists():
        raise SystemExit(
            f"No .git/hooks directory found at {git_hooks_dir} — "
            f"is {target_path} a git repository?"
        )

    templates_dir = Path(__file__).parent

    for name in HOOK_NAMES:
        src = templates_dir / f"{name}.template"
        dest = git_hooks_dir / name
        _back_up_foreign_hook(dest)
        shutil.copy(src, dest)
        dest.chmod(dest.stat().st_mode | stat.S_IEXEC)
        print(f"Installed {name} hook -> {dest}")

    print("\nDone. Hooks now call ai-test-tool automatically on commit/push/merge.")


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
