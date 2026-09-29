import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text, JSON, Float
from sqlalchemy.orm import relationship
from app.core.database import Base

class FeedbackEntry(Base):
    __tablename__ = "feedback_entries"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String(36), ForeignKey("documents.id"), nullable=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    rating = Column(Integer, nullable=False)           # 1 (poor) to 5 (excellent)
    feedback_category = Column(String(50), nullable=False) # correct, missing_authority, wrong_citation, legally_risky, poor_drafting
    original_text = Column(Text, nullable=True)
    corrected_text = Column(Text, nullable=True)
    reviewer_reasoning = Column(Text, nullable=True)
    is_promoted_to_eval = Column(String(50), default="no") # no, approved, pending
    created_at = Column(DateTime, default=datetime.utcnow)

class EvaluationCase(Base):
    __tablename__ = "evaluation_cases"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    category = Column(String(100), nullable=False)    # e.g., "commercial_lease_intake", "anti_hallucination"
    input_prompt = Column(Text, nullable=False)
    expected_facts = Column(JSON, default=dict)
    expected_clauses = Column(JSON, default=list)
    forbidden_terms = Column(JSON, default=list)      # Words/statutes that should NEVER be hallucinated
    benchmark_score = Column(Float, default=100.0)
    last_run_score = Column(Float, nullable=True)
    last_run_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
