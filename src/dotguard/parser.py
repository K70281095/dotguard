"""A small, dependency-free parser for .env files.

Supported syntax:

    # a comment
    KEY=value
    export KEY=value
    KEY="double quoted with \\n escapes"   # trailing comment
    KEY='single quoted, taken literally'
    KEY=value # trailing comment (needs a space before #)

Annotation comments directly above a key attach metadata to it:

    # @type port
    # @required
    PORT=8080
"""

from __future__ import annotations

import re
from typing import Dict, List, Tuple

from dotguard.models import Entry, EnvFile


class ParseError(ValueError):
    def __init__(self, message: str, path: str, line: int) -> None:
        super().__init__(f"{path}:{line}: {message}")
        self.path = path
        self.line = line


_KEY_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_.]*$")
_ANNOTATION_RE = re.compile(r"^@([a-z][a-z0-9_-]*)(?:\s+(.*))?$")
_ESCAPES = {"n": "\n", "t": "\t", "r": "\r", '"': '"', "\\": "\\", "$": "$"}


def parse_file(path: str) -> EnvFile:
    with open(path, encoding="utf-8") as handle:
        return parse(handle.read(), path=path)


def parse(text: str, path: str = "<string>") -> EnvFile:
    env = EnvFile(path=path)
    annotations: Dict[str, str] = {}
    doc: List[str] = []

    for number, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()

        if not line:
            # A blank line detaches comments from the next key.
            annotations, doc = {}, []
            continue

        if line.startswith("#"):
            comment = line[1:].strip()
            match = _ANNOTATION_RE.match(comment)
            if match:
                annotations[match.group(1)] = (match.group(2) or "").strip()
            else:
                doc.append(comment)
            continue

        key, value = _parse_assignment(line, path, number)
        if env.get(key) is not None:
            raise ParseError(f"duplicate key {key!r}", path, number)
        env.entries.append(
            Entry(key=key, value=value, line=number, annotations=annotations, doc=doc)
        )
        annotations, doc = {}, []

    return env


def _parse_assignment(line: str, path: str, number: int) -> Tuple[str, str]:
    if line.startswith("export "):
        line = line[len("export "):].lstrip()

    if "=" not in line:
        raise ParseError("expected KEY=value", path, number)

    key, rest = line.split("=", 1)
    key = key.strip()
    if not _KEY_RE.match(key):
        raise ParseError(f"invalid key {key!r}", path, number)

    rest = rest.strip()
    if rest.startswith('"'):
        value, tail = _read_quoted(rest, '"', path, number)
        value = _unescape(value)
    elif rest.startswith("'"):
        value, tail = _read_quoted(rest, "'", path, number)
    else:
        value, tail = _strip_inline_comment(rest), ""

    if tail and not tail.lstrip().startswith("#"):
        raise ParseError("unexpected text after closing quote", path, number)
    return key, value


def _read_quoted(text: str, quote: str, path: str, number: int) -> Tuple[str, str]:
    i = 1
    while i < len(text):
        char = text[i]
        if char == "\\" and quote == '"':
            i += 2
            continue
        if char == quote:
            return text[1:i], text[i + 1:]
        i += 1
    raise ParseError("unterminated quoted value", path, number)


def _unescape(value: str) -> str:
    out = []
    i = 0
    while i < len(value):
        char = value[i]
        if char == "\\" and i + 1 < len(value):
            nxt = value[i + 1]
            out.append(_ESCAPES.get(nxt, "\\" + nxt))
            i += 2
        else:
            out.append(char)
            i += 1
    return "".join(out)


def _strip_inline_comment(value: str) -> str:
    # "a#b" stays as-is (common in URLs); only " #" starts a comment.
    match = re.search(r"\s#", value)
    if match:
        value = value[: match.start()]
    return value.strip()
