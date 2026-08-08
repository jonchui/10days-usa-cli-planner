"""Model backends.

Every backend shells out to a CLI you are already logged into, so the run
spends your existing Claude/Codex credits and needs no API key plumbing.

All calls go through a content-addressed cache, which is what makes a run
replayable: the same config + seed hits the cache and produces the same
report without spending anything.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import tempfile
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path


class BudgetExhausted(RuntimeError):
    """Raised when a run hits its call or wall-clock ceiling."""


@dataclass
class Completion:
    text: str
    cost_usd: float = 0.0
    cached: bool = False
    duration_s: float = 0.0
    error: str | None = None

    @property
    def ok(self) -> bool:
        return self.error is None and bool(self.text.strip())


@dataclass
class Budget:
    """Thread-safe ceiling shared by every side agent in a run."""

    max_calls: int
    max_seconds: float
    started: float = field(default_factory=time.monotonic)
    calls: int = 0
    cost_usd: float = 0.0
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def reserve(self) -> None:
        with self._lock:
            if self.calls >= self.max_calls:
                raise BudgetExhausted(f"call ceiling reached ({self.max_calls})")
            if time.monotonic() - self.started > self.max_seconds:
                raise BudgetExhausted(f"time ceiling reached ({self.max_seconds:.0f}s)")
            self.calls += 1

    def record_cost(self, cost: float) -> None:
        with self._lock:
            self.cost_usd += cost

    def refund(self) -> None:
        """Cache hits cost nothing, so they should not burn budget."""
        with self._lock:
            self.calls -= 1

    @property
    def elapsed(self) -> float:
        return time.monotonic() - self.started


class Backend:
    """Interface: turn (system, prompt) into text."""

    name = "base"

    def __init__(self, model: str, timeout: float, extra_args: list[str] | None = None):
        self.model = model
        self.timeout = timeout
        self.extra_args = list(extra_args or [])

    def preflight(self) -> None:
        """Fail fast with an actionable message before any work is queued."""

    def _invoke(self, system: str, prompt: str) -> Completion:
        raise NotImplementedError

    def complete(self, system: str, prompt: str) -> Completion:
        started = time.monotonic()
        result = self._invoke(system, prompt)
        result.duration_s = time.monotonic() - started
        return result


# Tools the lab must never touch: it generates text, it does not act.
_BLOCKED_TOOLS = (
    "Bash Read Write Edit NotebookEdit Glob Grep WebFetch WebSearch Task TodoWrite"
)

# When PromptLab is itself launched from inside a Claude Code session, the
# parent exports its own session identity. Every subprocess would inherit it
# and several agents would write to one transcript at once, which fails with an
# is_error result and zero tokens billed. Drop the identity, keep the auth.
_INHERITED_SESSION_VARS = (
    "CLAUDE_CODE_SESSION_ID",
    "CLAUDE_CODE_CHILD_SESSION",
    "CLAUDE_CODE_ENTRYPOINT",
    "CLAUDE_PID",
    "CLAUDE_AFTER_LAST_COMPACT",
    "CLAUDE_AUTO_BACKGROUND_TASKS",
    "CLAUDE_CODE_ADDITIONAL_DIRECTORIES_CLAUDE_MD",
)


def isolated_env() -> dict[str, str]:
    """A copy of os.environ with the parent session's identity removed."""
    env = os.environ.copy()
    for key in _INHERITED_SESSION_VARS:
        env.pop(key, None)
    return env


