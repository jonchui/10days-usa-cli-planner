# Progress

Updated: 2026-09-28 19:20 UTC

## Status

| milestone | state |
|---|---|
| Project scaffold, schema, tag taxonomy | done |
| Book 1 text | received (296-page PDF via iCloud link, stored in gitignored `source/`) |
| Exchanges logged with page + chapter + setting + hashtags | **146 verified** from book 1, all with PDF page numbers. The 10 recalled seeds are retired. |
| Categorize + pattern report | done, `reports/patterns.md` rewritten from real data (10 rules with page cites) |
| 80/20 test set | 35 records over the 7 categories that cover 92% of exchanges (`status`, `alert`, `ack`, `advise`, `calc`, `snark`, `interject`) |
| Eval harness + leaderboard | done, runs after every version; no-API replay backend + judge-file |
| Guppy v0.0 rules | run |
| Guppy v0.2 / v0.3 prompts | run blind on session credits (see run log) |
| Guppy v1.0 fine-tune | not started; `training/sft.jsonl` has 111 training examples (test set excluded) |

## Run log (book-1 test set, 35 verified records)

| version | match | judge | F1 | note |
|---|---|---|---|---|
| v0.0 rules | 0% | n/a | 0.03 | floor |
| v0.2 prompt | 2.9% | 34.3% | 0.17 | still says "Acknowledged"; the book never does |
| v0.3 prompt (data-derived rules) | 5.7% | 28.6% | 0.22 | gets the naval "Aye", interjections 2/5; judge fell because it invents specific figures and facts the book does not have (`ack` 80%, `advise`/`snark`/`status` 0% on both versions) |

Earlier runs against the 8 recalled seeds (v0.1 50%, v0.2 75%) are kept in
`results/leaderboard.md` for history but are not comparable: the gold text
there was from memory.

What the real numbers say: verbatim match with the book is a very hard target
for a prompt alone. The prompt fixes the *form* (100% bracketed, right
acknowledgement vocabulary, right length) but cannot know the *facts* (the
specific number, what the scan found). Facts are what fine-tuning on the
exchange log plus retrieval of the surrounding scene would supply. The judge
score is the better progress signal for prompt versions; match % is the
target for the fine-tuned model.

## What was wrong in the recalled seeds (now corrected by the text)

- GUPPI never says `[Acknowledged]` or `[Affirmative]` to an order in book 1. It says `[Aye]`, `[Aye sir]`, `[Done]`, `[Noted]`, `[By your command]`.
- GUPPI is funny from p.76 on (`[Aye aye sir]`, `[Already on the list. Bump it up?]`), not only in later books.
- The acronym line is answered to a silent query, p.39, not a spoken question.
- The number interjections are exact: `[117]`, `[483.957642]`, `[32]`, `[128]`, `[20 cm when not constrained]`, `[133 years ago]`.
- 7% of GUPPI lines are unsolicited caveats/objections (`advise`), a category the seeds did not have.

## Blockers (yours)

1. **Books 2–5.** Same iCloud-link route works. Each book is ~10 min of my time to extract, review and tag.
2. **API key (optional).** Only needed if you want CI to run the prompt eval itself. Blind runs on session credits work fine via the replay backend.

## ETAs

| quotes | grab | process | test |
|---|---|---|---|
| 10 | done | done | done |
| 100 | done (146 from book 1) | done | done |
| 1,000 | **corpus estimate: ~600–750 literal GUPPI lines across 5 books** (book 1 = 146). ~10 min per book once the file arrives | ~15 min per book | ~5 min per version per book |

Reaching 1,000 training rows will need ~300 augmented rows (paraphrased Bob
inputs over verified outputs, tagged `synthetic`); the test set stays
verified-only.

## Next actions

1. Books 2–5 → extract, review, tag (same pipeline).
2. Add scene retrieval to the prompt backend (give the model the previous 2–3 exchanges of the same scene) and re-run v0.4; expect the judge score to move, not match %.
3. Fine-tune on `training/sft.jsonl` (Bedrock custom model or open weights) → Guppy v1.0; re-test on the same 35 (then the cross-book) test set.
