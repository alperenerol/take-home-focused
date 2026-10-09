# Windmill Bank - Mortgage Case Assessment Agent

A small agentic application for mortgage underwriting triage: assess one submitted case
(customer declaration + supporting evidence) against the lender's operational policy and
produce a structured recommendation dossier for a human underwriter.

Built as an exercise in applied agent engineering.

> STATUS: work in progress. This README is a skeleton and is completed through build phase P7.

## Stack

- LangChain `create_agent` - standard ReAct loop over LangGraph; the model decides tool calls.
- Native tools: `search_policy` (RAG over the policy corpus) and `mortgage_calculator`
  (deterministic LTV / DTI / stress math, unit-tested).
- Custom case service exposed as an MCP server (FastMCP over stdio) and loaded with
  `langchain.mcp`: `get_case_files`, `submit_dossier`.
- OpenAI models (cheap-first: Luna-class agent, Sol-class judge).
- LangSmith for tracing and evaluation.

## Quickstart

Requires Python 3.10+ (developed on 3.12).

1. Environment: `cp .env.example .env` and fill in `OPENAI_API_KEY` and `LANGSMITH_API_KEY`.
2. Set up: `make setup` (creates `.venv`, installs pinned dependencies).
3. Tests: `make test`.
4. Assess a case (from P3): `make run CASE=case-001`.

## LangSmith setup

Create a project named `windmill-bank-agent` (LangSmith -> Projects). In the project's
Settings, set data retention to Extended (180 days) BEFORE the first run so traces survive
long enough to be inspected. Trace and evaluation run links will be listed here at P7.

## Architecture

```text
TBD (diagram lands at P7)
```

## Evaluation

TBD (P4-P6): ~20 synthetic cases with expected outcomes; deterministic evaluators plus a
calibrated LLM judge; before/after comparison with slices.

## Repository layout

- `src/` - agent, tools, MCP server, schemas
- `knowledge/` - policy corpus (markdown sections)
- `cases/` - case fixtures, expected labels, generator script
- `evals/` - LangSmith dataset upload, evaluators, runner, results
- `tests/` - unit tests

## Known limitations

TBD (P7).
