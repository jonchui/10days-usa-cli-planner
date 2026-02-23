# 10 Days in the USA CLI Planner

Text-based assistant and simulator for the **10 Days in the USA** style card game.

It helps you:

- play vs 1-3 computer players
- visualize state colors and adjacency
- reorder your hand quickly (arrow-key edit mode)
- evaluate pickup/discard decisions
- run an auto-planner from a forced start state
- track edit transactions and undo reordering changes

## Files

- `play_ten_days.py`: interactive CLI game
- `ten_days_usa.py`: rules engine, state graph, color map, route solver

## Requirements

- Python 3.10+
- Terminal with ANSI color support (optional but recommended)
- `curses` for arrow-key in-place edit mode (auto-falls back if unavailable)

## Run

```bash
python3 play_ten_days.py
```

Startup defaults (press Enter to accept):

- AI players: `[3]`
- Planes per color: `[2]`
- Drive cards: `[5]`
- Default edit method: `[cursor]`

## Core Rules Implemented

- You must start on a state and end on a state.
- Walking: adjacent state -> state.
- Driving: exactly 2-state distance (one state in between).
- Planes are color-specific (light blue and dark blue are different).
- Alaska/Hawaii are white island states with wildcard plane endpoint behavior.

## In-Game Controls (Human Turn)

- `1` edit using default method
- `2` pickup (discard row or deck)
- `3` toggle map
- `4` change default edit method
- `5` open full edit menu
- `6` auto-plan (forced-start route analysis)
- `7` transaction log

### Edit methods

1. `cursor/arrows`
2. `swap`
3. `full-order`

### Cursor edit mode (curses)

- Left/Right: move selection
- Up/Down: move selected card in hand
- Enter: swap with typed target index
- Digits + Enter: jump cursor
- `u`: undo last hand edit
- `t`: show recent transactions
- `q`: done

## Auto-Plan Mode

Choose a starting state card index and it will show:

- route count from that start for your current hand
- best outcomes for each discard pickup option
- top 3 likely draw cards with percentages and resulting route potential

This helps compare lines like:

- "If I take this plane from discard..."
- "If I draw from deck, what likely outcomes improve my route count?"

## Example Output (trimmed)

```text
Your hand:
 1               2               3               4               ...
[Plane]         [Alabama]       [Drive]         [Montana]       ...
(0)             (1)             (2)             (3)             ...

Discard row:
  d0: Hawaii
  d1: Plane
  d2: Plane

Action: 1)edit[cursor] 2)pickup 3)toggle-map 4)edit-method 5)edit-menu 6)auto-plan 7)tx-log :
```

## Notes

- This project is designed as a practical strategy helper and simulation tool.
- The solver uses deterministic search + memoization, not LLM guessing, for route validity.
