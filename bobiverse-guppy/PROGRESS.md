# Progress

Updated: 2026-09-28 19:10 UTC

## Status

| milestone | state |
|---|---|
| Project scaffold, schema, tag taxonomy | done |
| First 10 exchanges logged with context + hashtags | done — **all 10 are `recalled`, none page-verified** |
| Categorize + pattern report | done, `reports/patterns.md` |
| 80/20 test set | done, 8 of 10 records across 6 categories |
| Eval harness + leaderboard | done, runs after every version (`make eval`, CI workflow) |
| Trial run | done — Guppy v0.0 (rules) 62.5% match on 8 test records, see `results/leaderboard.md` |
| Guppy v0.1 (prompt) | run blind on session credits: 50% match, 62.5% judge, F1 0.74. Failure mode: adds a second clause |
| Guppy v0.2 (prompt + length discipline) | run blind on session credits: 75% match, 75% judge, F1 0.90. Remaining misses are the two exact numbers |
| Verified quotes with page numbers | **blocked: need the ebook files in `source/`** |

## Blockers (yours)

1. **Book text.** Drop the epub/txt/pdf of each book into `bobiverse-guppy/source/`
   (iCloud Drive is not reachable from this cloud session, and Dropbox / Google
   Drive have no Bobiverse files). Kindle → Calibre → epub works.
2. **API key (optional).** Runs so far used this session's own model access via
   the replay backend (`results/outputs-*.json` + `results/judge-*.json`).
   Set `ANTHROPIC_API_KEY` only if you want CI to run the prompt eval on its own.

## ETAs

Grabbing = extracting + logging with chapter/page/tags. Processing = review + auto-tag + pattern report. Testing = one eval run per version.

| quotes | grab | process | test | notes |
|---|---|---|---|---|
| 10 | **done** (recalled) → ~5 min after book 1 arrives to swap in verified lines | done | done (rules); ~2 min for v0.1 once key is set | |
| 100 | ~10 min after book 1 arrives (`extract.py` is instant; the time is skimming false positives) | ~30 min human skim + auto-tag | ~3 min per version with API, seconds for rules | book 1 alone should yield 100+ bracketed GUPPI lines |
| 1,000 | ~2 h after all 5 books arrive (skim ~200/book) | ~2 h review + tag | ~15 min per version | **caveat:** the five books likely contain 300–600 literal GUPPI lines total. Reaching 1,000 training rows means augmenting with paraphrased inputs and synthetic exchanges tagged `synthetic`; the test set stays verified-only |

## Next actions (in order, no input needed from you once the books are in `source/`)

1. `extract.py` on book 1 → verify/replace the 10 recalled seeds, log the first 100.
2. Re-run `categorize.py`; rewrite the observed-rules section of `reports/patterns.md` from real data.
3. Run v0.1 (prompt) with judge; iterate to v0.2, v0.3 on the training split only.
4. Books 2–5 → 300+ verified; build `training/sft.jsonl`; fine-tune (Bedrock custom model or open-weights) → Guppy v1.0; re-test.

## Run log

| version | how | match | judge | F1 | note |
|---|---|---|---|---|---|
| v0.0 rules | local | 62.5% | n/a | 0.83 | rules written knowing the seeds, smoke test only |
| v0.1 prompt | blind, session credits | 50% | 62.5% | 0.74 | over-elaborates: appends ranges/qualifiers |
| v0.2 prompt | blind, session credits | 75% | 75% | 0.90 | first v0.2 draft leaked two test phrases into the prompt examples; discarded and re-run with neutral examples before scoring |

All against 8 `recalled` records. Numbers will move once the book text verifies or replaces them.
