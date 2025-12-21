"""API routes for Saved Views"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import List, Optional
from datetime import datetime, timezone
import secrets

from app.core.db import get_db
from app.core.orm_saved_views import SavedViewORM
from app.api.routes_workspaces import get_current_user_optional, get_current_workspace_optional
from app.core.orm import UserORM
from app.core.orm_workspaces import WorkspaceORM

router = APIRouter()


def _get_view_meta(view: SavedViewORM) -> dict:
    if isinstance(view.filters, dict):
        meta = view.filters.get("__meta", {})
        if isinstance(meta, dict):
            return meta
    return {}


def _set_view_meta(view: SavedViewORM, meta: dict) -> None:
    if not isinstance(view.filters, dict):
        view.filters = {}
    view.filters["__meta"] = meta


@router.get("/saved-views")
async def list_saved_views(
    page_type: str,  # "leads", "jobs", "deals", "verification"
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user_optional),
    current_workspace: WorkspaceORM = Depends(get_current_workspace_optional),
):
    """List saved views for the current page type"""
    if not current_user or not current_workspace:
        return []

    # Get both personal and org-wide views
    views = db.query(SavedViewORM).filter(
        and_(
            SavedViewORM.organization_id == current_workspace.organization_id,
            SavedViewORM.page_type == page_type,
            or_(
                # Personal views
                and_(
                    SavedViewORM.user_id == current_user.id,
                    SavedViewORM.is_shared == False
                ),
                # Org-wide shared views
                SavedViewORM.is_shared == True
            )
        )
    ).order_by(
        SavedViewORM.is_pinned.desc(),  # Pinned first
        SavedViewORM.last_used_at.desc().nullslast(),  # Recently used next
        SavedViewORM.created_at.desc()  # Then by creation date
    ).all()

    return [
        {
            "id": v.id,
            "name": v.name,
            "page_type": v.page_type,
            "is_pinned": v.is_pinned,
            "is_shared": v.is_shared,
            "filters": v.filters,
            "sort_by": v.sort_by,
            "sort_order": v.sort_order,
            "visible_columns": v.visible_columns,
            "share_token": _get_view_meta(v).get("share_token"),
            "share_enabled": _get_view_meta(v).get("share_enabled", False),
            "last_used_at": v.last_used_at.isoformat() if v.last_used_at else None,
            "usage_count": v.usage_count,
            "created_at": v.created_at.isoformat(),
        }
        for v in views
    ]


@router.post("/saved-views")
async def create_saved_view(
    name: str,
    page_type: str,
    filters: dict,
    sort_by: Optional[str] = None,
    sort_order: Optional[str] = "desc",
    is_pinned: bool = False,
    is_shared: bool = False,
    visible_columns: Optional[List[str]] = None,
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user_optional),
    current_workspace: WorkspaceORM = Depends(get_current_workspace_optional),
):
    """Create a new saved view"""
    if not current_user or not current_workspace:
        raise HTTPException(status_code=401, detail="Authentication required")

    # Validate page_type
    valid_page_types = ["leads", "jobs", "deals", "verification"]
    if page_type not in valid_page_types:
        raise HTTPException(status_code=400, detail=f"Invalid page_type. Must be one of: {valid_page_types}")

    # If shared, user_id must be null (org-wide)
    user_id = None if is_shared else current_user.id

    view = SavedViewORM(
        organization_id=current_workspace.organization_id,
        workspace_id=current_workspace.id,
        user_id=user_id,
        name=name,
        page_type=page_type,
        filters=filters,
        sort_by=sort_by,
        sort_order=sort_order,
        is_pinned=is_pinned,
        is_shared=is_shared,
        visible_columns=visible_columns,
    )

    db.add(view)
    db.commit()
    db.refresh(view)

    return {
        "id": view.id,
        "name": view.name,
        "page_type": view.page_type,
        "is_pinned": view.is_pinned,
        "is_shared": view.is_shared,
        "filters": view.filters,
        "sort_by": view.sort_by,
        "sort_order": view.sort_order,
        "visible_columns": view.visible_columns,
        "share_token": _get_view_meta(view).get("share_token"),
        "share_enabled": _get_view_meta(view).get("share_enabled", False),
        "created_at": view.created_at.isoformat(),
    }


@router.put("/saved-views/{view_id}")
async def update_saved_view(
    view_id: int,
    name: Optional[str] = None,
    filters: Optional[dict] = None,
    sort_by: Optional[str] = None,
    sort_order: Optional[str] = None,
    is_pinned: Optional[bool] = None,
    is_shared: Optional[bool] = None,
    visible_columns: Optional[List[str]] = None,
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user_optional),
    current_workspace: WorkspaceORM = Depends(get_current_workspace_optional),
):
    """Update a saved view"""
    if not current_user or not current_workspace:
        raise HTTPException(status_code=401, detail="Authentication required")

    view = db.query(SavedViewORM).filter(
        and_(
            SavedViewORM.id == view_id,
            SavedViewORM.organization_id == current_workspace.organization_id,
        )
    ).first()

    if not view:
        raise HTTPException(status_code=404, detail="Saved view not found")

    # Check permissions: can only edit own views or org-wide views if user has permission
    if not view.is_shared and view.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only edit your own views")

    # Update fields
    if name is not None:
        view.name = name
    if filters is not None:
        view.filters = filters
    if sort_by is not None:
        view.sort_by = sort_by
    if sort_order is not None:
        view.sort_order = sort_order
    if is_pinned is not None:
        view.is_pinned = is_pinned
    if is_shared is not None:
        view.is_shared = is_shared
        # If making shared, remove user_id
        if is_shared:
            view.user_id = None
        elif not view.user_id:
            view.user_id = current_user.id
    if visible_columns is not None:
        view.visible_columns = visible_columns

    db.commit()
    db.refresh(view)

    return {
        "id": view.id,
        "name": view.name,
        "page_type": view.page_type,
        "is_pinned": view.is_pinned,
        "is_shared": view.is_shared,
        "filters": view.filters,
        "sort_by": view.sort_by,
        "sort_order": view.sort_order,
        "visible_columns": view.visible_columns,
        "share_token": _get_view_meta(view).get("share_token"),
        "share_enabled": _get_view_meta(view).get("share_enabled", False),
        "updated_at": view.updated_at.isoformat(),
    }


@router.post("/saved-views/{view_id}/use")
async def use_saved_view(
    view_id: int,
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user_optional),
    current_workspace: WorkspaceORM = Depends(get_current_workspace_optional),
):
    """Track usage of a saved view"""
    if not current_user or not current_workspace:
        raise HTTPException(status_code=401, detail="Authentication required")

    view = db.query(SavedViewORM).filter(
        and_(
            SavedViewORM.id == view_id,
            SavedViewORM.organization_id == current_workspace.organization_id,
        )
    ).first()

    if not view:
        raise HTTPException(status_code=404, detail="Saved view not found")

    # Update usage tracking
    view.last_used_at = datetime.now(timezone.utc)
    view.usage_count += 1

    db.commit()

    return {"success": True}


@router.post("/saved-views/{view_id}/share")
async def create_share_link(
    view_id: int,
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user_optional),
    current_workspace: WorkspaceORM = Depends(get_current_workspace_optional),
):
    """Generate or rotate a share token for a saved view."""
    if not current_user or not current_workspace:
        raise HTTPException(status_code=401, detail="Authentication required")

    view = db.query(SavedViewORM).filter(
        and_(
            SavedViewORM.id == view_id,
            SavedViewORM.organization_id == current_workspace.organization_id,
        )
    ).first()

    if not view:
        raise HTTPException(status_code=404, detail="Saved view not found")

    if not view.is_shared and view.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only share your own views")

    meta = _get_view_meta(view)
    meta["share_token"] = secrets.token_urlsafe(16)
    meta["share_enabled"] = True
    _set_view_meta(view, meta)

    db.commit()
    db.refresh(view)

    return {"share_token": meta["share_token"], "share_enabled": True}


@router.delete("/saved-views/{view_id}/share")
async def revoke_share_link(
    view_id: int,
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user_optional),
    current_workspace: WorkspaceORM = Depends(get_current_workspace_optional),
):
    """Disable sharing for a saved view."""
    if not current_user or not current_workspace:
        raise HTTPException(status_code=401, detail="Authentication required")

    view = db.query(SavedViewORM).filter(
        and_(
            SavedViewORM.id == view_id,
            SavedViewORM.organization_id == current_workspace.organization_id,
        )
    ).first()

    if not view:
        raise HTTPException(status_code=404, detail="Saved view not found")

    if not view.is_shared and view.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only update your own views")

    meta = _get_view_meta(view)
    meta["share_enabled"] = False
    _set_view_meta(view, meta)

    db.commit()
    return {"share_enabled": False}


@router.get("/saved-views/shared/{token}")
async def get_shared_view(
    token: str,
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user_optional),
    current_workspace: WorkspaceORM = Depends(get_current_workspace_optional),
):
    """Resolve a shared view token within the current org."""
    if not current_user or not current_workspace:
        raise HTTPException(status_code=401, detail="Authentication required")

    views = db.query(SavedViewORM).filter(
        SavedViewORM.organization_id == current_workspace.organization_id
    ).all()

    for view in views:
        meta = _get_view_meta(view)
        if meta.get("share_enabled") and meta.get("share_token") == token:
            return {
                "id": view.id,
                "name": view.name,
                "page_type": view.page_type,
                "is_pinned": view.is_pinned,
                "is_shared": view.is_shared,
                "filters": view.filters,
                "sort_by": view.sort_by,
                "sort_order": view.sort_order,
                "visible_columns": view.visible_columns,
                "share_token": meta.get("share_token"),
                "share_enabled": meta.get("share_enabled", False),
                "created_at": view.created_at.isoformat(),
            }

    raise HTTPException(status_code=404, detail="Shared view not found")


@router.delete("/saved-views/{view_id}")
async def delete_saved_view(
    view_id: int,
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user_optional),
    current_workspace: WorkspaceORM = Depends(get_current_workspace_optional),
):
    """Delete a saved view"""
    if not current_user or not current_workspace:
        raise HTTPException(status_code=401, detail="Authentication required")

    view = db.query(SavedViewORM).filter(
        and_(
            SavedViewORM.id == view_id,
            SavedViewORM.organization_id == current_workspace.organization_id,
        )
    ).first()

    if not view:
        raise HTTPException(status_code=404, detail="Saved view not found")

    # Check permissions: can only delete own views or org-wide views if user has permission
    if not view.is_shared and view.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only delete your own views")

    db.delete(view)
    db.commit()

    return {"success": True}

