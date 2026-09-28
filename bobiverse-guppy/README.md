# bobiverse-guppy

Goal: a model that answers exactly the way GUPPI does in Dennis E. Taylor's
Bobiverse, given the same inputs Bob gives it. This folder is the whole
pipeline: **log → categorize → test → train → re-test**.

```
data/quotes.jsonl        the log: one Bob→GUPPI exchange per line, with chapter, page, setting, hashtags
data/schema.md           field definitions
data/tags.md             hashtag taxonomy (#cat-*, #setting-*, #book*, #bob-*)
data/testset.json        the 80/20 representative test set (generated)
reports/patterns.md      what GUPPI's outputs have in common (generated)
guppy/rules.py           Guppy v0.0 — rule baseline, no model, runs anywhere
guppy/prompts/v0.1.md    Guppy v0.1 — system prompt for a frontier model (Claude API)
guppy/api_backend.py     prompt backend + LLM judge
scripts/extract.py       book file (epub/txt/pdf) → candidate exchanges with chapter/page/location
scripts/categorize.py    auto-tags + pattern report
scripts/ingest.py        merge reviewed candidates into the log
scripts/select_testset.py  pick the categories covering 80% of traffic, sample from each
scripts/run_eval.py      run a Guppy version on the test set, write results + leaderboard
training/build_sft.py    export chat-format SFT file (excludes the test set)
results/leaderboard.md   every run, match % per version
PROGRESS.md              status and ETAs
```

## Daily loop

```bash
cd bobiverse-guppy
make all                     # tag → testset → pytest → rules eval
make eval-prompt VERSION=v0.1   # needs ANTHROPIC_API_KEY; scores prompt-based Guppy + LLM judge
```

Every Guppy version = a prompt file (or later a fine-tuned model id). Run
`run_eval.py` after each one; the leaderboard keeps the history. CI
(`.github/workflows/guppy-eval.yml`) runs the tests and the rules eval on
every push, and the prompt eval when the `ANTHROPIC_API_KEY` secret exists.

## Getting to verified quotes

Put your own ebook in `source/` (gitignored) and run:

```bash
python scripts/extract.py source/book1-we-are-legion.epub --book 1
python scripts/categorize.py --input data/candidates.jsonl --no-report
# skim data/candidates.jsonl, delete false positives
python scripts/ingest.py data/candidates.jsonl --min-confidence 0.8
make all
```

Only `provenance: verified` records count toward the headline score. Book 1
is done: 146 verified exchanges with PDF page numbers (the 10 `recalled`
bootstrap seeds were retired once the text arrived).

## Running a Guppy version without an API key (replay backend)

Any model can be scored: generate answers for `results/inputs-testset.json`
(prompts only, no gold), save them as `{id: output}` JSON, optionally grade
them with the judge prompt in `guppy/api_backend.py` into `{id: true/false}`,
then:

```bash
python scripts/run_eval.py --backend replay:results/outputs-v0.3-cowork.json \
    --judge-file results/judge-v0.3-cowork.json --label v0.3-cowork
```

`format_input()` shows the model only the text *before* the exchange, with
earlier GUPPI lines redacted, so no test record leaks another's answer. New
prompt versions are leak-checked against the test set before they are run.

## Scoring

| metric | meaning |
|---|---|
| exact | byte-identical to the book line |
| match (headline) | identical after lowercasing and stripping brackets/punctuation/whitespace |
| F1 | token overlap, partial credit |
| bracket ok | model used the `[...]` form when the book did |
| judge | LLM says the line could stand in for the original (same info, same register) |

## Copyright note

The book text stays on your machine (`source/` is gitignored). The log holds
only short dialogue lines with citations, for a personal research project.
