# 🔄 Airbyte Automated Daily ELT Pipeline & Power BI DirectQuery Master Guide

This guide details how to configure **Airbyte (v0.50.36)** as an automated daily ELT orchestrator to ingest newly scraped 2026 streaming catalog records into PostgreSQL, and connect **Power BI Desktop** via **DirectQuery** for real-time reporting.

---

## 🏗️ Automated Daily Architecture Workflow

```mermaid
flowchart LR
    subgraph DailyScrape [Step 1: Automated Daily Web Scraper]
        SCRAPER[Live 2026 Web Scraper\nWikipedia + Tudum + RSS]
        RAW_FILES[(data/raw/ & data/processed/\nMaster CSV/Parquet Landing)]
        SCRAPER -->|Daily Cron: 05:00 UTC| RAW_FILES
    end

    subgraph AirbyteStack [Step 2: Airbyte Automated ELT Ingestion]
        AB_SRC[Airbyte Source\nFile / Custom HTTP REST]
        AB_SCHED{Airbyte Cron Scheduler\n0 6 * * * (06:00 UTC)}
        AB_DEST[Airbyte Postgres Destination\nhost.docker.internal:5432]
        
        RAW_FILES --> AB_SRC
        AB_SRC --> AB_SCHED
        AB_SCHED -->|Incremental Sync| AB_DEST
    end

    subgraph PostgresDWH [Step 3: PostgreSQL Star Schema Warehouse]
        STG[(staging.stg_netflix_titles\nRaw Landing Zone)]
        TRANSFORM[SQL / DBT / Python Daemon\nKimball Galaxy Model Upsert]
        STAR_SCHEMA[(reporting.dim_titles\nreporting.dim_genres\nreporting.dim_date\nreporting.fact_catalog_ratings\nreporting.fact_streaming_perf)]
        VIEW[(reporting.vw_powerbi_catalog_pulse\nReporting View)]

        AB_DEST --> STG
        STG --> TRANSFORM
        TRANSFORM --> STAR_SCHEMA
        STAR_SCHEMA --> VIEW
    end

    subgraph PowerBI [Step 4: Power BI Live Reporting]
        PBI_DQ[Power BI Desktop\nDirectQuery Mode]
        DASHBOARD[Executive 2026 Dashboard\nAutomatic Page Refresh: 5 mins]
        VIEW -. Live DirectQuery SQL .-> PBI_DQ
        PBI_DQ --> DASHBOARD
    end
```

---

## 🚀 Step 1: Verify Airbyte Stack Health

Airbyte is running in Docker Compose with all required containers:
- `airbyte-server` (Micronaut backend listening on internal port 8001)
- `airbyte-webapp` (Nginx frontend listening on `http://localhost:8000`)
- `airbyte-temporal` (Workflow orchestration engine)
- `airbyte-db` (PostgreSQL configs & jobs database)

### Health Check Commands:
```powershell
# 1. Check container statuses
docker ps --filter "name=airbyte"

# 2. Test Airbyte API Health endpoint
python -c "import requests; print(requests.get('http://localhost:8000/api/v1/health').json())"
# Output: {'available': True}
```

---

## 🛠️ Step 2: Step-by-Step Airbyte Source & Destination Configuration

