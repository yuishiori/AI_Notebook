from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from .. import models, schemas
from ..database import get_db
from ..ai.vector_db import get_vector_db
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
    db: Session = Depends(get_db)
):
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
    # Basic chunking
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

@router.post("/import/url", response_model=schemas.KnowledgeSource)
def import_url(
    workspace_id: str = Form(...),
    project_id: Optional[str] = Form(None),
    url: str = Form(...),
    db: Session = Depends(get_db)
):
    downloaded = trafilatura.fetch_url(url)
    if not downloaded:
        raise HTTPException(status_code=400, detail="Failed to fetch URL")

    content = trafilatura.extract(downloaded)
    title = trafilatura.extract_metadata(downloaded).title if trafilatura.extract_metadata(downloaded) else url

    db_source = models.KnowledgeSource(
        workspace_id=workspace_id,
        project_id=project_id,
        type="url",
        title=title,
        original_path_or_url=url
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
        "type": "url",
        "title": title,
        "chunk_index": i
    } for i in range(len(chunks))]
    ids = [f"{db_source.id}_{i}" for i in range(len(chunks))]

    vector_db.add_documents(workspace_id, chunks, metadatas, ids)

    return db_source

@router.post("/import/pptx", response_model=schemas.KnowledgeSource)
async def import_pptx(
    workspace_id: str = Form(...),
    project_id: Optional[str] = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    if not file.filename.endswith(".pptx"):
        raise HTTPException(status_code=400, detail="Only PPTX files are supported")

    file_content = await file.read()
    temp_path = os.path.join(settings.uploads_dir, f"{uuid.uuid4()}_{file.filename}")
    with open(temp_path, "wb") as f:
        f.write(file_content)

    prs = Presentation(temp_path)
    text_runs = []
    for slide in prs.slides:
        for shape in slide.shapes:
            if hasattr(shape, "text"):
                text_runs.append(shape.text)
        if slide.has_notes_slide:
            text_runs.append(slide.notes_slide.notes_text_frame.text)

    full_text = "\n".join(text_runs)

    db_source = models.KnowledgeSource(
        workspace_id=workspace_id,
        project_id=project_id,
        type="pptx",
        title=file.filename,
        original_path_or_url=temp_path
    )
    db.add(db_source)
    db.commit()
    db.refresh(db_source)

    # Vectorize
    vector_db = get_vector_db()
    chunk_size = settings.chunk_size
    chunks = [full_text[i:i + chunk_size] for i in range(0, len(full_text), chunk_size - settings.chunk_overlap)]

    metadatas = [{
        "source_id": db_source.id,
        "project_id": project_id or "",
        "type": "pptx",
        "title": file.filename,
        "chunk_index": i
    } for i in range(len(chunks))]
    ids = [f"{db_source.id}_{i}" for i in range(len(chunks))]

    vector_db.add_documents(workspace_id, chunks, metadatas, ids)

    return db_source

@router.get("/", response_model=List[schemas.KnowledgeSource])
def read_knowledge_sources(workspace_id: str, db: Session = Depends(get_db)):
    return db.query(models.KnowledgeSource).filter(models.KnowledgeSource.workspace_id == workspace_id).all()
