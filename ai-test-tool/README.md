# ai-test-tool

Orchestration, documentation, and notification agents for AI-assisted test
maintenance. Built to operate on the `travel-planner` app one directory up,
but doesn't hardcode that — every agent takes a `target` repo path.

Test-maintenance and reliability/verification are owned by teammates using
different AI tools (Copilot, ChatGPT) and plug in separately — see
[Extending with teammates' agents](#extending-with-teammates-agents) below.

## What's here

- **Orchestration agent** (`ai_test_tool/orchestrator.py`) — dispatches a
  git lifecycle stage (`pre-commit`, `post-commit`, `pre-push`, `on-save`)
  to whichever agents are registered for it, in order.
- **Documentation agent** (`ai_test_tool/agents/documentation.py`) — after
  each commit, appends an entry to the target repo's `CHANGELOG.md` with
  what changed and, where available, *why*.
- **Notification/UX agent** (`ai_test_tool/agents/notification.py`) —
  re-runs the test suite on every file save and prints an immediate
  pass/fail notification, so a developer finds out before they ever commit.
- **Hooks** (`ai_test_tool/hooks/`) — `pre-commit`/`post-commit`/`pre-push`/
  `post-merge` templates that call back into this tool, plus an installer.
  `post-merge` matters specifically for PRs merged on GitHub's web UI —
  that happens server-side, so a plain `git pull` afterward wouldn't
  otherwise trigger `post-commit`/documentation logging at all.

## Setup

From this directory:

```bash
pip install -e ".[dev]"
```

Install the git hooks into the target repo (defaults to the parent
directory, i.e. `travel-planner`):

```bash
python -m ai_test_tool.cli init ..
```

Start the live watcher (leave this running in a spare terminal, or wire it
to a VS Code task):

```bash
python -m ai_test_tool.cli watch ..
```

Write the one-time baseline changelog entry, before any agent has touched
the target repo:

```python
from ai_test_tool.agents.documentation import write_baseline
write_baseline("..")
```

## Running the tool's own tests

```bash
pytest -q
```

These test the agents' own logic (orchestrator dispatch order, changelog
formatting, notification state changes) — separate from whatever tests
exist in the target repo.

## Extending with teammates' agents

Test-maintenance and reliability don't live here — they're built with
different AI tools by teammates. To plug one in:

1. Add a module in `ai_test_tool/agents/`, e.g. `test_maintenance.py` or
   `reliability.py`, exposing:

   ```python
   def run(target: str, stage: str, **context) -> dict:
       ...
   ```

   matching the `AgentReport` shape in `ai_test_tool/agents/contracts.py`.

2. Register it in `ai_test_tool/agents/plugins.py` — see the comments
   there for which stage(s) each should run on.

Nothing in the orchestrator needs to change for this — `plugins.py` is the
one file that couples the orchestrator to teammate-provided code, and it's
written to fail gracefully (do nothing) if a module hasn't been added yet.
