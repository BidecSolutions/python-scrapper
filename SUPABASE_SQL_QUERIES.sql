-- ============================================================
-- SQL Queries for Supabase SQL Editor
-- ============================================================
-- Copy and paste these queries one at a time into Supabase SQL Editor

-- Query 1: List all databases in your Supabase project
SELECT 
    datname as database_name,
    pg_size_pretty(pg_database_size(datname)) as size
FROM pg_database 
WHERE datistemplate = false 
ORDER BY datname;

-- Query 2: Check current database you're connected to
SELECT current_database() as current_db, current_schema() as current_schema;

-- Query 3: List all schemas in current database
SELECT schema_name 
FROM information_schema.schemata 
WHERE schema_name NOT IN ('pg_catalog', 'information_schema', 'pg_toast')
ORDER BY schema_name;

-- Query 4: List all tables in public schema of current database
SELECT 
    table_name,
    table_type
FROM information_schema.tables 
WHERE table_schema = 'public'
ORDER BY table_name;

-- Query 5: Count tables in public schema
SELECT COUNT(*) as table_count
FROM information_schema.tables 
WHERE table_schema = 'public';

-- Query 6: Check if specific tables exist (test with a known table)
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
  AND table_name IN ('users', 'leads', 'jobs', 'organizations')
ORDER BY table_name;

