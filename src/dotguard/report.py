"""Render issues for people (text) and for tools (JSON, GitHub annotations)."""

from __future__ import annotations

import json
import os
import sys
from typing import TextIO

from dotguard.models import Issue, Severity

FORMATS = ("text", "json", "github")


def _use_color(stream: TextIO) -> bool:
    if os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("FORCE_COLOR"):
        return True
    return hasattr(stream, "isatty") and stream.isatty()


def _check_mark(stream: TextIO) -> str:
    # Windows consoles often use a legacy code page that cannot encode "✓".
    try:
        "✓".encode(getattr(stream, "encoding", None) or "utf-8")
    except (UnicodeEncodeError, LookupError):
        return "OK:"
    return "✓"


def _paint(text: str, code: str, enabled: bool) -> str:
    return f"\033[{code}m{text}\033[0m" if enabled else text


def render(issues: list[Issue], fmt: str = "text", stream: TextIO | None = None) -> None:
    # Resolve stdout at call time so redirection (and tests) work.
    stream = stream or sys.stdout
    if fmt == "json":
        json.dump({"issues": [i.to_dict() for i in issues], "summary": summary(issues)}, stream, indent=2)
        stream.write("\n")
    elif fmt == "github":
        _render_github(issues, stream)
    else:
        _render_text(issues, stream)


def summary(issues: list[Issue]) -> dict:
    errors = sum(1 for i in issues if i.severity is Severity.ERROR)
    return {"errors": errors, "warnings": len(issues) - errors}


def _render_text(issues: list[Issue], stream: TextIO) -> None:
    color = _use_color(stream)
    for item in issues:
        location = item.path if item.line is None else f"{item.path}:{item.line}"
        if item.severity is Severity.ERROR:
            label = _paint("error", "1;31", color)
        else:
            label = _paint("warning", "1;33", color)
        stream.write(f"{_paint(location, '2', color)}  {label} {item.code}  {item.message}\n")

    counts = summary(issues)
    if not issues:
        stream.write(_paint(f"{_check_mark(stream)} no problems found", "32", color) + "\n")
    else:
        stream.write(f"\n{counts['errors']} error(s), {counts['warnings']} warning(s)\n")


def _render_github(issues: list[Issue], stream: TextIO) -> None:
    # https://docs.github.com/actions/reference/workflow-commands-for-github-actions
    for item in issues:
        level = "error" if item.severity is Severity.ERROR else "warning"
        props = f"file={item.path}"
        if item.line is not None:
            props += f",line={item.line}"
        props += f",title=dotguard {item.code}"
        message = item.message.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")
        stream.write(f"::{level} {props}::{message}\n")
