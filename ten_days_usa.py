from __future__ import annotations

from functools import lru_cache
from typing import Iterable, Optional

# Standard U.S. state adjacency (land borders only). Alaska/Hawaii have none.
STATE_ADJACENCY = {
    "Alabama": ["Florida", "Georgia", "Mississippi", "Tennessee"],
    "Alaska": [],
    "Arizona": ["California", "Colorado", "New Mexico", "Nevada", "Utah"],
    "Arkansas": ["Louisiana", "Mississippi", "Missouri", "Oklahoma", "Tennessee", "Texas"],
    "California": ["Arizona", "Nevada", "Oregon"],
    "Colorado": ["Arizona", "Kansas", "Nebraska", "New Mexico", "Oklahoma", "Utah", "Wyoming"],
    "Connecticut": ["Massachusetts", "New York", "Rhode Island"],
    "Delaware": ["Maryland", "New Jersey", "Pennsylvania"],
    "Florida": ["Alabama", "Georgia"],
    "Georgia": ["Alabama", "Florida", "North Carolina", "South Carolina", "Tennessee"],
    "Hawaii": [],
    "Idaho": ["Montana", "Nevada", "Oregon", "Utah", "Washington", "Wyoming"],
    "Illinois": ["Indiana", "Iowa", "Kentucky", "Michigan", "Missouri", "Wisconsin"],
    "Indiana": ["Illinois", "Kentucky", "Michigan", "Ohio"],
    "Iowa": ["Illinois", "Minnesota", "Missouri", "Nebraska", "South Dakota", "Wisconsin"],
    "Kansas": ["Colorado", "Missouri", "Nebraska", "Oklahoma"],
    "Kentucky": ["Illinois", "Indiana", "Missouri", "Ohio", "Tennessee", "Virginia", "West Virginia"],
    "Louisiana": ["Arkansas", "Mississippi", "Texas"],
    "Maine": ["New Hampshire"],
    "Maryland": ["Delaware", "Pennsylvania", "Virginia", "West Virginia"],
    "Massachusetts": ["Connecticut", "New Hampshire", "New York", "Rhode Island", "Vermont"],
    "Michigan": ["Indiana", "Ohio", "Wisconsin"],
    "Minnesota": ["Iowa", "North Dakota", "South Dakota", "Wisconsin"],
    "Mississippi": ["Alabama", "Arkansas", "Louisiana", "Tennessee"],
    "Missouri": ["Arkansas", "Iowa", "Illinois", "Kansas", "Kentucky", "Nebraska", "Oklahoma", "Tennessee"],
    "Montana": ["Idaho", "North Dakota", "South Dakota", "Wyoming"],
    "Nebraska": ["Colorado", "Iowa", "Kansas", "Missouri", "South Dakota", "Wyoming"],
    "Nevada": ["Arizona", "California", "Idaho", "Oregon", "Utah"],
    "New Hampshire": ["Maine", "Massachusetts", "Vermont"],
    "New Jersey": ["Delaware", "New York", "Pennsylvania"],
    "New Mexico": ["Arizona", "Colorado", "Oklahoma", "Texas", "Utah"],
    "New York": ["Connecticut", "Massachusetts", "New Jersey", "Pennsylvania", "Vermont"],
    "North Carolina": ["Georgia", "South Carolina", "Tennessee", "Virginia"],
    "North Dakota": ["Minnesota", "Montana", "South Dakota"],
    "Ohio": ["Indiana", "Kentucky", "Michigan", "Pennsylvania", "West Virginia"],
    "Oklahoma": ["Arkansas", "Colorado", "Kansas", "Missouri", "New Mexico", "Texas"],
    "Oregon": ["California", "Idaho", "Nevada", "Washington"],
    "Pennsylvania": ["Delaware", "Maryland", "New Jersey", "New York", "Ohio", "West Virginia"],
    "Rhode Island": ["Connecticut", "Massachusetts"],
    "South Carolina": ["Georgia", "North Carolina"],
    "South Dakota": ["Iowa", "Minnesota", "Montana", "North Dakota", "Nebraska", "Wyoming"],
    "Tennessee": ["Alabama", "Arkansas", "Georgia", "Kentucky", "Mississippi", "Missouri", "North Carolina", "Virginia"],
    "Texas": ["Arkansas", "Louisiana", "New Mexico", "Oklahoma"],
    "Utah": ["Arizona", "Colorado", "Idaho", "Nevada", "New Mexico", "Wyoming"],
    "Vermont": ["Massachusetts", "New Hampshire", "New York"],
    "Virginia": ["Kentucky", "Maryland", "North Carolina", "Tennessee", "West Virginia"],
    "Washington": ["Idaho", "Oregon"],
    "West Virginia": ["Kentucky", "Maryland", "Ohio", "Pennsylvania", "Virginia"],
    "Wisconsin": ["Iowa", "Illinois", "Michigan", "Minnesota"],
    "Wyoming": ["Colorado", "Idaho", "Montana", "Nebraska", "South Dakota", "Utah"],
}

