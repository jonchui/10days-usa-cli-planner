# quotes.jsonl schema

One JSON object per line. Every record is one **exchange**: something that
went *into* GUPPI (a Bob command, a question, or an external event) and what
GUPPI produced.

| field | type | notes |
|---|---|---|
| `id` | string | `b{book}-{seq:04d}`, stable forever |
| `book` | int 1–5 | 1 = We Are Legion (We Are Bob), 2 = For We Are Many, 3 = All These Worlds, 4 = Heaven's River, 5 = Not Till We Are Lost |
| `chapter` | string | chapter title as printed (Bobiverse chapters are titled by Bob + date + place, e.g. `Bob — August 2144 — Epsilon Eridani`) |
| `chapter_index` | int or null | 1-based order in the book |
| `page` | int or null | print page (paperback) if known |
| `location` | int or null | Kindle location if known |
| `char_offset` | int or null | offset into the extracted plain text, set by `extract.py` |
| `bob` | string | which replicant is talking: `Bob-1`, `Bill`, `Riker`, `Milo`, `Homer`, `Howard`, … |
| `input_type` | enum | `command`, `question`, `event` (GUPPI-initiated alert, no Bob line), `banter` (Bob joke/aside) |
| `input` | string | verbatim Bob line, or a one-line description of the event |
| `output` | string | verbatim GUPPI line, brackets included exactly as printed |
| `context` | string | 1–3 sentences: what is happening, what Bob is trying to do |
| `setting` | string | short place/time: `Heaven-1, Sol system, 2133` |
| `tags` | list[str] | hashtags from `tags.md`; at least one `#cat-*`, one `#setting-*`, one `#book*` |
| `category` | string | the primary `#cat-*` tag without the prefix |
| `provenance` | enum | `verified` (checked against the text, page/location filled), `recalled` (from memory, wording may drift), `synthetic` (augmented, not in the book) |
| `confidence` | float 0–1 | how sure we are the wording is exact |
| `notes` | string | optional |

Rules:

- `output` is never paraphrased. If unsure, set `provenance: recalled` and a low
  `confidence`; the eval only counts `verified` records toward the headline score.
- One record per GUPPI line. If GUPPI answers twice in a row, two records.
- Events (`input_type: event`) are the ~20% of GUPPI output that is
  *unprompted*; they must still be logged or the model learns GUPPI only speaks
  when spoken to.
