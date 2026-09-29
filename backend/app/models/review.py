import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text, JSON, Boolean
from sqlalchemy.orm import relationship
from app.core.database import Base

class Review(Base):
    __tablename__ = "reviews"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String(36), ForeignKey("documents.id"), nullable=False, index=True)
    health_score = Column(Integer, default=100)        # 0 - 100
    completeness_score = Column(Integer, default=100)  # 0 - 100
    risk_score = Column(Integer, default=0)            # 0 - 100
    issues_data = Column(JSON, default=list)           # List of issues: {type, severity, clause, message, suggested_fix}
    professional_review_recommended = Column(Boolean, default=False)
    reviewed_by_lawyer_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    lawyer_notes = Column(Text, nullable=True)
    lawyer_verdict = Column(String(50), nullable=True) # approved, changes_requested, rejected
    created_at = Column(DateTime, default=datetime.utcnow)

    document = relationship("Document", back_populates="reviews")
    reviewer = relationship("User", foreign_keys=[reviewed_by_lawyer_id])
