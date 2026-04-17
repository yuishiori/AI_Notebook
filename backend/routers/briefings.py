from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from .. import models, schemas
from ..database import get_db
from datetime import date

router = APIRouter(prefix="/api/briefings", tags=["briefings"])

@router.get("/latest", response_model=Optional[schemas.Briefing])
def read_latest_briefing(workspace_id: str, db: Session = Depends(get_db)):
    return db.query(models.Briefing).filter(models.Briefing.workspace_id == workspace_id).order_by(models.Briefing.date.desc()).first()

@router.post("/trigger", response_model=schemas.Briefing)
def trigger_briefing(workspace_id: str, db: Session = Depends(get_db)):
    # Manual trigger logic for briefing
    # This should call the same logic as the scheduler
    # For now, just a placeholder
    db_briefing = models.Briefing(
        workspace_id=workspace_id,
        date=date.today(),
        content="This is a manually triggered briefing placeholder."
    )
    db.add(db_briefing)
    db.commit()
    db.refresh(db_briefing)
    return db_briefing
