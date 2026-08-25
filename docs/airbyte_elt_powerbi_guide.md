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

## 🔌 Step 2: Launching Airbyte

You can launch Airbyte locally using the official Airbyte installation tool:

### Option A: Using Airbyte CLI (`abctl` - Recommended)
```powershell
# Install and start Airbyte
abctl local install
```

### Option B: Using Official Airbyte Docker Repo
```powershell
git clone https://github.com/airbytehq/airbyte.git
cd airbyte
docker compose up -d
```

Once running, access the **Airbyte Web UI** at:
🌐 **`http://localhost:8000`**
- **Default Username**: `airbyte`
- **Default Password**: `password`

---

## 📥 Step 3: Configure Airbyte Source & Destination

### 1. Set Up Airbyte Destination (PostgreSQL)
1. In Airbyte UI, go to **Destinations** $\to$ **New destination**.
2. Select **Postgres**.
3. Configure connection:
   - **Host**: `host.docker.internal` *(or `localhost` if outside Docker)*
   - **Port**: `5432`
   - **DB Name**: `streampulse`
   - **Default Schema**: `staging`
   - **User**: `postgres`
   - **Password**: `postgres`
   - **SSL Mode**: `disable`
4. Click **Set up destination** (Airbyte will test the connection).

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
