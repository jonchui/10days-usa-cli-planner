#!/usr/bin/env python3
"""Printable PEMDAS worksheets - 50 questions laid out 5 across and 10 down.

Same question engine as the game, so a printed sheet matches the level the kid
is actually playing at. PDF output uses fpdf2 (https://github.com/py-pdf/fpdf2).

    pip install fpdf2

    python3 worksheet.py                    # all three kids, today's date
    python3 worksheet.py --kid sydney       # just Sydney
    python3 worksheet.py --level 4          # pin the difficulty
    python3 worksheet.py --count 50         # how many questions (default 50)
    python3 worksheet.py --cols 5           # columns across the page (default 5)
    python3 worksheet.py --no-ramp          # every question at the same level
    python3 worksheet.py --out ~/Desktop    # where to write the PDFs

Each sheet gets a matching answer key on page 2 in the same grid, so checking
them is a straight left-to-right read.
"""

from __future__ import annotations

import argparse
import datetime as dt
import os
import sys

import math_quest as mq

try:
    from fpdf import FPDF
except ImportError:
    sys.exit(
        "This needs fpdf2. Install it with:\n\n    pip install fpdf2\n\n"
        "(https://github.com/py-pdf/fpdf2)"
    )

# Core PDF fonts cover Latin-1, which includes x, / and the superscripts, so no
# font files need shipping alongside this script.
FONT = "Helvetica"
PRETTY = {" x ": "  ×  ", " / ": "  ÷  ", "^2": "²", "^3": "³", "^4": "⁴"}


def pretty(text: str) -> str:
    """Turn the engine's ASCII operators into real textbook symbols."""
    out = text
    for plain, symbol in PRETTY.items():
        out = out.replace(plain, symbol)
    return out


# The first level on each kid's ladder where an expression actually mixes
# precedence - i.e. where PEMDAS starts to matter at all. Sydney's first three
# levels are deliberately single-operation warm-ups, which are right for her
# first minutes in the game but make a useless order-of-operations worksheet.
PEMDAS_FLOOR = {"sydney": 4, "lucas": 1, "jordan": 1}


def level_band(kid_id: str, level: int, ramp: bool) -> tuple[int, int]:
    floor = PEMDAS_FLOOR[kid_id]
    if not ramp:
        return level, level
    return max(floor, level - 1), max(floor, min(10, level + 1))