### 2.1 Access the Airbyte Web UI
1. Open your browser and navigate to: **[http://localhost:8000](http://localhost:8000)**
2. Default credentials:
   - **Username**: `airbyte` (or `docker`)
   - **Password**: `password` (or `docker`)

---

### 2.2 Configure the Source (Daily Catalog Landing Feed)
1. Click on **Sources** in the left navigation sidebar $\to$ Click **+ New Source**.
2. Search and select: **File (CSV)** (or **Custom HTTP API / Local Filesystem**).
3. Fill in the source configuration fields:

| Configuration Field | Value to Enter | Description |
| :--- | :--- | :--- |
| **Source Name** | `StreamPulse_Daily_2026_Catalog` | Descriptive identifier |
| **Storage Provider** | `Local Filesystem` (or `HTTPS: Public Web`) | Source storage type |
| **File Path / URL** | `data/processed/netflix_catalog_enriched_master.csv` | Scraper master output path |
| **Format** | `csv` | Format of the file |
| **Reader Options** | `{"encoding": "utf-8"}` | UTF-8 parser options |

4. Click **Set up source**. Airbyte will run a connection check to validate readability.

---

### 2.3 Configure the Destination (PostgreSQL Staging Warehouse)
1. Click on **Destinations** in the left navigation sidebar $\to$ Click **+ New Destination**.
2. Search and select: **Postgres**.
3. Fill in the destination configuration fields:

| Configuration Field | Value to Enter | Why this is needed |
| :--- | :--- | :--- |
| **Destination Name** | `StreamPulse_PostgreSQL_Warehouse` | Destination identifier |
| **Host** | `host.docker.internal` | Connects from Docker container back to Windows host PostgreSQL |
| **Port** | `5432` | PostgreSQL standard port |
| **DB Name** | `streampulse` | Project database |
| **Default Schema** | `staging` | Isolates raw staging from reporting schema |
| **User** | `postgres` | Database admin user |
| **Password** | `postgres` | Database password |
| **SSL Mode** | `disable` | Local Docker bridge network |

4. Click **Set up destination**. Airbyte will test the PostgreSQL credentials and schema permissions.

---

### 2.4 Create the Automated Daily Replication Connection
1. Click on **Connections** $\to$ Click **+ New Connection**.
2. Select Source: `StreamPulse_Daily_2026_Catalog`.
3. Select Destination: `StreamPulse_PostgreSQL_Warehouse`.
4. Configure Connection Settings:

| Setting | Value | Rationale |
| :--- | :--- | :--- |
| **Connection Name** | `Daily_2026_Catalog_to_Staging` | Connection label |
| **Schedule Type** | `Scheduled` | Automated recurring job |
| **Cron Expression** | `0 6 * * *` (or select `Every 24 hours`) | Runs daily at 06:00 AM UTC (1 hour after scraper) |
| **Sync Mode** | `Incremental \| Append + Deduped` | Prevents duplicate titles while appending new releases |
| **Primary Key** | `netflix_id` | Unique title identifier |
| **Cursor Field** | `extracted_at` (or `date_added`) | High-watermark for incremental tracking |
| **Destination Stream Prefix** | `stg_` | Creates/updates `staging.stg_netflix_titles` |

5. Click **Save connection** $\to$ Click **Sync Now** to run the initial baseline replication!

---

### 2.5 Programmatic Airbyte Execution via Code (Python REST API Client)

You can also manage, test, and trigger the Airbyte replication connection entirely through code using StreamPulse's programmatic Python API client:

#### Run via CLI Runner:
```powershell
# Trigger immediate replication and wait for sync completion
python scripts/run_airbyte_connection.py --sync-now

# Or using Makefile:
make airbyte-sync
```

#### Programmatic Python Scripting Example:
```python
from src.load.airbyte_client import airbyte_client

# 1. Check Airbyte stack health
health = airbyte_client.check_health()
print(f"Airbyte Online: {health['available']}")

# 2. Get or create Workspace
workspace_id = airbyte_client.get_or_create_workspace(workspace_name="StreamPulse")

# 3. Discover/provision File CSV Source & PostgreSQL Destination
source_id = airbyte_client.get_or_create_source(
    workspace_id=workspace_id,
    source_name="StreamPulse_Daily_2026_Catalog",
    file_path="data/processed/netflix_catalog_enriched_master.csv",
)
dest_id = airbyte_client.get_or_create_destination(
    workspace_id=workspace_id,
    dest_name="StreamPulse_PostgreSQL_Warehouse",
    db_host="host.docker.internal",
    db_port=5432,
    db_name="streampulse",
    default_schema="staging",
)

# 4. Provision Replication Connection
conn_id = airbyte_client.get_or_create_connection(
    workspace_id=workspace_id,
    source_id=source_id,
    destination_id=dest_id,
    connection_name="Daily_2026_Catalog_to_Staging",
)

# 5. Trigger replication and block until completion
sync_result = airbyte_client.sync_and_wait(connection_id=conn_id, timeout_seconds=180)
print(f"Sync Result: {sync_result['success']}")
```

---

## ⚡ Step 3: Downstream Automatic Transformation Trigger

When Airbyte lands raw records into `staging.stg_netflix_titles`, the StreamPulse automated pipeline triggers the Kimball Galaxy transformation:

```powershell
# Run the pipeline daemon or scheduled task
python src/pipeline.py --mode stream --stream-interval 86400
```

### What happens automatically:
1. `reporting.dim_titles` is updated with `catalog_era`, `budget_usd`, and clean metadata.
2. `reporting.dim_genres` and `reporting.bridge_title_genre` map new multi-genre associations.
3. `reporting.fact_catalog_ratings` logs daily vote and popularity snapshots.
4. `reporting.fact_streaming_performance` logs global view hours and completion metrics.
5. `data/processed/lakehouse/*.parquet` files are updated with fresh Snappy compression.

---

## 📊 Step 4: Connecting Power BI via Live DirectQuery

Now connect Power BI Desktop to the PostgreSQL view so that daily Airbyte syncs instantly update the dashboard visuals:

### 4.1 Step-by-Step Power BI DirectQuery Connection:
1. Open **Power BI Desktop**.
2. Click **Get Data** $\to$ Select **PostgreSQL database** $\to$ Click **Connect**.
3. In the PostgreSQL dialog:
   - **Server**: `localhost:5432`
   - **Database**: `streampulse`
   - **Data Connectivity mode**: Select **DirectQuery** 🟢 *(Crucial for live auto-refresh!)*
   - **Advanced options**: Leave empty or paste:
     ```sql
     SELECT * FROM reporting.vw_powerbi_catalog_pulse;
     ```
4. Click **OK** $\to$ Enter credentials: User `postgres`, Password `postgres` $\to$ Click **Connect**.
5. Select `vw_powerbi_catalog_pulse` and click **Load**.

---

### 4.2 Enabling Automatic Page Refresh in Power BI:
1. Select the report canvas (click empty background).
2. Open the **Format visual** pane $\to$ select **Page refresh**.
3. Toggle **Page refresh** to **ON**.
4. Set **Refresh interval**: `5 Minutes` (or `1 Minute`).
5. **Result**: Every morning when Airbyte syncs new 2026 titles into PostgreSQL, your Power BI dashboard updates automatically without needing to republish!

---

## 💡 Troubleshooting & Production Best Practices

| Symptom | Cause | Solution |
| :--- | :--- | :--- |
| `Cannot connect to host.docker.internal` | Docker Desktop host networking on Windows | Ensure `host.docker.internal` is used as host inside Airbyte UI instead of `localhost`. |
| `Sync fails with table already exists` | Staging schema conflict | Set Airbyte sync mode to `Incremental \| Append + Deduped` or `Full Refresh \| Overwrite`. |
| `Power BI prompts for dataset refresh` | Imported mode was selected instead of DirectQuery | Reconnect using **DirectQuery** connectivity mode under PostgreSQL connector. |
| `Airbyte UI 502 Bad Gateway` | Server container still initializing Micronaut | Wait 20-30 seconds for `airbyte-server` to finish boot checks. |
