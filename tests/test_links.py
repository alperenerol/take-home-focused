"""Offline tests for trace stats, urls and the link collector mapping."""

import asyncio
from types import SimpleNamespace

from evals import links


def test_trace_stats_aggregates():
    kids = [
        SimpleNamespace(run_type="llm", total_tokens=100, prompt_tokens=80, completion_tokens=20, status="success", error=None),
        SimpleNamespace(run_type="llm", total_tokens=50, prompt_tokens=40, completion_tokens=10, status="success", error=None),
        SimpleNamespace(run_type="tool", total_tokens=None, prompt_tokens=None, completion_tokens=None, status="success", error=None),
        SimpleNamespace(run_type="tool", total_tokens=None, prompt_tokens=None, completion_tokens=None, status="error", error="boom"),
        SimpleNamespace(run_type="chain", total_tokens=None, prompt_tokens=None, completion_tokens=None, status="success", error=None),
    ]
    stats = links.trace_stats(kids)
    assert stats["llm_calls"] == 2
    assert stats["tool_calls"] == 2
    assert stats["chain_calls"] == 1
    assert stats["errors"] == 1
    assert stats["total_tokens"] == 150
    assert stats["prompt_tokens"] == 120


def test_trace_url_shape():
    url = links.trace_url("org-1", "proj-1", "trace-1")
    assert url == "https://smith.langchain.com/o/org-1/projects/p/proj-1/r/trace-1"


def make_fake_client():
    kids = {
        "t1": [
            SimpleNamespace(run_type="llm", total_tokens=30, prompt_tokens=20, completion_tokens=10, status="success", error=None),
            SimpleNamespace(run_type="tool", total_tokens=None, prompt_tokens=None, completion_tokens=None, status="success", error=None),
        ]
    }
    roots = [
        SimpleNamespace(
            id="r1",
            trace_id="t1",
            reference_example_id="e1",
            latency_seconds=12.5,
            run_type="chain",
            status="success",
            error=None,
        )
    ]
    project = SimpleNamespace(id="proj-1", name="baseline-v0-test", tenant_id="org-1", start_time=None)

    class FakeRuns:
        def query(self, **kwargs):
            runs = roots if kwargs.get("is_root") else kids.get(str(kwargs.get("trace_id")), [])

            async def gen():
                for run in runs:
                    yield run

            return gen()

    class FakeClient:
        runs = FakeRuns()

        def list_projects(self):
            return [project]

        def read_example(self, example_id):
            assert example_id == "e1"
            return SimpleNamespace(inputs={"case_id": "case-001"})

    return FakeClient()


def test_collect_maps_cases_and_stats():
    payload = asyncio.run(links.collect("baseline-v0", "baseline-v0-test", client=make_fake_client()))
    assert payload["experiment"] == "baseline-v0-test"
    case = payload["cases"]["case-001"]
    assert case["run_id"] == "r1"
    assert case["trace_id"] == "t1"
    assert case["latency_seconds"] == 12.5
    assert case["llm_calls"] == 1
    assert case["total_tokens"] == 30
    assert case["url"].endswith("/r/t1")
