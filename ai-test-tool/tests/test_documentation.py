import json
from pathlib import Path

from ai_test_tool.agents import documentation


def test_run_creates_changelog_with_commit_info(git_repo: Path):
    result = documentation.run(target=str(git_repo), stage="post-commit")

    changelog = git_repo / "CHANGELOG.md"
    assert changelog.exists()

    content = changelog.read_text(encoding="utf-8")
    assert "Initial commit" in content
    assert "sample.py" in content
    assert result["agent"] == "documentation"


def test_run_appends_rather_than_overwrites(git_repo: Path):
    documentation.run(target=str(git_repo), stage="post-commit")
    first_content = (git_repo / "CHANGELOG.md").read_text(encoding="utf-8")

    (git_repo / "second.py").write_text("def sub(a, b):\n    return a - b\n", encoding="utf-8")
    import subprocess

    subprocess.run(["git", "add", "."], cwd=git_repo, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "Add second"], cwd=git_repo, check=True)

    documentation.run(target=str(git_repo), stage="post-commit")
    second_content = (git_repo / "CHANGELOG.md").read_text(encoding="utf-8")

    assert second_content.startswith(first_content)
    assert "Add second" in second_content


def test_run_includes_reasoning_from_saved_pre_commit_state(git_repo: Path):
    state_dir = git_repo / ".ai-test-tool"
    state_dir.mkdir()
    state_file = state_dir / "last_run_pre-commit.json"
    state_file.write_text(
        json.dumps(
            [
                {
                    "agent": "test-maintenance",
                    "stage": "pre-commit",
                    "summary": "generated 1 test",
                    "details": {"notes": "function signature changed"},
                }
            ]
        ),
        encoding="utf-8",
    )

    documentation.run(target=str(git_repo), stage="post-commit")
    content = (git_repo / "CHANGELOG.md").read_text(encoding="utf-8")

    assert "function signature changed" in content


def test_write_baseline_counts_functions_and_tests(git_repo: Path):
    (git_repo / "tests").mkdir()
    (git_repo / "tests" / "test_sample.py").write_text(
        "def test_add():\n    assert True\n", encoding="utf-8"
    )

    result = documentation.write_baseline(target=str(git_repo))

    content = (git_repo / "CHANGELOG.md").read_text(encoding="utf-8")
    assert "Baseline" in content
    assert "Functions found: 1" in content
    assert "Existing tests: 1" in content
    assert "1 functions" in result["summary"]
