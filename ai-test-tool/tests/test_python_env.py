import sys
from pathlib import Path

from ai_test_tool.python_env import resolve_python


def test_resolve_python_prefers_target_venv_windows_layout(tmp_path: Path):
    venv_python = tmp_path / ".venv" / "Scripts" / "python.exe"
    venv_python.parent.mkdir(parents=True)
    venv_python.write_text("", encoding="utf-8")

    assert resolve_python(tmp_path) == str(venv_python)


def test_resolve_python_prefers_target_venv_unix_layout(tmp_path: Path):
    venv_python = tmp_path / ".venv" / "bin" / "python"
    venv_python.parent.mkdir(parents=True)
    venv_python.write_text("", encoding="utf-8")

    assert resolve_python(tmp_path) == str(venv_python)


def test_resolve_python_falls_back_to_own_interpreter_when_target_has_no_venv(tmp_path: Path):
    assert resolve_python(tmp_path) == sys.executable


def test_resolve_python_prefers_windows_layout_when_both_present(tmp_path: Path):
    windows_python = tmp_path / ".venv" / "Scripts" / "python.exe"
    windows_python.parent.mkdir(parents=True)
    windows_python.write_text("", encoding="utf-8")

    unix_python = tmp_path / ".venv" / "bin" / "python"
    unix_python.parent.mkdir(parents=True)
    unix_python.write_text("", encoding="utf-8")

    assert resolve_python(tmp_path) == str(windows_python)
