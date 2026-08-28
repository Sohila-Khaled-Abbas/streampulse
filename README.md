<div align="center">

# ⚡ StreamPulse

### *Live 2026 Streaming Intelligence, Kimball Galaxy Lakehouse & Power BI Analytics Platform*

[![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.14-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15.0-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Airbyte](https://img.shields.io/badge/Airbyte-0.50.36_ELT-615EFF?style=for-the-badge&logo=airbyte&logoColor=white)](https://airbyte.com/)
[![Docker](https://img.shields.io/badge/Docker-Enabled-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)
[![Power BI](https://img.shields.io/badge/Power_BI-DirectQuery-F2C811?style=for-the-badge&logo=powerbi&logoColor=black)](https://powerbi.microsoft.com/)
[![CI Pipeline](https://img.shields.io/badge/CI-GitHub_Actions-2088FF?style=for-the-badge&logo=githubactions&logoColor=white)](https://github.com/Sohila-Khaled-Abbas/streampulse/actions)
[![Code Style: Black](https://img.shields.io/badge/code%20style-black-000000.svg?style=for-the-badge)](https://github.com/psf/black)
[![Ruff](https://img.shields.io/badge/linter-ruff-261230?style=for-the-badge&logo=ruff&logoColor=white)](https://github.com/astral-sh/ruff)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg?style=for-the-badge)](LICENSE)

<p align="center">
  <b>An enterprise-grade, end-to-end Data Engineering &amp; Analytics Engineering platform extracting live 2026 Netflix catalog releases, web scraping real-time streaming drops, enriching entities with audience sentiment and TMDb ratings via fuzzy string resolution, orchestrating daily replication via Airbyte into a PostgreSQL Kimball Galaxy Star Schema, and streaming analytics live to Power BI DirectQuery.</b>
</p>

[📊 Power BI Masterclass](docs/powerbi_analytics_engineering_guide.md) •
[🔄 Airbyte ELT Guide](docs/airbyte_elt_powerbi_guide.md) •
[📐 Architecture Deep Dive](docs/architecture.md) •
[📖 Data Dictionary](docs/data_dictionary.md) •
[🚀 Setup Guide](docs/setup_guide.md) •
[🎯 Live Implementation Guide](docs/live_project_implementation_guide.md)

---

</div>

## 🖼️ High-Resolution Architecture & Data Model

<div align="center">
  <h3>System Architecture Diagram</h3>
  <img src="docs/assets/streampulse_architecture.svg" alt="StreamPulse 2026 Enterprise Architecture" width="100%" />
  <p><i>Editable Draw.io XML format available at <a href="docs/assets/streampulse_drawio_diagram.xml"><code>docs/assets/streampulse_drawio_diagram.xml</code></a></i></p>

  <br/>

  <h3>Kimball Galaxy Star Schema &amp; ERD</h3>
  <img src="docs/assets/streampulse_data_model.svg" alt="StreamPulse Kimball Galaxy Star Schema ERD" width="100%" />
</div>

---

## 📖 Table of Contents

- [Executive Summary](#-executive-summary)
- [System Architecture](#-system-architecture)
- [Key Features & Engineering Highlights](#-key-features--engineering-highlights)
- [Multi-Source Data Ingestion & Power Query Training](#-multi-source-data-ingestion--power-query-training)
- [Kimball Galaxy Data Model](#-kimball-galaxy-data-model)
- [Airbyte Automated Daily ELT Pipeline](#-airbyte-automated-daily-elt-pipeline)
- [Power BI Analytics Engineering & DAX](#-power-bi-analytics-engineering--dax)
- [Quick Start Guide](#-quick-start-guide)
- [Quality Assurance & Testing](#-quality-assurance--testing)
- [License](#-license)

---

## 🚀 Executive Summary

Streaming entertainment platforms release hundreds of original titles every month. **StreamPulse** provides streaming media intelligence through a resilient, automated ELT pipeline that:

1. **Extracts Live 2026 Releases**: Scrapes confirmed 2026 Netflix original films (*List of Netflix original films (since 2026)*), 2025/2024 releases, active multi-season TV programming, and real-time *What's on Netflix* live streaming RSS feeds.
2. **Replicates via Airbyte**: Ingests multi-source payloads (REST APIs, CSV flat files, wide Parquet lakehouse metrics) into an isolated PostgreSQL `staging` landing zone.
3. **Enriches & Resolves Entities**: Runs RapidFuzz Levenshtein string similarity and release-year windowing heuristics to match entities against TMDb, extracting Wikipedia infobox crew, budget, and audience ratings.
4. **Validates & Profiles Data**: Executes an automated statistical profiling engine computing field completeness, quality scores ($0-100\%$), era breakdowns, and rating tiers.
5. **Models Dimensional Warehouse**: Transforms cleaned data into a Kimball Galaxy Model (`dim_titles`, `dim_genres`, `dim_crew`, `dim_date`, `fact_catalog_ratings`, `fact_streaming_performance`).
6. **Surfaces Real-Time Analytics**: Powers interactive Power BI dashboards via DirectQuery for zero-lag visibility and automated 5-minute canvas refresh.

---

## 🧩 Multi-Source Data Ingestion & Power Query Training

StreamPulse ships with **5 distinct unmerged raw sources** containing deliberate real-world data quality issues for Power BI Power Query (M Language) training:

| Source # | Source Name | Storage Format | Location / Path | Real-World Cleaning Challenges |
| :--- | :--- | :--- | :--- | :--- |
| **Source 1** | `stg_netflix_titles` | PostgreSQL Table | `localhost:5432` / `staging.stg_netflix_titles` | Mixed date formats (`"January 15, 2026"`, `"15/01/2026"`), non-breaking spaces (`\xa0`), uppercase titles, JSON strings |
| **Source 2** | `Raw_Historical_Archive` | CSV Flat File | `data/raw/netflix_enriched_historical.csv` | **5,800+ historical titles (1945–2024)**, genre string arrays (`"['drama', 'crime']"`), floating-point IMDb/TMDb scores |
| **Source 3** | `Raw_IMDb_Ratings` | CSV Flat File | `data/raw/imdb_external_ratings.csv` | Shorthand vote counts (`"1.4M"`, `"850K"`), dirty ID prefixes (`"tt8001000"`, `"IMDB_8001000"`), duplicate snapshot rows |
| **Source 4** | `Raw_Viewership_Parquet` | Wide Parquet Lakehouse | `data/raw/streaming_viewership_wide.parquet` | Unpivoted wide monthly columns (`Hours_2026_01`), country variations (`"USA"`, `"US"`, `"u.s.a."`), sentinel values (`-999.0`) |
| **Source 5** | `Raw_Budget_JSON` | JSON Feed | `data/raw/boxoffice_budget_feed.json` | Dirty currency strings (`"$150M"`, `"€45 million"`), pipe-delimited genres (`"Action\|Sci-Fi"`), nested JSON records |

> 📘 *See the full step-by-step M Language cleaning recipes in [`docs/powerbi_analytics_engineering_guide.md`](docs/powerbi_analytics_engineering_guide.md).*

---

## 🏛️ Kimball Galaxy Data Model

The PostgreSQL reporting layer and Parquet Lakehouse (`data/processed/lakehouse/*.parquet`) follow the Kimball Galaxy dimensional modeling architecture:

```
[Dim_Titles] 1 <-------- * [Fact_Catalog_Ratings]        (Active, 1-to-Many, Single Direction)
[Dim_Titles] 1 <-------- * [Fact_Streaming_Performance]  (Active, 1-to-Many, Single Direction)
[Dim_Date]   1 <-------- * [Fact_Catalog_Ratings]        (Active, 1-to-Many, Single Direction)
[Dim_Date]   1 <-------- * [Fact_Streaming_Performance]  (Active, 1-to-Many, Single Direction)
[Dim_Date]   1 <-------- * [Dim_Titles] (Release_Date)   (Inactive, 1-to-Many, for USERELATIONSHIP)
[Dim_Genres] 1 <-------- * [Bridge_Title_Genre]          (Active, 1-to-Many)
[Dim_Titles] 1 <-------- * [Bridge_Title_Genre]          (Active, 1-to-Many, Both Direction)
```

---

## 🔄 Airbyte Automated Daily ELT Pipeline & Code Execution

Airbyte (v0.50.36) orchestrates daily automated replication with full programmatic Python control:

1. **Airbyte Web UI**: Accessible at [http://localhost:8000](http://localhost:8000) (Username: `airbyte`, Password: `password`).
2. **Programmatic Python API Client**: Use `AirbyteClient` in [`src/load/airbyte_client.py`](src/load/airbyte_client.py) to check stack health, provision workspaces, File sources, PostgreSQL destinations, and trigger sync jobs directly from code.
3. **CLI Connection Runner**: Execute replication anytime via CLI:
   ```bash
   python scripts/run_airbyte_connection.py --sync-now
   # or: make airbyte-sync
   ```
4. **Replication Schedule**: Configured on a **24-hour Cron** (`0 6 * * *`) replicating newly scraped catalog landing files into PostgreSQL `staging.stg_netflix_titles`.
5. **Sync Mode**: `Incremental | Append + Deduped` using `netflix_id` as primary key and `extracted_at` as cursor.

---

## 📊 Power BI Analytics Engineering & DAX

The project includes **25+ Enterprise DAX Measures** across 6 business analytics domains:

1. **Bayesian Audience Index**:
   $$\text{Bayesian Rating} = \frac{v}{v + m} \cdot R + \frac{m}{v + m} \cdot C$$
   *(where $v$ = title votes, $m$ = 500 minimum threshold, $R$ = title average, $C$ = catalog average).*
2. **Budget ROI & Cost Per View Hour**:
   $$\text{Effective Cost Per View Hour} = \frac{\text{Budget USD}}{\text{Total Global View Hours} \times 1,000,000}$$
3. **Streaming Velocity**: Measures the lag days between theatrical debut and SVOD drop.
4. **Time Intelligence**: Calculates YTD View Hours, QoQ Growth %, and Rolling 28-Day Viewership Momentum.
5. **Pareto 80/20 Concentration**: Dynamically tags the top 20% of catalog titles generating 80% of total viewership hours.
6. **Inactive & Virtual Relationships**: Implements `USERELATIONSHIP` on release vs drop dates and `TREATAS` for dynamic cross-genre affinity.

---

## ⚡ Quick Start Guide

### 1. Clone & Setup Virtual Environment
```powershell
git clone https://github.com/Sohila-Khaled-Abbas/streampulse.git
cd streampulse

python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .
```

### 2. Start PostgreSQL & Airbyte Docker Containers
```powershell
# Start PostgreSQL & pgAdmin
docker compose up -d

# Start Airbyte 0.50.36 ELT Stack
docker compose -f docker/docker-compose.airbyte.yml up -d
```

### 3. Prepare All 5 Power BI Sources & Run Airbyte Sync
```powershell
# Prepare, validate, and conform all 5 Power BI sources (including 5,800+ historical archive)
python scripts/prepare_powerbi_sources.py

# Programmatically trigger the Airbyte replication connection via code
python scripts/run_airbyte_connection.py --sync-now
```

### 4. Run the Live 2026 Pipeline
```powershell
# Execute live scraper, entity resolution, profiler, and warehouse loader
python src/pipeline.py --mode live --limit 50
```

---

## 🧪 Quality Assurance & Testing

Run the full pytest suite with code coverage:

```powershell
pytest -v
```

```text
============================= test session starts =============================
tests/test_airbyte_client.py ......... PASSED
tests/test_db.py ..................... PASSED
tests/test_extract.py ................ PASSED
tests/test_powerbi_sources.py ........ PASSED
tests/test_scraper_2026.py ........... PASSED
tests/test_transform.py .............. PASSED
tests/test_warehouse_loader.py ....... PASSED
============================= 29 passed in 27.31s =============================
```

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.
