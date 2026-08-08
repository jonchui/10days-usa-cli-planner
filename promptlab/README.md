# PromptLab

Give it a list of prompts. It runs each one in its own side agent that keeps
rewriting **itself** until a judge model stops finding faults, then hands you a
one-page digest of the winners.

The loop, per prompt:

```
generate ──► judge (0-100 + named weakness + critique)
   ▲                        │
   └──── rewrite the prompt ◄┘   parent = best-scoring attempt so far
```

Rewriting the *prompt* rather than re-rolling the *output* is what makes it
climb: each round is a mutation of the best prompt found so far, aimed at the
specific weakness the judge named. Agents run in parallel, one thread each.

## Run it

```bash
./promptlab.sh --dry-run          # free offline smoke test, no credits
./promptlab.sh                    # the 5 prompts, on claude/opus
./promptlab.sh --only comedy --rounds 6
./promptlab.sh --backend codex --model gpt-5
./promptlab.sh promptlab/prompts/ten-days-strategy.toml
```

Needs Python 3.11+ (stdlib only) and a CLI you are already logged into —
`claude` or `codex`. No API keys, no `pip install`.

## What you get

```
runs/<timestamp>-<name>-<fingerprint>/
  BEST.md                 ← leaderboard + winning prompt + output, per agent
  run.json                ← scores, cost, call count, config fingerprint
  streaming-replacement.toml   ← snapshot of the exact prompt set used
  agents/<id>.json        ← every round: prompt, output, score, critique
  calls/*.json            ← every model call, request and response
```

`BEST.md` is the deliverable; everything else is there so any claim in it can
be traced back to the call that produced it.

## Reproducibility

- **One config file** holds the prompt set and every knob. It is snapshotted
  into the run directory and hashed into the run's `fingerprint`.
- **Seeded mutation.** Strategy selection is seeded per `(seed, prompt id)`, so
  the same config takes the same path through prompt space.
- **Content-addressed cache** in `.promptlab/cache`, keyed on
  `(backend, model, system, prompt)`. Re-running a finished config replays it
  from cache for free; `--no-cache` forces fresh calls.
- **Hermetic backend.** The `claude` backend runs with `--setting-sources ""`,
  `--strict-mcp-config`, a replaced system prompt, and tools disabled — so a
  run does not depend on the CLAUDE.md, skills, or MCP servers of the directory
  it was launched from. (It also saves ~20k tokens per call.)
- **Hard ceilings.** `--max-calls` and `--max-seconds` bound the spend; agents
  stop cleanly and still report what they found.

## Writing a prompt set

```toml
[run]
name = "my-set"
backend = "claude"
model = "opus"
rounds = 4              # max improvement rounds per agent
parallel = 5            # agents in flight at once
target_score = 93       # an agent stops early once it scores this well
max_calls = 200         # ceiling for the whole run
seed = 1337
rubric = ["usefulness", "specificity", "actionability", "honesty", "format"]

[[prompt]]
id = "series"
title = "A serialized show written for one viewer"
goal = "What good looks like — the judge grades against this, not the prompt."
prompt = """
...the actual prompt...
"""
rubric = ["hook", "prose quality", "cliffhanger"]   # optional, overrides [run]
```

`goal` matters most. The judge grades the *output against the goal*, so a vague
goal produces a lenient judge and the loop plateaus early.

## Cost

Each round costs 3 calls (generate, judge, rewrite). A 5-prompt × 4-round run is
~55 calls. On `claude/opus` that measured ~$0.04–0.25 per call depending on
output length. Start with `--rounds 2`, and use `--dry-run` to check wiring for
free.

## Mutation strategies

Each round picks one, preferring the judge's named weakness and otherwise taking
a seeded unused strategy: `specificity`, `structure`, `persona`, `constraints`,
`process`, `grounding`. Definitions are in `agent.py`.

## Tests

```bash
python3 -m unittest tests.test_promptlab -v
```

20 tests, fully offline via the `mock` backend. No credits spent.
