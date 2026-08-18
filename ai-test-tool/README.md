# ai-test-tool

Orchestration, test-maintenance, reliability, documentation, and
notification agents for AI-assisted test maintenance. Built to operate on
the `travel-planner` app one directory up, but doesn't hardcode that —
every agent takes a `target` repo path.

## What's here

- **Orchestration agent** (`ai_test_tool/orchestrator.py`) — dispatches a
  stage (`pre-commit`, `post-commit`, `pre-push`, `on-save`, or `init`) to
  whichever agents are registered for it, in order. The first four fire
  automatically from git hooks or the watcher; `init` fires once, directly,
  when you run `ai-test-tool init`.
- **Test-maintenance agent** (`ai_test_tool/agents/test_maintenance.py`) —
  two entry points, two scopes:
  - `run()`, on `pre-commit`/`on-save`: scans whatever source files changed
    in the current commit (or the single file just saved) for functions
    with no test coverage, capped at `MAX_FUNCTIONS_PER_RUN` (5) per
    dispatch — cheap enough to run on every commit.
  - `scan_repository()`, on `init` only: scans **every** non-excluded `.py`
    file in the repo, not just the current change, capped at
    `MAX_FUNCTIONS_PER_FULL_SCAN` (25) — a one-time, thorough pass meant
    for a repo that hasn't had this tool running from the start. Never
    wired into a git hook, so a normal commit never pays full-repo-scan
    cost. Run `init --skip-scan` to install hooks without triggering it.

  Both write tests via the Claude API, with the function's source redacted
  for likely secrets before it's sent. See [AI setup](#ai-setup) below —
  without an API key, either entry point no-ops with a clear reason instead
  of blocking anything.
- **Reliability agent** (`ai_test_tool/agents/reliability.py`) —
  independently verifies whether a generated test is actually trustworthy:
  runs it for real, checks its assertions can fail, checks it isn't
  hallucinating code that doesn't exist, and checks it carries the
  AI-generated disclosure marker (EU AI Act, Article 50). Runs on
  `pre-commit`, `pre-push`, and `init` — always after test-maintenance,
  verifying whatever it just generated.
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
directory, i.e. `travel-planner`). By default this also runs a one-time
full-repository scan for untested functions right away (test-maintenance,
then reliability) — useful for a repo that hasn't had this tool running
from the start, since per-commit scanning alone would only ever catch gaps
in future changes, not existing ones:

```bash
python -m ai_test_tool.cli init ..
```

Generated tests are written to disk but not staged or committed
automatically — review with `git diff`, then `git add` and commit whatever
you're satisfied with. Skip the scan (install hooks only) with:

```bash
python -m ai_test_tool.cli init .. --skip-scan
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
