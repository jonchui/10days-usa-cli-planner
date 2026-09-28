#!/usr/bin/env python3
"""Merge reviewed candidates into data/quotes.jsonl (skips ids already present,
re-numbers per book so ids never collide).

    python scripts/ingest.py data/candidates.jsonl
    python scripts/ingest.py data/candidates.jsonl --min-confidence 0.8
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import QUOTES, load_quotes, normalize, save_quotes  # noqa: E402


def merge(existing: list[dict], new: list[dict], min_conf: float) -> tuple[list[dict], int]:
    seen = {(r["book"], normalize(r["input"]), normalize(r["output"])) for r in existing}
    next_seq = {}
    for r in existing:
        b, s = r["id"].split("-")
        next_seq[int(b[1:])] = max(next_seq.get(int(b[1:]), 0), int(s))
    added = 0
    for r in new:
        if r.get("confidence", 0) < min_conf:
            continue
        key = (r["book"], normalize(r["input"]), normalize(r["output"]))
        if key in seen:
            continue
        next_seq[r["book"]] = next_seq.get(r["book"], 0) + 1
        r["id"] = f"b{r['book']}-{next_seq[r['book']]:04d}"
        existing.append(r)
        seen.add(key)
        added += 1
    return existing, added


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("candidates", type=Path)
    ap.add_argument("--min-confidence", type=float, default=0.0)
    a = ap.parse_args(argv)
    existing = load_quotes(QUOTES) if QUOTES.exists() else []
    merged, added = merge(existing, load_quotes(a.candidates), a.min_confidence)
    save_quotes(merged, QUOTES)
    print(f"added {added}, total {len(merged)} -> {QUOTES}")


if __name__ == "__main__":
    main()
