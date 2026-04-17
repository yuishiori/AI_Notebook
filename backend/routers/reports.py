from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from .. import models, schemas
from ..database import get_db
from ..config import settings
import os

router = APIRouter(prefix="/api/reports", tags=["reports"])

@router.get("/", response_model=List[schemas.Report])
def read_reports(workspace_id: str, db: Session = Depends(get_db)):
    return db.query(models.Report).filter(models.Report.workspace_id == workspace_id).all()

@router.post("/generate", response_model=schemas.Report)
def generate_report(report_in: schemas.ReportCreate, db: Session = Depends(get_db)):
    # Logic to generate report using LLM will go here or in a background task
    # For now, just create the record
    db_report = models.Report(**report_in.model_dump())
    db.add(db_report)
    db.commit()
    db.refresh(db_report)
    return db_report

@router.patch("/{report_id}", response_model=schemas.Report)
def update_report(report_id: str, report_update: dict, db: Session = Depends(get_db)):
    db_report = db.query(models.Report).filter(models.Report.id == report_id).first()
    if not db_report:
        raise HTTPException(status_code=404, detail="Report not found")

    for key, value in report_update.items():
        setattr(db_report, key, value)

    db.commit()
    db.refresh(db_report)
    return db_report