# Color assignments (5-color palette).
# Color labels: red, light_blue, dark_blue, green, yellow (light brown on board).
STATE_COLORS = {
    "Alabama": "dark_blue",
    "Alaska": "white",
    "Arizona": "yellow",
    "Arkansas": "yellow",
    "California": "green",
    "Colorado": "red",
    "Connecticut": "green",
    "Delaware": "yellow",
    "Florida": "green",
    "Georgia": "light_blue",
    "Hawaii": "white",
    "Idaho": "red",
    "Illinois": "dark_blue",
    "Indiana": "green",
    "Iowa": "light_blue",
    "Kansas": "yellow",
    "Kentucky": "light_blue",
    "Louisiana": "light_blue",
    "Maine": "dark_blue",
    "Maryland": "green",
    "Massachusetts": "light_blue",
    "Michigan": "red",
    "Minnesota": "green",
    "Mississippi": "red",
    "Missouri": "red",
    "Montana": "green",
    "Nebraska": "green",
    "Nevada": "light_blue",
    "New Hampshire": "green",
    "New Jersey": "red",
    "New Mexico": "light_blue",
    "New York": "dark_blue",
    "North Carolina": "dark_blue",
    "North Dakota": "red",
    "Ohio": "yellow",
    "Oklahoma": "dark_blue",
    "Oregon": "dark_blue",
    "Pennsylvania": "light_blue",
    "Rhode Island": "yellow",
    "South Carolina": "yellow",
    "South Dakota": "dark_blue",
    "Tennessee": "green",
    "Texas": "red",
    "Utah": "dark_blue",
    "Vermont": "red",
    "Virginia": "red",
    "Washington": "yellow",
    "West Virginia": "dark_blue",
    "Wisconsin": "yellow",
    "Wyoming": "light_blue",
}

# Special rule: Alaska and Hawaii can be reached by any plane color,
# as long as the plane matches the other endpoint's color.
PLANE_WILDCARD_STATES = {"Alaska", "Hawaii"}


def normalize_state(name: str) -> str:
    name = name.strip()
    if name not in STATE_ADJACENCY:
        raise ValueError(f"Unknown state: {name}")
    return name


def build_drive_reachability(*, include_adjacent: bool) -> dict[str, set[str]]:
    reach = {}
    for state, neighbors in STATE_ADJACENCY.items():
        reachable = set()
        for mid in neighbors:
            for dest in STATE_ADJACENCY[mid]:
                if dest != state:
                    reachable.add(dest)
        if include_adjacent:
            reachable.update(neighbors)
        reach[state] = reachable
    return reach


