from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from .. import models, schemas
from ..database import get_db
from ..dependencies import get_current_user

router = APIRouter(prefix="/api/conversations", tags=["conversations"])

@router.get("/", response_model=List[schemas.Conversation])
def read_conversations(workspace_id: str, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    # Verify workspace ownership
    ws = db.query(models.Workspace).filter(models.Workspace.id == workspace_id, models.Workspace.owner_id == current_user.id).first()
    if not ws:
        raise HTTPException(status_code=403, detail="Not authorized")
    return db.query(models.Conversation).filter(models.Conversation.workspace_id == workspace_id).order_by(models.Conversation.updated_at.desc()).all()

@router.post("/", response_model=schemas.Conversation)
def create_conversation(conversation: schemas.ConversationCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    # Verify workspace ownership
    ws = db.query(models.Workspace).filter(models.Workspace.id == conversation.workspace_id, models.Workspace.owner_id == current_user.id).first()
    if not ws:
        raise HTTPException(status_code=403, detail="Not authorized")
    db_conversation = models.Conversation(**conversation.model_dump())
    db.add(db_conversation)
    db.commit()
    db.refresh(db_conversation)
    return db_conversation

@router.get("/{conversation_id}/messages", response_model=List[schemas.Message])
def read_messages(conversation_id: str, db: Session = Depends(get_db)):
    return db.query(models.Message).filter(models.Message.conversation_id == conversation_id).order_by(models.Message.created_at.asc()).all()

@router.delete("/{conversation_id}")
def delete_conversation(conversation_id: str, db: Session = Depends(get_db)):
    db_conversation = db.query(models.Conversation).filter(models.Conversation.id == conversation_id).first()
    if not db_conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Delete related messages first
    db.query(models.Message).filter(models.Message.conversation_id == conversation_id).delete()
    db.delete(db_conversation)
    db.commit()
    return {"message": "Conversation deleted"}
