"""Scoring an output against the prompt's own rubric.

The judge is a separate model call with a strict JSON contract. Keeping it
separate from generation is what lets the loop climb: the generator never
sees its own grade until it is fed back as a critique.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field

from .backends import CachedClient
from .config import PromptSpec

JUDGE_SYSTEM = """You are a strict evaluator producing a SCORECARD.

You grade one AI output against the user's stated goal and a rubric.
You are hard to impress: 60 is competent, 80 is genuinely good, 95+ is
best-in-class and rare. Generic, padded, or hedging output scores low no
matter how fluent it is.

Reply with ONLY a JSON object, no prose and no code fences:
{
  "dimensions": {"<rubric dimension>": <0-100 int>, ...},
  "score": <0-100 int, the weighted whole>,
  "weakest": "<the single weakest dimension>",
  "critique": "<2-4 sentences: the most important concrete flaw and the specific fix>",
  "why_it_wins": "<one sentence a busy reader could use to judge this output>"
}"""


@dataclass
class Verdict:
    score: float
    dimensions: dict[str, float] = field(default_factory=dict)
    weakest: str = ""
    critique: str = ""
    why_it_wins: str = ""
    error: str | None = None


def _extract_json(text: str) -> dict | None:
    """Pull the first balanced JSON object out of a model reply."""
    text = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.MULTILINE).strip()
    start = text.find("{")
    if start == -1:
        return None
    depth, in_string, escaped = 0, False, False
    for i, ch in enumerate(text[start:], start):
        if in_string:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_string = False
            continue
        if ch == '"':
            in_string = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(text[start : i + 1])
                except json.JSONDecodeError:
                    return None
    return None


def judge(client: CachedClient, spec: PromptSpec, prompt: str, output: str) -> Verdict:
    rubric = "\n".join(f"- {dim}" for dim in spec.rubric)
    request = f"""GOAL THE USER WANTS SERVED:
{spec.goal or spec.title}

RUBRIC DIMENSIONS:
{rubric}

PROMPT THAT WAS SENT:
<prompt>
{prompt}
</prompt>

OUTPUT TO GRADE:
<output>
{output}
</output>

Grade the OUTPUT (not the prompt). Return the SCORECARD JSON only."""

    result = client.complete(JUDGE_SYSTEM, request, tag=f"judge-{spec.slug}")
    if not result.ok:
        return Verdict(score=0.0, error=result.error or "empty judge reply")

    data = _extract_json(result.text)
    if not data or "score" not in data:
        return Verdict(score=0.0, error="judge did not return parseable JSON")

    dims = {
        str(k): _clamp(v)
        for k, v in (data.get("dimensions") or {}).items()
        if isinstance(v, (int, float))
    }
    return Verdict(
        score=_clamp(data.get("score")),
        dimensions=dims,
        weakest=str(data.get("weakest") or (min(dims, key=dims.get) if dims else "")),
        critique=str(data.get("critique") or "").strip(),
        why_it_wins=str(data.get("why_it_wins") or "").strip(),
    )


def _clamp(value) -> float:
    try:
        return max(0.0, min(100.0, float(value)))
    except (TypeError, ValueError):
        return 0.0
