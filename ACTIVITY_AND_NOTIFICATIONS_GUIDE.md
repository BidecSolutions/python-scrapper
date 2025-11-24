# Activity & Notifications System Guide

## Overview

This guide explains the activity tracking and notifications system that provides:
- **Global Activity View** for super admins (all workspaces)
- **Workspace Activity View** for normal users (their workspace only)
- **In-App Notifications** with header bell and dropdown

## Backend Implementation

### Activity Model

The `ActivityORM` model (`app/core/orm_activity.py`) tracks events across the system:
- Lead events (created, updated, added to list)
- Email events (found, verified)
- Campaign events (sent, outcomes)
- Task events (created, completed)
- Playbook events (run, completed)
- Job events (created, completed, failed)

### Notification Model

The `NotificationORM` model (`app/core/orm_notifications.py`) stores user-facing notifications:
- `user_id` set = personal notification
- `user_id` null = workspace-level (shown to admins)

### API Endpoints

#### Admin Activity (Super Admin Only)
- `GET /api/admin/activity` - List all activity across all workspaces
  - Query params: `page`, `page_size`, `workspace_id`, `actor_user_id`, `type`

#### Workspace Activity
- `GET /api/activity` - List activity for current workspace
  - Query params: `page`, `page_size`, `type`

#### Notifications
- `GET /api/notifications` - List notifications for current user
  - Query params: `only_unread`, `limit`
- `PATCH /api/notifications/{id}` - Update notification (mark read/archived)
- `POST /api/notifications/mark-all-read` - Mark all as read

### Creating Notifications

Use the `create_notification` helper from `app/services/notification_service.py`:

```python
from app.services.notification_service import create_notification
from app.core.orm_notifications import NotificationType

# When a task is assigned
create_notification(
    db,
    workspace_id=workspace.id,
    user_id=task.user_id,
    type=NotificationType.task_assigned,
    title="New task assigned",
    body=f"{task.title}",
    target_url=f"/leads/{task.lead_id}?tab=tasks",
    meta={"task_id": task.id, "lead_id": task.lead_id},
)
```

## Frontend Implementation

### Pages

1. **Admin Activity Page** (`/admin/activity`)
   - Super admin only
   - Shows all activity across all workspaces
   - Filters: workspace ID, user ID, activity type

2. **Workspace Activity Page** (`/activity`)
   - Normal users
   - Shows activity for current workspace only
   - Filter: activity type

### Components

**NotificationsBell** (`frontend/components/layout/NotificationsBell.tsx`)
- Header bell icon with unread count badge
- Dropdown with notification list
- Auto-refreshes every 60 seconds
- Click to mark read and navigate to target URL
- "Mark all as read" button

### Integration

The `NotificationsBell` is automatically included in `AppLayout` header.

## Usage Examples

### Creating Notifications from Existing Flows

**Task Creation:**
```python
# In your task creation endpoint
task = LeadTaskORM(...)
db.add(task)
db.flush()

create_notification(
    db,
    workspace_id=task.workspace_id,
    user_id=task.user_id,
    type=NotificationType.task_assigned,
    title="New task assigned",
    body=task.title,
    target_url=f"/leads/{task.lead_id}?tab=tasks",
)
```

**Playbook Completion:**
```python
# In playbook completion handler
create_notification(
    db,
    workspace_id=playbook_job.workspace_id,
    user_id=None,  # Workspace-level
    type=NotificationType.playbook_completed,
    title="Playbook completed",
    body=f"LinkedIn → Campaign playbook completed (243 leads added)",
    target_url=f"/playbooks/jobs/{playbook_job.id}",
    meta={"playbook_id": playbook_job.id, "leads_count": 243},
)
```

**Reply Received:**
```python
# In email sync service when reply detected
create_notification(
    db,
    workspace_id=lead.workspace_id,
    user_id=lead.owner_user_id,
    type=NotificationType.reply_received,
    title="New reply received",
    body=f"Reply from {lead.name}",
    target_url=f"/leads/{lead.id}",
    meta={"lead_id": lead.id, "campaign_id": campaign_id},
)
```

## Database Migration

Run the migration script:

```bash
python migrate_add_notifications.py
```

This creates the `notifications` table with all required columns and indexes.

## Next Steps

1. **Wire notifications into existing flows:**
   - Task creation/assignment
   - Playbook completion/failure
   - Email replies (when email sync is implemented)
   - Campaign outcomes

2. **Add notification preferences:**
   - User settings for notification types
   - Email notifications (optional)

3. **Add critical events widget:**
   - Super admin dashboard widget
   - Shows recent critical audit events

4. **Add notification sounds:**
   - Optional browser notification API
   - Sound effects for important notifications

