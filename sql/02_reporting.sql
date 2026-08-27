-- ==============================================================================
-- StreamPulse: 02_reporting.sql
-- Enterprise Kimball Galaxy Schema & Power BI DirectQuery Analytics Layer
-- ==============================================================================

-- Cleanly drop old views first
DROP VIEW IF EXISTS reporting.vw_powerbi_performance_matrix CASCADE;
DROP VIEW IF EXISTS reporting.vw_powerbi_catalog_pulse CASCADE;

-- Ensure fresh schema creation if needed
CREATE TABLE IF NOT EXISTS reporting.dim_date (
    date_key INT PRIMARY KEY,                       -- Format: YYYYMMDD
    full_date DATE UNIQUE NOT NULL,
    year INT NOT NULL,
    quarter INT NOT NULL,
    quarter_name VARCHAR(10) NOT NULL,              -- 'Q1 2026'
    month_number INT NOT NULL,
    month_name VARCHAR(20) NOT NULL,
    month_short VARCHAR(5) NOT NULL,
    week_of_year INT NOT NULL,
    day_of_month INT NOT NULL,
    day_of_week INT NOT NULL,
    day_name VARCHAR(15) NOT NULL,
    is_weekend BOOLEAN NOT NULL,
    is_netflix_quarter_end BOOLEAN NOT NULL,
    fiscal_period VARCHAR(15) NOT NULL
);

