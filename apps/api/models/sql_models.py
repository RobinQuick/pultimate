import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from ..database import Base


def generate_uuid():
    return str(uuid.uuid4())

class Tenant(Base):
    __tablename__ = "tenants"
    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False)
    slug = Column(String, unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    users = relationship("User", back_populates="tenant")
    workspaces = relationship("Workspace", back_populates="tenant")

class Workspace(Base):
    __tablename__ = "workspaces"
    id = Column(String, primary_key=True, default=generate_uuid)
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False)
    name = Column(String, nullable=False)
    
    tenant = relationship("Tenant", back_populates="workspaces")
    decks = relationship("Deck", back_populates="workspace")
    templates = relationship("Template", back_populates="workspace")

class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, default=generate_uuid)
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    
    tenant = relationship("Tenant", back_populates="users")
    decks = relationship("Deck", back_populates="owner")

class Template(Base):
    __tablename__ = "templates"
    id = Column(String, primary_key=True, default=generate_uuid)
    workspace_id = Column(String, ForeignKey("workspaces.id"), nullable=False)
    name = Column(String, nullable=False)
    is_archived = Column(Boolean, default=False)
    
    workspace = relationship("Workspace", back_populates="templates")
    versions = relationship("TemplateVersion", back_populates="template")

class TemplateVersion(Base):
    __tablename__ = "template_versions"
    id = Column(String, primary_key=True, default=generate_uuid)
    template_id = Column(String, ForeignKey("templates.id"), nullable=False)
    version_num = Column(Integer, nullable=False)
    s3_key_potx = Column(String, nullable=False)
    config_json = Column(JSONB, nullable=True) # Stores TemplateSpec v1
    status = Column(String, default="DRAFT") # DRAFT, PUBLISHED
    published_at = Column(DateTime, nullable=True)
    
    template = relationship("Template", back_populates="versions")

class Deck(Base):
    __tablename__ = "decks"
    id = Column(String, primary_key=True, default=generate_uuid)
    workspace_id = Column(String, ForeignKey("workspaces.id"), nullable=False)
    owner_id = Column(String, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
    
    workspace = relationship("Workspace", back_populates="decks")
    owner = relationship("User", back_populates="decks")
    files = relationship("DeckFile", back_populates="deck")
    analyses = relationship("Analysis", back_populates="deck")

class DeckFile(Base):
    __tablename__ = "deck_files"
    id = Column(String, primary_key=True, default=generate_uuid)
    deck_id = Column(String, ForeignKey("decks.id"), nullable=False)
    type = Column(String, nullable=False) # SOURCE, CLEANED, REPORT
    s3_key = Column(String, nullable=False)
    filename = Column(String, nullable=False)
    
    deck = relationship("Deck", back_populates="files")

class Analysis(Base):
    __tablename__ = "analyses"
    id = Column(String, primary_key=True, default=generate_uuid)
    deck_id = Column(String, ForeignKey("decks.id"), nullable=False)
    status = Column(String, default="PENDING") # PENDING, RUNNING, COMPLETED, FAILED
    score = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    deck = relationship("Deck", back_populates="analyses")
    findings = relationship("Finding", back_populates="analysis")

class Finding(Base):
    __tablename__ = "findings"
    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(String, ForeignKey("analyses.id"), nullable=False)
    slide_index = Column(Integer)
    rule_id = Column(String)
    severity = Column(String)
    message = Column(String)
    
    analysis = relationship("Analysis", back_populates="findings")
