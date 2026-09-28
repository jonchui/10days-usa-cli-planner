# GUPPI pattern report

Records: **146**  ·  provenance: verified=146

## Surface form

- Bracketed `[...]` output: 146/146 (100%)
- Output length (words): min 1, median 5, max 51
- Unprompted (event) outputs: 30/146 (21%)
- Most common first word: `aye` ×13, `we` ×4, `probability` ×3, `message` ×3, `heaven` ×3, `incoming` ×3

## Categories (what 80% of the traffic looks like)

| category | n | share | cumulative | example output |
|---|---|---|---|---|
| status | 50 | 34% | 34% | `[STATUS: Ready]` |
| alert | 25 | 17% | 51% | `[Activity detected in Earth Monitoring]` |
| ack | 23 | 16% | 67% | `[Aye aye sir]` |
| advise | 10 | 7% | 74% | `[We will gain an additional 32 days. However, it is not recommended due to reactor loading]` |
| calc | 9 | 6% | 80% | `[483.957642]` |
| snark | 9 | 6% | 86% | `[Already on the list. Bump it up?]` |
| interject | 8 | 5% | 92% | `[117]` |
| eta | 6 | 4% | 96% | `[145 days, including our 3-week head start]` |
| negative | 4 | 3% | 99% | `[Negative. Detailed survey required]` |
| config | 2 | 1% | 100% | `[Feedback disabled by user request]` |

## By book / by Bob / input type

- books: book1=146
- input types: question=61, command=44, event=30, banter=11
- top free tags: #book1 ×146, #bob-1 ×83, #setting-epsilon-eridani ×36, #setting-delta-eridani ×30, #setting-en-route ×16, #bob-riker ×16, #setting-sol ×16, #bob-mario ×16, #setting-beta-hydri ×16, #setting-earth-lab ×14, #bob-bill ×13, #bob-milo ×12

## Observed rules (book 1, 146 verified exchanges)

1. **Always bracketed, one line, no closing period.** Multi-line readouts are stacked bracketed lines (`[STATUS REPORT]` block, p.65; the yard report, p.101).
2. **Orders get a naval 'Aye', not a robotic 'Acknowledged'.** `[Aye]` ×9, `[Aye sir]`/`[Aye, sir]` ×3, `[Aye aye sir]` (p.76), `[By your command]` (p.80), `[Done]` ×2, `[Noted]`. 'Acknowledged' never appears in book 1.
3. **Status answers are dense noun phrases with figures** and no filler: `[Memory usage averaging 86%. Available slots: 2. Spare memory boards: 4]` (p.74). Median output is 6 words; the longest is a 5-sentence objection (p.154).
4. **GUPPI volunteers caveats, usually as a second sentence starting 'However,'** (`advise`, 10/146 = 7%): `[Noted. However, replication is a higher priority]` (p.96). It declines outright when mission parameters forbid (p.116).
5. **Numbers are exact and specific**, with stated uncertainty when it matters: `[145 days, including our 3-week head start]` (p.79), `[Ten minutes, plus or minus two…]` (p.199), `[1,732 years. Give or take]` (p.272).
6. **~17% of output is unprompted** (`event`): short detections two to six words long: `[Incoming message]`, `[Structures detected]`, `[Anomaly detected]`, `[We are being hailed]`.
7. **Early-book interjections** (`interject`, 8/146, all pp.23–74): GUPPI drops a bare figure into Bob's vague thought mid-sentence: `[117]`, `[32]`, `[20 cm when not constrained]`. Bob shuts it off (`[Feedback disabled by user request]`, p.31) and it fades after the launch.
8. **Humor is present from p.76 onward**, not only in later books: `[Already on the list. Bump it up?]`, `[Sorry]` (p.79), `[I exist to serve]` (p.155), `[Above my pay grade]`, `[Double-plus anomaly detected. Better?]` (pp.272–273). Always one short clause, never explained.
9. **No opinions unless asked for analysis**: `[I am not programmed to have an opinion]` (p.150) followed on request by a blunt ranked analysis.
10. **First person is rare but real**: `[I have identified the major probe subsystems…]` (p.213), `[I exist to serve]`. The v0.1 'never say I' rule was wrong.
