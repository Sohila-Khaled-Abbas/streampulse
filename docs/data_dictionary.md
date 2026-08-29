# ⚡ StreamPulse: Enterprise Data Dictionary & Kimball Galaxy Schema Documentation

This document serves as the enterprise data catalog for the **StreamPulse Multi-Source Kimball Galaxy Constellation Model**, documenting tables across both the Staging Ingestion Layer and the Reporting Semantic Layer.

---

## 1. Staging Ingestion Layer (`staging`)

### `staging.stg_netflix_titles`
*Landing table for daily Netflix scraped releases and sync feeds.*
| Column Name | Data Type | Nullable | Description | Example Values |
| :--- | :--- | :--- | :--- | :--- |
| `netflix_id` | `VARCHAR(50)` | NO (PK) | Unique Netflix UnoGS/Catalog identifier | `8001`, `81459281` |
| `title` | `VARCHAR(500)` | NO | Raw title as listed on streaming platform | `Avatar: Fire and Ash` |
| `title_type` | `VARCHAR(20)` | YES | Media classification (`Movie`, `TV Show`) | `Movie`, `TV Show` |
| `synopsis` | `TEXT` | YES | Narrative plot overview | `In a future where the elite...` |
| `release_year` | `INT` | YES | Canonical theatrical/broadcast release year | `2026`, `2024` |
| `date_added` | `TIMESTAMP` | YES | Timestamp when title was ingested into catalog | `2026-02-27T19:00:00Z` |
| `runtime_seconds` | `INT` | YES | Runtime duration in raw seconds | `5400`, `8700` |
| `maturity_rating` | `VARCHAR(20)` | YES | Age classification rating | `TV-MA`, `PG-13`, `R` |
| `raw_json` | `JSONB` | YES | Full raw payload for lineage tracking | `{"cast": [...], "director": "..."}` |
| `extracted_at` | `TIMESTAMP` | NO | Pipeline extraction timestamp | `NOW()` |

---

## 2. Kimball Galaxy Reporting & Semantic Layer (`reporting`)

### Conformed Dimensions

#### `reporting.dim_titles` (Conformed Title Dimension)
*Master title dimension linking live streaming releases and 7,786 historical benchmark titles.*
| Column Name | Data Type | Constraints | Description | Business Rules / M Logic |
| :--- | :--- | :--- | :--- | :--- |
| `title_key` | `BIGSERIAL / INT64` | PRIMARY KEY | Surrogate integer key | Sequential 1-based index |
| `netflix_id` | `VARCHAR(50)` | UNIQUE, NOT NULL | Natural Netflix catalog identifier | Conformed natural key |
| `canonical_title` | `VARCHAR(500)` | NOT NULL | Conformed title name | Capitalized, stripped of `\xa0` |
| `media_type` | `VARCHAR(20)` | NOT NULL | `Movie` or `TV Show` | Standardized title type |
| `release_year` | `INT` | NOT NULL | Premiere release year | Fallback default: `2020` |
| `netflix_date_added` | `DATE` | NOT NULL | First date available on Netflix | Standardized ISO Date |
| `maturity_rating` | `VARCHAR(20)` | NOT NULL | Content maturity rating | Standardized: `TV-MA`, `PG-13` |
| `runtime_minutes` | `INT` | NOT NULL | Duration in minutes | Converted from seconds / strings |
| `catalog_era` | `VARCHAR(50)` | NOT NULL | Era segmentation | `2026 Live Releases`, `Historical (<2015)` |
| `runtime_tier` | `VARCHAR(50)` | NOT NULL | Runtime categorization | `Short (<45m)`, `Standard`, `Epic (>140m)` |
| `maturity_category`| `VARCHAR(50)` | NOT NULL | Target audience grouping | `Adult (18+)`, `Teens (13+)`, `Kids (G)` |
| `is_active` | `BOOLEAN` | DEFAULT TRUE | Active streaming catalog status | Filter flag for active analytics |

---

