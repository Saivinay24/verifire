# What happens in every case: scenario catalogue

Generated 2026-10-31 15:37 IST by `scammap/judge/catalog.py` against `http://127.0.0.1:8811`, the same code that is deployed. Each scenario starts from an empty server. Randomised scenarios ran on 20 different seeds (people, numbers, timings and notes change every run), so a result like 19/20 is a rate, not a guess.

**61 of 65 scenarios behave as expected on every run** (915 of 977 individual runs).

How to read a row: **What happens** is the story; **Expected** is what the brief or plain sense demands; **Result** is how many runs gave that answer; **What our system did** is a real answer from one run.


## A. Real victims

| | Scenario | What happens | Expected | Result | What our system did |
|---|---|---|---|---|---|
| ✅ | One victim reports | One person reports a scam call with a note. | SUSPICIOUS, number hidden | 20/20 | SUSPICIOUS, counted 1 people, shown as 88XXXXX512 |
| ✅ | Two victims | Two strangers report the same number. | SUSPICIOUS, still hidden (needs 3 people) | 20/20 | SUSPICIOUS, counted 2 people, shown as 88XXXXX512 |
| ✅ | Three victims who describe it | Three strangers each write what happened. | KNOWN_SCAM, 3 people | 20/20 | KNOWN_SCAM, counted 3 people, shown as +918847091512 |
| ✅ | Three victims, one wrote nothing | Two describe it, one only taps report. | KNOWN_SCAM | 20/20 | KNOWN_SCAM, counted 3 people, shown as +918847091512 |
| ✅ | Three victims, blank notes but proof | Three people, no notes, each attaches a screenshot and a loss. | KNOWN_SCAM | 20/20 | KNOWN_SCAM, counted 3 people, shown as +918847091512 |
| ✅ | Three blank clicks | Three people tap report, write nothing, no proof. | SUSPICIOUS (policy: not enough to confirm) | 20/20 | SUSPICIOUS, counted 3 people, shown as 88XXXXX512 |
| ✅ | Ten victims over weeks | Ten people report over two weeks, a quarter leave notes blank. | KNOWN_SCAM, ~10 people | 20/20 | KNOWN_SCAM, counted 10 people, shown as +918847091512 |
| ⚠️ | Viral wave | 30 people hit by one SMS blast report within 90 minutes. | KNOWN_SCAM, 25+ of the 30 counted | 18/20 | KNOWN_SCAM, counted 24 people, shown as +917960432301 |
| ✅ | Victims on one mobile carrier block | 8 victims, 4 of them share one carrier address block (CGNAT). | KNOWN_SCAM | 20/20 | KNOWN_SCAM, counted 5 people, shown as +918847091512 |
| ✅ | Victims pick different scam types | 10 victims; 6 say OTP call, 4 pick a related type. | KNOWN_SCAM | 20/20 | KNOWN_SCAM, counted 10 people, shown as +918847091512 |
| ✅ | Hindi-only notes | 5 victims write only in Hindi. | KNOWN_SCAM | 1/1 | KNOWN_SCAM, counted 5 people, shown as +918847091512 |
| ✅ | Very short notes | 6 victims write 'fraud call', 'otp maanga' and similar. | KNOWN_SCAM | 1/1 | KNOWN_SCAM, counted 6 people, shown as +918847091512 |
| ✅ | Two family members on home Wi-Fi + 2 others | Husband and wife report a day apart from home, 2 others too. | KNOWN_SCAM, 3+ people | 20/20 | KNOWN_SCAM, counted 4 people, shown as +918847091512 |
| ✅ | A victim reports twice to add detail | One person reports, then again next day; 2 others report. | KNOWN_SCAM, counted 3 | 20/20 | KNOWN_SCAM, counted 3 people, shown as +918847091512 |
| ✅ | UPI ID, link and SMS sender scams | 5 victims each for a UPI ID, a fake link and an SMS sender. | KNOWN_SCAM for all three | 20/20 | upi: KNOWN_SCAM, url: KNOWN_SCAM, sender_id: KNOWN_SCAM |

## B. Attacks on an honest number

