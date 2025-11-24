"""HubSpot CRM integration service"""
import logging
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from datetime import datetime
import httpx

from app.core.orm import LeadORM, EmailORM
from app.core.orm_lists import LeadListORM, LeadListLeadORM
from app.core.orm_integrations import OrganizationIntegrationORM

logger = logging.getLogger(__name__)


def get_hubspot_integration(db: Session, organization_id: int) -> Optional[OrganizationIntegrationORM]:
    """Get HubSpot integration for an organization"""
    return db.query(OrganizationIntegrationORM).filter(
        OrganizationIntegrationORM.organization_id == organization_id,
        OrganizationIntegrationORM.type == "hubspot",
        OrganizationIntegrationORM.is_active == "active"
    ).first()


def create_hubspot_contact(
    access_token: str,
    email: str,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    company: Optional[str] = None,
    job_title: Optional[str] = None,
    linkedin_url: Optional[str] = None,
    **kwargs
) -> Optional[Dict[str, Any]]:
    """
    Create a contact in HubSpot
    
    Returns:
        Contact data with 'id' and 'properties', or None if failed
    """
    url = "https://api.hubapi.com/crm/v3/objects/contacts"
    
    properties = {
        "email": email,
    }
    
    if first_name:
        properties["firstname"] = first_name
    if last_name:
        properties["lastname"] = last_name
    if company:
        properties["company"] = company
    if job_title:
        properties["jobtitle"] = job_title
    if linkedin_url:
        properties["linkedin_url"] = linkedin_url
    
    # Add custom properties
    properties.update(kwargs)
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    
    payload = {"properties": properties}
    
    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            return response.json()
    except Exception as e:
        logger.error(f"Failed to create HubSpot contact: {e}")
        return None


def update_hubspot_contact(
    access_token: str,
    contact_id: str,
    **properties
) -> Optional[Dict[str, Any]]:
    """Update a HubSpot contact"""
    url = f"https://api.hubapi.com/crm/v3/objects/contacts/{contact_id}"
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    
    payload = {"properties": properties}
    
    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.patch(url, json=payload, headers=headers)
            response.raise_for_status()
            return response.json()
    except Exception as e:
        logger.error(f"Failed to update HubSpot contact {contact_id}: {e}")
        return None


def find_hubspot_contact_by_email(
    access_token: str,
    email: str
) -> Optional[Dict[str, Any]]:
    """Find a HubSpot contact by email"""
    url = "https://api.hubapi.com/crm/v3/objects/contacts/search"
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    
    payload = {
        "filterGroups": [
            {
                "filters": [
                    {
                        "propertyName": "email",
                        "operator": "EQ",
                        "value": email
                    }
                ]
            }
        ],
        "limit": 1
    }
    
    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            if data.get("results") and len(data["results"]) > 0:
                return data["results"][0]
            return None
    except Exception as e:
        logger.error(f"Failed to find HubSpot contact by email: {e}")
        return None


def create_hubspot_list(
    access_token: str,
    name: str,
    contact_ids: List[str]
) -> Optional[str]:
    """Create a static list in HubSpot and add contacts"""
    # First create the list
    url = "https://api.hubapi.com/contacts/v1/lists"
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    
    payload = {
        "name": name,
        "dynamic": False,  # Static list
    }
    
    try:
        with httpx.Client(timeout=10.0) as client:
            # Create list
            response = client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            list_data = response.json()
            list_id = list_data.get("listId")
            
            if not list_id or not contact_ids:
                return list_id
            
            # Add contacts to list
            add_url = f"https://api.hubapi.com/contacts/v1/lists/{list_id}/add"
            add_payload = {
                "vids": [int(cid) for cid in contact_ids if cid.isdigit()]
            }
            
            add_response = client.post(add_url, json=add_payload, headers=headers)
            add_response.raise_for_status()
            
            return list_id
    except Exception as e:
        logger.error(f"Failed to create HubSpot list: {e}")
        return None


