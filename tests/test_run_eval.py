"""Offline tests for the eval runner plumbing (fake agent, no network)."""

import asyncio
import json
from types import SimpleNamespace

import evals.run_eval as run_eval
from evals.judge import JudgeVerdict
from src import config


def test_extract_tool_names_mixed_shapes():
    messages = [
        SimpleNamespace(tool_calls=[{"name": "get_case_files", "args": {}}]),
        SimpleNamespace(content="thinking"),
        SimpleNamespace(tool_calls=[SimpleNamespace(name="search_policy", args={})]),
        SimpleNamespace(tool_calls=None),
    ]
    assert run_eval.extract_tool_names(messages) == ["get_case_files", "search_policy"]


def test_target_writes_record_and_reads_submission(tmp_path, monkeypatch):
    monkeypatch.setattr(run_eval, "RESULTS_DIR", tmp_path / "results")
    monkeypatch.setattr(config, "SUBMITTED_DIR", tmp_path / "submitted")
    run_id = "test-run"

    dossier = {"case_id": "case-001", "status": "READY_FOR_UNDERWRITING", "checks": []}
    submission = config.SUBMITTED_DIR / run_id / "case-001.json"
    submission.parent.mkdir(parents=True)
    submission.write_text(json.dumps({"run_id": run_id, "dossier": dossier}), encoding="utf-8")

    class FakeAgent:
        async def ainvoke(self, payload):
            return {
                "messages": [
                    SimpleNamespace(tool_calls=[{"name": "get_case_files"}]),
                    SimpleNamespace(tool_calls=[{"name": "submit_dossier"}]),
                ],
                "structured_response": SimpleNamespace(model_dump=lambda: dossier),
            }

    async def fake_build_agent():
        return FakeAgent()

    monkeypatch.setattr(run_eval, "build_agent", fake_build_agent)

    record = asyncio.run(run_eval.make_target(run_id)({"case_id": "case-001"}))
    assert record["submitted"] == dossier
    assert record["structured"] == dossier
    assert record["tool_names"] == ["get_case_files", "submit_dossier"]
    assert record["model"] == config.AGENT_MODEL

    saved = json.loads((run_eval.record_path(run_id, "case-001")).read_text(encoding="utf-8"))
    assert saved == record


def test_target_records_error_and_reraises(tmp_path, monkeypatch):
    monkeypatch.setattr(run_eval, "RESULTS_DIR", tmp_path / "results")

    class BoomAgent:
        async def ainvoke(self, payload):
            raise RuntimeError("provider exploded")

    async def fake_build_agent():
        return BoomAgent()

    monkeypatch.setattr(run_eval, "build_agent", fake_build_agent)

    async def go():
        try:
            await run_eval.make_target("test-run")({"case_id": "case-002"})
        except RuntimeError as exc:
            assert "provider exploded" in str(exc)
        else:
            raise AssertionError("expected the target to re-raise")

    asyncio.run(go())
    saved = json.loads(run_eval.record_path("test-run", "case-002").read_text(encoding="utf-8"))
    assert "RuntimeError: provider exploded" in saved["error"]
    assert saved["submitted"] is None


def test_judge_evaluator_caches_verdict(tmp_path, monkeypatch):
    monkeypatch.setattr(run_eval, "RESULTS_DIR", tmp_path / "results")

    async def fake_judge_case(case_id, dossier, *, model=None):
        return JudgeVerdict(grounded=True, score=4, unsupported_claims=[], comment="fine")

    monkeypatch.setattr(run_eval, "judge_case", fake_judge_case)

    run = SimpleNamespace(
        outputs={"submitted": {"case_id": "case-001", "checks": []}},
        inputs={"case_id": "case-001"},
        error=None,
    )
    example = SimpleNamespace(inputs={"case_id": "case-001"}, outputs={})
    result = asyncio.run(run_eval.make_judge_evaluator("test-run")(run, example))
    assert result["key"] == "judge_grounded"
    assert result["score"] == 1.0
    assert "4/5" in result["comment"]

    cached = json.loads(
        (run_eval.results_dir("test-run") / "judge" / "case-001.json").read_text(encoding="utf-8")
    )
    assert cached["grounded"] is True and cached["score"] == 4


def test_judge_evaluator_without_submission():
    run = SimpleNamespace(outputs=None, inputs={"case_id": "case-001"}, error="boom")
    example = SimpleNamespace(inputs={"case_id": "case-001"}, outputs={})
    result = asyncio.run(run_eval.make_judge_evaluator("test-run")(run, example))
    assert result["score"] == 0.0
    assert "no submission" in result["comment"]
