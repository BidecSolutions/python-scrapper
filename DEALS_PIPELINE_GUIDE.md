# Deals/Opportunities Pipeline Guide

## Overview

The Deals Pipeline feature transforms your lead generation platform into a mini-CRM by tracking opportunities from positive replies through to revenue. This feature enables users to:

- Track deals through pipeline stages (New → Contacted → Qualified → Meeting → Proposal → Won/Lost)
- Link deals to leads, companies, campaigns, and segments
- Automatically create deals from positive replies
- View pipeline metrics and win rates
- Track revenue from outbound campaigns

## Backend Implementation

### Data Model

**DealORM** (`app/core/orm_deals.py`):
- Links to workspace, organization, company, lead, owner
- Tracks stage, value, currency, expected close date
- Records source (campaign, segment)
- Tracks won/lost status with timestamps

**DealStage Enum**:
- `new` - Just created
- `contacted` - Initial outreach made
- `qualified` - Positive response received
- `meeting_scheduled` - Meeting booked
- `proposal` - Proposal sent
- `won` - Deal closed successfully
- `lost` - Deal lost

### API Endpoints

1. **List Deals** - `GET /api/deals`
   - Filters: stage, owner, company, segment, search
   - Pagination support
   - Returns deals with full details

2. **Get Deal** - `GET /api/deals/{id}`
   - Returns single deal with all relationships

3. **Create Deal** - `POST /api/deals`
   - Creates new deal
   - Auto-links to lead/company if provided
   - Logs activity and creates notifications

4. **Update Deal** - `PATCH /api/deals/{id}`
   - Updates deal fields
   - Auto-sets won_at/lost_at when stage changes
   - Logs stage change activities

5. **Pipeline Summary** - `GET /api/deals/pipeline/summary`
   - Returns metrics: stage counts, values, win rate, avg days to close

### Automation

**Deal Creation from Positive Replies** (`app/services/deal_automation.py`):
- When a positive reply is detected:
  - Checks for existing open deal
  - Updates stage if deal exists
  - Creates new deal if none exists
  - Creates follow-up task ("Schedule discovery call")
  - Sends notification to deal owner

**Integration Points**:
- Email sync service can call `create_deal_from_positive_reply()`
- Campaign outcomes can trigger deal creation
- Manual creation from Lead Detail panel

## Frontend Implementation

### Pages

1. **Pipeline View** (`/deals`)
   - Kanban board with columns for each stage
   - Drag & drop to change stages (future enhancement)
   - Shows deal value, owner, days open
   - Filters: owner, stage, search

2. **Deal Detail** (`/deals/{id}`)
   - Overview tab: Stage, value, dates, owner, source
   - Timeline tab: Activity history
   - Tasks tab: Deal-specific tasks and notes

### Components

1. **PipelineCard** (`frontend/components/dashboard/PipelineCard.tsx`)
   - Dashboard widget showing:
     - In-progress pipeline value
     - Won deals (last 30 days)
     - Win rate (90 days)
     - Average days to close

2. **Create Deal Button** (in LeadDetailPanel)
   - One-click deal creation from lead
   - Auto-fills lead and company info
   - Navigates to new deal page

### Navigation

- Added "Deals" link to sidebar (TrendingUp icon)
- Accessible from main navigation

## Usage Examples

### Creating a Deal from a Lead

1. Open Lead Detail panel
2. Click "+ Create Deal" button
3. Deal is created with:
   - Name: "{Lead Name} – Opportunity"
   - Stage: "qualified"
   - Linked to lead and company
   - Owner: Current user

### Automatic Deal Creation

When a positive reply is detected (via email sync):

```python
from app.services.deal_automation import create_deal_from_positive_reply

deal = create_deal_from_positive_reply(
    db,
    lead=lead,
    campaign_id=campaign_id,
    segment_id=segment_id,
    reply_text=reply_text,
)
```

This will:
- Create deal if none exists
- Update stage if deal exists
- Create follow-up task
- Send notification

### Updating Deal Stage

```typescript
await apiClient.updateDeal(dealId, {
  stage: "meeting_scheduled",
  expected_close_date: "2025-12-15T00:00:00Z",
});
```

## Integration with Existing Features

- **Leads & Segments**: Feed deals (high-score leads → opportunities)
- **Campaigns**: Track which campaigns generate deals
- **AI Scoring**: High-score leads more likely to create/win deals
- **Inbox Sync**: Auto-create deals from positive replies
- **Tasks & Notes**: Link tasks/notes to deals
- **Activity Timeline**: All deal events logged
- **Notifications**: Deal creation and stage changes trigger notifications
- **Super Admin**: Can view all deals in global activity

## Next Steps

1. **Drag & Drop**: Implement drag-and-drop in Kanban view
2. **Calendar Integration**: Auto-update stage when meeting booked
3. **Deal Playbooks**: Auto-create tasks/sequences when stage changes
4. **Revenue Reporting**: Advanced reporting by segment/campaign/rep
5. **Custom Stages**: Allow workspaces to customize pipeline stages

## Database Migration

Run the migration script:

```bash
python migrate_add_deals.py
```

This creates:
- `deals` table with all columns and indexes
- Adds `deal_id` to `activities`, `lead_tasks`, `lead_notes` tables

