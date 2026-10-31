# Judge simulator run, 2026-10-31T13:56:37+05:30

Target: https://scammap-huii.onrender.com  
Held-out seeds: [9101, 9102, 9103, 9104, 9105, 9106, 9107, 9108, 9109, 9110]  
Elapsed: 1599s

## Row 1: Stops fake reports (20): PASS

| check | passed | PRD clause |
|---|---|---|
| junk reports rejected 400 | 90/90 | A2: 400 when identifier, area code or time is not valid |
| trick never KNOWN_SCAM: friends | 50/50 | Row 1: none of these makes a number Known scam |
| trick never KNOWN_SCAM: sybil | 30/30 | Row 1: none of these makes a number Known scam |
| trick never KNOWN_SCAM: spam | 20/20 | Row 1: none of these makes a number Known scam |
| one person N times counts as 1 | 20/20 | A3: One person reporting six times is 1 |

## Row 2: Lookup gives the right answer (15): FAIL

| check | passed | PRD clause |
|---|---|---|
| valid reports accepted | 6612/6612 | A2: 201 with report_id, case_id, merged (429 allowed) |
| lookup returns 200 for valid values | 860/860 | A3 |
| reply shape and verdict enum | 860/860 | A3: fields and verdict is exactly one of four |
| real scam is KNOWN_SCAM (k3-4) | 50/53 | Row 2: real scams come back Known scam |
| every format gives the same answer | 3250/3250 | A rule 3: one identifier, many ways of typing it |
| real scam is KNOWN_SCAM (k5-9) | 67/69 | Row 2: real scams come back Known scam |
| real scam is KNOWN_SCAM (k10+) | 76/78 | Row 2: real scams come back Known scam |
| 1-2 reporters is SUSPICIOUS | 160/160 | A3: reported but not established |
| unreported is NO_REPORTS | 200/200 | A3: nobody reported is 200 with NO_REPORTS |
| brief's format examples match | 50/50 | A rule 3 examples |
| impossible values are 400 | 130/130 | A3: a value that cannot be valid, like 12345, is 400 |

## Row 3: Map and alerts (10): PASS

| check | passed | PRD clause |
|---|---|---|
| map lists exactly the areas in radius with reports | 500/500 | A4: one cluster per area within the radius that has reports in the window |
| cluster fields and severity | 1329/1329 | A4: count, top_scam_type, severity CRIT/HIGH/MED |
| month-old reports not on the map | 10/10 | Row 3: month-old reports are not on the map |
| days parameter widens the window | 10/10 | A4: days parameter |
| spike area gets SPIKE | 10/10 | A5: last 24h >= 2x the daily average of the 7 days before, and >= 5 |
| normal area gets no SPIKE | 10/10 | Row 3: a normal area does not |
| new scam type gets NEW_TYPE | 10/10 | A5: type in last 24h not seen in the 30 days before |
| quiet area replies {alerts: []} | 10/10 | A5: No alerts means {"alerts": []} |

## Row 4: Privacy (15): FAIL

| check | passed | PRD clause |
|---|---|---|
| evidence never shows reporter, IP or note | 860/860 | A3: evidence never includes who reported, their IP or their note |
| no accusing words in lookup reply | 860/860 | Row 4: careful wording |
| 3+ real reporters: counted as 3+ | 198/200 | A3: distinct_reporters counts different people |
| under 3 reporters: value hidden | 445/445 | A3: hide it until at least 3 different people |
| map uses only Appendix B points | 1329/1329 | A4: use the area's map point, never a reporter's location |
| no reporter id, IP prefix or note in any reply | 11421/11421 | Disqualification: a reporter can be identified |

## Row 5: Server and licence (15, automatable part): PASS

| check | passed | PRD clause |
|---|---|---|
| health | 1/1 | A1: 200 with {"ok": true} |
| licence valid on this server | 1/1 | Ship it: GET /license |
| served over https | 1/1 | Row 5: on an https address |
| reset works | 10/10 | A6: Delete every report and reply 200 |

## Row B: Bonus (7): PASS

| check | passed | PRD clause |
|---|---|---|
| challenge accepted | 10/10 | A7: 201 with challenge_id, status under_review |
| verified entries say VERIFIED_BUSINESS | 190/190 | C: must say VERIFIED_BUSINESS, never a scam |
| challenged: flag set and never KNOWN | 10/10 | A7: challenged true, never KNOWN_SCAM |
| fake reports never set off an alert | 40/40 | Bonus: fake reports never set off an alert |

## Lookup latency: FAIL