class ClaudeCLIBackend(Backend):
    """Headless `claude -p`, using whatever plan the CLI is logged into.

    Deliberately hermetic: settings sources and MCP servers are switched off and
    the system prompt is replaced rather than appended, so a run does not
    depend on the CLAUDE.md, skills, or MCP config of whatever directory it was
    started from. That is what makes results comparable across machines — and
    it cuts roughly 20k tokens of coding-agent scaffolding off every call.
    """

    name = "claude"

    def preflight(self) -> None:
        if not shutil.which("claude"):
            raise RuntimeError(
                "the `claude` CLI is not on PATH. Install it "
                "(https://claude.com/claude-code) or run with --backend mock."
            )

    def _argv(self, system: str) -> list[str]:
        argv = [
            "claude",
            "-p",
            "--output-format",
            "json",
            "--model",
            self.model,
            "--max-turns",
            "1",
            "--setting-sources",
            "",
            "--strict-mcp-config",
            "--disallowed-tools",
            _BLOCKED_TOOLS,
        ]
        if system:
            argv += ["--system-prompt", system]
        return argv + self.extra_args

    def _invoke(self, system: str, prompt: str) -> Completion:
        try:
            proc = subprocess.run(
                self._argv(system),
                input=prompt,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                cwd=tempfile.gettempdir(),
                env=isolated_env(),
            )
        except subprocess.TimeoutExpired:
            return Completion(text="", error=f"timeout after {self.timeout:.0f}s")

        raw = proc.stdout.strip()

        if proc.returncode != 0:
            # A failing run still prints its JSON envelope; surface the human
            # message from it rather than a wall of usage counters.
            return Completion(
                text="", error=f"exit {proc.returncode}: {_cli_error_message(raw, proc.stderr)}"
            )

        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            # Older CLIs (or --output-format text) just print the answer.
            return Completion(text=raw)

        if isinstance(payload, list):  # stream-json shape
            payload = next(
                (m for m in reversed(payload) if m.get("type") == "result"), {}
            )
        if payload.get("is_error"):
            return Completion(text="", error=str(payload.get("result", "cli error"))[:400])
        return Completion(
            text=str(payload.get("result", "")),
            cost_usd=float(payload.get("total_cost_usd") or 0.0),
        )


class CodexCLIBackend(Backend):
    """OpenAI Codex CLI in non-interactive `exec` mode."""

    name = "codex"

    def preflight(self) -> None:
        if not shutil.which("codex"):
            raise RuntimeError(
                "the `codex` CLI is not on PATH. Install it "
                "(https://github.com/openai/codex) or run with --backend claude."
            )

    def _invoke(self, system: str, prompt: str) -> Completion:
        argv = ["codex", "exec", "--skip-git-repo-check"]
        if self.model:
            argv += ["--model", self.model]
        argv += self.extra_args
        body = f"{system}\n\n---\n\n{prompt}" if system else prompt
        try:
            proc = subprocess.run(
                argv,
                input=body,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                env=isolated_env(),
            )
        except subprocess.TimeoutExpired:
            return Completion(text="", error=f"timeout after {self.timeout:.0f}s")
        if proc.returncode != 0:
            return Completion(
                text="",
                error=f"exit {proc.returncode}: {_cli_error_message(proc.stdout, proc.stderr)}",
            )
        return Completion(text=_strip_codex_chrome(proc.stdout))


