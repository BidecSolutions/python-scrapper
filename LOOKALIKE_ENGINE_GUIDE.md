# AI Lookalike & Expansion Engine Guide

## Overview

The AI Lookalike Engine uses machine learning to find similar leads/companies based on your best performers. Instead of guessing niches, it learns from what's already working and finds more of the same.

## How It Works

1. **Input Set**: User selects a segment, list, or campaign with "good" leads (replied, won, high score)
2. **Profile Building**: System computes embeddings for positive examples and creates a centroid profile
3. **Similarity Search**: Finds other leads/companies with similar embeddings using cosine similarity
4. **Ranking**: Returns candidates sorted by similarity score (0-1)
5. **Output**: User can review and add candidates to lists/segments

## Backend Implementation

### Data Models

**LookalikeJobORM** (`app/core/orm_lookalike.py`):
- Tracks lookalike job execution
- Stores source (segment/list/campaign)
- Stores profile embedding (centroid of positive examples)
- Status: pending → running → completed/failed

**LookalikeCandidateORM**:
- Stores individual lookalike results
- Links to lead/company
- Stores similarity score (0-1)
- Stores reason vector (which features contributed most)

### Embedding Service

**Feature Engineering** (`app/services/lookalike_embedding.py`):
- **Company Embedding**: Industry, size, geography, tech stack, intent signals
- **Lead Embedding**: Company features + title/seniority, role family, engagement signals
- **Profile Embedding**: Weighted centroid of positive example embeddings
- **Similarity**: Cosine similarity between profile and candidate embeddings

**Embedding Dimensions**: 256 (configurable via `EMBEDDING_DIM`)

### Lookalike Service

**Profile Building** (`app/services/lookalike_service.py`):
- Collects positive leads from segment/list
- Computes embeddings for each
- Creates weighted centroid (higher weight for "won" vs "good" vs high score)
- Stores profile embedding in job

**Finding Lookalikes**:
- Queries all leads in workspace (excluding positive examples)
- Computes embedding for each candidate
- Calculates cosine similarity with profile
- Filters by minimum score (default 0.7)
- Sorts by score descending
- Returns top N candidates

### API Endpoints

1. **Create Lookalike Job** - `POST /api/lookalike/jobs`
   - Body: `source_segment_id`, `source_list_id`, or `source_campaign_id`
   - Optional: `min_score`, `max_results`, `filters`
   - Returns job with status "pending"
   - Background task processes job

2. **Get Lookalike Job** - `GET /api/lookalike/jobs/{id}`
   - Returns job with candidates (paginated)
   - Includes similarity scores and reason vectors

3. **List Lookalike Jobs** - `GET /api/lookalike/jobs`
   - Returns all jobs for workspace

## Frontend Implementation

### Pages

1. **Lookalike Jobs List** (`/lookalike/jobs`):
   - Table of all lookalike jobs
   - Shows status, source, examples count, candidates found
   - Click to view results

2. **Lookalike Results** (`/lookalike/jobs/{id}`):
   - Shows job status and progress
   - Table of candidates with:
     - Similarity score (0-100) with visual bar
     - Lead link
     - Reason vector (why similar: industry, size, tech, geo)
   - Bulk selection to add to list
   - Auto-refreshes if job is running

### Components

**LookalikeCard** (`frontend/components/segments/LookalikeCard.tsx`):
- Shows on segment/campaign pages
- Button to "Find Lookalike Leads"
- Displays positive example count

## Usage Flow

1. **User on Segment Page**:
   - Sees "AI Lookalikes" card
   - Clicks "Find Lookalike Leads"
   - Job is created and starts processing

2. **Job Processing** (background):
   - Collects positive leads from segment
   - Builds profile embedding
   - Searches for similar leads
   - Saves candidates with scores

3. **User Views Results**:
   - Sees ranked list of candidates
   - Can filter by min score
   - Selects candidates
   - Adds to new list or existing segment

## Integration Points

- **Segments**: Trigger lookalikes from high-performing segments
- **Campaigns**: Find lookalikes from campaigns with high reply rates
- **Lead Scoring**: Lookalike score can be added as feature to overall lead score
- **NBA (Next Best Action)**: Suggest creating lookalike segment when campaign succeeds
- **Templates & AI**: Use templates that worked for source segment on lookalikes

## Technical Details

### Embedding Computation

**Company Features** (indices 0-128):
- Industry (0-20): One-hot encoding
- Size (20-25): Bucket encoding
- Geography (25-55): Country/region encoding
- Tech stack (55-75): Binary flags
- Intent signals (75-95): Binary flags
- Remaining: Projection of existing features

**Lead Features** (indices 128-256):
- Seniority level (128-133): C-level, VP, Director, Manager, IC
- Role family (133-142): Sales, Marketing, Product, Engineering, HR
- Title keywords (142-162): Hash-based encoding
- Engagement (162-167): Fit label, health score, ML score

**Combined**: 70% company + 30% lead features

### Similarity Scoring

- Uses cosine similarity (normalized dot product)
- Returns score 0-1 (1 = identical, 0 = completely different)
- Reason vector breaks down similarity by feature category

## Performance Considerations

- **Current**: Processes up to 10,000 leads per job
- **Future**: Use vector DB (pgvector, Pinecone, Qdrant) for faster search
- **Caching**: Profile embeddings can be cached for similar jobs
- **Batch Processing**: Process candidates in batches for large workspaces

## Next Steps

1. **Vector Database Integration**:
   - Use pgvector for PostgreSQL
   - Or external vector DB (Pinecone, Qdrant)
   - Enables fast similarity search on millions of leads

2. **Advanced ML**:
   - Train MLP model on reply/won outcomes
   - Use graph neural networks (GNN) for company relationships
   - Fine-tune embeddings based on user feedback

3. **Feature Expansion**:
   - Add more company features (funding, revenue, growth signals)
   - Add more lead features (social activity, content engagement)
   - Use website text embeddings (sentence transformers)

4. **UI Enhancements**:
   - Visual similarity comparison (side-by-side)
   - "Why similar" detailed breakdown
   - Preview candidate before adding to list
   - Bulk actions (add all, filter by score, etc.)

## Database Migration

Run the migration script:

```bash
python migrate_add_lookalike.py
```

This creates:
- `lookalike_jobs` table
- `lookalike_candidates` table
- All required indexes

