#!/usr/bin/env python3
"""Auto-tag exchanges and write the pattern report.

    python scripts/categorize.py                 # tag data/quotes.jsonl in place, write reports/patterns.md
    python scripts/categorize.py --input data/candidates.jsonl --no-report

Only fills in a missing `category` / missing `#cat-*` tag; hand-set tags win.
"""
from __future__ import annotations

import argparse
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import ROOT, load_quotes, normalize, save_quotes  # noqa: E402

# (category, output regex, input regex) — first match wins, ordered by specificity.
RULES = [
    ("alert",     r"^\[?(contact|incoming|warning|alert|detect|proximity|unidentified)", None),
    ("clarify",   r"^\[?(query|specify|clarif|please define|define )", None),
    ("negative",  r"^\[?(negative|unable|cannot|no match|not found|insufficient)", None),
    ("interject", r"^\[?[\d.]+\s*(hours?|minutes?|seconds?|days?|years?|km|percent|%)\]?$", r"^\(bob thinks"),
    ("eta",       r"(estimated|eta|transit|arrival|time to|hours|days|years|months)", r"(how long|how far|when|eta|arrive)"),
    ("calc",      r"(\d+(\.\d+)?\s*(%|percent)|probability|approximately|[\d.]+ ?(km|g|tons?))", r"(calculate|odds|probab|how many|how much|what are the chances)"),
    ("status",    r"(nominal|status|online|offline|operational|at \d+%)", r"(status|report|how are|diagnostic)"),
    ("config",    None, r"(avatar|call you|your name|from now on|only respond|rename|stop that)"),
    ("execute",   r"^\[?(launching|firing|deploying|executing|building|launched|fired)", r"^(guppi,?\s*)?(launch|fire|deploy|build|execute|engage)"),
    ("literal",   None, r"(that's just great|is it just me|you know what i mean|oh great|wonderful)"),
    ("snark",     r"(obviously|as usual|again|if you insist|of course)", None),
    ("ack",       r"^\[?(acknowledged|affirmative|working|confirmed|understood|done|yes)\]?$", None),
]


def guess_category(rec: dict) -> str:
    out, inp = normalize(rec["output"]), normalize(rec["input"])
    raw_out = rec["output"].strip().lower()
    for cat, out_re, in_re in RULES:
        if out_re and (re.search(out_re, raw_out) or re.search(out_re, out)):
            if in_re is None or re.search(in_re, inp) or cat in {"alert", "clarify", "negative", "ack", "execute", "snark"}:
                return cat
        if in_re and out_re is None and re.search(in_re, inp):
            return cat
    if rec.get("input_type") == "event":
        return "alert"
    return "ack" if len(out.split()) <= 2 else "status"


def tag(recs: list[dict]) -> int:
    changed = 0
    for r in recs:
        tags = list(r.get("tags") or [])
        cat = r.get("category") or ""
        if not cat:
            cat = guess_category(r)
            r["category"] = cat
            changed += 1
        if not any(t.startswith("#cat-") for t in tags):
            tags.insert(0, f"#cat-{cat}")
            changed += 1
        if f"#book{r['book']}" not in tags:
            tags.append(f"#book{r['book']}")
        r["tags"] = list(dict.fromkeys(tags))
    return changed


def pattern_report(recs: list[dict]) -> str:
    n = len(recs)
    cats = Counter(r["category"] for r in recs)
    books = Counter(r["book"] for r in recs)
    itypes = Counter(r["input_type"] for r in recs)
    prov = Counter(r["provenance"] for r in recs)
    lens = [len(r["output"].split()) for r in recs]
    bracketed = sum(1 for r in recs if r["output"].strip().startswith("[") and r["output"].strip().endswith("]"))
    first = Counter(normalize(r["output"]).split()[0] for r in recs if normalize(r["output"]))
    by_cat_examples = defaultdict(list)
    for r in recs:
        by_cat_examples[r["category"]].append(r)
    tags = Counter(t for r in recs for t in r["tags"] if not t.startswith("#cat-"))

    def pct(x):
        return f"{100 * x / n:.0f}%" if n else "n/a"

    L = ["# GUPPI pattern report", "", f"Records: **{n}**  ·  provenance: " + ", ".join(f"{k}={v}" for k, v in prov.items()), ""]
    L += ["## Surface form", "",
          f"- Bracketed `[...]` output: {bracketed}/{n} ({pct(bracketed)})",
          f"- Output length (words): min {min(lens) if lens else 0}, median {sorted(lens)[len(lens)//2] if lens else 0}, max {max(lens) if lens else 0}",
          f"- Unprompted (event) outputs: {itypes.get('event', 0)}/{n} ({pct(itypes.get('event', 0))})",
          "- Most common first word: " + ", ".join(f"`{w}` ×{c}" for w, c in first.most_common(6)),
          ""]
    L += ["## Categories (what 80% of the traffic looks like)", "", "| category | n | share | cumulative | example output |", "|---|---|---|---|---|"]
    cum = 0
    for cat, c in cats.most_common():
        cum += c
        ex = by_cat_examples[cat][0]["output"].replace("|", "\\|")
        L.append(f"| {cat} | {c} | {pct(c)} | {pct(cum)} | `{ex}` |")
    L += ["", "## By book / by Bob / input type", "",
          "- books: " + ", ".join(f"book{b}={c}" for b, c in sorted(books.items())),
          "- input types: " + ", ".join(f"{k}={v}" for k, v in itypes.most_common()),
          "- top free tags: " + ", ".join(f"{t} ×{c}" for t, c in tags.most_common(12)),
          ""]
    L += ["## Observed rules (update as the corpus grows)", "",
          "1. **Always bracketed, never a pronoun 'I'.** GUPPI reports; it does not narrate itself.",
          "2. **One clause per line.** Confirmation words stand alone: `[Acknowledged]`, `[Affirmative]`, `[Negative]`.",
          "3. **Numbers are exact, not rounded**, and delivered without hedging words (no 'about', 'roughly').",
          "4. **No unsolicited opinion.** Alerts state a fact (`[Contact...]`), never a recommendation, unless Bob asks.",
          "5. **Idioms and rhetorical questions get literal treatment** (`[Query: define ...]`).",
          "6. **Behaviour is configurable by Bob** and the change is confirmed with a bare `[Acknowledged]`.",
          "7. **Later books drift toward dry snark** while keeping the bracketed, clause-length form. Tag these `#cat-snark` so the eval can score era-appropriate register.",
          ""]
    return "\n".join(L)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", type=Path, default=ROOT / "data" / "quotes.jsonl")
    ap.add_argument("--report", type=Path, default=ROOT / "reports" / "patterns.md")
    ap.add_argument("--no-report", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    recs = load_quotes(a.input)
    changed = tag(recs)
    if not a.dry_run:
        save_quotes(recs, a.input)
    print(f"{len(recs)} records, {changed} fields auto-filled")
    if not a.no_report:
        a.report.parent.mkdir(parents=True, exist_ok=True)
        a.report.write_text(pattern_report(recs), encoding="utf-8")
        print(f"report -> {a.report}")


if __name__ == "__main__":
    main()
