# Authentication & User Management Guide

## Overview

This guide explains the new authentication system with user approval, feature gating, and super admin capabilities.

## Features

1. **Sign up / Sign in**: Users can register and login
2. **User Approval**: Admin controls who can use the app (pending → active)
3. **Feature Gating**: Admin can enable/disable advanced features per user
4. **Super Admin**: Platform-level admin who can see and manage everything

## Backend Implementation

### User Model Fields

The `UserORM` model now includes:

- `status`: `pending` | `active` | `suspended`
- `is_super_admin`: Boolean flag for platform admin
- `can_use_advanced`: Boolean flag for advanced features access

### Authentication Endpoints

#### Sign Up
```http
POST /api/auth/signup
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securepassword123",
  "full_name": "John Doe"  // optional
}
```

Response:
```json
{
  "id": 1,
  "email": "user@example.com",
  "full_name": "John Doe",
  "status": "pending",
  "is_super_admin": false,
  "can_use_advanced": false,
  ...
}
```

**Note**: New users are created with `status="pending"` and must be approved by a super admin.

#### Login
```http
POST /api/auth/login
Content-Type: application/x-www-form-urlencoded

username=user@example.com&password=securepassword123
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Note**: Only users with `status="active"` can login.

#### Get Current User
```http
GET /api/me
Authorization: Bearer <token>
```

Response:
```json
{
  "id": 1,
  "email": "user@example.com",
  "full_name": "John Doe",
  "status": "active",
  "is_super_admin": false,
  "can_use_advanced": true,
  ...
}
```

### Admin Endpoints (Super Admin Only)

#### List Users
```http
GET /api/admin/users?page=1&page_size=20&q=search&status=active
Authorization: Bearer <super_admin_token>
```

#### Update User
```http
PATCH /api/admin/users/{user_id}
Authorization: Bearer <super_admin_token>
Content-Type: application/json

{
  "status": "active",              // optional
  "can_use_advanced": true,         // optional
  "is_super_admin": false           // optional
}
```

### Permission Dependencies

Use these in your FastAPI routes:

```python
from app.api.dependencies import require_advanced_user, require_super_admin
from app.api.routes_auth import get_current_user

# Require any authenticated user
@router.get("/some-endpoint")
def some_endpoint(current_user: UserORM = Depends(get_current_user)):
    ...

# Require advanced features
@router.post("/ai/playbooks/draft")
def ai_playbook(
    current_user: UserORM = Depends(require_advanced_user)
):
    ...

# Require super admin
@router.get("/admin/users")
def list_users(
    current_user: UserORM = Depends(require_super_admin)
):
    ...
```

## Frontend Implementation

### API Client

The API client (`frontend/lib/api.ts`) now includes:

- `apiClient.signup(email, password, fullName?)`
- `apiClient.login(email, password)` - stores token in localStorage
- `apiClient.getMe()` - get current user info
- `apiClient.getAdminUsers(params?)` - list users (super admin)
- `apiClient.updateAdminUser(userId, updates)` - update user (super admin)

### JWT Token Handling

The API client automatically:
1. Reads `access_token` from `localStorage` on each request
2. Adds `Authorization: Bearer <token>` header
3. Stores token after successful login

### Admin Users Page

Located at: `frontend/app/admin/users/page.tsx`

Features:
- List all users with pagination
- Search by email/name
- Filter by status
- Approve/Suspend users
- Toggle advanced features
- Toggle super admin status

**Access**: Only visible to users with `is_super_admin=true`

## Usage Flow

### 1. User Signs Up

1. User visits signup page
2. Fills email, password, name
3. Submits → `POST /api/auth/signup`
4. User sees: "Signup successful. Your account is pending approval."

### 2. Super Admin Approves

1. Super admin logs in
2. Navigates to `/admin/users`
3. Sees user with status "pending"
4. Clicks "Approve" → user status changes to "active"
5. Optionally toggles "Advanced" checkbox

### 3. User Logs In

1. User visits login page
2. Enters email/password
3. Submits → `POST /api/auth/login`
4. If `status="active"`, receives JWT token
5. Token stored in localStorage
6. User can now access the app

### 4. Feature Gating

**Backend:**
- Advanced endpoints use `require_advanced_user` dependency
- Returns 403 if `can_use_advanced=false`

**Frontend:**
- Call `/api/me` on app load
- Check `can_use_advanced` flag
- Hide/disable advanced UI elements if false
- Show message: "Advanced features not enabled. Contact admin."

## Environment Variables

Add to `.env`:

```bash
JWT_SECRET_KEY=your-secret-key-change-in-production-min-32-chars-please-use-a-secure-random-string
```

**Important**: Use a strong, random secret key in production!

## Database Migration

Run the migration script:

```bash
python migrate_add_user_auth_fields.py
```

This adds:
- `status` column (default: 'pending')
- `is_super_admin` column (default: false)
- `can_use_advanced` column (default: false)
- Indexes for performance

## Creating First Super Admin

After migration, manually set a user as super admin:

```python
# In Python shell or migration script
from app.core.db import SessionLocal
from app.core.orm import UserORM

db = SessionLocal()
user = db.query(UserORM).filter(UserORM.email == "admin@example.com").first()
if user:
    user.is_super_admin = True
    user.status = "active"
    user.can_use_advanced = True
    db.commit()
```

Or via SQL:

```sql
UPDATE users 
SET is_super_admin = 1, status = 'active', can_use_advanced = 1 
WHERE email = 'admin@example.com';
```

## Security Notes

1. **JWT Secret Key**: Must be at least 32 characters, random, and kept secret
2. **Password Hashing**: Uses bcrypt (already implemented)
3. **Token Expiry**: 7 days (configurable in `app/services/jwt_service.py`)
4. **Super Admin**: Only grant to trusted users
5. **HTTPS**: Always use HTTPS in production

## Next Steps

1. Create login/signup pages in frontend
2. Add route guards to protect admin pages
3. Add "Advanced features" messaging in UI
4. Implement logout functionality (clear localStorage)
5. Add email verification (optional)
6. Add password reset (optional)

## Example: Protecting Advanced Endpoints

```python
# Before
@router.post("/ai/playbooks/draft")
def draft_playbook(...):
    ...

# After
from app.api.dependencies import require_advanced_user

@router.post("/ai/playbooks/draft")
def draft_playbook(
    ...,
    current_user: UserORM = Depends(require_advanced_user)
):
    ...
```

## Example: Frontend Feature Gating

```typescript
// In your component
const { data: user } = useQuery('me', apiClient.getMe);

if (!user || user.status !== 'active') {
  return <PendingApprovalMessage />;
}

if (!user.can_use_advanced) {
  return (
    <div>
      <h2>Advanced Features</h2>
      <p>This feature is not enabled for your account. Contact your administrator.</p>
    </div>
  );
}

// Show advanced features
```

