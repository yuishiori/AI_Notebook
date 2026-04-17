from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from .. import models, schemas
from ..database import get_db
from datetime import date

router = APIRouter(prefix="/api/work-logs", tags=["work-logs"])

@router.get("/", response_model=List[schemas.WorkLog])
def read_work_logs(
    project_id: Optional[str] = None,
    workspace_id: Optional[str] = None,
    iso_week: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(models.WorkLog)
    if project_id:
        query = query.filter(models.WorkLog.project_id == project_id)
    if workspace_id:
        query = query.filter(models.WorkLog.workspace_id == workspace_id)
    if iso_week:
        query = query.filter(models.WorkLog.iso_week == iso_week)
    return query.all()

@router.post("/", response_model=schemas.WorkLog)
def create_work_log(work_log: schemas.WorkLogCreate, db: Session = Depends(get_db)):
    db_work_log = models.WorkLog(**work_log.model_dump())
    db.add(db_work_log)

    # Update project's last_updated_at
    project = db.query(models.Project).filter(models.Project.id == work_log.project_id).first()
    if project:
        project.last_updated_at = db_work_log.created_at

    db.commit()
    db.refresh(db_work_log)
    return db_work_log
