from extract import extract, split_chapters

SAMPLE = """Bob – August 17, 2133 – Sol

I lit the drive and settled in. "GUPPI, status report."

[All systems nominal]

Fine. "How long to Epsilon Eridani?"

[Estimated transit time: eleven years]

Bill – March 3, 2145 – Epsilon Eridani

Something pinged. [Contact. Unidentified vessel on intercept course]

The year was [2145] which is not speech.
"""


def test_split_chapters_finds_headings():
    ch = split_chapters(SAMPLE)
    assert [c[0].split("–")[0].strip() for c in ch] == ["Bob", "Bill"]


def test_extract_pairs_inputs_and_outputs():
    recs = extract(SAMPLE, book=1, chars_per_page=100)
    outs = [r["output"] for r in recs]
    assert outs == ["[All systems nominal]", "[Estimated transit time: eleven years]",
                    "[Contact. Unidentified vessel on intercept course]"]
    assert recs[0]["input"] == "GUPPI, status report."
    assert recs[1]["input_type"] == "question"
    assert recs[2]["bob"] == "Bill" and recs[2]["input_type"] == "event"
    assert recs[2]["chapter_index"] == 2 and recs[2]["page"] >= 1 and recs[2]["location"] >= 0
    assert recs[0]["id"] == "b1-0001" and recs[0]["provenance"] == "verified"
