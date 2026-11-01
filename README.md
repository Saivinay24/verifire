# VeriFire

Our answer to PS 03, Community Scam Map (CyberForge 2026 by Mitigata), from Team Velosta.


People report scam calls, SMS, UPI ids and links in a few taps, with no login. Anyone can look up a number before they answer or pay. The map shows where scams are rising, area by area. Fake reports from spammers, fake accounts or friends piling on never turn an honest number into a "Known scam".

- **Live server:** https://scammap-huii.onrender.com (hosted in Singapore, so it answers fast from India)
- **App:** the same address on any phone or laptop. It is a mobile website you can add to the home screen, in English and Hindi, with its own layout for laptop screens.
- **Code:** https://github.com/Saivinay24/verifire
- **Demo Video:** https://youtu.be/051OKV0sthI

What the app does on top of the brief:
- **Say it instead of typing.** The note box takes speech in English or Hindi, turned into text by the browser's speech service (in Chrome, that is Google's), never by our server. VeriFire stores only the note's fingerprint, never the words, the same as a typed note.
- **Prepare my complaint.** After a report, the app writes a complaint from it, with blanks in [brackets] for the person to fill in. They can copy it, share it, open it as an email to their bank, or open cybercrime.gov.in. Nothing is sent by our server. If money was lost, it leads with "Call 1930 first".
- **The city at a glance.** The map fills the screen. A sheet pulls up over it with alerts, trending scam types, numbers 3 or more people reported, each area's count, and a recent feed. Everything on it comes only from reports the trust engine counted, so a fake-account farm adds nothing.
- **Live on VeriFire.** A statistics page for the last 7, 30 or 90 days: reports counted against reports set aside, a 14-day chart, and breakdowns by scam type, channel and city. Next to it sit official national figures, quoted with their source.

## Contents

