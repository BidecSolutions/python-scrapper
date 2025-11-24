# Universal Robots Implementation

## Overview

This document describes the Universal Robots feature - an AI-powered scraping system that allows users to create custom scrapers from natural language prompts, test them on sample URLs, run them on multiple URLs, and import results as leads.

## Architecture

### Backend Components

1. **Database Schema** (`app/core/orm_robots.py`)
   - `robots`: Robot definitions (schema, workflow_spec)
   - `robot_runs`: Execution runs
   - `robot_run_urls`: URLs to process
   - `robot_run_rows`: Extracted data rows

2. **Services**
   - `app/services/robots_ai.py`: LLM-powered robot generation
   - `app/services/robots_engine.py`: Workflow execution engine
   - `app/services/geocoding.py`: OpenCage geocoding integration

3. **API Endpoints** (`app/api/routes_robots.py`)
   - `POST /api/robots/ai`: Generate robot from prompt
   - `POST /api/robots`: Save robot
   - `GET /api/robots`: List robots
   - `GET /api/robots/{id}`: Get robot details
   - `POST /api/robots/{id}/test`: Test on sample URL
   - `POST /api/robots/{id}/runs`: Create and run robot
   - `GET /api/robot-runs/{id}/rows`: Get run results
   - `POST /api/robot-runs/{id}/import-leads`: Import as leads

4. **Geocoding API** (`app/api/routes_geo.py`)
   - `GET /api/geo/search`: Geocode location text
   - `GET /api/geo/reverse`: Reverse geocode lat/lng

### Frontend Components (To Be Implemented)

1. **Pages**
   - `/robots`: Robots list
   - `/robots/new`: AI robot builder wizard
   - `/robots/[id]`: Robot detail & runs
   - `/robots/runs/[runId]`: Run results view

2. **Components**
   - `RobotBuilderWizard`: Multi-step robot creation
   - `RobotTestPreview`: Test results preview
   - `RobotRunResults`: Data table with export/import
   - `ImportLeadsModal`: Field mapping interface

## User Flow

1. **Create Robot**
   - User describes what they want in natural language
   - AI generates schema and workflow
   - User can edit fields and test on sample URL
   - Save robot

2. **Run Robot**
   - Paste URLs or upload CSV
   - Robot processes URLs in background
   - View progress and results

3. **Import Leads**
   - Map robot fields to lead fields
   - Import selected/all rows
   - Leads trigger AI scoring/enrichment

## Configuration

### Environment Variables

```bash
# OpenCage Geocoding (required for location features)
OPENCAGE_API_KEY=your_key_here

# Optional: Google Geocoding (for premium features)
GOOGLE_GEOCODING_API_KEY=your_key_here

# LLM for robot generation (uses existing GROQ_API_KEY)
GROQ_API_KEY=your_key_here
```

### Security Note

⚠️ **IMPORTANT**: The OpenCage API key has been added to `.env`. 

**You should:**
1. Revoke the exposed key and generate a new one
2. Never commit `.env` to version control
3. Use environment variables in production (Docker, systemd, etc.)

## Database Migration

Run the migration script to create tables:

```bash
python migrate_robots_tables.py
```

This creates:
- `robots` table
- `robot_runs` table
- `robot_run_urls` table
- `robot_run_rows` table
- Adds `source_robot_run_id` column to `leads` table

## Next Steps

1. ✅ Backend API endpoints created
2. ✅ Database schema created
3. ✅ Geocoding service integrated
4. ⏳ Frontend UI components (in progress)
5. ⏳ Background task queue for async processing
6. ⏳ Enhanced error handling and retries
7. ⏳ CSV upload for URLs
8. ⏳ Advanced workflow features (pagination, JavaScript rendering)

## API Usage Examples

### Generate Robot from Prompt

```bash
curl -X POST http://localhost:8000/api/robots/ai \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Extract restaurant name, website, email, phone, rating from Yelp listing pages",
    "sample_url": "https://www.yelp.com/search?find_desc=Restaurants&find_loc=Karachi"
  }'
```

### Test Robot

```bash
curl -X POST http://localhost:8000/api/robots/1/test \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.yelp.com/search?find_desc=Restaurants&find_loc=Karachi"
  }'
```

### Run Robot on URLs

```bash
curl -X POST http://localhost:8000/api/robots/1/runs \
  -H "Content-Type: application/json" \
  -d '{
    "urls": [
      "https://www.yelp.com/search?find_desc=Restaurants&find_loc=Karachi",
      "https://www.yelp.com/search?find_desc=Restaurants&find_loc=Lahore"
    ]
  }'
```

### Import as Leads

```bash
curl -X POST http://localhost:8000/api/robot-runs/1/import-leads \
  -H "Content-Type: application/json" \
  -d '{
    "field_mapping": {
      "name": "name",
      "website": "website",
      "email": "email",
      "phone": "phone",
      "city": "city"
    }
  }'
```

## Integration with Existing Features

- **Leads**: Imported robot rows become leads with `source="robot"` and `source_robot_run_id`
- **AI Scoring**: New leads automatically trigger scoring pipeline
- **Playbooks**: Robot-imported leads contribute to niche/location playbooks
- **Segments**: Leads can be segmented by robot source
- **Geocoding**: Address fields are geocoded using OpenCage

