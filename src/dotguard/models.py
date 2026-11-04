"""Data types shared across dotguard."""

from __future__ import annotations

import enum
from dataclasses import dataclass, field


class Severity(str, enum.Enum):
    ERROR = "error"
    WARNING = "warning"


@dataclass
class Entry:
    """A single KEY=value assignment in a .env file."""

    key: str
    value: str
    line: int
    # Annotations come from "# @name value" comments directly above the key.
    annotations: dict[str, str] = field(default_factory=dict)
    # Plain comment lines above the key, used as human documentation.
    doc: list[str] = field(default_factory=list)
    # Names referenced as $NAME / ${NAME} that were not defined earlier.
    unresolved: list[str] = field(default_factory=list)


@dataclass
class EnvFile:
    path: str
    entries: list[Entry] = field(default_factory=list)

    def get(self, key: str) -> Entry | None:
        for entry in self.entries:
            if entry.key == key:
                return entry
        return None

    def keys(self) -> list[str]:
        return [entry.key for entry in self.entries]


@dataclass
class Issue:
    """A problem found while checking or scanning a file."""

    code: str
    message: str
    severity: Severity
    path: str
    line: int | None = None
    key: str | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "code": self.code,
            "message": self.message,
            "severity": self.severity.value,
            "path": self.path,
            "line": self.line,
            "key": self.key,
        }
