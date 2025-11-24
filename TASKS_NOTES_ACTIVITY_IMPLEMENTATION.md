# Tasks & Notes + Activity Timeline Implementation

## ✅ What's Been Implemented

### 1. Tasks & Notes Models (`app/core/orm_tasks_notes.py`)

**LeadNoteORM:**
- `content` (Text) - Note content up to 2000 chars
- `user_id` - Who created the note
- `lead_id` - Related lead
- `workspace_id` - Workspace scoping

**LeadTaskORM:**
- `title` (String) - Task title
- `type` (Enum) - TaskType: follow_up, call, email, enrich, add_to_campaign, custom
- `status` (Enum) - TaskStatus: open, done, cancelled
- `due_at` (DateTime) - Optional due date
- `description` (Text) - Optional description
- `assigned_to_user_id` - Can assign to different user
- `completed_at` - Set when status changes to done

### 2. Activity Timeline Model (`app/core/orm_activity.py`)

**ActivityORM:**
- Generic event log table
- `type` (ActivityType enum) - Event type
- `actor_user_id` - Who performed the action
- Related object IDs: `lead_id`, `list_id`, `campaign_id`, `task_id`, `job_id`, `note_id`
- `meta` (JSON) - Flexible metadata for event details

**ActivityType Enum:**
- Lead events: lead_created, lead_updated, lead_added_to_list, etc.
- Email events: email_found, email_verified
- Campaign events: campaign_sent, campaign_event, etc.
- Task events: task_created, task_completed
- Note events: note_added
- Playbook, list, job, integration, workspace events

### 3. Activity Logger Service (`app/services/activity_logger.py`)

**`log_activity()` function:**
- Centralized logging for all events
- Takes organization_id, workspace_id, type, actor, related objects, metadata
- Creates ActivityORM record and commits

### 4. Task from NBA Helper (`app/services/task_from_nba.py`)

**`ensure_task_from_next_action()` function:**
- Creates tasks automatically from Next Best Action
- Handles: schedule_follow_up, review_or_enrich, add_to_campaign
- Prevents duplicate tasks
- Logs activity when task is created

### 5. API Endpoints

**Notes (`app/api/routes_tasks_notes.py`):**
- `GET /api/leads/{lead_id}/notes` - List notes for a lead
- `POST /api/leads/{lead_id}/notes` - Create a note

**Tasks:**
- `GET /api/leads/{lead_id}/tasks` - List tasks for a lead
- `POST /api/leads/{lead_id}/tasks` - Create a task
- `PATCH /api/tasks/{task_id}` - Update task (status, title, due date, etc.)
- `GET /api/tasks` - Get all tasks (workspace-scoped, with filters)

**Activity (`app/api/routes_activity.py`):**
- `GET /api/leads/{lead_id}/activity` - Get activity timeline for a lead
- `GET /api/activity` - Get workspace activity feed

## 🔄 Next Steps

### 1. Integrate Activity Logging Throughout System

Add `log_activity()` calls in:

**Lead Creation:**
```python
# In linkedin_capture, company_search, CSV import
log_activity(
    db=db,
    organization_id=org.id,
    workspace_id=workspace_id,
    type=ActivityType.lead_created,
    actor_user_id=user_id,
    lead_id=lead.id,
    meta={"source": "linkedin_extension"},
)
```

**Email Operations:**
```python
# When email is found/verified
log_activity(
    db=db,
    organization_id=org.id,
    workspace_id=workspace_id,
    type=ActivityType.email_verified,
    lead_id=lead.id,
    meta={"email": email, "status": "valid", "confidence": 0.95},
)
```

**List Operations:**
```python
# When lead is added to list
log_activity(
    db=db,
    organization_id=org.id,
    workspace_id=workspace_id,
    type=ActivityType.lead_added_to_list,
    actor_user_id=user_id,
    lead_id=lead.id,
    list_id=list_id,
    meta={"list_name": list.name},
)
```

