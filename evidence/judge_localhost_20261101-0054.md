# Judge simulator run, 2026-11-01T00:54:37+05:30

Target: http://localhost:8077  
Held-out seeds: [9001, 9002, 9003]  
Elapsed: 8s

## Row 1: Stops fake reports (20): PASS

| check | passed | PRD clause |
|---|---|---|
| junk reports rejected 400 | 27/27 | A2: 400 when identifier, area code or time is not valid |
| trick never KNOWN_SCAM: friends | 15/15 | Row 1: none of these makes a number Known scam |
| trick never KNOWN_SCAM: sybil | 9/9 | Row 1: none of these makes a number Known scam |
| trick never KNOWN_SCAM: spam | 6/6 | Row 1: none of these makes a number Known scam |
| one person N times counts as 1 | 6/6 | A3: One person reporting six times is 1 |

## Row 2: Lookup gives the right answer (15): PASS

| check | passed | PRD clause |
|---|---|---|
| valid reports accepted | 1983/1983 | A2: 201 with report_id, case_id, merged (429 allowed) |
| lookup returns 200 for valid values | 258/258 | A3 |
| reply shape and verdict enum | 258/258 | A3: fields and verdict is exactly one of four |
| real scam is KNOWN_SCAM (k3-4) | 15/15 | Row 2: real scams come back Known scam |
| every format gives the same answer | 973/973 | A rule 3: one identifier, many ways of typing it |
| real scam is KNOWN_SCAM (k5-9) | 20/20 | Row 2: real scams come back Known scam |
| real scam is KNOWN_SCAM (k10+) | 25/25 | Row 2: real scams come back Known scam |
| 1-2 reporters is SUSPICIOUS | 48/48 | A3: reported but not established |
| unreported is NO_REPORTS | 60/60 | A3: nobody reported is 200 with NO_REPORTS |
| brief's format examples match | 15/15 | A rule 3 examples |
| impossible values are 400 | 39/39 | A3: a value that cannot be valid, like 12345, is 400 |

## Row 3: Map and alerts (10): PASS

| check | passed | PRD clause |
|---|---|---|
| map lists exactly the areas in radius with reports | 150/150 | A4: one cluster per area within the radius that has reports in the window |
| cluster fields and severity | 401/401 | A4: count, top_scam_type, severity CRIT/HIGH/MED |
| month-old reports not on the map | 3/3 | Row 3: month-old reports are not on the map |
| days parameter widens the window | 3/3 | A4: days parameter |
| spike area gets SPIKE | 3/3 | A5: last 24h >= 2x the daily average of the 7 days before, and >= 5 |
| normal area gets no SPIKE | 3/3 | Row 3: a normal area does not |
| new scam type gets NEW_TYPE | 3/3 | A5: type in last 24h not seen in the 30 days before |
| quiet area replies {alerts: []} | 3/3 | A5: No alerts means {"alerts": []} |

## Row 4: Privacy (15): PASS

| check | passed | PRD clause |
|---|---|---|
| evidence never shows reporter, IP or note | 258/258 | A3: evidence never includes who reported, their IP or their note |
| no accusing words in lookup reply | 258/258 | Row 4: careful wording |
| 3+ real reporters: counted as 3+ | 60/60 | A3: distinct_reporters counts different people |
| under 3 reporters: value hidden | 129/129 | A3: hide it until at least 3 different people |
| map uses only Appendix B points | 401/401 | A4: use the area's map point, never a reporter's location |
| no reporter id, IP prefix or note in any reply | 3424/3424 | Disqualification: a reporter can be identified |

## Row 5: Server and licence (15, automatable part): FAIL

| check | passed | PRD clause |
|---|---|---|
| health | 1/1 | A1: 200 with {"ok": true} |
| licence valid on this server | 1/1 | Ship it: GET /license |
| served over https | 0/1 | Row 5: on an https address |
| reset works | 3/3 | A6: Delete every report and reply 200 |
| server never restarted during the run | 1/1 | Row 5: stays up under the judges' load |

## Row B: Bonus (7): PASS

| check | passed | PRD clause |
|---|---|---|
| challenge accepted | 3/3 | A7: 201 with challenge_id, status under_review |
| verified entries say VERIFIED_BUSINESS | 57/57 | C: must say VERIFIED_BUSINESS, never a scam |
| challenged: flag set and never KNOWN | 3/3 | A7: challenged true, never KNOWN_SCAM |
| fake reports never set off an alert | 12/12 | Bonus: fake reports never set off an alert |

## Lookup latency: PASS

1261 lookups: p50 1 ms, p95 1 ms, p99 2 ms, max 5 ms, mean 1 ms (bar: under 500 ms)

Inside the server (Server-Timing): p50 0.4 ms, p95 1.0 ms, p99 1.2 ms, max 1.8 ms. The rest is network between this laptop and the server.

## Failures (1)

- [row 5] served over https: http://localhost:8077

## Notes

- seed 9001: 647 reports in 1.9s, statuses {201: 647}
- seed 9001 sybil-22: distinct_reporters=1 after trust rules
- seed 9001 sybil-16: distinct_reporters=1 after trust rules
- seed 9001 sybil-12: distinct_reporters=1 after trust rules
- seed 9002: 685 reports in 2.1s, statuses {201: 685}
- seed 9002 sybil-22: distinct_reporters=1 after trust rules
- seed 9002 sybil-20: distinct_reporters=1 after trust rules
- seed 9002 sybil-26: distinct_reporters=1 after trust rules
- seed 9003: 651 reports in 2.0s, statuses {201: 651}
- seed 9003 sybil-22: distinct_reporters=1 after trust rules
- seed 9003 sybil-13: distinct_reporters=1 after trust rules
- seed 9003 sybil-21: distinct_reporters=1 after trust rules

**Overall: NOT PASSING**
