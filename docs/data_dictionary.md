# ⚡ StreamPulse: Data Dictionary & Schema Documentation

## 1. Staging Schema (`staging`)

The staging schema holds raw landing data ingested from web scrapers and external APIs.

### `staging.stg_netflix_titles`
| Column Name | Data Type | Nullable | Description |
| :--- | :--- | :--- | :--- |
| `netflix_id` | `VARCHAR(50)` | NO (PK) | Unique Netflix UnoGS/Wikipedia surrogate identifier |
| `title` | `VARCHAR(500)` | NO | Title as listed on Netflix |
| `title_type` | `VARCHAR(20)` | YES | Type of media (`movie`, `series`) |
| `synopsis` | `TEXT` | YES | Plot overview |
| `release_year` | `INT` | YES | Year original title was released |
| `date_added` | `TIMESTAMP` | YES | Timestamp when title was added to Netflix catalog |
| `runtime_seconds` | `INT` | YES | Total runtime in seconds |
| `maturity_rating` | `VARCHAR(20)` | YES | Content maturity rating (e.g., `TV-MA`, `PG-13`) |
| `raw_json` | `JSONB` | YES | Raw JSON response for audit trail |
| `extracted_at` | `TIMESTAMP` | NO | Ingestion timestamp (default `NOW()`) |

---

### `staging.stg_tmdb_metadata`
| Column Name | Data Type | Nullable | Description |
| :--- | :--- | :--- | :--- |
| `tmdb_id` | `INT` | NO (PK) | TMDb unique entity ID |
| `media_type` | `VARCHAR(20)` | NO | Media type (`movie` or `tv`) |
| `title` | `VARCHAR(500)` | NO | Canonical title on TMDb |
| `original_title` | `VARCHAR(500)` | YES | Native language title |
| `release_date` | `DATE` | YES | Premiere release date |
| `vote_average` | `NUMERIC(3,1)` | YES | User rating score (0.0 to 10.0) |
| `vote_count` | `INT` | YES | Number of audience votes |
| `popularity` | `NUMERIC(10,3)` | YES | TMDb algorithmic popularity score |
| `genres_json` | `JSONB` | YES | Array of genre objects `[{id, name}]` |
| `raw_json` | `JSONB` | YES | Raw payload |
| `extracted_at` | `TIMESTAMP` | NO | Ingestion timestamp |

---

## 2. Reporting Schema (`reporting`)

The reporting schema implements a Kimball dimensional star schema optimized for Power BI DirectQuery.

### `reporting.dim_titles` (Conformed Dimension)
| Column Name | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `title_key` | `BIGSERIAL` | PRIMARY KEY | Surrogate key for title |
| `netflix_id` | `VARCHAR(50)` | UNIQUE, NOT NULL | Netflix catalog ID |
| `tmdb_id` | `INT` | NULLABLE | Resolved TMDb / IMDb identifier |
| `canonical_title` | `VARCHAR(500)` | NOT NULL | Conformed display title |
| `media_type` | `VARCHAR(20)` | NOT NULL | `movie` or `series` |
| `release_year` | `INT` | NULLABLE | Canonical release year |
| `release_date` | `DATE` | NULLABLE | Theatrical / premiere date |
| `netflix_date_added` | `DATE` | NOT NULL | Date available on Netflix |
| `maturity_rating` | `VARCHAR(20)` | NULLABLE | Content age rating (e.g. `PG-13`, `TV-MA`) |
| `runtime_minutes` | `INT` | NULLABLE | Runtime formatted in minutes |
| `match_confidence` | `NUMERIC(5,2)` | NOT NULL | Entity resolution score (100.00 = exact) |
| `is_active` | `BOOLEAN` | DEFAULT TRUE | Active catalog flag |
| `created_at` | `TIMESTAMP` | NOT NULL | Record creation timestamp |
| `updated_at` | `TIMESTAMP` | NOT NULL | Record last update timestamp |

---

---

### `reporting.dim_genres` (Genre Dimension)
| Column Name | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `genre_key` | `BIGSERIAL` | PRIMARY KEY | Surrogate key for genre |
| `genre_name` | `VARCHAR(100)` | UNIQUE, NOT NULL | Standardized canonical genre name |
| `tmdb_genre_id` | `INT` | NULLABLE | TMDb standard genre identifier |
| `genre_category` | `VARCHAR(50)` | NOT NULL | Genre grouping (`Mainstream`, `Prestige Drama`, etc.) |

---

### `reporting.bridge_title_genre` (Many-to-Many Bridge)
| Column Name | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `bridge_key` | `BIGSERIAL` | PRIMARY KEY | Surrogate bridge key |
| `title_key` | `BIGINT` | FK $\to$ `dim_titles` | Reference to title |
| `genre_key` | `BIGINT` | FK $\to$ `dim_genres` | Reference to genre |
| `genre_weight` | `NUMERIC(3,2)` | DEFAULT 1.00 | Fractional weight for multi-genre allocation |

---

