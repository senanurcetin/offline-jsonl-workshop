# AGENTS.md

Instructions for AI coding agents (and humans) working in this repository.

## Project contract
- Offline, dependency-free Python 3.10+ example. Do not add network calls, third-party packages, credentials or paid APIs.
- The validator must never print input records. Keep error messages privacy-safe and keep the input byte limits.

## Commands (run from repository root)
```sh
python -B -m unittest discover -p "test_*.py" -q
python -B verify_release.py
python -B red_green_demo.py
python -B jsonl_utf8_guard.py --input sample_events.jsonl
git diff --check
```

## Rules
- For a behavior defect, add a failing regression test first, then the smallest fix.
- If an allowlisted file changes, regenerate `SHA256SUMS` (full sorted allowlist). Never edit a digest to hide an unexplained failure.
- Use synthetic fixtures only. No private data, tokens or backup files.
- Follow `CONTRIBUTING.md`. Disclose AI assistance in the PR description; report only checks you actually ran.
