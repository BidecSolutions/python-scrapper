# Advanced AI Features Implementation

## Overview

This document describes three major AI/ML features implemented end-to-end:

1. **AI Lead Dossier** - Deep multi-agent research on leads
2. **Decision Makers & Identity Graph** - People + company graph with decision maker scoring
3. **Next Best Action Engine** - RL/bandit recommender for outreach actions

All features are integrated into the existing Lead Detail panel and work seamlessly with the Universal Robots feature.

## 1. AI Lead Dossier

### Database Schema

- **`dossiers`** table with:
  - `status`: pending | running | completed | failed
  - `sections`: JSONB with structured content
  - `started_at`, `completed_at`: Timing tracking
  - `error`: Error messages

### Backend

- **Service**: `app/services/dossier_service.py`
  - `generate_dossier()`: Collects website content, tech stack, social data
  - Calls LLM (Groq) to generate structured sections
  - Returns: overview, offer, audience, digital_presence, social_topics, risks, angle, email, linkedin_dm

- **API Endpoints**:
  - `POST /api/v2/leads/{id}/dossier` - Generate dossier (creates/updates)
  - `GET /api/v2/leads/{id}/dossier` - Get existing dossier

### Frontend

- **Component**: `LeadDossierCard` (already integrated in `LeadDetailPanel`)
- Shows "Generate AI Dossier" button
- Displays sections with copy buttons
- Polls for status updates during generation

## 2. Decision Makers & Identity Graph

### Database Schema

- **`entities`**: Companies, people, domains, social profiles
- **`edges`**: Relationships (works_at, owns, mentions, etc.)
- **`person_scores`**: Decision maker scores per person-company pair
- **`leads.company_entity_id`**: Links leads to company entities

### Backend

- **Service**: `app/services/identity_graph_service.py`
  - `get_or_create_company_entity()`: Creates company entity from lead
  - `add_person_to_company()`: Adds person and creates works_at edge
  - `score_decision_maker()`: Feature-based scoring (title keywords, seniority)
  - `get_key_people_for_lead()`: Returns top decision makers

- **API Endpoints**:
  - `GET /api/v2/leads/{id}/key-people` - Get decision makers

### Frontend

- **Component**: `KeyPeopleCard` (already integrated)
- Shows 3-5 people with:
  - Name, title, LinkedIn link
  - Decision maker score (0-100)
  - Role badge (Primary/Secondary/Influencer)
  - Reason snippet

## 3. Next Best Action Engine

### Database Schema

- **`next_actions`**: Recommended actions per lead
- **`action_outcomes`**: Tracked actions and outcomes (for RL training)
- **`leads.nb_action`**, `nb_action_score`, `nb_action_generated_at`: Cached recommendations

### Backend

- **Service**: `app/services/next_action_service.py`
  - `get_next_action_for_lead()`: Contextual bandit (v1: rule-based, future: ML)
  - Features: smart_score, quality_score, digital_maturity, has_email/phone/social, days_since_created
  - Actions: email_template_a, email_template_b, linkedin_dm, skip
  - `record_action_outcome()`: Records outcomes for training
  - `get_bulk_actions()`: Batch recommendations

- **API Endpoints**:
  - `GET /api/v2/leads/{id}/next-action` - Get recommendation
  - `POST /api/v2/leads/{id}/actions` - Record action outcome
  - `POST /api/v2/leads/bulk-next-actions` - Bulk recommendations

### Frontend

- **Component**: `NextActionCard` (already integrated)
- Shows recommended action at top of Lead Detail panel
- Displays confidence score and reason
- Shows alternatives
- Can record outcomes (future: manual tagging UI)

## Integration Points

### Lead Detail Panel

All three features are integrated into `LeadDetailPanel.tsx`:

1. **Next Best Action** - Top of panel (prominent)
2. **Key People** - After tech stack
3. **Social Insights** - After key people
4. **AI Dossier** - After social insights

### API Client

Frontend API methods in `frontend/lib/api.ts`:
- `getNextAction()`, `recordAction()`, `getBulkActions()`
- `getKeyPeople()`
- `generateDossier()`, `getDossier()`

## Database Migration

Run migration to create/update tables:

```bash
python migrate_v2_advanced_features.py
```

This:
- Creates `person_scores` table
- Updates `dossiers` table (adds status tracking)
- Updates `action_outcomes` (adds suggested_by_ai, outcome_at)
- Adds `company_entity_id`, `nb_action`, `nb_action_score`, `nb_action_generated_at` to `leads`

## Usage Examples

### Generate Dossier

```bash
curl -X POST http://localhost:8002/api/v2/leads/1/dossier
```

### Get Key People

```bash
curl http://localhost:8002/api/v2/leads/1/key-people?limit=5
```

### Get Next Action

```bash
curl http://localhost:8002/api/v2/leads/1/next-action
```

### Record Action Outcome

```bash
curl -X POST http://localhost:8002/api/v2/leads/1/actions \
  -H "Content-Type: application/json" \
  -d '{"action": "email_template_b", "outcome": "replied", "suggested_by_ai": true}'
```

## Next Steps

1. ✅ Database schema created
2. ✅ Backend services implemented
3. ✅ API endpoints created
4. ✅ Frontend components integrated
5. ⏳ Background task queue for async dossier generation
6. ⏳ Enhanced decision maker scoring (GNN/ML)
7. ⏳ ML model training for next best action
8. ⏳ Bulk action UI on Leads list page
9. ⏳ LinkedIn integration for real person data

## Architecture Notes

- **Dossier**: Synchronous generation (can be moved to background tasks)
- **Identity Graph**: Builds incrementally as leads are enriched
- **Next Action**: Rule-based v1, ready for ML upgrade
- All features use existing LLM client (Groq) and database infrastructure

