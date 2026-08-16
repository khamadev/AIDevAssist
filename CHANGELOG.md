# Changelog

## Wed Aug 12 22:43:01 2026 +0300 — Remove unused env example files
- Commit: `f55df5b`
- Author: MuhdKhamarullah
- Changes:
```
.env.example       | 5 -----
 .env.local.example | 5 -----
 2 files changed, 10 deletions(-)
```

## 2026-08-13 06:37 UTC — Baseline
- Functions found: 25
- Existing tests: 4
- AI-modified files so far: 0

## Thu Aug 13 09:41:56 2026 +0300 — Scaffold ai-test-tool: orchestration, documentation, notification agents + hooks
- Commit: `980b86f`
- Author: MuhdKhamarullah
- Changes:
```
.github/workflows/ai-test-tool-tests.yml           |  31 ++++
 .github/workflows/tests.yml                        |   4 +
 .gitignore                                         |   1 +
 CHANGELOG.md                                       |  17 ++
 ai-test-tool/.claude/agents/documentation.md       |  46 +++++
 ai-test-tool/.claude/agents/notification.md        |  50 ++++++
 ai-test-tool/.claude/agents/orchestration.md       |  47 +++++
 ai-test-tool/README.md                             |  85 +++++++++
 ai-test-tool/ai_test_tool.egg-info/PKG-INFO        |   8 +
 ai-test-tool/ai_test_tool.egg-info/SOURCES.txt     |  21 +++
 .../ai_test_tool.egg-info/dependency_links.txt     |   1 +
 .../ai_test_tool.egg-info/entry_points.txt         |   2 +
 ai-test-tool/ai_test_tool.egg-info/requires.txt    |   4 +
 ai-test-tool/ai_test_tool.egg-info/top_level.txt   |   1 +
 ai-test-tool/ai_test_tool/__init__.py              |   0
 ai-test-tool/ai_test_tool/agents/__init__.py       |   0
 ai-test-tool/ai_test_tool/agents/contracts.py      |  60 +++++++
 ai-test-tool/ai_test_tool/agents/documentation.py  | 200 +++++++++++++++++++++
 ai-test-tool/ai_test_tool/agents/notification.py   |  57 ++++++
 ai-test-tool/ai_test_tool/agents/plugins.py        |  42 +++++
 ai-test-tool/ai_test_tool/cli.py                   | 107 +++++++++++
 ai-test-tool/ai_test_tool/hooks/__init__.py        |   0
 ai-test-tool/ai_test_tool/hooks/install.py         |  29 +++
 .../ai_test_tool/hooks/post-commit.template        |   5 +
 .../ai_test_tool/hooks/pre-commit.template         |   6 +
 ai-test-tool/ai_test_tool/hooks/pre-push.template  |   6 +
 ai-test-tool/ai_test_tool/orchestrator.py          |  58 ++++++
 ai-test-tool/pyproject.toml                        |  18 ++
 ai-test-tool/tests/__init__.py                     |   0
 ai-test-tool/tests/conftest.py                     |  31 ++++
 ai-test-tool/tests/test_documentation.py           |  72 ++++++++
 ai-test-tool/tests/test_notification.py            |  55 ++++++
 ai-test-tool/tests/test_orchestrator.py            |  64 +++++++
 33 files changed, 1128 insertions(+)
```

## Thu Aug 13 09:45:55 2026 +0300 — Fix pytest collecting ai-test-tool/tests when run from repo root
- Commit: `f4ff73e`
- Author: MuhdKhamarullah
- Changes:
```
.github/workflows/tests.yml | 2 +-
 pytest.ini                  | 3 +++
 2 files changed, 4 insertions(+), 1 deletion(-)
```

## Thu Aug 13 09:51:15 2026 +0300 — Test: verify hooks fire correctly
- Commit: `db67781`
- Author: MuhdKhamarullah
- Changes:
```
README.md | Bin 4006 -> 4054 bytes
 1 file changed, 0 insertions(+), 0 deletions(-)
```

## Thu Aug 13 09:55:46 2026 +0300 — Fix README encoding corrupted by PowerShell redirection
- Commit: `b4b4887`
- Author: MuhdKhamarullah
- Changes:
```
README.md | Bin 4054 -> 4006 bytes
 1 file changed, 0 insertions(+), 0 deletions(-)
```

## Fri Aug 14 09:10:17 2026 +0300 — Update .gitignore
- Commit: `beb4514`
- Author: MuhdKhamarullah
- Changes:
```
.gitignore   |  1 +
 CHANGELOG.md | 69 ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
 2 files changed, 70 insertions(+)
```

## Fri Aug 14 09:48:21 2026 +0300 — Stop tracking .env.local, already covered by .gitignore
- Commit: `becda60`
- Author: MuhdKhamarullah
- Changes:
```
.env.local | 5 -----
 1 file changed, 5 deletions(-)
```

