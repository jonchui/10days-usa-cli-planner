from common import normalize, score_pair, token_f1


def test_normalize_ignores_brackets_case_punct():
    assert normalize("[Acknowledged.]") == normalize("acknowledged")
    assert normalize("[All systems nominal]") == "all systems nominal"


def test_score_pair_exact_and_normalized():
    s = score_pair("[Acknowledged]", "[Acknowledged]")
    assert s["exact"] and s["normalized"] and s["f1"] == 1.0 and s["bracket_ok"]
    s = score_pair("Acknowledged", "[Acknowledged]")
    assert not s["exact"] and s["normalized"] and not s["bracket_ok"]


def test_f1_partial():
    assert 0 < token_f1("[Negative]", "[Negative. No match in database]") < 1
    assert token_f1("[Working]", "[Affirmative]") == 0.0


def test_eval_context_never_shows_gold_or_following_text():
    from common import eval_context, format_input
    rec = {"setting": "x", "context": "He said [Aye] and waited. ▸ [I exist to serve] then more", "input_type": "command", "bob": "Bob-1", "input": "Go."}
    assert eval_context(rec) == "He said […] and waited."
    assert "exist" not in format_input(rec)
