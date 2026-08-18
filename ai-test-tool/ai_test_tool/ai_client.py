"""Thin wrapper around the Claude API, used by test-maintenance to write tests.

Isolated into its own module for two reasons:

1. It's the one seam that needs mocking in tests — nothing in this project's
   own test suite should make a real network call or require a real API key.
2. `anthropic` stays an *optional* dependency (see pyproject.toml). A repo
   that never sets ANTHROPIC_API_KEY can still install and run ai-test-tool
   normally; test generation just no-ops with a clear reason instead of
   crashing the import, or worse, a git hook.
"""

import os

DEFAULT_MODEL = "claude-sonnet-4-5"
DEFAULT_TIMEOUT_SECONDS = 30.0


class AIUnavailable(Exception):
    """Raised when a test can't be generated — missing key, missing package,
    network failure, or a malformed response. Callers are expected to treat
    this as "skip this function, note why," never as a reason to crash the
    calling git hook.
    """


def generate(prompt: str, *, max_tokens: int = 1024) -> str:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise AIUnavailable("ANTHROPIC_API_KEY is not set")

    try:
        import anthropic
    except ImportError as exc:
        raise AIUnavailable(
            "the 'anthropic' package is not installed (pip install anthropic)"
        ) from exc

    client = anthropic.Anthropic(api_key=api_key, timeout=DEFAULT_TIMEOUT_SECONDS)
    model = os.environ.get("AI_TEST_TOOL_MODEL", DEFAULT_MODEL)

    try:
        response = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
    except anthropic.APIError as exc:
        raise AIUnavailable(f"Claude API call failed: {exc}") from exc

    text = "".join(
        block.text for block in response.content if getattr(block, "type", None) == "text"
    )
    if not text.strip():
        raise AIUnavailable("Claude returned an empty response")
    return text
