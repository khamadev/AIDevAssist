from pathlib import Path

from ai_test_tool.cli import _schedule_watches, _should_dispatch


class FakeObserver:
    def __init__(self):
        self.scheduled: list[tuple[str, bool]] = []

    def schedule(self, handler, path, recursive=False):
        self.scheduled.append((path, recursive))


def test_schedule_watches_skips_excluded_directories(tmp_path: Path):
    (tmp_path / ".venv").mkdir()
    (tmp_path / "ai-test-tool").mkdir()
    (tmp_path / "__pycache__").mkdir()
    (tmp_path / "app").mkdir()
    (tmp_path / "tests").mkdir()

    observer = FakeObserver()
    _schedule_watches(observer, handler=object(), target_path=tmp_path)

    watched_paths = {Path(p).name for p, _recursive in observer.scheduled}
    assert ".venv" not in watched_paths
    assert "ai-test-tool" not in watched_paths
    assert "__pycache__" not in watched_paths
    assert "app" in watched_paths
    assert "tests" in watched_paths


def test_schedule_watches_watches_root_non_recursively(tmp_path: Path):
    observer = FakeObserver()
    _schedule_watches(observer, handler=object(), target_path=tmp_path)

    root_entries = [entry for entry in observer.scheduled if entry[0] == str(tmp_path)]
    assert root_entries == [(str(tmp_path), False)]


def test_should_dispatch_allows_first_event():
    last_event_time: dict[str, float] = {}
    assert _should_dispatch(last_event_time, "app/x.py", now=100.0) is True


def test_should_dispatch_blocks_rapid_repeat_events_for_same_file():
    last_event_time: dict[str, float] = {}
    assert _should_dispatch(last_event_time, "app/x.py", now=100.0) is True
    assert _should_dispatch(last_event_time, "app/x.py", now=100.3) is False


def test_should_dispatch_allows_event_after_debounce_window_passes():
    last_event_time: dict[str, float] = {}
    assert _should_dispatch(last_event_time, "app/x.py", now=100.0) is True
    assert _should_dispatch(last_event_time, "app/x.py", now=101.5) is True


def test_should_dispatch_tracks_each_file_independently():
    last_event_time: dict[str, float] = {}
    assert _should_dispatch(last_event_time, "app/x.py", now=100.0) is True
    # A different file at the same instant must not be debounced by x.py's event.
    assert _should_dispatch(last_event_time, "app/y.py", now=100.0) is True
