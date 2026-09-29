import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Text, JSON, Float
from app.core.database import Base

class DeedRecord(Base):
    __tablename__ = "deed_records"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    deed_title = Column(String(255), nullable=False)
    deed_type = Column(String(100), default="saf_kabala")  # saf_kabala, heba, bonton_nama, baya_dalil, danpatra, etc.
    deed_number = Column(String(100), nullable=True)
    registration_year = Column(Integer, nullable=True)
    registration_date = Column(String(100), nullable=True)
    sub_registry_office = Column(String(150), nullable=True)
    district = Column(String(100), nullable=True)
    thana = Column(String(100), nullable=True)
    mouza = Column(String(150), nullable=True)
    jl_number = Column(String(50), nullable=True)

    parties = Column(JSON, default=dict)
    schedule = Column(JSON, default=dict)
    boundaries = Column(JSON, default=dict)
    financials = Column(JSON, default=dict)
    chain_of_title = Column(JSON, default=dict)
    unclear_texts = Column(JSON, default=list)

    # Document Vision & HTR Pipeline Fields
    image_quality_report = Column(JSON, default=dict)
    layout_zones = Column(JSON, default=list)
    text_lines = Column(JSON, default=list)
    structured_fields = Column(JSON, default=dict)
    reading_report = Column(JSON, default=dict)
    page_image_paths = Column(JSON, default=list)

    overall_confidence_score = Column(Integer, default=90)
    clarity_rating = Column(String(50), default="moderate")  # high, moderate, faded_unclear
    fraud_risk_score = Column(Integer, default=15)  # 0-100
    fraud_risk_level = Column(String(50), default="low")  # low, suspicious, high_risk
    fraud_assessment = Column(JSON, default=dict)

    original_file_path = Column(String(500), nullable=True)
    enhanced_image_path = Column(String(500), nullable=True)
    docx_path = Column(String(500), nullable=True)
    pdf_path = Column(String(500), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class DeedCorrectionRecord(Base):
    """
    Phase 20: Verified Training Data from User Corrections.
    Stores human-verified corrections with source coordinates,
    AI predictions, and confidence scores for future Bengali Land Deed HTR model fine-tuning.
    """
    __tablename__ = "deed_corrections"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    deed_id = Column(String(36), nullable=False)
    field_key = Column(String(100), nullable=False)
    line_index = Column(Integer, nullable=True)
    source_bbox = Column(JSON, nullable=True)
    ai_prediction = Column(Text, nullable=True)
    human_correction = Column(Text, nullable=False)
    confidence = Column(Integer, default=100)
    verified_by = Column(String(100), default="advocate_user")
    created_at = Column(DateTime, default=datetime.utcnow)

