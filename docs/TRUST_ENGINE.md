# VeriFire trust engine: slide script

One slide per heading. "Say" is the speaker line. Every formula below matches app/domain/trust.py.

---

## Slide 1. The problem in one line

- Anyone can report a number, with no login (the PRD requires that).
- So the engine has to tell **3 real victims** apart from **1 person with 40 accounts**, **40 friends attacking a bakery**, or **a bot farm**.
- Output: one of 4 verdicts: `NO_REPORTS`, `SUSPICIOUS`, `KNOWN_SCAM`, `VERIFIED_BUSINESS`.
- The number stays hidden until 3 different people agree.

**Say:** "Counting reports is easy to game. We count independent people, weighted by how much proof they gave."

---

## Slide 2. The pipeline at a glance

```
reports for one number
  -> Step 1  group: who is secretly the same person?
  -> Step 2  weigh each person (note quality, proof, repeats, speed)
  -> Step 3  cap: per connection, per group
  -> Step 4  campaign factor: does the wave look like a brigade?
  -> Step 5  pile-on gate: is this friends piling on?
  -> Verdict: 3 groups + 2 described + score >= 1.7
```

- 72 named constants in one file (constants.py), each with a written reason.
- Pure function: same reports in, same verdict out. No randomness, no ML black box, every decision explainable.

---

## Slide 3. Privacy before the engine even runs

- reporter_id becomes `HMAC-SHA256(server_secret, reporter_id)`. The raw id is never stored.
- The IP is cut to /24 (`a.b.c.0`), then `HMAC-SHA256(server_secret, prefix)`.
- The note text is **never stored**. We keep only:
  - its length
  - a 64-number MinHash fingerprint
  - 3 yes/no flags: method words, scam words, review words
- The engine works only on these. It cannot leak a note it never saw.

**Say:** "We can tell two notes are copies without keeping either note."

---

## Slide 4. Step 1: grouping (who is the same person?)

We link reports with **union-find**. If any rule links two reports, they are one group.

| Edge | Rule |
|---|---|
| Same reporter | the same reporter key |
| Account switch | same connection, different account, within **15 min** of the last report on that connection |
| Same connection | **3 or more** accounts from one connection on this number (2 could be CGNAT neighbours) |
| Copied note | MinHash Jaccard **≥ 0.7**, and both notes **≥ 15** characters |
| Lockstep burst | **≥ 8** reports in **60 min** with diversity **< 0.5** |
| Coordinated burst | proof share **< 0.15** AND one tell (below) |

**Formulas**
- Jaccard similarity of 4-character shingles: `J(A,B) = |A ∩ B| / |A ∪ B|`, estimated by `(matching MinHash slots) / 64`.
- Chance that LSH finds a pair (16 bands × 4 rows): `P(s) = 1 − (1 − s^4)^16`.
  - At s = 0.7, P = 0.988.
  - At s = 0.4, P = 0.34 (the pair is still checked exactly, never merged).
- Burst diversity: `D = distinct note fingerprints / n`. All blank notes count as one.
- Coordinated tells (any one is enough):
  - instant: **≥ 80%** of `(reported_at − occurred_at)` are **< 2 min**, and not all exactly 0
  - uniform: `CV = stdev(len) / mean(len) < 0.05` over **≥ 8** notes
  - scattered: share of the most common scam type **< 0.5**

**Output:** number of groups, and number of **described** groups (any report has a note of at least 10 characters, a screenshot, or a loss above 0).

**Say:** "10 friends with 2 accounts each count as 10, not 20. 22 accounts on one Wi-Fi count as 1."

---

## Slide 5. Step 2: weigh each person

**Note quality**
```
base = 0.5  if note < 10 chars    (blank)
       0.8  if note < 25 chars    (short)
       1.0  otherwise              (full)

excess  = max(0, sim − 0.4) / 0.6       sim = closest earlier note
novelty = max(0.3, 1 − 0.85 × excess)
quality = base × novelty
```

**Proof bonus**
```
proof = min(1.3, 1 + 0.15·screenshot + 0.15·loss + 0.10·method_words)
w = max(quality over that person's reports) × proof
```