### `reporting.dim_date` (Conformed Calendar Dimension)
| Column Name | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `date_key` | `INT` | PRIMARY KEY | Integer date key (`YYYYMMDD`) |
| `full_date` | `DATE` | UNIQUE, NOT NULL | Calendar date |
| `year` | `INT` | NOT NULL | Calendar year (e.g. 2026) |
| `quarter` | `INT` | NOT NULL | Quarter (1-4) |
| `quarter_name` | `VARCHAR(20)` | NOT NULL | Formatted quarter (`Q1 2026`) |
| `month_number` | `INT` | NOT NULL | Month number (1-12) |
| `month_name` | `VARCHAR(20)` | NOT NULL | Full month name (`January`) |
| `is_weekend` | `BOOLEAN` | NOT NULL | Weekend indicator |
| `is_current_year` | `BOOLEAN` | NOT NULL | Dynamic current year flag |
| `relative_year_offset` | `INT` | NOT NULL | Offset from current year (`0` = current, `-1` = prior) |

---

### `reporting.fact_catalog_ratings` (Fact Table: Ratings & Score Snapshots)
| Column Name | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `fact_rating_key` | `BIGSERIAL` | PRIMARY KEY | Surrogate key for fact row |
| `title_key` | `BIGINT` | FK $\to$ `dim_titles` | Foreign key referencing title |
| `date_key` | `INT` | FK $\to$ `dim_date` | Foreign key referencing calendar date |
| `vote_average` | `NUMERIC(3,1)` | NOT NULL | Audience rating (0.0 - 10.0) |
| `vote_count` | `INT` | NOT NULL | Audience vote count |
| `critic_score` | `NUMERIC(5,2)` | NULLABLE | TMDb / Metascore index (0-100) |
| `days_to_streaming` | `INT` | NULLABLE | Days from premiere to streaming release |
| `is_trending` | `BOOLEAN` | NOT NULL | High velocity / trending flag |
| `recorded_at` | `TIMESTAMP` | NOT NULL | Ingestion timestamp |

---

### `reporting.fact_streaming_performance` (Fact Table: Granular Telemetry)
| Column Name | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `performance_key` | `BIGSERIAL` | PRIMARY KEY | Surrogate key for fact row |
| `title_key` | `BIGINT` | FK $\to$ `dim_titles` | Reference to title |
| `date_key` | `INT` | FK $\to$ `dim_date` | Reference to calendar date |
| `territory_standardized` | `VARCHAR(50)` | NOT NULL | Standardized territory (`United States`, `Global`, etc.) |
| `device_category` | `VARCHAR(50)` | NOT NULL | Device category (`Connected TV`, `Mobile`, `Web`) |
| `global_view_hours_millions` | `NUMERIC(10,2)` | NOT NULL | Total global view hours (millions) |
| `avg_completion_pct` | `NUMERIC(5,2)` | NOT NULL | Average audience completion rate (%) |
| `subscribers_reached_thousands` | `NUMERIC(10,2)` | NOT NULL | Unique accounts reached (thousands) |

---

### `reporting.vw_powerbi_catalog_pulse` (DirectQuery View)
| Field | Type | Description |
| :--- | :--- | :--- |
| `title_key` | `BIGINT` | Primary dimension key |
| `title` | `VARCHAR` | Conformed title name |
| `media_type` | `VARCHAR` | `movie` or `series` |
| `release_year` | `INT` | Release year |
| `catalog_era` | `VARCHAR` | `'2026 Live Releases'`, `'2024-2025 Modern'`, or `'Historical Archive'` |
| `netflix_date_added` | `DATE` | Streaming drop date |
| `maturity_rating` | `VARCHAR` | Content rating |
| `runtime_minutes` | `INT` | Runtime in minutes |
| `match_confidence` | `NUMERIC` | Fuzzy match confidence score |
| `vote_average` | `NUMERIC` | Current audience score |
| `vote_count` | `INT` | Total audience ratings |
| `popularity_score` | `NUMERIC` | Popularity score |
| `days_to_streaming` | `INT` | Streaming velocity (days) |
| `is_trending` | `BOOLEAN` | Trending release indicator |
| `rating_tier` | `VARCHAR` | `'Top Rated (>= 8.0)'`, `'Good (6.5 - 7.9)'`, `'Mixed (< 6.5)'` |

---

## 3. Raw Training Sources (`data/raw/`)

| File Name | Format | Record Count | Description & Ingestion Role |
| :--- | :--- | :--- | :--- |
| `netflix_enriched_historical.csv` | CSV | 7,788 titles | Historical benchmark catalog archive (1945–2024) |
| `imdb_external_ratings.csv` | CSV | 24 snapshots | Live periodic audience ratings snapshot with string formats |
| `streaming_viewership_wide.parquet` | Parquet | 20 records | Granular multi-month wide telemetry metrics |
| `boxoffice_budget_feed.json` | JSON | 20 feeds | Production budget, talent, and nested genre categorizations |

---

## 4. Data Profiling & Quality Artifact (`data_profiling_report.json`)

| Metric / Section | Description |
| :--- | :--- |
| `validation_status` | Overall validation state (`PASSED` or `WARNING`) |
| `quality_score` | Weighted completeness score ($0-100\%$) across title, ID, year, and rating |
| `total_records` | Count of processed and conformed titles |
| `era_breakdown` | Counts for `2026_live`, `2024_2025_modern`, and `historical_archive` |
| `media_type_breakdown` | Distribution of `movie` vs `series` |
| `rating_tier_distribution` | Count of `top_rated`, `good`, `mixed`, and `unrated` |
| `match_confidence_distribution` | High ($\ge 90\%$), Medium ($75-89\%$), and Low ($<75\%$) counts |
| `field_completeness` | Dictionary of present vs missing counts and completeness percentages per field |
