from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from .. import models, schemas
from ..database import get_db
from ..dependencies import get_current_user

router = APIRouter(prefix="/api/projects", tags=["projects"])

@router.get("/", response_model=List[schemas.Project])
def read_projects(workspace_id: Optional[str] = None, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    query = db.query(models.Project).join(models.Workspace)
    query = query.filter(models.Workspace.owner_id == current_user.id)
    if workspace_id:
        query = query.filter(models.Project.workspace_id == workspace_id)
    return query.all()

@router.post("/", response_model=schemas.Project)
def create_project(project: schemas.ProjectCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    # Verify workspace belongs to user
    ws = db.query(models.Workspace).filter(models.Workspace.id == project.workspace_id, models.Workspace.owner_id == current_user.id).first()
    if not ws:
        raise HTTPException(status_code=403, detail="Not authorized to access this workspace")
    db_project = models.Project(**project.model_dump())
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project

@router.get("/{project_id}", response_model=schemas.Project)
def read_project(project_id: str, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    db_project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if db_project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    # Verify workspace belongs to user
    ws = db.query(models.Workspace).filter(models.Workspace.id == db_project.workspace_id, models.Workspace.owner_id == current_user.id).first()
    if not ws:
        raise HTTPException(status_code=403, detail="Not authorized to access this project")
    return db_project
