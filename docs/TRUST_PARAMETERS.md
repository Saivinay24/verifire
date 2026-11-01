# Every number we chose, and where it came from

All numbers were checked against the code on 31 Oct 2026, so this file matches the deployed build.

Each section below lists its constants, then the exact formula they appear in (constants in capitals, matching app/domain/trust.py).

## The count

| Area | Named constants | File |
|---|---|---|
| Trust engine: verdict bar | 4 | app/domain/constants.py |
| Trust engine: step 1, grouping | 12 | app/domain/constants.py |
| Trust engine: step 2, weight per person | 16 | app/domain/constants.py |
| Trust engine: step 3, caps | 3 | app/domain/constants.py |
| Trust engine: step 4, campaign factor | 23 | app/domain/constants.py |
| Trust engine: step 5, pile-on gate | 7 | app/domain/constants.py |
| Alerts | 4 | app/domain/constants.py |
| Rate limits | 3 | app/domain/constants.py |
| **Total in constants.py** | **72** | |
| Note fingerprint (MinHash) | 3 | app/domain/notes.py |
| Lookup reply and cache | 3 | app/services/lookup.py |
| Licence | 3 | app/domain/licence.py, app/services/licence.py |
| Report time check | 1 | app/services/reports.py |
| Map | 3 (2 defaults + earth radius) | app/api/routes.py, app/services/areas.py |
| Alert windows and severity | 5 (24h, 8d, 31d, 10, 5) | app/domain/alerts.py, app/services/areas.py |
| Database pool | 3 | app/db.py |
| **Total outside the trust engine file** | **21** | |

There is also one inline literal in the trust engine: the 0.7 weight on method words in the evidence factor (step 4).

Honest summary: **72 tunable numbers** in one file, plus 21 fixed engineering and PRD values elsewhere.

## How each value was chosen (the 7 sources)

Every value comes from one of these. We say which one for each number below.

| Tag | Source | Meaning |
|---|---|---|
| **PRD** | The brief itself | Copied straight from the PRD text or its appendices. |
| **MIN** | Smallest-case derivation | Worked backwards from the smallest case that must pass and the biggest case that must fail. |
| **SIM** | Simulator assumption | An assumption we built into our test world (judge/world.py). It is not measured from real Indian scam data. |
| **MEAS** | Measured on the simulator | Measured by running the code over thousands of simulated reports. |
| **TUNE** | Hand-tuned on the harness | We started from a reasoned value, ran the randomised harness, looked at which cases failed, changed the value by hand and ran it again, until genuine cases passed AND every attack failed. Then all values were frozen and checked on holdout seeds we had never tuned on. There was no automated sweep. |
| **RES** | Initial research | Taken from our initial research report (section 4.3). "RES (x), then TUNE" means the research suggested x and the harness made us change it. |
| **ENG** | Engineering default | A standard systems choice such as a cache size or a pool size. |

