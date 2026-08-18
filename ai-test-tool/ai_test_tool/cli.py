"""ai-test-tool CLI: init (install hooks), orchestrate (run agents), watch (live)."""

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

from . import orchestrator
from .agents.test_maintenance import MAX_FUNCTIONS_PER_FULL_SCAN
from .exclusions import is_excluded
from .hooks.install import install_hooks

STATE_DIR = ".ai-test-tool"
STAGES = ["pre-commit", "post-commit", "pre-push", "on-save"]
# Many editors fire multiple filesystem events per save — ignore repeats
# for the same file within this window rather than re-running tests for
# each one.
WATCH_DEBOUNCE_SECONDS = 1.0


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="ai-test-tool")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="Install git hooks into the target repo")
    init_parser.add_argument("target", nargs="?", default=".")
    init_parser.add_argument(
        "--skip-scan",
        action="store_true",
        help=(
            "Skip the full-repository test-maintenance + reliability scan "
            "that normally runs after hooks are installed"
        ),
    )

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
        _run_init(args.target, skip_scan=args.skip_scan)
    elif args.command == "orchestrate":
        _run_orchestrate(args.stage, args.target, args.file)
    elif args.command == "watch":
        _run_watch(args.target)


def _run_init(target: str, skip_scan: bool) -> None:
    install_hooks(target)
    if skip_scan:
        return

    print(
        "\nScanning the full repository for untested functions "
        "(test-maintenance + reliability)...\n"
        "This can take a while and make several AI model calls, capped at "
        f"{MAX_FUNCTIONS_PER_FULL_SCAN} functions. Run `init --skip-scan` "
        "to install hooks without it."
    )
    orchestrator.bootstrap()
    results = orchestrator.dispatch("init", target=target)
    _print_results(results)

    generated = any(
        result.get("agent") == "test-maintenance" and result.get("details", {}).get("generated")
        for result in results
    )
    if generated:
        print(
            "\nGenerated tests were written to disk but not staged or "
            "committed — review them with `git diff`, then `git add` and "
            "commit whatever you're satisfied with."
        )


def _print_results(results: list[dict]) -> None:
    for result in results:
        print(f"[{result['agent']}] {result['summary']}")
        # A summary can read as positive ("2/2 tests reliable") while the
        # commit is still blocked for an unrelated reason (e.g. a
        # compliance check, not a reliability one) — always show *why*
        # when passed is False, don't make the developer go dig for it.
        if result.get("passed") is False:
            _print_failure_reason(result)


def _run_orchestrate(stage: str, target: str, changed_file: str | None) -> None:
    orchestrator.bootstrap()
    results = orchestrator.dispatch(stage, target=target, changed_file=changed_file)
    _print_results(results)

    if stage == "pre-commit":
        _stage_generated_files(target, results)

    _save_state(target, stage, results)

    failed = any(r.get("passed") is False for r in results)
    if failed and _human_override_requested():
        # A human must always be able to override an automated block —
        # this is a deliberate, visible escape hatch, not a silent bypass:
        # every use is printed and written to state so it shows up in the
        # documentation agent's changelog entry, not hidden from review.
        print(
            "[orchestrator] Blocking result overridden by "
            "AI_TEST_TOOL_OVERRIDE=1 — a human takes responsibility for this commit."
        )
        _save_state(target, stage, results, overridden=True)
        sys.exit(0)
    sys.exit(1 if failed else 0)


def _human_override_requested() -> bool:
    return os.environ.get("AI_TEST_TOOL_OVERRIDE") == "1"


def _print_failure_reason(result: dict) -> None:
    details = result.get("details", {})
    files = details.get("files")
    printed = False
    if files:
        for file_detail in files:
            notes = file_detail.get("notes")
            if notes:
                print(f"    - {file_detail.get('test_path', '?')}: {notes}")
                printed = True
    if not printed and details.get("notes"):
        print(f"    - {details['notes']}")


