from extract import extract, split_chapters

SAMPLE = """
<<PAGE 1>>
12. Bob – August 17, 2133 – Sol

I lit the drive and settled in. "GUPPI, status report."

[All systems nominal]

Fine. "How long to Epsilon Eridani?"

[Estimated transit time: eleven years]

<<PAGE 2>>
13. Bill – March 3, 2145 – Epsilon Eridani

Something pinged. [Contact. Unidentified vessel on intercept course]

I had been out for [18 hours] of downtime.
[STATUS REPORT]
[Drive: Nominal]
"""


def test_split_chapters_finds_headings():
    ch = split_chapters(SAMPLE)
    assert [c[0].split(".")[0] for c in ch] == ["12", "13"]


def test_extract_pairs_inputs_and_outputs():
    recs = extract(SAMPLE, book=1, chars_per_page=100)
    outs = [r["output"] for r in recs]
    assert outs == ["[All systems nominal]", "[Estimated transit time: eleven years]",
                    "[Contact. Unidentified vessel on intercept course]", "[18 hours]",
                    "[STATUS REPORT]\n[Drive: Nominal]"]
    assert recs[0]["input"] == "GUPPI, status report." and recs[0]["input_type"] == "command"
    assert recs[1]["input_type"] == "question"
    assert recs[2]["bob"] == "Bill" and recs[2]["page"] == 2 and recs[2]["chapter_index"] == 2
    assert recs[3]["category"] == "interject" and recs[3]["input_type"] == "banter"
    assert recs[0]["id"] == "b1-0001" and recs[0]["provenance"] == "verified"
