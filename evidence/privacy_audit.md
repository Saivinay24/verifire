# Privacy audit, 2026-10-31 20:33 IST

Target: `http://localhost:8077`, seeds [9001, 9002] (1332 reports loaded), database and server log inspected directly.

| Check | Passed |
|---|---|
| ✅ 1. database holds no reporter id, IP prefix or note text | 10/10 |
| ✅ 1. reports table has no location or free-text column | 2/2 |
| ✅ 2. stored keys are keyed hashes, not recomputable plain hashes | 2/2 |
| ✅ 3. server logs hold no reporter id, IP, note or reported identifier | 1/1 |
| ✅ 3. server logs were actually written during the audit | 1/1 |
| ✅ 4. alert replies leak nothing | 50/50 |
| ✅ 4. attacked numbers are never unmasked (spam, fake accounts, friends) | 80/80 |
| ✅ 4. city feed has only time, channel, type, area, masked value | 1681/1681 |
| ✅ 4. city feed times are rounded to the hour | 1681/1681 |
| ✅ 4. city sheet never shows a number the lookup keeps hidden | 150/150 |
| ✅ 4. city sheet replies leak nothing | 150/150 |
| ✅ 4. every city sheet point is an official area point | 974/974 |
| ✅ 4. every map point is an official area point | 1685/1685 |
| ✅ 4. evidence has only time, channel, type, area | 3434/3434 |
| ✅ 4. hidden under 3 people (attack) | 62/62 |
| ✅ 4. hidden under 3 people (low-report) | 172/172 |
| ✅ 4. hidden under 3 people (unreported) | 188/188 |
| ✅ 4. lookup replies leak nothing | 688/688 |
| ✅ 4. map replies leak nothing | 150/150 |
| ✅ 4. no accusing words in city sheet replies | 150/150 |
| ✅ 4. no accusing words in lookup replies | 688/688 |
| ✅ 4. other replies leak nothing | 8/8 |
| ✅ 4. report replies leak nothing | 1332/1332 |
| ✅ 4. stats never name a number | 6/6 |
| ✅ 4. stats replies leak nothing | 6/6 |
| ✅ 5. error replies never echo the input | 8/8 |
| ✅ 6. 'near me' picks the nearest area on the phone itself | 1/1 |
| ✅ 6. app never sends coordinates (only the area code) | 1/1 |
| ✅ 6. no accusing words anywhere in the app (English and Hindi) | 1/1 |
| ✅ 6. no login, accounts or tracking in the app | 1/1 |

**ALL PRIVACY CHECKS PASS**

## Failures

None.