def normalize_plane_color(color: str) -> str:
    c = color.strip().lower().replace("-", " ")
    if c in {"brown", "light brown", "tan"}:
        return "yellow"
    if c in {"light blue", "light_blue"}:
        return "light_blue"
    if c in {"dark blue", "dark_blue", "navy"}:
        return "dark_blue"
    if c in {"blue"}:
        # Ambiguous; default to light_blue unless specified
        return "light_blue"
    return c


def card_from_string(value: str) -> dict:
    """
    Parse simple card strings.
    - State card: "Texas"
    - Drive card: "Drive"
    - Plane card: "Plane:red" or "Plane red"
    """
    value = value.strip()
    lower = value.lower()
    if lower in {"drive", "car"}:
        return {"type": "drive"}
    if "plane" in lower:
        parts = value.replace(":", " ").replace("-", " ").split()
        parts = [p.strip() for p in parts if p.strip()]
        if "plane" not in [p.lower() for p in parts]:
            raise ValueError(f"Plane card must include 'plane': {value}")
        # color is any non-plane word(s)
        words = [p for p in parts if p.lower() != "plane"]
        if not words:
            raise ValueError(f"Plane card must include a color: {value}")
        color = normalize_plane_color(" ".join(words))
        return {"type": "plane", "color": color}
    # Otherwise treat as state card
    return {"type": "state", "state": normalize_state(value)}


def card_to_string(card: dict) -> str:
    if card["type"] == "state":
        return card["state"]
    if card["type"] == "drive":
        return "Drive"
    if card["type"] == "plane":
        return f"Plane({card['color']})"
    return "Unknown"


def can_walk(from_state: str, to_state: str) -> bool:
    return to_state in STATE_ADJACENCY[from_state]


def can_drive(
    from_state: str,
    to_state: str,
    drive_reach: dict[str, set[str]],
) -> bool:
    return to_state in drive_reach[from_state]


def can_fly(from_state: str, to_state: str, plane_color: str) -> bool:
    if from_state in PLANE_WILDCARD_STATES and to_state in PLANE_WILDCARD_STATES:
        return True
    if from_state in PLANE_WILDCARD_STATES:
        return STATE_COLORS[to_state] == plane_color
    if to_state in PLANE_WILDCARD_STATES:
        return STATE_COLORS[from_state] == plane_color
    return STATE_COLORS[from_state] == plane_color and STATE_COLORS[to_state] == plane_color


