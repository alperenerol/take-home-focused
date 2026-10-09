# Mortgage Evidence & Policy Assessment Agent - common tasks.
# Quickstart: cp .env.example .env (fill keys) -> make setup -> make test

PYTHON ?= python3.12
VENV := .venv
PY := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

.PHONY: setup test generate-cases verify-labels run upload-dataset eval clean

setup: ## Create the virtualenv and install pinned dependencies
	$(PYTHON) -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt

test: ## Run unit tests
	$(PY) -m pytest -q

generate-cases: ## Generate synthetic case fixtures (P1)
	$(PY) cases/generate.py

verify-labels: ## Re-derive and check case labels against policy rules
	$(PY) cases/verify_labels.py

run: ## Assess one case: make run CASE=case-001 RUN=dev-smoke
	$(PY) -m src.cli --case $(CASE) --run-id $(or $(RUN),local)

upload-dataset: ## Upload the eval dataset to LangSmith (P4)
	$(PY) -m evals.upload_dataset

eval: ## Run the evaluation: make eval RUN_ID=baseline-v0 [CASES=case-001,case-002]
	$(PY) -m evals.run_eval --run-id $(RUN_ID) $(if $(CASES),--cases $(CASES),)

clean: ## Remove caches
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	rm -rf .pytest_cache
