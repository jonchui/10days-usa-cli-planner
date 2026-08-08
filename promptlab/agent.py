"""One side agent per prompt: generate, grade, rewrite the prompt, repeat.

The crawler-like behaviour comes from mutating the *prompt*, not just
re-rolling the output. Each round keeps the best prompt found so far as the
parent, so a run is a hill climb over prompt space with the judge as the
fitness function.
"""

from __future__ import annotations

import random
import time
from dataclasses import asdict, dataclass, field

from .backends import BudgetExhausted, CachedClient
from .config import PromptSpec, RunConfig
from .judge import Verdict, judge

GEN_SYSTEM = """You are answering a user's prompt for real use, not demonstrating
that you understand it. Produce the finished artifact itself: no preamble, no
"here's what I'd do", no offers to continue. Be concrete and specific; invent
plausible detail rather than leaving placeholders. Prefer substance over length."""

ENGINEER_SYSTEM = """You are a PROMPT ENGINEER improving a prompt that will be sent
to a strong model.

You are given the current prompt, the output it produced, and an evaluator's
critique. Rewrite the PROMPT so the next output scores higher on the stated
weakness. Keep the user's original intent exactly; do not answer the prompt
yourself and do not narrate your changes.

Rules:
- Output ONLY the rewritten prompt text, ready to paste. No preamble, no fences.
- Keep it under 300 words. Longer is not better; sharper is.
- A human must still recognise it as the same request."""

# Each strategy is a nudge given to the prompt engineer. Selection is seeded,
# so a given (seed, prompt, round) always tries the same strategy.
STRATEGIES: dict[str, str] = {
    "specificity": "Add concrete constraints: quantities, named examples, ranges, edge cases.",
    "structure": "Impose an explicit output structure (sections, fields, or a schema) that fits the goal.",
    "persona": "Name the expertise the answerer should bring and the exact audience being served.",
    "constraints": "Add sharp negative constraints that rule out the generic failure modes seen here.",
    "process": "Ask for the reasoning or selection process to happen before the answer, then the answer alone.",
    "grounding": "Force the answer to commit to specifics: real names, numbers, and tradeoffs, with uncertainty stated plainly.",
}


@dataclass
class Attempt:
    round: int
    strategy: str
    prompt: str
    output: str
    score: float
    dimensions: dict[str, float] = field(default_factory=dict)
    critique: str = ""
    why_it_wins: str = ""
    error: str | None = None
    elapsed_s: float = 0.0


@dataclass
class AgentResult:
    spec: PromptSpec
    attempts: list[Attempt] = field(default_factory=list)
    stopped_because: str = "rounds exhausted"

    @property
    def best(self) -> Attempt | None:
        scored = [a for a in self.attempts if a.error is None]
        return max(scored, key=lambda a: a.score) if scored else None

    @property
    def first(self) -> Attempt | None:
        return self.attempts[0] if self.attempts else None

    @property
    def improvement(self) -> float:
        best, first = self.best, self.first
        if not best or not first or first.error:
            return 0.0
        return best.score - first.score

    def to_dict(self) -> dict:
        best = self.best
        return {
            "id": self.spec.id,
            "title": self.spec.title,
            "goal": self.spec.goal,
            "stopped_because": self.stopped_because,
            "best_score": best.score if best else 0.0,
            "best_round": best.round if best else None,
            "improvement": round(self.improvement, 1),
            "attempts": [asdict(a) for a in self.attempts],
        }


def _pick_strategy(rng: random.Random, verdict: Verdict, used: set[str]) -> str:
    """Prefer the judge's named weakness; otherwise take an unused strategy."""
    weakest = (verdict.weakest or "").lower()
    for name in STRATEGIES:
        if name in weakest and name not in used:
            return name
    fresh = [name for name in STRATEGIES if name not in used]
    return rng.choice(fresh or list(STRATEGIES))


def _mutate(
    client: CachedClient,
    spec: PromptSpec,
    prompt: str,
    output: str,
    verdict: Verdict,
    strategy: str,
) -> str:
    request = f"""USER'S UNDERLYING GOAL:
{spec.goal or spec.title}

CURRENT PROMPT:
<prompt>
{prompt}
</prompt>

OUTPUT IT PRODUCED (truncated):
<output>
{output[:2500]}
</output>

EVALUATOR SCORE: {verdict.score:.0f}/100
WEAKEST DIMENSION: {verdict.weakest or "unspecified"}
EVALUATOR CRITIQUE: {verdict.critique or "none given"}

IMPROVEMENT STRATEGY FOR THIS ROUND: {STRATEGIES[strategy]}

---
Rewrite the prompt now."""

    result = client.complete(ENGINEER_SYSTEM, request, tag=f"evolve-{spec.slug}")
    if not result.ok:
        return prompt
    rewritten = result.text.strip().strip("`").strip()
    # A rewrite that collapses to nothing useful is worse than keeping the parent.
    return rewritten if len(rewritten) > 40 else prompt


def run_agent(
    spec: PromptSpec,
    cfg: RunConfig,
    client: CachedClient,
    on_event=lambda *_: None,
) -> AgentResult:
    """Hill-climb one prompt for up to cfg.rounds rounds."""
    result = AgentResult(spec=spec)
    rng = random.Random(f"{cfg.seed}:{spec.id}")
    prompt = spec.prompt
    strategy = "baseline"
    used: set[str] = set()

    for round_i in range(1, cfg.rounds + 1):
        started = time.monotonic()
        try:
            generated = client.complete(GEN_SYSTEM, prompt, tag=f"gen-{spec.slug}")
            if not generated.ok:
                result.attempts.append(
                    Attempt(round_i, strategy, prompt, "", 0.0, error=generated.error)
                )
                on_event(spec.id, round_i, 0.0, f"generation failed: {generated.error}")
                break

            verdict = judge(client, spec, prompt, generated.text)
        except BudgetExhausted as exc:
            result.stopped_because = str(exc)
            on_event(spec.id, round_i, 0.0, f"stopped: {exc}")
            break

        result.attempts.append(
            Attempt(
                round=round_i,
                strategy=strategy,
                prompt=prompt,
                output=generated.text,
                score=verdict.score,
                dimensions=verdict.dimensions,
                critique=verdict.critique,
                why_it_wins=verdict.why_it_wins,
                error=verdict.error,
                elapsed_s=round(time.monotonic() - started, 1),
            )
        )
        on_event(spec.id, round_i, verdict.score, verdict.weakest or "")

        if verdict.error:
            result.stopped_because = f"judge error: {verdict.error}"
            break
        if verdict.score >= cfg.target_score:
            result.stopped_because = f"hit target score ({cfg.target_score:.0f})"
            break
        if round_i == cfg.rounds:
            break

        parent = result.best or result.attempts[-1]
        strategy = _pick_strategy(rng, verdict, used)
        used.add(strategy)
        try:
            prompt = _mutate(
                client, spec, parent.prompt, parent.output, verdict, strategy
            )
        except BudgetExhausted as exc:
            result.stopped_because = str(exc)
            break

    return result