#### `reporting.dim_date` (Dynamic Calendar Dimension)
*Conformed enterprise calendar supporting fiscal quarters, rolling velocity, and time intelligence.*
| Column Name | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `date_key` | `INT` | PRIMARY KEY | Integer date key formatted as `YYYYMMDD` (e.g. `20260227`) |
| `full_date` | `DATE` | UNIQUE, NOT NULL | Calendar date (`2026-02-27`) |
| `year` | `INT` | NOT NULL | Calendar year (`2026`) |
| `quarter` | `INT` | NOT NULL | Calendar quarter (`1` to `4`) |
| `quarter_name` | `VARCHAR(10)` | NOT NULL | Formatted quarter string (`Q1 2026`) |
| `month_number` | `INT` | NOT NULL | Month index (`1` to `12`) |
| `month_name` | `VARCHAR(20)` | NOT NULL | Full month name (`February`) |
| `month_short` | `VARCHAR(5)` | NOT NULL | 3-letter month abbreviation (`Feb`) |
| `day_of_week` | `INT` | NOT NULL | 1 (Monday) to 7 (Sunday) |
| `day_name` | `VARCHAR(15)` | NOT NULL | Day string (`Friday`) |
| `is_weekend` | `BOOLEAN` | NOT NULL | True if Saturday or Sunday |
| `fiscal_period` | `VARCHAR(15)` | NOT NULL | Formatted fiscal period (`FY2026-Q1`) |
| `is_current_year` | `BOOLEAN` | NOT NULL | True if date belongs to current calendar year |
| `relative_year_offset`| `INT` | NOT NULL | Year offset (`0` for current year, `-1` for prior year) |
| `is_netflix_quarter_end`| `BOOLEAN` | NOT NULL | True on Mar 31, Jun 30, Sep 30, Dec 31 |

---

#### `reporting.dim_genres` (Standardized Genre Dimension)
*Conformed genre taxonomy aligned with TMDB and Netflix category mappings.*
| Column Name | Data Type | Constraints | Description | Category Group |
| :--- | :--- | :--- | :--- | :--- |
| `genre_key` | `INT` | PRIMARY KEY | Surrogate genre key (`1` to `13`) | Sequential index |
| `tmdb_genre_id` | `INT` | UNIQUE, NOT NULL | TMDB canonical genre ID | Standard identifier |
| `genre_name` | `VARCHAR(100)` | UNIQUE, NOT NULL | Genre name | `Action`, `Drama`, `Sci-Fi` |
| `genre_category` | `VARCHAR(50)` | NOT NULL | High-level genre cluster | `Mainstream Commercial`, `Prestige` |
| `sort_order` | `INT` | NOT NULL | Standardized visual sort order | 1 to 13 |

---

#### `reporting.dim_territory` (Global Geography Dimension)
*Conformed global regional dimension capturing country codes, currency, and market maturity.*
| Column Name | Data Type | Constraints | Description | Example Values |
| :--- | :--- | :--- | :--- | :--- |
| `territory_key` | `INT` | PRIMARY KEY | Surrogate territory key | `1`, `2`, `3`, `4`, `5` |
| `territory_code` | `VARCHAR(5)` | UNIQUE, NOT NULL | ISO 2-letter country/region code | `US`, `GB`, `KR`, `JP`, `GL` |
| `territory_name` | `VARCHAR(100)` | NOT NULL | Territory display name | `United States`, `South Korea` |
| `region_group` | `VARCHAR(50)` | NOT NULL | Global operational hub | `North America`, `EMEA`, `APAC` |
| `currency_code` | `VARCHAR(10)` | NOT NULL | Primary settlement currency | `USD`, `GBP`, `KRW`, `JPY` |
| `market_maturity` | `VARCHAR(50)` | NOT NULL | Streaming adoption tier | `Mature Hub`, `High Growth` |
| `streaming_penetration_pct`| `NUMERIC(4,2)`| NOT NULL | Estimated household penetration | `0.85`, `0.72` |

---

#### `reporting.dim_talent_crew` (Creative Talent Dimension)
*Captures directors and producers across historical and live catalog releases.*
| Column Name | Data Type | Constraints | Description | Example Values |
| :--- | :--- | :--- | :--- | :--- |
| `crew_key` | `INT` | PRIMARY KEY | Surrogate talent key | Sequential index |
| `person_name` | `VARCHAR(200)` | UNIQUE, NOT NULL | Full name of director or producer | `Christopher Nolan`, `David Fincher` |
| `primary_role` | `VARCHAR(50)` | NOT NULL | Primary creative credit | `Director`, `Producer` |
| `star_power_tier` | `VARCHAR(50)` | NOT NULL | Industry tiering classification | `Tier 1 - Global A-List`, `Tier 2` |

---

### Bridge Tables (Many-to-Many Relationships)

