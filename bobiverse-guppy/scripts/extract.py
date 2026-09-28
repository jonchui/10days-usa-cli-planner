#!/usr/bin/env python3
"""Extract candidate Bob->GUPPI exchanges from a book file (epub / txt / pdf).

GUPPI's lines are printed in square brackets, so every bracketed run of text
that looks like speech is a candidate output. The nearest preceding quoted
line is taken as the input; the surrounding paragraph is kept as context.

    python scripts/extract.py source/book1-we-are-legion.epub --book 1
    python scripts/extract.py source/book1.txt --book 1 --chars-per-page 1800

Writes data/candidates.jsonl (gitignored). Review, then merge into
data/quotes.jsonl with scripts/ingest.py.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import ROOT  # noqa: E402

BRACKET = re.compile(r"\[([^\[\]\n]{1,300})\]")
QUOTE = re.compile(r"[\"“]([^\"”\n]{1,400})[\"”]")
# Bobiverse chapter headings look like:  Bob – August 17, 2133 – Sol   (dash variants)
CHAPTER = re.compile(
    r"^\s*([A-Z][A-Za-z0-9\-']{1,20})\s*[–—-]\s*([A-Z][a-z]+\s+\d{1,2},?\s*\d{4}|\w+\s+\d{4})\s*[–—-]\s*(.+?)\s*$",
    re.M,
)
KINDLE_LOC_BYTES = 128


def read_text(path: Path) -> str:
    suf = path.suffix.lower()
    if suf == ".txt":
        return path.read_text(encoding="utf-8", errors="replace")
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
    if suf == ".pdf":
        from pypdf import PdfReader

        return "\n\n".join((p.extract_text() or "") for p in PdfReader(str(path)).pages)
    raise SystemExit(f"unsupported file type: {suf}")


def split_chapters(text: str) -> list[tuple[str, int, str]]:
    """Return [(title, start_offset, body)]; whole text as one chapter if no headings."""
    heads = list(CHAPTER.finditer(text))
    if not heads:
        return [("(no chapter headings found)", 0, text)]
    out = []
    for i, m in enumerate(heads):
        end = heads[i + 1].start() if i + 1 < len(heads) else len(text)
        out.append((m.group(0).strip(), m.start(), text[m.end():end]))
    return out


def looks_like_speech(s: str) -> bool:
    s = s.strip()
    if len(s) < 2 or s.isdigit():
        return False
    if re.fullmatch(r"[\d\s.,:%-]+", s):
        return False
    return any(c.isalpha() for c in s)


def extract(text: str, book: int, chars_per_page: int) -> list[dict]:
    recs = []
    seq = 0
    for ci, (title, ch_off, body) in enumerate(split_chapters(text), 1):
        bob = title.split("–")[0].split("—")[0].split("-")[0].strip() or "Bob-1"
        if bob == "Bob":
            bob = "Bob-1"
        for m in BRACKET.finditer(body):
            out = m.group(1).strip()
            if not looks_like_speech(out):
                continue
            before = body[max(0, m.start() - 1200): m.start()]
            quotes = QUOTE.findall(before)
            inp = quotes[-1].strip() if quotes else ""
            input_type = "command" if inp else "event"
            if inp.endswith("?"):
                input_type = "question"
            para_start = before.rfind("\n\n")
            ctx = (before[para_start:] if para_start >= 0 else before[-400:]).strip()
            ctx = re.sub(r"\s+", " ", ctx)[-400:]
            abs_off = ch_off + len(title) + m.start()
            seq += 1
            recs.append({
                "id": f"b{book}-{seq:04d}",
                "book": book,
                "chapter": title,
                "chapter_index": ci,
                "page": abs_off // chars_per_page + 1,
                "location": abs_off // KINDLE_LOC_BYTES,
                "char_offset": abs_off,
                "bob": bob,
                "input_type": input_type,
                "input": inp or "(event) see context",
                "output": f"[{out}]",
                "context": ctx,
                "setting": title.split("–")[-1].split("—")[-1].strip(),
                "tags": [f"#book{book}", f"#bob-{bob.lower().replace('bob-', '')}"],
                "category": "",
                "provenance": "verified",
                "confidence": 0.9,
                "notes": "page/location estimated from character offset; verify against print edition",
            })
    return recs


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file", type=Path)
    ap.add_argument("--book", type=int, required=True)
    ap.add_argument("--chars-per-page", type=int, default=1800, help="paperback ≈ 1800 chars/page")
    ap.add_argument("--out", type=Path, default=ROOT / "data" / "candidates.jsonl")
    a = ap.parse_args(argv)
    text = read_text(a.file)
    recs = extract(text, a.book, a.chars_per_page)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as f:
        for r in recs:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    chapters = len(split_chapters(text))
    print(f"{len(recs)} candidate exchanges across {chapters} chapters -> {a.out}")
    print("next: python scripts/categorize.py --input data/candidates.jsonl ; review ; python scripts/ingest.py data/candidates.jsonl")


if __name__ == "__main__":
    main()
