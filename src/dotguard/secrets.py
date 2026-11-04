"""Find real-looking secrets in files that are meant to be committed."""

from __future__ import annotations

import math
import re
from collections import Counter
from typing import List, Tuple

from dotguard.models import EnvFile, Issue, Severity

# Well-known credential formats. Each match is an error: these are never
# placeholders.
KNOWN_TOKENS: List[Tuple[str, "re.Pattern[str]"]] = [
    ("AWS access key ID", re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b")),
    ("GitHub token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36,}\b")),
    ("GitHub fine-grained token", re.compile(r"\bgithub_pat_[A-Za-z0-9_]{60,}\b")),
    ("Slack token", re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}\b")),
    ("Stripe live key", re.compile(r"\b[sr]k_live_[A-Za-z0-9]{16,}\b")),
    ("Google API key", re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b")),
    ("OpenAI-style API key", re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9_-]{32,}\b")),
    ("private key", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("JSON Web Token", re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}")),
]

SENSITIVE_NAME = re.compile(
    r"(SECRET|TOKEN|PASSWORD|PASSWD|PWD|PRIVATE|CREDENTIAL|API_?KEY|ACCESS_?KEY|AUTH)",
    re.IGNORECASE,
)

# Values that are obviously documentation, not real credentials.
PLACEHOLDER = re.compile(
    r"^(?:|changeme|change[-_]me|replace[-_]?me|todo|secret|password|example.*|your[-_].*|"
    r"<.*>|\{\{.*\}\}|\$\{.*\}|x+|\*+|\.\.\.|null|none|test|dummy.*|fake.*|placeholder.*)$",
    re.IGNORECASE,
)

ENTROPY_THRESHOLD = 3.5
MIN_SECRET_LENGTH = 16


def shannon_entropy(value: str) -> float:
    if not value:
        return 0.0
    counts = Counter(value)
    total = len(value)
    return -sum((n / total) * math.log2(n / total) for n in counts.values())


def scan(env: EnvFile) -> List[Issue]:
    """Report values in ``env`` that look like real credentials."""
    issues: List[Issue] = []

    for entry in env.entries:
        value = entry.value

        known = next((name for name, regex in KNOWN_TOKENS if regex.search(value)), None)
        if known:
            issues.append(
                Issue(
                    "DS001",
                    f"{entry.key} contains what looks like a real {known}",
                    Severity.ERROR,
                    env.path,
                    entry.line,
                    entry.key,
                )
            )
            continue

        if PLACEHOLDER.match(value):
            continue

        looks_sensitive = SENSITIVE_NAME.search(entry.key) or "secret" in entry.annotations
        if (
            looks_sensitive
            and len(value) >= MIN_SECRET_LENGTH
            and shannon_entropy(value) >= ENTROPY_THRESHOLD
        ):
            issues.append(
                Issue(
                    "DS002",
                    f"{entry.key} has a high-entropy value; use a placeholder in shared files",
                    Severity.WARNING,
                    env.path,
                    entry.line,
                    entry.key,
                )
            )

    return issues