class MockBackend(Backend):
    """Deterministic offline stand-in, for tests and `--dry-run` plumbing checks."""

    name = "mock"

    def _invoke(self, system: str, prompt: str) -> Completion:
        digest = hashlib.sha256((system + prompt).encode()).hexdigest()
        if "SCORECARD" in system:
            # Score climbs with prompt length so the loop visibly converges.
            score = min(97, 55 + len(prompt) // 60)
            dims = {"usefulness": score, "specificity": score, "format": score}
            return Completion(
                text=json.dumps(
                    {
                        "dimensions": dims,
                        "score": score,
                        "weakest": "specificity",
                        "critique": "mock backend: add concrete constraints",
                        "why_it_wins": "mock verdict",
                    }
                )
            )
        if "PROMPT ENGINEER" in system:
            return Completion(text=prompt.split("---", 1)[-1].strip() + f"\n\nAlso: be concrete ({digest[:6]}).")
        return Completion(text=f"[mock output {digest[:8]}]\n\n{prompt[:280]}")


def _cli_error_message(stdout: str, stderr: str) -> str:
    """Pull the readable failure reason out of a CLI's JSON error envelope."""
    try:
        payload = json.loads(stdout)
    except (json.JSONDecodeError, TypeError):
        payload = None
    if isinstance(payload, dict):
        message = str(payload.get("result") or payload.get("error") or "").strip()
        reason = str(payload.get("subtype") or payload.get("terminal_reason") or "").strip()
        detail = " / ".join(part for part in (message, reason) if part)
        if detail:
            return detail[:300]
    return ((stderr or stdout or "no output").strip())[:300]


def _strip_codex_chrome(stdout: str) -> str:
    """Drop the leading metadata block codex exec prints before the answer."""
    lines = stdout.splitlines()
    for i, line in enumerate(lines):
        if line.strip().startswith("--------") and i + 1 < len(lines):
            return "\n".join(lines[i + 1 :]).strip()
    return stdout.strip()


BACKENDS: dict[str, type[Backend]] = {
    "claude": ClaudeCLIBackend,
    "codex": CodexCLIBackend,
    "mock": MockBackend,
}


def build_backend(name: str, model: str, timeout: float, extra_args: list[str]) -> Backend:
    try:
        cls = BACKENDS[name]
    except KeyError:
        raise ValueError(
            f"unknown backend '{name}' (choose from {', '.join(sorted(BACKENDS))})"
        ) from None
    return cls(model=model, timeout=timeout, extra_args=extra_args)


class CachedClient:
    """Backend + on-disk cache + shared budget + retries.

    This is the only thing the agents call, so every model interaction in a
    run lands in one place: cached, logged, and counted.
    """

    def __init__(
        self,
        backend: Backend,
        cache_dir: Path,
        budget: Budget,
        log_dir: Path,
        use_cache: bool = True,
        retries: int = 2,
    ):
        self.backend = backend
        self.cache_dir = cache_dir
        self.budget = budget
        self.log_dir = log_dir
        self.use_cache = use_cache
        self.retries = retries
        self._lock = threading.Lock()
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def _key(self, system: str, prompt: str) -> str:
        blob = json.dumps(
            [self.backend.name, self.backend.model, system, prompt], sort_keys=True
        )
        return hashlib.sha256(blob.encode()).hexdigest()

    def complete(self, system: str, prompt: str, *, tag: str = "call") -> Completion:
        key = self._key(system, prompt)
        cache_file = self.cache_dir / f"{key}.json"

        if self.use_cache and cache_file.exists():
            payload = json.loads(cache_file.read_text(encoding="utf-8"))
            return Completion(text=payload["text"], cost_usd=0.0, cached=True)

        last: Completion | None = None
        for attempt in range(self.retries + 1):
            self.budget.reserve()
            result = self.backend.complete(system, prompt)
            if result.ok:
                self.budget.record_cost(result.cost_usd)
                if self.use_cache:
                    cache_file.write_text(
                        json.dumps({"text": result.text, "model": self.backend.model}),
                        encoding="utf-8",
                    )
                self._log(tag, key, system, prompt, result)
                return result
            last = result
            if attempt < self.retries:
                time.sleep(2 ** attempt)

        assert last is not None
        self._log(tag, key, system, prompt, last)
        return last

    def _log(self, tag: str, key: str, system: str, prompt: str, result: Completion) -> None:
        record = {
            "tag": tag,
            "key": key,
            "backend": self.backend.name,
            "model": self.backend.model,
            "system": system,
            "prompt": prompt,
            "text": result.text,
            "error": result.error,
            "cost_usd": result.cost_usd,
            "duration_s": round(result.duration_s, 2),
        }
        path = self.log_dir / f"{int(time.time() * 1000)}-{tag}-{key[:8]}.json"
        with self._lock:
            path.write_text(json.dumps(record, indent=2), encoding="utf-8")


def default_cache_dir() -> Path:
    return Path(os.environ.get("PROMPTLAB_CACHE", ".promptlab/cache"))
