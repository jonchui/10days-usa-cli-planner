# Guppy leaderboard

Headline = normalized match on VERIFIED test records. `all` includes recalled records whose gold text is unverified.

| run (UTC) | version | n test | verified match | all match | all exact | mean F1 | bracket ok | judge |
|---|---|---|---|---|---|---|---|---|
| 2026-09-28T18:09:00Z | `v0.0-rules` | 8 | n/a | 62.5% | 62.5% | 0.825 | 100.0% | n/a |
| 2026-09-28T19:13:25Z | `v0.0-rules` | 35 | 0.0% | 0.0% | 0.0% | 0.0 | 100.0% | n/a |
| 2026-09-28T19:07:02Z | `v0.1-cowork` | 8 | n/a | 50.0% | 50.0% | 0.739 | 100.0% | 62.5% |
| 2026-09-28T19:08:34Z | `v0.2-cowork` | 8 | n/a | 75.0% | 75.0% | 0.902 | 100.0% | 75.0% |

## Latest run by category (`v0.2-cowork`)

| category | n | match | F1 |
|---|---|---|---|
| alert | 1 | 100.0% | 1.0 |
| config | 3 | 100.0% | 1.0 |
| eta | 1 | 0.0% | 0.545 |
| execute | 1 | 100.0% | 1.0 |
| interject | 1 | 0.0% | 0.667 |
| status | 1 | 100.0% | 1.0 |
