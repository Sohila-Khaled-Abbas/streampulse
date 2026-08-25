-- ==============================================================================
-- StreamPulse: 00_init.sql
-- Database and Schema Initialization
-- ==============================================================================

-- Create application schemas
CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS reporting;

-- Enable UUID & Trigram extensions for fuzzy matching & text search in PostgreSQL
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Grant permissions to default user
GRANT ALL ON SCHEMA staging TO postgres;
GRANT ALL ON SCHEMA reporting TO postgres;
