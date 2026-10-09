"""CLI: assess one mortgage case end to end.

Usage:
    python -m src.cli --case case-001 --run-id dev-smoke

The agent reads the case over MCP, applies the policy with its tools, submits the
dossier through the case-service, and this command reports what was submitted and
where it was stored (submitted/<run-id>/<case>.json). Exit code 0 only when a
submission landed.
"""

import argparse
import asyncio
import json
import os
import sys
import time

from src import config
from src.agent import build_agent
from src.schemas import Dossier


def _usage_totals(messages) -> tuple[int, int]:
    inp = out = 0
    for message in messages:
        usage = getattr(message, "usage_metadata", None) or {}
        inp += usage.get("input_tokens", 0) or 0
        out += usage.get("output_tokens", 0) or 0
    return inp, out


async def assess(case_id: str, run_id: str) -> int:
    os.environ["WINDMILL_RUN_ID"] = run_id

    print(f"[cli] assessing {case_id} as run '{run_id}' with {config.AGENT_MODEL}")
    started = time.monotonic()
    agent = await build_agent()
    result = await agent.ainvoke(
        {"messages": [{"role": "user", "content": f"Assess mortgage case {case_id}."}]}
    )
    elapsed = time.monotonic() - started

    input_tokens, output_tokens = _usage_totals(result.get("messages", []))
    structured: Dossier | None = result.get("structured_response")

    submitted_path = config.SUBMITTED_DIR / run_id / f"{case_id}.json"
    ok = True

    print(f"[cli] run finished in {elapsed:.0f}s; tokens in/out: {input_tokens}/{output_tokens}")
    if structured is None:
        print("[cli] ERROR: the agent returned no structured dossier")
        ok = False
    else:
        print(f"[cli] final status: {structured.status.value}")
        for check in structured.checks:
            missing = f" missing={check.missing_items}" if check.missing_items else ""
            print(f"  {check.check_id.value:22s} {check.outcome.value}{missing}")
        for action in structured.required_actions:
            print(f"  action: {action}")

    if submitted_path.exists():
        stored = json.loads(submitted_path.read_text(encoding="utf-8"))
        print(f"[cli] submission stored: {submitted_path} (at {stored['submitted_at']})")
        submitted_status = stored["dossier"]["status"]
        if structured is not None and submitted_status != structured.status.value:
            print(
                f"[cli] WARNING: submitted status {submitted_status} does not match "
                f"structured response {structured.status.value}"
            )
            ok = False
    else:
        print(f"[cli] ERROR: no submission found at {submitted_path}")
        ok = False

    return 0 if ok else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Assess one mortgage case end to end.")
    parser.add_argument("--case", required=True, help="case id, e.g. case-001")
    parser.add_argument("--run-id", default=None, help="run id for submission folders")
    args = parser.parse_args()

    run_id = args.run_id or config.RUN_ID
    return asyncio.run(assess(args.case, run_id))


if __name__ == "__main__":
    sys.exit(main())
