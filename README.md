# Red → Green: UTF-8 JSONL Validation Workshop

A small original, dependency-free, offline Python example showing how Unicode characters differ from UTF-8 bytes. Intended as a potential hands-on Claude Code / open-source community workshop. **No workshop or attendance is claimed to have taken place.**

## English

Requirements: Python 3.10+; no cloud, API keys, paid services, or extra packages.

Run from this directory:

~~~powershell
py -3 jsonl_utf8_guard.py --input sample_events.jsonl
py -3 -m unittest discover -p "test_*.py" -v
py -3 red_green_demo.py
~~~

For a minimal reproducer, compare the character count of the rocket emoji (1) with its UTF-8 byte length (4). A limit expressed in bytes must check the latter. This verifier reads JSONL with a bounded buffer, validates UTF-8 strictly, **rejects ambiguous duplicate object keys (including nested and Unicode-escaped duplicates)**, and emits **only the number of JSON objects**. It does not print any input records.

The `red_green_demo.py` command automatically creates an intentionally buggy copy in a temporary directory, confirms that the targeted regression test fails there, and reruns the same test against the original corrected code. It verifies that the working source was never modified. You can also inspect the two implementations manually in a disposable copy.

Security and scope: No network requests, code execution of user JSON, original-content logging, input modification, or credentials. The example is educational, not a general production parser.

## Türkçe

Gereksinimler: Python 3.10+; hesap, bulut, API anahtarı veya ek paket gerekmez.

~~~powershell
py -3 jsonl_utf8_guard.py --input sample_events.jsonl
py -3 -m unittest discover -p "test_*.py" -v
py -3 red_green_demo.py
~~~

Temel problem: 🚀 emojisi 1 Unicode karakteri olmasına rağmen UTF-8 ile 4 bayt yer kaplar. Eğer bir akış işleyici boyut sınırını bayt cinsinden ilan ediyorsa karakter sayısını değil gerçek bayt sayısını kontrol etmelidir.

`red_green_demo.py` hatalı sürümü geçici bir dizinde oluşturur; regresyon testinin burada **beklenen şekilde başarısız** olduğunu ve orijinal, doğru kodda **başarılı** olduğunu otomatik doğrular. Kaynak dosyanın değiştirilmediğini de SHA-256 ile kontrol eder. Doğrulayıcı JSON nesnelerindeki **tekrarlanan anahtarları**, iç içe ve Unicode escape ile yazılmış olanlar dahil, reddeder; böylece son değerin sessizce öncekinin üzerine yazılması önlenir. Örnek yerel çalışır, dışarı veri göndermez ve dosya içeriğini veya hassas anahtar adlarını çıktıda paylaşmaz.

**Durum:** Atölye içeriği geliştirilmiştir. Gerçek etkinlik, katılımcı, sponsorluk veya program kabulü iddiası yoktur.


## Standalone public-source package (prepared; not published)

This workshop is independently authored example material, **not** an official Anthropic product, partnership, certification, or an Anthropic-maintained repository. The source is provided under the MIT license in `LICENSE`. No workshop has been hosted.

The original development workspace contains a separate release builder (`prepare_workshop_release.py`) that packages this workshop reproducibly from an explicit allowlist. The builder is not required to use the extracted archive. The archive contains this README, bilingual runbook, sample, license, two scripts, two test modules, and a `SHA256SUMS` manifest. It excludes backups, credentials and local handoff files.

After extracting the ZIP into its own directory:

~~~powershell
py -3 -m unittest discover -p "test_*.py" -q
py -3 red_green_demo.py
py -3 jsonl_utf8_guard.py --input sample_events.jsonl
~~~

Rebuilding the package with the same source bytes produces the same ZIP hash. A SHA-256 sidecar is emitted beside the ZIP. A public GitHub repository has **not** been created for the release at the time of packaging.
