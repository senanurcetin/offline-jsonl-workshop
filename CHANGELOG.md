# Changelog

All notable changes are documented here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Versions follow [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added
- `--max-errors N` for `jsonl_utf8_guard.py --report-all`: lists at most `N` errors instead of 100 (`"truncated": true` still marks a longer list, exit code stays `2`). `N` must be a positive integer, and the option is a usage error without `--report-all` (#63).

## [0.3.0] - 2026-11-20

### Added
- `--report-all` for `jsonl_utf8_guard.py`: keeps scanning past the first invalid line and prints one JSON summary, `{"status": "invalid", "records": N, "errors": [{"line": L, "reason": "..."}], "truncated": false, "max_bytes": ...}`, exit code `2`. At most `MAX_REPORTED_ERRORS` (100) errors are listed and `"truncated": true` marks a longer list; `records` counts valid objects across the whole file. An over-long line is still rejected before decoding and is drained in fixed-size chunks so later lines can be checked. The default single-error behavior, messages and exit codes are unchanged (#33).

### Fixed
- Non-object JSONL records name their JSON type without including input values: `Line N: expected a JSON object, got an array` (also `a string`, `a number`, `true`, `false`, `null`) (#47).
- `--max-bytes` is validated by argparse, so `0` and negative values are a usage error naming the argument (`must be a positive integer, got 0`, exit 2) instead of a `Validation failed:` line that read like bad input. The library check in `iter_jsonl_records` is unchanged for direct callers; a non-number keeps argparse's own message (#41).
- Rejections that already had their own cause now say so instead of the generic `invalid JSON`: a repeated object key reports `Line N: duplicate JSON object key`, and `NaN` / `Infinity` / `-Infinity` report `Line N: non-finite number (NaN or Infinity) is not allowed`. Neither message includes the key or any record content; real parse errors keep `invalid JSON` (#40).

## [0.2.0] - 2026-11-18

### Added
- `--version` flag for `jsonl_utf8_guard.py` and the `jsonl-utf8-guard` console script: prints one line (for example `jsonl_utf8_guard 0.2.0`) and exits 0 without reading stdin or `--input`. The version is a `__version__` constant kept equal to `pyproject.toml` by a unit test; 7 new CLI tests; `SHA256SUMS` regenerated (#8).

### Fixed
- A file starting with a UTF-8 byte order mark is still rejected, but the error now says so (`Line 1: starts with a UTF-8 byte order mark (BOM)`) instead of a generic `invalid JSON` (#31, thanks @P1LOTRX).
- A line containing a bare carriage return (for example a CR-only file) is still rejected, but the error now explains it (`Line N: contains a bare carriage return; use LF or CRLF line endings`) instead of a generic `invalid JSON`. The byte-limit check still runs first (#32, thanks @P1LOTRX).

### Documentation
- `docs/AI_WORKFLOW_TUTORIAL_TR_EN.md`: a 5-minute TR/EN tutorial on the real Claude Code workflow used for #8, linked from the README; `SHA256SUMS` regenerated for the README change (#16).
- README (EN/TR): install from PyPI with `pip install jsonl-utf8-guard`; `SHA256SUMS` regenerated for the README change.

## [0.1.0] - 2026-11-04

### Added
- Packaging as `jsonl-utf8-guard` (`pyproject.toml`, `jsonl-utf8-guard` console script, no runtime dependencies), a CI job that builds the wheel and runs it from a clean venv, and a PyPI Trusted Publishing release workflow (`docs/RELEASING.md`).
- Offline SHA-256 release verification CLI (`verify_release.py`) with ZIP verification without extraction and trusted SHA-256 sidecar support.
- Cross-platform CI (Ubuntu and Windows, Python 3.10/3.12/3.13) and `AGENTS.md` (#6).
- CLI exit-code and privacy tests (#7).
- `docs/AI_ASSISTANCE_LOG.md` recording AI-assisted changes (#11).
- CI `quality` job: ruff, `mypy --strict` and a 75% coverage floor (#21); Actions pinned to commit SHAs with Dependabot updates (#18, #19, #20).
- Seeded boundary and property tests (#22).
- Further seeded edge-case tests for issue #15: every byte limit around multibyte characters, invalid UTF-8 sequences, CR-only and mixed line endings, `\uXXXX` escapes and surrogates, escaped duplicate keys at any depth, and nesting around the recursion limit.

### Fixed
- Byte-exact manifest preserved across Windows checkouts via `.gitattributes`.
- Corrupted DEFLATE and LZMA ZIP streams are handled (#5).
- Deeply nested JSON no longer crashes the validator with an uncaught `RecursionError`; it is reported as a validation error (exit 2) (#12).

### Changed
- Removed accidentally committed `__pycache__/*.pyc` files and added `.gitignore` (#21).

### Documentation
- Bilingual (TR/EN) JSONL UTF-8 validation workshop, runbook, contributor onboarding (#4) and security policy.
