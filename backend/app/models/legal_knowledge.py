import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text, JSON, Boolean, Float
from sqlalchemy.orm import relationship
from app.core.database import Base

class Law(Base):
    __tablename__ = "laws"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    act_name = Column(String(255), nullable=False, index=True)
    act_year = Column(Integer, nullable=False)
    act_number = Column(String(50), nullable=True)     # e.g., "Act IV of 1882"
    jurisdiction = Column(String(100), default="Bangladesh")
    category = Column(String(100), nullable=True)      # property, contract, employment, penal, corporate
    status = Column(String(50), default="in_force")     # in_force, amended, repealed
    created_at = Column(DateTime, default=datetime.utcnow)

    sections = relationship("LawSection", back_populates="law", cascade="all, delete-orphan")

class LawSection(Base):
    __tablename__ = "law_sections"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    law_id = Column(String(36), ForeignKey("laws.id"), nullable=False, index=True)
    section_number = Column(String(50), nullable=False)  # e.g. "106", "107", "108"
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    verified_status = Column(String(50), default="verified")  # verified, provisional, unverified
    source_url = Column(String(500), nullable=True)           # e.g., bdlaws.minlaw.gov.bd
    effective_date = Column(String(50), nullable=True)
    amendment_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    law = relationship("Law", back_populates="sections")

class IngestedDocument(Base):
    __tablename__ = "ingested_documents"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(255), nullable=False)
    source_file = Column(String(255), nullable=False)
    file_type = Column(String(50), default="pdf")
    file_size_mb = Column(Float, default=0.0)
    total_pages = Column(Integer, default=0)
    total_lessons = Column(Integer, default=0)
    status = Column(String(50), default="indexed")
    created_at = Column(DateTime, default=datetime.utcnow)

    lessons = relationship("IngestedLesson", back_populates="document", cascade="all, delete-orphan")

class IngestedLesson(Base):
    __tablename__ = "ingested_lessons"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String(36), ForeignKey("ingested_documents.id"), nullable=False, index=True)
    chapter_num = Column(Integer, nullable=True)
    chapter_title = Column(String(255), nullable=True)
    lesson_title = Column(String(255), nullable=False)
    page_start = Column(Integer, nullable=True)
    page_end = Column(Integer, nullable=True)
    category = Column(String(100), default="general")
    content_summary = Column(Text, nullable=True)
    key_principles = Column(JSON, default=list)
    sample_clauses = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)

    document = relationship("IngestedDocument", back_populates="lessons")

