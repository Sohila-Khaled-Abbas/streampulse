-- ==============================================================================
-- StreamPulse: 01_staging.sql
-- Raw Staging Landing Tables
-- ==============================================================================

-- Staging table for Netflix Catalog extractions
CREATE TABLE IF NOT EXISTS staging.stg_netflix_titles (
    netflix_id VARCHAR(50) PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    title_type VARCHAR(20),
    synopsis TEXT,
    release_year INT,
    date_added TIMESTAMP,
    runtime_seconds INT,
    maturity_rating VARCHAR(20),
    raw_json JSONB,
    extracted_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Staging table for TMDb enriched metadata
CREATE TABLE IF NOT EXISTS staging.stg_tmdb_metadata (
    tmdb_id INT PRIMARY KEY,
    media_type VARCHAR(20) NOT NULL,
    title VARCHAR(500) NOT NULL,
    original_title VARCHAR(500),
    release_date DATE,
    vote_average NUMERIC(3,1),
    vote_count INT,
    popularity NUMERIC(10,3),
    genres_json JSONB,
    cast_json JSONB,
    raw_json JSONB,
    extracted_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Staging indexes for efficient joining and lookup
CREATE INDEX IF NOT EXISTS idx_stg_netflix_title ON staging.stg_netflix_titles(title);
CREATE INDEX IF NOT EXISTS idx_stg_tmdb_title ON staging.stg_tmdb_metadata(title);
