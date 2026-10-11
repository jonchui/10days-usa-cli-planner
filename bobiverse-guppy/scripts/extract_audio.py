#!/usr/bin/env python3
"""Candidate GUPPI exchanges from a transcript-derived text (no [brackets], no quote marks).

Audiobook text (SyncRead's text.pdf / text.txt from Whisper) has none of the typography that
extract.py relies on, so GUPPI's lines cannot be found by pattern. This script does the part
that can be automated: it finds every scene in which GUPPI is addressed or named and cuts a
window of sentences around it, with the PDF page and the spoken chapter heading, into
data/windows-b{N}.jsonl. An LLM pass (scripts/label_windows.md) then marks, inside each
window, which sentences are GUPPI's output and what Bob's input was; the result is reviewed and
ingested like any candidates file.

    python scripts/extract_audio.py source/book5-not-till-we-are-lost.txt --book 5
    python scripts/extract_audio.py source/book1-we-are-legion.txt --book 1 --strip-brackets --measure

--measure (book 1 only) strips the brackets and reports how many of the verified exchanges in
data/quotes.jsonl fall inside a window: the recall ceiling of this method on audio-only text.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import ROOT, load_quotes, normalize  # noqa: E402

PAGE_MARK = re.compile(r"<<PAGE (\d+)>>")
MENTION = re.compile(r"\b(gupp(?:y|i|ie)s?)\b", re.I)
SENT_END = re.compile(r"(?<=[.!?…])\s+|\n{2,}")
# spoken heading as typeset by audio_to_book: "14 Bob August 2144 Epsilon Eridani" or "3. Bob, June 25th, 2133"
HEADING = re.compile(r"^\s*(\d{1,3})\.?\s+(Bob|Bill|Riker|Milo|Homer|Howard|Mario|Calvin|Khan|Goku|Luke|Bender|"
                     r"Garfield|Hungry|Herschel|Neil|Will|Marcus|Hugh|Jacques|Theresa|Bridget|Thor|Daedalus|Icarus|"
                     r"Ick|Dae|Loki|Bashful|Bert|Ernie|Claude|Elmer|Phineas|Ferb|Oliver|Fred|Garf|Hal|Dopey|Doc)\b"
                     r"[^\n]{0,80}$", re.M)
WINDOW = 12   # sentences each side of a mention
CHAIN = 30    # keep extending over runs of short (dialogue) sentences, up to this many
SHORT = 18    # words: a sentence this short is probably dialogue
# Measured on book 1 with brackets stripped (146 verified lines): window 12 + chain -> 92% of GUPPI lines
# fall inside a window while the windows cover 28% of the book. Window 5 alone: 71% / 14%.


def strip_brackets(text: str) -> str:
    """Make real-book text look like transcript text: drop [ ] and quote marks."""
    text = re.sub(r"\[(?!<)([^\[\]]{1,600})\]", r"\1", text)
    return re.sub(r"[\"“”]", "", text)


def sentences(text: str) -> list[tuple[int, int, str]]:
    """[(start, end, sentence)] over the whole text, page markers kept as their own items."""
    out, pos = [], 0
    for m in SENT_END.finditer(text):
        s = text[pos:m.start()]
        if s.strip():
            out.append((pos, m.start(), s))
        pos = m.end()
    if text[pos:].strip():
        out.append((pos, len(text), text[pos:]))
    return out


def page_at(text: str, offset: int) -> int | None:
    last = None
    for m in PAGE_MARK.finditer(text, 0, offset):
        last = int(m.group(1))
    return last


def chapter_at(headings: list[tuple[int, str]], offset: int) -> tuple[int | None, str]:
    cur = (None, "")
    for i, (off, title) in enumerate(headings, 1):
        if off <= offset:
            cur = (i, title)
        else:
            break
    return cur


def windows(text: str, book: int) -> list[dict]:
    sents = sentences(text)
    heads = [(m.start(), re.sub(r"\s+", " ", m.group(0)).strip()) for m in HEADING.finditer(text)]
    hit = [i for i, (_, _, s) in enumerate(sents) if MENTION.search(s)]
    spans: list[list[int]] = []
    for i in hit:
        lo, hi = max(0, i - WINDOW), min(len(sents) - 1, i + WINDOW)
        while hi + 1 < len(sents) and len(sents[hi + 1][2].split()) <= SHORT and hi - i < WINDOW + CHAIN:
            hi += 1
        if spans and lo <= spans[-1][1] + 1:
            spans[-1][1] = max(spans[-1][1], hi)
        else:
            spans.append([lo, hi])
    out = []
    for k, (lo, hi) in enumerate(spans, 1):
        start, end = sents[lo][0], sents[hi][1]
        body = PAGE_MARK.sub(" ", text[start:end])
        body = re.sub(r"[ \t]*\n[ \t]*", " ", body).strip()
        ci, title = chapter_at(heads, start)
        if ci is None:  # window starts before the first heading on its page
            inside = [(i, t) for i, (off, t) in enumerate(heads, 1) if start <= off < end]
            if inside:
                ci, title = inside[0]
        page = page_at(text, start)
        if page is None:  # window starts before the first marker on its page
            m = PAGE_MARK.search(text, start, end)
            page = int(m.group(1)) if m else None
        out.append({
            "id": f"w{book}-{k:04d}",
            "book": book,
            "chapter": title,
            "chapter_index": ci,
            "page": page,
            "page_end": page_at(text, end),
            "char_offset": start,
            "mentions": len(MENTION.findall(body)),
            "text": body,
        })
    return out


def measure(text_stripped: str, wins: list[dict], book: int) -> dict:
    """How many verified exchanges of `book` fall inside some window (recall ceiling)."""
    blob = normalize(" ".join(w["text"] for w in wins))
    recs = [r for r in load_quotes() if r["book"] == book]
    hits = [r for r in recs if normalize(r["output"]) and normalize(r["output"]) in blob]
    missed = [r["id"] for r in recs if r not in hits]
    return {"verified": len(recs), "inside_a_window": len(hits), "recall": round(len(hits) / max(1, len(recs)), 3),
            "windows": len(wins), "window_words": len(blob.split()), "missed": missed}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file", type=Path, help=".txt with <<PAGE n>> markers (bobiverse.py export) or a .pdf")
    ap.add_argument("--book", type=int, required=True)
    ap.add_argument("--strip-brackets", action="store_true", help="simulate transcript text from a real book")
    ap.add_argument("--measure", action="store_true", help="recall of the verified quotes (needs --strip-brackets on a real book)")
    ap.add_argument("--out", type=Path, default=None)
    a = ap.parse_args(argv)
    if a.file.suffix.lower() == ".pdf":
        import pymupdf
        text = "".join(f"\n\f<<PAGE {i + 1}>>\n{p.get_text()}" for i, p in enumerate(pymupdf.open(str(a.file))))
    else:
        text = a.file.read_text(encoding="utf-8", errors="replace")
    if a.strip_brackets:
        text = strip_brackets(text)
    wins = windows(text, a.book)
    out = a.out or ROOT / "data" / f"windows-b{a.book}.jsonl"
    with open(out, "w", encoding="utf-8") as f:
        for w in wins:
            f.write(json.dumps(w, ensure_ascii=False) + "\n")
    words = sum(len(w["text"].split()) for w in wins)
    print(f"{len(wins)} windows, {words} words ({100 * words / max(1, len(text.split())):.0f}% of the book) -> {out}")
    if a.measure:
        print(json.dumps(measure(text, wins, a.book), indent=1))


if __name__ == "__main__":
    main()
