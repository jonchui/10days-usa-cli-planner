# Labeling GUPPI exchanges in transcript windows (books made from audio)

Audio-derived text has no `[brackets]` and no quote marks, so GUPPI's lines must be picked out by
reading. Each window in `data/windows-b{N}.jsonl` is a scene in which GUPPI is named or speaks.
Run this as a blind labeling pass (one window per item, no answer key exists) with a model on
session credits or the API, then `scripts/ingest.py` the result.

## Prompt (system)

You are annotating scenes from Dennis E. Taylor's Bobiverse novels, transcribed from the
audiobook (so there are no quotation marks or brackets; names may be misspelled: "Guppy",
"Guppi", "GUPPI" are the same character). GUPPI is the ship's interface software. In the printed
books every GUPPI line is in square brackets and is terse: `[Aye]`, `[All systems nominal]`,
`[Contact. Unidentified vessel on intercept course]`, a bare number interjected into Bob's thought.

For the scene you are given, list every line GUPPI says, in order. For each, give:
- `output`: GUPPI's line exactly as the transcript has it (no paraphrase), wrapped in `[ ]`.
- `input`: what prompted it: the preceding line Bob (or the clone narrating) says to GUPPI,
  verbatim; or, if GUPPI speaks unprompted, `(event) <one-line description>`; or, for a bare figure
  GUPPI drops into Bob's thought, `(thought) <the thought with ___ where the number goes>`.
- `input_type`: `command`, `question`, `event`, or `banter`.
- `bob`: which clone is narrating (from the chapter heading).
- `confidence`: 0–1 that this sentence really is GUPPI and not narration or another character.
Skip narration about GUPPI ("Guppy rolled his eyes") and lines by other characters. If the scene
has no GUPPI line, return an empty list.

Return JSON: `{"window_id": "...", "exchanges": [{output, input, input_type, bob, confidence}]}`.

## After labeling

```bash
python scripts/windows_to_candidates.py data/labels-b5.jsonl --book 5   # -> data/candidates.jsonl with page/chapter from the window
python scripts/categorize.py --input data/candidates.jsonl --no-report
python scripts/ingest.py data/candidates.jsonl --min-confidence 0.7
```

Records from audio text get `provenance: "verified"` only after a human spot-check against the
audiobook; until then they are ingested with `provenance: "synthetic"` and
`notes: "audio transcript; wording is Whisper's"` so the headline score stays book-exact.
