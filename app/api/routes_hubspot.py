"""HubSpot Integration API routes"""
import logging
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional, List

from app.core.db import get_db
from app.core.orm_integrations import OrganizationIntegrationORM
from app.api.routes_settings import get_or_create_default_org
from app.services.hubspot_integration import (
    get_hubspot_integration,
    push_leads_to_hubspot
)

logger = logging.getLogger(__name__)
router = APIRouter()


class HubSpotConnectRequest(BaseModel):
    """Request to connect HubSpot"""
    access_token: str = Field(..., description="HubSpot private app access token")


class HubSpotStatusResponse(BaseModel):
    """HubSpot integration status"""
    connected: bool
    last_synced_at: Optional[str] = None


@router.post("/integrations/hubspot/connect")
def connect_hubspot(
    request: HubSpotConnectRequest,
    db: Session = Depends(get_db),
):
    """Connect HubSpot integration (store access token)"""
    org = get_or_create_default_org(db)
    
    # Check if integration already exists
    existing = db.query(OrganizationIntegrationORM).filter(
        OrganizationIntegrationORM.organization_id == org.id,
        OrganizationIntegrationORM.type == "hubspot"
    ).first()
    
    if existing:
        # Update existing
        existing.access_token = request.access_token
        existing.is_active = "active"
        existing.error_message = None
    else:
        # Create new
        existing = OrganizationIntegrationORM(
            organization_id=org.id,
            type="hubspot",
            access_token=request.access_token,
            is_active="active",
        )
        db.add(existing)
    
    db.commit()
    
    return {"message": "HubSpot connected successfully"}


@router.get("/integrations/hubspot/status", response_model=HubSpotStatusResponse)
def get_hubspot_status(
    db: Session = Depends(get_db),
):
    """Get HubSpot integration status"""
    org = get_or_create_default_org(db)
    
    integration = get_hubspot_integration(db, org.id)
    
    if not integration:
        return HubSpotStatusResponse(connected=False)
    
    return HubSpotStatusResponse(
        connected=True,
        last_synced_at=integration.last_synced_at.isoformat() if integration.last_synced_at else None,
    )


class HubSpotPushRequest(BaseModel):
    """Request to push leads to HubSpot"""
    status_filter: List[str] = Field(default=["valid"], description="Email statuses to include")
    upsert: bool = Field(default=True, description="Create or update existing contacts")
    create_static_list: bool = Field(default=False, description="Create a static list in HubSpot")


class HubSpotPushResponse(BaseModel):
    """Response from HubSpot push"""
    contacts_created: int
    contacts_updated: int
    errors: int
    hubspot_list_id: Optional[str] = None


@router.post("/lists/{list_id}/export/hubspot", response_model=HubSpotPushResponse)
def push_list_to_hubspot(
    list_id: int,
    request: HubSpotPushRequest,
    db: Session = Depends(get_db),
):
    """Push leads from a list to HubSpot"""
    org = get_or_create_default_org(db)
    
    try:
        result = push_leads_to_hubspot(
            db=db,
            organization_id=org.id,
            list_id=list_id,
            status_filter=request.status_filter,
            upsert=request.upsert,
            create_static_list=request.create_static_list
        )
        
        return HubSpotPushResponse(
            contacts_created=result["contacts_created"],
            contacts_updated=result["contacts_updated"],
            errors=result["errors"],
            hubspot_list_id=result.get("hubspot_list_id"),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to push to HubSpot: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to push leads to HubSpot")


@router.delete("/integrations/hubspot/disconnect")
def disconnect_hubspot(
    db: Session = Depends(get_db),
):
    """Disconnect HubSpot integration"""
    org = get_or_create_default_org(db)
    
    integration = db.query(OrganizationIntegrationORM).filter(
        OrganizationIntegrationORM.organization_id == org.id,
        OrganizationIntegrationORM.type == "hubspot"
    ).first()
    
    if integration:
        integration.is_active = "inactive"
        db.commit()
    
    return {"message": "HubSpot disconnected"}

