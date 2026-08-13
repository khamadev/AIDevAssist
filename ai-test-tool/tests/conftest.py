import subprocess
from pathlib import Path

import pytest

from ai_test_tool import orchestrator


@pytest.fixture(autouse=True)
def reset_orchestrator():
    """Ensure each test starts with a clean, un-bootstrapped registry."""
    orchestrator.reset()
    yield
    orchestrator.reset()


@pytest.fixture
def git_repo(tmp_path: Path) -> Path:
    """A throwaway git repo with one commit, for agents that shell out to git."""
    repo = tmp_path / "repo"
    repo.mkdir()

    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True)

    (repo / "sample.py").write_text("def add(a, b):\n    return a + b\n", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "Initial commit"], cwd=repo, check=True)

    return repo
