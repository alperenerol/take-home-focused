"""Shared configuration: repo paths, .env loading, model pins.

Everything that needs to find a directory or an environment variable goes through
this module so paths stay consistent between the CLI, tools, MCP server and tests.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[1]

load_dotenv(REPO_ROOT / ".env")

KNOWLEDGE_DIR = REPO_ROOT / "knowledge" / "policy"
CASES_DIR = REPO_ROOT / "cases"
FIXTURES_DIR = CASES_DIR / "fixtures"
LABELS_DIR = CASES_DIR / "labels"
EVALS_DIR = REPO_ROOT / "evals"
SUBMITTED_DIR = Path(os.environ.get("WINDMILL_SUBMITTED_DIR", REPO_ROOT / "submitted"))

# Model pins (see .env.example). Agent model is the Luna class; judge is the Sol class.
AGENT_MODEL = os.environ.get("AGENT_MODEL", "gpt-6-luna")
JUDGE_MODEL = os.environ.get("JUDGE_MODEL", "gpt-6.1-sol")

EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "text-embedding-3-small")

# Identifier for a run of the agent; submissions and eval results are namespaced by it
# so before/after runs never overwrite each other.
RUN_ID = os.environ.get("WINDMILL_RUN_ID", "local")
