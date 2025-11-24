"""Universal Robots API endpoints"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import logging

from app.core.db import get_db
from app.core.orm import OrganizationORM, LeadORM
from app.core.orm_robots import (
    RobotORM, RobotRunORM, RobotRunUrlORM, RobotRunRowORM,
    RobotMode, RobotRunStatus, URLStatus
)
from app.services.robots_ai import RobotsAIService
from app.services.robots_engine import RobotsEngine, RobotExecutionError
from app.api.routes_settings import get_or_create_default_org

logger = logging.getLogger(__name__)
router = APIRouter()


# ============================================================================
# Request/Response Models
# ============================================================================

class RobotAICreateRequest(BaseModel):
    prompt: str
    sample_url: Optional[str] = None


class RobotSaveRequest(BaseModel):
    name: str
    description: Optional[str] = None
    prompt: Optional[str] = None
    sample_url: Optional[str] = None
    field_schema: List[dict] = Field(..., alias="schema")  # Field schema definition (using alias to avoid shadowing BaseModel.schema)
    workflow_spec: dict
    
    class Config:
        populate_by_name = True  # Allow both field_schema and schema in JSON
    
    class Config:
        # Allow field name "schema" even though it shadows BaseModel attribute
        populate_by_name = True


class RobotTestRequest(BaseModel):
    url: str
    search_query: Optional[str] = None  # For interactive scraping


class RobotRunRequest(BaseModel):
    urls: List[str]
    search_query: Optional[str] = None  # For interactive scraping (applied to all URLs)


class ImportLeadsRequest(BaseModel):
    field_mapping: dict  # {"robot_field": "lead_field"}
    row_ids: Optional[List[int]] = None  # If None, import all rows


# ============================================================================
# Robot CRUD
# ============================================================================

@router.post("/robots/ai")
async def generate_robot_ai(
    request: RobotAICreateRequest,
    db: Session = Depends(get_db),
):
    """Generate robot schema and workflow from natural language prompt"""
    try:
        result = await RobotsAIService.generate_robot_from_prompt(
            request.prompt,
            request.sample_url
        )
        return {
            "name": f"Robot: {request.prompt[:50]}...",
            "schema": result.get("schema", []),
            "workflow_spec": result.get("workflow_spec", {}),
        }
    except Exception as e:
        logger.error(f"Failed to generate robot: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to generate robot: {str(e)}")


@router.post("/robots")
def create_robot(
    request: RobotSaveRequest,
    db: Session = Depends(get_db),
):
    """Create a new robot"""
    org = get_or_create_default_org(db)
    
    robot = RobotORM(
        organization_id=org.id,
        name=request.name,
        description=request.description,
        prompt=request.prompt,
        sample_url=request.sample_url,
        mode=RobotMode.ai if request.prompt else RobotMode.manual,
        schema=request.field_schema,
        workflow_spec=request.workflow_spec,
    )
    
    db.add(robot)
    db.commit()
    db.refresh(robot)
    
    return {
        "id": robot.id,
        "name": robot.name,
        "description": robot.description,
        "mode": robot.mode.value,
        "schema": robot.schema,
        "workflow_spec": robot.workflow_spec,
        "created_at": robot.created_at.isoformat(),
    }


@router.get("/robots")
def list_robots(
    db: Session = Depends(get_db),
):
    """List all robots"""
    org = get_or_create_default_org(db)
    
    robots = db.query(RobotORM).filter(
        RobotORM.organization_id == org.id
    ).order_by(RobotORM.created_at.desc()).all()
    
    result = []
    for robot in robots:
        # Get last run info
        last_run = db.query(RobotRunORM).filter(
            RobotRunORM.robot_id == robot.id
        ).order_by(RobotRunORM.created_at.desc()).first()
        
        result.append({
            "id": robot.id,
            "name": robot.name,
            "description": robot.description,
            "mode": robot.mode.value,
            "created_at": robot.created_at.isoformat(),
            "updated_at": robot.updated_at.isoformat(),
            "last_run": {
                "id": last_run.id,
                "status": last_run.status.value,
                "total_rows": last_run.total_rows,
                "created_at": last_run.created_at.isoformat(),
            } if last_run else None,
        })
    
    return result


@router.get("/robots/{robot_id}")
def get_robot(
    robot_id: int,
    db: Session = Depends(get_db),
):
    """Get robot details"""
    org = get_or_create_default_org(db)
    
    robot = db.query(RobotORM).filter(
        RobotORM.organization_id == org.id,
        RobotORM.id == robot_id
    ).first()
    
    if not robot:
        raise HTTPException(status_code=404, detail="Robot not found")
    
    # Get runs
    runs = db.query(RobotRunORM).filter(
        RobotRunORM.robot_id == robot_id
    ).order_by(RobotRunORM.created_at.desc()).limit(10).all()
    
    return {
        "id": robot.id,
        "name": robot.name,
        "description": robot.description,
        "mode": robot.mode.value,
        "prompt": robot.prompt,
        "sample_url": robot.sample_url,
        "schema": robot.schema,
        "workflow_spec": robot.workflow_spec,
        "created_at": robot.created_at.isoformat(),
        "updated_at": robot.updated_at.isoformat(),
        "runs": [
            {
                "id": run.id,
                "status": run.status.value,
                "total_urls": run.total_urls,
                "processed_urls": run.processed_urls,
                "total_rows": run.total_rows,
                "created_at": run.created_at.isoformat(),
                "started_at": run.started_at.isoformat() if run.started_at else None,
                "finished_at": run.finished_at.isoformat() if run.finished_at else None,
            }
            for run in runs
        ],
    }


@router.post("/robots/{robot_id}/test")
def test_robot(
    robot_id: int,
    request: RobotTestRequest,
    db: Session = Depends(get_db),
):
    """Test robot on a single URL"""
    org = get_or_create_default_org(db)
    
    robot = db.query(RobotORM).filter(
        RobotORM.organization_id == org.id,
        RobotORM.id == robot_id
    ).first()
    
    if not robot:
        raise HTTPException(status_code=404, detail="Robot not found")
    
    try:
        rows = RobotsEngine.execute_workflow(
            request.url,
            robot.workflow_spec,
            robot.schema,
            search_query=request.search_query
        )
        return {
            "url": request.url,
            "rows_extracted": len(rows),
            "data": rows[:5],  # Return first 5 for preview
            "total": len(rows),
        }
    except RobotExecutionError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Test failed: {str(e)}")


# ============================================================================
# Robot Runs
# ============================================================================

@router.post("/robots/{robot_id}/runs")
def create_robot_run(
    robot_id: int,
    request: RobotRunRequest,
    db: Session = Depends(get_db),
):
    """Create and start a robot run"""
    org = get_or_create_default_org(db)
    
    robot = db.query(RobotORM).filter(
        RobotORM.organization_id == org.id,
        RobotORM.id == robot_id
    ).first()
    
    if not robot:
        raise HTTPException(status_code=404, detail="Robot not found")
    
    # Create run
    run = RobotRunORM(
        organization_id=org.id,
        robot_id=robot_id,
        status=RobotRunStatus.queued,
        total_urls=len(request.urls),
        started_at=datetime.utcnow(),
    )
    db.add(run)
    db.flush()
    
    # Add URLs
    for url in request.urls:
        url_record = RobotRunUrlORM(
            run_id=run.id,
            url=url,
            status=URLStatus.pending,
        )
        db.add(url_record)
    
    db.commit()
    db.refresh(run)
    
    # TODO: Enqueue background task to process URLs
    # For now, we'll process synchronously (not ideal for production)
    _process_robot_run_sync(db, run.id, robot, search_query=request.search_query)
    
    return {
        "id": run.id,
        "status": run.status.value,
        "total_urls": run.total_urls,
        "total_rows": run.total_rows,
        "created_at": run.created_at.isoformat(),
    }


def _process_robot_run_sync(db: Session, run_id: int, robot: RobotORM, search_query: Optional[str] = None):
    """Process robot run synchronously (should be background task in production)"""
    run = db.query(RobotRunORM).filter(RobotRunORM.id == run_id).first()
    if not run:
        return
    
    run.status = RobotRunStatus.running
    db.commit()
    
    urls = db.query(RobotRunUrlORM).filter(
        RobotRunUrlORM.run_id == run_id,
        RobotRunUrlORM.status == URLStatus.pending
    ).all()
    
    total_rows = 0
    
    for url_record in urls:
        try:
            rows = RobotsEngine.execute_workflow(
                url_record.url,
                robot.workflow_spec,
                robot.schema,
                search_query=search_query
            )
            
            # Save rows
            for row_data in rows:
                row = RobotRunRowORM(
                    run_id=run_id,
                    source_url=url_record.url,
                    data=row_data,
                )
                db.add(row)
                total_rows += 1
            
            url_record.status = URLStatus.done
            run.processed_urls += 1
            
        except Exception as e:
            url_record.status = URLStatus.error
            url_record.error = str(e)[:500]
            logger.error(f"Failed to process URL {url_record.url}: {e}")
        
        db.commit()
    
    run.total_rows = total_rows
    run.status = RobotRunStatus.completed
    run.finished_at = datetime.utcnow()
    db.commit()


@router.get("/robots/{robot_id}/runs")
def list_robot_runs(
    robot_id: int,
    db: Session = Depends(get_db),
):
    """List runs for a robot"""
    org = get_or_create_default_org(db)
    
    runs = db.query(RobotRunORM).filter(
        RobotRunORM.organization_id == org.id,
        RobotRunORM.robot_id == robot_id
    ).order_by(RobotRunORM.created_at.desc()).all()
    
    return [
        {
            "id": run.id,
            "status": run.status.value,
            "total_urls": run.total_urls,
            "processed_urls": run.processed_urls,
            "total_rows": run.total_rows,
            "created_at": run.created_at.isoformat(),
            "started_at": run.started_at.isoformat() if run.started_at else None,
            "finished_at": run.finished_at.isoformat() if run.finished_at else None,
        }
        for run in runs
    ]


@router.get("/robot-runs/{run_id}")
def get_robot_run(
    run_id: int,
    db: Session = Depends(get_db),
):
    """Get robot run details"""
    org = get_or_create_default_org(db)
    
    run = db.query(RobotRunORM).filter(
        RobotRunORM.organization_id == org.id,
        RobotRunORM.id == run_id
    ).first()
    
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    
    robot = db.query(RobotORM).filter(RobotORM.id == run.robot_id).first()
    
    return {
        "id": run.id,
        "robot_id": run.robot_id,
        "robot_name": robot.name if robot else None,
        "status": run.status.value,
        "total_urls": run.total_urls,
        "processed_urls": run.processed_urls,
        "total_rows": run.total_rows,
        "error": run.error,
        "created_at": run.created_at.isoformat(),
        "started_at": run.started_at.isoformat() if run.started_at else None,
        "finished_at": run.finished_at.isoformat() if run.finished_at else None,
    }


@router.get("/robot-runs/{run_id}/rows")
def get_robot_run_rows(
    run_id: int,
    limit: int = Query(100, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """Get paginated rows from a robot run"""
    org = get_or_create_default_org(db)
    
    # Verify run belongs to org
    run = db.query(RobotRunORM).filter(
        RobotRunORM.organization_id == org.id,
        RobotRunORM.id == run_id
    ).first()
    
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    
    # Get rows
    rows = db.query(RobotRunRowORM).filter(
        RobotRunRowORM.run_id == run_id
    ).order_by(RobotRunRowORM.id).limit(limit).offset(offset).all()
    
    total = db.query(RobotRunRowORM).filter(
        RobotRunRowORM.run_id == run_id
    ).count()
    
    return {
        "rows": [
            {
                "id": row.id,
                "source_url": row.source_url,
                "data": row.data,
                "created_at": row.created_at.isoformat(),
            }
            for row in rows
        ],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


# ============================================================================
# Import Leads
# ============================================================================

@router.post("/robot-runs/{run_id}/import-leads")
def import_robot_run_as_leads(
    run_id: int,
    request: ImportLeadsRequest,
    db: Session = Depends(get_db),
):
    """Import robot run rows as leads"""
    org = get_or_create_default_org(db)
    
    # Verify run
    run = db.query(RobotRunORM).filter(
        RobotRunORM.organization_id == org.id,
        RobotRunORM.id == run_id
    ).first()
    
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    
    robot = db.query(RobotORM).filter(RobotORM.id == run.robot_id).first()
    if not robot:
        raise HTTPException(status_code=404, detail="Robot not found")
    
    # Get rows to import
    query = db.query(RobotRunRowORM).filter(RobotRunRowORM.run_id == run_id)
    if request.row_ids:
        query = query.filter(RobotRunRowORM.id.in_(request.row_ids))
    
    rows = query.all()
    
    if not rows:
        raise HTTPException(status_code=400, detail="No rows to import")
    
    # Import leads
    imported_count = 0
    lead_ids = []
    
    for row in rows:
        data = row.data
        
        # Map fields
        name = data.get(request.field_mapping.get("name", "name"))
        website = data.get(request.field_mapping.get("website", "website"))
        email = data.get(request.field_mapping.get("email", "email"))
        phone = data.get(request.field_mapping.get("phone", "phone"))
        city = data.get(request.field_mapping.get("city", "city"))
        country = data.get(request.field_mapping.get("country", "country"))
        address = data.get(request.field_mapping.get("address", "address"))
        
        # Create lead directly
        try:
            lead = LeadORM(
                organization_id=org.id,
                name=name,
                website=website,
                emails=[email] if email else [],
                phones=[phone] if phone else [],
                city=city,
                country=country,
                address=address,
                source="robot",
                sources=["robot"],
                source_robot_run_id=run_id,
            )
            db.add(lead)
            db.flush()
            lead_ids.append(lead.id)
            imported_count += 1
        except Exception as e:
            logger.error(f"Failed to import lead from row {row.id}: {e}")
            continue
    
    db.commit()
    
    return {
        "imported": imported_count,
        "lead_ids": lead_ids,
        "robot_name": robot.name,
    }

