"""Compare a .env file with the .env.example that documents it."""

from __future__ import annotations

import re

from dotguard.models import Entry, EnvFile, Issue, Severity
from dotguard.types import NUMERIC_TYPES, VALIDATORS

KNOWN_ANNOTATIONS = {
    "type",
    "required",
    "optional",
    "pattern",
    "values",
    "min",
    "max",
    "secret",
    "deprecated",
}


def check(env: EnvFile, example: EnvFile, strict: bool = False) -> list[Issue]:
    """Return every issue found in ``env`` according to ``example``.

    ``strict`` turns keys that exist only in ``env`` into errors instead of
    warnings.
    """
    issues: list[Issue] = []

    for spec in example.entries:
        issues.extend(_check_annotations(spec, example.path))
        entry = env.get(spec.key)

        if entry is None:
            if "optional" not in spec.annotations:
                issues.append(
                    Issue(
                        "DG001",
                        f"{spec.key} is missing (documented in {example.path}:{spec.line})",
                        Severity.ERROR,
                        env.path,
                        key=spec.key,
                    )
                )
            continue

        if "deprecated" in spec.annotations:
            reason = spec.annotations["deprecated"] or "it is deprecated"
            issues.append(
                Issue(
                    "DG008",
                    f"{spec.key} is deprecated: {reason}",
                    Severity.WARNING,
                    env.path,
                    entry.line,
                    spec.key,
                )
            )

        issues.extend(_check_value(entry, spec, env.path))

    documented = set(example.keys())
    for entry in env.entries:
        for name in entry.unresolved:
            issues.append(
                Issue(
                    "DG011",
                    f"{entry.key} references ${{{name}}}, which is not defined above it",
                    Severity.WARNING,
                    env.path,
                    entry.line,
                    entry.key,
                )
            )
        if entry.key not in documented:
            issues.append(
                Issue(
                    "DG002",
                    f"{entry.key} is not documented in {example.path}",
                    Severity.ERROR if strict else Severity.WARNING,
                    env.path,
                    entry.line,
                    entry.key,
                )
            )

    return issues


def _check_annotations(spec: Entry, path: str) -> list[Issue]:
    issues = []
    for name in spec.annotations:
        if name not in KNOWN_ANNOTATIONS:
            issues.append(
                Issue(
                    "DG009",
                    f"unknown annotation @{name} on {spec.key}",
                    Severity.WARNING,
                    path,
                    spec.line,
                    spec.key,
                )
            )

    type_name = spec.annotations.get("type")
    if type_name is not None and type_name not in VALIDATORS:
        issues.append(
            Issue(
                "DG010",
                f"unknown @type {type_name!r} on {spec.key}; "
                f"choose one of: {', '.join(sorted(VALIDATORS))}",
                Severity.ERROR,
                path,
                spec.line,
                spec.key,
            )
        )

    pattern = spec.annotations.get("pattern")
    if pattern is not None:
        try:
            re.compile(pattern)
        except re.error as exc:
            issues.append(
                Issue(
                    "DG010",
                    f"invalid @pattern on {spec.key}: {exc}",
                    Severity.ERROR,
                    path,
                    spec.line,
                    spec.key,
                )
            )
    return issues


def _check_value(entry: Entry, spec: Entry, path: str) -> list[Issue]:
    rules = spec.annotations
    value = entry.value

    def issue(code: str, message: str) -> Issue:
        return Issue(code, message, Severity.ERROR, path, entry.line, entry.key)

    if value == "":
        if "required" in rules:
            return [issue("DG003", f"{entry.key} is required but empty")]
        # An empty optional value has nothing else to validate.
        return []

    type_name = rules.get("type", "string")
    validator = VALIDATORS.get(type_name)
    if validator is not None:
        reason = validator(value)
        if reason:
            return [issue("DG004", f"{entry.key}={_preview(value, rules)}: {reason}")]

    issues = []

    pattern = rules.get("pattern")
    if pattern is not None:
        try:
            if not re.fullmatch(pattern, value):
                issues.append(
                    issue("DG005", f"{entry.key} does not match pattern {pattern!r}")
                )
        except re.error:
            pass  # Already reported by _check_annotations.

    allowed = rules.get("values")
    if allowed:
        choices = [choice.strip() for choice in allowed.split(",") if choice.strip()]
        if value not in choices:
            issues.append(
                issue(
                    "DG007",
                    f"{entry.key}={_preview(value, rules)} is not one of: {', '.join(choices)}",
                )
            )

    if type_name in NUMERIC_TYPES:
        number = float(value)
        for bound, compare, word in (("min", float.__lt__, "below"), ("max", float.__gt__, "above")):
            limit = rules.get(bound)
            if limit is None:
                continue
            try:
                limit_value = float(limit)
            except ValueError:
                continue
            if compare(number, limit_value):
                issues.append(
                    issue("DG006", f"{entry.key}={value} is {word} the @{bound} of {limit}")
                )

    return issues


def _preview(value: str, rules: dict) -> str:
    """Never echo a secret back to the terminal or a CI log."""
    if "secret" in rules:
        return "****"
    return value if len(value) <= 40 else value[:37] + "..."
