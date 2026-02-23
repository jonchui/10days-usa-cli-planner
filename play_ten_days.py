from __future__ import annotations

import os
import random
import re
from dataclasses import dataclass, field

import ten_days_usa as game


PLANE_COLORS = ["red", "green", "yellow", "light_blue", "dark_blue"]
ANSI_RESET = "\033[0m"
ANSI_BOLD = "\033[1m"
ANSI_COLORS = {
    "red": "\033[31m",
    "green": "\033[32m",
    "yellow": "\033[33m",
    "light_blue": "\033[96m",
    "dark_blue": "\033[38;5;19m",
    "white": "\033[97m",
}

STATE_EMOJI = {
    "Alabama": "🎸",
    "Alaska": "❄️",
    "Arizona": "🏜️",
    "Arkansas": "⛰️",
    "California": "🌉",
    "Colorado": "🏔️",
    "Connecticut": "⚓",
    "Delaware": "🦀",
    "Florida": "🐊",
    "Georgia": "🍑",
    "Hawaii": "🌺",
    "Idaho": "🥔",
    "Illinois": "🌆",
    "Indiana": "🏎️",
    "Iowa": "🌽",
    "Kansas": "🌻",
    "Kentucky": "🐎",
    "Louisiana": "🎷",
    "Maine": "🦞",
    "Maryland": "🦀",
    "Massachusetts": "🏛️",
    "Michigan": "🌊",
    "Minnesota": "🛶",
    "Mississippi": "🎺",
    "Missouri": "🌉",
    "Montana": "🦬",
    "Nebraska": "🌽",
    "Nevada": "🎰",
    "New Hampshire": "🍁",
    "New Jersey": "🛣️",
    "New Mexico": "🎈",
    "New York": "🗽",
    "North Carolina": "🏖️",
    "North Dakota": "🌾",
    "Ohio": "🎡",
    "Oklahoma": "🛣️",
    "Oregon": "🌲",
    "Pennsylvania": "🔔",
    "Rhode Island": "⛵",
    "South Carolina": "🏖️",
    "South Dakota": "🦬",
    "Tennessee": "🎵",
    "Texas": "🤠",
    "Utah": "🏜️",
    "Vermont": "🍁",
    "Virginia": "🏛️",
    "Washington": "☕",
    "West Virginia": "⛏️",
    "Wisconsin": "🧀",
    "Wyoming": "🦬",
}


@dataclass
class Player:
    name: str
    is_human: bool
    hand: list[dict]


@dataclass
class GameSettings:
    show_map: bool = True
    default_edit_method: str = "cursor"
    plane_per_color: int = 2
    drive_cards: int = 5
    transaction_log: list[str] = field(default_factory=list)


def use_color_output() -> bool:
    if os.environ.get("NO_COLOR"):
        return False
    return True


def paint(text: str, color: str, *, bold: bool = False) -> str:
    if not use_color_output():
        return text
    prefix = ANSI_COLORS.get(color, "")
    if bold:
        prefix = ANSI_BOLD + prefix
    if not prefix:
        return text
    return f"{prefix}{text}{ANSI_RESET}"


def color_token(color: str) -> str:
    return paint(color, color, bold=True)


ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


def visible_len(text: str) -> int:
    return len(ANSI_RE.sub("", text))


def pad_ansi(text: str, width: int) -> str:
    needed = max(0, width - visible_len(text))
    return text + (" " * needed)


def card_text(card: dict) -> str:
    if card["type"] == "state":
        return state_text(card["state"], short=False)
    if card["type"] == "plane":
        return "✈️ Plane"
    return "🚗 Drive"


def card_color(card: dict) -> str | None:
    if card["type"] == "state":
        return game.STATE_COLORS[card["state"]]
    if card["type"] == "plane":
        return card["color"]
    return None


def card_label(card: dict) -> str:
    text = card_text(card)
    color = card_color(card)
    if color:
        return paint(text, color, bold=True)
    return text


def state_emoji(state: str) -> str:
    return STATE_EMOJI.get(state, "🗺️")


def state_text(state: str, *, short: bool) -> str:
    # Canonical state label formatter: use this everywhere state text is rendered.
    if short:
        return f"{STATE_ABBR[state]}{state_emoji(state)}"
    return f"{state_emoji(state)} {state}"


def state_map_token(state: str) -> str:
    return state_text(state, short=True)


def validate_state_formatters() -> None:
    """
    Lightweight DRY guard: keep all state UI text flowing through state_text().
    Fails fast if formatter behavior drifts during future edits.
    """
    for state in game.STATE_ADJACENCY.keys():
        long_label = state_text(state, short=False)
        short_label = state_text(state, short=True)
        emoji = state_emoji(state)
        assert state in long_label
        assert STATE_ABBR[state] in short_label
        assert emoji in long_label and emoji in short_label


def describe_hand(hand: list[dict]) -> str:
    return ", ".join(f"{i}:{card_label(c)}" for i, c in enumerate(hand))


def render_hand_slots(hand: list[dict]) -> str:
    width = max(16, max(visible_len(f"[{card_label(c)}]") for c in hand) + 3)
    top = "".join(pad_ansi(f"{i+1:>2}", width) for i in range(len(hand)))
    bottom = "".join(pad_ansi(f"[{card_label(c)}]", width) for c in hand)
    idx = "".join(pad_ansi(f"({i})", width) for i in range(len(hand)))
    return f"{top}\n{bottom}\n{idx}"


