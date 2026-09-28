"""Shared helpers: loading/saving quotes, normalizing GUPPI output, scoring."""
from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
QUOTES = ROOT / "data" / "quotes.jsonl"
TESTSET = ROOT / "data" / "testset.json"
RESULTS = ROOT / "results"

REQUIRED = {"id", "book", "chapter", "bob", "input_type", "input", "output",
            "context", "setting", "tags", "category", "provenance", "confidence"}
PROVENANCE = {"verified", "recalled", "synthetic"}
INPUT_TYPES = {"command", "question", "event", "banter"}


def load_quotes(path: Path = QUOTES) -> list[dict]:
    recs = []
    with open(path, encoding="utf-8") as f:
        for n, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            missing = REQUIRED - rec.keys()
            if missing:
                raise ValueError(f"{path}:{n} missing fields {sorted(missing)}")
            if rec["provenance"] not in PROVENANCE:
                raise ValueError(f"{path}:{n} bad provenance {rec['provenance']!r}")
            if rec["input_type"] not in INPUT_TYPES:
                raise ValueError(f"{path}:{n} bad input_type {rec['input_type']!r}")
            recs.append(rec)
    ids = Counter(r["id"] for r in recs)
    dupes = [k for k, v in ids.items() if v > 1]
    if dupes:
        raise ValueError(f"duplicate ids: {dupes}")
    return recs


def save_quotes(recs: list[dict], path: Path = QUOTES) -> None:
    with open(path, "w", encoding="utf-8") as f:
        for r in recs:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


_PUNCT = re.compile(r"[^\w\s]")
_WS = re.compile(r"\s+")


def normalize(text: str) -> str:
    """Case, punctuation, brackets and whitespace insensitive form of a line."""
    t = text.strip().lower()
    t = t.replace("guppy", "guppi")
    t = _PUNCT.sub(" ", t)
    return _WS.sub(" ", t).strip()


def token_f1(pred: str, gold: str) -> float:
    p, g = normalize(pred).split(), normalize(gold).split()
    if not p and not g:
        return 1.0
    if not p or not g:
        return 0.0
    common = Counter(p) & Counter(g)
    overlap = sum(common.values())
    if overlap == 0:
        return 0.0
    prec, rec = overlap / len(p), overlap / len(g)
    return 2 * prec * rec / (prec + rec)


def is_bracketed(text: str) -> bool:
    t = text.strip()
    return t.startswith("[") and t.endswith("]")


def score_pair(pred: str, gold: str) -> dict:
    return {
        "exact": pred.strip() == gold.strip(),
        "normalized": normalize(pred) == normalize(gold),
        "f1": round(token_f1(pred, gold), 4),
        "bracket_ok": is_bracketed(pred) == is_bracketed(gold),
        "length_ratio": round((len(pred.split()) or 1) / (len(gold.split()) or 1), 3),
    }


def format_input(rec: dict) -> str:
    """What the model under test sees: setting + context + the actual input."""
    return (
        f"Setting: {rec['setting']}\n"
        f"Context: {rec['context']}\n"
        f"Input type: {rec['input_type']}\n"
        f"{rec['bob']}: {rec['input']}"
    )
