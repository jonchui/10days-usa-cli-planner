# Progress

Updated: 2026-09-28

## Status

| milestone | state |
|---|---|
| Project scaffold, schema, tag taxonomy | done |
| First 10 exchanges logged with context + hashtags | done — **all 10 are `recalled`, none page-verified** |
| Categorize + pattern report | done, `reports/patterns.md` |
| 80/20 test set | done, 8 of 10 records across 6 categories |
| Eval harness + leaderboard | done, runs after every version (`make eval`, CI workflow) |
| Trial run | done — Guppy v0.0 (rules) 62.5% match on 8 test records, see `results/leaderboard.md` |
| Guppy v0.1 (prompt on Claude API) | written, **not run: no `ANTHROPIC_API_KEY` in this environment** |
| Verified quotes with page numbers | **blocked: need the ebook files in `source/`** |

## Blockers (yours)

1. **Book text.** Drop the epub/txt/pdf of each book into `bobiverse-guppy/source/`
   (iCloud Drive is not reachable from this cloud session, and Dropbox / Google
   Drive have no Bobiverse files). Kindle → Calibre → epub works.
2. **API key.** Set `ANTHROPIC_API_KEY` (locally or as a GitHub secret) to run
   v0.1 and the LLM judge.

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