def format_route(route: list[dict]) -> str:
    return " -> ".join(card_label(card) for card in route)


def show_color_legend() -> None:
    print(
        "Color legend:",
        ", ".join(f"{paint(k, k, bold=True)}" for k in ["red", "green", "yellow", "light_blue", "dark_blue", "white"]),
    )


STATE_ABBR = {
    "Alabama": "AL",
    "Alaska": "AK",
    "Arizona": "AZ",
    "Arkansas": "AR",
    "California": "CA",
    "Colorado": "CO",
    "Connecticut": "CT",
    "Delaware": "DE",
    "Florida": "FL",
    "Georgia": "GA",
    "Hawaii": "HI",
    "Idaho": "ID",
    "Illinois": "IL",
    "Indiana": "IN",
    "Iowa": "IA",
    "Kansas": "KS",
    "Kentucky": "KY",
    "Louisiana": "LA",
    "Maine": "ME",
    "Maryland": "MD",
    "Massachusetts": "MA",
    "Michigan": "MI",
    "Minnesota": "MN",
    "Mississippi": "MS",
    "Missouri": "MO",
    "Montana": "MT",
    "Nebraska": "NE",
    "Nevada": "NV",
    "New Hampshire": "NH",
    "New Jersey": "NJ",
    "New Mexico": "NM",
    "New York": "NY",
    "North Carolina": "NC",
    "North Dakota": "ND",
    "Ohio": "OH",
    "Oklahoma": "OK",
    "Oregon": "OR",
    "Pennsylvania": "PA",
    "Rhode Island": "RI",
    "South Carolina": "SC",
    "South Dakota": "SD",
    "Tennessee": "TN",
    "Texas": "TX",
    "Utah": "UT",
    "Vermont": "VT",
    "Virginia": "VA",
    "Washington": "WA",
    "West Virginia": "WV",
    "Wisconsin": "WI",
    "Wyoming": "WY",
}


ABBR_TO_STATE = {abbr: name for name, abbr in STATE_ABBR.items()}


# Approximate node placement to resemble USA layout in text mode.
# Coordinates are in character-space for ASCII graph rendering.
MAP_POS = {
    "WA": (6, 2),
    "OR": (6, 6),
    "CA": (6, 10),
    "ID": (12, 5),
    "NV": (11, 9),
    "UT": (16, 9),
    "AZ": (14, 13),
    "MT": (18, 2),
    "WY": (19, 6),
    "CO": (21, 10),
    "NM": (21, 14),
    "ND": (28, 2),
    "SD": (28, 6),
    "NE": (28, 9),
    "KS": (28, 12),
    "OK": (28, 15),
    "TX": (28, 18),
    "MN": (34, 3),
    "IA": (34, 7),
    "MO": (34, 11),
    "AR": (34, 15),
    "LA": (34, 19),
    "WI": (40, 4),
    "IL": (40, 8),
    "MS": (40, 16),
    "MI": (46, 4),
    "IN": (45, 8),
    "OH": (50, 8),
    "KY": (46, 11),
    "TN": (46, 14),
    "AL": (45, 18),
    "GA": (50, 18),
    "FL": (54, 22),
    "SC": (54, 15),
    "NC": (54, 13),
    "VA": (58, 11),
    "WV": (54, 10),
    "PA": (56, 8),
    "NY": (58, 5),
    "VT": (62, 4),
    "NH": (64, 4),
    "ME": (67, 2),
    "MA": (63, 6),
    "CT": (62, 7),
    "RI": (64, 7),
    "NJ": (59, 8),
    "DE": (60, 10),
    "MD": (58, 10),
    "AK": (4, 22),
    "HI": (12, 23),
}


def _edge_glyph(dx: int, dy: int) -> str:
    if dy == 0:
        return "-"
    if dx == 0:
        return "|"
    return "/" if (dx > 0 and dy < 0) or (dx < 0 and dy > 0) else "\\"


def _draw_edge(canvas: list[list[str]], x1: int, y1: int, x2: int, y2: int) -> None:
    dx = x2 - x1
    dy = y2 - y1
    steps = max(abs(dx), abs(dy))
    if steps <= 1:
        return
    # Draw a single connector mark at midpoint to reduce clutter.
    # This keeps adjacency visible while preserving a cleaner USA shape.
    x = round((x1 + x2) / 2)
    y = round((y1 + y2) / 2)
    if y < 0 or y >= len(canvas) or x < 0 or x >= len(canvas[0]):
        return

    if abs(dx) >= abs(dy) * 2:
        glyph = "-"
    elif abs(dy) >= abs(dx) * 2:
        glyph = "|"
    else:
        glyph = _edge_glyph(dx, dy)

    if canvas[y][x].strip() == "":
        canvas[y][x] = glyph
    elif canvas[y][x] in {"-", "|", "/", "\\"} and canvas[y][x] != glyph:
        canvas[y][x] = "+"


MAP_HEADER = "USA adjacency map (lines show neighboring borders)"


