# Proposed Community Workshop — bilingual facilitator runbook

**Status: content developed; event NOT held, attendees NOT counted.**
Audience: Python beginners/intermediates; local or online Turkish/English developers.
Duration: 45 minutes. No Claude subscription, API credits, tokens, or account required for the offline core exercise.

## Türkçe plan

- 0–5 dk — GitHub PR mantığı: sorunu tanımlama, küçük ve incelenebilir değişiklikler.
- 5–12 dk — Gerçek hata sınıfı: emoji karakter sayısı ile UTF-8 bayt sayısı farkı. Ölçüm ve etkisi.
- 12–22 dk — Red: geçici kopyadaki karakter sayısı kontrolünün bir regresyon testinden kalması.
- 22–32 dk — Green: ham bayt kontrolünün uygulanması ve tüm testlerin yeniden çalıştırılması.
- 32–38 dk — Review: güvenlik, veri gizliliği, JSONL kaydı, tekrarlanan anahtarların reddedilmesi ve fail-closed mantığı.
- 38–45 dk — Soru-cevap; GitHub PR özetinde yeniden üretim adımları ve dürüst AI katkı beyanı.

## English plan

- 0–5 min — Why small reviewable PRs matter.
- 5–12 min — Unicode code points versus UTF-8 bytes in streaming JSONL.
- 12–22 min — Red: run a failing regression in a **disposable copy** with an incorrect character-count guard.
- 22–32 min — Green: restore byte-size validation and execute all tests.
- 32–38 min — Review: privacy, bounded reads, malformed UTF-8, duplicate JSON object keys (including nested / escaped keys), fail-closed behavior.
- 38–45 min — Q&A and how to describe verified tests in a GitHub PR.

## Offline commands

Run in the community_demo folder (Windows):

~~~powershell
py -3 jsonl_utf8_guard.py --input sample_events.jsonl
py -3 -m unittest discover -p "test_*.py" -v
py -3 red_green_demo.py
~~~

The CLI prints only an aggregate record count; it never returns source messages.
The example never makes network calls.

## Demonstration integrity checklist

- Publish/announce **only if** an event really exists and has a confirmed time/location.
- Do not imply official Anthropic partnership, sponsorship or Community Ambassador status.
- Do not claim an attendance count, testimonials, delivered classes, or actual Claude API use without evidence.
- Avoid collecting participant personal information without clear notice and consent.
- Do not present this independent sample as an Anthropic SDK patch or an accepted upstream PR.
- Record future genuine impact with optional public event links, published materials, and verified pull requests.
