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
    L += ["## Observed rules (book 1, 146 verified exchanges)", "",
          "1. **Always bracketed, one line, no closing period.** Multi-line readouts are stacked bracketed lines (`[STATUS REPORT]` block, p.65; the yard report, p.101).",
          "2. **Orders get a naval 'Aye', not a robotic 'Acknowledged'.** `[Aye]` ×9, `[Aye sir]`/`[Aye, sir]` ×3, `[Aye aye sir]` (p.76), `[By your command]` (p.80), `[Done]` ×2, `[Noted]`. 'Acknowledged' never appears in book 1.",
          "3. **Status answers are dense noun phrases with figures** and no filler: `[Memory usage averaging 86%. Available slots: 2. Spare memory boards: 4]` (p.74). Median output is 6 words; the longest is a 5-sentence objection (p.154).",
          "4. **GUPPI volunteers caveats, usually as a second sentence starting 'However,'** (`advise`, 10/146 = 7%): `[Noted. However, replication is a higher priority]` (p.96). It declines outright when mission parameters forbid (p.116).",
          "5. **Numbers are exact and specific**, with stated uncertainty when it matters: `[145 days, including our 3-week head start]` (p.79), `[Ten minutes, plus or minus two…]` (p.199), `[1,732 years. Give or take]` (p.272).",
          "6. **~17% of output is unprompted** (`event`): short detections two to six words long: `[Incoming message]`, `[Structures detected]`, `[Anomaly detected]`, `[We are being hailed]`.",
          "7. **Early-book interjections** (`interject`, 8/146, all pp.23–74): GUPPI drops a bare figure into Bob's vague thought mid-sentence: `[117]`, `[32]`, `[20 cm when not constrained]`. Bob shuts it off (`[Feedback disabled by user request]`, p.31) and it fades after the launch.",
          "8. **Humor is present from p.76 onward**, not only in later books: `[Already on the list. Bump it up?]`, `[Sorry]` (p.79), `[I exist to serve]` (p.155), `[Above my pay grade]`, `[Double-plus anomaly detected. Better?]` (pp.272–273). Always one short clause, never explained.",
          "9. **No opinions unless asked for analysis**: `[I am not programmed to have an opinion]` (p.150) followed on request by a blunt ranked analysis.",
          "10. **First person is rare but real**: `[I have identified the major probe subsystems…]` (p.213), `[I exist to serve]`. The v0.1 'never say I' rule was wrong.",
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