def _build_map_canvas() -> list[list[str]]:
    width = 74
    height = 26
    canvas = [[" " for _ in range(width)] for _ in range(height)]

    # Draw bordering edges from adjacency graph.
    for state, neighbors in game.STATE_ADJACENCY.items():
        a = STATE_ABBR[state]
        if a not in MAP_POS:
            continue
        x1, y1 = MAP_POS[a]
        for n in neighbors:
            b = STATE_ABBR[n]
            if b not in MAP_POS or a >= b:
                continue
            x2, y2 = MAP_POS[b]
            _draw_edge(canvas, x1, y1, x2, y2)

    # Draw nodes last so they stand over edges.
    for abbr, (x, y) in MAP_POS.items():
        if 0 <= y < height and 0 <= x < width - 1:
            canvas[y][x] = abbr[0]
            canvas[y][x + 1] = abbr[1]

    return canvas


def get_map_lines(*, colorize: bool) -> list[str]:
    canvas = _build_map_canvas()
    width = len(canvas[0]) if canvas else 0
    state_at = {(y, x): ABBR_TO_STATE[abbr] for abbr, (x, y) in MAP_POS.items()}
    lines: list[str] = []

    if colorize:
        for y, row in enumerate(canvas):
            x = 0
            out = ""
            while x < width:
                state = state_at.get((y, x))
                if state:
                    out += paint(state_map_token(state), game.STATE_COLORS[state], bold=True)
                    x += 2
                else:
                    out += row[x]
                    x += 1
            lines.append(out.rstrip())
    else:
        lines = ["".join(row).rstrip() for row in canvas]

    return [MAP_HEADER, ""] + lines


def render_text_map() -> str:
    return "\n".join(get_map_lines(colorize=True))


def render_text_map_plain() -> str:
    return "\n".join(get_map_lines(colorize=False))


def draw_map_curses(stdscr, start_row: int, color_pair_for: dict[str, int]) -> int:
    import curses

    lines = get_map_lines(colorize=False)
    max_rows = curses.LINES
    max_cols = max(1, curses.COLS - 1)
    row = start_row
    for line in lines:
        if row >= max_rows - 1:
            break
        stdscr.addstr(row, 0, line[:max_cols])
        row += 1

    # Overlay colored abbreviations using the same map coordinates.
    # +2 for header + blank line from get_map_lines()
    row_offset = start_row + 2
    for abbr, (x, y) in MAP_POS.items():
        state = ABBR_TO_STATE[abbr]
        color = game.STATE_COLORS[state]
        attr = curses.color_pair(color_pair_for.get(color, 0)) | curses.A_BOLD
        token = state_map_token(state)
        draw_y = row_offset + y
        if draw_y < 0 or draw_y >= max_rows - 1:
            continue
        if x < 0 or x + len(token) >= max_cols:
            continue
        stdscr.addstr(draw_y, x, token, attr)

    return row


def build_default_deck(plane_per_color: int = 2, drive_cards: int = 5) -> list[dict]:
    deck = [game.card_from_string(state) for state in game.STATE_ADJACENCY.keys()]
    for color in PLANE_COLORS:
        for _ in range(plane_per_color):
            deck.append({"type": "plane", "color": color})
    for _ in range(drive_cards):
        deck.append({"type": "drive"})
    return deck


def draw(deck: list[dict]) -> dict:
    return deck.pop()


def refill_discard_row(deck: list[dict], discard_row: list[dict]) -> None:
    while len(discard_row) < 3 and deck:
        discard_row.append(draw(deck))


def score_hand(analysis: dict) -> tuple:
    if analysis["full_routes"] > 0:
        return (2, analysis["full_routes"], analysis["best_length"])
    return (1, analysis["best_length"], 0)


def utility_score(analysis: dict) -> int:
    # Hand utility for move ranking, not exact game-theory win probability.
    if analysis["full_routes"] > 0:
        return 100_000 + analysis["full_routes"]
    return analysis["best_length"] * 100


def clone_hand(hand: list[dict]) -> list[dict]:
    return [dict(card) for card in hand]


def hand_signature(hand: list[dict]) -> tuple[tuple[str, str], ...]:
    return tuple(card_key(card) for card in hand)


def log_transaction(
    settings: GameSettings,
    *,
    action: str,
    before: list[dict],
    after: list[dict],
) -> None:
    if hand_signature(before) == hand_signature(after):
        return
    settings.transaction_log.append(
        f"{action}: {' | '.join(card_text(c) for c in before)} -> {' | '.join(card_text(c) for c in after)}"
    )


def print_transaction_tail(settings: GameSettings, limit: int = 5) -> None:
    if not settings.transaction_log:
        print("No transactions yet.")
        return
    print("Recent transactions:")
    for line in settings.transaction_log[-limit:]:
        print("  -", line)


def card_key(card: dict) -> tuple[str, str]:
    if card["type"] == "state":
        return ("state", card["state"])
    if card["type"] == "plane":
        return ("plane", card["color"])
    return ("drive", "drive")


def card_from_key(key: tuple[str, str]) -> dict:
    t, v = key
    if t == "state":
        return {"type": "state", "state": v}
    if t == "plane":
        return {"type": "plane", "color": v}
    return {"type": "drive"}


def analyze_from_start(hand: list[dict], start_state: str, *, max_routes: int = 3) -> dict:
    forced = game.solve_routes(hand, drive_include_adjacent=False, max_routes=max_routes, forced_start_state=start_state)
    base = game.analyze_hand(hand, drive_include_adjacent=False, max_routes=max_routes)
    return {
        "forced_routes": forced["count"],
        "forced_samples": forced["routes"],
        "best_length": base["best_length"],
        "utility": 100_000 + forced["count"] if forced["count"] > 0 else base["best_length"] * 100,
    }


