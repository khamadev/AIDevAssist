"""ai-test-tool CLI: init (install hooks), orchestrate (run agents), watch (live)."""

import argparse
import json
import sys
import time
from pathlib import Path

from . import orchestrator
from .hooks.install import install_hooks

STATE_DIR = ".ai-test-tool"
STAGES = ["pre-commit", "post-commit", "pre-push", "on-save"]


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="ai-test-tool")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="Install git hooks into the target repo")
    init_parser.add_argument("target", nargs="?", default=".")

    orchestrate_parser = subparsers.add_parser(
        "orchestrate", help="Run the agents registered for a given stage"
    )
    orchestrate_parser.add_argument("--stage", required=True, choices=STAGES)
    orchestrate_parser.add_argument("--target", default=".")
    orchestrate_parser.add_argument(
        "--file", default=None, help="Changed file path (used by the on-save stage)"
    )

    watch_parser = subparsers.add_parser(
        "watch", help="Watch the target repo and notify on test breakage while coding"
    )
    watch_parser.add_argument("target", nargs="?", default=".")

    args = parser.parse_args(argv)

    if args.command == "init":
        install_hooks(args.target)
    elif args.command == "orchestrate":
        _run_orchestrate(args.stage, args.target, args.file)
    elif args.command == "watch":
        _run_watch(args.target)


def _run_orchestrate(stage: str, target: str, changed_file: str | None) -> None:
    orchestrator.bootstrap()
    results = orchestrator.dispatch(stage, target=target, changed_file=changed_file)

    for result in results:
        print(f"[{result['agent']}] {result['summary']}")

    _save_state(target, stage, results)

    failed = any(r.get("passed") is False for r in results)
    sys.exit(1 if failed else 0)


def _save_state(target: str, stage: str, results: list[dict]) -> None:
    """Persist a stage's results so a later, separate process can read them.

    Needed because pre-commit and post-commit are different hook
    invocations (different processes) — see documentation.py.
    """
    state_dir = Path(target).resolve() / STATE_DIR
    state_dir.mkdir(exist_ok=True)
    state_file = state_dir / f"last_run_{stage}.json"
    state_file.write_text(json.dumps(results, indent=2), encoding="utf-8")


def _run_watch(target: str) -> None:
    try:
        from watchdog.events import FileSystemEventHandler
        from watchdog.observers import Observer
    except ImportError:
        raise SystemExit(
            "The 'watch' command requires the 'watchdog' package. "
            "Install it with: pip install watchdog"
        )

    orchestrator.bootstrap()
    target_path = str(Path(target).resolve())

    class Handler(FileSystemEventHandler):
        def on_modified(self, event):
            if event.is_directory or not event.src_path.endswith(".py"):
                return
            orchestrator.dispatch(
                "on-save", target=target_path, changed_file=event.src_path
            )

    observer = Observer()
    observer.schedule(Handler(), target_path, recursive=True)
    observer.start()
    print(f"Watching {target_path} for changes... (Ctrl+C to stop)")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


if __name__ == "__main__":
    main()
