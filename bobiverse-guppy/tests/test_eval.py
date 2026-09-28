import json

from run_eval import summarize
from select_testset import select
from guppy import rules
from common import load_quotes, score_pair


def test_rules_backend_returns_bracketed_lines():
    for r in load_quotes():
        out = rules.respond(r)
        assert out.startswith("[") and out.endswith("]")


def test_select_testset_covers_80pct():
    sel = select(load_quotes(), per_category=3, coverage=0.8)
    assert sel["covered_share"] >= 0.8
    assert sel["n_test"] <= sel["n_total"]
    assert len(set(sel["ids"])) == len(sel["ids"])


def test_summarize_splits_verified_and_recalled():
    rows = [{"category": "ack", "provenance": "verified", **score_pair("[Acknowledged]", "[Acknowledged]")},
            {"category": "ack", "provenance": "recalled", **score_pair("[Nope]", "[Acknowledged]")}]
    s = summarize(rows)
    assert s["verified"]["match_pct"] == 100.0 and s["recalled"]["match_pct"] == 0.0 and s["all"]["match_pct"] == 50.0
    json.dumps(s)
