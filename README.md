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


## Public source and standalone offline package

This workshop is independently authored example material, **not** an official Anthropic product, partnership, certification, or an Anthropic-maintained repository. The source is provided under the MIT license in `LICENSE`. No workshop has been hosted.

The original development workspace contains a separate release builder (`prepare_workshop_release.py`) that packages this workshop reproducibly from an explicit allowlist. The builder is not required to use the extracted archive. The archive contains this README, bilingual runbook, sample, license, three scripts, three test modules, and a `SHA256SUMS` manifest. It excludes backups, credentials and local handoff files.

After extracting the ZIP into its own directory:

~~~powershell
py -3 -m unittest discover -p "test_*.py" -q
py -3 verify_release.py
py -3 red_green_demo.py
py -3 jsonl_utf8_guard.py --input sample_events.jsonl
~~~

Rebuilding the package with the same source bytes produces the same ZIP hash. A SHA-256 sidecar is emitted beside the ZIP. Public repository: https://github.com/senanurcetin/offline-jsonl-workshop. The reusable offline ZIP can be built locally; it is not claimed as a published GitHub Release. Git checkouts preserve source bytes for the accompanying `SHA256SUMS` manifest via `.gitattributes`.

### Public repository integrity check

After cloning the public repository, or extracting the offline ZIP, run `py -3 verify_release.py` in the project directory. This local, dependency-free command validates every expected file against `SHA256SUMS`. It rejects malformed, duplicate, unexpected or path-traversal manifest entries, detects changed or missing source files, and does not reveal source contents. Git's `.gitattributes` preserves the manifest-verified bytes on Windows, macOS and Linux.

### Türkçe — Yayımlanan dosyaları doğrulama

GitHub deposunu klonladıktan veya ZIP paketini çıkardıktan sonra proje klasöründe `py -3 verify_release.py` komutunu çalıştır. Araç, beklenen tüm kaynak dosyalarını `SHA256SUMS` ile karşılaştırır; değiştirilmiş veya eksik dosyaları, hatalı veya yinelenmiş manifest kayıtlarını ve klasör dışına erişim girişimlerini reddeder. Ek paket veya ağ bağlantısı gerekmez; dosya içeriği ekrana yazdırılmaz.


### Verify the ZIP without extracting it (English)

The verifier can inspect a local workshop ZIP **without extraction**:

~~~powershell
py -3 verify_release.py --archive "path\to\offline-jsonl-workshop.zip"
~~~

This checks the exact expected members, rejects duplicate, unsafe, symlinked, encrypted, oversized or missing ZIP entries, and verifies source bytes against the bundled SHA256SUMS. It performs no network requests and does not execute archive contents.

**Integrity is not authenticity:** An attacker who replaces both files *and* the included manifest could produce another self-consistent ZIP. To authenticate a download, also compare the full ZIP SHA-256 against a checksum obtained from a trusted independent channel. This repository does not claim a published ZIP release.

### ZIP paketini çıkarmadan doğrula (Türkçe)

Bir ZIP dosyasının içeriğini klasöre açmadan kontrol etmek için:

~~~powershell
py -3 verify_release.py --archive "path\to\offline-jsonl-workshop.zip"
~~~

Bu işlem ZIP içindeki beklenen dosyaları ve SHA256SUMS değerlerini doğrular; yinelenen, eksik, güvensiz, sembolik bağlantılı ve aşırı büyük kayıtları reddeder. Ağ bağlantısı veya ZIP içindeki kodun çalıştırılması gerekmez.

**Bütünlük, kaynak kimliğini kanıtlamaz:** Dosyalarla birlikte manifest de değiştirilmişse sahte bir paket kendi içinde tutarlı görünebilir. Gerçek kaynağı doğrulamak için ZIP dosyasının SHA-256 değerini ayrıca güvenilir bir kanaldan alınan değerle karşılaştırın.


### Independently trusted ZIP SHA-256 (English)

Checking the hash manifest inside a ZIP proves internal consistency, not
the identity of the publisher. For stronger verification, get the **complete
ZIP file's SHA-256** from a trusted independent channel, and pass that value
explicitly alongside the local ZIP path:

~~~powershell
py -3 verify_release.py --archive "path\to\offline-jsonl-workshop.zip" --expected-archive-sha256 "<trusted_64_character_lowercase_sha256>"
~~~

The tool verifies the **exact bytes it subsequently parses**, then validates
the internal allowlisted source checksums. It rejects malformed and mismatched
trusted hashes, requires the --archive flag, and does not use an internet connection.
A checksum supplied by the same untrusted download location does **not** by
itself prove publisher authenticity. No release signature or externally
trusted checksum distribution is claimed by this project.

### Haricî güvenilir ZIP SHA-256 kontrolü (Türkçe)

ZIP içindeki SHA256SUMS dosyasının doğrulanması, paketin yalnızca kendi
içinde tutarlı olduğunu gösterir. Paketin tam SHA-256 değerini **bağımsız ve
güvenilir bir kaynaktan** elde ettiğinizde bunu ayrıca kullanabilirsiniz:

~~~powershell
py -3 verify_release.py --archive "path\to\offline-jsonl-workshop.zip" --expected-archive-sha256 "<guvenilir_64_karakter_kucuk_harf_sha256>"
~~~

Bu kontrol, arşivin tüm baytlarını güvenilir değerle karşılaştırır ve ardından
içerik manifestini doğrular. Hatalı hash biçimi veya uyuşmayan değer reddedilir.
İnternet, ücretli servis veya arşivi açıp içindeki kodu çalıştırmak gerekmez.
ZIP ve doğrulama değeri aynı güvenilmeyen kaynaktan alındıysa işlem tek başına
kaynağın özgünlüğünü kanıtlamaz.