def best_discard_after_pick(hand: list[dict], pick: dict, *, start_state: str | None = None) -> dict:
    best = None
    best_discard = None
    best_hand = None
    best_analysis = None
    for i in range(len(hand) + 1):
        new_hand = hand + [pick]
        discard = new_hand.pop(i)
        if start_state:
            s_analysis = analyze_from_start(new_hand, start_state, max_routes=3)
            score = (2, s_analysis["forced_routes"], s_analysis["best_length"])
        else:
            s_analysis = game.analyze_hand(new_hand, drive_include_adjacent=False, max_routes=3)
            score = score_hand(s_analysis)
        if best is None or score > best:
            best = score
            best_discard = discard
            best_hand = new_hand
            best_analysis = s_analysis
    return {"discard": best_discard, "hand": best_hand, "score": best, "analysis": best_analysis}


def show_analysis(hand: list[dict]) -> None:
    analysis = game.analyze_hand(hand, drive_include_adjacent=False, max_routes=3)
    if analysis["full_routes"] > 0:
        print(f"Full routes: {analysis['full_routes']}")
    else:
        print("No full 10-card route yet.")


def show_pick_suggestions(hand: list[dict], discard_row: list[dict]) -> None:
    print("Suggestions if you take a discard:")
    for i, card in enumerate(discard_row):
        result = best_discard_after_pick(hand, card)
        analysis = game.analyze_hand(result["hand"], drive_include_adjacent=False, max_routes=1)
        if analysis["full_routes"] > 0:
            summary = f"routes {analysis['full_routes']}"
        else:
            summary = f"best length {analysis['best_length']}"
        print(
            f"  - take d{i}:{card_label(card)} -> discard {card_label(result['discard'])} -> {summary}"
        )
    print("If you draw from deck, we will evaluate after you see the card.")


def render_turn_ui(hand: list[dict], discard_row: list[dict], settings: GameSettings) -> None:
    if settings.show_map:
        print("\nUSA map (text):")
        print(render_text_map())
    print("\nYour hand:")
    print(render_hand_slots(hand))
    print("Discard row:")
    for i, c in enumerate(discard_row):
        print(f"  d{i}: {card_label(c)}")


def estimate_draw_probabilities(
    settings: GameSettings,
    hand: list[dict],
    discard_row: list[dict],
) -> list[tuple[dict, int, int, float]]:
    pool: dict[tuple[str, str], int] = {}
    for state in game.STATE_ADJACENCY.keys():
        pool[("state", state)] = 1
    for color in PLANE_COLORS:
        pool[("plane", color)] = settings.plane_per_color
    pool[("drive", "drive")] = settings.drive_cards

    for card in hand + discard_row:
        key = card_key(card)
        if key in pool and pool[key] > 0:
            pool[key] -= 1

    remaining = [(card_from_key(k), c) for k, c in pool.items() if c > 0]
    total = sum(c for _, c in remaining)
    if total <= 0:
        return []
    ranked = sorted(
        [(card, c, total, (100.0 * c / total)) for card, c in remaining],
        key=lambda x: (-x[3], card_text(x[0])),
    )
    return ranked


def autocomplete_planner(
    hand: list[dict],
    discard_row: list[dict],
    settings: GameSettings,
) -> None:
    state_indices = [i for i, c in enumerate(hand) if c["type"] == "state"]
    if not state_indices:
        print("No state cards in hand; cannot set start state.")
        return

    print("Choose start state index:")
    print(" ".join(f"{i}:{card_label(hand[i])}" for i in state_indices))
    try:
        idx = int(input("start> ").strip())
    except Exception:
        print("Invalid index.")
        return
    if idx not in state_indices:
        print("Start must be a state card index from your hand.")
        return
    start_state = hand[idx]["state"]
    print(f"Planner start state: {card_label(hand[idx])}")

    current = analyze_from_start(hand, start_state, max_routes=3)
    print(f"Current hand from start -> full routes: {current['forced_routes']}")
    for r in current["forced_samples"][:3]:
        print("  -", format_route(r))

    print("\nDiscard pickup options:")
    for i, d in enumerate(discard_row):
        result = best_discard_after_pick(hand, d, start_state=start_state)
        a = result["analysis"]
        print(
            f"  d{i}:{card_label(d)} -> discard {card_label(result['discard'])} "
            f"-> routes from start: {a['forced_routes']}"
        )
        for r in a["forced_samples"][:2]:
            print("     ", format_route(r))

    probs = estimate_draw_probabilities(settings, hand, discard_row)
    top3 = probs[:3]
    if top3:
        print("\nTop 3 likely draw cards:")
        for card, count, total, pct in top3:
            result = best_discard_after_pick(hand, card, start_state=start_state)
            a = result["analysis"]
            print(
                f"  {card_label(card)}: {pct:.1f}% ({count}/{total}) "
                f"-> best discard {card_label(result['discard'])}, routes from start: {a['forced_routes']}"
            )


def render_hand_cursor(hand: list[dict], cursor: int) -> str:
    out = []
    for i, card in enumerate(hand):
        marker = ">" if i == cursor else " "
        out.append(f"{marker}{i}:{card_label(card)}")
    return ", ".join(out)


def clamp_cursor(cursor: int, hand_len: int) -> int:
    return max(0, min(hand_len - 1, cursor))