def _stage_generated_files(target: str, results: list[dict]) -> None:
    """`git add` any files an agent generated/modified during pre-commit.

    Without this, a hook that writes a file mid-run (e.g. test-maintenance
    generating a test) has no effect on the commit that triggered it — git
    snapshots whatever was staged *before* the hook ran, so the generated
    file would silently be left out of the very commit meant to include it,
    sitting as an unrelated uncommitted change afterward instead.
    """
    paths: list[str] = []
    for result in results:
        details = result.get("details", {})
        generated = details.get("generated_test_path")
        if generated:
            paths.append(generated)
        paths.extend(details.get("generated_test_paths") or [])

    if not paths:
        return

    subprocess.run(["git", "add", *paths], cwd=target, check=False)


def _save_state(
    target: str, stage: str, results: list[dict], overridden: bool = False
) -> None:
    """Persist a stage's results so a later, separate process can read them.

    Needed because pre-commit and post-commit are different hook
    invocations (different processes) — see documentation.py.

    `overridden` records that a human bypassed a blocking result via
    AI_TEST_TOOL_OVERRIDE — the documentation agent reads this same file,
    so an override always lands in the changelog's "Why" line rather than
    disappearing once the commit goes through.

    Best-effort: a filesystem problem here (permissions, disk full, read-only
    checkout) shouldn't block a commit/push over a bookkeeping write — the
    orchestrate command's own pass/fail exit code doesn't depend on this.
    """
    try:
        state_dir = Path(target).resolve() / STATE_DIR
        state_dir.mkdir(exist_ok=True)
        state_file = state_dir / f"last_run_{stage}.json"
        payload = {"results": results, "human_override": overridden}
        state_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    except OSError as exc:
        print(f"[orchestrator] Warning: could not save state ({exc})", file=sys.stderr)


def _should_dispatch(last_event_time: dict[str, float], path: str, now: float) -> bool:
    """Debounce check: True (and records `now`) only if enough time has
    passed since the last dispatch for this exact path.
    """
    last = last_event_time.get(path, 0.0)
    if now - last < WATCH_DEBOUNCE_SECONDS:
        return False
    last_event_time[path] = now
    return True


def _schedule_watches(observer, handler, target_path: Path) -> None:
    """Watch `target_path`, skipping excluded directories (`.venv/`,
    `ai-test-tool/`, etc.) entirely rather than only filtering their events
    after the fact. Those directories can contain thousands of files
    (especially `.venv/`), and placing OS-level watches on them wastes
    resources and can noticeably slow the watcher down for no benefit —
    nothing in there is ever something a developer wants live feedback on.
    """
    observer.schedule(handler, str(target_path), recursive=False)
    for child in sorted(target_path.iterdir()):
        if not child.is_dir() or is_excluded(child):
            continue
        observer.schedule(handler, str(child), recursive=True)


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
    target_path = Path(target).resolve()
    last_event_time: dict[str, float] = {}

    class Handler(FileSystemEventHandler):
        def on_modified(self, event):
            self._handle(event, event.src_path)

        def on_created(self, event):
            self._handle(event, event.src_path)

        def on_moved(self, event):
            # Many editors and tools save atomically (write to a temp file,
            # then rename it over the original) rather than writing
            # in-place — that produces a "moved" event on the final path,
            # not "modified". Without this, saves from any tool using that
            # pattern (confirmed: `sed -i`, and Claude Code's own file
            # write) would be silently missed entirely.
            self._handle(event, event.dest_path)

        def _handle(self, event, path: str) -> None:
            if event.is_directory or not path.endswith(".py"):
                return
            if is_excluded(Path(path)):
                return
            if not _should_dispatch(last_event_time, path, time.monotonic()):
                return

            results = orchestrator.dispatch(
                "on-save", target=str(target_path), changed_file=path
            )
            # orchestrator.dispatch isolates a crashing agent so it can't
            # take down the watcher — but if nothing here surfaces that
            # crash, it's just as bad as a crash: the developer sees
            # nothing print at all and has no idea the watcher stopped
            # actually checking their save. Every result — including a
            # crash report (passed: None) — must be visible.
            for result in results:
                if result.get("passed") is None:
                    print(f"[{result['agent']}] {result['summary']}")

    observer = Observer()
    _schedule_watches(observer, Handler(), target_path)
    observer.start()
    print(
        f"Watching {target_path} for changes "
        "(excluding .venv, ai-test-tool, __pycache__, .git)... (Ctrl+C to stop)"
    )

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


if __name__ == "__main__":
    main()
