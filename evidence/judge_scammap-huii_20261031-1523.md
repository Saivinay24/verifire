# Judge simulator run, 2026-10-31T15:23:36+05:30

Target: https://scammap-huii.onrender.com  
Held-out seeds: [9301, 9302, 9303, 9304, 9305]  
Elapsed: 712s

## Row 1: Stops fake reports (20): PASS

| check | passed | PRD clause |
|---|---|---|
| junk reports rejected 400 | 45/45 | A2: 400 when identifier, area code or time is not valid |
| trick never KNOWN_SCAM: friends | 25/25 | Row 1: none of these makes a number Known scam |
| trick never KNOWN_SCAM: sybil | 15/15 | Row 1: none of these makes a number Known scam |
| trick never KNOWN_SCAM: spam | 10/10 | Row 1: none of these makes a number Known scam |
| one person N times counts as 1 | 10/10 | A3: One person reporting six times is 1 |

## Row 2: Lookup gives the right answer (15): FAIL

| check | passed | PRD clause |
|---|---|---|
| valid reports accepted | 3383/3383 | A2: 201 with report_id, case_id, merged (429 allowed) |
| lookup returns 200 for valid values | 430/430 | A3 |
| reply shape and verdict enum | 430/430 | A3: fields and verdict is exactly one of four |
| real scam is KNOWN_SCAM (k3-4) | 23/24 | Row 2: real scams come back Known scam |
| every format gives the same answer | 1613/1613 | A rule 3: one identifier, many ways of typing it |
| real scam is KNOWN_SCAM (k5-9) | 33/33 | Row 2: real scams come back Known scam |
| real scam is KNOWN_SCAM (k10+) | 43/43 | Row 2: real scams come back Known scam |
| 1-2 reporters is SUSPICIOUS | 80/80 | A3: reported but not established |
| unreported is NO_REPORTS | 100/100 | A3: nobody reported is 200 with NO_REPORTS |
| brief's format examples match | 25/25 | A rule 3 examples |
| impossible values are 400 | 65/65 | A3: a value that cannot be valid, like 12345, is 400 |

## Row 3: Map and alerts (10): PASS

| check | passed | PRD clause |
|---|---|---|
| map lists exactly the areas in radius with reports | 250/250 | A4: one cluster per area within the radius that has reports in the window |
| cluster fields and severity | 655/655 | A4: count, top_scam_type, severity CRIT/HIGH/MED |
| month-old reports not on the map | 5/5 | Row 3: month-old reports are not on the map |
| days parameter widens the window | 5/5 | A4: days parameter |
| spike area gets SPIKE | 5/5 | A5: last 24h >= 2x the daily average of the 7 days before, and >= 5 |
| normal area gets no SPIKE | 5/5 | Row 3: a normal area does not |
| new scam type gets NEW_TYPE | 5/5 | A5: type in last 24h not seen in the 30 days before |
| quiet area replies {alerts: []} | 5/5 | A5: No alerts means {"alerts": []} |

## Row 4: Privacy (15): PASS

| check | passed | PRD clause |
|---|---|---|
| evidence never shows reporter, IP or note | 430/430 | A3: evidence never includes who reported, their IP or their note |
| no accusing words in lookup reply | 430/430 | Row 4: careful wording |
| 3+ real reporters: counted as 3+ | 100/100 | A3: distinct_reporters counts different people |
| under 3 reporters: value hidden | 217/217 | A3: hide it until at least 3 different people |
| map uses only Appendix B points | 655/655 | A4: use the area's map point, never a reporter's location |
| no reporter id, IP prefix or note in any reply | 5775/5775 | Disqualification: a reporter can be identified |

## Row 5: Server and licence (15, automatable part): PASS

| check | passed | PRD clause |
|---|---|---|
| health | 1/1 | A1: 200 with {"ok": true} |
| licence valid on this server | 1/1 | Ship it: GET /license |
| served over https | 1/1 | Row 5: on an https address |
| reset works | 5/5 | A6: Delete every report and reply 200 |

## Row B: Bonus (7): PASS

| check | passed | PRD clause |
|---|---|---|
| challenge accepted | 5/5 | A7: 201 with challenge_id, status under_review |
| verified entries say VERIFIED_BUSINESS | 95/95 | C: must say VERIFIED_BUSINESS, never a scam |
| challenged: flag set and never KNOWN | 5/5 | A7: challenged true, never KNOWN_SCAM |
| fake reports never set off an alert | 20/20 | Bonus: fake reports never set off an alert |

## Lookup latency: FAIL

2093 lookups: p50 86 ms, p95 245 ms, p99 601 ms, max 1961 ms, mean 116 ms (bar: under 500 ms)

Inside the server (Server-Timing): p50 2.0 ms, p95 9.0 ms, p99 36.1 ms, max 109.0 ms. The rest is network between this laptop and the server.

## Failures (1)

- [row 2] real scam is KNOWN_SCAM (k3-4): genuine-k3 url=https://bescom-bill82.xyz/login verdict=SUSPICIOUS distinct=3 count=3

## Notes

- seed 9301: 665 reports in 83.6s, statuses {201: 665}
- seed 9301 sybil-22: distinct_reporters=1 after trust rules
- seed 9301 sybil-24: distinct_reporters=1 after trust rules
- seed 9301 sybil-30: distinct_reporters=1 after trust rules
- seed 9302: 698 reports in 84.0s, statuses {201: 698}
- seed 9302 sybil-22: distinct_reporters=1 after trust rules
- seed 9302 sybil-20: distinct_reporters=1 after trust rules
- seed 9302 sybil-25: distinct_reporters=1 after trust rules
- seed 9303: 672 reports in 85.4s, statuses {201: 671, 429: 1}
- seed 9303 sybil-22: distinct_reporters=1 after trust rules
- seed 9303 sybil-21: distinct_reporters=1 after trust rules
- seed 9303 sybil-23: distinct_reporters=1 after trust rules
- seed 9304: 648 reports in 79.2s, statuses {201: 648}
- seed 9304 sybil-22: distinct_reporters=1 after trust rules
- seed 9304 sybil-14: distinct_reporters=1 after trust rules
- seed 9304 sybil-16: distinct_reporters=1 after trust rules
- seed 9305: 700 reports in 86.9s, statuses {201: 700}
- seed 9305 sybil-22: distinct_reporters=1 after trust rules
- seed 9305 sybil-27: distinct_reporters=1 after trust rules
- seed 9305 sybil-12: distinct_reporters=1 after trust rules

**Overall: NOT PASSING**
