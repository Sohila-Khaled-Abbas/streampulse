-- ==============================================================================
-- StreamPulse: 00_init.sql
-- Database and Schema Initialization
-- ==============================================================================

-- Create application schemas
CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS reporting;

-- The connecting database role owns the schemas it creates. Avoid hard-coded
-- provider-specific role names (for example, `postgres`) so this also works on Neon.