#### `reporting.bridge_title_genre`
*Resolves the many-to-many relationship between `Dim_Titles` and `Dim_Genres`.*
| Column Name | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `title_key` | `BIGINT` | FK $\to$ `dim_titles.title_key` | Referenced title |
| `genre_key` | `INT` | FK $\to$ `dim_genres.genre_key` | Referenced genre |
| `genre_weight` | `NUMERIC(3,2)` | NOT NULL DEFAULT 1.00 | Weight for fractional revenue/view allocation |

---

#### `reporting.bridge_title_talent`
*Resolves the many-to-many relationship between `Dim_Titles` and `Dim_Talent_Crew`.*
| Column Name | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `title_key` | `BIGINT` | FK $\to$ `dim_titles.title_key` | Referenced title |
| `crew_key` | `INT` | FK $\to$ `dim_talent_crew.crew_key` | Referenced director/producer |
| `billing_order` | `INT` | NOT NULL DEFAULT 1 | Credit billing rank on title |

---

### Fact Tables (Multi-Grain Constellation Facts)

#### `reporting.fact_streaming_performance` (Granular Telemetry Fact)
*Captures monthly streaming viewership, completion rates, and subscriber reach.*
| Column Name | Data Type | Constraints | Description | Grain & Aggregation Rule |
| :--- | :--- | :--- | :--- | :--- |
| `performance_key` | `BIGSERIAL / INT64` | PRIMARY KEY | Surrogate fact key | Unique per monthly record |
| `title_key` | `BIGINT` | FK $\to$ `dim_titles` | Reference to title | Grain: Title |
| `date_key` | `INT` | FK $\to$ `dim_date` | Reference to month start date | Grain: Month |
| `territory_key` | `INT` | FK $\to$ `dim_territory` | Reference to territory | Grain: Territory |
| `device_category` | `VARCHAR(50)` | NOT NULL | Streaming hardware category | `Connected TV`, `Mobile`, `Web` |
| `global_view_hours_millions`| `NUMERIC(10,2)`| NOT NULL | Total streaming hours (Millions) | Additive (`SUM`) |
| `avg_completion_pct` | `NUMERIC(5,2)` | NOT NULL | Average title completion rate | Non-Additive (`AVERAGE`) |
| `subscribers_reached_thousands`| `INT` | NOT NULL | Unique active profiles reached (k) | Semi-Additive |

---

#### `reporting.fact_catalog_ratings` (Periodic Rating Snapshot Fact)
*Captures periodic audience ratings, vote volumes, and critic scores.*
| Column Name | Data Type | Constraints | Description | Grain & Aggregation Rule |
| :--- | :--- | :--- | :--- | :--- |
| `fact_rating_key` | `BIGSERIAL / INT64` | PRIMARY KEY | Surrogate fact key | Unique per snapshot |
| `title_key` | `BIGINT` | FK $\to$ `dim_titles` | Reference to title | Grain: Title |
| `date_key` | `INT` | FK $\to$ `dim_date` | Snapshot timestamp date key | Grain: Snapshot Date |
| `vote_average` | `NUMERIC(3,1)` | NOT NULL | Raw IMDb / TMDb score (0-10) | Non-Additive (`AVERAGE`) |
| `vote_count` | `INT` | NOT NULL | Total vote volume | Additive (`SUM`) |
| `critic_score` | `NUMERIC(4,1)` | NOT NULL | Metascore / Critic rating (0-100)| Non-Additive (`AVERAGE`) |

---

#### `reporting.fact_financial_roi` (Production Budget & Unit Economics Fact)
*Captures production budgets, worldwide box office gross, and theatrical profitability.*
| Column Name | Data Type | Constraints | Description | Grain & Aggregation Rule |
| :--- | :--- | :--- | :--- | :--- |
| `financial_key` | `BIGSERIAL / INT64` | PRIMARY KEY | Surrogate fact key | Unique per title financial record |
| `title_key` | `BIGINT` | FK $\to$ `dim_titles` | Reference to title | Grain: Title |
| `date_key` | `INT` | FK $\to$ `dim_date` | Premiere calendar date key | Grain: Premiere Date |
| `production_budget_usd` | `NUMERIC(15,2)`| NOT NULL | Production budget in USD | Additive (`SUM`) |
| `worldwide_gross_usd` | `NUMERIC(15,2)`| NOT NULL | Global box office gross in USD | Additive (`SUM`) |
| `financial_roi_tier` | `VARCHAR(50)` | NOT NULL | ROI category | `Blockbuster Hit`, `Underperformer` |

---

*Enterprise Data Dictionary verified for StreamPulse Kimball Galaxy Semantic Model.*
