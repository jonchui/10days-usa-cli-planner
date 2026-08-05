"""Config loading for PromptLab.

A run is fully described by one TOML file, so a run is reproducible by
re-pointing at the same file (plus the same seed and cache).
"""

from __future__ import annotations

import hashlib
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

DEFAULT_RUBRIC = [
    "usefulness",
    "specificity",
    "actionability",
    "honesty",
    "format",
]


@dataclass(frozen=True)
class PromptSpec:
    """One prompt to be optimized by one side agent."""

    id: str
    title: str
    goal: str
    prompt: str
    rubric: list[str] = field(default_factory=lambda: list(DEFAULT_RUBRIC))

    @property
    def slug(self) -> str:
        return "".join(c if c.isalnum() or c in "-_" else "-" for c in self.id)


@dataclass(frozen=True)
class RunConfig:
    """Everything that controls a run, hashed for reproducibility."""

    name: str
    backend: str
    model: str
    rounds: int
    parallel: int
    target_score: float
    max_calls: int
    max_seconds: float
    seed: int
    timeout: float
    extra_args: list[str]
    prompts: list[PromptSpec]
    source_path: Path
    source_text: str

    @property
    def fingerprint(self) -> str:
        """Stable hash of the config text + knobs that change results."""
        payload = "\n".join(
            [
                self.source_text,
                self.backend,
                self.model,
                str(self.rounds),
                str(self.target_score),
                str(self.seed),
            ]
        )
        return hashlib.sha256(payload.encode()).hexdigest()[:12]


class ConfigError(ValueError):
    pass


def load_config(path: Path, overrides: dict | None = None) -> RunConfig:
    """Read a TOML prompt-set file into a RunConfig.

    CLI overrides win over file values so a single config can be re-run
    cheaply (``--rounds 1 --backend mock``) without editing it.
    """
    overrides = {k: v for k, v in (overrides or {}).items() if v is not None}
    text = path.read_text(encoding="utf-8")
    try:
        data = tomllib.loads(text)
    except tomllib.TOMLDecodeError as exc:
        raise ConfigError(f"{path}: invalid TOML: {exc}") from exc

    run = data.get("run", {})
    raw_prompts = data.get("prompt", [])
    if not raw_prompts:
        raise ConfigError(f"{path}: no [[prompt]] entries found")

    default_rubric = run.get("rubric", DEFAULT_RUBRIC)
    prompts: list[PromptSpec] = []
    seen: set[str] = set()
    for i, entry in enumerate(raw_prompts):
        for required in ("id", "prompt"):
            if not entry.get(required):
                raise ConfigError(f"{path}: [[prompt]] #{i + 1} is missing '{required}'")
        pid = str(entry["id"])
        if pid in seen:
            raise ConfigError(f"{path}: duplicate prompt id '{pid}'")
        seen.add(pid)
        prompts.append(
            PromptSpec(
                id=pid,
                title=str(entry.get("title", pid)),
                goal=str(entry.get("goal", "")).strip(),
                prompt=str(entry["prompt"]).strip(),
                rubric=list(entry.get("rubric", default_rubric)),
            )
        )

    only = overrides.pop("only", None)
    if only:
        wanted = {s.strip() for s in only.split(",") if s.strip()}
        unknown = wanted - {p.id for p in prompts}
        if unknown:
            raise ConfigError(f"unknown prompt id(s): {', '.join(sorted(unknown))}")
        prompts = [p for p in prompts if p.id in wanted]

    def pick(key: str, default):
        return overrides.get(key, run.get(key, default))

    cfg = RunConfig(
        name=str(pick("name", path.stem)),
        backend=str(pick("backend", "claude")),
        model=str(pick("model", "opus")),
        rounds=int(pick("rounds", 4)),
        parallel=int(pick("parallel", 4)),
        target_score=float(pick("target_score", 93.0)),
        max_calls=int(pick("max_calls", 200)),
        max_seconds=float(pick("max_seconds", 3600.0)),
        seed=int(pick("seed", 1337)),
        timeout=float(pick("timeout", 300.0)),
        extra_args=list(pick("extra_args", [])),
        prompts=prompts,
        source_path=path,
        source_text=text,
    )
    if cfg.rounds < 1:
        raise ConfigError("rounds must be >= 1")
    if cfg.parallel < 1:
        raise ConfigError("parallel must be >= 1")
    return cfg
