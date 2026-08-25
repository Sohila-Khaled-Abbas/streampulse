.PHONY: help install dev-install lint format test clean docker-up docker-down run-pipeline

PYTHON ?= python
PIP ?= pip

help:
	@echo "StreamPulse CLI Automation commands:"
	@echo "  install         Install production dependencies"
	@echo "  dev-install     Install dependencies including testing/linting tools"
	@echo "  lint            Run ruff & mypy checks"
	@echo "  format          Run black & ruff autofix"
	@echo "  test            Run pytest suite with coverage"
	@echo "  docker-up       Start PostgreSQL and pgAdmin via Docker Compose"
	@echo "  docker-down     Stop and tear down Docker containers"
	@echo "  airbyte-install Install and launch Airbyte locally in Docker"
	@echo "  airbyte-status  Check local Airbyte cluster health"
	@echo "  airbyte-creds   View local Airbyte login credentials"
	@echo "  fetch-historical Download and cache 5,800+ historical enriched Netflix titles"
	@echo "  run-pipeline    Execute the full end-to-end ELT pipeline"
	@echo "  clean           Remove temporary caches and build artifacts"

airbyte-install:
	.\abctl-v0.30.4-windows-amd64\abctl.exe local install --low-resource-mode --no-browser

airbyte-status:
	.\abctl-v0.30.4-windows-amd64\abctl.exe local status

airbyte-creds:
	.\abctl-v0.30.4-windows-amd64\abctl.exe local credentials

fetch-historical:
	$(PYTHON) scripts/fetch_historical_dataset.py

install:
	$(PIP) install -r requirements.txt

dev-install:
	$(PIP) install -e .[dev]

lint:
	ruff check .
	mypy src/

format:
	black src/ tests/
	ruff check --fix .

test:
	pytest

docker-up:
	docker compose up -d

docker-down:
	docker compose down

run-pipeline:
	$(PYTHON) -m src.pipeline

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache .coverage htmlcov .mypy_cache
