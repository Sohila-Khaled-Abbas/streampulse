# StreamPulse: Data Dictionary & Schema Documentation

## 1. Staging Schema (`staging`)

The staging schema holds semi-structured, raw landing data ingested from external APIs.

### `staging.stg_netflix_titles`
| Column Name | Data Type | Nullable | Description |
| :--- | :--- | :--- | :--- |
| `netflix_id` | `VARCHAR(50)` | NO (PK) | Unique Netflix UnoGS/Catalog identifier |
| `title` | `VARCHAR(500)` | NO | Title as listed on Netflix |
| `title_type` | `VARCHAR(20)` | YES | Type of media (`movie`, `series`, `documentary`) |
| `synopsis` | `TEXT` | YES | Plot overview |
| `release_year` | `INT` | YES | Year original title was released |
| `date_added` | `TIMESTAMP` | YES | Timestamp when title was added to Netflix catalog |
| `runtime_seconds` | `INT` | YES | Total runtime in seconds |
| `maturity_rating` | `VARCHAR(20)` | YES | Content maturity rating (e.g., `TV-MA`, `PG-13`) |
| `raw_json` | `JSONB` | YES | Raw API JSON response for audit trail |
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
| `cast_json` | `JSONB` | YES | Array of cast members `[{id, name, character}]` |
| `raw_json` | `JSONB` | YES | Raw TMDb payload |
| `extracted_at` | `TIMESTAMP` | NO | Ingestion timestamp |

---

## 2. Reporting Schema (`reporting`)

The reporting schema implements a conformed dimensional model optimized for analytics and Power BI DirectQuery.

### `reporting.dim_titles` (Conformed Dimension)
| Column Name | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `title_key` | `BIGSERIAL` | PRIMARY KEY | Surrogate surrogate key for title |
| `netflix_id` | `VARCHAR(50)` | UNIQUE, NOT NULL | Netflix catalog ID |
| `tmdb_id` | `INT` | NULLABLE | Resolved TMDb identifier |
| `canonical_title` | `VARCHAR(500)` | NOT NULL | Conformed, display title |
| `media_type` | `VARCHAR(20)` | NOT NULL | `Movie` or `TV Series` |
| `release_year` | `INT` | NULLABLE | Canonical release year |
| `release_date` | `DATE` | NULLABLE | Theatrical / global premiere date |
| `netflix_date_added` | `DATE` | NOT NULL | Date available on Netflix |
| `maturity_rating` | `VARCHAR(20)` | NULLABLE | Content age rating |
| `runtime_minutes` | `INT` | NULLABLE | Runtime formatted in minutes |
| `match_confidence` | `NUMERIC(5,2)` | NOT NULL | Entity resolution score (100.00 = exact) |
| `is_active` | `BOOLEAN` | DEFAULT TRUE | Catalog status flag |

---

### `reporting.dim_genres`
| Column Name | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `genre_key` | `SERIAL` | PRIMARY KEY | Surrogate genre key |
| `tmdb_genre_id` | `INT` | UNIQUE | TMDb standard genre ID |
| `genre_name` | `VARCHAR(100)` | NOT NULL | Genre label (e.g. `Action`, `Sci-Fi`) |

---

### `reporting.bridge_title_genre`
| Column Name | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `title_key` | `BIGINT` | FK $\to$ `dim_titles.title_key` | Foreign key to title |
| `genre_key` | `INT` | FK $\to$ `dim_genres.genre_key` | Foreign key to genre |

---

### `reporting.fact_catalog_ratings` (Fact Table)
| Column Name | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `fact_rating_key` | `BIGSERIAL` | PRIMARY KEY | Fact surrogate key |
| `title_key` | `BIGINT` | FK $\to$ `dim_titles.title_key` | Title reference |
| `date_key` | `INT` | FK $\to$ `dim_date.date_key` | Date snapshot key (`YYYYMMDD`) |
| `vote_average` | `NUMERIC(3,1)` | NOT NULL | Current user rating |
| `vote_count` | `INT` | NOT NULL | Total user votes |
| `popularity_score` | `NUMERIC(10,3)` | NOT NULL | Current TMDb popularity index |
| `days_to_streaming`| `INT` | NULLABLE | `date_added - release_date` in days |
| `is_trending` | `BOOLEAN` | NOT NULL | Flag for high-velocity popular titles |
