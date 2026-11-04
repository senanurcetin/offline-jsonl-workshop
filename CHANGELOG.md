# Changelog

All notable changes are documented here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Versions follow [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Documentation
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
