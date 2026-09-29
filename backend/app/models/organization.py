import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime
from app.core.database import Base

class Organization(Base):
    __tablename__ = "organizations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    org_type = Column(String(50), default="individual")  # individual, law_firm, corporate, enterprise
    plan = Column(String(50), default="starter")          # starter, pro, firm, enterprise
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