## Fri Aug 14 09:56:00 2026 +0300 — Add Claude Code reliability agent spec, untrack egg-info build artifacts
- Commit: `f40b8f4`
- Author: MuhdKhamarullah
- Changes:
```
.gitignore                                         |  1 +
 CHANGELOG.md                                       | 19 +++++++
 ai-test-tool/.claude/agents/reliability.md         | 58 ++++++++++++++++++++++
 ai-test-tool/ai_test_tool.egg-info/PKG-INFO        |  8 ---
 ai-test-tool/ai_test_tool.egg-info/SOURCES.txt     | 21 --------
 .../ai_test_tool.egg-info/dependency_links.txt     |  1 -
 .../ai_test_tool.egg-info/entry_points.txt         |  2 -
 ai-test-tool/ai_test_tool.egg-info/requires.txt    |  4 --
 ai-test-tool/ai_test_tool.egg-info/top_level.txt   |  1 -
 9 files changed, 78 insertions(+), 37 deletions(-)
```

## Fri Aug 14 10:06:20 2026 +0300 — Fix reliability agent blocking unrelated commits; implement with EU AI Act Art. 50 check
- Commit: `52f8633`
- Author: MuhdKhamarullah
- Changes:
```
CHANGELOG.md                                    |  17 ++
 ai-test-tool/.claude/agents/reliability.md      |  19 +++
 ai-test-tool/ai_test_tool/agents/contracts.py   |   3 +
 ai-test-tool/ai_test_tool/agents/plugins.py     |  11 +-
 ai-test-tool/ai_test_tool/agents/reliability.py | 204 ++++++++++++++++++++++++
 ai-test-tool/tests/test_reliability.py          | 158 ++++++++++++++++++
 6 files changed, 408 insertions(+), 4 deletions(-)
```

## Fri Aug 14 10:36:31 2026 +0300 — Extend reliability: multi-file verification, hallucination detection; harden notification watcher (exclude .venv/etc, debounce)
- Commit: `98103a1`
- Author: MuhdKhamarullah
- Changes:
```
CHANGELOG.md                                       |  14 +++
 ai-test-tool/.claude/agents/notification.md        |  18 ++-
 ai-test-tool/.claude/agents/reliability.md         |  31 +++--
 ai-test-tool/README.md                             |   7 +-
 ai-test-tool/ai_test_tool/agents/contracts.py      |  20 ++-
 ai-test-tool/ai_test_tool/agents/documentation.py  |  20 +--
 ai-test-tool/ai_test_tool/agents/reliability.py    | 139 +++++++++++++++------
 ai-test-tool/ai_test_tool/cli.py                   |  62 +++++++--
 ai-test-tool/ai_test_tool/exclusions.py            |  22 ++++
 ai-test-tool/ai_test_tool/hooks/install.py         |  33 ++++-
 .../ai_test_tool/hooks/post-merge.template         |  10 ++
 ai-test-tool/ai_test_tool/orchestrator.py          |  23 +++-
 ai-test-tool/tests/test_cli_watch.py               |  61 +++++++++
 ai-test-tool/tests/test_hooks_install.py           |  54 ++++++++
 ai-test-tool/tests/test_orchestrator.py            |  55 ++++++++
 ai-test-tool/tests/test_reliability.py             |  96 ++++++++++++++
 16 files changed, 582 insertions(+), 83 deletions(-)
```

## Fri Aug 14 10:52:06 2026 +0300 — Scope Copilot instructions to ai-test-tool/, fix .NET-vs-Python framework mismatch
- Commit: `74e01b2`
- Author: MuhdKhamarullah
- Changes:
```
.github/copilot-instructions.md                    | 16 -------
 .../instructions/test-maintenance.instructions.md  | 51 ++++++++++++++++++++++
 CHANGELOG.md                                       | 24 ++++++++++
 3 files changed, 75 insertions(+), 16 deletions(-)
```

## Fri Aug 14 10:55:10 2026 +0300 — Scope README to Docker-only; make docker-compose self-contained (no .env required)
- Commit: `b1f5d23`
- Author: MuhdKhamarullah
- Changes:
```
CHANGELOG.md       | 11 ++++++++
 README.md          | 82 ++++++++++--------------------------------------------
 docker-compose.yml |  4 ++-
 3 files changed, 29 insertions(+), 68 deletions(-)
```

## Sun Aug 16 13:56:03 2026 +0300 — Fix AI-disclosure check to scan whole file, not just first 500 chars
- Commit: `63b1839`
- Author: MuhdKhamarullah
- Changes:
```
CHANGELOG.md                                    | 11 +++++++++++
 ai-test-tool/ai_test_tool/agents/reliability.py | 14 +++++++++-----
 ai-test-tool/tests/test_reliability.py          | 22 ++++++++++++++++++++++
 3 files changed, 42 insertions(+), 5 deletions(-)
```

