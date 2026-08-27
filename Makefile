.PHONY: help install dev-install lint format test clean docker-up docker-down run-pipeline run-live run-full run-stream profile-data

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
	@echo "  airbyte-up      Start lightweight Airbyte Web UI & Server via Docker"
	@echo "  airbyte-down    Stop standalone Airbyte containers"
	@echo "  airbyte-sync    Run Airbyte connection and ELT replication via code"
	@echo "  fetch-historical Download and cache 5,800+ historical enriched Netflix titles"
	@echo "  prepare-powerbi Prepare, validate, and verify all 5 Power BI sources"
	@echo "  run-live        Execute live 2026/2025 web scraping & enrichment pipeline"
	@echo "  run-full        Execute full historical + 2026 live ingestion pipeline"
	@echo "  run-stream      Start real-time continuous streaming ingestion daemon"
	@echo "  profile-data    Run statistical catalog profiling and data quality validation"
	@echo "  run-pipeline    Default pipeline execution (Live mode)"
	@echo "  clean           Remove temporary caches and build artifacts"

airbyte-up:
	docker compose -f docker/docker-compose.airbyte.yml up -d

airbyte-down:
	docker compose -f docker/docker-compose.airbyte.yml down

airbyte-sync:
	$(PYTHON) scripts/run_airbyte_connection.py --sync-now

prepare-powerbi:
	$(PYTHON) scripts/prepare_powerbi_sources.py

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
	pytest tests/ -v

docker-up:
	docker compose up -d

docker-down:
	docker compose down

run-live:
	$(PYTHON) -m src.pipeline --mode live --years 2026,2025 --limit 50

run-full:
	$(PYTHON) -m src.pipeline --mode full --include-historical --years 2026,2025

run-stream:
	$(PYTHON) -m src.pipeline --mode stream --years 2026 --stream-interval 60

profile-data:
	$(PYTHON) -m src.pipeline --mode live --limit 50 --dry-run

run-pipeline: run-live

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache .coverage htmlcov .mypy_cache
