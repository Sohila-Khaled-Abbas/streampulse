# ⚡ StreamPulse: Complete Setup & Deployment Guide

This guide provides end-to-end instructions for configuring your local development environment, running the **2026 live web scraping & ELT pipeline**, verifying data quality and statistical profiling outputs, and connecting real-time streaming dashboards in Power BI.

---

## 1. Prerequisites

Ensure you have the following software installed:
- **Python**: Version 3.10 or higher (Python 3.10, 3.11, 3.12, 3.14 supported)
- **Docker Desktop**: (v20.10+) for containerized PostgreSQL and pgAdmin
- **Git**: Version 2.30+
- **Power BI Desktop**: (Optional, for dashboard development and DirectQuery)

---

## 2. API Key Provisioning (Zero-Cost & Optional APIs)

StreamPulse features a **zero-cost hybrid architecture** requiring **no paid subscriptions**:

1. **Zero-Cost Web Scrapers (Built-In & Default)**:
   - Built-in multi-source scraper in `src/extract/netflix_scraper.py` extracting 2026 releases (`List of Netflix original films (since 2026)`), 2025/2024 films, active TV programming, and real-time *What's on Netflix* streaming RSS feeds.
   - Built-in `WebEnricher` in `src/extract/enricher_scraper.py` extracting Wikipedia infoboxes (directors, cast, budget, synopsis) and calculating calibrated rating metrics.

