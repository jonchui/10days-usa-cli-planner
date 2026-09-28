#!/usr/bin/env python3
"""Extract candidate Bob->GUPPI exchanges from a book file (pdf / epub / txt).

GUPPI's lines are printed in square brackets, so every bracketed run of text
is a candidate output (numbers included: early-book GUPPI interjects bare
figures into Bob's thoughts). Consecutive bracketed lines separated only by
whitespace are one output (status reports). The input is the last quoted line
before the bracket if one ends close to it, otherwise the last sentence of
Bob's narration/thought before it.

    python scripts/extract.py source/book1-we-are-legion.pdf --book 1
    python scripts/extract.py source/book1.txt --book 1 --chars-per-page 1800

PDF input is converted to text with real page markers (`<<PAGE n>>`), so
`page` is the actual PDF page. For txt/epub without markers, page is estimated
from the character offset. Writes data/candidates.jsonl (gitignored).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import ROOT  # noqa: E402

PAGE_MARK = re.compile(r"<<PAGE (\d+)>>")
BRACKET = re.compile(r"\[([^\[\]]{1,600})\]")
QUOTE = re.compile(r"[\"“]([^\"”]{1,400})[\"”]", re.S)
BOBS = "Bob|Bill|Riker|Milo|Homer|Howard|Mario|Calvin|Khan|Goku|Luke|Bender|Garfield|Hungry|Herschel|Neil"
CHAPTER = re.compile(rf"^\s*(\d{{1,3}})\.\s+({BOBS})\b[^\n]*$", re.M)
KINDLE_LOC_BYTES = 128
DASH = re.compile(r"\s*[–—-]\s*")


def read_text(path: Path) -> str:
    suf = path.suffix.lower()
    if suf == ".txt":
        return path.read_text(encoding="utf-8", errors="replace")
    if suf == ".pdf":
        import pymupdf

        doc = pymupdf.open(str(path))
        return "".join(f"\n\f<<PAGE {i + 1}>>\n{p.get_text()}" for i, p in enumerate(doc))
    if suf == ".epub":
        import ebooklib
        from bs4 import BeautifulSoup
        from ebooklib import epub

        book = epub.read_epub(str(path))
        parts = []
        for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
            soup = BeautifulSoup(item.get_content(), "html.parser")
            for h in soup.find_all(["h1", "h2", "h3"]):
                h.insert_before("\n\n")
                h.insert_after("\n\n")
            parts.append(soup.get_text("\n"))
        return "\n\n".join(parts)
    raise SystemExit(f"unsupported file type: {suf}")


def split_chapters(text: str) -> list[tuple[str, int, str]]:
    """[(title, start_offset, body)] — numbered title-case headings ("12. Bob – …"),
    first occurrence per number, numbers must increase. The table of contents is
    upper-case in the PDF so it never matches; back-matter repeats are dropped."""
    heads, seen, last = [], set(), 0
    for m in CHAPTER.finditer(text):
        n = int(m.group(1))
        if n in seen or n < last:
            continue
        seen.add(n); last = n
        heads.append(m)
    if not heads:
        return [("(no chapter headings found)", 0, text)]
    out = []
    for i, m in enumerate(heads):
        end = heads[i + 1].start() if i + 1 < len(heads) else len(text)
        out.append((re.sub(r"\s+", " ", m.group(0)).strip(), m.start(), text[m.end():end])) 
    return out


def clean(s: str) -> str:
    return re.sub(r"\s+", " ", s.replace("\f", " ")).strip()


def strip_page_marks(s: str) -> str:
    return PAGE_MARK.sub(" ", s)


def page_at(text: str, offset: int) -> int | None:
    last = None
    for m in PAGE_MARK.finditer(text, 0, offset):
        last = int(m.group(1))
    return last


def guess_input(before: str) -> tuple[str, str]:
    """Return (input, input_type) from the text preceding a bracket."""
    before = strip_page_marks(before)
    tail = before[-500:]
    quotes = list(QUOTE.finditer(tail))
    if quotes and len(tail) - quotes[-1].end() <= 160:
        q = clean(quotes[-1].group(1))
        return q, ("question" if q.rstrip().endswith("?") else "command")
    # unquoted thought / narration: last sentence(s) before the bracket
    flat = clean(tail)
    sents = re.split(r"(?<=[.!?…])\s+", flat)
    last = " ".join(s for s in sents[-2:] if s).strip()
    if not last:
        return "(event) see context", "event"
    last = last[-220:]
    if last.endswith("?"):
        return last, "question"
    return last, "banter"


def extract(text: str, book: int, chars_per_page: int) -> list[dict]:
    recs, seq = [], 0
    has_marks = bool(PAGE_MARK.search(text))
    for ci, (title, ch_off, body) in enumerate(split_chapters(text), 1):
        parts = DASH.split(title.split(".", 1)[1].strip()) if "." in title else [title]
        bob = parts[0].split()[0] if parts and parts[0] else "Bob"
        bob = "Bob-1" if bob == "Bob" else bob
        setting = ", ".join(p for p in parts[1:] if p) or parts[0]
        body_off = ch_off + len(title)
        matches = list(BRACKET.finditer(body))
        i = 0
        while i < len(matches):
            m = matches[i]
            outs = [clean(m.group(1))]
            end = m.end()
            # group consecutive bracket lines separated only by whitespace / page marks
            while i + 1 < len(matches) and clean(strip_page_marks(body[end:matches[i + 1].start()])) in ("", "."):
                i += 1
                outs.append(clean(matches[i].group(1)))
                end = matches[i].end()
            before = body[max(0, m.start() - 1500): m.start()]
            inp, itype = guess_input(before)
            prev_char = clean(strip_page_marks(before))[-1:] if clean(strip_page_marks(before)) else ""
            after = clean(strip_page_marks(body[end:end + 80]))
            mid_sentence = prev_char and prev_char not in ".!?…\"”" and after[:1].islower()
            abs_off = body_off + m.start()
            page = page_at(text, abs_off) if has_marks else abs_off // chars_per_page + 1
            seq += 1
            recs.append({
                "id": f"b{book}-{seq:04d}",
                "book": book,
                "chapter": title,
                "chapter_index": ci,
                "page": page,
                "location": abs_off // KINDLE_LOC_BYTES,
                "char_offset": abs_off,
                "bob": bob,
                "input_type": "banter" if mid_sentence else itype,
                "input": inp,
                "output": "\n".join(f"[{o}]" for o in outs),
                "context": clean(strip_page_marks(before))[-380:] + " ▸ " + after[:60],
                "setting": setting,
                "tags": [f"#book{book}", f"#bob-{bob.lower().replace('bob-', '')}"] + (["#cat-interject"] if mid_sentence else []),
                "category": "interject" if mid_sentence else "",
                "provenance": "verified",
                "confidence": 0.95,
                "notes": "page = PDF page" if has_marks else "page estimated from character offset",
            })
            i += 1
    return recs


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file", type=Path)
    ap.add_argument("--book", type=int, required=True)
    ap.add_argument("--chars-per-page", type=int, default=1800, help="paperback ≈ 1800 chars/page (txt/epub only)")
    ap.add_argument("--out", type=Path, default=ROOT / "data" / "candidates.jsonl")
    a = ap.parse_args(argv)
    text = read_text(a.file)
    recs = extract(text, a.book, a.chars_per_page)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as f:
        for r in recs:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"{len(recs)} candidate exchanges across {len(split_chapters(text))} chapters -> {a.out}")
    print("next: python scripts/categorize.py --input data/candidates.jsonl --no-report ; review ; python scripts/ingest.py data/candidates.jsonl")


if __name__ == "__main__":
    main()
