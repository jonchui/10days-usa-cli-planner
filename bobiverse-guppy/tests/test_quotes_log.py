from common import load_quotes


def test_log_loads_and_is_well_formed():
    recs = load_quotes()
    assert len(recs) >= 10
    for r in recs:
        assert r["output"].strip().startswith("["), r["id"]
        assert any(t.startswith("#cat-") for t in r["tags"]), r["id"]
        assert any(t.startswith("#setting-") for t in r["tags"]), r["id"]
        assert any(t.startswith("#book") for t in r["tags"]), r["id"]
        assert any(t.startswith("#bob-") for t in r["tags"]), r["id"]
        assert 0 <= r["confidence"] <= 1
        assert r["context"] and r["setting"]
