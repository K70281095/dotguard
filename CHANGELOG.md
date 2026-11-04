# Changelog

All notable changes to this project are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project
uses [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [0.2.0] - 2026-11-04

### Added

- Published to PyPI as `dotguard-cli`, with a release workflow using trusted publishing.
- `dotguard diff`: compare the keys (and, with `--values`, the values) of two env files.
- Quoted values can span several lines.
- `$NAME`, `${NAME}`, `${NAME:-default}` and `${NAME-default}` references to keys defined earlier
  in the same file, with a new `DG011` warning for references that cannot be resolved.

### Fixed

- `dotguard init --keep-values` now escapes `$` so values survive a round trip.

## [0.1.0] - 2026-11-04

### Added

- `dotguard check`: validate a `.env` file against an annotated `.env.example`.
- Annotations: `@type`, `@required`, `@optional`, `@pattern`, `@values`, `@min`, `@max`,
  `@secret`, `@deprecated`.
- Types: `string`, `int`, `float`, `bool`, `port`, `url`, `email`.
- `dotguard scan`: detect well-known credential formats and high-entropy secrets.
- `dotguard init`: generate a safe `.env.example` from an existing `.env`.
- Output formats: `text`, `json` and `github` (Actions annotations).
- Composite GitHub Action and pre-commit hooks.

[Unreleased]: https://github.com/K70281095/dotguard/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/K70281095/dotguard/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/K70281095/dotguard/releases/tag/v0.1.0
