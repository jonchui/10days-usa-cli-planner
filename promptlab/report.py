"""Turn a run into something a human reads in 30 seconds."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from .agent import AgentResult
from .backends import Budget
from .config import RunConfig

OUTPUT_PREVIEW_CHARS = 1200


def _bar(score: float, width: int = 10) -> str:
    filled = int(round(score / 100 * width))
    return "█" * filled + "·" * (width - filled)


def _trim(text: str, limit: int = OUTPUT_PREVIEW_CHARS) -> tuple[str, bool]:
    text = text.strip()
    if len(text) <= limit:
        return text, False
    cut = text[:limit]
    # Prefer to break on a paragraph boundary so the preview reads cleanly.
    boundary = cut.rfind("\n\n")
    if boundary > limit * 0.6:
        cut = cut[:boundary]
    return cut.rstrip(), True


def terminal_digest(results: list[AgentResult], cfg: RunConfig, budget: Budget) -> str:
    """The short version, printed when the run ends."""
    ranked = sorted(results, key=lambda r: (r.best.score if r.best else 0), reverse=True)
    lines = [
        "",
        f"  PromptLab · {cfg.name} · {cfg.backend}/{cfg.model}",
        f"  {len(results)} agents · {budget.calls} calls · {budget.elapsed:.0f}s"
        + (f" · ${budget.cost_usd:.2f}" if budget.cost_usd else ""),
        "",
    ]
    for rank, res in enumerate(ranked, 1):
        best = res.best
        if not best:
            lines.append(f"  {rank}. {res.spec.title[:44]:<44}  —  no scored output")
            continue
        delta = f"+{res.improvement:.0f}" if res.improvement > 0 else f"{res.improvement:.0f}"
        lines.append(
            f"  {rank}. {res.spec.title[:44]:<44} {_bar(best.score)} "
            f"{best.score:5.1f}  (r{best.round}, {delta})"
        )
        if best.why_it_wins:
            lines.append(f"     {_trim(best.why_it_wins, 96)[0]}")
    lines.append("")
    return "\n".join(lines)


def write_report(
    results: list[AgentResult], cfg: RunConfig, budget: Budget, run_dir: Path
) -> Path:
    """Write BEST.md: leaderboard, then winning prompt + output per agent."""
    ranked = sorted(results, key=lambda r: (r.best.score if r.best else 0), reverse=True)
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    out: list[str] = [
        f"# {cfg.name} — best outputs",
        "",
        f"`{cfg.backend}/{cfg.model}` · {len(results)} side agents · up to {cfg.rounds} rounds each  ",
        f"{budget.calls} model calls · {budget.elapsed:.0f}s"
        + (f" · ${budget.cost_usd:.2f}" if budget.cost_usd else " · cost not reported")
        + f" · config `{cfg.source_path.name}` (fingerprint `{cfg.fingerprint}`) · {stamp}",
        "",
        "## Leaderboard",
        "",
        "| # | Prompt | Best | Round | Gain vs. round 1 | Stopped because |",
        "|---|--------|------|-------|------------------|-----------------|",
    ]
    for rank, res in enumerate(ranked, 1):
        best = res.best
        score = f"**{best.score:.0f}**" if best else "—"
        rnd = str(best.round) if best else "—"
        gain = f"+{res.improvement:.0f}" if res.improvement > 0 else f"{res.improvement:.0f}"
        out.append(
            f"| {rank} | {res.spec.title} | {score} | {rnd} | {gain} | {res.stopped_because} |"
        )

    out += ["", "---", ""]

    for rank, res in enumerate(ranked, 1):
        best = res.best
        out.append(f"## {rank}. {res.spec.title}")
        out.append("")
        if not best:
            out += [
                "No scored output — every round errored.",
                "",
                "```",
                (res.attempts[-1].error if res.attempts else "no attempts recorded") or "",
                "```",
                "",
            ]
            continue

        out.append(f"**{best.score:.0f}/100** after {len(res.attempts)} round(s) · "
                   f"strategy that won: `{best.strategy}`")
        out.append("")
        if best.why_it_wins:
            out += [f"> {best.why_it_wins}", ""]
        if best.dimensions:
            dims = " · ".join(f"{k} {v:.0f}" for k, v in best.dimensions.items())
            out += [f"`{dims}`", ""]

        preview, truncated = _trim(best.output)
        out += ["**Output**", "", preview]
        if truncated:
            out.append("")
            out.append(f"*(truncated — full text in `agents/{res.spec.slug}.json`)*")
        out += ["", "<details><summary>Winning prompt (copy-paste)</summary>", "", "```text",
                best.prompt.strip(), "```", "", "</details>", ""]

        if len(res.attempts) > 1:
            trail = " → ".join(
                f"r{a.round} {a.score:.0f}" + (f" [{a.strategy}]" if a.strategy != "baseline" else "")
                for a in res.attempts
            )
            out += [f"<details><summary>Score trail</summary>", "", f"`{trail}`", ""]
            for a in res.attempts:
                if a.critique:
                    out.append(f"- **r{a.round}** ({a.score:.0f}) — {a.critique}")
            out += ["", "</details>", ""]

        out.append("---")
        out.append("")

    report_path = run_dir / "BEST.md"
    report_path.write_text("\n".join(out), encoding="utf-8")
    return report_path


def write_raw(results: list[AgentResult], cfg: RunConfig, budget: Budget, run_dir: Path) -> None:
    """Full transcripts, so a report can always be traced back to its evidence."""
    agents_dir = run_dir / "agents"
    agents_dir.mkdir(parents=True, exist_ok=True)
    for res in results:
        (agents_dir / f"{res.spec.slug}.json").write_text(
            json.dumps(res.to_dict(), indent=2), encoding="utf-8"
        )

    (run_dir / "run.json").write_text(
        json.dumps(
            {
                "name": cfg.name,
                "backend": cfg.backend,
                "model": cfg.model,
                "rounds": cfg.rounds,
                "parallel": cfg.parallel,
                "seed": cfg.seed,
                "target_score": cfg.target_score,
                "config_file": str(cfg.source_path),
                "config_fingerprint": cfg.fingerprint,
                "calls": budget.calls,
                "cost_usd": round(budget.cost_usd, 4),
                "elapsed_s": round(budget.elapsed, 1),
                "finished_at": datetime.now(timezone.utc).isoformat(),
                "results": [
                    {
                        "id": r.spec.id,
                        "best_score": r.best.score if r.best else 0.0,
                        "improvement": round(r.improvement, 1),
                        "rounds_run": len(r.attempts),
                    }
                    for r in results
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    # Snapshot the exact prompt set that produced this run.
    (run_dir / cfg.source_path.name).write_text(cfg.source_text, encoding="utf-8")
