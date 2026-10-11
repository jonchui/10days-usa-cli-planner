"""Guppy vN — prompt-based backend on the Claude API.

A "version" is a system-prompt file under guppy/prompts/ plus a model id.
Later versions may point at a fine-tuned model; the interface is the same.
"""
from __future__ import annotations

import os
from pathlib import Path

import anthropic

from scripts.common import format_input

DEFAULT_MODEL = "claude-opus-5"


class PromptGuppy:
    def __init__(self, prompt_file: Path, model: str = DEFAULT_MODEL, effort: str = "low"):
        self.prompt = Path(prompt_file).read_text(encoding="utf-8")
        self.model = model
        self.effort = effort
        self.client = anthropic.Anthropic()
        self.version = f"{Path(prompt_file).stem}-{model}"

    def respond(self, rec: dict) -> str:
        resp = self.client.messages.create(
            model=self.model,
            max_tokens=256,
            system=[{"type": "text", "text": self.prompt, "cache_control": {"type": "ephemeral"}}],
            output_config={"effort": self.effort},
            messages=[{"role": "user", "content": format_input(rec)}],
        )
        if resp.stop_reason == "refusal":
            return "[refusal]"
        text = "".join(b.text for b in resp.content if b.type == "text").strip()
        return text.splitlines()[0].strip() if text else ""


JUDGE_PROMPT = """You are grading whether a candidate line could stand in for the original GUPPI line from the Bobiverse books.
Answer YES only if the candidate (1) carries the same information/decision as the original, (2) has the same register: bracketed, terse, no first person, no hedging, and (3) is roughly the same length (within 2x).
Answer with a single word: YES or NO."""


def judge(client: anthropic.Anthropic, rec: dict, pred: str, model: str = "claude-sonnet-5") -> bool:
    resp = client.messages.create(
        model=model,
        max_tokens=8,
        system=JUDGE_PROMPT,
        output_config={"effort": "low"},
        messages=[{"role": "user", "content": f"{format_input(rec)}\n\nORIGINAL: {rec['output']}\nCANDIDATE: {pred}"}],
    )
    text = "".join(b.text for b in resp.content if b.type == "text").strip().upper()
    return text.startswith("YES")


def have_credentials() -> bool:
    return bool(os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN"))
