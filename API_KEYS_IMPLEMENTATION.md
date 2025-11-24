# API Keys Management + Rate Limiting Implementation

## ✅ What's Been Implemented

### 1. Database Models

**New Model** (`app/core/orm_api_keys.py`):
- `APIKeyORM` - API key storage with workspace scoping
- `ApiKeyScope` - Enum of available scopes

**Key Features:**
- Stores `key_hash` (SHA-256) - never stores raw key
- `key_prefix` for display (first 20 chars)
- Scopes as comma-separated string
- Rate limits: per minute, per hour, per day
- Usage tracking: `last_used_at`, `last_used_ip`, `total_requests`
- Optional expiration date

### 2. Authentication Service

**API Key Auth** (`app/services/api_key_auth.py`):
- `generate_api_key()` - Generate new key with hash
- `get_api_key_from_header()` - Extract from `Authorization: Bearer` or `X-Bidec-Api-Key`
- `get_api_key_context()` - Validate key, check scopes, enforce rate limits
- `check_rate_limit()` - Redis-based or in-memory rate limiting

**Rate Limiting:**
- Per-minute, per-hour, per-day limits
- Redis-backed (with in-memory fallback for dev)
- Token bucket / fixed window algorithm

### 3. API Endpoints

**API Key Management** (`app/api/routes_api_keys.py`):
- `POST /api/api-keys` - Create key (returns token once)
- `GET /api/api-keys` - List all keys for workspace
- `GET /api/api-keys/{id}` - Get specific key
- `PATCH /api/api-keys/{id}` - Update/revoke key
- `DELETE /api/api-keys/{id}` - Delete key permanently

**Permissions:**
- Only Owner/Admin can create/manage keys
- Keys are scoped to workspace

### 4. Integration with LinkedIn Extension

**Updated** (`app/api/routes_linkedin.py`):
- `/leads/linkedin-capture` now supports API key auth
- Falls back to user JWT if no API key provided
- Uses workspace from API key context

## 🔄 Next Steps

### 1. Update Extension to Use API Keys

**Chrome Extension:**
- Replace user JWT storage with API key
- Store API key in `chrome.storage.sync`
- Use `Authorization: Bearer {api_key}` header
- Show key management UI in popup

### 2. Add Scope Checking to More Endpoints

Update endpoints to check scopes:
```python
@router.post("/leads")
def create_lead(
    request: Request,
    api_context: Optional[ApiKeyContext] = Depends(get_api_key_context),
    ...
):
    if api_context:
        # Check scope
        if "leads:write" not in api_context.scopes:
            raise HTTPException(403, "Insufficient permissions")
```

### 3. Redis Setup (Production)

Install and configure Redis:
```bash
# Install Redis
# Windows: Download from https://redis.io/download
# Linux: sudo apt-get install redis-server

# Update .env
REDIS_URL=redis://localhost:6379/0
```

Update `check_rate_limit()` to use Redis connection from config.

### 4. Frontend UI

**API Keys Page** (`/settings/api-keys`):
- List of keys with status, last used, scopes
- "Create API Key" button
- Show token once in modal (copy button)
- Revoke/delete actions
- Usage stats display

**Extension Popup:**
- API key input field
- "Generate new key" link to settings
- Status indicator (connected/not connected)

## 📋 Available Scopes

- `leads:read` - Read leads
- `leads:write` - Create/update leads
- `jobs:read` - Read jobs
- `jobs:write` - Create/run jobs
- `lists:read` - Read lists
- `lists:write` - Create/update lists
- `playbooks:read` - Read playbooks
- `playbooks:write` - Run playbooks
- `segments:read` - Read segments
- `segments:write` - Create/update segments
- `email:verify` - Verify emails
- `email:find` - Find emails
- `company:search` - Company search
- `workspace:read` - Read workspace info
- `workspace:write` - Manage workspace

## 🔐 Security Best Practices

1. **Never store raw keys** - Only hash is stored
2. **Show token once** - Only on creation, never again
3. **Scope principle** - Grant minimum required permissions
4. **Rate limiting** - Prevent abuse and DoS
5. **Expiration** - Set expiration for temporary keys
6. **Rotation** - Encourage periodic key rotation
7. **Revocation** - Easy key revocation for compromised keys

## 🚀 Usage Examples

**Create API Key:**
```bash
POST /api/api-keys
{
  "name": "LinkedIn Extension",
  "scopes": ["leads:read", "leads:write"],
  "rate_limit_per_minute": 120
}

# Response includes token (show once!)
{
  "id": 1,
  "token": "bidec_live_9f3f1a0b0c6f4a20a31d...",
  ...
}
```

**Use API Key:**
```bash
curl -H "Authorization: Bearer bidec_live_9f3f1a0b0c6f4a20a31d..." \
     https://api.example.com/api/leads/linkedin-capture
```

**Rate Limit Response:**
```json
{
  "detail": "Rate limit exceeded: 120 requests per minute"
}
```
Status: 429 Too Many Requests

## ⚠️ Important Notes

1. **Backward Compatibility:** Existing endpoints still work with user JWT auth
2. **Workspace Scoping:** Keys are tied to workspace, resources inherit workspace
3. **Rate Limiting:** Redis recommended for production, in-memory fallback for dev
4. **Key Display:** Only show `key_prefix` in UI after creation (never full token)
5. **Migration:** Existing `APIKeyORM` in `orm.py` can coexist, new keys use `APIKeyORM` in `orm_api_keys.py`

