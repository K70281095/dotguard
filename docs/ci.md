# Running dotguard in CI and git hooks

The two most useful checks to automate are:

- **`dotguard scan .env.example`** on every push, so a real credential never lands in the
  repository.
- **`dotguard check --strict`** in deployment pipelines, against the environment file that is
  about to be used.

## GitHub Actions (composite action)

```yaml
name: env
on: [push, pull_request]

jobs:
  dotguard:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
      - uses: K70281095/dotguard@v0.1.0
        with:
          command: scan
          args: .env.example
```

Inputs:

| Input | Default | Description |
|---|---|---|
| `command` | `scan` | `check`, `scan` or `init`. |
| `args` | `""` | Extra arguments passed to the command. |
| `python-version` | `3.12` | Python used to run dotguard. |

Output uses the `github` format, so problems show up as annotations on the pull request diff.

## GitHub Actions (manual)

```yaml
- uses: actions/setup-python@v6
  with:
    python-version: "3.12"
- run: pip install git+https://github.com/K70281095/dotguard.git
- run: dotguard check --env .env.ci --strict --format github
```

## GitLab CI

```yaml
dotguard:
  image: python:3.12-slim
  script:
    - pip install git+https://github.com/K70281095/dotguard.git
    - dotguard scan .env.example
```

## pre-commit

```yaml
repos:
  - repo: https://github.com/K70281095/dotguard
    rev: v0.1.0
    hooks:
      - id: dotguard-scan    # scans .env.example (and any *.env.example) when they change
      - id: dotguard-check   # checks .env against .env.example
```

## Plain git hook

Save as `.git/hooks/pre-commit` and make it executable (`chmod +x`):

```sh
#!/bin/sh
exec dotguard scan .env.example
```

## Using the JSON output

```bash
dotguard check --format json | jq '.issues[] | select(.severity == "error") | .key'
```
