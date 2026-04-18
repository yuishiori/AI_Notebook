from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from .. import models, schemas
from ..database import get_db
from ..dependencies import get_current_user
from datetime import date

router = APIRouter(prefix="/api/briefings", tags=["briefings"])

@router.get("/latest", response_model=Optional[schemas.Briefing])
def read_latest_briefing(workspace_id: str, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    ws = db.query(models.Workspace).filter(models.Workspace.id == workspace_id, models.Workspace.owner_id == current_user.id).first()
    if not ws: raise HTTPException(status_code=403, detail="Not authorized")
    return db.query(models.Briefing).filter(models.Briefing.workspace_id == workspace_id).order_by(models.Briefing.date.desc()).first()
