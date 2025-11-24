# Workspaces, Teams & Roles Implementation

## ✅ What's Been Implemented

### 1. Database Models

**New Models:**
- `WorkspaceORM` (`app/core/orm_workspaces.py`) - Workspace/team unit
- `WorkspaceMemberORM` - User-workspace relationship with roles

**Workspace Roles:**
- `owner` - Full control (billing, members, delete)
- `admin` - Manage members, integrations, playbooks
- `member` - Capture leads, run jobs, export lists
- `viewer` - Read-only access

### 2. Permission System

**Permission Service** (`app/services/workspace_permissions.py`):
- `require_workspace_member()` - Verify membership
- `require_role()` - Check specific roles
- Helper functions: `can_manage_billing()`, `can_manage_members()`, etc.

### 3. API Endpoints

**Workspace Management** (`app/api/routes_workspaces.py`):
- `GET /api/workspaces` - List user's workspaces
- `POST /api/workspaces` - Create workspace (user becomes owner)
- `POST /api/workspaces/{id}/switch` - Switch active workspace

**Team Management:**
- `GET /api/workspaces/{id}/members` - List members
- `POST /api/workspaces/{id}/members/invite` - Invite user
- `PATCH /api/workspaces/{id}/members/{member_id}` - Update role
- `DELETE /api/workspaces/{id}/members/{member_id}` - Remove member

## 🔄 Next Steps (Migration)

### 1. Add `workspace_id` to Shared Resources

You need to add `workspace_id` columns to these models:

```python
# In app/core/orm.py - LeadORM
workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=True, index=True)

# In app/core/orm_lists.py - LeadListORM
workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=True, index=True)

# In app/core/orm.py - ScrapeJobORM
workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=True, index=True)

# In app/core/orm_segments.py - SegmentORM
workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=True, index=True)

# In app/core/orm_playbooks.py - PlaybookJobORM
workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=True, index=True)

# In app/core/orm_company_search.py - CompanySearchJobORM
workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=True, index=True)

# In app/core/orm_integrations.py - OrganizationIntegrationORM
workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=True, index=True)
```

### 2. Update Queries to Filter by Workspace

All API endpoints should:
1. Get `workspace_id` from JWT/session (active workspace)
2. Filter queries by `workspace_id` instead of just `organization_id`
3. Verify user is a member of that workspace

Example:
```python
@router.get("/leads")
def get_leads(
    workspace_id: int = Depends(get_active_workspace_id),
    db: Session = Depends(get_db),
):
    # Verify membership
    require_workspace_member(db, workspace_id, current_user_id)
    
    # Filter by workspace
    leads = db.query(LeadORM).filter(
        LeadORM.workspace_id == workspace_id
    ).all()
```

### 3. Migration Script

Create a migration to:
1. Create default workspace for each organization
2. Add all existing users as workspace owners
3. Set `workspace_id` on all existing leads, lists, jobs, etc.

```python
# migrate_add_workspaces.py
def migrate():
    # 1. Create default workspace for each org
    # 2. Add users as owners
    # 3. Set workspace_id on all resources
    pass
```

### 4. Frontend Integration

**Workspace Switcher:**
- Add dropdown in top-left of app layout
- Show current workspace name
- List all user's workspaces
- "Create new workspace" option
- On selection, call `/api/workspaces/{id}/switch` and reload

**Team Settings Page:**
- Settings → Team tab
- Show workspace name, plan
- Members table with roles
- Invite user form
- Change role / remove member actions

**Permission Checks:**
- Hide/disable UI elements based on user role
- Show permission errors when actions are blocked

## 📋 Permission Matrix

| Action | Owner | Admin | Member | Viewer |
|--------|:-----:|:-----:|:------:|:------:|
| Manage billing | ✅ | ❌ | ❌ | ❌ |
| Manage members | ✅ | ✅ | ❌ | ❌ |
| Setup integrations | ✅ | ✅ | ❌ | ❌ |
| Create/edit playbooks | ✅ | ✅ | ✅ | ❌ |
| Capture leads | ✅ | ✅ | ✅ | ❌ |
| Run jobs | ✅ | ✅ | ✅ | ❌ |
| Export lists | ✅ | ✅ | ✅ | ❌ |
| View resources | ✅ | ✅ | ✅ | ✅ |

## 🔗 Integration Points

**LinkedIn Extension:**
- Use active workspace's API key
- Captured leads go to active workspace

**Company Search, Playbooks, Lists:**
- All scoped by `workspace_id`
- Members can collaborate on shared resources

**Credits:**
- Tracked at organization level (shared across workspaces)
- Or workspace-level if you want isolation

**HubSpot Integration:**
- Configured per workspace
- One workspace → one HubSpot account

## 🚀 Usage Examples

**Create Workspace:**
```bash
POST /api/workspaces
{
  "name": "My Agency",
  "description": "Main workspace for client work"
}
```

**Invite Team Member:**
```bash
POST /api/workspaces/1/members/invite
{
  "email": "teammate@example.com",
  "role": "member"
}
```

**Switch Workspace:**
```bash
POST /api/workspaces/2/switch
# Returns workspace info for frontend to store in session
```

## ⚠️ Important Notes

1. **Backward Compatibility:** Start with `workspace_id` as nullable, then migrate existing data
2. **Default Workspace:** Create a default workspace for each organization during migration
3. **Auth Integration:** Replace `get_current_user_id()` placeholder with actual JWT/session auth
4. **Workspace Context:** Store active `workspace_id` in JWT claims or session storage
5. **Email Invites:** Implement email sending for pending invites (currently just logs)

## 🎯 Future Enhancements

- Workspace-level API keys
- Workspace usage analytics
- Workspace templates
- Cross-workspace lead sharing
- Workspace-level custom fields

