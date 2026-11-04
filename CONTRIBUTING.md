# Contributing to dotguard

Thanks for taking the time to contribute! This guide explains how to get set up and what we
look for in a pull request.

## Ways to help

- **Report a bug.** Open an issue with the smallest `.env` / `.env.example` pair that shows it.
  Please replace any real values with placeholders first.
- **Suggest a feature.** Open an issue describing the problem before writing code, so we can
  agree on the approach.
- **Improve the docs.** Typos, unclear wording and missing examples are all worth fixing.
- **Add a secret pattern.** New entries in `KNOWN_TOKENS` (`src/dotguard/secrets.py`) are very
  welcome. Include a link to the provider's documentation of the format and a test that builds
  the fake token from pieces (see `tests/test_secrets.py`) so the repository never contains
  something that looks like a real credential.
- **Look for `good first issue`** labels if you are new to the project.

## Development setup

dotguard has no runtime dependencies, so a plain Python 3.9+ install is enough.

```bash
git clone https://github.com/K70281095/dotguard.git
cd dotguard
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

Run the tests:

```bash
python -m unittest discover -s tests -v
```

Run the linter:

```bash
ruff check .
ruff format --check .
```

Try your change on the bundled example:

```bash
dotguard check --env examples/.env --example examples/.env.example
```

## Pull request checklist

- [ ] One logical change per pull request.
- [ ] Tests added or updated for the behaviour you changed.
- [ ] `python -m unittest discover -s tests` passes.
- [ ] `ruff check .` passes.
- [ ] User-facing changes are described in `CHANGELOG.md` under **Unreleased**.
- [ ] New rule codes are documented in `docs/rules.md`; new annotations in `docs/annotations.md`.

## Design principles

1. **No runtime dependencies.** Anything that needs a third-party package belongs behind an
   optional extra, if at all.
2. **Never print a secret.** Messages must go through `_preview()` (or equivalent) for any key
   that may be sensitive.
3. **Stable rule codes.** A code such as `DG004` keeps its meaning forever, because people
   filter on it in CI. Add a new code rather than changing an old one.
4. **Readable `.env.example`.** Annotations should stay short and obvious to someone who has
   never heard of dotguard.

## Commit messages

Use the imperative mood and keep the first line under ~70 characters, for example
`Add @type uuid` or `Fix inline comment parsing after quoted values`.

## Releasing (maintainers)

Releases are published to PyPI as **`dotguard-cli`** (the name `dotguard` was already taken
there; the command and the import name are still `dotguard`).

1. Move the **Unreleased** entries in `CHANGELOG.md` under a new version heading.
2. Bump `version` in `pyproject.toml` and `__version__` in `src/dotguard/__init__.py`.
3. Commit and push, then create a GitHub release whose tag is `v` + that version, e.g. `v0.2.0`.
4. The **Release** workflow checks the tag, builds the package and uploads it to PyPI.

One-time PyPI setup (trusted publishing, no API token needed):

1. Sign in at [pypi.org](https://pypi.org) and open **Your projects → Publishing → Add a new
   pending publisher**.
2. Fill in: PyPI project name `dotguard-cli`, owner `K70281095`, repository `dotguard`,
   workflow `release.yml`, environment `pypi`.
3. On GitHub, create the environment under **Settings → Environments → New environment →
   `pypi`**.

By contributing, you agree that your contributions are licensed under the [MIT License](LICENSE)
and that you will follow the [Code of Conduct](CODE_OF_CONDUCT.md).
