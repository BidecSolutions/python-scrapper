"""API Key authentication and rate limiting"""
import hashlib
import logging
import time
from typing import Optional, List, Set
from fastapi import Request, HTTPException, status
from sqlalchemy.orm import Session

from app.core.orm_api_keys import APIKeyORM, ApiKeyScope
from app.core.orm_workspaces import WorkspaceORM
from app.core.orm import OrganizationORM

logger = logging.getLogger(__name__)

# Default rate limits
DEFAULT_RATE_LIMIT_PER_MINUTE = 60
DEFAULT_RATE_LIMIT_PER_HOUR = 1000
DEFAULT_RATE_LIMIT_PER_DAY = 10000


class ApiKeyContext:
    """Context for API key authenticated requests"""
    def __init__(
        self,
        api_key: APIKeyORM,
        workspace: Optional[WorkspaceORM] = None,
        organization: Optional[OrganizationORM] = None,
        scopes: Optional[Set[str]] = None
    ):
        self.api_key = api_key
        self.workspace = workspace
        self.organization = organization
        self.scopes = scopes or set()


def hash_api_key(token: str) -> str:
    """Hash an API key token using SHA-256"""
    return hashlib.sha256(token.encode('utf-8')).hexdigest()


def generate_api_key(prefix: str = "bidec_live") -> tuple[str, str]:
    """
    Generate a new API key
    
    Returns:
        (raw_token, key_hash)
    """
    import secrets
    # Generate 32-byte random token
    raw_token = secrets.token_urlsafe(32)
    # Create full key with prefix
    full_key = f"{prefix}_{raw_token}"
    # Hash it
    key_hash = hash_api_key(full_key)
    return full_key, key_hash


def parse_scopes(scopes_str: str) -> Set[str]:
    """Parse comma-separated scopes string into a set"""
    if not scopes_str:
        return set()
    return {s.strip() for s in scopes_str.split(",") if s.strip()}


def get_api_key_from_header(request: Request) -> Optional[str]:
    """Extract API key from request headers"""
    # Try Authorization header first
    auth = request.headers.get("Authorization")
    if auth:
        if auth.startswith("Bearer "):
            return auth[len("Bearer "):].strip()
        # Also support just the token without "Bearer"
        return auth.strip()
    
    # Try custom header
    api_key = request.headers.get("X-Bidec-Api-Key") or request.headers.get("X-API-Key")
    if api_key:
        return api_key.strip()
    
    return None


def get_api_key_context(
    request: Request,
    db: Session,
    required_scopes: Optional[List[str]] = None
) -> Optional[ApiKeyContext]:
    """
    Get API key context from request
    
    Returns:
        ApiKeyContext if valid API key found, None otherwise (fallback to user auth)
    
    Raises:
        HTTPException if API key is invalid or insufficient permissions
    """
    token = get_api_key_from_header(request)
    if not token:
        return None  # No API key, fallback to normal user auth
    
    # Hash the token
    key_hash = hash_api_key(token)
    
    # Look up API key
    api_key = db.query(APIKeyORM).filter(
        APIKeyORM.key_hash == key_hash,
        APIKeyORM.active == True
    ).first()
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    
    # Check expiration
    if api_key.expires_at and api_key.expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key has expired"
        )
    
    # Load workspace or organization
    workspace = None
    organization = None
    
    if api_key.workspace_id:
        workspace = db.query(WorkspaceORM).filter(WorkspaceORM.id == api_key.workspace_id).first()
        if not workspace:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Workspace not found"
            )
        # Get organization from workspace
        organization = db.query(OrganizationORM).filter(OrganizationORM.id == workspace.organization_id).first()
    elif api_key.organization_id:
        # Backward compatibility
        organization = db.query(OrganizationORM).filter(OrganizationORM.id == api_key.organization_id).first()
        if not organization:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Organization not found"
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key not associated with workspace or organization"
        )
    
    # Parse scopes
    scopes = parse_scopes(api_key.scopes)
    
    # Check required scopes
    if required_scopes:
        missing_scopes = set(required_scopes) - scopes
        if missing_scopes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required scopes: {', '.join(missing_scopes)}"
            )
    
    # Check rate limits
    check_rate_limit(api_key, request, db)
    
    # Update usage tracking
    from datetime import datetime
    client_ip = request.client.host if request.client else None
    
    api_key.last_used_at = datetime.utcnow()
    api_key.last_used_ip = client_ip
    api_key.total_requests += 1
    db.commit()
    
    return ApiKeyContext(
        api_key=api_key,
        workspace=workspace,
        organization=organization,
        scopes=scopes
    )


