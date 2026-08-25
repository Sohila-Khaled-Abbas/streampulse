# Contributing to StreamPulse

Thank you for your interest in contributing to **StreamPulse**! We welcome contributions ranging from bug fixes, documentation improvements, new API extractors, transformation enhancements, to dashboard visuals.

---

## Code of Conduct
This project and everyone participating in it is governed by our [Code of Conduct](file:///d:/courses/Data%20Science/Data%20Engineering/Projects/streampulse/CODE_OF_CONDUCT.md). By participating, you are expected to uphold this standard.

---

## Development Workflow

### 1. Fork and Clone
```bash
git clone https://github.com/your-username/streampulse.git
cd streampulse
```

### 2. Environment Setup
Create and activate a virtual environment (Python 3.10+ recommended):
```bash
python -m venv .venv

# On Linux/macOS
source .venv/bin/activate

# On Windows (PowerShell)
.venv\Scripts\Activate.ps1
```

Install development dependencies:
```bash
pip install -r requirements.txt
pip install -e .[dev]
```

### 3. Local Infrastructure
Spin up the local PostgreSQL database using Docker Compose:
```bash
docker compose up -d
```

Copy the environment variable template:
```bash
cp .env.example .env
# Edit .env with your local credentials and API keys
```

---

## Coding Guidelines

- **Style**: Follow PEP 8 standards. We use `black` and `ruff` for formatting and linting.
  ```bash
  # Check formatting & linting
  ruff check .
  black --check src/ tests/
  ```
- **Type Annotations**: Use Python type hinting (`pydantic`, `typing`) across all new modules and verify with `mypy src/`.
- **Testing**: Write unit tests for new extractors, parsers, and fuzzy matching algorithms in `tests/`.
  ```bash
  pytest --cov=src
  ```
- **Documentation**: If your change alters data schemas, updates configurations, or introduces new features, update relevant markdown files in `docs/` and `README.md`.

---

## Git Workflow & Submitting PRs

1. **Branch Naming**: Use descriptive branch names:
   - `feat/add-imdb-extractor`
   - `fix/fuzzy-match-year-boundary`
   - `docs/update-architecture-diagram`
2. **Commit Messages**: Write clear, descriptive commit messages adhering to Conventional Commits:
   - `feat: implement Levenshtein distance fallback in entity resolution`
   - `fix: handle null release dates from TMDb API response`
   - `docs: update data dictionary for fact_ratings`
3. **Open a Pull Request**: Fill out the [Pull Request Template](file:///d:/courses/Data%20Science/Data%20Engineering/Projects/streampulse/.github/PULL_REQUEST_TEMPLATE.md) completely.
