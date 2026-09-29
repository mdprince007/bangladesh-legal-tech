import os
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.config import settings
from app.models.deed import DeedRecord
from app.schemas.deed import (
    DeedDetailResponse, DeedListItem, DeedUpdateRequest,
    DeedCorrectionRequest, DeedCorrectionResponse, DeedFieldVerifyRequest,
    DevCropTestRequest, DevCropTestResponse
)
import cv2
import numpy as np
from app.services.deed_intelligence_service import deed_intelligence_service
from app.services.deed_reading_service import deed_reading_service

router = APIRouter()


def _storage_url(abs_path: str) -> str:
    storage_root = os.path.abspath(settings.STORAGE_DIR)
    rel = os.path.relpath(os.path.abspath(abs_path), storage_root).replace(os.sep, "/")
    return f"/storage/{rel}"


def _page_image_urls(d) -> List[str]:
    paths = getattr(d, "page_image_paths", None) or []
    return [_storage_url(p) for p in paths if p]

def _build_deed_response(d, orig_rel=None, enhanced_rel=None, docx_url=None, pdf_url=None, created_at=None) -> DeedDetailResponse:
    if hasattr(d, "id"):
        # ORM model
        return DeedDetailResponse(
            id=d.id,
            deed_title=d.deed_title,
            deed_type=d.deed_type,
            deed_number=d.deed_number,
            registration_year=d.registration_year,
            registration_date=d.registration_date,
            sub_registry_office=d.sub_registry_office,
            district=d.district,
            thana=d.thana,
            mouza=d.mouza,
            jl_number=d.jl_number,
            parties=d.parties or {},
            schedule=d.schedule or {},
            boundaries=d.boundaries or {},
            financials=d.financials or {},
            chain_of_title=d.chain_of_title or {},
            unclear_texts=d.unclear_texts or [],
            image_quality_report=getattr(d, "image_quality_report", {}) or {},
            layout_zones=getattr(d, "layout_zones", []) or [],
            text_lines=getattr(d, "text_lines", []) or [],
            structured_fields=getattr(d, "structured_fields", {}) or {},
            reading_report=getattr(d, "reading_report", {}) or {},
            page_images=_page_image_urls(d),
            overall_confidence_score=d.overall_confidence_score or 0,
            clarity_rating=d.clarity_rating or "moderate",
            fraud_risk_score=d.fraud_risk_score or 15,
            fraud_risk_level=d.fraud_risk_level or "low",
            fraud_assessment=d.fraud_assessment or {},
            original_file_path=orig_rel or (f"/storage/deed_uploads/{os.path.basename(d.original_file_path)}" if d.original_file_path else None),
            enhanced_image_path=enhanced_rel or (f"/storage/enhanced_deeds/{os.path.basename(d.enhanced_image_path)}" if d.enhanced_image_path else None),
            docx_url=docx_url or f"/api/v1/deeds/{d.id}/export/docx",
            pdf_url=pdf_url or f"/api/v1/deeds/{d.id}/export/pdf",
            created_at=d.created_at.isoformat() if hasattr(d.created_at, "isoformat") else str(d.created_at)
        )
    else:
        # Dictionary (e.g. sample deed)
        return DeedDetailResponse(
            id=d["id"],
            deed_title=d["deed_title"],
            deed_type=d["deed_type"],
            deed_number=d.get("deed_number"),
            registration_year=d.get("registration_year"),
            registration_date=d.get("registration_date"),
            sub_registry_office=d.get("sub_registry_office"),
            district=d.get("district"),
            thana=d.get("thana"),
            mouza=d.get("mouza"),
            jl_number=d.get("jl_number"),
            parties=d.get("parties", {}),
            schedule=d.get("schedule", {}),
            boundaries=d.get("boundaries", {}),
            financials=d.get("financials", {}),
            chain_of_title=d.get("chain_of_title", {}),
            unclear_texts=d.get("unclear_texts", []),
            image_quality_report=d.get("image_quality_report", {
                "estimated_dpi": 300,
                "blur_metric": 450.0,
                "contrast_std": 48.0,
                "overall_score": 92,
                "quality_level": "EXCELLENT",
                "quality_badge_bn": "সন্তোষজনক",
                "warnings": []
            }),
            layout_zones=d.get("layout_zones", []),
            text_lines=d.get("text_lines", []),
            structured_fields=d.get("structured_fields", {}),
            overall_confidence_score=d.get("overall_confidence_score", 90),
            clarity_rating=d.get("clarity_rating", "moderate"),
            fraud_risk_score=d.get("fraud_risk_score", 15),
            fraud_risk_level=d.get("fraud_risk_level", "low"),
            fraud_assessment=d.get("fraud_assessment", {}),
            original_file_path=d.get("original_file_path"),
            enhanced_image_path=d.get("enhanced_image_path"),
            docx_url=None,
            pdf_url=None,
            created_at=created_at or "1974-10-28T00:00:00"
        )