def plain_card_label(card: dict) -> str:
    return card_text(card)


def try_edit_hand_cursor_mode_curses(hand: list[dict], settings: GameSettings) -> tuple[list[dict], bool]:
    try:
        import curses
    except Exception:
        return hand, False

    def _run(stdscr) -> list[dict]:
        color_pair_for = {
            "red": 1,
            "green": 2,
            "yellow": 3,
            "light_blue": 4,
            "dark_blue": 5,
            "white": 6,
        }
        try:
            curses.start_color()
            curses.use_default_colors()
            curses.init_pair(1, curses.COLOR_RED, -1)
            curses.init_pair(2, curses.COLOR_GREEN, -1)
            curses.init_pair(3, curses.COLOR_YELLOW, -1)
            curses.init_pair(4, curses.COLOR_CYAN, -1)
            curses.init_pair(5, curses.COLOR_BLUE, -1)
            curses.init_pair(6, curses.COLOR_WHITE, -1)
        except Exception:
            color_pair_for = {}

        undo_stack: list[list[dict]] = []
        curses.curs_set(0)
        stdscr.keypad(True)
        cursor = 0
        jump_buffer = ""
        swap_mode = False
        swap_buffer = ""

        while True:
            stdscr.erase()
            row_offset = 0
            if settings.show_map:
                row_offset = draw_map_curses(stdscr, row_offset, color_pair_for)
                row_offset += 1

            stdscr.addstr(row_offset, 0, "Arrow edit mode (q=done, u=undo, t=tx-log)")
            stdscr.addstr(row_offset + 1, 0, "Left/Right: move  Up/Down: shift card")
            stdscr.addstr(row_offset + 2, 0, "Digits+Enter: jump index  Enter: swap with index")
            if swap_mode:
                stdscr.addstr(row_offset + 3, 0, f"Swap target index: {swap_buffer}")
            else:
                stdscr.addstr(row_offset + 3, 0, f"Jump index buffer: {jump_buffer}")

            row = row_offset + 5
            col = 0
            for i, c in enumerate(hand):
                left = f"[{i}:"
                label = plain_card_label(c)
                right = "] "
                color = card_color(c)
                color_attr = curses.color_pair(color_pair_for.get(color, 0)) if color else curses.A_NORMAL
                base_attr = curses.A_REVERSE if i == cursor else curses.A_NORMAL
                max_x = max(20, curses.COLS - 1)
                if col + len(left + label + right) >= max_x:
                    row += 1
                    col = 0
                if row < curses.LINES - 1:
                    remain = max_x - col - 1
                    if remain > 0:
                        part = left[:remain]
                        stdscr.addstr(row, col, part, base_attr)
                        col += len(part)
                    remain = max_x - col - 1
                    if remain > 0:
                        part = label[:remain]
                        stdscr.addstr(row, col, part, base_attr | color_attr | curses.A_BOLD)
                        col += len(part)
                    remain = max_x - col - 1
                    if remain > 0:
                        part = right[:remain]
                        stdscr.addstr(row, col, part, base_attr)
                        col += len(part)
                else:
                    col += len(left + label + right)

            stdscr.refresh()
            ch = stdscr.getch()

            if ch in (ord("q"), ord("Q")):
                break
            if ch in (ord("u"), ord("U")):
                if undo_stack:
                    hand[:] = undo_stack.pop()
                continue
            if ch in (ord("t"), ord("T")):
                stdscr.erase()
                stdscr.addstr(0, 0, "Recent transactions (press any key)")
                tail = settings.transaction_log[-10:]
                for i, line in enumerate(tail, start=1):
                    if i >= curses.LINES - 1:
                        break
                    stdscr.addstr(i, 0, line[: max(0, curses.COLS - 1)])
                stdscr.refresh()
                stdscr.getch()
                continue

            if ch in (curses.KEY_LEFT,):
                cursor = clamp_cursor(cursor - 1, len(hand))
                continue
            if ch in (curses.KEY_RIGHT,):
                cursor = clamp_cursor(cursor + 1, len(hand))
                continue
            if ch in (curses.KEY_UP,) and cursor > 0:
                before = clone_hand(hand)
                undo_stack.append(before)
                hand[cursor - 1], hand[cursor] = hand[cursor], hand[cursor - 1]
                log_transaction(settings, action=f"move {cursor}->{cursor-1}", before=before, after=hand)
                cursor -= 1
                continue
            if ch in (curses.KEY_DOWN,) and cursor < len(hand) - 1:
                before = clone_hand(hand)
                undo_stack.append(before)
                hand[cursor + 1], hand[cursor] = hand[cursor], hand[cursor + 1]
                log_transaction(settings, action=f"move {cursor}->{cursor+1}", before=before, after=hand)
                cursor += 1
                continue

            if ch in (10, 13):
                if swap_mode:
                    if swap_buffer.isdigit():
                        target = int(swap_buffer)
                        if 0 <= target < len(hand):
                            before = clone_hand(hand)
                            undo_stack.append(before)
                            hand[cursor], hand[target] = hand[target], hand[cursor]
                            log_transaction(
                                settings,
                                action=f"swap {cursor}<->{target}",
                                before=before,
                                after=hand,
                            )
                            cursor = target
                    swap_mode = False
                    swap_buffer = ""
                    continue

                if jump_buffer.isdigit():
                    target = int(jump_buffer)
                    cursor = clamp_cursor(target, len(hand))
                    jump_buffer = ""
                else:
                    swap_mode = True
                    swap_buffer = ""
                continue

            if ch in (27,):
                # Escape cancels jump/swap input mode.
                swap_mode = False
                swap_buffer = ""
                jump_buffer = ""
                continue

            if ch in (curses.KEY_BACKSPACE, 127, 8):
                if swap_mode:
                    swap_buffer = swap_buffer[:-1]
                else:
                    jump_buffer = jump_buffer[:-1]
                continue

            if 48 <= ch <= 57:
                if swap_mode:
                    swap_buffer += chr(ch)
                else:
                    jump_buffer += chr(ch)
                continue

        return hand

    try:
        return curses.wrapper(_run), True
    except Exception:
        return hand, False


