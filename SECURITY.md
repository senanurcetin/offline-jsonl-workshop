# Security Policy

## Supported scope

Only the current main branch is actively maintained. The project is an independent educational Python/JSONL and ZIP-integrity workshop, not a production security product, an official Anthropic tool, or a guarantee against every malicious input. No historical support series or response-time SLA is promised.

## Private vulnerability reporting

Do **not** disclose credentials, real user records, sensitive proof-of-concept payloads or exploit details in a public issue or PR.

If GitHub's Security → Report a vulnerability option is enabled for this repository, please use that private channel. Otherwise, arrange an appropriate private reporting channel with the maintainer before sending confidential details. No unverified security email address or response deadline is provided here.

A non-sensitive correctness bug with a harmless synthetic reproduction can be filed as a regular issue. Include affected commit, Python version, operating system, precise impact, minimized sanitized reproduction and, where possible, a regression test.

## Integrity and trust limits

- The included SHA256SUMS manifest proves that the packaged files match the manifest; it does not authenticate the publisher.
- A .zip.sha256 sidecar from the same untrusted download location is not an independent trust anchor.
- The verifier does not extract or execute ZIP content; it still is not a production archive security review.
- Do not share private keys, access tokens, personal JSONL records or customer datasets in tests, bug reports or workshops.
- The maintainers will evaluate reports and any disclosure based on verified severity and available capacity.

## Türkçe

Bu projeye ilişkin güvenlik açıklarını bildirirken gizli bilgileri, gerçek kullanıcı verilerini veya hassas exploit ayrıntılarını herkese açık issue ve PR'lara yazmayın. GitHub özel güvenlik bildirimi etkinse Security → Report a vulnerability seçeneğini kullanın. Etkin değilse önce özel iletişim kanalı üzerinde anlaşın. ZIP içindeki SHA-256 manifesti tek başına yayıncı kimliğini kanıtlamaz.