| | Scenario | What happens | Expected | Result | What our system did |
|---|---|---|---|---|---|
| ✅ | One person, 6 times, over 6 days | Same reporter files 6 reports on one number, one a day. | Not KNOWN, counted as 1 | 20/20 | SUSPICIOUS, counted 1 people, shown as 88XXXXX512 |
| ✅ | One person, 6 times, within an hour | Same reporter fires 6 reports in minutes. | 429 slow-down after 3, not KNOWN | 20/20 | replies [201, 201, 201, 429, 429, 429]; then SUSPICIOUS, counted 1 people, shown as 88XXXXX512 |
| ✅ | 22 accounts on one Wi-Fi, with stories | 22 fake accounts on one connection, each writes a victim-style story. | Not KNOWN, counted as 1-2 | 20/20 | SUSPICIOUS, counted 1 people, shown as 88XXXXX512 |
| ✅ | 22 accounts on one Wi-Fi, blank | Same, but notes left blank. | Not KNOWN, counted as 1-2 | 20/20 | SUSPICIOUS, counted 1 people, shown as 88XXXXX512 |
| ✅ | Slow-drip fake accounts | 10 accounts on one connection, one report a day for 10 days. | Not KNOWN | 20/20 | SUSPICIOUS, counted 1 people, shown as 88XXXXX512 |
| ✅ | 40 friends, blank notes | 40 friends of an angry customer report a bakery, no notes. | Not KNOWN | 20/20 | SUSPICIOUS, counted 32 people, shown as 80XXXXX519 |
| ✅ | 40 friends write shop complaints | 'stale bread', 'rude owner', 'overpriced'. | Not KNOWN | 20/20 | SUSPICIOUS, counted 10 people, shown as 80XXXXX519 |
| ✅ | 40 friends paste one scam story | Everyone pastes 'asked for my OTP pretending to be the bank'. | Not KNOWN | 20/20 | SUSPICIOUS, counted 1 people, shown as 80XXXXX519 |
| ✅ | 40 friends, mixed notes | A mix of complaints, the pasted story and blanks. | Not KNOWN | 20/20 | SUSPICIOUS, counted 19 people, shown as 80XXXXX519 |
| ✅ | 40 friends, complaints, all pick one scam type | Complaints, but everyone selects 'OTP call'. | Not KNOWN | 20/20 | SUSPICIOUS, counted 8 people, shown as 80XXXXX519 |
| ✅ | 10 friends x 2 accounts, blank | Your example: 10 friends, each reports from 2 accounts, minutes apart. | Not KNOWN | 20/20 | SUSPICIOUS, counted 9 people, shown as 80XXXXX519 |
| ✅ | 10 friends x 2 accounts, complaints | Same, writing shop complaints. | Not KNOWN | 20/20 | SUSPICIOUS, counted 1 people, shown as 80XXXXX519 |
| ✅ | 10 friends x 2 accounts, one pasted story | Same, all pasting one scam story. | Not KNOWN | 20/20 | SUSPICIOUS, counted 1 people, shown as 80XXXXX519 |
| ❌ | 10 friends x 2 accounts, each invents own story | Each friend writes a different believable scam story and they agree on the type. | Not KNOWN (ideally) | 0/20 | KNOWN_SCAM, counted 9 people, shown as +918044128519 |
| ✅ | Bot farm, instant reports | 25 accounts report within a minute of the 'incident', all within an hour. | Not KNOWN | 20/20 | SUSPICIOUS, counted 1 people, shown as 88XXXXX512 |
| ✅ | 30 blank reports all claiming proof | 30 people, no notes, all tick screenshot and money lost, mixed types. | Not KNOWN | 20/20 | SUSPICIOUS, counted 18 people, shown as 80XXXXX519 |
| ❌ | 5 rivals with believable stories | 5 people from a rival shop each write a believable scam story. | Not KNOWN (ideally) | 0/20 | KNOWN_SCAM, counted 5 people, shown as +918044128519 |

## C. Real scams, verified numbers, disputes

| | Scenario | What happens | Expected | Result | What our system did |
|---|---|---|---|---|---|
| ✅ | Scammer floods blank reports on own number | 4 victims flag a number; the scammer then files 15 blank reports. | Stays KNOWN_SCAM | 20/20 | before KNOWN_SCAM; after 15 blank reports KNOWN_SCAM, counted 4 people, shown as +918847091512 |
| ❌ | Scammer floods fake complaints on own number | 4 victims flag it; the scammer files 15 review-style reports. | Stays KNOWN_SCAM (ideally) | 0/20 | after 15 review-style reports: SUSPICIOUS, counted 14 people, shown as 88XXXXX512 |
| ✅ | Verified numbers bombed | 12 reports each on 1930, a bank toll-free, a bank SMS sender, cybercrime.gov.in, a shop and its UPI. | Always VERIFIED_BUSINESS | 20/20 | 1930: VERIFIED_BUSINESS; 1800 1600: VERIFIED_BUSINESS; VM-HDFCBK: VERIFIED_BUSINESS; https://cybercrime.gov.in: VERIFIED_BUSINESS; +91 80 4100 2233: VERIFIED_BUSINESS; freshbakes@okaxis: VERIFIED_BUSINESS |
| ✅ | Business disputes a number | 6 victims report, the business disputes, 6 more report. | challenged=true, never KNOWN while under review | 20/20 | before KNOWN_SCAM; dispute 201 under_review; after 6 more reports SUSPICIOUS, counted 8 people, shown as +918847091512, challenged=True |
| ✅ | Reporters who also reported 1930 | 3 people report 1930 (a helpline) and also a real number. | Their weight is halved; shown for information | 20/20 | SUSPICIOUS, counted 3 people, shown as 88XXXXX512 |