**Campaign Operations:**
```python
# When campaign results are imported
log_activity(
    db=db,
    organization_id=org.id,
    workspace_id=workspace_id,
    type=ActivityType.campaign_outcome_imported,
    lead_id=lead.id,
    campaign_id=campaign_id,
    meta={"event": "replied", "campaign_name": campaign.name},
)
```

### 2. Frontend Integration

**Lead Detail Page:**
- Add "Notes & Tasks" section/sidebar
- Show open tasks first, then completed
- Add note textarea with "Add note" button
- Show activity timeline tab/section

**Tasks Page:**
- New page: `/tasks`
- Filters: My tasks / All, Status, Due date (overdue/today/this week)
- Table: Task, Lead, Type, Due date, Assigned to, Status
- Actions: Mark as done, Edit, Delete

**Activity Feed:**
- Dashboard widget or dedicated page
- Show workspace activity with filters
- Group by date, show icons per activity type

### 3. NBA Integration

Add "Create task from suggestion" button in Lead Detail:
```typescript
// When user clicks "Create task" from NBA card
await api.post(`/api/leads/${leadId}/tasks`, {
  title: "Follow up after reply",
  type: "follow_up",
  due_at: new Date(Date.now() + 2 * 24 * 60 * 60 * 1000).toISOString(),
});
```

Or use the helper function:
```python
# In API endpoint
from app.services.task_from_nba import ensure_task_from_next_action
task = ensure_task_from_next_action(db, lead, current_user_id)
```

### 4. Bulk Task Creation

Add endpoint for bulk task creation:
```python
@router.post("/leads/bulk-tasks")
def create_bulk_tasks(
    lead_ids: List[int],
    task_data: TaskCreate,
    ...
):
    # Create tasks for multiple leads
```

### 5. Activity Feed Aggregation

Add summary endpoints:
- `GET /api/activity/summary` - Counts by type, user, date range
- `GET /api/activity/stats` - Activity stats for dashboard

## 📊 Usage Examples

**Create Note:**
```bash
POST /api/leads/123/notes
{
  "content": "Had a quick intro call, seems interested in Q1 pilot."
}
```

**Create Task:**
```bash
POST /api/leads/123/tasks
{
  "title": "Follow up after reply",
  "type": "follow_up",
  "due_at": "2025-11-25T10:00:00Z"
}
```

**Get Lead Activity:**
```bash
GET /api/leads/123/activity?limit=50
```

**Get Workspace Activity:**
```bash
GET /api/activity?workspace_id=1&limit=50&type_filter=lead_created
```

**Get Tasks:**
```bash
GET /api/tasks?status=open&due_filter=overdue
```

## 🎯 Integration Points

**With Next Best Action:**
- NBA suggestions can create tasks automatically
- Tasks show in activity timeline
- Completed tasks update NBA

**With Campaigns:**
- Campaign events logged to activity
- Replies/opens create follow-up tasks
- Campaign outcomes visible in lead timeline

**With Segments & Lists:**
- List creation logged
- Lead additions/removals logged
- Bulk task creation from segments

**With Workspaces:**
- Activity feed shows workspace-level events
- Tasks assigned to workspace members
- Team activity visible to managers

## ⚠️ Important Notes

1. **Activity Logging**: Add logging calls throughout the system for complete timeline
2. **Performance**: For large datasets, consider:
   - Pagination for activity feeds
   - Indexing on `created_at`, `type`, `lead_id`, `workspace_id`
   - Archiving old activities
3. **Task Assignment**: Tasks can be assigned to different users than creator
4. **Due Dates**: Tasks support optional due dates for prioritization
5. **Activity Meta**: Use `meta` field to store event-specific details (email, campaign name, etc.)

## 🚀 Future Enhancements

- **Task Templates**: Pre-defined task templates for common actions
- **Task Recurring**: Recurring tasks (e.g., "Follow up weekly")
- **Activity Search**: Search activity by content, user, date range
- **Activity Export**: Export activity timeline to CSV
- **Task Dependencies**: Link tasks together
- **Activity Notifications**: Notify users of important activities
- **Activity Aggregation**: Daily/weekly activity summaries

