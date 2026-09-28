#!/usr/bin/env python3
"""Run one Guppy version against the test set and record match percentages.

    python scripts/run_eval.py --backend rules
    python scripts/run_eval.py --backend prompt:guppy/prompts/v0.1.md [--model claude-opus-5] [--judge]
    python scripts/run_eval.py --backend replay:results/outputs-v0.2.json   # {id: output}
    python scripts/run_eval.py --backend rules --all     # every record, not just the test set

Writes results/runs/<version>__<utc>.json and refreshes results/leaderboard.md.
Headline number = % of VERIFIED test records whose output matches after
normalization (case/punctuation/brackets/whitespace). Recalled records are
scored too but reported separately, because their gold text may be off.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import RESULTS, TESTSET, load_quotes, score_pair  # noqa: E402


def make_backend(spec: str, model: str | None):
    if spec == "rules":
        from guppy import rules
        return rules.VERSION, rules.respond, None
    kind, _, arg = spec.partition(":")
    if kind == "prompt":
        from guppy.api_backend import DEFAULT_MODEL, PromptGuppy, have_credentials
        if not have_credentials():
            raise SystemExit("prompt backend needs ANTHROPIC_API_KEY (or ANTHROPIC_AUTH_TOKEN / `ant auth login`)")
        g = PromptGuppy(Path(arg), model or DEFAULT_MODEL)
        return g.version, g.respond, g.client
    if kind == "replay":
        outputs = json.loads(Path(arg).read_text())
        return f"replay-{Path(arg).stem}", (lambda rec: outputs.get(rec["id"], "")), None
    raise SystemExit(f"unknown backend {spec!r}")


def summarize(rows: list[dict]) -> dict:
    def block(rs):
        n = len(rs)
        if not n:
            return {"n": 0}
        return {
            "n": n,
            "exact_pct": round(100 * sum(r["exact"] for r in rs) / n, 1),
            "match_pct": round(100 * sum(r["normalized"] for r in rs) / n, 1),
            "judge_pct": round(100 * sum(bool(r.get("judge")) for r in rs) / n, 1) if any("judge" in r for r in rs) else None,
            "mean_f1": round(sum(r["f1"] for r in rs) / n, 3),
            "bracket_ok_pct": round(100 * sum(r["bracket_ok"] for r in rs) / n, 1),
        }
    by_cat, by_prov = defaultdict(list), defaultdict(list)
    for r in rows:
        by_cat[r["category"]].append(r)
        by_prov[r["provenance"]].append(r)
    return {
        "all": block(rows),
        "verified": block(by_prov.get("verified", [])),
        "recalled": block(by_prov.get("recalled", [])),
        "by_category": {c: block(rs) for c, rs in sorted(by_cat.items())},
    }


def write_leaderboard(runs_dir: Path, out: Path) -> None:
    runs = []
    for p in sorted(runs_dir.glob("*.json")):
        d = json.loads(p.read_text())
        runs.append(d)
    L = ["# Guppy leaderboard", "",
         "Headline = normalized match on VERIFIED test records. `all` includes recalled records whose gold text is unverified.", "",
         "| run (UTC) | version | n test | verified match | all match | all exact | mean F1 | bracket ok | judge |",
         "|---|---|---|---|---|---|---|---|---|"]
    for d in runs:
        s = d["summary"]
        v = s["verified"]
        L.append(f"| {d['timestamp']} | `{d['version']}` | {s['all']['n']} | "
                 f"{'n/a' if v['n'] == 0 else str(v['match_pct']) + '%'} | {s['all']['match_pct']}% | {s['all']['exact_pct']}% | "
                 f"{s['all']['mean_f1']} | {s['all']['bracket_ok_pct']}% | "
                 f"{'n/a' if s['all'].get('judge_pct') is None else str(s['all']['judge_pct']) + '%'} |")
    if runs:
        last = runs[-1]
        L += ["", f"## Latest run by category (`{last['version']}`)", "", "| category | n | match | F1 |", "|---|---|---|---|"]
        for c, b in last["summary"]["by_category"].items():
            L.append(f"| {c} | {b['n']} | {b['match_pct']}% | {b['mean_f1']} |")
    out.write_text("\n".join(L) + "\n", encoding="utf-8")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--backend", default="rules")
    ap.add_argument("--model", default=None)
    ap.add_argument("--judge", action="store_true", help="also ask an LLM judge (needs API key)")
    ap.add_argument("--all", action="store_true", help="score every record instead of the test set")
    ap.add_argument("--label", default=None, help="override version label in results")
    a = ap.parse_args(argv)

    recs = load_quotes()
    if not a.all:
        if not TESTSET.exists():
            raise SystemExit("no data/testset.json — run scripts/select_testset.py first, or pass --all")
        ids = set(json.loads(TESTSET.read_text())["ids"])
        recs = [r for r in recs if r["id"] in ids]
    version, respond, client = make_backend(a.backend, a.model)
    version = a.label or version

    rows = []
    for r in recs:
        pred = respond(r)
        row = {"id": r["id"], "category": r["category"], "provenance": r["provenance"],
               "input": r["input"], "gold": r["output"], "pred": pred, **score_pair(pred, r["output"])}
        if a.judge:
            from guppy.api_backend import judge
            import anthropic
            row["judge"] = judge(client or anthropic.Anthropic(), r, pred)
        rows.append(row)
        mark = "✓" if row["normalized"] else "✗"
        print(f"{mark} {r['id']} [{r['category']}] gold={r['output']!r} pred={pred!r}")

    summary = summarize(rows)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    runs_dir = RESULTS / "runs"
    runs_dir.mkdir(parents=True, exist_ok=True)
    out = runs_dir / f"{version}__{ts.replace(':', '')}.json"
    out.write_text(json.dumps({"version": version, "timestamp": ts, "backend": a.backend, "scope": "all" if a.all else "testset",
                               "summary": summary, "rows": rows}, indent=2, ensure_ascii=False) + "\n")
    write_leaderboard(runs_dir, RESULTS / "leaderboard.md")
    s = summary
    print(f"\n{version}: all match {s['all']['match_pct']}% (n={s['all']['n']}), verified match "
          f"{'n/a' if s['verified']['n'] == 0 else str(s['verified']['match_pct']) + '%'} (n={s['verified']['n']}), mean F1 {s['all']['mean_f1']}")
    print(f"-> {out}\n-> {RESULTS / 'leaderboard.md'}")


if __name__ == "__main__":
    main()