@router.get("/samples", response_model=List[DeedDetailResponse])
def get_sample_historical_deeds():
    """
    Returns pre-packaged historical benchmark deeds (1974 Saf-Kabala, 1988 Heba, 1952 Forgery)
    with their complete digitized land schedule and fraud audit reports.
    """
    samples = deed_intelligence_service.get_sample_deeds()
    return [_build_deed_response(s) for s in samples]

@router.get("/samples/{sample_id}", response_model=DeedDetailResponse)
def get_sample_deed(sample_id: str):
    sample = deed_intelligence_service.get_sample_by_id(sample_id)
    if not sample:
        raise HTTPException(status_code=404, detail="Sample deed not found")
    return _build_deed_response(sample)

@router.post("/upload", response_model=DeedDetailResponse)
async def upload_and_analyze_deed(
    file: UploadFile = File(...),
    deed_type: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """
    Uploads a scanned historical land deed (PDF, PNG, JPG),
    enhances ink contrast, extracts structured schedule, flags unclear cursive handwriting,
    performs 8 fraud & authenticity checks, and stores the digitized record.
    """
    storage_dir = os.path.abspath(settings.STORAGE_DIR)
    uploads_dir = os.path.join(storage_dir, "deed_uploads")
    os.makedirs(uploads_dir, exist_ok=True)

    # Keep only the basename and prefix a unique id so uploads cannot escape uploads_dir or overwrite each other
    safe_name = f"{uuid.uuid4().hex[:8]}_{os.path.basename(file.filename or 'deed_upload')}"
    file_path = os.path.join(uploads_dir, safe_name)
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)

    record = deed_intelligence_service.process_and_analyze_deed(
        file_path=file_path,
        filename=file.filename,
        db=db,
        deed_type_hint=deed_type
    )

    enhanced_rel = f"/storage/enhanced_deeds/{os.path.basename(record.enhanced_image_path)}" if record.enhanced_image_path else None
    orig_rel = f"/storage/deed_uploads/{os.path.basename(record.original_file_path)}" if record.original_file_path else None
    return _build_deed_response(record, orig_rel=orig_rel, enhanced_rel=enhanced_rel)

@router.get("/", response_model=List[DeedListItem])
def list_deeds(db: Session = Depends(get_db)):
    """Lists all analyzed deeds stored in database."""
    deeds = db.query(DeedRecord).order_by(DeedRecord.created_at.desc()).all()
    return [
        DeedListItem(
            id=d.id,
            deed_title=d.deed_title,
            deed_type=d.deed_type,
            deed_number=d.deed_number,
            registration_year=d.registration_year,
            mouza=d.mouza,
            fraud_risk_score=d.fraud_risk_score or 15,
            fraud_risk_level=d.fraud_risk_level or "low",
            overall_confidence_score=d.overall_confidence_score or 90,
            created_at=d.created_at.isoformat()
        )
        for d in deeds
    ]

@router.get("/engine-status")
def get_reading_engine_status():
    """Which deed readers are active (dual vision models / local OCR only / manual) and what that means for accuracy."""
    return deed_reading_service.engine_status()


