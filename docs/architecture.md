# StreamPulse: Architecture & Technical Design

## 1. System Overview

StreamPulse is a resilient, modern ELT (Extract, Load, Transform) data engineering pipeline designed to ingest streaming catalog updates from Netflix, enrich those records with real-time metadata and audience ratings from The Movie Database (TMDb), perform algorithmic entity resolution, and expose dimensional data models to Power BI in DirectQuery mode for low-latency analytics.

```mermaid
flowchart TD
    subgraph Sources["1. Ingestion / Data Sources"]
        A1["RapidAPI (UnoGS Netflix Catalog)"]
        A2["TMDb API (Metadata, Popularity, Ratings)"]
    end

    subgraph Staging["2. Raw Staging Layer (PostgreSQL)"]
        B1[("stg_netflix_titles")]
        B2[("stg_tmdb_movies")]
        B3[("stg_tmdb_tv")]
    end

    subgraph Transformation["3. Processing & Entity Resolution"]
        C1["Title Normalization & Cleaning"]
        C2["Fuzzy Matching Engine (RapidFuzz / Levenshtein)"]
        C3["Year Range & Alias Resolution"]
        C4["Dimensional Modeling / Star Schema"]
    end

    subgraph Warehouse["4. Reporting Layer (PostgreSQL)"]
        D1[("dim_titles (Conformed)")]
        D2[("dim_genres")]
        D3[("dim_cast_crew")]
        D4[("fact_catalog_ratings")]
        D5["vw_powerbi_catalog_pulse (View)"]
    end

    subgraph BI["5. Analytics & Visualization"]
        E1["Power BI Desktop (DirectQuery)"]
        E2["Executive Streaming KPIs Dashboard"]
    end

    Sources -->|Airbyte / Python Extraction| Staging
    Staging -->|Python & SQL ELT| Transformation
    Transformation -->|Load Conformed Data| Warehouse
    Warehouse -->|DirectQuery (Low Latency)| BI
```

---

## 2. Core Architectural Pillars

### A. Extract & Ingest (EL)
- **Netflix Catalog Ingestion**: Scheduled Python or Airbyte connectors query RapidAPI for delta loads (newly added titles within the last $N$ hours or full batch refreshes).
- **TMDb Rating Enrichment**: For each ingested title, TMDb endpoints (`/search/movie`, `/search/tv`, `/movie/{id}/credits`, `/movie/{id}/keywords`) are queried with exponential backoff and rate-limiting to pull user ratings, vote counts, popularity indices, genres, and cast metadata.

### B. Raw Storage & Isolation (PostgreSQL Staging)
- Raw JSON payloads and tabular extracts land directly into the dedicated `staging` schema.
- Immutable raw data ensures idempotency, auditability, and replayability without re-hitting external third-party rate-limited APIs.

### C. Entity Resolution & Transformation (T)
- **Title Normalization**: Lowercasing, removing punctuation, handling stop words, roman numerals (`Part II` $\to$ `Part 2`), and regional variations.
- **Multi-Pass Resolution**:
  1. *Exact Match*: `normalized_title` + `exact_release_year`.
  2. *Fuzzy Match*: Levenshtein token sort ratio $\ge 85$ with `|netflix_year - tmdb_year| <= 1`.
  3. *Unresolved Queue*: Edge cases flagged with confidence scores for manual review or secondary heuristics.

### D. Dimensional Data Modeling (Star Schema)
Data is loaded into the `reporting` schema structured around analytics and Power BI performance:
- **`dim_titles`**: Surrogate key, Netflix ID, TMDb ID, canonical title, runtime, country, maturity rating, release date.
- **`dim_genres`** & **`bridge_title_genre`**: Many-to-many relationship supporting multi-genre filtering.
- **`dim_cast_crew`** & **`bridge_title_crew`**: Actors, directors, producers, and character names.
- **`fact_catalog_ratings`**: Snapshot metrics including vote average, vote count, TMDb popularity score, date added to Netflix, and days from theatrical release to streaming debut.

### E. Power BI DirectQuery Integration
- Exposes pre-aggregated and indexed SQL views (`vw_powerbi_catalog_pulse`).
- Utilizes composite and direct query models to eliminate data import lag and visualize real-time catalog changes.
