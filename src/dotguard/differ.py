"""Compare the keys of two environment files, e.g. staging and production."""

from __future__ import annotations

from dotguard.models import EnvFile, Issue, Severity


def diff(left: EnvFile, right: EnvFile, compare_values: bool = False) -> list[Issue]:
    """Report keys that exist in only one file.

    With ``compare_values``, also report keys whose values differ. Values are
    never included in the messages, so the output is safe to share.
    """
    issues: list[Issue] = []
    right_keys = set(right.keys())
    left_keys = set(left.keys())

    for entry in left.entries:
        if entry.key not in right_keys:
            issues.append(
                Issue(
                    "DD001",
                    f"{entry.key} is set in {left.path} but missing from {right.path}",
                    Severity.ERROR,
                    left.path,
                    entry.line,
                    entry.key,
                )
            )

    for entry in right.entries:
        if entry.key not in left_keys:
            issues.append(
                Issue(
                    "DD002",
                    f"{entry.key} is set in {right.path} but missing from {left.path}",
                    Severity.ERROR,
                    right.path,
                    entry.line,
                    entry.key,
                )
            )

    if compare_values:
        for entry in left.entries:
            other = right.get(entry.key)
            if other is not None and other.value != entry.value:
                issues.append(
                    Issue(
                        "DD003",
                        f"{entry.key} has a different value in {right.path}:{other.line}",
                        Severity.WARNING,
                        left.path,
                        entry.line,
                        entry.key,
                    )
                )

    return issues
