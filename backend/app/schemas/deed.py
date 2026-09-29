from typing import Optional, List, Dict, Any
from pydantic import BaseModel

class UnclearTextItem(BaseModel):
    term_location: str
    raw_ocr_snippet: str
    extracted_reading: str
    confidence_score: int
    alternatives: List[str]
    guidance: str

class RedFlagItem(BaseModel):
    severity: str
    title: str
    message_bangla: str

class FraudAssessment(BaseModel):
    fraud_risk_score: int
    fraud_risk_level: str
    red_flags: List[RedFlagItem]
    passed_checks: List[str]
    legal_recommendation: str

class DeedDetailResponse(BaseModel):
    id: str
    deed_title: str
    deed_type: str
    deed_number: Optional[str] = None
    registration_year: Optional[int] = None
    registration_date: Optional[str] = None
    sub_registry_office: Optional[str] = None
    district: Optional[str] = None
    thana: Optional[str] = None
    mouza: Optional[str] = None
    jl_number: Optional[str] = None
    parties: Dict[str, Any] = {}
    schedule: Dict[str, Any] = {}
    boundaries: Dict[str, Any] = {}
    financials: Dict[str, Any] = {}
    chain_of_title: Dict[str, Any] = {}
    unclear_texts: List[Dict[str, Any]] = []
    
    # Document Vision & HTR Fields
    image_quality_report: Dict[str, Any] = {}
    layout_zones: List[Dict[str, Any]] = []
    text_lines: List[Dict[str, Any]] = []
    structured_fields: Dict[str, Any] = {}
    # Field-by-field reading report (statuses, alternatives, checks, human verification)
    reading_report: Dict[str, Any] = {}
    page_images: List[str] = []

    overall_confidence_score: int = 90
    clarity_rating: str = "moderate"
    fraud_risk_score: int = 15
    fraud_risk_level: str = "low"
    fraud_assessment: Dict[str, Any] = {}
    original_file_path: Optional[str] = None
    enhanced_image_path: Optional[str] = None
    docx_url: Optional[str] = None
    pdf_url: Optional[str] = None
    created_at: Optional[str] = None

class DeedListItem(BaseModel):
    id: str
    deed_title: str
    deed_type: str
    deed_number: Optional[str] = None
    registration_year: Optional[int] = None
    mouza: Optional[str] = None
    fraud_risk_score: int
    fraud_risk_level: str
    overall_confidence_score: int
    created_at: Optional[str] = None

class DeedUpdateRequest(BaseModel):
    deed_title: Optional[str] = None
    deed_type: Optional[str] = None
    deed_number: Optional[str] = None
    registration_year: Optional[int] = None
    registration_date: Optional[str] = None
    sub_registry_office: Optional[str] = None
    district: Optional[str] = None
    thana: Optional[str] = None
    mouza: Optional[str] = None
    jl_number: Optional[str] = None
    parties: Optional[Dict[str, Any]] = None
    schedule: Optional[Dict[str, Any]] = None
    boundaries: Optional[Dict[str, Any]] = None
    financials: Optional[Dict[str, Any]] = None
    chain_of_title: Optional[Dict[str, Any]] = None
    structured_fields: Optional[Dict[str, Any]] = None

class DeedFieldVerifyRequest(BaseModel):
    field_key: str
    value: Optional[str] = None      # the value the person confirmed or typed; None = field truly absent
    verified_by: str = "advocate_user"

class DeedCorrectionRequest(BaseModel):
    deed_id: str
    field_key: str
    line_index: Optional[int] = None
    source_bbox: Optional[List[int]] = None
    ai_prediction: Optional[str] = None
    human_correction: str
    confidence: int = 100
    verified_by: Optional[str] = "advocate_user"

class DeedCorrectionResponse(BaseModel):
    id: str
    deed_id: str
    field_key: str
    human_correction: str
    status: str = "saved"
    message: str = "সংশোধন সফলভাবে যাচাইকৃত প্রশিক্ষণ ডেটাসেটে সংরক্ষিত হয়েছে।"

class DevCropTestRequest(BaseModel):
    ground_truth: Optional[str] = None
    field_key: Optional[str] = None

class DevCropTestResponse(BaseModel):
    passes: Dict[str, Any]
    best_prediction: str
    confidence: int
    cer: Optional[float] = None
    wer: Optional[float] = None
    failure_reason: Optional[str] = None