def edit_hand_cursor_mode(hand: list[dict], settings: GameSettings) -> list[dict]:
    hand, used_curses = try_edit_hand_cursor_mode_curses(hand, settings)
    if used_curses:
        return hand

    cursor = 0
    undo_stack: list[list[dict]] = []
    print("Cursor edit mode: left/right (l/r), up/down (u/d), number jump, Enter=swap, u=undo, t=tx-log, done")
    print("Tip: curses/arrow mode unavailable, using typed fallback.")
    while True:
        print(render_hand_cursor(hand, cursor))
        cmd = input("edit> ").strip().lower()
        if cmd in {"done", "q", "quit"}:
            return hand
        if cmd in {"u", "undo"}:
            if undo_stack:
                hand[:] = undo_stack.pop()
            continue
        if cmd in {"t", "tx", "transactions"}:
            print_transaction_tail(settings)
            continue
        if cmd in {"left", "l"}:
            cursor = clamp_cursor(cursor - 1, len(hand))
            continue
        if cmd in {"right", "r"}:
            cursor = clamp_cursor(cursor + 1, len(hand))
            continue
        if cmd in {"up"} and cursor > 0:
            before = clone_hand(hand)
            undo_stack.append(before)
            hand[cursor - 1], hand[cursor] = hand[cursor], hand[cursor - 1]
            log_transaction(settings, action=f"move {cursor}->{cursor-1}", before=before, after=hand)
            cursor -= 1
            continue
        if cmd in {"down", "d"} and cursor < len(hand) - 1:
            before = clone_hand(hand)
            undo_stack.append(before)
            hand[cursor + 1], hand[cursor] = hand[cursor], hand[cursor + 1]
            log_transaction(settings, action=f"move {cursor}->{cursor+1}", before=before, after=hand)
            cursor += 1
            continue
        if cmd == "":
            try:
                j = int(input(f"Swap card {cursor} with index: ").strip())
                if 0 <= j < len(hand):
                    before = clone_hand(hand)
                    undo_stack.append(before)
                    hand[cursor], hand[j] = hand[j], hand[cursor]
                    log_transaction(settings, action=f"swap {cursor}<->{j}", before=before, after=hand)
                    cursor = j
            except Exception:
                pass
            continue
        if cmd.isdigit():
            cursor = clamp_cursor(int(cmd), len(hand))
            continue
        print("Unknown command.")


def edit_hand_swap_mode(hand: list[dict], settings: GameSettings) -> list[dict]:
    undo_stack: list[list[dict]] = []
    print("Swap mode: enter two indexes, e.g. '2 7'. Type done to exit. Use u=undo, t=tx-log.")
    while True:
        print(describe_hand(hand))
        cmd = input("swap> ").strip().lower()
        if cmd in {"done", "q", "quit"}:
            return hand
        if cmd in {"u", "undo"}:
            if undo_stack:
                hand[:] = undo_stack.pop()
            continue
        if cmd in {"t", "tx", "transactions"}:
            print_transaction_tail(settings)
            continue
        parts = cmd.split()
        if len(parts) != 2 or not all(p.isdigit() for p in parts):
            print("Use: i j")
            continue
        i, j = int(parts[0]), int(parts[1])
        if 0 <= i < len(hand) and 0 <= j < len(hand):
            before = clone_hand(hand)
            undo_stack.append(before)
            hand[i], hand[j] = hand[j], hand[i]
            log_transaction(settings, action=f"swap {i}<->{j}", before=before, after=hand)


def edit_hand_order_mode(hand: list[dict], settings: GameSettings) -> list[dict]:
    print("Order mode: type indices in desired order, e.g. '3 0 1 2 ...'.")
    print(describe_hand(hand))
    cmd = input("order> ").strip()
    parts = cmd.split()
    if len(parts) != len(hand) or not all(p.isdigit() for p in parts):
        print("Invalid order input.")
        return hand
    order = [int(p) for p in parts]
    if sorted(order) != list(range(len(hand))):
        print("Order must include each index exactly once.")
        return hand
    before = clone_hand(hand)
    after = [hand[i] for i in order]
    log_transaction(settings, action="reorder full-hand", before=before, after=after)
    return after


def apply_edit_method(hand: list[dict], method: str, settings: GameSettings) -> list[dict]:
    m = method.lower()
    if m in {"1", "cursor", "arrows"}:
        return edit_hand_cursor_mode(hand, settings)
    if m in {"2", "swap"}:
        return edit_hand_swap_mode(hand, settings)
    if m in {"3", "order", "full-order"}:
        return edit_hand_order_mode(hand, settings)
    return hand