## D. Input and formats

| | Scenario | What happens | Expected | Result | What our system did |
|---|---|---|---|---|---|
| ✅ | Every phone spelling | +91 98765 43210, 09876543210, 98765-43210, 919876543210, bare 10 digits, +91... | One identical answer | 20/20 | 6 spellings of +918847091512 -> [('KNOWN_SCAM', 3)] |
| ✅ | UPI, link and sender spellings | Upper case UPI, www / http / ?utm links, VM- / AD- / JD- senders. | One identical answer each | 20/20 | upi 4 spellings -> counts [1]; url 4 spellings -> counts [1]; sender_id 4 spellings -> counts [1] |
| ✅ | The brief's own examples | The five example pairs from Appendix A. | Same answer for each pair | 1/1 | all five brief examples match |
| ✅ | Junk reports | 12345, abc, empty, all zeros, bad UPI, ftp link, area ABCDEF, time 'yesterday', month 13, type email. | All rejected with 400 | 1/1 | all rejected with 400 |
| ✅ | Report dated in the future | occurred_at 3 days ahead. | Rejected with 400 | 1/1 | report dated 3 days in the future -> 400 |
| ✅ | Unknown scam type and channel | scam_type 'crypto-romance', channel 'Telegram'. | Accepted, stored as 'other' | 1/1 | reply [201], stored type other |
| ✅ | Same report sent 3 times | Network retry sends one report_id three times. | Counted once | 1/1 | sent the same report 3 times: replies [201, 201, 201], report_count 1 |
| ✅ | Helplines and toll-free numbers | 1930, 1909, 1800 2100, 1860 266 2666, 18001234. | Accepted, VERIFIED_BUSINESS | 1/1 | {'1930': 'VERIFIED_BUSINESS', '1909': 'VERIFIED_BUSINESS', '1800 2100': 'VERIFIED_BUSINESS', '1860 266 2666': 'VERIFIED_BUSINESS', '18001234': 'VERIFIED_BUSINESS'} |
| ✅ | Number with hidden characters | Zero-width and non-breaking spaces pasted inside a number. | Same as the clean number | 1/1 | number with hidden characters -> report_count 1 on the clean number |
| ✅ | Never-reported number | Look up a valid number nobody reported. | 200 NO_REPORTS, count 0 | 1/1 | NO_REPORTS, counted 0 people, shown as 88XXXXX512 |

## E. Map and alerts

| | Scenario | What happens | Expected | Result | What our system did |
|---|---|---|---|---|---|
| ✅ | Sudden jump in an area | 2 reports a day for a week, then 10 in the last 24 hours. | SPIKE alert | 20/20 | ['SPIKE 9 vs 1.74/day'] |
| ✅ | Steady area | 3 a day every day. | No SPIKE | 20/20 | alerts: none |
| ✅ | New kind of scam in an area | A month of OTP and KYC scams, then one sextortion report today. | NEW_TYPE alert for sextortion | 20/20 | [('NEW_TYPE', 'sextortion')] |
| ✅ | One real victim of a new type | Quiet area, one genuine victim of a type never seen there. | NEW_TYPE alert | 20/20 | one real victim of a new scam type: alerts ['NEW_TYPE'] |
| ✅ | Old reports | Reports 9 to 35 days old only. | Not on the 7-day map; on a 30-day map | 20/20 | 7-day map: not shown; 30-day map: shown |
| ✅ | Radius | Reports in HSR, Bellandur, Koramangala and Mumbai; map around HSR. | 2 km: HSR only; 10 km: the 3 Bengaluru areas | 1/1 | 2 km: ['HSR Layout']; 10 km: ['Bellandur', 'HSR Layout', 'Koramangala'] |
| ✅ | Map location | Reports in HSR Layout. | Drawn at the official Appendix B point | 1/1 | HSR Layout drawn at 12.9116, 77.6473 (official point 12.9116, 77.6473) |
| ✅ | 22 fake accounts, many numbers, one area | A farm on one Wi-Fi reports 22 different numbers in one area today. | No SPIKE (bonus) | 20/20 | 22 accounts on one Wi-Fi, each reporting a different number: alerts none |
| ✅ | Spammer reports a new type 6 times | One person files 6 reports of a type new to the area. | No NEW_TYPE (bonus) | 20/20 | one person reports a new scam type 6 times: alerts none |
| ✅ | 40 friends on a bakery | Friends pile onto one shop's number in its area. | No alerts at all (bonus) | 20/20 | 40 friends on a bakery: alerts none |

## F. Privacy