1. [Run it](#run-it)
2. [Tech stack](#tech-stack)
3. [The API](#the-api)
4. [How the trust rules work](#how-the-trust-rules-work)
5. [Privacy](#privacy)
6. [How the licence works](#how-the-licence-works)
7. [How we tested it](#how-we-tested-it)
8. [Known limits](#known-limits)
9. [Repository layout](#repository-layout)

## Run it

### Use the live server

Nothing to install. Open https://scammap-huii.onrender.com on a phone or point the test tool at it.

To load demo numbers (this resets the server first):

```bash
uv run python -m judge.demo_seed --base-url https://scammap-huii.onrender.com
```

| Look up | What it shows |
|---|---|
| `98450 11111` | Known scam: 5 real victims, number shown |
| UPI `refund.helpdesk@ybl` | Known scam: 4 real victims |
| `98450 22222` | Suspicious: only 2 people, number hidden |
| `98450 33333` | Suspicious: one person reported 6 times, counted as 1 |
| `98450 44444` | Suspicious: 22 fake accounts on one Wi-Fi, counted as 1 |
| `98450 55555` | Suspicious: 40 friends attacking a bakery, never Known scam |
| `98450 66666` | Suspicious: 10 friends with 2 accounts each, same text |
| `98450 88888` | Suspicious: 25 bots inside a minute |
| `98450 77777` | Suspicious: the owner disputed it |
| `1930` | Verified business (the national cybercrime helpline) |
| `98450 99999` | No reports |

Map: area **560034** (Koramangala) shows a spike alert.

### Run it on your laptop

You need Python 3.12, [uv](https://docs.astral.sh/uv/) and Postgres.

```bash
uv sync
createdb scammap
export DATABASE_URL=postgresql+psycopg://localhost/scammap
export REPORTER_HMAC_SECRET=$(openssl rand -hex 32)
uv run alembic upgrade head
uv run uvicorn app.main:app --port 8000
```

Open http://127.0.0.1:8000. The server starts with a valid licence (`licences/bootstrap.json`), so it works straight away.

### Checks

```bash
uv run pytest -q          # 110 tests
uv run ruff check . && uv run ruff format --check . && uv run mypy app
```

GitHub Actions runs the same checks against a real Postgres on every push.

### Deploy your own

`render.yaml` is a Render blueprint for one web service and one Postgres database, both in Singapore. It creates the HMAC secret itself. Database migrations run on every start.

## Tech stack

| Layer | What we used | Why |
|---|---|---|
| Language | Python 3.12 | Fast to write, easy for judges to read |
| Web framework | FastAPI + Uvicorn | Async server, exact control over status codes and reply shapes |
| Database | PostgreSQL 16 | Real transactions, so every report and lookup is consistent |
| Database access | SQLAlchemy 2 Core + psycopg 3 | Plain SQL we can read, no hidden ORM queries |
| Migrations | Alembic | Database changes are versioned and applied on every deploy |
| Settings | pydantic-settings | Secrets come from environment variables, never from code |
| Licence signing | PyNaCl (Ed25519) | Small, fast, standard signatures. Only the public key is in the code |
| Note fingerprints | MinHash + LSH, written by us | Spots copied notes without storing any note text |
| Front end | Plain HTML, CSS and JavaScript (no framework, no build step) | Loads fast on cheap phones and slow networks |
| Map | Leaflet 1.9.4 + OpenStreetMap tiles | Free and open, loaded only when the map opens |
| Hindi | Noto Sans Devanagari, plus the browser's own speech for spoken labels | Readable Hindi, and tiles read aloud for people who can't read |
| App install | Web app manifest | Add to home screen on Android and iPhone, no app store |
| Hosting | Render (Singapore web service + Postgres) | HTTPS by default, close to India |
| Quality | pytest, ruff, mypy (strict), GitHub Actions | Every push is tested, linted and type-checked |
| Package manager | uv | Locked versions, so a fresh install matches ours |
| Test tools | judge/ (written by us) | A test world built only from the brief, run against the live server |

## The API

The seven addresses from Appendix A have no login, as the brief asks.

| Address | What it does |
|---|---|
| `GET /health` | `{"ok": true}`. Always works, even when the licence has expired |
| `POST /reports` | Saves a report. 201, 400 for bad input, 429 when someone reports too fast |
| `GET /lookup?type=&value=` | The verdict for a number, UPI id, link or SMS sender |
| `GET /lookup/reports?type=&value=` | Every report filed on one number, newest first: when, how, scam type, area, and yes/no proof badges (screenshot, lost money, described it). Same masking as the lookup. Never who reported, what they wrote or how much. Extra, not in Appendix A |
| `GET /map?pincode=&days=&radius_km=` | Scam clusters near an area (defaults: 7 days, 2 km) |
| `GET /alerts?pincode=` | `SPIKE` and `NEW_TYPE` alerts for an area |
| `GET /city?pincode=&days=` | The app's city sheet: hot areas, trending types, known scam numbers, recent feed (default 7 days). Extra, not in Appendix A |
| `GET /stats?days=` | Live totals and breakdowns, counted after the trust rules (default 30 days). Extra, not in Appendix A |
| `POST /admin/reset` | Deletes every report |
| `POST /challenges` | A business disputes a number (bonus). 409 if that number's last dispute ended against the claim in the past 90 days; 429 after 20 disputes from one network in a day |
| `GET /review/disputes`, `POST /review/disputes/{id}` | The reviewer's queue and decisions (`upheld` or `rejected`), behind the `REVIEW_KEY` header. Off when `REVIEW_KEY` is unset. Extra, not in Appendix A |
| `GET /license`, `POST /license` | Show or replace the licence |

**Every way of typing a number gives the same answer.** For example, `+91 98765 43210`, `098765-43210` and `9876543210` are all one number. The same holds for UPI ids in any letter case, links with or without `https://` and `www`, and sender ids like `VM-HDFCBK` and `HDFCBK`.

## How the trust rules work

We count **independent people, weighted by how much proof they gave**, not raw reports. Every number goes through 5 steps. All 72 constants live in one file, `app/domain/constants.py`, and each has a written reason.

1. **Group: who is really the same person?** Reports are merged into one group when any of these holds:
   - the same reporter
   - accounts switched on one connection within 15 minutes
   - 3 or more accounts from one connection
   - copied notes (similarity 0.7 or more)
   - a burst of 8 or more reports in an hour that all say the same thing
   - a burst with no proof that was filed instantly, has unnaturally even notes, or has no agreement on scam type

2. **Weigh each person.**
   - Note quality: a blank note is worth 0.5, a short one 0.8, a full one 1.0.
   - Copied notes lose value (down to 30%).
   - Proof adds up to 30%: a screenshot, a stated loss, or scam method words.
   - Repeat reports and reporting too fast reduce weight.
   - Someone who also reported a verified bank number counts half.

3. **Cap.**
   - People on one connection count as at most `min(1 + 0.15 ln n, 1.25)`. Two people on home Wi-Fi count as 1.10, and 22 fake accounts count as 1.25.
   - A group counts as at most 1.3, which is one fully proven person.

4. **Campaign factor.** Does the wave look real? Real victims trickle in over hours, from many places, with proof. Brigades arrive in minutes, from one place, with nothing. Seven bounded factors (speed, merged groups, blank notes, one area, proof, back-dating, uniform notes) multiply the score by between 0.2 and 1.1.

5. **Pile-on check.** With 8 or more people, it is a pile-on if any of these holds:
   - 75% or more said nothing: no note, and no screenshot or stated loss (proof without words counts only when 75% or more agree on the scam type)
   - 30% or more of the notes read like shop reviews
   - under 10% showed any harm: a screenshot, a stated loss, or the scam method named
   - fewer than half agree on the scam type (stages of one script, like a customs parcel call that turns into a digital arrest, count as one)

   A pile-on is never "Known scam". This is how "40 friends reporting a real bakery" is stopped. If a scammer floods their own number with empty reports to trigger the check, we re-check using only the people who said something or showed harm, and only if they are independent people (not accounts the engine already tied together). The type vote is one per independent group, so fake accounts merged into one voice cannot outvote the victims.

**Verdict.**
- A number is **Known scam** when there is no pile-on, at least **3 groups**, at least **2 of them described** what happened or showed proof, and the **score is 1.7 or more**.
- Why 1.7: three real victims with blank notes who each lost money score 3 × 0.575 = 1.725. Three blank clicks score 1.5.
- Verified business and helpline numbers always say **Verified business**.
- A disputed number is never Known scam while it is under review. Every review ends; see "Disputes" below.

### Disputes: protect a wrongly reported owner, never shield a scammer

The brief's rule (a disputed number is never Known scam while under review) would, on its own, let a scammer dispute every number he uses and turn each red warning amber for good. So every dispute ends, and each way out is decided by something the claimant does not control:

| Outcome | When | What people then see |
|---|---|---|
| **Upheld** | A reviewer accepts the owner's proof | The reports so far are set aside; the number starts fresh, and new reports count as usual |
| **Rejected** | A reviewer does not | The normal verdict comes back |
| **Overruled** | New people on new networks, none of whom reported before the dispute, keep reporting it, clear the full Known scam bar on their own, and are spread over at least 6 hours | The normal verdict comes back |
| **Lapsed** | Nobody decided within 7 days | The normal verdict comes back |

- After a dispute is rejected, overruled or lapsed, that number cannot be disputed again for 90 days.
- One network can open at most 20 disputes a day. The reviewer sees how many numbers the same contact or network has disputed, so one scammer disputing his whole list shows up as one pattern.
- While a dispute is open, the reply keeps the evidence (how many people, what scam, when) and shows the review deadline, so people are still warned. Only the strongest label waits.
- Times are the server's receive times, which no client can set. A burst of reports fired right after a dispute (the harassment pattern) cannot break it; an active scam keeps producing new victims over hours.
- Who reviews: whoever runs VeriFire (for us, the team; in production, the operator or a partner bank or telecom). The page is at `/review`. It shows the owner's proof and the counted evidence, never who reported.
- These 5 numbers live in `app/domain/disputes.py`, apart from the 72 trust constants, which disputes do not change. `tests/test_disputes.py` has one test per case above, and each rule was checked by removing it and watching its test fail.

**Why a fake-reported number is not labelled a scam:** the lookup reply only ever shows counts and evidence. Because of the steps above, `distinct_reporters` counts independent people, so 22 fake accounts show as 1.

**Alerts use the same rules.** Only reports that pass the trust rules count towards a spike, so fake reports cannot set one off.
- **SPIKE:** the last 24 hours have at least 5 reports and at least twice the daily average of the 7 days before.
- **NEW_TYPE:** a scam type that was not seen in the 30 days before.

Full detail:
- [docs/TRUST_PARAMETERS.md](docs/TRUST_PARAMETERS.md): every constant, its value, where it came from, and the exact formula it sits in.
- [docs/TRUST_ENGINE.md](docs/TRUST_ENGINE.md): a step-by-step walk-through with worked numbers.

## Privacy

- **Reporter ids and IPs are never stored.**
  - Each reporter id is replaced by `HMAC-SHA256(server secret, id)`.
  - Each IP is cut to its /24 and hashed the same way.
  - Without the secret, nobody can work backwards from these to a person.
- **Note text is never stored.** We keep only its length, a 64-number fingerprint for spotting copies, and three yes/no flags. The note cannot leak because it is not there.
- **No exact location.** The map shows only the official point for each area (Appendix B). On the phone, "near me" picks the nearest area on the phone itself and sends only the area code.
- **Masking.** A number reported by fewer than 3 different people is shown masked, like `98XXXXX222`.
- **Evidence** in a lookup shows only the time, channel, scam type and area. It never shows who reported, their IP, or their note.
- **"See all reports filed"** lists every report on a number with the same fields, plus three yes/no proof badges. The number stays masked under 3 people, and verified numbers list nothing. What people wrote cannot be shown because it is never stored.
- **The city sheet and stats** follow the same rules. A number shows in full only where the lookup would show it in full. Feed times are rounded to the hour, and every point is an official area point.
- **Speech and complaints stay on the phone.** Speech is turned into text by the browser's own speech service, and no audio reaches our server. The complaint is built on the phone and goes only where the person sends it.
- **Logs** keep only an allowed list of fields. They hold no reporter, IP, note or reported number.
- **Careful wording:** "Reported by 5 people", never "fraudster". This applies in English and Hindi.
- **No login, no accounts, no analytics, no scraping.**

The privacy audit loads full test worlds and then checks:
- the database itself
- the server log
- every API reply
- the app code

Result: 0 failures. See `evidence/privacy_audit.md`, or run it yourself with `uv run python -m judge.privacy_audit`.

## How the licence works

**The licence file.**
- It is a JSON document: `licence_id`, `licensee`, `issued_at`, `expires_at` and an **Ed25519 signature** over those four fields.
- The server holds only the **public key**. The private key stays on the vendor laptop (`~/.scammap-keys/`) and is never in this repository.
- Changing any field breaks the signature.

**Checking.** The licence is checked on **every request**, not only at start-up.
- The active licence is cached for at most 5 seconds, so a new upload or an expiry takes effect within seconds, with no restart.
- When it expires, every address except `/health` and `/license` answers `403 LICENSE_EXPIRED`, and the app shows a "Licence expired" screen.
- **Data is locked, never deleted.**

**Renewing.** `POST /license` with a new signed file works at once. The old data is all still there.

**Clock rollback.** The server stores the latest time it has seen, every 10 seconds, in the database.
- If the clock is moved back more than 5 minutes behind that time, or behind the licence's issue time, the licence is refused.
- Turning the clock back cannot make an expired licence valid again.

**State.** The licence and the high-water time live in the database, so a restart or a second server instance agrees.

**Demo files.**

```bash
# long licence, ready in the repo
licences/demo-bank-long.json

# 5-minute licence, minted right before the demo so it is still fresh
uv run python -m scripts.mint_licence --licensee "Demo Bank" --minutes 5 --out licences/demo-5min.json
```

The four-step demo from the brief can be run and timed automatically:

```bash
uv run python -m judge.licence_demo --base-url https://scammap-huii.onrender.com
```

It passed all 4 steps on the live server (`evidence/licence_demo_20261031-1528.md`).

To present it live, one step per Enter key (it mints the 5-minute licence on the spot, shows a forged licence being refused, counts down to the expiry, then renews with the long licence):

```bash
scripts/demo_licence.sh            # MIN=2 for a shorter wait
```

## How we tested it

`judge/world.py` builds test worlds **only from the brief**. Each world has:
- real victims (3 to 30 per number)
- spammers
- fake-account farms
- friends piling on
- real verified numbers
- area spikes and new scam types
- every number written in many formats

`judge/run.py` plays a world against a server and grades every scoring row of the brief.

Rule: we tuned on some seeds and **tested on fresh seeds we had never tuned on**.

Live server, held-out seeds 9101 to 9110 (about 6,600 reports):

| Check | Result |
|---|---|
| Tricks never become Known scam (friends, fake accounts, spam) | 100 / 100 |
| Real scams found as Known scam | 199 / 200 |
| Numbers with 1 or 2 reporters stay Suspicious | 160 / 160 |
| Under 3 people, number hidden | 434 / 434 |
| Every way of typing a number gives the same answer | 3,250 / 3,250 |
| Replies that leak a reporter, IP or note | 0 of 11,421 |
| Map, spike and new-type alerts | all pass |
| Fake reports never set off an alert | 40 / 40 |
| Lookup time | p50 82 ms, p95 166 ms, p99 294 ms (inside the server: p50 1.8 ms) |

There is also a scenario catalogue (`judge/catalog.py`) with 65 stories, from "10 friends with 2 accounts each" to "a scammer floods their own number". Results: [docs/SCENARIOS.md](docs/SCENARIOS.md).

**Blind evaluation.** An outside agent that saw only the brief (never our code or tests) wrote its own attack suite and ran it against the server. Every named trick, alone or combined, was stopped in 160 of 160 attack runs, and none of those fakes set off an alert. The failures it found were traced to their exact cause in the engine and fixed; the few cases we chose not to change are listed under Known limits.

## Known limits

We state these rather than hide them.

- **Three victims with blank notes and little proof** stay Suspicious. This is deliberate: the bar is 1.7, and three blank clicks must never pass.
- **Friends who each write their own convincing scam story** can look like real victims. No report-only system can tell them apart. The defences are the dispute feature and the verified list.
- **In a fast viral wave**, some real victims sharing one connection within 15 minutes are merged. About 24 of 30 are counted.
- **Many real victims with only blank notes** (no words, no screenshot, no loss) stay Suspicious, because that is exactly the shape of the "40 friends" attack. And victims who all write the same few short Hindi or Hinglish phrases can be merged as copies; truly different Hindi notes are counted normally.
- **Say it on iPhone needs Safari.** Apple lets only Safari use the speech engine, so in Chrome, Firefox or Edge on iPhone the button opens the note with the keyboard up and points to the keyboard's mic key, which works in English and Hindi.
- **The constants were tuned on our own simulator**, because no public, labelled set of Indian scam reports exists. The held-out seeds were never used for tuning.

## Repository layout

```
app/
  api/        routes, health, licence gate
  domain/     trust rules, constants, number formats, notes fingerprint, licence check, alerts
  services/   reports, lookup (with cache), areas and map, licence state, challenges
  repos/      database tables and queries
  static/     the mobile web app (HTML, CSS, JS)
migrations/   Alembic database migrations
licences/     the bootstrap and long demo licences (public, signed)
scripts/      mint_licence.py (vendor laptop only), demo_licence.sh, keepalive.py
judge/        test world, grader, scenario catalogue, privacy audit, licence demo, demo data
tests/        110 unit and API contract tests
evidence/     saved results of every live run
docs/         trust parameters and trust engine walk-through
```
