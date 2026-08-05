#!/usr/bin/env python3
"""Math Quest — the terminal version of the daily PEMDAS adventure.

Same engine as index.html: the day's questions are generated from a seed made
of today's date in DD/MM/YY form plus the kid's name, difficulty adapts to how
fast and how accurately they answer, and the level they reach is remembered for
tomorrow in a JSON file next to this script.

    python3 math_quest.py                 # pick a kid, play today's quest
    python3 math_quest.py --kid sydney    # jump straight in
    python3 math_quest.py --length 80     # how many questions today
    python3 math_quest.py --date 05/08/26 # replay a specific day
    python3 math_quest.py --selftest      # validate the generator
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import random
import sys
import time

SAVE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "math_quest_save.json")

# --------------------------------------------------------------------------
# expression engine
# --------------------------------------------------------------------------
# An expression is a list of tokens: numbers, operator strings, or nested
# lists (which mean parentheses). The solver walks it in true PEMDAS order and
# records each step, which is what powers the hints and walkthroughs.

OPS = {
    "+": lambda a, b: a + b,
    "-": lambda a, b: a - b,
    "x": lambda a, b: a * b,
    "/": lambda a, b: a / b,
    "^": lambda a, b: a ** b,
}
RULE_OF = {"^": "Exponents", "x": "Multiply", "/": "Divide", "+": "Add", "-": "Subtract"}
SUPERSCRIPT = {2: "²", 3: "³", 4: "⁴"}


def render(tokens) -> str:
    """Draw the expression the way a textbook would, including 4²."""
    parts: list[str] = []
    i = 0
    while i < len(tokens):
        t = tokens[i]
        if t == "^":
            power = tokens[i + 1]
            parts[-1] += SUPERSCRIPT.get(power, "^" + str(power))
            i += 2
            continue
        parts.append("(" + render(t) + ")" if isinstance(t, list) else str(t))
        i += 1
    return " ".join(parts)


def solve(tokens, steps, wrap=None):
    """Reduce the expression, appending a step dict for every operation.

    `wrap` renders a partially-solved token list back in its full context, so a
    step taken inside parentheses still reports the whole expression rather
    than just the fragment inside the brackets.
    """
    if wrap is None:
        wrap = render
    tokens = list(tokens)

    # 1. Parentheses, innermost first.
    for i, tok in enumerate(tokens):
        if isinstance(tok, list):
            inner_text = render(tok)

            def inner_wrap(inner_tokens, _i=i, _outer=tokens):
                copy = list(_outer)
                copy[_i] = inner_tokens[0] if len(inner_tokens) == 1 else list(inner_tokens)
                return wrap(copy)

            mark = len(steps)
            value = solve(tok, steps, inner_wrap)
            tokens[i] = value
            added = len(steps) - mark
            if added == 1:
                steps[mark]["rule"] = "Parentheses"
                steps[mark]["text"] = f"Parentheses first: ({inner_text}) = {fmt(value)}"
            elif added > 1:
                steps[-1]["text"] += " - that finishes the ( )"
            if steps:
                steps[-1]["after"] = wrap(tokens)

    # 2. Exponents, 3. multiply/divide, 4. add/subtract - each left to right.
    for group in (("^",), ("x", "/"), ("+", "-")):
        i = 1
        while i < len(tokens):
            if tokens[i] in group:
                a, op, b = tokens[i - 1], tokens[i], tokens[i + 1]
                value = OPS[op](a, b)
                tokens[i - 1:i + 2] = [value]
                if op == "^":
                    text = f"{a}{SUPERSCRIPT.get(b, '^' + str(b))} means " + \
                           " x ".join([str(a)] * b) + f" = {fmt(value)}"
                else:
                    text = f"{a} {op} {b} = {fmt(value)}"
                steps.append({"rule": RULE_OF[op], "text": text, "value": value, "after": wrap(tokens)})
                i = 1
            else:
                i += 2
    return tokens[0]


def fmt(value):
    return int(value) if isinstance(value, float) and value.is_integer() else value


def analyse(tokens):
    steps: list[dict] = []
    answer = solve(tokens, steps)
    return {"text": render(tokens), "answer": fmt(answer), "steps": steps}


def rules_used(tokens) -> set:
    found = set()

    def walk(items):
        for t in items:
            if isinstance(t, list):
                found.add("parentheses")
                walk(t)
            elif t == "^":
                found.add("exponents")
            elif t in ("x", "/"):
                found.add("multiply-divide")
            elif t in ("+", "-"):
                found.add("add-subtract")

    walk(tokens)
    return found


# --------------------------------------------------------------------------
# problem shapes
# --------------------------------------------------------------------------

def _div_pair(r, c):
    b = r.randint(2, c["divisor"])
    return b * r.randint(2, c["factor"]), b


SHAPES = {
    "add":     lambda r, c: [r.randint(1, c["term"]), "+", r.randint(1, c["term"])],
    "sub":     lambda r, c: (lambda a: [a, "-", r.randint(1, a)])(r.randint(2, c["term"])),
    "mul":     lambda r, c: [r.choice(c["factors"]), "x", r.randint(2, c["factor"])],
    "addAdd":  lambda r, c: [r.randint(1, c["term"]), "+", r.randint(1, c["term"]), "+", r.randint(1, c["term"])],
    "mulAdd":  lambda r, c: [r.randint(1, c["term"]), "+", r.choice(c["factors"]), "x", r.randint(2, c["factor"])],
    "addMul":  lambda r, c: [r.choice(c["factors"]), "x", r.randint(2, c["factor"]), "+", r.randint(1, c["term"])],
    "mulSub":  lambda r, c: [r.randint(4, c["term"]), "-", r.choice(c["factors"]), "x", r.randint(2, c["factor"])],
    "parenMul": lambda r, c: [[r.randint(1, c["term"]), "+", r.randint(1, c["term"])], "x", r.randint(2, c["factor"])],
    "parenSub": lambda r, c: (lambda a: [[a, "-", r.randint(1, a - 1)], "x", r.randint(2, c["factor"])])(r.randint(3, c["term"])),
    "twoMul":  lambda r, c: [r.choice(c["factors"]), "x", r.randint(2, c["factor"]), "+", r.choice(c["factors"]), "x", r.randint(2, c["factor"])],
    "threeMix": lambda r, c: [r.randint(1, c["term"]), "+", r.choice(c["factors"]), "x", r.randint(2, c["factor"]), "-", r.randint(1, c["term"])],
    "parenMulSub": lambda r, c: [[r.randint(1, c["term"]), "+", r.randint(1, c["term"])], "x", r.randint(2, c["factor"]), "-", r.randint(1, c["term"])],
    "divAdd":  lambda r, c: (lambda p: [p[0], "/", p[1], "+", r.randint(1, c["term"])])(_div_pair(r, c)),
    "addDiv":  lambda r, c: (lambda p: [r.randint(1, c["term"]), "+", p[0], "/", p[1]])(_div_pair(r, c)),
    "mulDiv":  lambda r, c: (lambda p: [r.choice(c["factors"]), "x", r.randint(2, c["factor"]), "+", p[0], "/", p[1]])(_div_pair(r, c)),
    "parenDiv": lambda r, c: (lambda p: [[p[0], "/", p[1]], "+", r.randint(1, c["term"])])(_div_pair(r, c)),
    "parenParen": lambda r, c: (lambda a: [[r.randint(1, c["term"]), "+", r.randint(1, c["term"])], "x", [a, "-", r.randint(1, a - 1)]])(r.randint(3, c["term"])),
    "sqAdd":   lambda r, c: [r.randint(2, c["power"]), "^", 2, "+", r.randint(1, c["term"])],
    "sqMul":   lambda r, c: [r.randint(2, c["power"]), "^", 2, "+", r.choice(c["factors"]), "x", r.randint(2, c["factor"])],
    "parenSq": lambda r, c: [[r.randint(1, 4), "+", r.randint(1, 4)], "^", 2, "-", r.randint(1, c["term"])],
    "mulParen": lambda r, c: (lambda p: [r.randint(2, c["factor"]), "x", [r.randint(1, c["term"]), "+", r.randint(1, c["term"])], "-", p[0], "/", p[1]])(_div_pair(r, c)),
    "nested":  lambda r, c: [[[r.randint(1, c["term"]), "+", r.randint(1, c["term"])], "x", r.randint(2, c["factor"])], "/", r.randint(2, c["divisor"]), "+", r.randint(1, c["term"])],
    "bigMix":  lambda r, c: (lambda p: [r.randint(2, c["power"]), "^", 2, "-", [p[0], "/", p[1], "+", r.randint(1, c["term"])]])(_div_pair(r, c)),
}


def build_problem(rng, shape_names, cfg):
    for _ in range(400):
        name = rng.choice(shape_names)
        tokens = SHAPES[name](rng, cfg)
        info = analyse(tokens)
        answer = info["answer"]
        if not isinstance(answer, int):
            continue
        if answer > cfg["maxAnswer"]:
            continue
        if not cfg.get("allowNegative") and answer < 0:
            continue
        if "minAnswer" in cfg and answer < cfg["minAnswer"]:
            continue
        bad = any(
            not float(s["value"]).is_integer()
            or (not cfg.get("allowNegative") and s["value"] < 0)
            or abs(s["value"]) > cfg["maxAnswer"] * 2
            for s in info["steps"]
        )
        if bad:
            continue
        return {"text": info["text"], "answer": answer, "steps": info["steps"],
                "tokens": tokens, "rules": rules_used(tokens), "shape": name}

    # Guaranteed fallback, still inside the config's own limits.
    tokens = [rng.randint(1, min(6, cfg["term"])), "+", rng.choice(cfg["factors"]),
              "x", rng.randint(2, min(3, cfg["factor"]))]
    info = analyse(tokens)
    return {"text": info["text"], "answer": info["answer"], "steps": info["steps"],
            "tokens": tokens, "rules": rules_used(tokens), "shape": "FALLBACK"}


# --------------------------------------------------------------------------
# the three adventurers
# --------------------------------------------------------------------------
# Sydney's ladder is deliberately gentle: levels 1-3 are single-step warm-ups,
# her times tables never go past 5, answers stay under 45, division only
# appears at level 8 and squares only at level 10. She also climbs slower and
# drops faster than the boys so she stays in the "I can do this" zone.

KIDS = {
    "sydney": {
        "name": "Sydney", "emoji": "(boba)", "short_day": True, "wave": 5,
        "tagline": "Boba & ice cream shop with Stripes the tiger",
        "start": 1, "up_streak": 4, "down_misses": 2, "pace": 40,
        "cfg": {"term": 9, "factor": 5, "factors": [2, 3, 4, 5], "divisor": 4,
                "power": 3, "maxAnswer": 45, "allowNegative": False, "minAnswer": 0},
        "ladder": [
            (["add", "sub"], {"term": 9, "maxAnswer": 18}),
            (["add", "sub", "addAdd"], {"term": 9, "maxAnswer": 24}),
            (["mul", "addAdd"], {"term": 9, "factor": 5, "maxAnswer": 25}),
            (["mulAdd", "addMul"], {"term": 8, "factor": 4, "factors": [2, 3, 4], "maxAnswer": 28}),
            (["mulAdd", "addMul", "mulSub"], {"term": 9, "factor": 5, "maxAnswer": 32}),
            (["parenMul", "parenSub"], {"term": 5, "factor": 4, "maxAnswer": 36}),
            (["parenMul", "mulAdd", "twoMul"], {"term": 6, "factor": 4, "maxAnswer": 40}),
            (["divAdd", "addDiv", "parenDiv"], {"term": 8, "factor": 5, "divisor": 4, "maxAnswer": 40}),
            (["threeMix", "parenMulSub"], {"term": 7, "factor": 4, "maxAnswer": 42}),
            (["sqAdd", "parenMul", "divAdd"], {"term": 8, "factor": 5, "power": 4, "maxAnswer": 45}),
        ],
        "lessons": [
            "Math has an order, like making boba: pearls in the cup FIRST, then the tea.",
            "When you see + and + together, just go left to right, one scoop at a time.",
            "x means groups of. 3 x 4 is 3 cups with 4 pearls each. Count the pearls!",
            "BIG RULE: x always goes before +. Multiply first, then add.",
            "Still x before +. Do the x part, write the small answer down, then finish.",
            "Parentheses ( ) are a hug. Whatever is inside the hug gets done first.",
            "Hug first ( ), then x, then +. Three easy steps, in that order, every time.",
            "/ means sharing fairly. 12 / 3 is 12 sprinkles shared with 3 friends.",
            "The full order: ( ) first, then x and /, then + and - last. You know it all!",
            "A little 2 up high means times itself. 3² = 3 x 3 = 9. Last secret ingredient!",
        ],
        "story": [
            "Stripes the tiger flipped the OPEN sign. First customers are lining up!",
            "A field trip bus just pulled up. Twelve thirsty kids. Go go go!",
            "Someone ordered a rainbow sundae with EVERY topping.",
            "The ice cream machine is making funny noises. Solve fast, keep it cool.",
            "A tiny princess wants a sparkly lychee boba for her spa party.",
            "Stripes spilled the tapioca. Earn it back, one order at a time.",
            "Art class is here! They want drinks in every color of the rainbow.",
            "A food critic walked in wearing sunglasses inside. Stay calm.",
            "Line out the door. You are the fastest boba maker in town.",
            "FINAL ORDER: Stripes' Secret Recipe. Only a master can make it.",
        ],
        "rewards": ["Tapioca Pearls", "Mango Popping Boba", "Whipped Cream", "Rainbow Sprinkles",
                    "Strawberry Drizzle", "Lychee Jelly", "Brown Sugar Swirl", "Sparkle Spa Sticker",
                    "Golden Straw", "Stripes' Secret Recipe"],
        "cheer": ["Yes! Stripes is doing a happy tail wiggle.", "Perfect pour!",
                  "That customer is SO happy.", "You are amazing at this.", "Sweet! Literally."],
        "kind": ["Almost! Look again, you are close.", "Ooh, so close. Try one more time.",
                 "No worries, even Stripes messes up.", "That is a tricky one. Here is a clue."],
    },
    "lucas": {
        "name": "Lucas", "emoji": "(fish)", "short_day": False, "wave": 10,
        "tagline": "Fishing trip - deeper water, rarer fish",
        "start": 2, "up_streak": 3, "down_misses": 2, "pace": 22,
        "cfg": {"term": 12, "factor": 9, "factors": [2, 3, 4, 5, 6, 7, 8, 9], "divisor": 6,
                "power": 6, "maxAnswer": 200, "allowNegative": False},
        "ladder": [
            (["mulAdd", "addMul"], {"term": 10, "factor": 6, "maxAnswer": 70}),
            (["mulAdd", "mulSub", "twoMul"], {"term": 12, "factor": 7, "maxAnswer": 90}),
            (["parenMul", "parenSub"], {"term": 10, "factor": 8, "maxAnswer": 110}),
            (["threeMix", "twoMul", "divAdd"], {"term": 12, "factor": 8, "maxAnswer": 120}),
            (["mulDiv", "parenMulSub", "addDiv"], {"term": 12, "factor": 8, "divisor": 6, "maxAnswer": 130}),
            (["parenParen", "parenMulSub"], {"term": 11, "factor": 8, "maxAnswer": 150}),
            (["sqAdd", "sqMul", "mulDiv"], {"term": 12, "factor": 8, "power": 6, "maxAnswer": 160}),
            (["parenSq", "parenParen", "mulParen"], {"term": 12, "factor": 8, "maxAnswer": 170}),
            (["nested", "mulParen", "sqMul"], {"term": 12, "factor": 9, "divisor": 6, "maxAnswer": 180}),
            (["bigMix", "nested", "parenSq"], {"term": 12, "factor": 9, "power": 7, "maxAnswer": 200}),
        ],
        "lessons": [
            "PEMDAS is your tackle box order: Parentheses, Exponents, Multiply/Divide, Add/Subtract.",
            "Multiply and divide always beat add and subtract. Line up your x and / first.",
            "Parentheses outrank everything. Clear the ( ) before you cast anything else.",
            "Three or more operations? Scan the whole line first, then attack in PEMDAS order.",
            "x and / are equal rank - do them left to right, in the order they appear.",
            "Two sets of parentheses? Solve each one separately, then combine.",
            "Exponents come right after parentheses. 4² = 16 happens before any multiplying.",
            "A parenthesis can be squared: (3 + 2)² means solve inside first, THEN square it.",
            "Nested parentheses: always work from the innermost hook outward.",
            "+ and - are also equal rank - left to right. Never jump to the easy-looking one.",
        ],
        "story": [
            "Dawn on the water. Glassy calm. Perfect conditions.",
            "You found a drop-off. Fish are stacked on the ledge.",
            "Something big just followed your lure to the boat.",
            "Wind picking up. Harder casts, better fish.",
            "You switched to the deep spinner. Nice call.",
            "Weed line ahead - this is where the smart ones hide.",
            "Storm clouds building. Fish are feeding hard before it hits.",
            "You are in 40 feet of water now. Trophy territory.",
            "Your line just went tight and started peeling. Hold on.",
            "Last cast of the day. Everyone knows what happens on the last cast.",
        ],
        "rewards": ["Sunfish", "Bluegill", "Yellow Perch", "Smallmouth Bass", "Walleye",
                    "Northern Pike", "Lake Trout", "Muskie", "Sturgeon", "Legendary Golden Muskie"],
        "cheer": ["Fish on!", "Perfect cast.", "Clean hookset.", "That is a keeper.", "Netted it."],
        "kind": ["Missed the hookset. Reel in and try again.", "It shook off. Happens to everyone.",
                 "Close - check your order of operations.", "Snagged. Look at the hint and re-cast."],
    },
    "jordan": {
        "name": "Jordan", "emoji": "(trophy)", "short_day": False, "wave": 10,
        "tagline": "Trophy road - Bronze to Legendary",
        "start": 3, "up_streak": 3, "down_misses": 2, "pace": 18,
        "cfg": {"term": 14, "factor": 9, "factors": [2, 3, 4, 5, 6, 7, 8, 9], "divisor": 8,
                "power": 8, "maxAnswer": 260, "allowNegative": True, "minAnswer": -30},
        "ladder": [
            (["mulAdd", "twoMul"], {"term": 12, "factor": 8, "maxAnswer": 90}),
            (["parenMul", "threeMix", "mulSub"], {"term": 13, "factor": 9, "maxAnswer": 120}),
            (["parenMulSub", "divAdd", "twoMul"], {"term": 14, "factor": 9, "maxAnswer": 140}),
            (["mulDiv", "parenParen"], {"term": 14, "factor": 9, "divisor": 8, "maxAnswer": 160}),
            (["sqAdd", "sqMul", "parenParen"], {"term": 14, "factor": 9, "power": 7, "maxAnswer": 180}),
            (["parenSq", "mulParen", "mulDiv"], {"term": 14, "factor": 9, "maxAnswer": 200}),
            (["nested", "sqMul", "parenSq"], {"term": 14, "factor": 9, "divisor": 8, "maxAnswer": 220}),
            (["bigMix", "nested", "mulParen"], {"term": 14, "factor": 9, "power": 8, "maxAnswer": 240}),
            (["bigMix", "parenSq", "nested"], {"term": 15, "factor": 9, "power": 8, "maxAnswer": 250}),
            (["bigMix", "nested", "sqMul", "parenSq"], {"term": 15, "factor": 9, "power": 9, "maxAnswer": 260}),
        ],
        "lessons": [
            "PEMDAS is the meta: Parentheses, Exponents, Multiply/Divide, Add/Subtract.",
            "Multiply and divide always outrank add and subtract. No exceptions.",
            "Parentheses are the super. They fire first, every single time.",
            "x and / share a rank - resolve them left to right, not strongest-first.",
            "Exponents come second, right after parentheses. Square before you multiply.",
            "A squared parenthesis: solve the inside completely, then apply the exponent.",
            "Nested parentheses = innermost first. Peel it like layers.",
            "Long expressions: identify every operation before you touch one.",
            "Negative intermediate results are fine. Keep the sign and keep going.",
            "Full send: parentheses, exponents, x / left to right, + - left to right.",
        ],
        "story": [
            "Match starting. Bronze lobby, but everyone starts somewhere.",
            "Two-game win streak. The ladder is moving.",
            "Enemy team is stacked. Focus up.",
            "You just got a triple. Trophies climbing fast.",
            "Diamond lobby. The plays are cleaner up here.",
            "Someone in chat said you got carried. Prove them wrong.",
            "Epic range. Every match counts double now.",
            "One loss from a rank down. Do not choke.",
            "Mythic push. This is the grind you came for.",
            "Legendary gate. Win this and it is on your profile forever.",
        ],
        "rewards": ["Bronze", "Silver", "Gold", "Diamond", "Epic", "Mythic",
                    "Legendary", "Masters", "Pro Badge", "Hall of Fame"],
        "cheer": ["Clean.", "Triple kill.", "Trophies up!", "That was a pro play.", "Star player."],
        "kind": ["Knocked out. Respawn and read the hint.", "Close match. Check your order.",
                 "Lost that round - but rank is not gone.", "They got you. Look at the walkthrough."],
    },
}

HINT_LABELS = {
    "Parentheses": "Look for the parentheses ( ). Whatever is inside gets solved first.",
    "Exponents": "There is a little raised number. That is an exponent - do it right after parentheses.",
    "Multiply": "Find the x or / first. They always go before + and -.",
    "Divide": "Find the x or / first. They always go before + and -.",
    "Add": "Only + and - here, so just work left to right.",
    "Subtract": "Only + and - here, so just work left to right.",
}
COACH_ADVICE = {
    "parentheses": "Parentheses keep sneaking past. Whatever is inside the ( ) gets finished completely before anything else touches it.",
    "exponents": "Exponents are the tricky ones right now. A small raised 2 means 'times itself' - and it happens before any multiplying.",
    "multiply-divide": "The big one to lock in: x and / always happen before + and -, even when the + comes first on the page.",
    "add-subtract": "Watch the left-to-right rule. When it is only + and -, work strictly left to right.",
}

LENGTH_CHOICES = [20, 40, 80, 100]


def question_count(kid_id: str, base: int) -> int:
    kid = KIDS[kid_id]
    if not kid["short_day"]:
        return base
    wave = kid["wave"]
    return max(wave * 2, round(base * 0.4 / wave) * wave)


# --------------------------------------------------------------------------
# save file
# --------------------------------------------------------------------------

def load_all() -> dict:
    try:
        with open(SAVE_PATH, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return {}


def save_all(data: dict) -> None:
    try:
        with open(SAVE_PATH, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2)
    except OSError as exc:
        print(f"(could not save progress: {exc})")


def kid_save(data: dict, kid_id: str) -> dict:
    entry = data.get(kid_id) or {}
    entry.setdefault("level", KIDS[kid_id]["start"])
    entry.setdefault("lifetime_correct", 0)
    entry.setdefault("lifetime_wrong", 0)
    entry.setdefault("best_streak", 0)
    entry.setdefault("rewards", [])
    entry.setdefault("miss_rules", {})
    entry.setdefault("days_played", [])
    data[kid_id] = entry
    return entry


# --------------------------------------------------------------------------
# generation
# --------------------------------------------------------------------------

def make_question(kid_id: str, level: int, day_key: str, salt: str):
    kid = KIDS[kid_id]
    shapes, overrides = kid["ladder"][max(0, min(10, level) - 1)]
    cfg = dict(kid["cfg"])
    cfg.update(overrides)
    rng = random.Random(f"{day_key}|{kid_id}|L{level}|{salt}")
    return build_problem(rng, shapes, cfg)


def date_key(when: dt.date) -> str:
    return when.strftime("%d/%m/%y")


# --------------------------------------------------------------------------
# playing
# --------------------------------------------------------------------------

BAR_WIDTH = 28


def rule_key(step_rule: str) -> str:
    return {"Parentheses": "parentheses", "Exponents": "exponents",
            "Multiply": "multiply-divide", "Divide": "multiply-divide"}.get(step_rule, "add-subtract")


def show_hint(problem: dict, stage: int) -> None:
    steps = problem["steps"]
    if stage == 1:
        print("   HINT: " + HINT_LABELS.get(steps[0]["rule"], HINT_LABELS["Add"]))
    elif stage == 2:
        print(f"   HINT: start with  {steps[0]['text']}")
        print(f"         now it reads  {steps[0]['after']}")
    else:
        print("   WALKTHROUGH:")
        for i, step in enumerate(steps, 1):
            tail = f"   ->  {step['after']}" if step["after"] != str(problem["answer"]) else ""
            print(f"     {i}. [{step['rule']}] {step['text']}{tail}")


def play(kid_id: str, day_key: str, base_length: int) -> None:
    kid = KIDS[kid_id]
    data = load_all()
    save = kid_save(data, kid_id)

    total = question_count(kid_id, base_length)
    level = save["level"]
    streak = best_streak = correct = wrong = wave_misses = 0

    print()
    print("=" * 62)
    print(f"  MATH QUEST  -  {kid['name']}  {kid['emoji']}")
    print(f"  {kid['tagline']}")
    print(f"  Quest key {day_key}   |   {total} questions   |   starting at level {level}")
    print("=" * 62)
    print("  Type your answer and press Enter.  'h' = hint,  'q' = quit early.")

    index = 0
    while index < total:
        wave_index = index // kid["wave"]
        if index % kid["wave"] == 0:
            print()
            print("-" * 62)
            print(f"  WAVE {wave_index + 1}: {kid['story'][min(wave_index, 9)]}")
            print(f"  Coach tip: {kid['lessons'][min(level - 1, 9)]}")
            print("-" * 62)

        problem = make_question(kid_id, level, day_key, f"q{index}")
        asked_at = time.time()
        hint_stage = 0
        attempts = 0

        filled = int(BAR_WIDTH * index / total)
        bar = "#" * filled + "." * (BAR_WIDTH - filled)
        print()
        print(f"  [{bar}] {index + 1}/{total}   level {level}   {correct} right"
              + (f"   {streak} in a row" if streak >= 2 else ""))
        print(f"    {problem['text']}  =  ?")

        while True:
            try:
                raw = input("    your answer > ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\n  Quest paused. Progress saved.")
                save["level"] = level
                save["best_streak"] = max(save["best_streak"], best_streak)
                save_all(data)
                return

            if raw.lower() in ("q", "quit", "exit"):
                print("  Quest paused. Progress saved.")
                save["level"] = level
                save["best_streak"] = max(save["best_streak"], best_streak)
                save_all(data)
                return
            if raw.lower() in ("h", "hint", "?"):
                hint_stage = min(3, hint_stage + 1)
                show_hint(problem, hint_stage)
                continue
            try:
                given = int(raw)
            except ValueError:
                print("   (type a whole number, or 'h' for a hint)")
                continue

            elapsed = time.time() - asked_at
            if given == problem["answer"]:
                correct += 1
                streak += 1
                best_streak = max(best_streak, streak)
                save["lifetime_correct"] += 1
                quick = elapsed <= kid["pace"] * 0.55
                print("   " + ("* " if quick else "") + random.choice(kid["cheer"]))
                if streak >= kid["up_streak"] and elapsed <= kid["pace"] and level < 10:
                    level += 1
                    streak = 0
                    print(f"   >>> LEVEL UP! Now level {level}.")
                break

            wrong += 1
            wave_misses += 1
            streak = 0
            attempts += 1
            save["lifetime_wrong"] += 1
            for r in problem["rules"]:
                save["miss_rules"][r] = save["miss_rules"].get(r, 0) + 1
            print("   " + random.choice(kid["kind"]))
            if wave_misses >= kid["down_misses"] and level > 1:
                level -= 1
                wave_misses = 0
                print(f"   (easing off to level {level})")
            hint_stage = min(hint_stage + 1, 3 if attempts >= 2 else 2)
            show_hint(problem, hint_stage)
            if attempts >= 2:
                print(f"   The answer is {problem['answer']}. Type it in to keep going!")

        index += 1
        if index % kid["wave"] == 0:
            reward = kid["rewards"][min(index // kid["wave"] - 1, 9)]
            if reward not in save["rewards"]:
                save["rewards"].append(reward)
            print()
            print(f"   *** WAVE CLEAR! Unlocked: {reward} ***")
            wave_misses = 0

    total_answered = correct + wrong
    pct = round(correct / total_answered * 100) if total_answered else 100
    save["level"] = level
    save["best_streak"] = max(save["best_streak"], best_streak)
    if day_key not in save["days_played"]:
        save["days_played"].append(day_key)
    save_all(data)

    print()
    print("=" * 62)
    print(f"  QUEST COMPLETE, {kid['name'].upper()}!")
    print(f"  {correct} right  |  level {level}  |  best streak {best_streak}  |  {pct}% first try")
    print(f"  Treasures: {', '.join(save['rewards'])}")
    worst = max(save["miss_rules"], key=save["miss_rules"].get) if save["miss_rules"] else None
    print()
    print("  COACH NOTES")
    if worst and save["miss_rules"][worst] > 1:
        print("  " + COACH_ADVICE[worst])
    else:
        print("  Nothing to fix today. Clean run.")
    print(f"  Days played: {len(save['days_played'])}  |  Lifetime correct: {save['lifetime_correct']}")
    print("=" * 62)


# --------------------------------------------------------------------------
# self test
# --------------------------------------------------------------------------

def selftest() -> int:
    failures = []
    checked = 0
    for kid_id, kid in KIDS.items():
        for level in range(1, 11):
            shapes, overrides = kid["ladder"][level - 1]
            cfg = dict(kid["cfg"])
            cfg.update(overrides)
            lo, hi = 10 ** 9, -10 ** 9
            for i in range(120):
                rng = random.Random(f"05/08/26|{kid_id}|L{level}|q{i}")
                p = build_problem(rng, shapes, cfg)
                checked += 1
                if p["shape"] == "FALLBACK":
                    failures.append(f"{kid_id} L{level}: generator fell back")
                if not isinstance(p["answer"], int):
                    failures.append(f"{kid_id} L{level}: non-integer answer {p['text']}")
                if p["answer"] > cfg["maxAnswer"]:
                    failures.append(f"{kid_id} L{level}: {p['answer']} over cap {cfg['maxAnswer']}")
                if not cfg.get("allowNegative") and p["answer"] < 0:
                    failures.append(f"{kid_id} L{level}: negative answer {p['text']}")
                for s in p["steps"]:
                    if not float(s["value"]).is_integer():
                        failures.append(f"{kid_id} L{level}: fractional step {s['text']}")
                if not p["steps"]:
                    failures.append(f"{kid_id} L{level}: no steps for {p['text']}")
                if analyse(p["tokens"])["answer"] != p["answer"]:
                    failures.append(f"{kid_id} L{level}: unstable solve {p['text']}")
                if kid_id == "sydney":
                    for j in range(1, len(p["tokens"]) - 1):
                        t = p["tokens"]
                        if t[j] == "x" and isinstance(t[j - 1], int) and isinstance(t[j + 1], int):
                            if min(t[j - 1], t[j + 1]) > 5 or max(t[j - 1], t[j + 1]) > 10:
                                failures.append(f"SYDNEY L{level}: hard times-table in {p['text']}")
                lo, hi = min(lo, p["answer"]), max(hi, p["answer"])
            print(f"  {kid_id:<7} L{level:<2} answers {lo:>4} .. {hi:>4}   e.g. {p['text']} = {p['answer']}")

    # determinism, and different days give different quests
    a = make_question("sydney", 4, "05/08/26", "q3")
    b = make_question("sydney", 4, "05/08/26", "q3")
    if a["text"] != b["text"]:
        failures.append("not deterministic for the same date")
    c = make_question("sydney", 4, "06/08/26", "q3")
    if a["text"] == c["text"]:
        failures.append("different dates produce the same question")

    print()
    if failures:
        print(f"FAILURES ({len(failures)}):")
        for f in failures[:20]:
            print("  " + f)
        return 1
    print(f"ALL CHECKS PASSED ({checked} generated questions)")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Math Quest - a daily PEMDAS adventure.")
    parser.add_argument("--kid", choices=sorted(KIDS), help="skip the menu")
    parser.add_argument("--length", type=int, default=80, choices=LENGTH_CHOICES,
                        help="questions per day for Lucas and Jordan (Sydney gets a shorter day)")
    parser.add_argument("--date", help="replay a specific day, in DD/MM/YY form")
    parser.add_argument("--selftest", action="store_true", help="validate the question generator")
    args = parser.parse_args()

    if args.selftest:
        return selftest()

    day_key = args.date or date_key(dt.date.today())

    kid_id = args.kid
    if not kid_id:
        data = load_all()
        print()
        print(f"  MATH QUEST  -  today's quest key is {day_key}")
        print()
        order = ["sydney", "lucas", "jordan"]
        for i, kid in enumerate(order, 1):
            saved = (data.get(kid) or {}).get("level", KIDS[kid]["start"])
            count = question_count(kid, args.length)
            print(f"   {i}. {KIDS[kid]['name']:<7} level {saved:<3} {count:>3} questions   {KIDS[kid]['tagline']}")
        print()
        try:
            choice = input("  Who is playing? (1-3) > ").strip()
        except (EOFError, KeyboardInterrupt):
            return 0
        if choice not in ("1", "2", "3"):
            print("  Pick 1, 2 or 3.")
            return 1
        kid_id = order[int(choice) - 1]

    play(kid_id, day_key, args.length)
    return 0


if __name__ == "__main__":
    sys.exit(main())
