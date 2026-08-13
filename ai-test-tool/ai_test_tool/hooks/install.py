"""Copies hook templates into a target repo's .git/hooks/."""

import shutil
import stat
from pathlib import Path

HOOK_NAMES = ["pre-commit", "post-commit", "pre-push"]


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
        shutil.copy(src, dest)
        dest.chmod(dest.stat().st_mode | stat.S_IEXEC)
        print(f"Installed {name} hook -> {dest}")

    print("\nDone. Hooks now call ai-test-tool automatically on commit/push.")