def solve_routes(
    cards: list[dict],
    *,
    drive_include_adjacent: bool = False,
    max_routes: Optional[int] = 1,
    forced_start_state: Optional[str] = None,
) -> dict:
    """
    Find valid itineraries using all cards in an order that respects travel rules.
    - Walking: adjacent states with no transport card between them
    - Drive: state -> drive -> state, where destination is distance-2 away
      (set drive_include_adjacent=True to allow distance-1 as well)
    - Plane: state -> plane(color) -> state, both states share that color

    Returns: dict with count and sample routes (if requested).
    """
    if not cards:
        return {"count": 0, "routes": []}

    drive_reach = build_drive_reachability(include_adjacent=drive_include_adjacent)

    # Preprocess cards
    n = len(cards)
    card_types = [c["type"] for c in cards]
    card_states = [c.get("state") for c in cards]
    card_plane_colors = [c.get("color") for c in cards]

    state_indices = [i for i, t in enumerate(card_types) if t == "state"]
    if not state_indices:
        return {"count": 0, "routes": []}

    @lru_cache(maxsize=None)
    def dfs(used_mask: int, last_state: str, pending_transport_idx: int) -> int:
        # pending_transport_idx == -1 means no pending transport
        if used_mask == (1 << n) - 1:
            return 1 if pending_transport_idx == -1 else 0

        total = 0
        if pending_transport_idx == -1:
            # Last card was a state. We may place a state (walk) or a transport.
            for i in range(n):
                if used_mask & (1 << i):
                    continue
                if card_types[i] == "state":
                    next_state = card_states[i]
                    if can_walk(last_state, next_state):
                        total += dfs(used_mask | (1 << i), next_state, -1)
                else:
                    total += dfs(used_mask | (1 << i), last_state, i)
        else:
            # We just placed a transport; next must be a state compatible with it.
            transport_type = card_types[pending_transport_idx]
            transport_color = card_plane_colors[pending_transport_idx]
            for i in range(n):
                if used_mask & (1 << i):
                    continue
                if card_types[i] != "state":
                    continue
                next_state = card_states[i]
                if transport_type == "drive":
                    if can_drive(last_state, next_state, drive_reach):
                        total += dfs(used_mask | (1 << i), next_state, -1)
                elif transport_type == "plane":
                    if can_fly(last_state, next_state, transport_color):
                        total += dfs(used_mask | (1 << i), next_state, -1)
        return total

    start_candidates = state_indices
    if forced_start_state is not None:
        forced_start_state = normalize_state(forced_start_state)
        start_candidates = [i for i in state_indices if card_states[i] == forced_start_state]

    total_routes = 0
    for start_idx in start_candidates:
        total_routes += dfs(1 << start_idx, card_states[start_idx], -1)

    routes = []
    if max_routes and total_routes > 0:
        def build_routes(limit: int) -> list[list[int]]:
            collected: list[list[int]] = []

            def helper(used_mask: int, last_state: str, pending_transport_idx: int, path: list[int]) -> None:
                if len(collected) >= limit:
                    return
                if used_mask == (1 << n) - 1:
                    if pending_transport_idx == -1:
                        collected.append(path[:])
                    return

                if pending_transport_idx == -1:
                    for i in range(n):
                        if used_mask & (1 << i):
                            continue
                        if card_types[i] == "state":
                            next_state = card_states[i]
                            if can_walk(last_state, next_state):
                                if dfs(used_mask | (1 << i), next_state, -1) > 0:
                                    helper(used_mask | (1 << i), next_state, -1, path + [i])
                        else:
                            if dfs(used_mask | (1 << i), last_state, i) > 0:
                                helper(used_mask | (1 << i), last_state, i, path + [i])
                    return

                transport_type = card_types[pending_transport_idx]
                transport_color = card_plane_colors[pending_transport_idx]
                for i in range(n):
                    if used_mask & (1 << i):
                        continue
                    if card_types[i] != "state":
                        continue
                    next_state = card_states[i]
                    if transport_type == "drive":
                        ok = can_drive(last_state, next_state, drive_reach)
                    else:
                        ok = can_fly(last_state, next_state, transport_color)
                    if ok and dfs(used_mask | (1 << i), next_state, -1) > 0:
                        helper(used_mask | (1 << i), next_state, -1, path + [i])

            for start_idx in start_candidates:
                if len(collected) >= limit:
                    break
                if dfs(1 << start_idx, card_states[start_idx], -1) > 0:
                    helper(1 << start_idx, card_states[start_idx], -1, [start_idx])

            return collected

        routes_idx = build_routes(limit=max_routes)
        routes = [[cards[i] for i in route] for route in routes_idx]

    return {"count": total_routes, "routes": routes}