def choose_default_edit_method(settings: GameSettings) -> None:
    print(f"Current default edit method: {settings.default_edit_method}")
    print("Choose default: 1) cursor (c) 2) swap (s) 3) full-order (o)")
    cmd = input("method> ").strip().lower()
    if cmd in {"1", "cursor", "arrows", "c"}:
        settings.default_edit_method = "cursor"
    elif cmd in {"2", "swap", "s"}:
        settings.default_edit_method = "swap"
    elif cmd in {"3", "order", "full-order", "o"}:
        settings.default_edit_method = "order"
    else:
        print("Unknown method. Keeping current default.")


def edit_hand_menu(hand: list[dict], settings: GameSettings) -> list[dict]:
    while True:
        print("Edit options: 1) cursor(c) 2) swap(s) 3) full-order(o) 4) set-default(d) 5) exit(x)")
        cmd = input("choose> ").strip().lower()
        if cmd in {"5", "exit", "x", "q"}:
            return hand
        if cmd in {"1", "c"}:
            hand = edit_hand_cursor_mode(hand, settings)
            continue
        if cmd in {"2", "s"}:
            hand = edit_hand_swap_mode(hand, settings)
            continue
        if cmd in {"3", "o"}:
            hand = edit_hand_order_mode(hand, settings)
            continue
        if cmd in {"4", "default", "d"}:
            choose_default_edit_method(settings)
            continue
        print("Unknown edit choice.")


def discard_move_diagnostics(hand_11: list[dict], chosen_discard_idx: int) -> dict:
    options = []
    for i in range(len(hand_11)):
        new_hand = hand_11[:]
        discard = new_hand.pop(i)
        analysis = game.analyze_hand(new_hand, drive_include_adjacent=False, max_routes=1)
        options.append(
            {
                "idx": i,
                "discard": discard,
                "analysis": analysis,
                "utility": utility_score(analysis),
            }
        )
    options.sort(key=lambda x: x["utility"], reverse=True)
    chosen = next(x for x in options if x["idx"] == chosen_discard_idx)
    better = sum(1 for x in options if x["utility"] > chosen["utility"])
    at_or_below = sum(1 for x in options if x["utility"] <= chosen["utility"])
    est_win_pct = round(100.0 * at_or_below / len(options), 1)
    return {
        "chosen": chosen,
        "better_moves": better,
        "estimated_win_pct": est_win_pct,
        "top_option": options[0],
    }


def ai_turn(player: Player, deck: list[dict], discard_row: list[dict]) -> dict:
    current = game.analyze_hand(player.hand, drive_include_adjacent=False, max_routes=0)
    best_choice = None

    for i, card in enumerate(discard_row):
        result = best_discard_after_pick(player.hand, card)
        analysis = game.analyze_hand(result["hand"], drive_include_adjacent=False, max_routes=0)
        score = score_hand(analysis)
        choice = ("discard", i, card, result["discard"], result["hand"], score)
        if best_choice is None or score > best_choice[-1]:
            best_choice = choice

    # Average AI: if discard doesn't improve, 40% draw from deck
    current_score = score_hand(current)
    if best_choice and best_choice[-1] <= current_score and random.random() < 0.4:
        drawn = draw(deck)
        result = best_discard_after_pick(player.hand, drawn)
        player.hand = result["hand"]
        discard_row.append(result["discard"])
        print(f"{player.name} draws from deck and discards {card_label(result['discard'])}.")
        return {"win": game.solve_routes(player.hand, max_routes=0)["count"] > 0}

    # Take best discard
    if best_choice:
        _, idx, card, discard, new_hand, _ = best_choice
        player.hand = new_hand
        discard_row.pop(idx)
        discard_row.append(discard)
        print(f"{player.name} takes {card_label(card)} and discards {card_label(discard)}.")
        return {"win": game.solve_routes(player.hand, max_routes=0)["count"] > 0}

    # Fallback to deck
    drawn = draw(deck)
    result = best_discard_after_pick(player.hand, drawn)
    player.hand = result["hand"]
    discard_row.append(result["discard"])
    print(f"{player.name} draws from deck and discards {card_label(result['discard'])}.")
    return {"win": game.solve_routes(player.hand, max_routes=0)["count"] > 0}


