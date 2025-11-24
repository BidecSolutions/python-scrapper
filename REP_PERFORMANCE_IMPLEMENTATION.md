# Rep Performance & Leaderboard Implementation

## ✅ What's Been Implemented

### 1. Database Schema Updates

**Added to `LeadORM`:**
- `owner_user_id` - Primary rep/owner of the lead (for attribution)
- `owner` relationship to UserORM

**Updated `UserORM`:**
- `owned_leads` relationship to LeadORM

### 2. Rep Performance Service (`app/services/rep_performance_service.py`)

**Metrics Calculated:**
- **New leads owned** - Leads created/assigned to rep in time window
- **Leads worked** - Distinct leads where rep created tasks or notes
- **Tasks created/completed** - Task activity metrics
- **Task completion rate** - Percentage of tasks completed
- **Campaign impact** - Opens, replies, bounces on rep's leads
- **Campaign rates** - Reply rate, open rate, bounce rate
- **Source breakdown** - Percentage of leads by source (LinkedIn, CSV, Company search)

**Functions:**
- `get_rep_performance()` - Calculate metrics for workspace members
- `get_rep_leaderboard()` - Get sorted leaderboard by metric

### 3. API Endpoints (`app/api/routes_rep_performance.py`)

- `GET /api/reports/rep-performance` - Get performance for all members or specific user
- `GET /api/reports/leaderboard` - Get sorted leaderboard
- `GET /api/reports/users/{user_id}/performance` - Get specific user's performance

**Query Parameters:**
- `workspace_id` (optional) - Workspace filter
- `days` (default: 30) - Time window
- `user_id` (optional) - Specific user
- `sort_by` (leaderboard) - Sort metric: "replies", "leads_worked", "tasks_completed", "reply_rate"

**Permissions:**
- Users can view their own stats
- Admins/Owners can view all team stats

## 🔄 Next Steps

### 1. Set Lead Ownership

Update lead creation to set `owner_user_id`:

**LinkedIn Capture:**
```python
# In linkedin_capture
lead.owner_user_id = current_user_id  # Or from API key context
```

**Company Search:**
```python
# In company_search
lead.owner_user_id = current_user_id
```

**CSV Import:**
```python
# In CSV import
lead.owner_user_id = current_user_id
```

**Manual Creation:**
```python
# When user manually creates lead
lead.owner_user_id = current_user_id
```

### 2. Frontend Integration

**Leaderboard Page (`/team/performance`):**
- Table with columns: Rep, New leads, Leads worked, Tasks done, Replies, Reply rate
- Toggle time range: 7 days, 30 days, 90 days
- Sort by: Replies, Leads worked, Tasks completed, Reply rate
- Click rep name → opens per-rep view

**Per-Rep View (`/team/{userId}`):**
- Header: Name, email, role, time range selector
- Key metrics cards:
  - New leads owned
  - Leads worked
  - Tasks created/completed & completion rate
  - Campaign replies & reply rate
  - Bounce rate
- Charts:
  - Daily tasks completed (bar chart)
  - Daily replies generated (line chart)
  - Source mix (pie chart: LinkedIn vs Company vs CSV)
- Top segments (segments where their leads produced most replies)

### 3. Activity Logging Integration

Ensure activity logging captures ownership:
- When lead is created, log with `actor_user_id` set
- When lead ownership changes, log activity
- Campaign events should attribute to lead owner

### 4. Attribution Logic

**First Touch Attribution:**
- If `owner_user_id` not set, use `created_by_user_id`
- Or use first activity (task/note) creator

**Last Touch Attribution (optional):**
- Track last user who worked the lead
- Show both first and last touch in reports

### 5. Enhanced Metrics

Add more metrics:
- **Response time** - Average time to reply
- **Conversion rate** - Leads that converted to customers
- **Segment performance** - Which segments work best for each rep
- **Time to first contact** - How quickly reps work new leads
- **Activity frequency** - Notes/tasks per lead

## 📊 Usage Examples

**Get Leaderboard:**
```bash
GET /api/reports/leaderboard?workspace_id=1&days=30&sort_by=replies
```

**Response:**
```json
[
  {
    "user_id": 12,
    "name": "Ali",
    "email": "ali@example.com",
    "role": "member",
    "new_leads_owned": 85,
    "leads_worked": 120,
    "tasks_created": 40,
    "tasks_completed": 32,
    "task_completion_rate": 80.0,
    "campaign_leads_sent": 200,
    "campaign_opens": 120,
    "campaign_replies": 26,
    "campaign_bounces": 5,
    "campaign_reply_rate": 13.0,
    "campaign_open_rate": 60.0,
    "campaign_bounce_rate": 2.5,
    "source_breakdown": {
      "linkedin_extension": 70.0,
      "company_search": 20.0,
      "csv": 10.0
    }
  }
]
```

**Get Specific User Performance:**
```bash
GET /api/reports/users/12/performance?workspace_id=1&days=30
```

## 🎯 Integration Points

**With Workspaces:**
- Performance scoped to workspace
- Only workspace members appear in leaderboard
- Role-based access (members see own, admins see all)

**With Tasks & Notes:**
- Tasks and notes count toward "leads worked"
- Task completion rate shows productivity

**With Campaigns:**
- Campaign outcomes attributed to lead owner
- Reply/open rates show rep effectiveness

**With Segments:**
- Can show which segments work best for each rep
- Cross-rep vs segment analysis

**With Activity Timeline:**
- Activity feed shows rep actions
- Timeline helps verify attribution

## ⚠️ Important Notes

1. **Lead Ownership**: Set `owner_user_id` when leads are created for accurate attribution
2. **Fallback Attribution**: If `owner_user_id` not set, use `created_by_user_id` or first activity creator
3. **Campaign Attribution**: Campaign outcomes attributed to lead owner, not campaign creator
4. **Performance**: For large teams, consider caching results or pre-computing metrics
5. **Privacy**: Members can only see their own stats unless they're admin/owner

## 🚀 Future Enhancements

- **Team Goals**: Set targets for leads, tasks, replies per rep
- **Performance Trends**: Show performance over time (weekly/monthly trends)
- **Comparative Analysis**: Compare rep performance side-by-side
- **Automated Insights**: "Ali's reply rate improved 15% this month"
- **Gamification**: Badges, achievements, streaks
- **Export Reports**: PDF/CSV export of performance data
- **Custom Metrics**: Allow managers to define custom KPIs

## 💡 Manager Value Proposition

This feature provides:
- **Visibility**: See who's actually working leads
- **Accountability**: Track tasks, notes, and outcomes per rep
- **Optimization**: Identify top performers and learn from them
- **Coaching**: Use data to guide rep improvement
- **ROI Proof**: Show which reps generate the most replies