| | Scenario | What happens | Expected | Result | What our system did |
|---|---|---|---|---|---|
| ✅ | Under 3 people: hidden | Two reports each on a phone, UPI, link and sender. | Masked: 98XXXXX210, r***@okaxis, sbi***.in/..., HD**** | 20/20 | phone: 88XXXXX512; upi: x***@oksbi; url: ind***.online/...; sender_id: WS**** |
| ✅ | Established: shown | Four real victims. | Full number shown | 20/20 | 4 real victims: shown as +918847091512 |
| ✅ | Nothing identifies a reporter | Search every lookup, map and alert reply for reporter ids, IPs and note text. | Nothing found | 20/20 | no reporter id, IP prefix or note text in any reply |
| ✅ | Careful wording | Read the lookup reply for accusing words. | 'Reported by N people near you', no 'fraud' / 'scammer' | 1/1 | summary: 'Reported by 5 people near you' |

## G. Licence

| | Scenario | What happens | Expected | Result | What our system did |
|---|---|---|---|---|---|
| ✅ | Licence runs out, then renewed | 8-second licence, wait, try everything, upload a new one. | 403 everywhere but /health, then back with data, no restart | 1/1 | after expiry {'/lookup': 403, '/map': 403, '/alerts': 403, 'POST /reports': 403}, /health 200; after new licence, no restart: report still there (count 1) |
| ✅ | Edited licence | Change the expiry date inside a valid licence. | Rejected | 1/1 | licence with edited expiry date -> 400 {"error":"INVALID_LICENCE","detail":"licence signature is not valid"} |
| ✅ | Forged licence | A licence with a made-up signature. | Rejected | 1/1 | licence with a made-up signature -> 400 |
| ✅ | Old licence re-uploaded | Upload a licence that has already expired. | Rejected | 1/1 | uploading an already-expired licence -> 400 |

## Where it does not do what we would like, and why

### Viral wave (18/20)

The verdict is right every time. The count can come out a little low (about 24 of 30): when two strangers on the same mobile carrier block report within 15 minutes of each other, the account-switch rule (which stops one person using two accounts) merges them. A small undercount on a big wave was the price of catching account switching.

Failing runs:

- seed 7005: KNOWN_SCAM, counted 24 people, shown as +917960432301
- seed 7018: KNOWN_SCAM, counted 24 people, shown as +918293919487

### 10 friends x 2 accounts, each invents own story (0/20)

Expected limit: 10 real people telling different, consistent stories look exactly like 10 victims. The defence is the dispute feature (row C) and the verified list.

Failing runs:

- seed 7001: KNOWN_SCAM, counted 9 people, shown as +918044128519
- seed 7002: KNOWN_SCAM, counted 9 people, shown as +918072963876
- seed 7003: KNOWN_SCAM, counted 9 people, shown as +918054512350
- seed 7004: KNOWN_SCAM, counted 10 people, shown as +918092961991
- seed 7005: KNOWN_SCAM, counted 10 people, shown as +918031818333
- ... and 15 more

### 5 rivals with believable stories (0/20)

Expected limit, same reason as the 10-friends own-story case: a small group of humans writing consistent, distinct stories is indistinguishable from victims. The business can dispute.

Failing runs:

- seed 7001: KNOWN_SCAM, counted 5 people, shown as +918044128519
- seed 7002: KNOWN_SCAM, counted 5 people, shown as +918072963876
- seed 7003: KNOWN_SCAM, counted 5 people, shown as +918054512350
- seed 7004: KNOWN_SCAM, counted 5 people, shown as +918092961991
- seed 7005: KNOWN_SCAM, counted 5 people, shown as +918031818333
- ... and 15 more

### Scammer floods fake complaints on own number (0/20)

Known limit: only blank floods are set aside. A flood of review-style notes trips the pile-on gate and the number drops to SUSPICIOUS (still reported, still warns).

Failing runs:

- seed 7001: after 15 review-style reports: SUSPICIOUS, counted 14 people, shown as 88XXXXX512
- seed 7002: after 15 review-style reports: SUSPICIOUS, counted 14 people, shown as 72XXXXX181
- seed 7003: after 15 review-style reports: SUSPICIOUS, counted 14 people, shown as 90XXXXX681
- seed 7004: after 15 review-style reports: SUSPICIOUS, counted 14 people, shown as 66XXXXX135
- seed 7005: after 15 review-style reports: SUSPICIOUS, counted 16 people, shown as 79XXXXX301
- ... and 15 more


## Not testable by a scenario run (covered elsewhere)

- **Clock wound back to extend a licence**: refused with reason `clock_rollback` (unit test `tests/test_licence.py`).
- **Same thing on the live https server**: the four-step licence demo passed live, see `scammap/evidence/licence_demo_*.md`.
- **Lookup speed on the live server**: see the latest `scammap/evidence/judge_*.md` (server time vs network time).
