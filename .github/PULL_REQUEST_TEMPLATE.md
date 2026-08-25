## Description
Provide a concise explanation of the changes introduced in this pull request and the rationale behind them.

## Type of Change
- [ ] 🐛 Bug fix (non-breaking change which fixes an issue)
- [ ] ✨ New feature (non-breaking change which adds functionality)
- [ ] 💥 Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] 📝 Documentation update
- [ ] ⚡ Performance optimization
- [ ] 🧹 Refactoring / Code style clean up
- [ ] 🧪 Test coverage improvement

## Pipeline Layer Impacted
- [ ] Ingestion & API Extractors (`src/extract/`)
- [ ] Entity Resolution & Transformations (`src/transform/`)
- [ ] Database Loaders & Data Models (`src/utils/db.py`, `sql/`)
- [ ] Power BI Dashboards (`dashboard/`)
- [ ] CI/CD & DevOps (`.github/`, `docker-compose.yml`)

## Testing & Verification
Describe how these changes were tested:
- [ ] Unit tests added / updated and passing (`pytest`)
- [ ] Static type check passing (`mypy src/`)
- [ ] Code formatting & linting clean (`ruff check .`)
- [ ] Manual end-to-end pipeline run verified against staging database

## Screenshots / Evidence (if applicable)
Add query results, execution logs, or dashboard visuals here.

## Checklist
- [ ] My code adheres to the project's coding style and guidelines.
- [ ] I have performed a self-review of my own code.
- [ ] I have commented my code, particularly in hard-to-understand areas.
- [ ] I have updated corresponding documentation in `docs/`.