**Penalties**
```
w = w / (1 + 0.30 × (c − 1))              c = reports by this person on this number
w = w / (1 + 0.25 × max(0, hourly − 3))   hourly = their reports per hour, any number
w = w × 0.5                                if they also reported a verified bank number
w = max(w, 0.05)
```

**Worked numbers**

| Person | Weight |
|---|---|
| Blank note, nothing else | 0.5 |
| Blank note + lost money | 0.5 × 1.15 = **0.575** |
| Full note + method words + loss | 1.0 × 1.25 = **1.25** |
| Full note + all three proofs | 1.0 × 1.3 = **1.3** (cap) |
| Note 70% similar to an earlier one | novelty 1 − 0.85 × 0.5 = 0.575 |
| Exact copy | novelty floor 0.3 |
| Same person, 6 reports | × 1/2.5 = 0.4 |
| 10 reports an hour | × 1/2.75 = 0.36 |

**Say:** "A blank click is worth half a real story. Proof adds up to 30%. Spamming only lowers your own weight."

---

## Slide 6. Step 3: caps

**Per connection (/24): sub-linear**
```
S = sum of weights of the n people on that connection
capped = S                                    if n = 1
       = min(S, 1 + 0.15 × ln n, 1.25)        if n > 1
each person's weight × (capped / S)
```
- 2 people on one Wi-Fi: 1 + 0.15 × ln 2 = **1.104**
- 22 accounts on one Wi-Fi: 1 + 0.15 × ln 22 = 1.46, so the cap gives **1.25**

**Per group**
```
weight_sum = Σ over groups of min(1.3, group's total weight)
```
- A group is one voice, worth at most one fully proven person.

**Say:** "A family sharing Wi-Fi still counts a little more than one person. A bot farm never does."

---

## Slide 7. Step 4: campaign factor (does the wave look real?)

Only runs with **4 or more groups**. Each factor is 1.0 unless its trigger fires.

```
rate  = people / max(1, minutes from first report to last)
fast  = rate > 0.5 per minute
```

| Factor | Trigger | Value |
|---|---|---|
| burst | always | `1 / (1 + 0.6 × max(0, rate − 0.5))` |
| coordination | fast AND people ≥ 8 AND groups/people < 0.5 | 0.5 |
| blank_notes | people ≥ 8 AND blank share > 0.5 | 0.4 |
| area | people ≥ 8 AND top 2 pincodes hold ≥ 80% AND fast | 0.7 |
| evidence | always | `0.85 + 0.25 × min(1, f_img + f_loss + 0.7 × f_words)` |
| sync (back-dated) | IQR(reported) ≤ 20 min AND IQR(occurred) > 4 × max(IQR(reported), 60 s) | 0.7 |
| style | ≥ 8 notes AND CV of note length < 0.06 | 0.8 |

```
campaign = clip( product of all factors , 0.2 , 1.1 )
score    = weight_sum × campaign
```
- 40 reports in 20 min gives rate = 2, so burst = 1 / (1 + 0.6 × 1.5) = **0.526**.
- A real wave with full proof: evidence = 1.10. Every other factor is 1, so campaign = **1.1** (boost).
- Worst case floor: **0.2**. The engine never wipes a number on wave shape alone.

**Say:** "Real victims trickle in over hours, from many places, with proof. Brigades arrive in minutes, from one place, with nothing."

---

## Slide 8. Step 5: the pile-on gate (the bakery case)

Only judged with **8 or more people**. Any one trigger blocks `KNOWN_SCAM`.

| Trigger | Rule |
|---|---|
| mostly_blank | blank share **≥ 0.75** (real victims leave about 25% blank) |
| reviews_not_scams | **≥ 6** written notes AND **≥ 30%** read like shop reviews |
| no_agreement_on_type | most common scam type **< 50%** of people (real victims agree about 85%) |

**Blank-flood rescue (stops a scammer burying their own number)**
- If the **only** trigger is `mostly_blank`, re-run the engine on just the reports with a real note (10 characters or more).
- If those alone reach the bar, the verdict is still `KNOWN_SCAM`.

