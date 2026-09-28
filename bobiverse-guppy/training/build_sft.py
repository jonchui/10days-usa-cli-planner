#!/usr/bin/env python3
"""Export the quote log as a supervised fine-tuning file (chat format).

    python training/build_sft.py                    # verified only, excludes test set -> training/sft.jsonl
    python training/build_sft.py --include-recalled

Each line: {"messages": [{"role":"system",...},{"role":"user",...},{"role":"assistant",...}], "meta": {...}}
This is the format most post-training stacks accept directly (Bedrock custom
models, OpenAI-style trainers, Axolotl/TRL with a chat template).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from common import TESTSET, format_input, load_quotes  # noqa: E402

SYSTEM = (ROOT / "guppy" / "prompts" / "v0.1.md").read_text(encoding="utf-8")


def build(recs: list[dict], test_ids: set[str], include_recalled: bool) -> list[dict]:
    out = []
    for r in recs:
        if r["id"] in test_ids:
            continue
        if r["provenance"] == "recalled" and not include_recalled:
            continue
        out.append({
            "messages": [
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": format_input(r)},
                {"role": "assistant", "content": r["output"]},
            ],
            "meta": {"id": r["id"], "book": r["book"], "chapter": r["chapter"], "page": r["page"],
                     "category": r["category"], "tags": r["tags"], "provenance": r["provenance"]},
        })
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--include-recalled", action="store_true")
    ap.add_argument("--out", type=Path, default=ROOT / "training" / "sft.jsonl")
    a = ap.parse_args(argv)
    test_ids = set(json.loads(TESTSET.read_text())["ids"]) if TESTSET.exists() else set()
    rows = build(load_quotes(), test_ids, a.include_recalled)
    with open(a.out, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"{len(rows)} training examples -> {a.out} (excluded {len(test_ids)} test ids)")


if __name__ == "__main__":
    main()
