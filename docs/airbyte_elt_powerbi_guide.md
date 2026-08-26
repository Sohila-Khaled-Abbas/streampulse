# 🔄 Airbyte ELT to Power BI DirectQuery Guide

This guide walks you through using **Airbyte** as the Extract & Load (EL) engine in StreamPulse, loading raw streaming catalog data into PostgreSQL, transforming it into a dimensional model, and serving real-time dashboards in **Power BI via DirectQuery**.

---

## 🏗️ ELT Architectural Flow

```mermaid
flowchart LR
    subgraph Extract["1. Extract"]
        A1["Netflix Catalog (API / Scraped Feed)"]
        A2["TMDb Metadata & Ratings API"]
        A3["Kaggle 5,800+ Historical Dataset"]
    end

    subgraph Load["2. Load (Airbyte)"]
        B["Airbyte Ingestion Engine"]
        C[("PostgreSQL: staging schema")]
    end

    subgraph Transform["3. Transform"]
        D["SQL DDL & Views (sql/02_reporting.sql)"]
        E["Fuzzy Entity Matching (RapidFuzz)"]
        F[("PostgreSQL: reporting schema (Star Schema)")]
    end

    subgraph Visualize["4. Visualize"]
        G["vw_powerbi_catalog_pulse"]
        H["Power BI Desktop (DirectQuery)"]
    end

    A1 & A2 & A3 -->|Airbyte Source| B
    B -->|Airbyte Destination| C
    C --> D & E
    D & E --> F
    F --> G
    G -->|DirectQuery (Zero Lag)| H
```

---

## 🚀 Step 1: Starting Your Infrastructure

Your local data warehouse (PostgreSQL) and database GUI (pgAdmin) are running via Docker Compose:

```powershell
docker compose up -d
```

- **PostgreSQL Warehouse**: `localhost:5432` | User: `postgres` | Password: `postgres` | Database: `streampulse`
- **pgAdmin Web UI**: `http://localhost:5050` (Email: `admin@streampulse.local`, Password: `admin`)

---

## 🚀 Step 2: Ingestion & ELT Options

You have two powerful approaches for the **Extract & Load (EL)** stage:

### Option A: Native StreamPulse ELT Engine (Recommended — Zero RAM Overhead)
Because Airbyte has deprecated standalone Docker Compose and requires a heavy nested Kubernetes cluster, StreamPulse includes a built-in, lightweight Python ELT orchestrator that handles everything in seconds:

```powershell
# 1. Fetch & Cache Historical Benchmark Dataset (5,800+ titles)
python scripts/fetch_historical_dataset.py

# 2. Run the Full Ingestion, Web Scraping, TMDb Enrichment & Entity Resolution
python -m src.pipeline
```

This immediately parses, enriches, and writes clean records into `data/processed/netflix_catalog_enriched_master.csv` and loads into PostgreSQL.

---

### Option B: Airbyte Cloud (Free Tier)
For a complete Airbyte Web UI experience without local container bloat:
1. Sign up for a free account at [**cloud.airbyte.com**](https://cloud.airbyte.com).
2. Configure **Source**: `File (CSV)` with URL `https://raw.githubusercontent.com/amirtds/kaggle-netflix-tv-shows-and-movies/main/titles.csv`.
3. Configure **Destination**: Connect to your cloud PostgreSQL database (Neon / Supabase) or local database via ngrok tunnel.
4. Run the sync.

---

## 📥 Step 3: Configure Database Warehouse Destination (PostgreSQL)

Whether ingesting via StreamPulse Native ELT or Airbyte:

1. **Host**: `localhost` *(or `host.docker.internal` from inside Docker)*
2. **Port**: `5432`
3. **Database Name**: `streampulse`
4. **Default Schema**: `staging`
5. **User**: `postgres`
6. **Password**: `postgres`
7. **SSL Mode**: `disable`

pgAdmin is available to inspect tables directly at:
🌐 **`http://localhost:5050`** (Login: `admin@admin.com`, Password: `admin`)

---

### 2. Set Up Airbyte Source

You can choose one of the following Airbyte Sources:

#### Source Type 1: File / CSV (5,800+ Historical Dataset)
- **Source**: `File (CSV)`
- **URL**: `https://raw.githubusercontent.com/amirtds/kaggle-netflix-tv-shows-and-movies/main/titles.csv`
- **Storage Provider**: `HTTPS`
- **Format**: `CSV`

#### Source Type 2: Custom HTTP API (TMDb / RapidAPI)
- **Source**: `HTTP Request / Custom Connector`
- **URL**: `https://api.themoviedb.org/3/search/movie`
- **Authentication**: Bearer Token or Query Param `api_key=740540a48bb63145d15718d011f7bc57`

---

### 3. Create the Airbyte Connection & Sync
1. Go to **Connections** $\to$ **New connection**.
2. Select your **Source** and **Postgres Destination**.
3. **Replication Frequency**: Manual or Every 24 hours.
4. **Sync Mode**: `Full Refresh | Overwrite` or `Incremental | Append`.
5. Click **Set up connection** and then **Sync now**.

Airbyte will extract records from your source and load them directly into the PostgreSQL `staging` schema.

---

## ⚙️ Step 4: Run the Transformation (T)

Once raw data lands in `staging`, execute the transformation and entity resolution logic:

```powershell
# Executes entity resolution, unnesting, and populates the reporting star schema
python -m src.pipeline
```

This populates:
- `reporting.dim_titles` (Conformed title dimension)
- `reporting.dim_genres` (Genre dimension)
- `reporting.fact_catalog_ratings` (Snapshot facts)
- `reporting.vw_powerbi_catalog_pulse` (Optimized analytical view)

---

## 📊 Step 5: Connect Power BI via DirectQuery

1. Open **Power BI Desktop**.
2. Click **Get Data** $\to$ select **PostgreSQL Database**.
3. Fill in connection details:
   - **Server**: `localhost:5432`
   - **Database**: `streampulse`
   - **Data Connectivity mode**: Select **DirectQuery** ⚡
4. Enter credentials:
   - **User Name**: `postgres`
   - **Password**: `postgres`
5. Select the view: **`reporting.vw_powerbi_catalog_pulse`**.
6. Click **Load**.

---

## 📈 Step 6: Create Key Power BI Measures & Visuals

In Power BI Desktop, create these standard DAX measures:

```dax
// 1. Total Catalog Count
TotalTitles = COUNTROWS(vw_powerbi_catalog_pulse)

// 2. Average Audience Rating
AverageRating = AVERAGE(vw_powerbi_catalog_pulse[vote_average])

// 3. Average TMDb Popularity
AvgPopularity = AVERAGE(vw_powerbi_catalog_pulse[popularity_score])

// 4. High Rating Catalog Share (Rating >= 8.0)
TopTierPercentage = 
DIVIDE(
    CALCULATE(COUNTROWS(vw_powerbi_catalog_pulse), vw_powerbi_catalog_pulse[vote_average] >= 8.0),
    COUNTROWS(vw_powerbi_catalog_pulse),
    0
)
```

### Visuals Layout:
1. **Card Visuals**: `TotalTitles`, `AverageRating`, `AvgPopularity`.
2. **Scatter Plot**: X-axis: `vote_average`, Y-axis: `popularity_score`, Legend: `rating_tier`.
3. **Clustered Bar Chart**: Count of Titles by `maturity_rating` and `media_type`.
4. **Donut Chart**: `match_confidence` distribution.
