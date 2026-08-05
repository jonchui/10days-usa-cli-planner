"""Offline tests for PromptLab. No credits spent — everything uses MockBackend."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from promptlab.agent import STRATEGIES, run_agent  # noqa: E402
from promptlab.backends import (  # noqa: E402
    Budget,
    BudgetExhausted,
    CachedClient,
    MockBackend,
    build_backend,
)
from promptlab.cli import main  # noqa: E402
from promptlab.config import ConfigError, PromptSpec, load_config  # noqa: E402
from promptlab.judge import _extract_json, judge  # noqa: E402

CONFIG_TEXT = """
[run]
name = "unit"
backend = "mock"
rounds = 3
parallel = 2
target_score = 99
seed = 5

[[prompt]]
id = "alpha"
title = "Alpha"
goal = "Do alpha well"
prompt = "Write something about alpha."

[[prompt]]
id = "beta"
title = "Beta"
prompt = "Write something about beta."
rubric = ["wit"]
"""


class TempRun(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.config_path = self.root / "unit.toml"
        self.config_path.write_text(CONFIG_TEXT, encoding="utf-8")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def make_client(self, budget: Budget | None = None) -> CachedClient:
        return CachedClient(
            backend=MockBackend(model="mock", timeout=10),
            cache_dir=self.root / "cache",
            budget=budget or Budget(max_calls=500, max_seconds=600),
            log_dir=self.root / "calls",
        )


class ConfigTests(TempRun):
    def test_loads_prompts_and_defaults(self) -> None:
        cfg = load_config(self.config_path)
        self.assertEqual([p.id for p in cfg.prompts], ["alpha", "beta"])
        self.assertEqual(cfg.prompts[1].rubric, ["wit"])
        # Unspecified rubric falls back to the run-level default.
        self.assertIn("usefulness", cfg.prompts[0].rubric)

    def test_overrides_beat_file(self) -> None:
        cfg = load_config(self.config_path, {"rounds": 1, "backend": "claude"})
        self.assertEqual(cfg.rounds, 1)
        self.assertEqual(cfg.backend, "claude")

    def test_only_filter(self) -> None:
        cfg = load_config(self.config_path, {"only": "beta"})
        self.assertEqual([p.id for p in cfg.prompts], ["beta"])

    def test_only_rejects_unknown_id(self) -> None:
        with self.assertRaises(ConfigError):
            load_config(self.config_path, {"only": "gamma"})

    def test_missing_prompt_body_is_an_error(self) -> None:
        bad = self.root / "bad.toml"
        bad.write_text('[[prompt]]\nid = "x"\n', encoding="utf-8")
        with self.assertRaises(ConfigError):
            load_config(bad)

    def test_fingerprint_tracks_content(self) -> None:
        a = load_config(self.config_path)
        b = load_config(self.config_path, {"seed": 99})
        self.assertNotEqual(a.fingerprint, b.fingerprint)

    def test_shipped_configs_are_valid(self) -> None:
        for path in (Path(__file__).resolve().parents[1] / "promptlab" / "prompts").glob("*.toml"):
            cfg = load_config(path)
            self.assertTrue(cfg.prompts, f"{path.name} has no prompts")


class CacheAndBudgetTests(TempRun):
    def test_second_identical_call_is_cached_and_free(self) -> None:
        budget = Budget(max_calls=10, max_seconds=60)
        client = self.make_client(budget)
        first = client.complete("sys", "hello")
        second = client.complete("sys", "hello")
        self.assertFalse(first.cached)
        self.assertTrue(second.cached)
        self.assertEqual(first.text, second.text)
        self.assertEqual(budget.calls, 1)

    def test_budget_stops_the_run(self) -> None:
        budget = Budget(max_calls=1, max_seconds=60)
        client = self.make_client(budget)
        client.complete("sys", "one")
        with self.assertRaises(BudgetExhausted):
            client.complete("sys", "two")

    def test_calls_are_logged_for_audit(self) -> None:
        client = self.make_client()
        client.complete("sys", "logged", tag="gen-alpha")
        logs = list((self.root / "calls").glob("*.json"))
        self.assertEqual(len(logs), 1)
        record = json.loads(logs[0].read_text())
        self.assertEqual(record["tag"], "gen-alpha")
        self.assertIn("logged", record["prompt"])

    def test_unknown_backend_rejected(self) -> None:
        with self.assertRaises(ValueError):
            build_backend("nope", "m", 10, [])


class JudgeTests(TempRun):
    def test_extract_json_survives_fences_and_prose(self) -> None:
        payload = _extract_json('here you go:\n```json\n{"score": 88}\n```')
        self.assertEqual(payload, {"score": 88})

    def test_extract_json_handles_braces_in_strings(self) -> None:
        payload = _extract_json('{"critique": "use {placeholders} less", "score": 7}')
        self.assertEqual(payload["score"], 7)

    def test_extract_json_returns_none_on_garbage(self) -> None:
        self.assertIsNone(_extract_json("no json here"))

    def test_judge_produces_a_score(self) -> None:
        spec = PromptSpec(id="a", title="A", goal="g", prompt="p")
        verdict = judge(self.make_client(), spec, "prompt", "output")
        self.assertIsNone(verdict.error)
        self.assertGreater(verdict.score, 0)


class AgentTests(TempRun):
    def test_agent_climbs_and_keeps_the_best(self) -> None:
        cfg = load_config(self.config_path)
        result = run_agent(cfg.prompts[0], cfg, self.make_client())
        self.assertGreaterEqual(len(result.attempts), 2)
        self.assertIsNotNone(result.best)
        self.assertEqual(
            result.best.score, max(a.score for a in result.attempts)
        )
        # The mock scores longer prompts higher, so the loop must improve.
        self.assertGreater(result.improvement, 0)

    def test_agent_stops_at_target_score(self) -> None:
        cfg = load_config(self.config_path, {"target_score": 1, "rounds": 5})
        result = run_agent(cfg.prompts[0], cfg, self.make_client())
        self.assertEqual(len(result.attempts), 1)
        self.assertIn("target", result.stopped_because)

    def test_strategy_selection_is_seed_deterministic(self) -> None:
        cfg = load_config(self.config_path)
        a = run_agent(cfg.prompts[0], cfg, self.make_client())
        b = run_agent(cfg.prompts[0], cfg, self.make_client())
        self.assertEqual(
            [x.strategy for x in a.attempts], [x.strategy for x in b.attempts]
        )
        for attempt in a.attempts[1:]:
            self.assertIn(attempt.strategy, STRATEGIES)


class EndToEndTests(TempRun):
    def test_dry_run_writes_a_readable_report(self) -> None:
        out = self.root / "runs"
        code = main([
            str(self.config_path), "--dry-run", "--quiet",
            "--out", str(out), "--cache-dir", str(self.root / "cache"),
        ])
        self.assertEqual(code, 0)

        run_dirs = list(out.iterdir())
        self.assertEqual(len(run_dirs), 1)
        run_dir = run_dirs[0]

        report = (run_dir / "BEST.md").read_text()
        self.assertIn("## Leaderboard", report)
        self.assertIn("Alpha", report)
        self.assertIn("Winning prompt (copy-paste)", report)

        meta = json.loads((run_dir / "run.json").read_text())
        self.assertEqual(meta["backend"], "mock")
        self.assertEqual(len(meta["results"]), 2)

        # Transcripts and the exact prompt set are preserved alongside the report.
        self.assertTrue((run_dir / "agents" / "alpha.json").exists())
        self.assertTrue((run_dir / "unit.toml").exists())

    def test_missing_config_exits_cleanly(self) -> None:
        self.assertEqual(main([str(self.root / "nope.toml"), "--dry-run"]), 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
