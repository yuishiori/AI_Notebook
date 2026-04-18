from sqlalchemy import Column, String, Text, DateTime, Date, Boolean, ForeignKey, Integer, JSON
from sqlalchemy.orm import relationship, DeclarativeBase
import uuid
from datetime import datetime

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String)
    picture_url = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    workspaces = relationship("Workspace", back_populates="owner")

class Workspace(Base):
    __tablename__ = "workspaces"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    owner_id = Column(String, ForeignKey("users.id"))
    name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    owner = relationship("User", back_populates="workspaces")
    projects = relationship("Project", back_populates="workspace")
    work_logs = relationship("WorkLog", back_populates="workspace")
    conversations = relationship("Conversation", back_populates="workspace")
    knowledge_sources = relationship("KnowledgeSource", back_populates="workspace")
    reports = relationship("Report", back_populates="workspace")
    briefings = relationship("Briefing", back_populates="workspace")

class Project(Base):
    __tablename__ = "projects"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id = Column(String, ForeignKey("workspaces.id"))
    name = Column(String, nullable=False)
    description = Column(Text)
    status = Column(String, default="active") # active, paused, done
    start_date = Column(Date)
    due_date = Column(Date, nullable=True)
    last_updated_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

    workspace = relationship("Workspace", back_populates="projects")
    kpis = relationship("ProjectKPI", back_populates="project")
    work_logs = relationship("WorkLog", back_populates="project")
    knowledge_sources = relationship("KnowledgeSource", back_populates="project")

class ProjectKPI(Base):
    __tablename__ = "project_kpis"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String, ForeignKey("projects.id"))
    title = Column(Text, nullable=False)
    target = Column(Text)
    source = Column(String) # ai_inferred, user_defined
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="kpis")
    work_logs = relationship("WorkLog", back_populates="kpi")

class WorkLog(Base):
    __tablename__ = "work_logs"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String, ForeignKey("projects.id"))
    workspace_id = Column(String, ForeignKey("workspaces.id"))
    log_date = Column(Date, nullable=False)
    iso_week = Column(String, nullable=False) # YYYY-Www
    content = Column(Text, nullable=False)
    related_kpi_id = Column(String, ForeignKey("project_kpis.id"), nullable=True)
    source = Column(String) # manual, ai_tool
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="work_logs")
    workspace = relationship("Workspace", back_populates="work_logs")
    kpi = relationship("ProjectKPI", back_populates="work_logs")

class Conversation(Base):
    __tablename__ = "conversations"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id = Column(String, ForeignKey("workspaces.id"))
    project_id = Column(String, ForeignKey("projects.id"), nullable=True)
    title = Column(String)
    pinned = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    workspace = relationship("Workspace", back_populates="conversations")
    project = relationship("Project")
    messages = relationship("Message", back_populates="conversation")

class Message(Base):
    __tablename__ = "messages"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(String, ForeignKey("conversations.id"))
    role = Column(String, nullable=False) # user, assistant, tool, system
    content = Column(Text)
    tool_calls = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    conversation = relationship("Conversation", back_populates="messages")

class KnowledgeSource(Base):
    __tablename__ = "knowledge_sources"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id = Column(String, ForeignKey("workspaces.id"))
    project_id = Column(String, ForeignKey("projects.id"), nullable=True)
    type = Column(String) # pptx, txt, md, url, meeting
    title = Column(String)
    original_path_or_url = Column(Text)
    imported_at = Column(DateTime, default=datetime.utcnow)

    workspace = relationship("Workspace", back_populates="knowledge_sources")
    project = relationship("Project", back_populates="knowledge_sources")

class Report(Base):
    __tablename__ = "reports"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id = Column(String, ForeignKey("workspaces.id"))
    iso_week = Column(String, nullable=False)
    file_path = Column(Text)
    status = Column(String, default="draft") # draft, finalized
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    workspace = relationship("Workspace", back_populates="reports")

class Briefing(Base):
    __tablename__ = "briefings"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id = Column(String, ForeignKey("workspaces.id"))
    date = Column(Date, nullable=False)
    content = Column(Text)
    file_path = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    workspace = relationship("Workspace", back_populates="briefings")
