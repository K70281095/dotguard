"""Value validators used by the ``@type`` annotation."""

from __future__ import annotations

import re
from typing import Callable, Optional
from urllib.parse import urlparse

# A validator returns None when the value is valid, or a short reason otherwise.
Validator = Callable[[str], Optional[str]]

_TRUE = {"1", "true", "yes", "on"}
_FALSE = {"0", "false", "no", "off"}
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _string(value: str) -> str | None:
    return None


def _int(value: str) -> str | None:
    try:
        int(value, 10)
    except ValueError:
        return "expected an integer"
    return None


def _float(value: str) -> str | None:
    try:
        float(value)
    except ValueError:
        return "expected a number"
    return None


def _bool(value: str) -> str | None:
    if value.lower() in _TRUE | _FALSE:
        return None
    return "expected a boolean (true/false, yes/no, on/off, 1/0)"


def _port(value: str) -> str | None:
    if _int(value) is not None or not 1 <= int(value) <= 65535:
        return "expected a port number between 1 and 65535"
    return None


def _url(value: str) -> str | None:
    parsed = urlparse(value)
    if parsed.scheme and parsed.netloc:
        return None
    return "expected a URL with a scheme and host, e.g. https://example.com"


def _email(value: str) -> str | None:
    if _EMAIL_RE.match(value):
        return None
    return "expected an email address"


VALIDATORS: dict[str, Validator] = {
    "string": _string,
    "str": _string,
    "int": _int,
    "integer": _int,
    "float": _float,
    "number": _float,
    "bool": _bool,
    "boolean": _bool,
    "port": _port,
    "url": _url,
    "email": _email,
}

NUMERIC_TYPES = {"int", "integer", "float", "number", "port"}
