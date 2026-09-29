import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base

class Matter(Base):
    __tablename__ = "matters"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    org_id = Column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=False)
    matter_type = Column(String(100), nullable=False)  # commercial_lease, residential_rent, employment, nda, demand_notice, etc.
    client_name = Column(String(255), nullable=True)
    status = Column(String(50), default="active")       # active, draft_ready, in_review, finalized, archived
    facts_data = Column(JSON, default=dict)            # Structured fact model snapshot
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    organization = relationship("Organization", backref="matters")
    user = relationship("User", backref="matters")
