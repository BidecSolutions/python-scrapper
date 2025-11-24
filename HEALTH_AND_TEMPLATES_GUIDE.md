# Health & Quality Dashboard + Template Library Guide

## Overview

Two powerful features that give you operational visibility and content governance:

1. **Health & Quality Dashboard** - Monitor system health (deliverability, verification, campaigns, jobs)
2. **Template Library & Governance** - Centralized email templates with approval workflows

## Feature 1: Health & Quality Dashboard

### Backend Implementation

**Data Models:**
- `WorkspaceDailyMetricsORM` - Daily aggregated metrics per workspace
- `WorkspaceHealthSnapshotORM` - Health score snapshots over time

**API Endpoints:**
- `GET /api/health` - Workspace health dashboard
  - Returns health score, cards (deliverability, verification, campaigns, jobs), charts
  - Query param: `days` (7, 30, 90)
- `GET /api/health/admin/workspaces` - Super admin global view
  - Returns health summary for all workspaces

**Health Score Calculation:**
- Starts at 100
- Deducts points for:
  - High bounce rate (>10% = -25, >5% = -10)
  - Low verification quality (>30% invalid = -15)
  - Job failures (>5% = -10)
  - LinkedIn failures (>20% = -10)

### Frontend Implementation

**Pages:**
- `/health` - Workspace health dashboard
  - Health score with visual indicator
  - Cards for deliverability, verification, campaigns, jobs
  - Charts for trends (bounce rate, verification valid %, reply rate)
- `/admin/health` - Super admin global health view
  - Table of all workspaces with health scores
  - Color-coded by health (green/yellow/red)

### Usage

1. **View Workspace Health:**
   - Navigate to `/health`
   - Select time period (7/30/90 days)
   - Review health score and individual metrics

2. **Super Admin Global View:**
   - Navigate to `/admin/health`
   - See all workspaces at a glance
   - Identify workspaces with issues

### Next Steps

1. **Daily Aggregation Job:**
   - Create background job to compute daily metrics
   - Aggregate from CampaignLead, verification jobs, playbook jobs, etc.
   - Upsert into `WorkspaceDailyMetricsORM`

2. **Chart Library Integration:**
   - Add Chart.js or Recharts to render trend charts
   - Show bounce rate, verification valid %, reply rate over time

3. **Alerts:**
   - Set up alerts for health score drops
   - Notify workspace admins when metrics degrade

## Feature 2: Template Library & Governance

### Backend Implementation

**Data Models:**
- `TemplateORM` - Email templates with approval workflow
  - Fields: name, description, kind, subject, body, status, locked, tags
  - Status: draft → pending_approval → approved/rejected
- `TemplateGovernanceORM` - Governance rules per workspace
  - Require approval for new templates
  - Restrict to approved only
  - Allow personal templates
  - Require unsubscribe link

**API Endpoints:**
- `GET /api/templates` - List templates (filter by status, kind, tag)
- `GET /api/templates/{id}` - Get template detail
- `POST /api/templates` - Create template (auto-sets status based on governance)
- `PATCH /api/templates/{id}` - Update template (if not locked)
- `POST /api/templates/{id}/approve` - Approve template (admin only)
- `POST /api/templates/{id}/reject` - Reject template (admin only)
- `GET /api/templates/governance` - Get governance settings
- `PATCH /api/templates/governance` - Update governance settings (admin only)

### Frontend Implementation

**Pages:**
- `/templates` - Template library
  - Tabs: All, Draft, Pending, Approved
  - Table with name, kind, status, tags, updated date
  - Actions: View, Approve, Reject
- `/templates/new` - Create template (to be implemented)
- `/templates/{id}` - Edit template (to be implemented)

**Navigation:**
- Added "Templates" link to sidebar (FileText icon)
- Added "Health" link to sidebar (Activity icon)

### Template Workflow

1. **User Creates Template:**
   - Creates draft template
   - If governance requires approval → status = `pending_approval`
   - Otherwise → status = `draft`

2. **Admin Reviews:**
   - Sees pending templates in "Pending" tab
   - Can approve → status = `approved`
   - Can reject → status = `rejected` (with reason)

3. **Campaign Builder:**
   - Shows only `approved` templates (if `restrict_to_approved_only = true`)
   - Otherwise shows approved + personal drafts

### Integration Points

**AI Copilot:**
- Use approved templates as few-shot examples
- Match tone/structure of brand templates
- Suggest which template to use based on segment

**Campaign Builder:**
- Filter templates by status based on governance
- Show template performance metrics
- Enforce unsubscribe requirement if set

### Next Steps

1. **Template Editor:**
   - Create `/templates/new` and `/templates/{id}` pages
   - Rich text editor with variable hints ({{first_name}}, {{company}}, etc.)
   - Preview functionality

2. **Governance Settings UI:**
   - Add to workspace settings page
   - Toggle switches for each rule
   - Help text explaining each setting

3. **Template Performance:**
   - Track which templates are used in campaigns
   - Show open/reply/bounce rates per template
   - Compare approved vs ad-hoc templates

4. **Variable System:**
   - Define available variables
   - Validate templates contain required variables
   - Show variable hints in editor

## Database Migration

Run the migration script:

```bash
python migrate_add_health_templates.py
```

This creates:
- `workspace_daily_metrics` table
- `workspace_health_snapshots` table
- `templates` table
- `template_governance` table

## Summary

Both features are now implemented with:

✅ **Backend:**
- Data models for health metrics and templates
- API endpoints for health dashboard and template management
- Health score calculation logic
- Template approval workflow

✅ **Frontend:**
- Health dashboard page (`/health`)
- Super admin global health page (`/admin/health`)
- Template library page (`/templates`)
- Navigation links added

✅ **Database:**
- All tables created with proper indexes
- Migration script ready

**Remaining Work:**
1. Daily aggregation job for health metrics
2. Chart library integration for trend visualization
3. Template editor UI (create/edit pages)
4. Governance settings UI in workspace settings
5. Template performance tracking

