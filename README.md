# dotguard

**Validate `.env` files against a documented `.env.example`, and keep real secrets out of git.**

[![CI](https://github.com/K70281095/dotguard/actions/workflows/ci.yml/badge.svg)](https://github.com/K70281095/dotguard/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.9%20%E2%80%93%203.13-blue)
![Dependencies](https://img.shields.io/badge/dependencies-0-brightgreen)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

Almost every project has a `.env.example` that says which environment variables the app needs.
Almost every project also has that file drift out of date: a new variable gets added to the code
but not to the example, someone sets `PORT=80O0`, or a real API key slips into the example and
gets committed.

`dotguard` turns `.env.example` into a lightweight, human-readable **schema** and checks your
real `.env` against it, locally, in a pre-commit hook or in CI.

```console
$ dotguard check --env examples/.env --example examples/.env.example
examples/.env:3  error DG004  PORT=80O0: expected a port number between 1 and 65535
examples/.env:4  error DG007  APP_ENV=prod is not one of: development, staging, production
examples/.env:6  error DG006  WORKERS=64 is above the @max of 32
examples/.env:7  error DG004  BASE_URL=localhost:8080: expected a URL with a scheme and host, e.g. https://example.com
examples/.env  error DG001  DATABASE_URL is missing (documented in examples/.env.example:32)
examples/.env:8  error DG003  PAYMENTS_API_TOKEN is required but empty
examples/.env:10  warning DG008  VERBOSE is deprecated: use LOG_LEVEL=debug instead
examples/.env:11  warning DG002  OLD_FEATURE_FLAG is not documented in examples/.env.example

6 error(s), 2 warning(s)
```

---

## Table of contents

- [Why dotguard?](#why-dotguard)
- [Install](#install)
- [Quick start](#quick-start)
- [Annotating `.env.example`](#annotating-envexample)
- [Commands](#commands)
- [Output formats and exit codes](#output-formats-and-exit-codes)
- [Using dotguard in CI](#using-dotguard-in-ci)
- [Using it from Python](#using-it-from-python)
- [`.env` syntax supported](#env-syntax-supported)
- [Roadmap](#roadmap)
- [Contributing](#contributing)
- [License](#license)

## Why dotguard?

| | |
|---|---|
| **Zero dependencies** | Pure Python standard library. Nothing to audit, nothing to break. |
| **No new config file** | The schema lives as comments in the `.env.example` you already have. |
| **Catches real mistakes** | Missing keys, typos, wrong types, values outside an allowed list or range. |
| **Secret scanning** | Flags real-looking AWS, GitHub, Slack, Stripe, Google and OpenAI-style keys, private keys and JWTs in files you commit. |
| **Never leaks values** | Keys marked `@secret` are printed as `****` in every message and CI log. |
| **CI-friendly** | Stable rule codes, JSON output, GitHub Actions annotations, clear exit codes. |

## Install

```bash
pip install git+https://github.com/K70281095/dotguard.git
```

Or run it from a clone without installing:

```bash
git clone https://github.com/K70281095/dotguard.git
cd dotguard
PYTHONPATH=src python3 -m dotguard --help
```

Requires Python 3.9 or newer.

## Quick start

1. **Already have a `.env` but no example?** Generate one. Sensitive-looking keys get `@secret`
   and every value is blanked, so the result is safe to commit:

   ```bash
   dotguard init            # writes .env.example from .env
   dotguard init --keep-values   # keep non-secret values as defaults
   ```

2. **Document the rules** by adding annotation comments (see below).

3. **Check your environment**:

   ```bash
   dotguard check
   ```

4. **Make sure nobody commits a real secret** in the example:

   ```bash
   dotguard scan .env.example
   ```

A full, working example lives in [`examples/`](examples/).

## Annotating `.env.example`

Write annotations as comments directly above a key. Ordinary comments become the key's
documentation. A blank line ends the block.

```bash
# Port the HTTP server listens on.
# @type port
# @required
PORT=8080

# Which deployment this is.
# @values development, staging, production
APP_ENV=development

# Number of background workers.
# @type int
# @min 1
# @max 32
WORKERS=4

# Postgres connection string.
# @type url
# @secret
DATABASE_URL=

# Sentry DSN. Leave empty to disable error reporting.
# @optional
SENTRY_DSN=

# @deprecated use LOG_LEVEL instead
# @optional
VERBOSE=
```

| Annotation | Meaning |
|---|---|
| `@type T` | Value must be of type `T`: `string` (default), `int`, `float`, `bool`, `port`, `url`, `email`. |
| `@required` | Value must not be empty. |
| `@optional` | Key may be absent from `.env`. Without it, every documented key must be present. |
| `@pattern REGEX` | Value must fully match the Python regular expression. |
| `@values a, b, c` | Value must be one of the listed choices. |
| `@min N` / `@max N` | Inclusive bounds for numeric types. |
| `@secret` | Never print the value; also makes `scan` treat the key as sensitive. |
| `@deprecated [reason]` | Warn when the key is still set. |

Full reference: [docs/annotations.md](docs/annotations.md). Every rule code (`DG001`…) is
explained in [docs/rules.md](docs/rules.md).

## Commands

### `dotguard check`

```
dotguard check [--env .env] [--example .env.example] [--strict]
               [--format text|json|github] [--fail-on-warning]
```

Checks every key documented in the example against the env file. With `--strict`, keys that
exist in `.env` but not in the example are errors instead of warnings, which helps keep the
example complete.

### `dotguard scan`

```
dotguard scan [FILES ...] [--format text|json|github] [--fail-on-warning]
```

Scans files you intend to commit (default: `.env.example`) for:

- **DS001 (error):** well-known credential formats (AWS, GitHub, Slack, Stripe live keys,
  Google API keys, OpenAI-style keys, PEM private keys, JWTs).
- **DS002 (warning):** long, high-entropy values under sensitive-looking names
  (`*_TOKEN`, `*_SECRET`, `*PASSWORD*`, `*API_KEY*`, …) or keys marked `@secret`.

Obvious placeholders such as `changeme`, `<your-token>`, `xxxx` and `${VAR}` are ignored.

### `dotguard init`

```
dotguard init [--env .env] [--output .env.example] [--keep-values] [--force]
```

Creates a starter `.env.example` from an existing `.env`, guessing `@type` for ports, numbers,
booleans, URLs and emails and marking sensitive keys `@secret`. Secret values are never copied,
even with `--keep-values`. It refuses to overwrite an existing file unless you pass `--force`.

## Output formats and exit codes

| `--format` | Use it for |
|---|---|
| `text` (default) | People. Colored when writing to a terminal; respects `NO_COLOR` and `FORCE_COLOR`. |
| `json` | Other tools. `{"issues": [...], "summary": {"errors": N, "warnings": N}}` |
| `github` | GitHub Actions. Issues appear as inline annotations on the pull request. |

| Exit code | Meaning |
|---|---|
| `0` | No errors (warnings allowed unless `--fail-on-warning`). |
| `1` | Problems found. |
| `2` | Usage error: a file is missing or cannot be parsed. |

## Using dotguard in CI

### GitHub Actions

This repository is also a composite action:

```yaml
- uses: actions/checkout@v4
- uses: K70281095/dotguard@v0.1.0
  with:
    command: scan
    args: .env.example
```

Or install and run it yourself:

```yaml
- uses: actions/setup-python@v5
  with:
    python-version: "3.12"
- run: pip install git+https://github.com/K70281095/dotguard.git
- run: dotguard scan .env.example --format github
```

### pre-commit

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/K70281095/dotguard
    rev: v0.1.0
    hooks:
      - id: dotguard-scan
```

More recipes, including GitLab CI and a plain git hook: [docs/ci.md](docs/ci.md).

## Using it from Python

```python
import dotguard

env = dotguard.parse_file(".env")
example = dotguard.parse_file(".env.example")

for issue in dotguard.check(env, example, strict=True):
    print(issue.code, issue.severity.value, issue.message)

for issue in dotguard.scan(example):
    print("possible secret:", issue.key)
```

## `.env` syntax supported

```bash
# comments on their own line
KEY=value
export KEY=value                # "export" prefix is allowed
KEY=value # trailing comment    # needs whitespace before "#"
URL=https://example.com/#anchor # "#" inside a value is kept
KEY="double \"quoted\"\nwith escapes"   # \n \t \r \" \\ \$
KEY='single quoted, taken literally'
EMPTY=
```

Duplicate keys and malformed lines are reported with their file and line number.

## Roadmap

- [ ] `${VAR}` interpolation when checking values
- [ ] Multi-line double-quoted values
- [ ] Publish to PyPI
- [ ] `dotguard diff` to compare two environments (e.g. staging vs production keys)
- [ ] Optional JSON Schema export

Ideas and pull requests are welcome. See the [issues](https://github.com/K70281095/dotguard/issues).

## Contributing

Contributions of every size are welcome: bug reports, docs fixes, new secret patterns, new
`@type`s. Please read [CONTRIBUTING.md](CONTRIBUTING.md) and our
[Code of Conduct](CODE_OF_CONDUCT.md). To report a vulnerability, see [SECURITY.md](SECURITY.md).

## License

[MIT](LICENSE) © 2026 Kanhaiya Kumar
