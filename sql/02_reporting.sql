-- ==============================================================================
-- StreamPulse: 02_reporting.sql
-- Dimensional Star Schema and Reporting Views for Power BI DirectQuery
-- ==============================================================================

-- Conformed Title Dimension
CREATE TABLE IF NOT EXISTS reporting.dim_titles (
    title_key BIGSERIAL PRIMARY KEY,
    netflix_id VARCHAR(50) UNIQUE NOT NULL,
    tmdb_id INT,
    canonical_title VARCHAR(500) NOT NULL,
    media_type VARCHAR(20) NOT NULL,
    release_year INT,
    release_date DATE,
    netflix_date_added DATE NOT NULL,
    maturity_rating VARCHAR(20),
    runtime_minutes INT,
    match_confidence NUMERIC(5,2) NOT NULL DEFAULT 100.0,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Genre Dimension
CREATE TABLE IF NOT EXISTS reporting.dim_genres (
    genre_key SERIAL PRIMARY KEY,
    tmdb_genre_id INT UNIQUE NOT NULL,
    genre_name VARCHAR(100) NOT NULL
);

-- Title <-> Genre Bridge Table
CREATE TABLE IF NOT EXISTS reporting.bridge_title_genre (
    title_key BIGINT REFERENCES reporting.dim_titles(title_key) ON DELETE CASCADE,
    genre_key INT REFERENCES reporting.dim_genres(genre_key) ON DELETE CASCADE,
    PRIMARY KEY (title_key, genre_key)
);

-- Fact Table: Catalog Ratings & Velocity Snapshot
CREATE TABLE IF NOT EXISTS reporting.fact_catalog_ratings (
    fact_rating_key BIGSERIAL PRIMARY KEY,
    title_key BIGINT NOT NULL REFERENCES reporting.dim_titles(title_key) ON DELETE CASCADE,
    snapshot_date DATE NOT NULL DEFAULT CURRENT_DATE,
    vote_average NUMERIC(3,1) NOT NULL,
    vote_count INT NOT NULL,
    popularity_score NUMERIC(10,3) NOT NULL,
    days_to_streaming INT,
    is_trending BOOLEAN NOT NULL DEFAULT FALSE,
    recorded_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Performance Indexes for Power BI DirectQuery
CREATE INDEX IF NOT EXISTS idx_dim_titles_media_type ON reporting.dim_titles(media_type);
CREATE INDEX IF NOT EXISTS idx_dim_titles_release_year ON reporting.dim_titles(release_year);
CREATE INDEX IF NOT EXISTS idx_dim_titles_date_added ON reporting.dim_titles(netflix_date_added);
CREATE INDEX IF NOT EXISTS idx_fact_ratings_title ON reporting.fact_catalog_ratings(title_key);
CREATE INDEX IF NOT EXISTS idx_fact_ratings_date ON reporting.fact_catalog_ratings(snapshot_date);
CREATE INDEX IF NOT EXISTS idx_fact_ratings_trending ON reporting.fact_catalog_ratings(is_trending);

-- Power BI Reporting DirectQuery View
DROP VIEW IF EXISTS reporting.vw_powerbi_catalog_pulse CASCADE;

CREATE VIEW reporting.vw_powerbi_catalog_pulse AS
SELECT
    t.title_key,
    t.netflix_id,
    t.canonical_title AS title,
    t.media_type,
    t.release_year,
    CASE
        WHEN t.release_year = 2026 THEN '2026 Live Releases'
        WHEN t.release_year IN (2024, 2025) THEN '2024-2025 Modern'
        ELSE 'Historical Archive (<2024)'
    END AS catalog_era,
    t.release_date,
    t.netflix_date_added,
    t.maturity_rating,
    t.runtime_minutes,
    t.match_confidence,
    COALESCE(r.vote_average, 0.0) AS vote_average,
    COALESCE(r.vote_count, 0) AS vote_count,
    COALESCE(r.popularity_score, 0.0) AS popularity_score,
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
        days_to_streaming,
        is_trending
    FROM reporting.fact_catalog_ratings
    ORDER BY title_key, snapshot_date DESC, recorded_at DESC
) r ON t.title_key = r.title_key
WHERE t.is_active = TRUE;
