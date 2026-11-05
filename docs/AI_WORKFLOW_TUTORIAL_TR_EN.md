# 5-minute AI-assisted change workflow — bilingual tutorial

**Status: this describes one real change, issue [#8](https://github.com/senanurcetin/offline-jsonl-workshop/issues/8) (`--version` flag), implemented in PR [#28](https://github.com/senanurcetin/offline-jsonl-workshop/pull/28).**
The AI tool was **Claude Code (Anthropic, model Claude Opus 5.5)** in a local Claude Code desktop session. Issue #8 originally asked for OpenAI Codex. The repository owner chose Claude Code instead, so **Codex was not used**. Commands and outputs below are real, shortened, from Windows 11 with Python 3.11.9.

## Türkçe

### 1. Kurallar: `AGENTS.md` (≈30 sn)

Ajan işe başlamadan önce [`AGENTS.md`](../AGENTS.md) ve [`CONTRIBUTING.md`](../CONTRIBUTING.md) dosyalarını okur. Bu dosyalar şunları söyler: çevrimdışı kal, girdi kayıtlarını asla yazdırma, önce test yaz, izinli listedeki bir dosya değişirse `SHA256SUMS` dosyasını yenile, yalnızca gerçekten çalıştırdığın kontrolleri raporla ve AI yardımını PR'da açıkla.

### 2. Görev istemi (özet) (≈30 sn)

> #8'i AGENTS.md ve CONTRIBUTING.md'ye uyarak uygula. `--version` bir satır yazsın ve girdi okumadan 0 ile çıksın. Önce CLI testlerini yaz, `SHA256SUMS`'u yenile, CHANGELOG ve AI yardım günlüğünü güncelle, AGENTS.md'deki tüm kontrolleri çalıştır, PR aç, birleştirme yapma.

### 3. Önce test: kırmızı (≈1 dk)

`CLIExitCodeTests` sınıfına 7 test eklendi: tek satır çıktı, 0 çıkış kodu, `pyproject.toml` ile aynı sürüm, stdin yokken veya kapalıyken çalışma, girdiyi okumama ve yankılamama, `--input` dosyasını açmama. Kod değişmeden önce:

~~~text
$ python -B -m unittest test_jsonl_utf8_guard.CLIExitCodeTests -q
jsonl_utf8_guard.py: error: unrecognized arguments: --version
Ran 13 tests ... FAILED (failures=7, errors=1)
~~~

### 4. En küçük değişiklik: yeşil (≈1 dk)

`jsonl_utf8_guard.py` dosyasına bir `__version__ = "0.1.0"` sabiti ve argparse `action="version"` eklendi. Argparse sürümü argümanları ayrıştırırken yazdırır, yani stdin veya dosya açılmadan önce. Bu yüzden çıktıda bir kayıt bulunamaz.

~~~text
$ python -B -m unittest test_jsonl_utf8_guard.CLIExitCodeTests -q
Ran 13 tests ... OK
$ python -B jsonl_utf8_guard.py --version
jsonl_utf8_guard 0.1.0
~~~

### 5. `SHA256SUMS` ve `verify_release.py` (≈1 dk)

Doğrulayıcı eski özeti hemen yakaladı. Tam ve sıralı izinli liste yeniden üretildi. Yalnızca değişen iki dosyanın özeti değişti.

~~~text
$ python -B verify_release.py
Verification failed: Source checksum mismatch: jsonl_utf8_guard.py
$ python -B verify_release.py        # SHA256SUMS yenilendikten sonra
{"files": 11, "manifest": "SHA256SUMS", "status": "ok"}
~~~

### 6. Tüm kontroller (≈30 sn)

~~~text
unittest discover      -> Ran 89 tests ... OK (skipped=2)
red_green_demo.py      -> {"red": "expected regression failure", "green": "regression test passed", ...}
sample validation      -> {"status": "ok", "records": 2, "max_bytes": 65536}
ruff check .           -> All checks passed!
coverage report        -> TOTAL 78% (floor 75%)
git diff --check       -> CRLF satırlarında "trailing whitespace"
~~~

`git diff --check` uyarısı gerçek bir boşluk hatası değildir. `.gitattributes` içindeki `-text` CRLF baytlarını korur (#22 ve #24'te de aynı). `git -c core.whitespace=cr-at-eol diff --check` temiz çıkar. `mypy` yerelde kurulu değildi, bu yüzden CI'daki `quality` işine bırakıldı.

### 7. AI yardım bölümüyle PR (≈30 sn)

PR [#28](https://github.com/senanurcetin/offline-jsonl-workshop/pull/28) depo şablonunu kullanır. `Closes #8` içerir. Kırmızı ve yeşil çıktılarını, kontrolleri ve "AI assistance" bölümünü gösterir: araç Claude Code (Claude Opus 5.5), yerel oturum (paylaşılabilir bağlantı yok), istem özeti, Codex kullanılmadığı bilgisi ve insan incelemesi gerektiği notu. [`docs/AI_ASSISTANCE_LOG.md`](AI_ASSISTANCE_LOG.md) dosyasına bir satır eklendi. Barındırılan CI, PR #28 üzerinde 8 işin tamamını geçti (Ubuntu/Windows × Python 3.10/3.12/3.13 testleri, `mypy --strict` dahil `quality` ve `package`). PR birleştirilmedi; birleştirme kararı depo sahibine aittir.

## English

### 1. Rules: `AGENTS.md` (≈30 s)

Before it starts, the agent reads [`AGENTS.md`](../AGENTS.md) and [`CONTRIBUTING.md`](../CONTRIBUTING.md). They say: stay offline, never print input records, write the test first, regenerate `SHA256SUMS` when an allowlisted file changes, report only checks you actually ran, and disclose AI assistance in the PR.

### 2. Task prompt (summary) (≈30 s)

> Implement #8 following AGENTS.md and CONTRIBUTING.md. `--version` prints one line and exits 0 without reading input. Write the CLI tests first, regenerate `SHA256SUMS`, update CHANGELOG and the AI assistance log, run every check in AGENTS.md, open a PR, do not merge.

### 3. Test first: red (≈1 min)

Seven tests were added to `CLIExitCodeTests`. They check for one line of output, exit 0, the same version as `pyproject.toml`, that it works with no stdin or a closed stdin, that it never reads or echoes input, and that it doesn't open `--input`. Before the code change:

~~~text
$ python -B -m unittest test_jsonl_utf8_guard.CLIExitCodeTests -q
jsonl_utf8_guard.py: error: unrecognized arguments: --version
Ran 13 tests ... FAILED (failures=7, errors=1)
~~~

### 4. Smallest change: green (≈1 min)

A `__version__ = "0.1.0"` constant and an argparse `action="version"` were added to `jsonl_utf8_guard.py`. Argparse prints the version while it parses the arguments, before stdin or a file is opened. So the output cannot contain a record.

~~~text
$ python -B -m unittest test_jsonl_utf8_guard.CLIExitCodeTests -q
Ran 13 tests ... OK
$ python -B jsonl_utf8_guard.py --version
jsonl_utf8_guard 0.1.0
~~~

### 5. `SHA256SUMS` and `verify_release.py` (≈1 min)

The verifier caught the stale digest at once. The full sorted allowlist was regenerated. Only the digests of the two changed files changed.

~~~text
$ python -B verify_release.py
Verification failed: Source checksum mismatch: jsonl_utf8_guard.py
$ python -B verify_release.py        # after regenerating SHA256SUMS
{"files": 11, "manifest": "SHA256SUMS", "status": "ok"}
~~~

### 6. All checks (≈30 s)

~~~text
unittest discover      -> Ran 89 tests ... OK (skipped=2)
red_green_demo.py      -> {"red": "expected regression failure", "green": "regression test passed", ...}
sample validation      -> {"status": "ok", "records": 2, "max_bytes": 65536}
ruff check .           -> All checks passed!
coverage report        -> TOTAL 78% (floor 75%)
git diff --check       -> "trailing whitespace" on CRLF lines
~~~

The `git diff --check` warning isn't a real whitespace error. `-text` in `.gitattributes` keeps the CRLF bytes (the same as in #22 and #24). `git -c core.whitespace=cr-at-eol diff --check` is clean. `mypy` wasn't installed locally, so it was left to the CI `quality` job.

### 7. PR with an AI-assistance section (≈30 s)

PR [#28](https://github.com/senanurcetin/offline-jsonl-workshop/pull/28) uses the repository template. It contains `Closes #8`. It shows the red and green output, the checks, and an "AI assistance" section: the tool was Claude Code (Claude Opus 5.5), the session was local (no shareable link), a summary of the prompt, a note that Codex was not used, and a note that a human should review it. A row was added to [`docs/AI_ASSISTANCE_LOG.md`](AI_ASSISTANCE_LOG.md). Hosted CI passed all 8 jobs on PR #28: the Ubuntu/Windows × Python 3.10/3.12/3.13 tests, `quality` (including `mypy --strict`) and `package`. The PR was not merged; that decision belongs to the repository owner.

## Integrity checklist

- Describe only what was actually done; name the tool that was actually used.
- Report only checks you ran; keep hosted CI results separate from local results.
- Do not claim an event, attendance or an official partnership.