def push_leads_to_hubspot(
    db: Session,
    organization_id: int,
    list_id: int,
    status_filter: List[str] = ["valid"],
    upsert: bool = True,
    create_static_list: bool = False
) -> Dict[str, Any]:
    """
    Push leads from a list to HubSpot
    
    Returns:
        Dict with counts: {contacts_created, contacts_updated, errors, hubspot_list_id}
    """
    integration = get_hubspot_integration(db, organization_id)
    if not integration:
        raise ValueError("HubSpot integration not found or not active")
    
    access_token = integration.access_token
    
    # Get list and leads
    lead_list = db.query(LeadListORM).filter(
        LeadListORM.id == list_id,
        LeadListORM.organization_id == organization_id
    ).first()
    
    if not lead_list:
        raise ValueError(f"List {list_id} not found")
    
    # Get leads in list
    list_leads = db.query(LeadListLeadORM).filter(
        LeadListLeadORM.list_id == list_id
    ).all()
    
    lead_ids = [ll.lead_id for ll in list_leads]
    
    # Get leads with valid emails
    leads = db.query(LeadORM).filter(
        LeadORM.id.in_(lead_ids),
        LeadORM.organization_id == organization_id
    ).all()
    
    contacts_created = 0
    contacts_updated = 0
    errors = 0
    hubspot_contact_ids = []
    
    for lead in leads:
        # Get primary email
        email_record = db.query(EmailORM).filter(
            EmailORM.lead_id == lead.id,
            EmailORM.organization_id == organization_id,
            EmailORM.verify_status.in_(status_filter)
        ).order_by(EmailORM.created_at.desc()).first()
        
        if not email_record:
            continue
        
        email = email_record.email
        
        # Extract name
        first_name = ""
        last_name = ""
        if lead.contact_person_name:
            parts = lead.contact_person_name.split()
            first_name = parts[0] if parts else ""
            last_name = " ".join(parts[1:]) if len(parts) > 1 else ""
        elif lead.name:
            parts = lead.name.split()
            first_name = parts[0] if parts else ""
            last_name = " ".join(parts[1:]) if len(parts) > 1 else ""
        
        # Check if contact already exists in HubSpot
        existing_contact = None
        if upsert and lead.hubspot_contact_id:
            # Try to use stored contact ID
            existing_contact = {"id": lead.hubspot_contact_id}
        elif upsert:
            # Search by email
            existing_contact = find_hubspot_contact_by_email(access_token, email)
        
        # Prepare contact properties
        properties = {
            "company": lead.name or "",
            "jobtitle": lead.contact_person_role or "",
            "linkedin_url": lead.linkedin_url or "",
        }
        
        if lead.intro_line:
            properties["notes"] = lead.intro_line
        
        if lead.quality_score:
            properties["hs_lead_status"] = "QUALIFIED" if lead.quality_score >= 70 else "NEW"
        
        try:
            if existing_contact:
                # Update existing contact
                contact_id = existing_contact.get("id")
                result = update_hubspot_contact(
                    access_token,
                    contact_id,
                    **properties
                )
                if result:
                    contacts_updated += 1
                    hubspot_contact_ids.append(str(contact_id))
                    # Update lead with contact ID if not set
                    if not lead.hubspot_contact_id:
                        lead.hubspot_contact_id = str(contact_id)
                        db.commit()
            else:
                # Create new contact
                result = create_hubspot_contact(
                    access_token,
                    email,
                    first_name=first_name,
                    last_name=last_name,
                    **properties
                )
                if result:
                    contacts_created += 1
                    contact_id = result.get("id")
                    hubspot_contact_ids.append(str(contact_id))
                    # Store contact ID on lead
                    lead.hubspot_contact_id = str(contact_id)
                    db.commit()
                else:
                    errors += 1
        except Exception as e:
            logger.error(f"Failed to push lead {lead.id} to HubSpot: {e}")
            errors += 1
    
    # Create static list if requested
    hubspot_list_id = None
    if create_static_list and hubspot_contact_ids:
        hubspot_list_id = create_hubspot_list(
            access_token,
            lead_list.name,
            hubspot_contact_ids
        )
    
    # Update integration last_synced_at
    integration.last_synced_at = datetime.utcnow()
    db.commit()
    
    return {
        "contacts_created": contacts_created,
        "contacts_updated": contacts_updated,
        "errors": errors,
        "hubspot_list_id": hubspot_list_id,
    }