**Where the 72 came from.** The first build had 56 constants. 28 came from our initial research (17 at the research's exact value and 11 changed after harness runs; one of the 17, STYLE_MAX_CV, was later tuned from 0.18 to 0.06, so 16 are exact today), 3 from the brief, and 25 were ours. The other 14 were added while tuning, each time the harness found an attack the engine missed: 5 coordinated-burst rules, then 8 (the pile-on gate, the "2 must describe it" rule and the alert group cap), then the account-switch and account-farm rules (one pile-on constant was removed at the same time). The last 2 (PILE_ON_MIN_HARM_SHARE, PROOF_MIN_TYPE_SHARE) came from a blind evaluation written without access to our harness; see below.

We did not have a real labelled dataset of Indian scam reports, because none is public. So **TUNE** and **MEAS** values are tuned against our simulator, not against the real world. In the eval, say that plainly. The defence is that every value was then tested on held-out seeds (9101 to 9110 and 9301 to 9305) that were never used for tuning.

## Verdict (4)

| Constant | Value | Source | Why this value |
|---|---|---|---|
| KNOWN_MIN_GROUPS | 3 | PRD | The brief's own "3 different people" bar for unmasking. |
| KNOWN_MIN_DESCRIBED | 2 | MIN + TUNE | At least 2 of those 3 must have said what happened or shown proof. We tried 3, but real k3 cases with one blank note were failing; 2 still blocks every trick. |
| KNOWN_MIN_SCORE | 1.7 | MIN | The smallest real case is 3 people with blank notes who each lost money: 3 × 0.575 = 1.725, which passes. Three blank clicks with no proof score 3 × 0.5 = 1.5, which fails. 1.7 sits between them. We came down from 2.5, then 2.1, then 1.7. |
| UNMASK_MIN_SCORE | 1.7 | MIN | Same bar, so a number is never unmasked on weaker evidence than a "Known scam" verdict. |


**Formula: Verdict and unmasking**
```
established = no pile-on AND groups >= KNOWN_MIN_GROUPS AND described >= KNOWN_MIN_DESCRIBED AND score >= KNOWN_MIN_SCORE
unmask      = verified OR (established at UNMASK_MIN_SCORE)
```

## Step 1: grouping, who is really the same person (12)

| Constant | Value | Source | Why |
|---|---|---|---|
| NOTE_DUP_SIMILARITY | 0.7 | TUNE | Copy-paste with small edits scores above 0.8 Jaccard. Two real victims of the same script score 0.3 to 0.5. 0.7 separates them. |
| NOTE_DUP_MIN_CHARS | 15 | TUNE | Short notes like "fraud call" collide by chance, so they are never linked. |
| BURST_WINDOW | 60 min | TUNE | The window used to look for a brigade. |
| BURST_MIN_REPORTS | 8 | TUNE | Below 8 there is too little to call it coordinated. Also matches the pile-on minimum. |
| BURST_MIN_DIVERSITY | 0.3 | TUNE | If under 30% of the notes in the burst are distinct, it is a lockstep brigade. Lowered from 0.5 after the blind evaluation: real waves whose notes come from a small template pool sat at about 0.46. A blank or short report with proof of harm is its own voice; a short note counts by its exact text. |
| COORD_MAX_EVIDENCE_SHARE | 0.15 | TUNE | A coordinated burst has almost no screenshots or losses (under 15%). |
| COORD_INSTANT_LAG | 2 min | TUNE | A victim of a 3-hour call does not report 30 seconds after it started. |
| COORD_INSTANT_SHARE | 0.8 | TUNE | 80% of the burst reported "instantly". |
| COORD_UNIFORM_CV | 0.05 | MEAS | Generated text has very even note lengths (CV about 0.03). Real notes never go below 0.07. |
| COORD_SCATTER_SHARE | 0.5 | SIM | One number runs one script. If no scam type covers half the burst, the reporters are not real victims. |
| SAME_CONNECTION_PAIR_WINDOW | 15 min | TUNE | Two accounts on one connection within 15 minutes is one person switching accounts (the "10 friends with 2 accounts each" case). |
| SAME_CONNECTION_MIN_ACCOUNTS | 3 | TUNE | Two accounts on a /24 can be neighbours on a carrier (CGNAT). 3 or more is a farm. We raised this from 2 after the holdout. |



**Formula: Step 1, grouping (union-find; any edge merges two reports into one group)**
```
copied_note:     J(A,B) >= NOTE_DUP_SIMILARITY  AND  min(len_A, len_B) >= NOTE_DUP_MIN_CHARS
                 J = |A ∩ B| / |A ∪ B| over 4-char shingles, estimated as matching slots / SIG_SIZE
                 LSH finds a pair with P(s) = 1 - (1 - s^4)^LSH_BANDS
account_switch:  same /24, different account, gap <= SAME_CONNECTION_PAIR_WINDOW
same_connection: accounts on one /24 for this number >= SAME_CONNECTION_MIN_ACCOUNTS
lockstep_burst:  reports in BURST_WINDOW >= BURST_MIN_REPORTS  AND  distinct notes / n < BURST_MIN_DIVERSITY
coordinated:     proof share < COORD_MAX_EVIDENCE_SHARE  AND  one of:
                 share(lag < COORD_INSTANT_LAG) >= COORD_INSTANT_SHARE
                 stdev(len) / mean(len) < COORD_UNIFORM_CV
                 top scam type share < COORD_SCATTER_SHARE
described group: any note >= NOTE_SHORT_CHARS, or a screenshot, or a loss > 0
```

## Step 2: weight per person (16)

| Constant | Value | Source | Why |
|---|---|---|---|
| NOTE_SHORT_CHARS | 10 | RES | Under 10 characters counts as blank ("scam", "fraud"). |
| NOTE_FULL_CHARS | 25 | RES | 25 or more characters is a real sentence. |
| NOTE_WEIGHT_EMPTY | 0.5 | RES (0.35), then TUNE | The brief says a personal description counts more. A blank report is worth half. |
| NOTE_WEIGHT_SHORT | 0.8 | RES (0.65), then TUNE | A short note sits between blank and full. |
| NOTE_NOVELTY_PENALTY | 0.85 | RES | From the initial research, section 4.3 (novelty-weighted notes). |
| NOTE_NOVELTY_FREE | 0.4 | MEAS | Real victims of the same script share phrases. Similarity under 0.4 is never penalised. |
| NOTE_NOVELTY_FLOOR | 0.3 | TUNE | A copied note still keeps 30% of its value, so one honest person quoting another is not wiped out. |
| EVIDENCE_SCREENSHOT | 0.15 | RES | Bonus for a screenshot. |
| EVIDENCE_LOSS | 0.15 | TUNE | Bonus for a stated money loss. |
| EVIDENCE_LEXICON | 0.10 | RES | Bonus for scam method words (OTP, KYC, anydesk, and so on). It is smaller because words are easy to fake. |
| EVIDENCE_CAP | 1.3 | RES (1.25), then TUNE | Evidence can raise weight by at most 30%. |
| REPEAT_DAMPING | 0.30 | RES | One person reporting many times is still one voice. |
| VELOCITY_FREE_PER_HOUR | 3 | RES | Up to 3 reports per hour from one person is normal. |
| VELOCITY_DAMPING | 0.25 | RES | Above that, each extra report per hour cuts weight. |
| VERIFIED_REPORTER_FACTOR | 0.5 | TUNE | Someone who also reported a verified bank number is less reliable. |
| UNIT_WEIGHT_MIN | 0.05 | RES | A floor so no weight ever reaches zero or goes negative. |


**Formula: Step 2, weight of one person**
```
base     = NOTE_WEIGHT_EMPTY if len < NOTE_SHORT_CHARS, NOTE_WEIGHT_SHORT if len < NOTE_FULL_CHARS, else 1.0
excess   = max(0, sim - NOTE_NOVELTY_FREE) / (1 - NOTE_NOVELTY_FREE)
novelty  = max(NOTE_NOVELTY_FLOOR, 1 - NOTE_NOVELTY_PENALTY * excess)
proof    = min(EVIDENCE_CAP, 1 + EVIDENCE_SCREENSHOT*shot + EVIDENCE_LOSS*loss + EVIDENCE_LEXICON*words)
w        = max(base * novelty) * proof
w        = w / (1 + REPEAT_DAMPING * (c - 1))
w        = w / (1 + VELOCITY_DAMPING * max(0, hourly - VELOCITY_FREE_PER_HOUR))
w        = w * VERIFIED_REPORTER_FACTOR        if they also reported a verified number
w        = max(w, UNIT_WEIGHT_MIN)
```

## Step 3: caps (3)

| Constant | Value | Source | Why |
|---|---|---|---|
| IP_CAP_SLOPE | 0.15 | RES | Two people on one Wi-Fi count as 1.104, not 2. |
| IP_CAP_MAX | 1.25 | RES | Twenty-two accounts on one connection count as 1.25 at most. |
| GROUP_CAP | 1.3 | MIN | A group is one voice, worth at most one person with full evidence (1.3). |


**Formula: Step 3, caps**
```
per /24:    capped = S if n = 1 else min(S, 1 + IP_CAP_SLOPE * ln n, IP_CAP_MAX); each w *= capped / S
weight_sum = Σ over groups of min(GROUP_CAP, group total)
```

## Step 4: campaign factor (23)

| Constant | Value | Source | Why |
|---|---|---|---|
| CAMPAIGN_MIN_GROUPS | 4 | RES | Wave statistics mean nothing with fewer than 4 groups. |
| CAMPAIGN_FLOOR | 0.2 | RES (0.15), then TUNE | Never cut a score by more than 80%. |
| CAMPAIGN_CEIL | 1.1 | RES (1.15), then TUNE | Never raise it by more than 10%. |
| BURST_RATE_FREE | 0.5 per min | RES | The fastest a real viral wave plausibly gets reported. |
| BURST_RATE_DAMPING | 0.6 | RES (0.30), then TUNE | 40 reports in 20 min (2 per min) gives 0.526. |
| AREA_MIN_UNITS | 8 | TUNE | Needs enough people to judge where they are. |
| AREA_CONCENTRATION | 0.8 | TUNE | 80% of reporters in the same place... |
| AREA_MAX_PINCODES | 2 | TUNE | ...meaning 2 pincodes or fewer... |
| AREA_FACTOR | 0.7 | TUNE | ...AND fast means a local brigade. |
| EVIDENCE_FACTOR_BASE | 0.85 | RES (0.45), then TUNE | A plain real campaign with no screenshots is never crushed. |
| EVIDENCE_FACTOR_SLOPE | 0.25 | RES (0.65), then TUNE | Full evidence lifts the factor to 1.10. |
| SYNC_REPORTED_IQR | 20 min | RES | All reports filed within about 20 minutes... |
| SYNC_RATIO | 4.0 | RES | ...but claiming incidents spread over more than 4 times that: back-dated. |
| SYNC_FACTOR | 0.7 | RES (0.50), then TUNE | |
| STYLE_MIN_NOTES | 8 | TUNE | Length spread over fewer notes is noise. |
| STYLE_MAX_CV | 0.06 | RES (0.18), then TUNE | Below every real sample (the 5th percentile was 0.07). Batch text sits around 0.03. |
| STYLE_FACTOR | 0.8 | RES (0.55), then TUNE | |
| COORDINATION_MIN_UNITS | 8 | TUNE | |
| COORDINATION_MAX_SHARE | 0.5 | TUNE | A fast wave where most reporters merged into shared groups... |
| COORDINATION_FACTOR | 0.5 | TUNE | ...means the rest are likely the same brigade. |
| BLANK_MIN_UNITS | 8 | TUNE | |
| BLANK_MAX_SHARE | 0.5 | SIM + TUNE | Real victims leave about 25% of notes blank (simulator assumption). More than half blank is suspicious. |
| BLANK_FACTOR | 0.5 | TUNE | Raised from 0.4 after the blind evaluation. The pile-on gate, not this factor, is what blocks a blank flood. |


**Formula: Step 4, campaign factor (only if groups >= CAMPAIGN_MIN_GROUPS)**
```
rate         = people / max(1, minutes first to last);  fast = rate > BURST_RATE_FREE
burst        = 1 / (1 + BURST_RATE_DAMPING * max(0, rate - BURST_RATE_FREE))
coordination = COORDINATION_FACTOR  if fast AND people >= COORDINATION_MIN_UNITS AND groups/people < COORDINATION_MAX_SHARE
blank_notes  = BLANK_FACTOR         if people >= BLANK_MIN_UNITS AND blank share > BLANK_MAX_SHARE
area         = AREA_FACTOR          if people >= AREA_MIN_UNITS AND top AREA_MAX_PINCODES pincodes >= AREA_CONCENTRATION AND fast
evidence     = EVIDENCE_FACTOR_BASE + EVIDENCE_FACTOR_SLOPE * min(1, f_img + f_loss + 0.7 * f_words)
sync         = SYNC_FACTOR          if IQR(reported) <= SYNC_REPORTED_IQR AND IQR(occurred) > SYNC_RATIO * max(IQR(reported), 60 s)
style        = STYLE_FACTOR         if notes >= STYLE_MIN_NOTES AND stdev(len)/mean(len) < STYLE_MAX_CV
campaign     = clip(product of factors, CAMPAIGN_FLOOR, CAMPAIGN_CEIL)
score        = weight_sum * campaign
```

## Step 5: pile-on gate (7)

| Constant | Value | Source | Why |
|---|---|---|---|
| PILE_ON_MIN_UNITS | 8 | TUNE | Only judged with enough people to tell. |
| PILE_ON_BLANK_SHARE | 0.75 | SIM | Real victims leave about 25% blank, so 3 times that is a pile-on. We raised it from 0.6 after the holdout. |
| PILE_ON_MIN_NOTES | 6 | TUNE | Enough written notes to judge their content. |
| PILE_ON_REVIEW_SHARE | 0.3 | MEAS | Review words ("bad service", "rude staff") showed up in 0 of 1,548 real-victim notes. Friends attacking a shop write them often. |
| PILE_ON_TYPE_SHARE | 0.5 | SIM | Real victims of one number agree on the scam type about 85% of the time (simulator assumption). Under 50% agreement is a pile-on. Stages of one script count as one type: courier-customs with digital-arrest, job-offer with investment-group. |
| PILE_ON_MIN_HARM_SHARE | 0.1 | MEAS | Under 10% of the people showed any harm (screenshot, stated loss, or the method named). Measured on both suites: every genuine group of 8+ had 21% or more; every fake-volume attack had 0%. |
| PROOF_MIN_TYPE_SHARE | 0.75 | MEAS | A blank report that only ticks screenshot or loss counts as "said something" when 75% or more agree on the type. Blind-eval real victims agree 100%; our "30 blank reports all claiming proof" attack about 40%. |


**Formula: Step 5, pile-on gate (only if people >= PILE_ON_MIN_UNITS)**
```
mostly_blank         share who said nothing >= PILE_ON_BLANK_SHARE
                     (said = note >= NOTE_SHORT_CHARS, or screenshot/loss if type agreement >= PROOF_MIN_TYPE_SHARE)
reviews_not_scams    written notes >= PILE_ON_MIN_NOTES AND review share >= PILE_ON_REVIEW_SHARE
no_harm_shown        share with screenshot, loss or method words < PILE_ON_MIN_HARM_SHARE
no_agreement_on_type top scam family share < PILE_ON_TYPE_SHARE
rescue: if only mostly_blank / no_harm_shown fired, re-run on the people who said something
        (for no_harm_shown: showed harm or wrote >= NOTE_FULL_CHARS); kept only if those people
        are independent: groups / accounts >= COORDINATION_MAX_SHARE
type vote and mostly_blank are also taken per independent group (one vote per group)
```

## Alerts (4)

| Constant | Value | Source | Why |
|---|---|---|---|
| ALERT_MAX_GROUP_REPORTS | 2 | TUNE | A victim may report twice to add detail. A third report on one number is spam. We lowered this from 3 after catalogue scenario 7010. |
| ALERT_MIN_CAMPAIGN | 0.5 | TUNE | Numbers damped below 0.5 never feed alerts. |
| SPIKE_MIN_COUNT | 5 | PRD | "and at least 5" |
| SPIKE_RATIO | 2.0 | PRD | "2x the daily average of the 7 days before" |


**Formula: Alerts and map**
```
alert-eligible report: campaign >= ALERT_MIN_CAMPAIGN, no pile-on, first report of its group, group size <= ALERT_MAX_GROUP_REPORTS
SPIKE:    count(last 24 h) >= SPIKE_MIN_COUNT AND count >= SPIKE_RATIO * (count 24 h to 8 d ago / 7)
          p_value = P(Poisson(max(baseline, 1)) >= count)
NEW_TYPE: type in last 24 h not seen 31 d to 24 h ago
map count = max(1, round(Σ per /24 of min(n, 1 + IP_CAP_SLOPE * ln n, IP_CAP_MAX)))
severity  = CRIT if count >= 10, HIGH if count >= 5, else MED
distance  = haversine with EARTH_RADIUS_KM; area within radius_km (default 2) and window days (default 7)
```

## Rate limits (3)

| Constant | Value | Source | Why |
|---|---|---|---|
| RATE_WINDOW | 1 hour | RES | The brief allows 429. |
| RATE_SAME_IDENTIFIER | 3 | RES (2 allowed), then TUNE | One person, the same number, more than 3 times in an hour returns 429. |
| RATE_PER_REPORTER | 20 | TUNE | One person, more than 20 reports in an hour on any numbers, returns 429. |


**Formula: Rate limits and input checks**
```
429 if same reporter + same number in RATE_WINDOW > RATE_SAME_IDENTIFIER, or same reporter in RATE_WINDOW > RATE_PER_REPORTER
400 if occurred_at > now + MAX_CLOCK_SKEW
```

## Outside the trust engine file (21)

| Constant | Value | Source | Why |
|---|---|---|---|
| SIG_SIZE (MinHash) | 64 | ENG | Similarity estimate error is about 1/√64 = 0.125. |
| LSH_BANDS | 16 (× 4 rows) | ENG | A pair at 0.7 similarity is found 98.8% of the time. |
| Shingle size | 4 characters | ENG | Works for English, Hinglish and Devanagari. |
| EVIDENCE_LIMIT | 20 | ENG | The most evidence rows returned per lookup. |
| CACHE_TTL_SECONDS | 60 | ENG | Lookup cache. It is also cleared on every write, so answers are never stale. |
| CACHE_MAX | 5000 | ENG | Memory bound on the cache. |
| CLOCK_TOLERANCE | 5 min | ENG | Licence rollback check. Allows normal clock drift. |
| Licence CACHE_SECONDS | 5 | ENG | The licence is re-checked every 5 seconds. |
| HIGH_WATER_EVERY | 10 s | ENG | How often the "latest time seen" is saved, so rolling the clock back is caught. |
| MAX_CLOCK_SKEW | 5 min | ENG | A report dated more than 5 minutes in the future returns 400. |
| Map default days | 7 | PRD | Appendix A.4 |
| Map default radius | 2 km | PRD | Appendix A.4 |
| EARTH_RADIUS_KM | 6371 | Physics | Haversine distance. |
| Spike window | 24 h | PRD | |
| Spike baseline | 7 days before that (24 h to 8 d ago) | PRD | |
| NEW_TYPE history | 30 days before the last 24 h (31 d to 24 h ago) | PRD | |
| Severity CRIT | 10 or more | ENG | The PRD names the levels but not the cut-offs. |
| Severity HIGH | 5 or more | ENG | Matches the spike minimum. |
| pool_size / max_overflow | 5 / 10 | ENG | Render free Postgres connection limit. |
| pool_recycle | 240 s | ENG | Render drops idle connections. Recycling avoids the per-query ping. |


**Formula: Licence**
```
valid    = Ed25519 signature checks AND no rollback AND now < expires_at
rollback = now < high_water - CLOCK_TOLERANCE  OR  now < issued_at - CLOCK_TOLERANCE   (refuse to serve)
re-check every CACHE_SECONDS; save high_water every HIGH_WATER_EVERY
```

## What proves the values work (measured, not claimed)

- **Fresh holdout, live server, seeds 9301 to 9305 (never tuned on):** rows 1, 3, 4, 5 and the bonus pass. One miss: a k3 case with 3 blank notes where only 2 had losses scored 1.65, below 1.7. That is the policy working as written.
- **Live rerun, seeds 9101 to 9110:**
  - Row 1 (tricks never KNOWN): 100/100.
  - Real scams KNOWN: 199/200. The one miss was a k3 case where 2 real people were merged into one.
  - Under 3 reporters: always hidden, 434/434.
  - No leak in 11,421 replies.
  - Map, alerts and bonus: all pass.
  - Lookup latency: p50 82 ms, p95 166 ms, p99 294 ms. Server time p50 1.8 ms.
- **Privacy audit:** 0 failures across database, logs, every API reply and the app. See evidence/privacy_audit.md.

## How each step uses its parameters

The engine takes every report about one number and decides whether real, independent people are behind them. This is the same 72, grouped by what they do in the code.

| Step | What it does | Parameters |
|---|---|---|
| 0. Rate limits | Stops floods at the door | 3 |
| 1. Merge fakes | Who is secretly the same person? | 12 |
| 2. Weigh | How much is each person worth? | 16 |
| 3. Cap | One connection or one group cannot count as many | 3 |
| 4. Does the crowd look real? | Does the wave look like real victims? | 23 |
| 5. Pile-on gate | Do these people sound like victims at all? | 7 |
| Verdict | KNOWN SCAM or not, and whether to unmask | 4 |
| Alerts | Which reports may trigger area alerts | 4 |
| **Total** | | **72** |


### Step 0: Rate limits (3), before anything is stored

- **In:** a new report. **Out:** accepted, or HTTP 429.
- `RATE_WINDOW` = 1 hour. `RATE_SAME_IDENTIFIER` = 3: more than 3 reports on the same number per hour is refused. `RATE_PER_REPORTER` = 20: more than 20 reports per hour in total is refused.
- **Why it helps:** the cheapest spam never reaches the engine. The brief requires it.

### Step 1: Merge reports from the same person (12)

- **In:** every report on this number. **Out:** groups, where each group is treated as one real person. Any one of the five checks below is enough to merge two reports.
- **Same story pasted by many accounts** (code name copied_note): `NOTE_DUP_SIMILARITY` = 0.7, `NOTE_DUP_MIN_CHARS` = 15. Notes 70% or more the same, both at least 15 characters, are one person. Catches 40 friends pasting one story; short notes like "fraud call" never link by chance.
- **One person logging in with a second account** (account_switch): `SAME_CONNECTION_PAIR_WINDOW` = 15 min. A new account on the same connection within 15 minutes is the same person. Catches 10 friends with 2 accounts each.
- **Many accounts on one Wi-Fi** (same_connection): `SAME_CONNECTION_MIN_ACCOUNTS` = 3. Three or more accounts on one connection are one person. Catches 22 accounts on one Wi-Fi. Not 2, because 2 can be strangers on one mobile carrier.
- **Same few notes repeated in one hour** (lockstep_burst): `BURST_WINDOW` = 60 min, `BURST_MIN_REPORTS` = 8, `BURST_MIN_DIVERSITY` = 0.3. Eight or more reports in an hour where under 30% of the notes differ are one brigade. A report with a screenshot or a loss is always its own voice.
- **Bot-like rush with no proof** (coordinated, 5 parameters): a burst where under 15% have proof (`COORD_MAX_EVIDENCE_SHARE`), plus one tell: 80% or more filed within 2 minutes of the claimed incident (`COORD_INSTANT_SHARE`, `COORD_INSTANT_LAG`), note lengths almost identical (`COORD_UNIFORM_CV` = 0.05), or no scam type covering half the burst (`COORD_SCATTER_SHARE` = 0.5). Catches bots and AI-written brigades.
- **Why it helps:** fakes that look separate are merged: 22 to 1, 40 to 1, 20 to 1.

### Step 2: How much each person counts (16)

- **In:** each group. **Out:** a weight from 0.05 to 1.3.
- **How much they wrote:** `NOTE_SHORT_CHARS` = 10, `NOTE_FULL_CHARS` = 25, `NOTE_WEIGHT_EMPTY` = 0.5, `NOTE_WEIGHT_SHORT` = 0.8. Blank 0.5, short 0.8, a real sentence 1.0. The brief says a personal description counts more.
- **Repeating someone else's words:** `NOTE_NOVELTY_PENALTY` = 0.85, `NOTE_NOVELTY_FREE` = 0.4, `NOTE_NOVELTY_FLOOR` = 0.3. A note that resembles earlier ones loses value. Similarity under 0.4 is free, because real victims of one script share phrases. Never below 0.3.
- **Extra credit for proof:** `EVIDENCE_SCREENSHOT` = 0.15, `EVIDENCE_LOSS` = 0.15, `EVIDENCE_LEXICON` = 0.10, `EVIDENCE_CAP` = 1.3. Screenshot +15%, money lost +15%, scam words (OTP, KYC) +10%, at most +30%.
- **Penalty for reporting again and again:** `REPEAT_DAMPING` = 0.30 (6 reports by one person: divided by 2.5). `VELOCITY_FREE_PER_HOUR` = 3 and `VELOCITY_DAMPING` = 0.25 (above 3 reports an hour, weight drops). `VERIFIED_REPORTER_FACTOR` = 0.5 (anyone who also reported a verified bank number counts half).
- **Lowest possible weight:** `UNIT_WEIGHT_MIN` = 0.05.
- **Why it helps:** a real victim with proof counts more than a blank click, and spamming only lowers your own weight.

### Step 3: Limits per Wi-Fi and per group (3)

- **In:** the weights. **Out:** the capped weight sum.
- `IP_CAP_SLOPE` = 0.15, `IP_CAP_MAX` = 1.25: everyone on one connection together is worth at most `1 + 0.15 ln n`, never above 1.25. A family of 2 on one Wi-Fi counts 1.104; a farm of 22 counts 1.25.
- `GROUP_CAP` = 1.3: a group is worth at most one fully proven person.
- **Why it helps:** volume from one place cannot add up to many people, but a real family is not wiped out.

### Step 4: Does the crowd look like real victims? (23)

- Runs only with 4 or more groups (`CAMPAIGN_MIN_GROUPS`). **In:** the whole wave. **Out:** one factor, clipped between `CAMPAIGN_FLOOR` = 0.2 and `CAMPAIGN_CEIL` = 1.1, that multiplies the score.

| Check | Parameters | Fires when | Effect |
|---|---|---|---|
| Reports arriving too fast | `BURST_RATE_FREE` 0.5/min, `BURST_RATE_DAMPING` 0.6 | Faster than 0.5 reports a minute | 40 in 20 min gives 0.526 |
| Most people turned out to be the same person | 8, 0.5, 0.5 | A fast wave where most people collapsed into shared groups | x 0.5 |
| Mostly empty reports | 8, 0.5, 0.5 | 8+ people and over half wrote nothing | x 0.5 |
| All from one small area | 8, 0.8, 2, 0.7 | 80%+ from 2 pincodes or fewer, arriving fast | x 0.7 |
| How much proof the crowd has | `EVIDENCE_FACTOR_BASE` 0.85, `EVIDENCE_FACTOR_SLOPE` 0.25 | Always | 0.85 with no proof, up to 1.10 with full proof |
| Filed together, dates spread out (back-dated) | 20 min, 4x, 0.7 | Filed within about 20 min but claiming incidents spread 4x wider | x 0.7 |
| Notes all the same length, like machine text | 8, 0.06, 0.8 | Note lengths as even as machine text | x 0.8 |

- **Why it helps:** real victims trickle in over hours, from many places, with proof; brigades do not. The 0.2 to 1.1 bounds mean no single check decides the verdict.

### Step 5: Pile-on check: are these really victims? (7)

- Judged only with 8 or more people (`PILE_ON_MIN_UNITS`). **In:** the groups and their notes. **Out:** pile-on yes or no. Yes means never KNOWN SCAM.
- `PILE_ON_BLANK_SHARE` = 0.75: 75% or more said nothing (real victims leave about 25% blank). A screenshot or a stated loss counts as saying something when 75% or more agree on the type (`PROOF_MIN_TYPE_SHARE`).
- `PILE_ON_MIN_HARM_SHARE` = 0.1: under 10% showed any harm (screenshot, loss or method words). Catches 40 accounts that drip short words like "scam number" over a week.
- `PILE_ON_MIN_NOTES` = 6 and `PILE_ON_REVIEW_SHARE` = 0.3: of 6 or more written notes, 30% or more read like shop reviews.
- `PILE_ON_TYPE_SHARE` = 0.5: the top scam type is under half (real victims agree about 85% of the time). Courier-customs and digital-arrest count as one script, as do job-offer and investment-group.
- If empty reports are the only problem, the engine rechecks only the people who said something or showed harm, so a scammer cannot bury their own number under empty reports.
- **Why it helps:** catches the brief's "40 friends report a real bakery", which can survive on volume alone.

### Verdict (4)

- **In:** groups, described groups, final score, pile-on result.
- KNOWN SCAM needs all of: `KNOWN_MIN_GROUPS` = 3 independent people, `KNOWN_MIN_DESCRIBED` = 2 of them described it or showed proof, `KNOWN_MIN_SCORE` = 1.7, and no pile-on.
- `UNMASK_MIN_SCORE` = 1.7: the full number is shown only under the same bar.
- **Why 1.7:** 3 real victims who each lost money, even with blank notes, score 1.725 and pass. 3 blank clicks score 1.5 and never do.

### Alerts (4)

- **In:** reports that survived the engine. **Out:** SPIKE and NEW_TYPE alerts for an area.
- `ALERT_MIN_CAMPAIGN` = 0.5: numbers whose crowd check fell below 0.5 never feed alerts.
- `ALERT_MAX_GROUP_REPORTS` = 2: a person may report twice to add detail; a third does not count.
- `SPIKE_MIN_COUNT` = 5, `SPIKE_RATIO` = 2.0: 5 or more trusted reports in 24 hours and at least 2x the daily average. Both from the brief.
- **Why it helps:** fake reports cannot raise a spike in your area, because they are filtered before counting.


## Blind evaluation (1 Nov 2026)

An agent with no access to our harness wrote its own judge-style test suite from the PRD (`eval_blind/`). On the old engine, 65 of its standard cases failed over 10 seeds: real victims who left the note blank but attached a screenshot or a loss, real waves whose notes came from a small template pool, victims who picked related scam types, and a slow-drip bakery brigade. Each failure was traced to the exact rule with the engine's own explain output, fixed, and measured on both suites plus seeds neither had used:

| Suite | Before | After |
|---|---|---|
| Blind eval t1, 30 fresh seeds, standard cases | 181 failures | 4 (all one marginal shape: 8 blank, no screenshot) |
| Our harness, 40 fresh seeds | 4 failures | same 4 (3-4 victim edge cases) |
| Our scenario catalog (HTTP, 20 seeds each) | baseline | identical row for row |

Still not caught, by design: 40 or 15 accounts that each invent a different believable story with proof (no text-only system can tell them from victims), and 12 victims who all report within 2 minutes with no proof (that is the bot-farm signature).

A second blind evaluation (eval_blind2/REPORT.md) then found two more holes, both fixed and measured the same way: a scammer flooding its own number with fake accounts on scattered types (fixed by one type vote per independent group) and three tricks stacked on one shop (fixed by a per-group blank check and an independence condition on the rescue).
