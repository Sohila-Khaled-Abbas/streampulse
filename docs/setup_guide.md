# StreamPulse: Complete Setup & Deployment Guide

This guide provides end-to-end instructions for configuring your local development environment, provisioning API access, initializing the PostgreSQL database, executing the ELT pipeline, and connecting Power BI.

---

## 1. Prerequisites

Ensure you have the following software installed:
- **Python**: Version 3.10 or higher
- **Docker & Docker Compose**: Docker Desktop (v20.10+) or Docker Engine
- **Git**: Version 2.30+
- **Power BI Desktop**: (Optional, for dashboard development and DirectQuery)

---

## 2. API Key Provisioning

StreamPulse integrates two external APIs:

1. **RapidAPI (Netflix UnoGS API)**:
   - Sign up at [RapidAPI](https://rapidapi.com).
   - Subscribe to the [UnoGS (uNoGS)](https://rapidapi.com/unogs/api/unogsng) or Netflix Catalog API endpoint.
   - Note your `X-RapidAPI-Key` and `X-RapidAPI-Host`.

2. **The Movie Database (TMDb)**:
   - Create a free account at [themoviedb.org](https://www.themoviedb.org/).
   - Navigate to **Settings > API** to generate your API Key (v3 auth) or API Read Access Token (v4 auth).

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

3. Open `.env` in your editor and configure the variables:
   ```env
   RAPIDAPI_KEY=your_actual_rapidapi_key
   TMDB_API_KEY=your_actual_tmdb_key
   DB_USER=postgres
   DB_PASSWORD=postgres
   DB_NAME=streampulse
   DB_HOST=localhost
   DB_PORT=5432
   ```

---

## 4. Virtual Environment & Dependencies

```bash
# Create virtual environment
python -m venv .venv

# Activate on Windows PowerShell
.venv\Scripts\Activate.ps1

# Activate on Linux/macOS
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
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

### 2. Standalone Airbyte UI & Server (Optional)
```bash
make airbyte-up
# Or: docker compose -f docker/docker-compose.airbyte.yml up -d
```
- **Airbyte Web UI**: `http://localhost:8000` (`airbyte` / `password`)

---

## 6. Running the Pipeline

Execute the end-to-end ELT pipeline:
```bash
# Run via python module
python -m src.pipeline

# Or using Makefile
make run-pipeline
```

The pipeline will:
1. Extract recent catalog changes from RapidAPI.
2. Ingest raw batches into `staging.stg_netflix_titles`.
3. Query TMDb for metadata, popularity, and ratings.
4. Execute fuzzy entity resolution matching Netflix entries against TMDb entities.
5. Populate `reporting.dim_titles`, `reporting.dim_genres`, and `reporting.fact_catalog_ratings`.

---

## 7. Power BI DirectQuery Configuration

1. Open **Power BI Desktop**.
2. Select **Get Data > PostgreSQL Database**.
3. Enter Connection details:
   - **Server**: `localhost:5432`
   - **Database**: `streampulse`
   - **Data Connectivity mode**: **DirectQuery**
4. Enter credentials (User: `postgres`, Password from `.env`).
5. Select the view: `reporting.vw_powerbi_catalog_pulse`.
6. Open or reload `dashboard/streampulse_analytics.pbix` to explore real-time visual metrics.
