from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from .. import models, schemas
from ..database import get_db
from ..dependencies import get_current_user
from ..config import settings
import os

router = APIRouter(prefix="/api/reports", tags=["reports"])

@router.get("/", response_model=List[schemas.Report])
def read_reports(workspace_id: str, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    ws = db.query(models.Workspace).filter(models.Workspace.id == workspace_id, models.Workspace.owner_id == current_user.id).first()
    if not ws: raise HTTPException(status_code=403, detail="Not authorized")
    return db.query(models.Report).filter(models.Report.workspace_id == workspace_id).all()
