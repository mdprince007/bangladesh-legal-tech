import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base

class Document(Base):
    __tablename__ = "documents"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    org_id = Column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    matter_id = Column(String(36), ForeignKey("matters.id"), nullable=True, index=True)
    template_id = Column(String(36), ForeignKey("templates.id"), nullable=True)
    title = Column(String(255), nullable=False)
    status = Column(String(50), default="draft")  # draft, under_review, lawyer_reviewed, finalized
    language = Column(String(50), default="en")   # en, bn, bilingual
    structured_facts = Column(JSON, default=dict)
    selected_clauses = Column(JSON, default=list) # List of clause objects with codes, styles, texts
    full_text = Column(Text, nullable=False)
    book_grounding_score = Column(Integer, nullable=True)
    book_chapter_reference = Column(String(500), nullable=True)
    book_applied_rules = Column(JSON, nullable=True)
    draft_audit = Column(JSON, nullable=True)
    docx_path = Column(String(500), nullable=True)
    pdf_path = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    organization = relationship("Organization")
    matter = relationship("Matter", backref="documents")
    template = relationship("Template")
    versions = relationship("DocumentVersion", back_populates="document", cascade="all, delete-orphan")
    reviews = relationship("Review", back_populates="document", cascade="all, delete-orphan")

class DocumentVersion(Base):
    __tablename__ = "document_versions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String(36), ForeignKey("documents.id"), nullable=False, index=True)
    version_num = Column(Integer, nullable=False)
    full_text = Column(Text, nullable=False)
    structured_facts = Column(JSON, default=dict)
    changed_by = Column(String(36), nullable=True)
    change_summary = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    document = relationship("Document", back_populates="versions")
