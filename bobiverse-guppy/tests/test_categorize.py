from categorize import guess_category, pattern_report, tag


def rec(inp, out, itype="command"):
    return {"id": "x", "book": 1, "input": inp, "output": out, "input_type": itype, "tags": [], "category": "",
            "provenance": "verified", "confidence": 1.0}


def test_guess_category_rules():
    assert guess_category(rec("GUPPI, status report.", "[All systems nominal]")) == "status"
    assert guess_category(rec("(event) ship detected", "[Contact. Unidentified vessel]", "event")) == "alert"
    assert guess_category(rec("GUPPI, launch busters!", "[Launching]")) == "execute"
    assert guess_category(rec("Can you identify it?", "[Negative. No match]")) == "negative"
    assert guess_category(rec("Well, that's just great.", "[Query: define 'great']", "banter")) == "clarify"
    assert guess_category(rec("GUPPI, how long to Epsilon Eridani?", "[Estimated transit time: eleven years]")) == "eta"
    assert guess_category(rec("GUPPI, plot a course.", "[Acknowledged]")) == "ack"


def test_tag_fills_missing_and_keeps_manual():
    r = rec("GUPPI, status?", "[All systems nominal]")
    r["tags"] = ["#cat-config"]
    r["category"] = "config"
    tag([r])
    assert r["category"] == "config" and "#cat-config" in r["tags"] and "#book1" in r["tags"]
    r2 = rec("GUPPI, status?", "[All systems nominal]")
    tag([r2])
    assert r2["category"] == "status" and "#cat-status" in r2["tags"]


def test_pattern_report_renders():
    txt = pattern_report([rec("a", "[Acknowledged]") | {"category": "ack"}])
    assert "Bracketed" in txt and "| ack |" in txt
