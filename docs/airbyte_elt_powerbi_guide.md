# 🔄 Airbyte ELT & Native 2026 Engine to Power BI DirectQuery Guide

This guide walks you through using either **Airbyte** or the **Native StreamPulse 2026 Web Scraping Engine** as the Extract & Load (EL) stage, loading raw streaming catalog data into PostgreSQL, transforming it into a dimensional model, and serving real-time dashboards in **Power BI via DirectQuery**.

---

## 🏗️ ELT Architectural Flow

```mermaid
flowchart LR
    subgraph Extract["1. Extract & Scrape"]
        A1["Wikipedia 2026 Netflix Originals"]
        A2["What's on Netflix Live RSS Feed"]
        A3["TMDb Metadata & Ratings API"]
        A4["Kaggle 5,800+ Historical Benchmark"]
    end

    subgraph Load["2. Load & Validate"]
        B["StreamPulse / Airbyte Loader"]
        C[("PostgreSQL: staging schema")]
        P["Data Quality & Profiling Engine"]
    end

    subgraph Transform["3. Transform & Model"]
        D["Entity Resolution (RapidFuzz >= 85%)"]
        E["Conformed Star Schema Modeler"]
        F[("PostgreSQL: reporting schema")]
    end

    subgraph Visualize["4. Real-Time BI"]
        G["reporting.vw_powerbi_catalog_pulse"]
        H["Power BI Desktop (DirectQuery)"]
    end

    A1 & A2 & A3 & A4 --> B
    B --> C
    B --> P
    C --> D
    D --> E
    E --> F
    F --> G
    G -->|DirectQuery (Zero Lag)| H
```

---

## 🚀 Step 1: Starting Your Infrastructure

Start PostgreSQL and pgAdmin via Docker Compose:

```powershell
docker compose up -d
```

- **PostgreSQL Warehouse**: `localhost:5432` | User: `postgres` | Password: `postgres` | Database: `streampulse`
- **pgAdmin Web UI**: `http://localhost:5050` (Email: `admin@admin.com`, Password: `admin`)

---

## 🚀 Step 2: Ingestion & ELT Options

### Option A: Native 2026 StreamPulse Engine (Recommended — Zero Cost & Live 2026 Data)
The native Python ELT engine automatically scrapes 2026 Wikipedia originals, ongoing TV series, and live streaming RSS feeds:

```powershell
# Run Live 2026 Pipeline
python -m src.pipeline --mode live --years 2026,2025 --limit 50

# Run with Real-Time Streaming Daemon (Continuous)
python -m src.pipeline --mode stream --years 2026 --stream-interval 60
```

### Option B: Airbyte Standalone Ingestion
If using Airbyte for enterprise connectors:
```powershell
# Start Airbyte containers
docker compose -f docker/docker-compose.airbyte.yml up -d
```
- Access Airbyte at `http://localhost:8000` (`airbyte` / `password`).
- Set Source: File / Custom HTTP Connector.
- Set Destination: PostgreSQL (`staging` schema).

---

## 📊 Step 3: Power BI DirectQuery Setup

1. Open **Power BI Desktop**.
2. Select **Get Data $\to$ PostgreSQL Database**.
3. Connection Parameters:
   - **Server**: `localhost:5432` (or your cloud host)
   - **Database**: `streampulse`
   - **Data Connectivity Mode**: **DirectQuery**
4. Choose View: `reporting.vw_powerbi_catalog_pulse`.

### Recommended DAX Measures
```dax
// 1. Average Rating
AvgAudienceScore = AVERAGE(vw_powerbi_catalog_pulse[vote_average])

// 2. Total Streaming Titles
TotalTitles = COUNTROWS(vw_powerbi_catalog_pulse)

// 3. 2026 Live Catalog Additions
Live2026Count = CALCULATE(COUNTROWS(vw_powerbi_catalog_pulse), vw_powerbi_catalog_pulse[release_year] = 2026)

// 4. Average Days to Streaming
AvgDaysToStream = AVERAGE(vw_powerbi_catalog_pulse[days_to_streaming])

// 5. Top Rated Ratio (>= 8.0)
TopRatedPct = 
DIVIDE(
    CALCULATE(COUNTROWS(vw_powerbi_catalog_pulse), vw_powerbi_catalog_pulse[vote_average] >= 8.0),
    COUNTROWS(vw_powerbi_catalog_pulse),
    0
)
```

---

## 🔍 Step 4: Data Quality & Profiling Audit

Verify that the pipeline produced clean, complete data:
```powershell
# Inspect latest data profiling JSON
cat data/processed/data_profiling_report.json
```
- Quality score must be $\ge 90\%$.
- Validation status must be `PASSED`.
