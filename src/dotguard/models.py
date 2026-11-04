"""Data types shared across dotguard."""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional


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
    annotations: Dict[str, str] = field(default_factory=dict)
    # Plain comment lines above the key, used as human documentation.
    doc: List[str] = field(default_factory=list)


@dataclass
class EnvFile:
    path: str
    entries: List[Entry] = field(default_factory=list)

    def get(self, key: str) -> Optional[Entry]:
        for entry in self.entries:
            if entry.key == key:
                return entry
        return None

    def keys(self) -> List[str]:
        return [entry.key for entry in self.entries]


@dataclass
class Issue:
    """A problem found while checking or scanning a file."""

    code: str
    message: str
    severity: Severity
    path: str
    line: Optional[int] = None
    key: Optional[str] = None

    def to_dict(self) -> Dict[str, object]:
        return {
            "code": self.code,
            "message": self.message,
            "severity": self.severity.value,
            "path": self.path,
            "line": self.line,
            "key": self.key,
        }