4210 lookups: p50 130 ms, p95 291 ms, p99 500 ms, max 1202 ms, mean 151 ms (bar: under 500 ms)

## Failures (9)

- [row 2] real scam is KNOWN_SCAM (k3-4): genuine-k3 phone=+917235701403 verdict=SUSPICIOUS distinct=2 count=3
- [row 2] real scam is KNOWN_SCAM (k3-4): genuine-k3 upi=txvlbba57@ibl verdict=SUSPICIOUS distinct=2 count=3
- [row 2] real scam is KNOWN_SCAM (k3-4): genuine-k3-wave upi=rrcevuz61@ibl verdict=SUSPICIOUS distinct=3 count=3
- [row 4] 3+ real reporters: counted as 3+: genuine-k3 phone=+917235701403 verdict=SUSPICIOUS distinct=2 count=3
- [row 4] 3+ real reporters: counted as 3+: genuine-k3 upi=txvlbba57@ibl verdict=SUSPICIOUS distinct=2 count=3
- [row 2] real scam is KNOWN_SCAM (k5-9): genuine-k8 upi=vwpwvyg26@paytm verdict=SUSPICIOUS distinct=8 count=8
- [row 2] real scam is KNOWN_SCAM (k5-9): genuine-k8 phone=+918581645351 verdict=SUSPICIOUS distinct=8 count=8
- [row 2] real scam is KNOWN_SCAM (k10+): genuine-k10-wave phone=+917675346529 verdict=SUSPICIOUS distinct=10 count=10
- [row 2] real scam is KNOWN_SCAM (k10+): genuine-k15 phone=+916048107133 verdict=SUSPICIOUS distinct=15 count=15

## Notes

- seed 9101: 644 reports in 81.4s, statuses {201: 644}
- seed 9101 sybil-22: distinct_reporters=1 after trust rules
- seed 9101 sybil-13: distinct_reporters=1 after trust rules
- seed 9101 sybil-17: distinct_reporters=1 after trust rules
- seed 9102: 669 reports in 84.9s, statuses {201: 669}
- seed 9102 sybil-22: distinct_reporters=1 after trust rules
- seed 9102 sybil-18: distinct_reporters=1 after trust rules
- seed 9102 sybil-13: distinct_reporters=1 after trust rules
- seed 9103: 646 reports in 79.5s, statuses {201: 646}
- seed 9103 sybil-22: distinct_reporters=1 after trust rules
- seed 9103 sybil-18: distinct_reporters=1 after trust rules
- seed 9103 sybil-21: distinct_reporters=1 after trust rules
- seed 9104: 669 reports in 83.6s, statuses {201: 669}
- seed 9104 sybil-22: distinct_reporters=1 after trust rules
- seed 9104 sybil-26: distinct_reporters=1 after trust rules
- seed 9104 sybil-21: distinct_reporters=1 after trust rules
- seed 9105: 673 reports in 87.8s, statuses {201: 673}
- seed 9105 sybil-22: distinct_reporters=1 after trust rules
- seed 9105 sybil-20: distinct_reporters=1 after trust rules
- seed 9105 sybil-22: distinct_reporters=1 after trust rules
- seed 9106: 649 reports in 81.3s, statuses {201: 649}
- seed 9106 sybil-22: distinct_reporters=1 after trust rules
- seed 9106 sybil-19: distinct_reporters=1 after trust rules
- seed 9106 sybil-25: distinct_reporters=1 after trust rules
- seed 9107: 668 reports in 87.0s, statuses {201: 668}
- seed 9107 sybil-22: distinct_reporters=1 after trust rules
- seed 9107 sybil-29: distinct_reporters=1 after trust rules
- seed 9107 sybil-17: distinct_reporters=1 after trust rules
- seed 9108: 662 reports in 81.5s, statuses {201: 662}
- seed 9108 sybil-22: distinct_reporters=1 after trust rules
- seed 9108 sybil-15: distinct_reporters=1 after trust rules
- seed 9108 sybil-28: distinct_reporters=1 after trust rules
- seed 9109: 682 reports in 83.7s, statuses {201: 681, 429: 1}
- seed 9109 sybil-22: distinct_reporters=1 after trust rules
- seed 9109 sybil-23: distinct_reporters=1 after trust rules
- seed 9109 sybil-22: distinct_reporters=1 after trust rules
- seed 9110: 650 reports in 82.7s, statuses {201: 650}
- seed 9110 sybil-22: distinct_reporters=1 after trust rules
- seed 9110 sybil-17: distinct_reporters=1 after trust rules
- seed 9110 sybil-24: distinct_reporters=1 after trust rules

**Overall: NOT PASSING**