def levels_for(count: int, low: int, high: int) -> list[int]:
    """Spread the questions evenly across the band, easiest first."""
    span = high - low + 1
    return [low + min(span - 1, i * span // count) for i in range(count)]


def saved_level(kid_id: str) -> int:
    data = mq.load_all()
    entry = data.get(kid_id) or {}
    return int(entry.get("level", mq.KIDS[kid_id]["start"]))


def build_problems(kid_id: str, day_key: str, count: int, low: int, high: int):
    """Fill the sheet, rejecting repeats so nobody answers 7 - 3 four times."""
    problems = []
    seen = set()
    for i, lvl in enumerate(levels_for(count, low, high)):
        chosen = None
        for attempt in range(60):
            # "sheet" in the salt keeps printed sheets from duplicating the
            # exact questions the kid gets on screen the same day.
            candidate = mq.make_question(kid_id, lvl, day_key, f"sheet{i}-{attempt}")
            if candidate["text"] not in seen:
                chosen = candidate
                break
        if chosen is None:
            # Small level, exhausted pool - a repeat beats a short sheet.
            chosen = mq.make_question(kid_id, lvl, day_key, f"sheet{i}-0")
        seen.add(chosen["text"])
        problems.append(chosen)
    return problems


def fit_font(pdf: FPDF, text: str, max_width: float, start: float = 11.0) -> float:
    """Shrink the type until the expression fits its column."""
    size = start
    while size > 5.5:
        pdf.set_font(FONT, "", size)
        if pdf.get_string_width(text) <= max_width:
            return size
        size -= 0.5
    return 5.5


def grid(pdf: FPDF, entries: list[str], cols: int, rows: int,
         left: float, top: float, width: float, height: float,
         answer_line: bool) -> None:
    col_w = width / cols
    row_h = height / rows
    for index, text in enumerate(entries):
        col, row = index % cols, index // cols
        if row >= rows:
            break
        x = left + col * col_w
        y = top + row * row_h

        pdf.set_font(FONT, "", 7)
        pdf.set_text_color(150)
        pdf.set_xy(x, y)
        pdf.cell(col_w, 4, f"{index + 1}.", align="L")

        pdf.set_text_color(0)
        size = fit_font(pdf, text, col_w - 4)
        pdf.set_font(FONT, "", size)
        pdf.set_xy(x, y + 4)
        pdf.cell(col_w - 3, 6, text, align="L")

        if answer_line:
            pdf.set_draw_color(190)
            pdf.set_line_width(0.3)
            pdf.line(x + 2, y + 15, x + col_w - 5, y + 15)


def add_sheet(pdf: FPDF, kid_id: str, day_key: str, problems, cols: int,
              low: int, high: int) -> None:
    kid = mq.KIDS[kid_id]
    count = len(problems)
    rows = (count + cols - 1) // cols

    for is_key in (False, True):
        pdf.add_page()
        left, top = pdf.l_margin, pdf.t_margin

        pdf.set_font(FONT, "B", 20)
        pdf.set_text_color(0)
        pdf.set_xy(left, top)
        title = f"{kid['name']}'s Math Quest" + ("  -  ANSWER KEY" if is_key else "")
        pdf.cell(0, 9, title, align="L")

        pdf.set_font(FONT, "", 9.5)
        pdf.set_text_color(110)
        pdf.set_xy(left, top + 10)
        band = f"level {low}" if low == high else f"levels {low}-{high}"
        pdf.cell(0, 5, f"{count} questions  ({cols} across, {rows} down)   |   "
                       f"{band}   |   quest key {day_key}", align="L")

        pdf.set_xy(left, top + 16)
        if is_key:
            pdf.cell(0, 5, "Remember: parentheses, then exponents, "
                           "then x and / left to right, then + and - left to right.", align="L")
        else:
            pdf.cell(0, 5, "Name: ______________________________     "
                           "Date: ______________     Time: ______________", align="L")

        pdf.set_draw_color(0)
        pdf.set_line_width(0.6)
        pdf.line(left, top + 24, pdf.w - pdf.r_margin, top + 24)

        body_top = top + 30
        body_height = pdf.h - pdf.b_margin - body_top - 8
        entries = [
            (f"{pretty(p['text'])} = {p['answer']}" if is_key else f"{pretty(p['text'])} =")
            for p in problems
        ]
        grid(pdf, entries, cols, rows, left, body_top,
             pdf.w - pdf.l_margin - pdf.r_margin, body_height, answer_line=not is_key)

        pdf.set_font(FONT, "", 7.5)
        pdf.set_text_color(150)
        pdf.set_xy(left, pdf.h - pdf.b_margin - 5)
        pdf.cell(0, 4, kid["tagline"] + "   |   Math Quest", align="L")


def make_pdf(kid_id: str, day_key: str, count: int, cols: int,
             level: int | None, ramp: bool, out_dir: str) -> str:
    # An explicit --level is obeyed exactly; otherwise start from where they
    # are in the game but never below the level where PEMDAS begins.
    if level is not None:
        lvl = level
    else:
        lvl = max(saved_level(kid_id), PEMDAS_FLOOR[kid_id])
    low, high = level_band(kid_id, lvl, ramp)
    problems = build_problems(kid_id, day_key, count, low, high)

    pdf = FPDF(orientation="P", unit="mm", format="Letter")
    pdf.set_auto_page_break(False)
    pdf.set_margins(11, 11, 11)
    pdf.set_title(f"Math Quest - {mq.KIDS[kid_id]['name']} - {day_key}")
    add_sheet(pdf, kid_id, day_key, problems, cols, low, high)

    stamp = day_key.replace("/", "-")
    path = os.path.join(out_dir, f"mathquest-{kid_id}-{stamp}.pdf")
    pdf.output(path)
    return path


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Printable PEMDAS worksheets, 5 across and 10 down.")
    parser.add_argument("--kid", choices=sorted(mq.KIDS) + ["all"], default="all")
    parser.add_argument("--count", type=int, default=50, help="questions per sheet (default 50)")
    parser.add_argument("--cols", type=int, default=5, help="columns across (default 5)")
    parser.add_argument("--level", type=int, choices=range(1, 11), metavar="1-10",
                        help="pin the difficulty (default: whatever level they are on)")
    parser.add_argument("--no-ramp", dest="ramp", action="store_false",
                        help="keep every question at the same level")
    parser.add_argument("--date", help="quest key to use, in DD/MM/YY form")
    parser.add_argument("--out", default=".", help="where to write the PDFs")
    args = parser.parse_args()

    if args.count < 1 or args.cols < 1:
        parser.error("--count and --cols must be positive")

    day_key = args.date or mq.date_key(dt.date.today())
    out_dir = os.path.abspath(os.path.expanduser(args.out))
    os.makedirs(out_dir, exist_ok=True)

    kids = sorted(mq.KIDS) if args.kid == "all" else [args.kid]
    for kid_id in kids:
        path = make_pdf(kid_id, day_key, args.count, args.cols,
                        args.level, args.ramp, out_dir)
        print(f"  {mq.KIDS[kid_id]['name']:<7} -> {path}")
    print("\n  Open them and hit Cmd-P. Page 1 is the worksheet, page 2 the answer key.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