@router.get("/{deed_id}", response_model=DeedDetailResponse)
def get_deed_by_id(deed_id: str, db: Session = Depends(get_db)):
    # First check sample deeds
    sample = deed_intelligence_service.get_sample_by_id(deed_id)
    if sample:
        return DeedDetailResponse(
            id=sample["id"],
            deed_title=sample["deed_title"],
            deed_type=sample["deed_type"],
            deed_number=sample.get("deed_number"),
            registration_year=sample.get("registration_year"),
            registration_date=sample.get("registration_date"),
            sub_registry_office=sample.get("sub_registry_office"),
            district=sample.get("district"),
            thana=sample.get("thana"),
            mouza=sample.get("mouza"),
            jl_number=sample.get("jl_number"),
            parties=sample.get("parties", {}),
            schedule=sample.get("schedule", {}),
            boundaries=sample.get("boundaries", {}),
            financials=sample.get("financials", {}),
            chain_of_title=sample.get("chain_of_title", {}),
            unclear_texts=sample.get("unclear_texts", []),
            overall_confidence_score=sample.get("overall_confidence_score", 90),
            clarity_rating=sample.get("clarity_rating", "moderate"),
            fraud_risk_score=sample.get("fraud_risk_score", 15),
            fraud_risk_level=sample.get("fraud_risk_level", "low"),
            fraud_assessment=sample.get("fraud_assessment", {}),
            original_file_path=sample.get("original_file_path"),
            enhanced_image_path=sample.get("enhanced_image_path"),
            docx_url=None,
            pdf_url=None,
            created_at="1974-10-28T00:00:00"
        )

    record = db.query(DeedRecord).filter(DeedRecord.id == deed_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Deed not found")

    enhanced_rel = f"/storage/enhanced_deeds/{os.path.basename(record.enhanced_image_path)}" if record.enhanced_image_path else None
    orig_rel = f"/storage/deed_uploads/{os.path.basename(record.original_file_path)}" if record.original_file_path else None
    return _build_deed_response(record, orig_rel=orig_rel, enhanced_rel=enhanced_rel)

@router.put("/{deed_id}", response_model=DeedDetailResponse)
def update_deed(deed_id: str, payload: DeedUpdateRequest, db: Session = Depends(get_db)):
    """
    Updates and refines digitized deed fields, then recalculates
    fraud audit scores and updates Word/PDF exports.
    """
    update_data = payload.model_dump(exclude_unset=True) if hasattr(payload, "model_dump") else payload.dict(exclude_unset=True)
    record = deed_intelligence_service.update_deed_record(deed_id, update_data, db)
    if not record:
        raise HTTPException(status_code=404, detail="Deed not found or cannot be updated")

    enhanced_rel = f"/storage/enhanced_deeds/{os.path.basename(record.enhanced_image_path)}" if record.enhanced_image_path else None
    orig_rel = f"/storage/deed_uploads/{os.path.basename(record.original_file_path)}" if record.original_file_path else None
    return _build_deed_response(record, orig_rel=orig_rel, enhanced_rel=enhanced_rel)

@router.post("/{deed_id}/verify-field", response_model=DeedDetailResponse)
def verify_deed_field(deed_id: str, payload: DeedFieldVerifyRequest, db: Session = Depends(get_db)):
    """
    A person confirms (same value) or corrects (new value) one field after checking it against the deed image.
    Only human-verified fields are treated as final; the correction is also saved as training data.
    """
    record = deed_intelligence_service.verify_field(deed_id, payload.field_key, payload.value, payload.verified_by, db)
    if not record:
        raise HTTPException(status_code=404, detail="Deed or field not found")
    return _build_deed_response(record)


@router.get("/{deed_id}/export/docx")
def export_deed_docx(deed_id: str, db: Session = Depends(get_db)):
    record = db.query(DeedRecord).filter(DeedRecord.id == deed_id).first()
    if not record or not record.docx_path or not os.path.exists(record.docx_path):
        raise HTTPException(status_code=404, detail="DOCX file not found")
    return FileResponse(
        record.docx_path,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=f"Deed_{record.deed_number or deed_id}.docx"
    )

@router.get("/{deed_id}/export/pdf")
def export_deed_pdf(deed_id: str, db: Session = Depends(get_db)):
    record = db.query(DeedRecord).filter(DeedRecord.id == deed_id).first()
    if not record or not record.pdf_path or not os.path.exists(record.pdf_path):
        raise HTTPException(status_code=404, detail="PDF file not found")
    return FileResponse(
        record.pdf_path,
        media_type="application/pdf",
        filename=f"Deed_{record.deed_number or deed_id}.pdf"
    )


@router.post("/{deed_id}/corrections", response_model=DeedCorrectionResponse)
def add_deed_correction(deed_id: str, payload: DeedCorrectionRequest, db: Session = Depends(get_db)):
    """Phase 20: Records verified human correction into domain-specific training dataset."""
    correction_dict = payload.model_dump(exclude_unset=True) if hasattr(payload, "model_dump") else payload.dict(exclude_unset=True)
    correction_dict["deed_id"] = deed_id
    rec = deed_intelligence_service.record_human_correction(db, correction_dict)
    return DeedCorrectionResponse(
        id=rec.id,
        deed_id=rec.deed_id,
        field_key=rec.field_key,
        human_correction=rec.human_correction,
        status="saved",
        message="সংশোধন সফলভাবে যাচাইকৃত প্রশিক্ষণ ডেটাসেটে সংরক্ষিত হয়েছে।"
    )

@router.get("/dev/corrections")
def list_deed_corrections(db: Session = Depends(get_db)):
    """Phase 20: Exports all domain-specific corrections for fine-tuning dataset."""
    return deed_intelligence_service.get_corrections(db)

@router.post("/dev/crop-test", response_model=DevCropTestResponse)
async def test_line_crop(
    file: UploadFile = File(...),
    ground_truth: Optional[str] = Form(None),
    field_key: Optional[str] = Form(None)
):
    """Phase 24: Developer Testing Tool - Evaluates crop across multi-pass filters, calculates CER/WER, and classifies failure."""
    content = await file.read()
    nparr = np.frombuffer(content, np.uint8)
    crop = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if crop is None:
        raise HTTPException(status_code=400, detail="Invalid image crop")

    result = deed_intelligence_service.run_dev_crop_test(crop, ground_truth=ground_truth, field_key=field_key)
    return DevCropTestResponse(
        passes=result["passes"],
        best_prediction=result["best_prediction"],
        confidence=result["confidence"],
        cer=result["cer"],
        wer=result["wer"],
        failure_reason=result["failure_reason"]
    )