def check_rate_limit(api_key: APIKeyORM, request: Request, db: Session) -> None:
    """
    Check rate limits for an API key
    
    Uses Redis if available, otherwise in-memory tracking (for development)
    """
    # Get limits
    limit_per_minute = api_key.rate_limit_per_minute or DEFAULT_RATE_LIMIT_PER_MINUTE
    limit_per_hour = api_key.rate_limit_per_hour
    limit_per_day = api_key.rate_limit_per_day
    
    # Try Redis first
    try:
        import redis
        redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
        redis_client.ping()
        
        current_time = int(time.time())
        current_minute = current_time // 60
        current_hour = current_time // 3600
        current_day = current_time // 86400
        
        # Check per-minute limit
        minute_key = f"rate:{api_key.id}:minute:{current_minute}"
        minute_count = redis_client.incr(minute_key)
        if minute_count == 1:
            redis_client.expire(minute_key, 70)  # Expire after 70 seconds
        
        if minute_count > limit_per_minute:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded: {limit_per_minute} requests per minute"
            )
        
        # Check per-hour limit if set
        if limit_per_hour:
            hour_key = f"rate:{api_key.id}:hour:{current_hour}"
            hour_count = redis_client.incr(hour_key)
            if hour_count == 1:
                redis_client.expire(hour_key, 3660)  # Expire after 61 minutes
            
            if hour_count > limit_per_hour:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Rate limit exceeded: {limit_per_hour} requests per hour"
                )
        
        # Check per-day limit if set
        if limit_per_day:
            day_key = f"rate:{api_key.id}:day:{current_day}"
            day_count = redis_client.incr(day_key)
            if day_count == 1:
                redis_client.expire(day_key, 86470)  # Expire after 24h + 70s
            
            if day_count > limit_per_day:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Rate limit exceeded: {limit_per_day} requests per day"
                )
        
        return
        
    except (ImportError, redis.ConnectionError, redis.TimeoutError):
        # Redis not available - use in-memory fallback (development only)
        logger.warning("Redis not available, using in-memory rate limiting (not suitable for production)")
        
        # Simple in-memory tracking (not thread-safe, but works for dev)
        if not hasattr(check_rate_limit, '_memory_store'):
            check_rate_limit._memory_store = {}
        
        current_minute = int(time.time()) // 60
        minute_key = f"{api_key.id}:{current_minute}"
        
        if minute_key not in check_rate_limit._memory_store:
            check_rate_limit._memory_store[minute_key] = 0
        
        check_rate_limit._memory_store[minute_key] += 1
        
        # Clean old entries (keep last 2 minutes)
        for key in list(check_rate_limit._memory_store.keys()):
            if int(key.split(':')[-1]) < current_minute - 2:
                del check_rate_limit._memory_store[key]
        
        if check_rate_limit._memory_store[minute_key] > limit_per_minute:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded: {limit_per_minute} requests per minute"
            )


def require_api_scope(*required_scopes: str):
    """
    Decorator to require specific API scopes
    
    Usage:
        @router.post("/leads")
        @require_api_scope("leads:read", "leads:write")
        def create_lead(...):
            ...
    """
    def decorator(func):
        # This would be used with FastAPI dependencies
        # For now, we'll handle scope checking in get_api_key_context
        return func
    return decorator

