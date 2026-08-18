"""Redacts likely secrets from source code before it's sent to the AI model.

Not a replacement for git-native secret scanning (e.g. a pre-commit hook
running gitleaks/trufflehog) — this is a narrow, defense-in-depth pass
specifically for the one place this project sends code to a third party:
test_maintenance.py's prompt to Claude. Regex-based secret detection has
real, known blind spots (anything not matching a recognized pattern or
naming convention passes through untouched); false positives (redacting
something that wasn't actually a secret) are treated as the safer failure
mode than false negatives, since a redacted placeholder still lets the
model write a perfectly good test — it just can't see the real value.
"""

import re
from collections.abc import Callable

_REDACTED = "[REDACTED]"

_ASSIGNMENT_PATTERN = re.compile(
    r"(?i)(?P<prefix>(api[_-]?key|secret[_-]?key|access[_-]?token|"
    r"auth[_-]?token|password|passwd|pwd)\s*"
    # Optional type annotation (`password: str = ...`) before the `=`.
    r"(?::\s*\w+\s*)?[:=]\s*)"
    r"(?P<quote>['\"])(?P<value>[^'\"]{6,})(?P=quote)"
)


def _redact_assignment(match: re.Match) -> str:
    return f"{match.group('prefix')}{match.group('quote')}{_REDACTED}{match.group('quote')}"


# Each rule is (pattern, replacement). Replacement can be a literal string
# or a callable taking the match, matching re.sub's own contract.
_RULES: list[tuple[re.Pattern, str | Callable[[re.Match], str]]] = [
    # AWS access key IDs have a fixed, recognizable prefix and length.
    (re.compile(r"AKIA[0-9A-Z]{16}"), _REDACTED),
    # PEM-format private key blocks.
    (
        re.compile(r"-----BEGIN[ A-Z]*PRIVATE KEY-----[\s\S]*?-----END[ A-Z]*PRIVATE KEY-----"),
        _REDACTED,
    ),
    # Bearer tokens in Authorization-header-style strings.
    (re.compile(r"Bearer\s+[A-Za-z0-9\-_.=]{10,}"), f"Bearer {_REDACTED}"),
    # Assignment to a name that strongly suggests a secret, quoted value —
    # keeps the variable name and quote style so the redacted code still
    # parses and reads naturally, only the value itself is hidden.
    (_ASSIGNMENT_PATTERN, _redact_assignment),
]


def redact(source: str) -> tuple[str, bool]:
    """Returns (possibly-redacted source, whether anything was redacted)."""
    result = source
    redacted_any = False
    for pattern, replacement in _RULES:
        result, count = pattern.subn(replacement, result)
        if count:
            redacted_any = True
    return result, redacted_any
