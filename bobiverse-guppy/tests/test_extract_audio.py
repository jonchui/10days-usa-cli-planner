from extract_audio import sentences, strip_brackets, windows

TXT = """
<<PAGE 1>>
14 Bob August 2144 Epsilon Eridani
I looked at the screen. Guppy, status report. All systems nominal. Fine. I went back to work on the
scouts for a while. The sun was bright. Nothing happened for a long time. Still nothing. I was bored.
<<PAGE 2>>
Then something pinged. Contact, unidentified vessel on intercept course. Oh crap.
"""


def test_strip_brackets_removes_typography():
    assert strip_brackets('He said "hi" [Aye] now') == "He said hi Aye now"
    assert strip_brackets("x <<PAGE 3>> y") == "x <<PAGE 3>> y"


def test_windows_find_guppy_scenes_with_page_and_chapter():
    w = windows(TXT, 5)
    assert len(w) == 1
    assert w[0]["page"] == 1 and w[0]["chapter"].startswith("14 Bob") and w[0]["mentions"] == 1
    assert "status report" in w[0]["text"] and "<<PAGE" not in w[0]["text"]
    assert w[0]["id"] == "w5-0001"


def test_sentences_split_on_terminators():
    s = [t for _, _, t in sentences("One. Two! Three? Four")]
    assert [x.strip() for x in s] == ["One.", "Two!", "Three?", "Four"]