def max_route_length(cards: list[dict], *, drive_include_adjacent: bool = False) -> dict:
    if not cards:
        return {"length": 0, "route": []}

    drive_reach = build_drive_reachability(include_adjacent=drive_include_adjacent)
    n = len(cards)
    card_types = [c["type"] for c in cards]
    card_states = [c.get("state") for c in cards]
    card_plane_colors = [c.get("color") for c in cards]
    state_indices = [i for i, t in enumerate(card_types) if t == "state"]
    if not state_indices:
        return {"length": 0, "route": []}

    @lru_cache(maxsize=None)
    def best_len(used_mask: int, last_state: str, pending_transport_idx: int) -> int:
        current = bin(used_mask).count("1")
        best = current
        if pending_transport_idx == -1:
            for i in range(n):
                if used_mask & (1 << i):
                    continue
                if card_types[i] == "state":
                    next_state = card_states[i]
                    if can_walk(last_state, next_state):
                        best = max(best, best_len(used_mask | (1 << i), next_state, -1))
                else:
                    best = max(best, best_len(used_mask | (1 << i), last_state, i))
        else:
            transport_type = card_types[pending_transport_idx]
            transport_color = card_plane_colors[pending_transport_idx]
            for i in range(n):
                if used_mask & (1 << i):
                    continue
                if card_types[i] != "state":
                    continue
                next_state = card_states[i]
                if transport_type == "drive":
                    ok = can_drive(last_state, next_state, drive_reach)
                else:
                    ok = can_fly(last_state, next_state, transport_color)
                if ok:
                    best = max(best, best_len(used_mask | (1 << i), next_state, -1))
        return best

    overall = 0
    for start_idx in state_indices:
        overall = max(overall, best_len(1 << start_idx, card_states[start_idx], -1))

    def build_path(used_mask: int, last_state: str, pending_transport_idx: int) -> list[int]:
        current = best_len(used_mask, last_state, pending_transport_idx)
        if current == bin(used_mask).count("1"):
            return []
        if pending_transport_idx == -1:
            for i in range(n):
                if used_mask & (1 << i):
                    continue
                if card_types[i] == "state":
                    next_state = card_states[i]
                    if can_walk(last_state, next_state):
                        if best_len(used_mask | (1 << i), next_state, -1) == current:
                            return [i] + build_path(used_mask | (1 << i), next_state, -1)
                else:
                    if best_len(used_mask | (1 << i), last_state, i) == current:
                        return [i] + build_path(used_mask | (1 << i), last_state, i)
        else:
            transport_type = card_types[pending_transport_idx]
            transport_color = card_plane_colors[pending_transport_idx]
            for i in range(n):
                if used_mask & (1 << i):
                    continue
                if card_types[i] != "state":
                    continue
                next_state = card_states[i]
                if transport_type == "drive":
                    ok = can_drive(last_state, next_state, drive_reach)
                else:
                    ok = can_fly(last_state, next_state, transport_color)
                if ok and best_len(used_mask | (1 << i), next_state, -1) == current:
                    return [i] + build_path(used_mask | (1 << i), next_state, -1)
        return []

    for start_idx in state_indices:
        if best_len(1 << start_idx, card_states[start_idx], -1) == overall:
            tail = build_path(1 << start_idx, card_states[start_idx], -1)
            return {"length": overall, "route": [cards[i] for i in [start_idx] + tail]}

    return {"length": overall, "route": []}


def analyze_hand(
    cards: list[dict],
    *,
    drive_include_adjacent: bool = False,
    max_routes: int = 3,
) -> dict:
    full = solve_routes(cards, drive_include_adjacent=drive_include_adjacent, max_routes=max_routes)
    if full["count"] > 0:
        return {
            "full_routes": full["count"],
            "routes": full["routes"],
            "best_length": len(cards),
            "best_route": full["routes"][0] if full["routes"] else [],
        }
    best = max_route_length(cards, drive_include_adjacent=drive_include_adjacent)
    return {
        "full_routes": 0,
        "routes": [],
        "best_length": best["length"],
        "best_route": best["route"],
    }


def describe_route(route: Iterable[dict]) -> str:
    return " -> ".join(card_to_string(c) for c in route)


if __name__ == "__main__":
    # Example usage
    example_cards = [
        card_from_string("Georgia"),
        card_from_string("Drive"),
        card_from_string("Tennessee"),
        card_from_string("Plane red"),
        card_from_string("Virginia"),
        card_from_string("Kentucky"),
        card_from_string("Plane blue"),
        card_from_string("New Mexico"),
        card_from_string("Colorado"),
        card_from_string("Rhode Island"),
    ]
    result = solve_routes(example_cards, drive_include_adjacent=False, max_routes=1)
    print("Total routes:", result["count"])
    if result["routes"]:
        print("Example:", describe_route(result["routes"][0]))
