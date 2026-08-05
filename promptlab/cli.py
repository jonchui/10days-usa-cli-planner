"""PromptLab CLI: run N prompts as N parallel self-improving side agents."""

from __future__ import annotations

import argparse
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

from .agent import AgentResult, run_agent
from .backends import Budget, CachedClient, build_backend, default_cache_dir
from .config import ConfigError, RunConfig, load_config
from .report import terminal_digest, write_raw, write_report

DEFAULT_CONFIG = Path(__file__).parent / "prompts" / "streaming-replacement.toml"


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="promptlab",
        description="Run each prompt in its own side agent that keeps rewriting "
        "itself until a judge model stops finding faults, then report the winners.",
    )
    p.add_argument("config", nargs="?", type=Path, default=DEFAULT_CONFIG,
                   help=f"TOML prompt set (default: {DEFAULT_CONFIG.name})")
    p.add_argument("--backend", choices=["claude", "codex", "mock"],
                   help="which CLI to drive (default: from config)")
    p.add_argument("--model", help="model name passed to the backend CLI")
    p.add_argument("--rounds", type=int, help="max improvement rounds per agent")
    p.add_argument("--parallel", type=int, help="agents to run concurrently")
    p.add_argument("--target-score", type=float, dest="target_score",
                   help="stop an agent early once it scores this well")
    p.add_argument("--max-calls", type=int, dest="max_calls",
                   help="hard ceiling on model calls for the whole run")
    p.add_argument("--max-seconds", type=float, dest="max_seconds",
                   help="hard wall-clock ceiling for the whole run")
    p.add_argument("--seed", type=int, help="seed for strategy selection")
    p.add_argument("--timeout", type=float, help="per-call timeout in seconds")
    p.add_argument("--only", help="comma-separated prompt ids to run")
    p.add_argument("--out", type=Path, default=Path("runs"), help="run output directory")
    p.add_argument("--cache-dir", type=Path, default=None,
                   help="shared response cache (default: $PROMPTLAB_CACHE or .promptlab/cache)")
    p.add_argument("--no-cache", action="store_true",
                   help="ignore the cache and re-spend credits")
    p.add_argument("--dry-run", action="store_true",
                   help="use the offline mock backend to check wiring for free")
    p.add_argument("--quiet", action="store_true", help="only print the final digest")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if not args.config.exists():
        print(f"config not found: {args.config}", file=sys.stderr)
        return 2

    overrides = {
        k: getattr(args, k)
        for k in ("backend", "model", "rounds", "parallel", "target_score",
                  "max_calls", "max_seconds", "seed", "timeout", "only")
    }
    if args.dry_run:
        overrides["backend"] = "mock"

    try:
        cfg = load_config(args.config, overrides)
    except ConfigError as exc:
        print(f"config error: {exc}", file=sys.stderr)
        return 2

    backend = build_backend(cfg.backend, cfg.model, cfg.timeout, cfg.extra_args)
    try:
        backend.preflight()
    except RuntimeError as exc:
        print(f"backend unavailable: {exc}", file=sys.stderr)
        return 3

    run_id = f"{datetime.now().strftime('%Y%m%d-%H%M%S')}-{cfg.name}-{cfg.fingerprint}"
    run_dir = args.out / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    budget = Budget(max_calls=cfg.max_calls, max_seconds=cfg.max_seconds)
    client = CachedClient(
        backend=backend,
        cache_dir=args.cache_dir or default_cache_dir(),
        budget=budget,
        log_dir=run_dir / "calls",
        use_cache=not args.no_cache,
    )

    if not args.quiet:
        print(f"PromptLab · {cfg.name} · {cfg.backend}/{cfg.model}")
        print(f"{len(cfg.prompts)} agents · up to {cfg.rounds} rounds · "
              f"{cfg.parallel} in parallel · ceiling {cfg.max_calls} calls")
        print(f"run dir: {run_dir}\n")

    print_lock = threading.Lock()

    def on_event(prompt_id: str, round_i: int, score: float, note: str) -> None:
        if args.quiet:
            return
        with print_lock:
            suffix = f"  ({note})" if note else ""
            print(f"  [{prompt_id}] round {round_i}: {score:5.1f}{suffix}", flush=True)

    results: list[AgentResult] = []
    with ThreadPoolExecutor(max_workers=cfg.parallel) as pool:
        futures = {
            pool.submit(run_agent, spec, cfg, client, on_event): spec
            for spec in cfg.prompts
        }
        try:
            for future in as_completed(futures):
                spec = futures[future]
                try:
                    results.append(future.result())
                except Exception as exc:  # one agent dying must not sink the run
                    with print_lock:
                        print(f"  [{spec.id}] agent crashed: {exc}", file=sys.stderr)
                    results.append(
                        AgentResult(spec=spec, stopped_because=f"crashed: {exc}")
                    )
        except KeyboardInterrupt:
            print("\ninterrupted — writing a report from what finished", file=sys.stderr)
            for future in futures:
                future.cancel()

    write_raw(results, cfg, budget, run_dir)
    report_path = write_report(results, cfg, budget, run_dir)

    print(terminal_digest(results, cfg, budget))
    print(f"  full report: {report_path}\n")

    return 0 if any(r.best for r in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
