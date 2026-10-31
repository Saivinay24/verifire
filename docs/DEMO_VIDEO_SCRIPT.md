# VeriFire demo video: script (2:50)

Record on a phone (screen recording) plus the laptop terminal. Every number below is real and on the live server after `judge/demo_seed.py`. Speak at an easy pace: about 380 words in total.

Before recording:
- Run `uv run python -m judge.demo_seed --base-url https://scammap-huii.onrender.com` and check that the table prints "yes" on every row.
- Open https://scammap-huii.onrender.com once so the server is awake.
- Have `scripts/demo_licence.sh` ready with `MIN=1`, so the expiry fits in the video.

| Time | Screen | Say |
|---|---|---|
| 0:00 to 0:15 | Phone, home screen of the app | "Ravi's father lost two lakh rupees to a fake police video call. The next day the same number called someone else, who had no way to check it. VeriFire lets anyone check a number before they answer or pay." |
| 0:15 to 0:35 | Type `98450 11111`, tap Check | "This number was reported by five different people over two days, with real stories. It shows Known scam, and the number is shown in full." |
| 0:35 to 0:50 | Check `98450 22222` | "This one has only two reports. It stays Suspicious, and the number is hidden, as the brief asks, until three different people agree." |
| 0:50 to 1:05 | Report flow: pick type, channel, area, a short note, Submit | "Reporting takes three taps and a few seconds, with no login. In English or Hindi." Tap the language switch once. |
| 1:05 to 1:40 | Check `98450 44444`, then `98450 55555`, then `98450 66666` | "No login means anyone can fake reports, so we count people, not reports. 22 accounts on one Wi-Fi: counted as one. 40 friends attacking a bakery with shop complaints: never Known scam. 10 friends with two accounts each, pasting one story: counted as one." |
| 1:40 to 1:55 | Check `1930` | "Real helplines like 1930 are on a verified list and can never be flagged, however many people report them." |
| 1:55 to 2:10 | Map tab, area 560034 | "The map shows each area's official point, never a person's location. Koramangala has a spike: 9 reports today against a usual 2 a day. Fake reports are filtered out before alerts are counted." |
| 2:10 to 2:40 | Laptop, `MIN=1 scripts/demo_licence.sh`, steps 1 to 5 (cut the waiting) | "The server only runs with a signed licence. A forged licence is refused. A one-minute licence expires, every request is refused, and the app shows Licence expired. The data is kept. Upload a new licence and it works again at once, with no restart." |
| 2:40 to 2:50 | Deck slide 11 (live numbers) | "On the live server, 100 of 100 fake-report tricks were blocked, 199 of 200 real scams were caught, and no reply leaked a reporter's identity. VeriFire, by Team Velosta." |

Cuts: if it runs long, drop the 1930 shot (1:40 to 1:55) first.
