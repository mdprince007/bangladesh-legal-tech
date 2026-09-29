import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text, JSON, Boolean
from sqlalchemy.orm import relationship
from app.core.database import Base

class Template(Base):
    __tablename__ = "templates"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    code = Column(String(100), unique=True, nullable=False, index=True)  # e.g., "BD_COMMERCIAL_LEASE"
    name = Column(String(255), nullable=False)
    name_bangla = Column(String(255), nullable=True)
    category = Column(String(100), nullable=False)  # lease, employment, corporate, notice
    jurisdiction = Column(String(100), default="Bangladesh")
    required_facts_schema = Column(JSON, default=dict)
    default_clause_order = Column(JSON, default=list)  # List of clause codes in sequence
    version = Column(Integer, default=1)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    clauses = relationship("Clause", back_populates="template", cascade="all, delete-orphan")

class Clause(Base):
    __tablename__ = "clauses"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    template_id = Column(String(36), ForeignKey("templates.id"), nullable=True, index=True)
    code = Column(String(100), unique=True, nullable=False, index=True)  # e.g. "LEASE_TERM_BALANCED"
    clause_type = Column(String(100), nullable=False)                    # term, rent, deposit, maintenance, termination, dispute
    title = Column(String(255), nullable=False)
    text_content = Column(Text, nullable=False)                          # Jinja2 / placeholder formatted template clause text
    explanation_bangla = Column(Text, nullable=False)                    # Plain Bangla explanation
    risk_level = Column(String(50), default="low")                       # low, medium, high
    style = Column(String(50), default="balanced")                       # balanced, landlord_friendly, tenant_friendly, etc.
    statutory_basis = Column(String(255), nullable=True)                 # e.g. "Section 106, Transfer of Property Act 1882"
    is_required = Column(Boolean, default=True)
    verification_status = Column(String(50), default="verified")         # verified, pending_review
    created_at = Column(DateTime, default=datetime.utcnow)

    template = relationship("Template", back_populates="clauses")
