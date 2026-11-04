# Changelog

All notable changes are documented here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). No GitHub Release has been published yet; entries are under "Unreleased" until a version is tagged.

## [Unreleased]

### Added
- Offline SHA-256 release verification CLI (`verify_release.py`) with ZIP verification without extraction and trusted SHA-256 sidecar support.
- Cross-platform CI (Ubuntu and Windows, Python 3.10/3.12/3.13) and `AGENTS.md` (#6).
- CLI exit-code and privacy tests (#7).
- `docs/AI_ASSISTANCE_LOG.md` recording AI-assisted changes (#11).

### Fixed
- Byte-exact manifest preserved across Windows checkouts via `.gitattributes`.
- Corrupted DEFLATE and LZMA ZIP streams are handled (#5).
- Deeply nested JSON no longer crashes the validator with an uncaught `RecursionError`; it is reported as a validation error (exit 2) (#12).

### Documentation
- Bilingual (TR/EN) JSONL UTF-8 validation workshop, runbook, contributor onboarding (#4) and security policy.