2. **The Movie Database (TMDb) Rating API (Free & Optional)**:
   - Create a free account at [themoviedb.org](https://www.themoviedb.org/).
   - Navigate to **Settings > API** to generate your API Key (v3 auth).

3. **RapidAPI Netflix UnoGS API (Optional)**:
   - If you have an active RapidAPI subscription, configure `RAPIDAPI_KEY` in `.env`.

---

## 3. Environment Configuration

1. Clone the repository and navigate into the root directory:
   ```bash
   git clone https://github.com/Sohila-Khaled-Abbas/streampulse.git
   cd streampulse
   ```

2. Create your `.env` file from `.env.example`:
   ```bash
   cp .env.example .env
   ```

3. Configure your credentials in `.env`:
   ```env
   RAPIDAPI_KEY=your_actual_rapidapi_key_or_leave_empty
   TMDB_API_KEY=your_actual_tmdb_key_or_leave_empty
   DB_USER=postgres
   DB_PASSWORD=postgres
   DB_NAME=streampulse
   DB_HOST=localhost
   DB_PORT=5432
   ```

---

## 4. Virtual Environment & Dependencies

```powershell
# Create virtual environment
python -m venv .venv

# Activate on Windows PowerShell
.venv\Scripts\Activate.ps1

# Activate on Linux/macOS
source .venv/bin/activate

# Install production dependencies
pip install -r requirements.txt

# (Optional) Install development dependencies
pip install -e .[dev]
```

---

## 5. Starting Docker Services

### 1. PostgreSQL & pgAdmin
```bash
make docker-up
# Or: docker compose up -d
```
- **PostgreSQL**: `localhost:5432` (`streampulse`)
- **pgAdmin 4**: `http://localhost:5050` (`admin@admin.com` / `admin`)

The initialization scripts in `sql/` execute automatically on first start:
- `sql/00_init.sql` (Creates `staging` and `reporting` schemas)
- `sql/01_staging.sql` (Creates staging landing tables)
- `sql/02_reporting.sql` (Creates dimensional star schema & DirectQuery view)

---

## 6. Running the 2026 Pipeline: Step-by-Step Execution

StreamPulse supports 4 flexible execution modes:

### Mode A: Live 2026 Catalog Ingestion (Recommended)
Scrapes confirmed 2026 releases, active TV series, and live streaming RSS deltas:
```powershell
python -m src.pipeline --mode live --years 2026,2025 --limit 50
# Or using Makefile:
make run-live
```

### Mode B: Full Historical Baseline + 2026 Live Ingestion
Loads 5,800+ historical Kaggle titles merged with 2026 live scraped additions:
```powershell
python -m src.pipeline --mode full --include-historical --years 2026,2025
# Or using Makefile:
make run-full
```

### Mode C: Real-Time Streaming Daemon Mode
Runs a continuous live polling loop (every 60 seconds) streaming new drops directly into PostgreSQL:
```powershell
python -m src.pipeline --mode stream --years 2026 --stream-interval 60
# Or using Makefile:
make run-stream
```

### Mode D: Data Profiling & Quality Validation Run
Runs statistical profiling and exports validation reports without modifying the database:
```powershell
python -m src.pipeline --mode live --limit 50 --dry-run
# Or using Makefile:
make profile-data
```

---

## 7. Pipeline Output & Data Validation Logs

When you execute `python -m src.pipeline --mode live --years 2026 --limit 30`, you will see structured step-by-step terminal outputs:

```text
================================================================================
[PIPELINE] STREAMPULSE ELT RUN: [MODE=LIVE]
Target Years: [2026] | Scrape Limit: 30 | Historical: False
================================================================================
--- STEP 1/5: INGESTION & LIVE 2026 WEB SCRAPING ---
Scraping live 2026 Netflix originals, programming, and RSS feeds...
[OK] Scraped 30 live 2025/2026 titles.
Total raw titles collected for processing: 30

--- STEP 2/5: DATA CLEANING & NORMALIZATION ---
[OK] Standardized and deduplicated 30 title records.

--- STEP 3/5: ENTITY RESOLUTION & LIVE ENRICHMENT ---
[OK] Enriched and resolved 30 titles.

--- STEP 4/5: DATA QUALITY VALIDATION & PROFILING ---
================================================================================
[REPORT] STREAMPULSE DATA QUALITY & CATALOG PROFILING REPORT
================================================================================
Validation Status: [PASSED] | Quality Score: 100.0% | Total Processed: 30 titles
--------------------------------------------------------------------------------
Catalog Eras: 2026 Live: 30 | 2024-2025 Modern: 0 | Historical Archive: 0
Media Distribution: Movies: 30 | Series/Shows: 0
Audience Metrics: Mean Rating: 6.61 / 10 | Mean Popularity: 8.81 | Mean Runtime: 110.0 mins
Entity Resolution: High Conf (>=90%): 30 | Medium (75-89%): 0
Top Genres: Drama (8), Comedy (7), Romance (3), Crime Thriller (2), Crime Drama (2)
================================================================================

--- STEP 5/5: WAREHOUSE LOADING & MASTER EXPORT ---
[HIGHLIGHTS] Live 2026 Catalog Highlights Preview:
   1. [2026-01-09] People We Meet on Vacation (MOVIE) | Rating: 6.98/10 | Pop: 9.52 | Source: wikipedia_2026_films
   2. [2026-01-16] The Rip (MOVIE) | Rating: 7.09/10 | Pop: 22.20 | Source: wikipedia_2026_films
   3. [2026-01-22] Cosmic Princess Kaguya! (MOVIE) | Rating: 8.3/10 | Pop: 11.47 | Source: wikipedia_2026_films
   4. [2026-01-22] From the Ashes: The Pit (MOVIE) | Rating: 4.22/10 | Pop: 3.92 | Source: wikipedia_2026_films
   5. [2026-01-23] The Big Fake (MOVIE) | Rating: 6.62/10 | Pop: 5.25 | Source: wikipedia_2026_films
================================================================================
[SUCCESS] STREAMPULSE ELT PIPELINE COMPLETED SUCCESSFULLY
Processed: 30 titles | Quality: 100.0% | Export: data\processed\netflix_catalog_enriched_master.csv
================================================================================
```

---

## 8. Analytics Engineering & Data Quality Artifacts

Every pipeline execution generates automated columnar Parquet and data quality artifacts in `data/processed/`:

1. **`data/processed/powerbi_reporting_pulse.parquet`**:
   - High-performance columnar Parquet file pre-modeled for Power BI Star-Schema analytics, containing `catalog_era`, `rating_tier`, `days_to_streaming`, and `is_trending`.

2. **`data/processed/netflix_catalog_enriched_master.parquet`**:
   - Master Snappy-compressed Parquet dataset with strictly enforced schema and typing for data lakehouse ingestion.

3. **`data/processed/netflix_catalog_enriched_master.csv`**:
   - Master conformed catalog containing all enriched 2026 live releases, TMDb IDs, audience ratings, vote counts, popularity scores, streaming velocity (`days_to_streaming`), and source tags.

4. **`data/processed/live_2026_pulse.json`**:
   - JSON structured feed of 2026 titles ready for web dashboards or API endpoints.

5. **`data/processed/data_profiling_report.json`**:
   - Machine-readable audit file containing:
     - Field-by-field completeness percentages (`missing_count`, `completeness_pct`).
     - Validation status (`PASSED` / `WARNING`).
     - Quality score ($0-100\%$).
     - Catalog era breakdown (2026 Live vs Modern vs Historical).
     - Rating tier and confidence distribution.

---

## 9. Automated Testing Suite

Execute unit and integration tests across scrapers, entity resolution, and warehouse loaders:
```powershell
.venv\Scripts\python.exe -m pytest tests/ -v
```

---

## 10. Power BI DirectQuery Configuration

1. Open **Power BI Desktop**.
2. Select **Get Data > PostgreSQL Database**.
3. Enter connection parameters:
   - **Server**: `localhost:5432` (or your Neon/Supabase cloud host)
   - **Database**: `streampulse`
   - **Data Connectivity Mode**: **DirectQuery**
4. Enter credentials (User: `postgres`, Password from `.env`).
5. Select the view: `reporting.vw_powerbi_catalog_pulse`.
6. Use the `catalog_era` filter to slice by **"2026 Live Releases"** or **"2024-2025 Modern"**.
