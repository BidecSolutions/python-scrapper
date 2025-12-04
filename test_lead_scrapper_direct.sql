-- ============================================================
-- SQL Queries to Run AFTER Switching to Lead_scrapper Database
-- ============================================================
-- IMPORTANT: First, use the "Primary Database" dropdown to select "Lead_scrapper"
-- Then run these queries one by one

-- Query 1: Verify you're in the correct database
SELECT current_database() as current_db;
-- Expected result: Lead_scrapper

-- Query 2: Count tables in public schema
SELECT COUNT(*) as table_count
FROM information_schema.tables 
WHERE table_schema = 'public';
-- Expected result: 75

-- Query 3: List all tables (first 20)
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
ORDER BY table_name
LIMIT 20;

-- Query 4: List all tables (complete list)
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
ORDER BY table_name;

-- Query 5: Check specific important tables exist
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
  AND table_name IN (
    'users', 
    'organizations', 
    'leads', 
    'jobs', 
    'duplicate_groups',
    'duplicate_leads',
    'saved_views'
  )
ORDER BY table_name;

-- Query 6: Get table count by category
SELECT 
    CASE 
        WHEN table_name LIKE '%user%' OR table_name LIKE '%auth%' THEN 'Authentication'
        WHEN table_name LIKE '%lead%' THEN 'Leads'
        WHEN table_name LIKE '%job%' THEN 'Jobs'
        WHEN table_name LIKE '%deal%' THEN 'Deals'
        WHEN table_name LIKE '%campaign%' THEN 'Campaigns'
        WHEN table_name LIKE '%duplicate%' THEN 'Duplicates'
        WHEN table_name LIKE '%saved%' OR table_name LIKE '%view%' THEN 'Views'
        ELSE 'Other'
    END as category,
    COUNT(*) as count
FROM information_schema.tables 
WHERE table_schema = 'public'
GROUP BY category
ORDER BY count DESC;

