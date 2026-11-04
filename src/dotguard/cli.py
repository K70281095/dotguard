"""Command-line interface: ``dotguard check | scan | diff | init``."""

from __future__ import annotations

import argparse
import os
import sys

from dotguard import __version__
from dotguard.checker import check
from dotguard.differ import diff
from dotguard.models import EnvFile, Issue, Severity
from dotguard.parser import ParseError, parse_file
from dotguard.report import FORMATS, render
from dotguard.secrets import SENSITIVE_NAME, scan
from dotguard.types import VALIDATORS

EXIT_OK = 0
EXIT_PROBLEMS = 1
EXIT_USAGE = 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="dotguard",
        description="Validate .env files against a documented .env.example.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command", metavar="COMMAND")
    sub.required = True

    def add_output_options(p: argparse.ArgumentParser) -> None:
        p.add_argument("--format", choices=FORMATS, default="text", help="output format (default: text)")
        p.add_argument(
            "--fail-on-warning",
            action="store_true",
            help="exit with status 1 on warnings too, not only on errors",
        )

    p_check = sub.add_parser("check", help="check a .env file against .env.example")
    p_check.add_argument("--env", default=".env", help="file to check (default: .env)")
    p_check.add_argument(
        "--example", default=".env.example", help="documented reference file (default: .env.example)"
    )
    p_check.add_argument(
        "--strict", action="store_true", help="treat keys missing from the example as errors"
    )
    add_output_options(p_check)

    p_scan = sub.add_parser("scan", help="look for real secrets in files you commit")
    p_scan.add_argument(
        "files", nargs="*", default=[".env.example"], help="files to scan (default: .env.example)"
    )
    add_output_options(p_scan)

    p_diff = sub.add_parser("diff", help="compare the keys of two env files, e.g. staging and production")
    p_diff.add_argument("left", help="first file, e.g. .env.staging")
    p_diff.add_argument("right", help="second file, e.g. .env.production")
    p_diff.add_argument(
        "--values",
        action="store_true",
        help="also report keys whose values differ (values themselves are never printed)",
    )
    add_output_options(p_diff)

    p_init = sub.add_parser("init", help="create .env.example from an existing .env")
    p_init.add_argument("--env", default=".env", help="source file (default: .env)")
    p_init.add_argument("--output", default=".env.example", help="file to write (default: .env.example)")
    p_init.add_argument(
        "--keep-values",
        action="store_true",
        help="keep non-sensitive values as defaults instead of blanking every value",
    )
    p_init.add_argument("--force", action="store_true", help="overwrite the output file if it exists")

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "check":
            return _cmd_check(args)
        if args.command == "scan":
            return _cmd_scan(args)
        if args.command == "diff":
            return _cmd_diff(args)
        return _cmd_init(args)
    except ParseError as exc:
        print(f"dotguard: parse error: {exc}", file=sys.stderr)
        return EXIT_USAGE
    except FileNotFoundError as exc:
        print(f"dotguard: file not found: {exc.filename}", file=sys.stderr)
        return EXIT_USAGE


def _exit_code(issues: list[Issue], fail_on_warning: bool) -> int:
    if any(i.severity is Severity.ERROR for i in issues):
        return EXIT_PROBLEMS
    if fail_on_warning and issues:
        return EXIT_PROBLEMS
    return EXIT_OK


def _cmd_check(args: argparse.Namespace) -> int:
    issues = check(parse_file(args.env), parse_file(args.example), strict=args.strict)
    render(issues, args.format)
    return _exit_code(issues, args.fail_on_warning)


def _cmd_scan(args: argparse.Namespace) -> int:
    issues: list[Issue] = []
    for path in args.files:
        issues.extend(scan(parse_file(path)))
    render(issues, args.format)
    return _exit_code(issues, args.fail_on_warning)


def _cmd_diff(args: argparse.Namespace) -> int:
    issues = diff(parse_file(args.left), parse_file(args.right), compare_values=args.values)
    render(issues, args.format)
    return _exit_code(issues, args.fail_on_warning)


def _cmd_init(args: argparse.Namespace) -> int:
    if os.path.exists(args.output) and not args.force:
        print(f"dotguard: {args.output} already exists (use --force to overwrite)", file=sys.stderr)
        return EXIT_USAGE

    source = parse_file(args.env)
    with open(args.output, "w", encoding="utf-8") as handle:
        handle.write(render_example(source, keep_values=args.keep_values))
    print(f"wrote {args.output} with {len(source.entries)} key(s) from {args.env}")
    return EXIT_OK


def render_example(source: EnvFile, keep_values: bool = False) -> str:
    """Turn a real .env into a shareable, annotated .env.example."""
    lines = [
        "# Generated by dotguard. Document each key, then commit this file.",
        "# Annotations: @type @required @optional @pattern @values @min @max @secret @deprecated",
        "",
    ]
    for entry in source.entries:
        lines.extend(f"# {text}" for text in entry.doc)
        for name, value in entry.annotations.items():
            lines.append(f"# @{name} {value}".rstrip())

        sensitive = bool(SENSITIVE_NAME.search(entry.key)) or "secret" in entry.annotations
        if sensitive and "secret" not in entry.annotations:
            lines.append("# @secret")
        if "type" not in entry.annotations and entry.value:
            guessed = _guess_type(entry.value)
            if guessed != "string":
                lines.append(f"# @type {guessed}")

        value = entry.value if keep_values and not sensitive else ""
        lines.append(f"{entry.key}={_quote(value)}")
        lines.append("")
    return "\n".join(lines)


def _guess_type(value: str) -> str:
    if value.lower() in {"true", "false", "yes", "no", "on", "off"}:
        return "bool"
    for name in ("port", "int", "float", "url", "email"):
        if VALIDATORS[name](value) is None:
            return name
    return "string"


def _quote(value: str) -> str:
    if value == "" or all(c.isalnum() or c in "-_./:@,+" for c in value):
        return value
    escaped = (
        value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("$", "\\$")
    )
    return f'"{escaped}"'


if __name__ == "__main__":
    sys.exit(main())