-- Title Dimension
CREATE TABLE IF NOT EXISTS reporting.dim_titles (
    title_key BIGSERIAL PRIMARY KEY,
    netflix_id VARCHAR(50) UNIQUE NOT NULL,
    tmdb_id INT,
    canonical_title VARCHAR(500) NOT NULL,
    media_type VARCHAR(20) NOT NULL,
    release_year INT NOT NULL,
    release_date DATE,
    netflix_date_added DATE NOT NULL,
    maturity_rating VARCHAR(20) DEFAULT 'TV-MA',
    runtime_minutes INT DEFAULT 90,
    budget_usd NUMERIC(15,2) DEFAULT 25000000.00,
    original_language VARCHAR(20) DEFAULT 'en',
    production_country VARCHAR(100) DEFAULT 'United States',
    catalog_era VARCHAR(50) NOT NULL DEFAULT '2026 Live Releases',
    match_confidence NUMERIC(5,2) NOT NULL DEFAULT 100.0,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- In case dim_titles already existed, add missing columns
ALTER TABLE reporting.dim_titles ADD COLUMN IF NOT EXISTS budget_usd NUMERIC(15,2) DEFAULT 25000000.00;
ALTER TABLE reporting.dim_titles ADD COLUMN IF NOT EXISTS original_language VARCHAR(20) DEFAULT 'en';
ALTER TABLE reporting.dim_titles ADD COLUMN IF NOT EXISTS production_country VARCHAR(100) DEFAULT 'United States';
ALTER TABLE reporting.dim_titles ADD COLUMN IF NOT EXISTS catalog_era VARCHAR(50) DEFAULT '2026 Live Releases';

-- Genre Dimension
CREATE TABLE IF NOT EXISTS reporting.dim_genres (
    genre_key SERIAL PRIMARY KEY,
    tmdb_genre_id INT UNIQUE NOT NULL,
    genre_name VARCHAR(100) NOT NULL,
    genre_category VARCHAR(50) DEFAULT 'Mainstream'
);

-- Title <-> Genre Bridge Table
CREATE TABLE IF NOT EXISTS reporting.bridge_title_genre (
    title_key BIGINT REFERENCES reporting.dim_titles(title_key) ON DELETE CASCADE,
    genre_key INT REFERENCES reporting.dim_genres(genre_key) ON DELETE CASCADE,
    genre_weight NUMERIC(3,2) DEFAULT 1.0,
    PRIMARY KEY (title_key, genre_key)
);

-- Crew & Cast Dimension
CREATE TABLE IF NOT EXISTS reporting.dim_crew (
    crew_key SERIAL PRIMARY KEY,
    person_name VARCHAR(200) UNIQUE NOT NULL,
    primary_role VARCHAR(50) NOT NULL,
    star_power_tier VARCHAR(30) DEFAULT 'Tier 2 - Known Talent'
);

-- Title <-> Crew Bridge Table
CREATE TABLE IF NOT EXISTS reporting.bridge_title_crew (
    title_key BIGINT REFERENCES reporting.dim_titles(title_key) ON DELETE CASCADE,
    crew_key INT REFERENCES reporting.dim_crew(crew_key) ON DELETE CASCADE,
    billing_order INT DEFAULT 1,
    role VARCHAR(50) DEFAULT 'Director',
    PRIMARY KEY (title_key, crew_key, role)
);

-- Fact Table 1: Ratings Snapshot Fact
CREATE TABLE IF NOT EXISTS reporting.fact_catalog_ratings (
    fact_rating_key BIGSERIAL PRIMARY KEY,
    title_key BIGINT NOT NULL REFERENCES reporting.dim_titles(title_key) ON DELETE CASCADE,
    date_key INT,
    snapshot_date DATE NOT NULL DEFAULT CURRENT_DATE,
    vote_average NUMERIC(3,1) NOT NULL,
    vote_count INT NOT NULL,
    popularity_score NUMERIC(10,3) NOT NULL,
    critic_score NUMERIC(4,1) DEFAULT 75.0,
    days_to_streaming INT DEFAULT 30,
    is_trending BOOLEAN NOT NULL DEFAULT FALSE,
    recorded_at TIMESTAMP NOT NULL DEFAULT NOW()
);

ALTER TABLE reporting.fact_catalog_ratings ADD COLUMN IF NOT EXISTS critic_score NUMERIC(4,1) DEFAULT 75.0;
ALTER TABLE reporting.fact_catalog_ratings ADD COLUMN IF NOT EXISTS date_key INT;

-- Fact Table 2: Streaming Performance & Viewership Hours
CREATE TABLE IF NOT EXISTS reporting.fact_streaming_performance (
    performance_key BIGSERIAL PRIMARY KEY,
    title_key BIGINT NOT NULL REFERENCES reporting.dim_titles(title_key) ON DELETE CASCADE,
    date_key INT NOT NULL,
    global_view_hours_millions NUMERIC(8,2) NOT NULL,
    estimated_unique_viewers_k INT NOT NULL,
    completion_rate_pct NUMERIC(5,2) NOT NULL,
    watch_time_retention_pct NUMERIC(5,2) NOT NULL,
    cost_per_view_hour_usd NUMERIC(8,4) NOT NULL,
    budget_efficiency_ratio NUMERIC(6,2) NOT NULL,
    global_top_10_rank INT,
    recorded_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Indexes for Ultra-Fast Power BI DirectQuery Performance
CREATE INDEX IF NOT EXISTS idx_dim_titles_media_type ON reporting.dim_titles(media_type);
CREATE INDEX IF NOT EXISTS idx_dim_titles_release_year ON reporting.dim_titles(release_year);
CREATE INDEX IF NOT EXISTS idx_dim_titles_date_added ON reporting.dim_titles(netflix_date_added);
CREATE INDEX IF NOT EXISTS idx_dim_titles_era ON reporting.dim_titles(catalog_era);
CREATE INDEX IF NOT EXISTS idx_fact_ratings_title ON reporting.fact_catalog_ratings(title_key);
CREATE INDEX IF NOT EXISTS idx_fact_ratings_date ON reporting.fact_catalog_ratings(snapshot_date);
CREATE INDEX IF NOT EXISTS idx_fact_perf_title ON reporting.fact_streaming_performance(title_key);
CREATE INDEX IF NOT EXISTS idx_fact_perf_date ON reporting.fact_streaming_performance(date_key);

-- -----------------------------------------------------------------------------
-- Power BI Reporting Views
-- -----------------------------------------------------------------------------

-- Master Catalog Pulse View (DirectQuery Friendly)
CREATE VIEW reporting.vw_powerbi_catalog_pulse AS
SELECT
    t.title_key,
    t.netflix_id,
    t.canonical_title AS title,
    t.media_type,
    t.release_year,
    t.catalog_era,
    t.release_date,
    t.netflix_date_added,
    t.maturity_rating,
    t.runtime_minutes,
    t.budget_usd,
    t.original_language,
    t.production_country,
    t.match_confidence,
    COALESCE(r.vote_average, 0.0) AS vote_average,
    COALESCE(r.vote_count, 0) AS vote_count,
    COALESCE(r.popularity_score, 0.0) AS popularity_score,
    COALESCE(r.critic_score, 70.0) AS critic_score,
    COALESCE(r.days_to_streaming, 30) AS days_to_streaming,
    COALESCE(r.is_trending, FALSE) AS is_trending,
    CASE
        WHEN r.vote_average >= 8.0 THEN 'Top Rated (>= 8.0)'
        WHEN r.vote_average >= 6.5 THEN 'Good (6.5 - 7.9)'
        WHEN r.vote_average > 0.0  THEN 'Mixed (< 6.5)'
        ELSE 'Unrated / Pending'
    END AS rating_tier
FROM reporting.dim_titles t
LEFT JOIN (
    SELECT DISTINCT ON (title_key)
        title_key,
        vote_average,
        vote_count,
        popularity_score,
        critic_score,
        days_to_streaming,
        is_trending
    FROM reporting.fact_catalog_ratings
    ORDER BY title_key, snapshot_date DESC, recorded_at DESC
) r ON t.title_key = r.title_key
WHERE t.is_active = TRUE;

-- Viewership & ROI Performance Matrix View
CREATE VIEW reporting.vw_powerbi_performance_matrix AS
SELECT
    t.title_key,
    t.canonical_title AS title,
    t.media_type,
    t.release_year,
    t.catalog_era,
    t.budget_usd,
    p.date_key,
    p.global_view_hours_millions,
    p.estimated_unique_viewers_k,
    p.completion_rate_pct,
    p.cost_per_view_hour_usd,
    p.budget_efficiency_ratio,
    p.global_top_10_rank,
    CASE 
        WHEN p.global_top_10_rank <= 3 THEN 'Top 3 Global Hit'
        WHEN p.global_top_10_rank <= 10 THEN 'Top 10 Charting'
        ELSE 'Broad Catalog'
    END AS streaming_tier
FROM reporting.dim_titles t
INNER JOIN reporting.fact_streaming_performance p ON t.title_key = p.title_key
WHERE t.is_active = TRUE;
