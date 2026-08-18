# ai-test-tool

Orchestration, test-maintenance, reliability, documentation, and
notification agents for AI-assisted test maintenance. Built to operate on
the `travel-planner` app one directory up, but doesn't hardcode that —
every agent takes a `target` repo path.

## What's here

- **Orchestration agent** (`ai_test_tool/orchestrator.py`) — dispatches a
  git lifecycle stage (`pre-commit`, `post-commit`, `pre-push`, `on-save`)
  to whichever agents are registered for it, in order.
- **Test-maintenance agent** (`ai_test_tool/agents/test_maintenance.py`) —
  scans whatever source files changed in the current commit (or the single
  file just saved, for `on-save`) for functions with no test coverage, and
  writes tests for them via the Claude API. Scoped to the current change,
  not the whole repository, and capped at `MAX_FUNCTIONS_PER_RUN` per
  dispatch. See [AI setup](#ai-setup) below — without an API key, this
  agent no-ops with a clear reason instead of blocking anything.
- **Reliability agent** (`ai_test_tool/agents/reliability.py`) —
  independently verifies whether a generated test is actually trustworthy:
  runs it for real, checks its assertions can fail, checks it isn't
  hallucinating code that doesn't exist, and checks it carries the
  AI-generated disclosure marker (EU AI Act, Article 50).
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

See [RESPONSIBLE_AI.md](RESPONSIBLE_AI.md) for how human oversight,
fairness, accessibility, and data handling are addressed structurally, not
just in policy.

## Setup

From this directory:

```bash
pip install -e ".[dev]"
```

### AI setup

Test-maintenance generation needs the optional `anthropic` package and an
API key:

```bash
pip install -e ".[ai]"
```

```bash
export ANTHROPIC_API_KEY=sk-ant-...
```

Without this, every other agent (hooks, reliability, documentation,
notification) works normally — test-maintenance just reports
`AIUnavailable` as the skip reason for any untested function it finds,
rather than blocking the commit or crashing the hook. Override the model
with `AI_TEST_TOOL_MODEL` if needed; defaults to `claude-sonnet-4-5`.

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

## Extending with a new agent

To add another agent (beyond the five above):

1. Add a module in `ai_test_tool/agents/`, exposing:

   ```python
   def run(target: str, stage: str, **context) -> dict:
       ...
   ```

   matching the `AgentReport` shape in `ai_test_tool/agents/contracts.py`.

2. Register it in `ai_test_tool/agents/plugins.py` — see the comments
   there for which stage(s) each should run on.

Nothing in the orchestrator needs to change for this — `plugins.py` is the
one file that couples the orchestrator to a given agent module, and it's
written to fail gracefully (do nothing) if a module hasn't been added yet.
