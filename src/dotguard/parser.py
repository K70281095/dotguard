"""A small, dependency-free parser for .env files.

Supported syntax:

    # a comment
    KEY=value
    export KEY=value
    KEY="double quoted with \\n escapes"   # trailing comment
    KEY='single quoted, taken literally'
    KEY=value # trailing comment (needs a space before #)
    KEY="a quoted value
    can span several lines"
    URL=http://${HOST}:${PORT:-8080}/   # references to earlier keys

Annotation comments directly above a key attach metadata to it:

    # @type port
    # @required
    PORT=8080
"""

from __future__ import annotations

import re

from dotguard.models import Entry, EnvFile


class ParseError(ValueError):
    def __init__(self, message: str, path: str, line: int) -> None:
        super().__init__(f"{path}:{line}: {message}")
        self.path = path
        self.line = line


_KEY_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_.]*$")
_ANNOTATION_RE = re.compile(r"^@([a-z][a-z0-9_-]*)(?:\s+(.*))?$")
_ESCAPES = {"n": "\n", "t": "\t", "r": "\r", '"': '"', "\\": "\\", "$": "$"}
# ${NAME}, ${NAME:-default}, ${NAME-default} or $NAME
_REFERENCE_RE = re.compile(
    r"\$(?:\{(?P<braced>[A-Za-z_][A-Za-z0-9_]*)(?:(?P<op>:?-)(?P<default>[^}]*))?\}"
    r"|(?P<bare>[A-Za-z_][A-Za-z0-9_]*))"
)


def parse_file(path: str, interpolate: bool = True) -> EnvFile:
    with open(path, encoding="utf-8") as handle:
        return parse(handle.read(), path=path, interpolate=interpolate)


def parse(text: str, path: str = "<string>", interpolate: bool = True) -> EnvFile:
    """Parse ``text`` into an :class:`EnvFile`.

    With ``interpolate``, ``$NAME`` and ``${NAME}`` in unquoted and
    double-quoted values are replaced by the value of a key defined earlier in
    the same file. Names that are not defined expand to an empty string and are
    recorded in ``Entry.unresolved``.
    """
    env = EnvFile(path=path)
    annotations: dict[str, str] = {}
    doc: list[str] = []
    lines = text.splitlines()
    index = 0

    while index < len(lines):
        number = index + 1
        line = lines[index].strip()
        index += 1

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

        key, rest = _split_assignment(line, path, number)

        # A quoted value may continue on the following lines until its
        # closing quote.
        if rest[:1] in ('"', "'"):
            while _find_closing_quote(rest, rest[0]) is None and index < len(lines):
                rest += "\n" + lines[index]
                index += 1

        known = {entry.key: entry.value for entry in env.entries} if interpolate else None
        unresolved: list[str] = []
        value = _parse_value(rest, path, number, known, unresolved)

        if env.get(key) is not None:
            raise ParseError(f"duplicate key {key!r}", path, number)
        env.entries.append(
            Entry(
                key=key,
                value=value,
                line=number,
                annotations=annotations,
                doc=doc,
                unresolved=unresolved,
            )
        )
        annotations, doc = {}, []

    return env


def _split_assignment(line: str, path: str, number: int) -> tuple[str, str]:
    if line.startswith("export "):
        line = line[len("export "):].lstrip()

    if "=" not in line:
        raise ParseError("expected KEY=value", path, number)

    key, rest = line.split("=", 1)
    key = key.strip()
    if not _KEY_RE.match(key):
        raise ParseError(f"invalid key {key!r}", path, number)
    return key, rest.strip()


def _parse_value(
    rest: str,
    path: str,
    number: int,
    known: dict[str, str] | None,
    unresolved: list[str],
) -> str:
    if rest.startswith("'"):
        # Single quotes: everything is literal, no escapes, no references.
        end = _find_closing_quote(rest, "'")
        if end is None:
            raise ParseError("unterminated quoted value", path, number)
        value, tail = rest[1:end], rest[end + 1:]
    elif rest.startswith('"'):
        end = _find_closing_quote(rest, '"')
        if end is None:
            raise ParseError("unterminated quoted value", path, number)
        value = _unescape(rest[1:end], known, unresolved)
        tail = rest[end + 1:]
    else:
        value = _unescape(_strip_inline_comment(rest), known, unresolved, escapes={"$": "$"})
        tail = ""

    if tail and not tail.lstrip().startswith("#"):
        raise ParseError("unexpected text after closing quote", path, number)
    return value


def _find_closing_quote(text: str, quote: str) -> int | None:
    i = 1
    while i < len(text):
        char = text[i]
        if char == "\\" and quote == '"':
            i += 2
            continue
        if char == quote:
            return i
        i += 1
    return None


def _unescape(
    value: str,
    known: dict[str, str] | None,
    unresolved: list[str],
    escapes: dict[str, str] = _ESCAPES,
) -> str:
    """Apply backslash escapes and, when ``known`` is given, expand references."""
    out = []
    i = 0
    while i < len(value):
        char = value[i]
        if char == "\\" and i + 1 < len(value) and value[i + 1] in escapes:
            out.append(escapes[value[i + 1]])
            i += 2
            continue
        if char == "$" and known is not None:
            match = _REFERENCE_RE.match(value, i)
            if match:
                out.append(_resolve(match, known, unresolved))
                i = match.end()
                continue
        out.append(char)
        i += 1
    return "".join(out)


def _resolve(match: re.Match[str], known: dict[str, str], unresolved: list[str]) -> str:
    name = match.group("braced") or match.group("bare")
    op, default = match.group("op"), match.group("default")
    value = known.get(name)

    if op == ":-" and not value:
        return default
    if op == "-" and value is None:
        return default
    if value is None:
        if name not in unresolved:
            unresolved.append(name)
        return ""
    return value


def _strip_inline_comment(value: str) -> str:
    # "a#b" stays as-is (common in URLs); only " #" starts a comment.
    match = re.search(r"\s#", value)
    if match:
        value = value[: match.start()]
    return value.strip()
