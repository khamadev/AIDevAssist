import subprocess
from pathlib import Path

import pytest

from ai_test_tool.hooks.install import HOOK_NAMES, install_hooks


@pytest.fixture
def bare_git_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    return repo


def test_install_hooks_raises_clearly_when_not_a_git_repo(tmp_path: Path):
    not_a_repo = tmp_path / "not-a-repo"
    not_a_repo.mkdir()

    with pytest.raises(SystemExit, match="git repository"):
        install_hooks(str(not_a_repo))


def test_install_hooks_installs_all_expected_hooks(bare_git_repo: Path):
    install_hooks(str(bare_git_repo))

    for name in HOOK_NAMES:
        hook_path = bare_git_repo / ".git" / "hooks" / name
        assert hook_path.exists()
        assert "ai_test_tool.cli orchestrate" in hook_path.read_text(encoding="utf-8")


def test_install_hooks_is_idempotent(bare_git_repo: Path):
    install_hooks(str(bare_git_repo))
    install_hooks(str(bare_git_repo))

    hook_path = bare_git_repo / ".git" / "hooks" / "pre-commit"
    backup_path = hook_path.with_name(hook_path.name + ".bak")
    assert hook_path.exists()
    assert not backup_path.exists()


def test_install_hooks_backs_up_a_pre_existing_foreign_hook(bare_git_repo: Path):
    hooks_dir = bare_git_repo / ".git" / "hooks"
    foreign_hook = hooks_dir / "pre-commit"
    foreign_hook.write_text("#!/usr/bin/env bash\necho 'a developer already had this'\n", encoding="utf-8")

    install_hooks(str(bare_git_repo))

    backup_path = foreign_hook.with_name(foreign_hook.name + ".bak")
    assert backup_path.exists()
    assert "a developer already had this" in backup_path.read_text(encoding="utf-8")
    assert "ai_test_tool.cli orchestrate" in foreign_hook.read_text(encoding="utf-8")
