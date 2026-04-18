from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from .. import models, schemas
from ..database import get_db
from ..ai.vector_db import get_vector_db
from ..dependencies import get_current_user
import os
import uuid
from datetime import datetime
from ..config import settings
import trafilatura
from pptx import Presentation

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])

@router.post("/import/text", response_model=schemas.KnowledgeSource)
def import_text(
    workspace_id: str = Form(...),
    project_id: Optional[str] = Form(None),
    title: str = Form(...),
    content: str = Form(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Verify workspace ownership
    ws = db.query(models.Workspace).filter(models.Workspace.id == workspace_id, models.Workspace.owner_id == current_user.id).first()
    if not ws: raise HTTPException(status_code=403, detail="Not authorized")

    db_source = models.KnowledgeSource(
        workspace_id=workspace_id,
        project_id=project_id,
        type="txt",
        title=title
    )
    db.add(db_source)
    db.commit()
    db.refresh(db_source)

    # Vectorize
    vector_db = get_vector_db()
    chunk_size = settings.chunk_size
    chunks = [content[i:i + chunk_size] for i in range(0, len(content), chunk_size - settings.chunk_overlap)]

    metadatas = [{
        "source_id": db_source.id,
        "project_id": project_id or "",
        "type": "txt",
        "title": title,
        "chunk_index": i
    } for i in range(len(chunks))]
    ids = [f"{db_source.id}_{i}" for i in range(len(chunks))]

    vector_db.add_documents(workspace_id, chunks, metadatas, ids)

    return db_source

@router.get("/", response_model=List[schemas.KnowledgeSource])
def read_knowledge_sources(workspace_id: str, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    # Verify workspace ownership
    ws = db.query(models.Workspace).filter(models.Workspace.id == workspace_id, models.Workspace.owner_id == current_user.id).first()
    if not ws: raise HTTPException(status_code=403, detail="Not authorized")
    return db.query(models.KnowledgeSource).filter(models.KnowledgeSource.workspace_id == workspace_id).all()
