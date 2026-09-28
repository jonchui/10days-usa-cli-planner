#!/usr/bin/env python3
"""Pick the 80/20 representative test set.

Take categories in frequency order until they cover >=80% of records, then
sample up to --per-category from each (verified records first, then highest
confidence). Everything else is training data. Deterministic (seeded).

    python scripts/select_testset.py            # -> data/testset.json
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import TESTSET, load_quotes  # noqa: E402


def select(recs: list[dict], per_category: int = 3, coverage: float = 0.8, seed: int = 7) -> dict:
    rng = random.Random(seed)
    cats = Counter(r["category"] for r in recs)
    total = len(recs)
    chosen_cats, cum = [], 0
    for cat, c in cats.most_common():
        chosen_cats.append(cat)
        cum += c
        if cum / total >= coverage:
            break
    by_cat = defaultdict(list)
    for r in recs:
        by_cat[r["category"]].append(r)
    ids = []
    for cat in chosen_cats:
        pool = by_cat[cat][:]
        rng.shuffle(pool)
        pool.sort(key=lambda r: (r["provenance"] != "verified", -r["confidence"]))
        ids += [r["id"] for r in pool[:per_category]]
    return {
        "coverage_target": coverage,
        "categories": chosen_cats,
        "covered_share": round(cum / total, 3),
        "ids": ids,
        "n_test": len(ids),
        "n_total": total,
    }


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--per-category", type=int, default=3)
    ap.add_argument("--coverage", type=float, default=0.8)
    ap.add_argument("--out", type=Path, default=TESTSET)
    a = ap.parse_args(argv)
    sel = select(load_quotes(), a.per_category, a.coverage)
    a.out.write_text(json.dumps(sel, indent=2) + "\n")
    print(f"{sel['n_test']}/{sel['n_total']} records in test set, categories={sel['categories']} "
          f"(cover {sel['covered_share']:.0%}) -> {a.out}")


if __name__ == "__main__":
    main()
