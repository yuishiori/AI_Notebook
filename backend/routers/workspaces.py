from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/api/workspaces", tags=["workspaces"])

@router.get("/", response_model=List[schemas.Workspace])
def read_workspaces(db: Session = Depends(get_db)):
    return db.query(models.Workspace).all()

@router.post("/", response_model=schemas.Workspace)
def create_workspace(workspace: schemas.WorkspaceCreate, db: Session = Depends(get_db)):
    db_workspace = models.Workspace(name=workspace.name)
    db.add(db_workspace)
    db.commit()
    db.refresh(db_workspace)
    return db_workspace
