# Contributing to Offline JSONL Workshop

This is an independent, MIT-licensed, offline Python 3.10+ educational example, not an Anthropic-owned repository or official Claude event.

## Select useful work

Please examine [open issues](https://github.com/senanurcetin/offline-jsonl-workshop/issues) and [open PRs](https://github.com/senanurcetin/offline-jsonl-workshop/pulls) before coding. Useful contributions improve a reproducible behavior defect, input/ZIP safety, test reliability, cross-platform behavior, accessibility or bilingual accuracy. For ambiguous behavior, propose intended semantics in an issue first. Do not send artificial, duplicate or contribution-count-farming PRs.

## Run the project locally

No external packages, online service, credentials or paid APIs are required.

~~~sh
python -B -m unittest discover -p "test_*.py" -q
python -B verify_release.py
python -B red_green_demo.py
python -B jsonl_utf8_guard.py --input sample_events.jsonl
~~~

On Windows, use py -3 instead of python if needed. The red→green demonstration intentionally fails a regression in a disposable temporary copy and then passes against the real source. Its overall command should exit successfully.

The SHA256SUMS manifest checks **exact bytes** for the project's explicitly listed source files; Git attributes protect these bytes from line-ending conversions. If you change a listed file, update its checksum and preserve the full sorted allowlist. Do not edit a digest merely to hide an unexplained failure. A bundled digest establishes self-consistency, not publisher authenticity. Separately trusted full-ZIP digests are needed to authenticate a downloaded archive.

## Pull request process

1. Describe a verifiable problem, link an issue if applicable and check for overlapping fixes.
2. Create a focused branch from up-to-date main.
3. For a behavior defect, demonstrate a failing regression before changing the implementation.
4. Implement the smallest complete fix; preserve input byte limits, privacy-safe error messages and the offline contract.
5. Regenerate SHA256SUMS if any allowlisted content changes.
6. Run focused and complete tests, source verification and git diff --check. Inspect the diff for credentials, private data and generated files.
7. Open a PR with reproduction, behavior changes, test commands and actual results, compatibility/limitations and any AI assistance.
8. Respond to requested reviews; a submitted PR is not a merged contribution.

## Safety and license

Use synthetic fixtures only. Do not publish private transcripts, users' data, tokens, configuration secrets, backup files, environment directories or unrelated workspace contents. The workshop is educational, not a certified production parser. Report sensitive vulnerabilities using [SECURITY.md](SECURITY.md), not a public proof of exploit.

Contributions are submitted under the project's existing MIT license.

## Türkçe

Gerçek hata düzeltmesi, regresyon testi, güvenlik iyileştirmesi ve anlaşılır teknik dokümantasyon katkıları kabul edilir. Önce açık issue ve PR'ları kontrol edin; aynı düzeltmeyi tekrarlamayın. Python 3.10+ yeterlidir. Tüm testleri çalıştırın, değişen manifest dosyalarının SHA-256 özetlerini doğru yenileyin ve PR açıklamasına test sonuçlarını ekleyin. Gizli anahtarları, gerçek kullanıcı verilerini ve kişisel yedekleri paylaşmayın.
