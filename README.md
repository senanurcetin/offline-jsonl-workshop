# Red → Green: UTF-8 JSONL Validation Workshop

[![CI](https://github.com/senanurcetin/offline-jsonl-workshop/actions/workflows/ci.yml/badge.svg)](https://github.com/senanurcetin/offline-jsonl-workshop/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/jsonl-utf8-guard.svg)](https://pypi.org/project/jsonl-utf8-guard/)
![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

A small, dependency-free, offline Python workshop that shows why a byte limit must count UTF-8 bytes rather than Unicode characters, using a strict JSONL validator and an automated red → green regression demo. Türkçe özet [aşağıda](#türkçe).

## At a glance

- 🚀 is **1** Unicode character but **4** UTF-8 bytes; a limit declared in bytes must check the latter.
- `jsonl_utf8_guard.py` reads JSONL with a bounded buffer, validates UTF-8 strictly, rejects duplicate object keys (including nested and Unicode-escaped ones) and prints **only the number of JSON objects**, never input records.
- `red_green_demo.py` proves the regression test catches the bug: it fails on a deliberately broken copy and passes on the real code.
- `verify_release.py` checks every source file, or a ZIP without extracting it, against `SHA256SUMS`.
- Python 3.10+ only: no network, packages, cloud services, API keys or credentials.

## Quick start

From PyPI:

~~~sh
pip install jsonl-utf8-guard
jsonl-utf8-guard --input sample_events.jsonl
~~~

From a clone, with nothing installed:

~~~powershell
py -3 jsonl_utf8_guard.py --input sample_events.jsonl
py -3 -m unittest discover -p "test_*.py" -v
py -3 red_green_demo.py
py -3 verify_release.py
~~~

## Details

### Red → green demo

`red_green_demo.py` creates an intentionally buggy copy in a temporary directory, confirms that the targeted regression test fails there, then reruns the same test against the corrected code. It checks with SHA-256 that the working source was never modified. You can also compare the two implementations by hand in a disposable copy.

### Verifying the files

`py -3 verify_release.py` validates every expected file against `SHA256SUMS`. It rejects malformed, duplicate, unexpected or path-traversal manifest entries, detects changed or missing files, and never prints file contents. `.gitattributes` keeps the manifest-verified bytes identical on Windows, macOS and Linux.

A workshop ZIP can be checked **without extraction**:

~~~powershell
py -3 verify_release.py --archive "path\to\offline-jsonl-workshop.zip"
~~~

This checks the exact expected members, rejects duplicate, unsafe, symlinked, encrypted, oversized or missing entries, and verifies source bytes against the bundled `SHA256SUMS` without running archive contents.

To authenticate a download, also check the full ZIP hash obtained from a trusted independent channel, either directly or from a sidecar file:

~~~powershell
py -3 verify_release.py --archive "path\to\offline-jsonl-workshop.zip" --expected-archive-sha256 "<trusted_64_character_lowercase_sha256>"
py -3 verify_release.py --archive "offline-jsonl-workshop.zip" --trusted-sha256-file "offline-jsonl-workshop.zip.sha256"
~~~

The tool hashes the exact bytes it then parses and rejects malformed or mismatched hashes; `--archive` is required. The sidecar must hold a single LF- or CRLF-terminated record in the format `<64 lowercase hex digits>  workshop.zip` with a matching ZIP filename; oversized, malformed or symlinked sidecars are rejected. The two options cannot be combined.

### Offline package

A separate release builder in the original development workspace (`prepare_workshop_release.py`, not needed to use the archive) packages the workshop from an explicit allowlist: this README, the bilingual runbook ([`WORKSHOP_RUNBOOK_TR_EN.md`](WORKSHOP_RUNBOOK_TR_EN.md)), the sample, the license, three scripts, three test modules and `SHA256SUMS`, without backups, credentials or local handoff files. Rebuilding from the same source bytes gives the same ZIP hash, and a SHA-256 sidecar is written beside the ZIP. After extracting it into its own directory:

~~~powershell
py -3 -m unittest discover -p "test_*.py" -q
py -3 verify_release.py
py -3 red_green_demo.py
py -3 jsonl_utf8_guard.py --input sample_events.jsonl
~~~

### AI-assisted workflow

A [5-minute tutorial (TR/EN)](https://github.com/senanurcetin/offline-jsonl-workshop/blob/main/docs/AI_WORKFLOW_TUTORIAL_TR_EN.md) walks through the Claude Code workflow used for the `--version` flag (#8): `AGENTS.md` rules, test first, `SHA256SUMS` update and a PR with an AI-assistance section.

## Limitations

- **Educational, not a production parser.** It does no network requests, never executes or logs input JSON, and never modifies input, but it is not a general-purpose JSON library.
- **Integrity is not authenticity.** The bundled `SHA256SUMS` proves only that a ZIP is self-consistent; an attacker who replaces the files and the manifest gets another consistent ZIP. A hash or sidecar downloaded from the same untrusted location proves nothing about the publisher, and no release signature or trusted checksum channel is provided.
- **No published workshop ZIP.** The offline package is built locally; it is not attached to a GitHub release.
- **Independent material.** This is not an official Anthropic product, partnership, certification or Anthropic-maintained repository, and no workshop, attendance, sponsorship or program acceptance is claimed.

## Türkçe

Bayt sınırının neden Unicode karakter sayısıyla değil UTF-8 bayt sayısıyla kontrol edilmesi gerektiğini gösteren, bağımlılıksız ve çevrimdışı bir Python atölyesi.

- 🚀 emojisi 1 Unicode karakteridir ama UTF-8 ile 4 bayt yer kaplar. Boyut sınırı bayt cinsinden ilan edildiyse gerçek bayt sayısı kontrol edilmelidir.
- Doğrulayıcı UTF-8'i katı biçimde denetler, iç içe ve Unicode escape ile yazılmış olanlar dahil **tekrarlanan anahtarları** reddeder (böylece son değer öncekinin üzerine sessizce yazılmaz) ve yalnızca nesne sayısını yazdırır; dosya içeriğini veya hassas anahtar adlarını paylaşmaz.
- `red_green_demo.py` hatalı sürümü geçici bir dizinde oluşturur, regresyon testinin orada **başarısız**, doğru kodda **başarılı** olduğunu otomatik doğrular ve kaynak dosyanın değişmediğini SHA-256 ile kontrol eder.
- Gereksinimler: Python 3.10+; hesap, bulut, API anahtarı veya ek paket gerekmez.

Kurulum ve çalıştırma:

~~~sh
pip install jsonl-utf8-guard
jsonl-utf8-guard --input sample_events.jsonl
~~~

Ya da hiçbir şey kurmadan klonlanmış depodan:

~~~powershell
py -3 jsonl_utf8_guard.py --input sample_events.jsonl
py -3 -m unittest discover -p "test_*.py" -v
py -3 red_green_demo.py
~~~

**Dosyaları doğrulama.** Depoyu klonladıktan veya ZIP paketini çıkardıktan sonra `py -3 verify_release.py` çalıştırın. Araç tüm kaynak dosyalarını `SHA256SUMS` ile karşılaştırır; değiştirilmiş veya eksik dosyaları, hatalı veya yinelenmiş manifest kayıtlarını ve klasör dışına erişim girişimlerini reddeder. ZIP'i açmadan kontrol etmek için `--archive "path\to\offline-jsonl-workshop.zip"` kullanın; yinelenen, eksik, güvensiz, sembolik bağlantılı ve aşırı büyük kayıtlar reddedilir, ZIP içindeki kod çalıştırılmaz. ZIP'in tam SHA-256 değerini bağımsız ve güvenilir bir kaynaktan aldıysanız `--expected-archive-sha256 "<guvenilir_64_karakter_kucuk_harf_sha256>"` veya `--trusted-sha256-file` ile ayrıca kontrol edin; yan dosya Windows CRLF ve Linux LF satır sonlarını destekler.

**Sınırlamalar.** Örnek eğitim amaçlıdır, genel bir üretim ayrıştırıcısı değildir. Paket içindeki `SHA256SUMS` yalnızca iç tutarlılığı gösterir, yayıncının kimliğini kanıtlamaz; ZIP ile aynı güvenilmeyen kaynaktan gelen hash veya yan dosya da kanıtlamaz. Atölye bağımsız olarak hazırlanmıştır; gerçek etkinlik, katılımcı, sponsorluk veya program kabulü iddiası yoktur.

AI destekli iş akışı: [5 dakikalık öğretici (TR/EN)](https://github.com/senanurcetin/offline-jsonl-workshop/blob/main/docs/AI_WORKFLOW_TUTORIAL_TR_EN.md), `--version` seçeneği (#8) için kullanılan Claude Code iş akışını anlatır: `AGENTS.md` kuralları, önce test, `SHA256SUMS` güncellemesi ve AI yardım bölümlü PR.

## License

[MIT](LICENSE)