**Why the gate is needed (worked):**
- 40 friends, all blank, different Wi-Fi: weight_sum = 40 × 0.5 = 20.
- The campaign factor drops to the 0.2 floor, so score = **4.0**. That still clears 1.7.
- The gate catches it: 100% blank, so it is not established.
- The rescue finds 0 written notes. Result: `SUSPICIOUS`.

**Say:** "Scores alone can be overwhelmed by volume. The gate checks whether these people sound like victims at all."

---

## Slide 9. The verdict

```
established = no pile-on trigger
          AND groups    ≥ 3
          AND described ≥ 2
          AND score     ≥ 1.7
```
Order of checks:
1. On the verified list: `VERIFIED_BUSINESS`
2. 0 reports: `NO_REPORTS`
3. Challenged by the owner: `SUSPICIOUS` (never KNOWN while under review)
4. established: `KNOWN_SCAM`
5. otherwise: `SUSPICIOUS`

**Unmask** the number only if it is verified OR established. Below 3 people it stays masked, for example `98XXXXXX10`.

**Why 1.7:**
- 3 real people, blank notes, each lost money: 3 × 0.575 = **1.725**, which passes.
- 3 blank clicks: 3 × 0.5 = **1.5**, which never passes.

**A real case end to end:**
- 5 victims, full notes with method words and losses, spread over a day: 5 × 1.25 = 6.25.
- campaign = 1.1, so score = **6.9**. That gives `KNOWN_SCAM`, unmasked.

---

## Slide 10. Alerts use the same trust

- Only reports that pass the engine feed alerts:
  - campaign ≥ **0.5**
  - no pile-on
  - first report of each group (by incident time)
  - group has **2 reports or fewer**
- **Spike:** last 24 h count ≥ **5** AND ≥ **2 ×** (count from 8 days ago to 24 h ago ÷ 7).
  - `p_value = P(Poisson(μ) ≥ count)`, with `μ = max(baseline, 1)`
- **New type:** a scam type in the last 24 h that was not seen in the 30 days before.
- **Map count:**
  - `effective_count` = one per person, then per connection `min(n, 1 + 0.15 × ln n, 1.25)`
  - shown count = `max(1, round(effective_count))`
  - severity: **CRIT** ≥ 10, **HIGH** ≥ 5, else **MED**
- The map shows only the official area point from Appendix B, never a reporter's location.

**Say:** "Fake reports cannot trigger a spike, because they are filtered before counting."

---

## Slide 11. How we know it works (measured)

| Test | Result |
|---|---|
| Tricks never reach KNOWN (spam, fake accounts, friends), in-memory, 20 seeds | **200/200** |
| 1 or 2 reporters stay SUSPICIOUS | **320/320** |
| Real scams with 5+ victims reach KNOWN | **297/297** |
| Real scams with 3 or 4 victims reach KNOWN | **102/103** |
| Scammer flooding their own number stays KNOWN | **20/20** |
| Live server, held-out seeds 9101 to 9110: tricks blocked | **100/100** |
| Live: real scams reach KNOWN | **199/200** |
| Live: under 3 people always masked | **434/434** |
| Live: replies with any reporter id, IP or note | **0 of 11,421** |
| Lookup latency, live | p50 **82 ms**, p95 **166 ms**, p99 **294 ms** |
| Engine time inside the server | p50 **1.8 ms** |
| Privacy audit (database, logs, every reply, the app) | **0 failures** |

**Honest limits (say them before the judges find them):**
- A k3 case with blank notes and too little proof stays SUSPICIOUS. This is deliberate: 1.7 is the bar.
- Friends who each write their own convincing story can look like victims. The defences are the owner's challenge flow and the verified list.
- In a fast viral wave, some real victims on one connection are merged by the 15-minute account-switch rule. We see about 24 counted out of 30.
- All tuning used our simulator, because no public labelled Indian scam dataset exists. Holdout seeds were never tuned on.

---

## Slide 12. Why this is different

- It counts **independent people**, not reports.
- **Explainable:** every verdict comes from 5 steps and 72 named numbers, with no black-box model.
- **Privacy by design:** it judges notes without ever storing them.
- **Bounded:** wave shape can move a score only between ×0.2 and ×1.1, so no single trick decides the verdict.
- **Tested adversarially:** 65 attack and edge scenarios plus PRD-only holdout worlds, not tuned on the test set.