def human_turn(
    player: Player, deck: list[dict], discard_row: list[dict], settings: GameSettings
) -> bool:
    while True:
        render_turn_ui(player.hand, discard_row, settings)
        show_analysis(player.hand)
        show_pick_suggestions(player.hand, discard_row)
        action = input(
            f"Action: 1)edit(e)[{settings.default_edit_method}] 2)pickup(p) 3)toggle-map(t) "
            f"4)set-edit-default(s) 5)edit-options(o) 6)auto-plan(a) 7)history-log(h) : "
        ).strip().lower()
        if action in {"1", "edit", "e"}:
            player.hand = apply_edit_method(player.hand, settings.default_edit_method, settings)
            continue
        if action in {"3", "toggle", "map", "m"}:
            settings.show_map = not settings.show_map
            print(f"Map view is now {'ON' if settings.show_map else 'OFF'}.")
            continue
        if action in {"4", "method", "set", "s"}:
            choose_default_edit_method(settings)
            continue
        if action in {"5", "menu", "options", "o"}:
            player.hand = edit_hand_menu(player.hand, settings)
            continue
        if action in {"6", "plan", "auto", "a"}:
            autocomplete_planner(player.hand, discard_row, settings)
            continue
        if action in {"7", "tx", "transactions", "history", "h"}:
            print_transaction_tail(settings)
            continue
        if action in {"2", "pickup", "p"}:
            break

    while True:
        choice = input("Pick (d0/d1/d2/deck): ").strip().lower()
        if choice.startswith("d") and len(choice) >= 2 and choice[1].isdigit():
            idx = int(choice[1])
            if 0 <= idx < len(discard_row):
                pick = discard_row.pop(idx)
                break
            print("Invalid discard choice.")
            continue
        if choice in {"deck", "draw"}:
            pick = draw(deck)
            print("You drew:", card_label(pick))
            break
        print("Choose d0, d1, d2, or deck.")

    hand_11 = player.hand + [pick]
    while True:
        render_turn_ui(hand_11, discard_row, settings)
        print("\nPost-pick mode (11 cards).")
        action = input(
            f"Action: 1)edit(e)[{settings.default_edit_method}] 2)discard(d) 3)toggle-map(t) "
            f"4)set-edit-default(s) 5)edit-options(o) 6)auto-plan(a) 7)history-log(h) : "
        ).strip().lower()
        if action in {"1", "edit", "e"}:
            hand_11 = apply_edit_method(hand_11, settings.default_edit_method, settings)
            continue
        if action in {"3", "toggle", "map", "m"}:
            settings.show_map = not settings.show_map
            print(f"Map view is now {'ON' if settings.show_map else 'OFF'}.")
            continue
        if action in {"4", "method", "set", "s"}:
            choose_default_edit_method(settings)
            continue
        if action in {"5", "menu", "options", "o"}:
            hand_11 = edit_hand_menu(hand_11, settings)
            continue
        if action in {"6", "plan", "auto", "a"}:
            autocomplete_planner(hand_11, discard_row, settings)
            continue
        if action in {"7", "tx", "transactions", "history", "h"}:
            print_transaction_tail(settings)
            continue
        if action in {"2", "discard", "d"}:
            try:
                discard_idx = int(input("Discard index: ").strip())
            except Exception:
                print("Invalid index.")
                continue
            if not (0 <= discard_idx < len(hand_11)):
                print("Invalid index.")
                continue
            diag = discard_move_diagnostics(hand_11, discard_idx)
            if diag["better_moves"] > 0:
                print(
                    f"Warning: this is not ideal. Estimated win chance: {diag['estimated_win_pct']}%. "
                    f"Better moves available: {diag['better_moves']}."
                )
                confirm = input("Keep this discard? (y/n): ").strip().lower()
                if confirm not in {"y", "yes"}:
                    continue
            discard = hand_11.pop(discard_idx)
            discard_row.append(discard)
            player.hand = hand_11
            print(f"You discarded {card_label(discard)}.")
            show_analysis(player.hand)
            return game.solve_routes(player.hand, max_routes=0)["count"] > 0


def play_game(
    ai_players: int = 3,
    *,
    seed: int | None = None,
    plane_per_color: int = 2,
    drive_cards: int = 5,
    default_edit_method: str = "cursor",
) -> None:
    validate_state_formatters()
    if seed is not None:
        random.seed(seed)
    deck = build_default_deck(plane_per_color=plane_per_color, drive_cards=drive_cards)
    random.shuffle(deck)

    players = [Player("You", True, [])]
    settings = GameSettings(
        show_map=True,
        default_edit_method=default_edit_method,
        plane_per_color=plane_per_color,
        drive_cards=drive_cards,
    )
    for i in range(ai_players):
        players.append(Player(f"CPU-{i+1}", False, []))

    for _ in range(10):
        for p in players:
            p.hand.append(draw(deck))

    discard_row: list[dict] = [draw(deck) for _ in range(3)]
    show_color_legend()

    turn = 0
    while True:
        player = players[turn]
        refill_discard_row(deck, discard_row)
        if player.is_human:
            won = human_turn(player, deck, discard_row, settings)
        else:
            won = ai_turn(player, deck, discard_row)["win"]

        if won:
            print(f"\n{player.name} wins!")
            if player.is_human:
                routes = game.solve_routes(player.hand, max_routes=1)["routes"]
                if routes:
                    print("Winning route:", format_route(routes[0]))
            break

        turn = (turn + 1) % len(players)


if __name__ == "__main__":
    ai_raw = input("Number of AI players (1-3) [3]: ").strip()
    try:
        ai_count = int(ai_raw) if ai_raw else 3
    except Exception:
        ai_count = 3
    ai_count = max(1, min(3, ai_count))
    planes_raw = input("Planes per color [2]: ").strip()
    try:
        plane_per_color = int(planes_raw) if planes_raw else 2
    except Exception:
        plane_per_color = 2
    drives_raw = input("Drive cards [5]: ").strip()
    try:
        drive_cards = int(drives_raw) if drives_raw else 5
    except Exception:
        drive_cards = 5
    default_method = input("Default edit method (cursor/swap/order) [cursor]: ").strip().lower()
    if default_method in {"c", "cursor"}:
        default_method = "cursor"
    elif default_method in {"s", "swap"}:
        default_method = "swap"
    elif default_method in {"o", "order"}:
        default_method = "order"
    else:
        default_method = "cursor"

    play_game(
        ai_players=ai_count,
        plane_per_color=plane_per_color,
        drive_cards=drive_cards,
        default_edit_method=default_method,
    )
