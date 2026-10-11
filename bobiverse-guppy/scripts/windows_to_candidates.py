#!/usr/bin/env python3
"""Turn labeled windows (scripts/label_windows.md output) into a candidates file for ingest.py.

    python scripts/windows_to_candidates.py data/labels-b5.jsonl --book 5 [--windows data/windows-b5.jsonl]

labels: one JSON per line {"window_id", "exchanges": [{output, input, input_type, bob, confidence}]}
Each exchange gets the window's page, chapter and setting; provenance "synthetic" (audio wording)
until a human confirms it against the narration, then flip it to "verified".
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import ROOT, save_quotes  # noqa: E402


def convert(labels: list[dict], wins: dict[str, dict], book: int) -> list[dict]:
    out, seq = [], 0
    for lab in labels:
        w = wins.get(lab.get("window_id"))
        if not w:
            continue
        parts = re.split(r"\s+", w["chapter"].strip()) if w.get("chapter") else []
        for ex in lab.get("exchanges", []):
            seq += 1
            o = ex["output"].strip()
            if not o.startswith("["):
                o = f"[{o.strip('[]')}]"
            bob = ex.get("bob") or (parts[1] if len(parts) > 1 else "Bob")
            bob = "Bob-1" if bob == "Bob" else bob
            out.append({
                "id": f"b{book}-{seq:04d}", "book": book, "chapter": w.get("chapter", ""),
                "chapter_index": w.get("chapter_index"), "page": w.get("page"), "location": None,
                "char_offset": w.get("char_offset"), "bob": bob, "input_type": ex.get("input_type", "command"),
                "input": ex.get("input", "(event) see context"), "output": o,
                "context": w["text"][:400], "setting": " ".join(parts[3:]) if len(parts) > 3 else w.get("chapter", ""),
                "tags": [f"#book{book}", f"#bob-{bob.lower().replace('bob-', '')}", "#audio-text"],
                "category": "", "provenance": "synthetic", "confidence": float(ex.get("confidence", 0.5)),
                "notes": "audio transcript; wording is Whisper's; page = text.pdf page",
            })
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("labels", type=Path)
    ap.add_argument("--book", type=int, required=True)
    ap.add_argument("--windows", type=Path, default=None)
    ap.add_argument("--out", type=Path, default=ROOT / "data" / "candidates.jsonl")
    a = ap.parse_args(argv)
    wf = a.windows or ROOT / "data" / f"windows-b{a.book}.jsonl"
    wins = {w["id"]: w for w in (json.loads(l) for l in wf.read_text().splitlines() if l.strip())}
    labels = [json.loads(l) for l in a.labels.read_text().splitlines() if l.strip()]
    recs = convert(labels, wins, a.book)
    save_quotes(recs, a.out)
    print(f"{len(recs)} candidate exchanges from {len(labels)} labeled windows -> {a.out}")


if __name__ == "__main__":
    main()
