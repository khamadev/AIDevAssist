import subprocess
from pathlib import Path

from ai_test_tool.cli import _stage_generated_files


def _init_repo(tmp_path: Path) -> Path:
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_path, check=True)
    return tmp_path


def _staged_files(repo: Path) -> set[str]:
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    )
    return set(result.stdout.splitlines())


def test_stages_a_single_generated_test_path(tmp_path: Path):
    repo = _init_repo(tmp_path)
    (repo / "test_new.py").write_text("def test_new():\n    assert True\n", encoding="utf-8")

    results = [
        {
            "agent": "test-maintenance",
            "details": {"generated_test_path": "test_new.py"},
        }
    ]
    _stage_generated_files(str(repo), results)

    assert "test_new.py" in _staged_files(repo)


def test_stages_multiple_generated_test_paths(tmp_path: Path):
    repo = _init_repo(tmp_path)
    (repo / "test_a.py").write_text("def test_a():\n    assert True\n", encoding="utf-8")
    (repo / "test_b.py").write_text("def test_b():\n    assert True\n", encoding="utf-8")

    results = [
        {
            "agent": "test-maintenance",
            "details": {"generated_test_paths": ["test_a.py", "test_b.py"]},
        }
    ]
    _stage_generated_files(str(repo), results)

    staged = _staged_files(repo)
    assert "test_a.py" in staged
    assert "test_b.py" in staged


def test_does_nothing_when_no_generated_paths_present(tmp_path: Path):
    repo = _init_repo(tmp_path)

    results = [{"agent": "reliability", "details": {}}]
    # Should not raise even with nothing to stage.
    _stage_generated_files(str(repo), results)

    assert _staged_files(repo) == set()
