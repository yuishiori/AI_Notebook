from pydantic import BaseModel, ConfigDict
from datetime import datetime, date
from typing import Optional, List, Dict, Any, Literal

# --- Workspace ---
class WorkspaceBase(BaseModel):
    name: str

class WorkspaceCreate(WorkspaceBase):
    pass

class Workspace(WorkspaceBase):
    model_config = ConfigDict(from_attributes=True)
    id: str
    created_at: datetime

# --- Project KPI ---
class ProjectKPIBase(BaseModel):
    title: str
    target: Optional[str] = None
    source: str = "user_defined" # ai_inferred, user_defined

class ProjectKPICreate(ProjectKPIBase):
    project_id: str

class ProjectKPI(ProjectKPIBase):
    model_config = ConfigDict(from_attributes=True)
    id: str
    project_id: str
    created_at: datetime

# --- Project ---
class ProjectBase(BaseModel):
    name: str
    description: Optional[str] = None
    status: str = "active" # active, paused, done
    start_date: Optional[date] = None
    due_date: Optional[date] = None

class ProjectCreate(ProjectBase):
    workspace_id: str

class Project(ProjectBase):
    model_config = ConfigDict(from_attributes=True)
    id: str
    workspace_id: str
    last_updated_at: datetime
    created_at: datetime
    kpis: List[ProjectKPI] = []

# --- Work Log ---
class WorkLogBase(BaseModel):
    project_id: str
    workspace_id: str
    log_date: date
    iso_week: str # YYYY-Www
    content: str
    related_kpi_id: Optional[str] = None
    source: str = "manual" # manual, ai_tool

class WorkLogCreate(WorkLogBase):
    pass

class WorkLog(WorkLogBase):
    model_config = ConfigDict(from_attributes=True)
    id: str
    created_at: datetime

# --- Message ---
class MessageBase(BaseModel):
    role: str # user, assistant, tool, system
    content: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None

class MessageCreate(MessageBase):
    conversation_id: str

class Message(MessageBase):
    model_config = ConfigDict(from_attributes=True)
    id: str
    conversation_id: str
    created_at: datetime

# --- Conversation ---
class ConversationBase(BaseModel):
    workspace_id: str
    title: Optional[str] = None
    pinned: bool = False

class ConversationCreate(ConversationBase):
    pass

class Conversation(ConversationBase):
    model_config = ConfigDict(from_attributes=True)
    id: str
    workspace_id: str
    created_at: datetime
    updated_at: datetime
    messages: List[Message] = []

# --- Knowledge Source ---
class KnowledgeSourceBase(BaseModel):
    workspace_id: str
    project_id: Optional[str] = None
    type: str # pptx, txt, md, url, meeting
    title: str
    original_path_or_url: Optional[str] = None

class KnowledgeSourceCreate(KnowledgeSourceBase):
    pass

class KnowledgeSource(KnowledgeSourceBase):
    model_config = ConfigDict(from_attributes=True)
    id: str
    workspace_id: str
    imported_at: datetime

# --- Report ---
class ReportBase(BaseModel):
    workspace_id: str
    iso_week: str
    file_path: Optional[str] = None
    status: str = "draft" # draft, finalized

class ReportCreate(ReportBase):
    pass

class Report(ReportBase):
    model_config = ConfigDict(from_attributes=True)
    id: str
    created_at: datetime
    updated_at: datetime

# --- Briefing ---
class BriefingBase(BaseModel):
    workspace_id: str
    date: date
    content: str
    file_path: Optional[str] = None

class BriefingCreate(BriefingBase):
    pass

class Briefing(BriefingBase):
    model_config = ConfigDict(from_attributes=True)
    id: str
    created_at: datetime

# --- Chat Request ---
class ChatRequest(BaseModel):
    conversation_id: str
    message: str
    workspace_id: str
