# AI assistance log

Only real, verifiable entries. Each row names the tool actually used. An empty tool column means no AI tool was used for that change.

| Date | Tool | Task | PR | Verified result |
| --- | --- | --- | --- | --- |
| 2026-11-04 | Claude Code | Add cross-platform CI workflow and `AGENTS.md` | [#6](https://github.com/senanurcetin/offline-jsonl-workshop/pull/6) | 62 tests, release verifier and red-green demo pass; 6 CI jobs (Ubuntu/Windows, Python 3.10/3.12/3.13) green |
| 2026-11-04 | Claude Code | Add 5 CLI exit-code and privacy tests | [#7](https://github.com/senanurcetin/offline-jsonl-workshop/pull/7) | 67 tests pass; `SHA256SUMS` regenerated; 6 CI jobs green |
| 2026-11-04 | Claude Code | Add this log | [#11](https://github.com/senanurcetin/offline-jsonl-workshop/pull/11) | Documentation only; 67 tests and 6 CI jobs green |
| 2026-11-04 | Claude Code | Found and fixed uncaught RecursionError on deeply nested JSON (red-green) | [#12](https://github.com/senanurcetin/offline-jsonl-workshop/pull/12) | Regression tests failed before and pass after; 69 tests; 6 CI jobs green |

## How to add an entry

1. Add a row in the same PR as the change. Use the tool you actually used (for example Codex or Claude Code).
2. State the measurable result (tests added, defect found, check outcomes) and what a human reviewed.
3. Do not log events, attendance or usage that did not happen.
