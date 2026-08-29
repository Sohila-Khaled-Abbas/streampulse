-- ==============================================================================
-- StreamPulse: 02_reporting.sql
-- Enterprise Kimball Galaxy Constellation Schema & Power BI DirectQuery Layer
-- ==============================================================================

-- Drop existing reporting views
DROP VIEW IF EXISTS reporting.vw_powerbi_galaxy_master CASCADE;
DROP VIEW IF EXISTS reporting.vw_powerbi_financial_roi CASCADE;
DROP VIEW IF EXISTS reporting.vw_powerbi_performance_matrix CASCADE;
DROP VIEW IF EXISTS reporting.vw_powerbi_catalog_pulse CASCADE;

-- -----------------------------------------------------------------------------
-- 1. Conformed Dimensions
-- -----------------------------------------------------------------------------

-- Calendar Dimension
CREATE TABLE IF NOT EXISTS reporting.dim_date (
    date_key INT PRIMARY KEY,                       -- Format: YYYYMMDD (e.g. 20260227)
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
    runtime_tier VARCHAR(50) DEFAULT 'Standard Feature (45-100m)',
    maturity_category VARCHAR(50) DEFAULT 'Adult / Mature (18+)',
    match_confidence NUMERIC(5,2) NOT NULL DEFAULT 100.0,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Genre Dimension
CREATE TABLE IF NOT EXISTS reporting.dim_genres (
    genre_key SERIAL PRIMARY KEY,
    tmdb_genre_id INT UNIQUE NOT NULL,
    genre_name VARCHAR(100) NOT NULL,
    genre_category VARCHAR(50) DEFAULT 'Mainstream Commercial',
    sort_order INT NOT NULL DEFAULT 1
);

-- Territory Dimension
CREATE TABLE IF NOT EXISTS reporting.dim_territory (
    territory_key SERIAL PRIMARY KEY,
    territory_code VARCHAR(5) UNIQUE NOT NULL,
    territory_name VARCHAR(100) NOT NULL,
    region_group VARCHAR(50) NOT NULL,
    currency_code VARCHAR(10) NOT NULL DEFAULT 'USD',
    market_maturity VARCHAR(50) DEFAULT 'Mature Hub',
    streaming_penetration_pct NUMERIC(4,2) DEFAULT 0.75
);

-- Talent & Crew Dimension
CREATE TABLE IF NOT EXISTS reporting.dim_talent_crew (
    crew_key SERIAL PRIMARY KEY,
    person_name VARCHAR(200) UNIQUE NOT NULL,
    primary_role VARCHAR(50) NOT NULL DEFAULT 'Director',
    star_power_tier VARCHAR(50) DEFAULT 'Tier 2 - Established Talent'
);

-- -----------------------------------------------------------------------------
-- 2. Bridge Tables (Many-to-Many Relationships)
-- -----------------------------------------------------------------------------

-- Title <-> Genre Bridge
CREATE TABLE IF NOT EXISTS reporting.bridge_title_genre (
    title_key BIGINT REFERENCES reporting.dim_titles(title_key) ON DELETE CASCADE,
    genre_key INT REFERENCES reporting.dim_genres(genre_key) ON DELETE CASCADE,
    genre_weight NUMERIC(3,2) DEFAULT 1.00,
    PRIMARY KEY (title_key, genre_key)
);

-- Title <-> Talent Bridge
CREATE TABLE IF NOT EXISTS reporting.bridge_title_talent (
    title_key BIGINT REFERENCES reporting.dim_titles(title_key) ON DELETE CASCADE,
    crew_key INT REFERENCES reporting.dim_talent_crew(crew_key) ON DELETE CASCADE,
    billing_order INT DEFAULT 1,
    PRIMARY KEY (title_key, crew_key)
);

-- -----------------------------------------------------------------------------
-- 3. Multi-Grain Constellation Fact Tables
-- -----------------------------------------------------------------------------

-- Fact 1: Periodic Ratings Snapshot Fact
CREATE TABLE IF NOT EXISTS reporting.fact_catalog_ratings (
    fact_rating_key BIGSERIAL PRIMARY KEY,
    title_key BIGINT NOT NULL REFERENCES reporting.dim_titles(title_key) ON DELETE CASCADE,
    date_key INT REFERENCES reporting.dim_date(date_key),
    snapshot_date DATE NOT NULL DEFAULT CURRENT_DATE,
    vote_average NUMERIC(3,1) NOT NULL,
    vote_count INT NOT NULL,
    popularity_score NUMERIC(10,3) DEFAULT 0.0,
    critic_score NUMERIC(4,1) DEFAULT 75.0,
    days_to_streaming INT DEFAULT 30,
    is_trending BOOLEAN NOT NULL DEFAULT FALSE,
    recorded_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Fact 2: Granular Streaming Performance Telemetry
CREATE TABLE IF NOT EXISTS reporting.fact_streaming_performance (
    performance_key BIGSERIAL PRIMARY KEY,
    title_key BIGINT NOT NULL REFERENCES reporting.dim_titles(title_key) ON DELETE CASCADE,
    date_key INT NOT NULL REFERENCES reporting.dim_date(date_key),
    territory_key INT REFERENCES reporting.dim_territory(territory_key),
    device_category VARCHAR(50) NOT NULL DEFAULT 'Connected TV',
    global_view_hours_millions NUMERIC(10,2) NOT NULL,
    avg_completion_pct NUMERIC(5,2) NOT NULL,
    subscribers_reached_thousands INT NOT NULL,
    cost_per_view_hour_usd NUMERIC(8,4) DEFAULT 0.05,
    recorded_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Fact 3: Production Budget & Financial ROI
CREATE TABLE IF NOT EXISTS reporting.fact_financial_roi (
    financial_key BIGSERIAL PRIMARY KEY,
    title_key BIGINT NOT NULL REFERENCES reporting.dim_titles(title_key) ON DELETE CASCADE,
    date_key INT REFERENCES reporting.dim_date(date_key),
    production_budget_usd NUMERIC(15,2) NOT NULL,
    worldwide_gross_usd NUMERIC(15,2) NOT NULL,
    financial_roi_tier VARCHAR(50) NOT NULL DEFAULT 'Underperformer',
    recorded_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- -----------------------------------------------------------------------------
-- 4. High-Performance Indexes for DirectQuery Acceleration
-- -----------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_dim_titles_media_type ON reporting.dim_titles(media_type);
CREATE INDEX IF NOT EXISTS idx_dim_titles_release_year ON reporting.dim_titles(release_year);
CREATE INDEX IF NOT EXISTS idx_dim_titles_era ON reporting.dim_titles(catalog_era);
CREATE INDEX IF NOT EXISTS idx_fact_ratings_composite ON reporting.fact_catalog_ratings(title_key, date_key);
CREATE INDEX IF NOT EXISTS idx_fact_perf_composite ON reporting.fact_streaming_performance(title_key, date_key, territory_key);
CREATE INDEX IF NOT EXISTS idx_fact_roi_composite ON reporting.fact_financial_roi(title_key, date_key);

-- -----------------------------------------------------------------------------
-- 5. Power BI DirectQuery Reporting Views
-- -----------------------------------------------------------------------------

-- View 1: Master Catalog Pulse View
CREATE VIEW reporting.vw_powerbi_catalog_pulse AS
SELECT
    t.title_key,
    t.netflix_id,
    t.canonical_title AS title,
    t.media_type,
    t.release_year,
    t.catalog_era,
    t.maturity_rating,
    t.runtime_minutes,
    t.runtime_tier,
    t.maturity_category,
    COALESCE(r.vote_average, 0.0) AS vote_average,
    COALESCE(r.vote_count, 0) AS vote_count,
    COALESCE(r.critic_score, 70.0) AS critic_score,
    -- Bayesian Weighted Score (m=25000, C=7.0)
    ROUND(((COALESCE(r.vote_count, 0) * COALESCE(r.vote_average, 7.0) + 25000.0 * 7.0) / (COALESCE(r.vote_count, 0) + 25000.0))::numeric, 2) AS bayesian_weighted_score,
    COALESCE(r.is_trending, FALSE) AS is_trending
FROM reporting.dim_titles t
LEFT JOIN (
    SELECT DISTINCT ON (title_key)
        title_key,
        vote_average,
        vote_count,
        critic_score,
        is_trending
    FROM reporting.fact_catalog_ratings
    ORDER BY title_key, snapshot_date DESC, recorded_at DESC
) r ON t.title_key = r.title_key
WHERE t.is_active = TRUE;

-- View 2: Financial ROI & Box Office Performance
CREATE VIEW reporting.vw_powerbi_financial_roi AS
SELECT
    t.title_key,
    t.canonical_title AS title,
    t.media_type,
    t.catalog_era,
    f.production_budget_usd,
    f.worldwide_gross_usd,
    (f.worldwide_gross_usd - f.production_budget_usd) AS net_profit_usd,
    CASE 
        WHEN f.production_budget_usd > 0 THEN ROUND((f.worldwide_gross_usd / f.production_budget_usd)::numeric, 2)
        ELSE 0.0
    END AS financial_roi_multiplier,
    f.financial_roi_tier
FROM reporting.dim_titles t
INNER JOIN reporting.fact_financial_roi f ON t.title_key = f.title_key
WHERE t.is_active = TRUE;

-- View 3: Master Galaxy Aggregation View
CREATE VIEW reporting.vw_powerbi_galaxy_master AS
SELECT
    t.title_key,
    t.canonical_title AS title,
    t.media_type,
    t.catalog_era,
    d.year AS streaming_year,
    d.quarter_name,
    COALESCE(ter.territory_name, 'Global') AS territory_name,
    p.device_category,
    p.global_view_hours_millions,
    p.avg_completion_pct,
    p.subscribers_reached_thousands,
    COALESCE(r.vote_average, 7.0) AS vote_average,
    COALESCE(f.production_budget_usd, 0.0) AS production_budget_usd
FROM reporting.dim_titles t
LEFT JOIN reporting.fact_streaming_performance p ON t.title_key = p.title_key
LEFT JOIN reporting.dim_date d ON p.date_key = d.date_key
LEFT JOIN reporting.dim_territory ter ON p.territory_key = ter.territory_key
LEFT JOIN (
    SELECT DISTINCT ON (title_key) title_key, vote_average FROM reporting.fact_catalog_ratings ORDER BY title_key, snapshot_date DESC
) r ON t.title_key = r.title_key
LEFT JOIN reporting.fact_financial_roi f ON t.title_key = f.title_key
WHERE t.is_active = TRUE;
