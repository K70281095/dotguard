"""dotguard: validate .env files against a documented .env.example."""

from dotguard.checker import check
from dotguard.differ import diff
from dotguard.models import Entry, EnvFile, Issue, Severity
from dotguard.parser import parse, parse_file
from dotguard.secrets import scan

__version__ = "0.2.0"

__all__ = [
    "Entry",
    "EnvFile",
    "Issue",
    "Severity",
    "check",
    "diff",
    "parse",
    "parse_file",
    "scan",
    "__version__",
]
