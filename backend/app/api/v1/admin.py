from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from app.core.database import get_db
from app.models.matter import Matter
from app.models.document import Document
from app.models.legal_knowledge import Law, LawSection, IngestedDocument, IngestedLesson
from app.models.template_clause import Template, Clause
from app.models.feedback import FeedbackEntry, EvaluationCase
from app.models.audit import AuditLog
from app.services.training_service import training_service

router = APIRouter()

class NasrinIngestRequest(BaseModel):
    chapter_num: Optional[int] = None
    ingest_all: bool = False

@router.get("/stats")
def get_admin_dashboard_stats(db: Session = Depends(get_db)):
    """
    Returns platform health and metrics for the Admin Dashboard.
    """
    return {
        "platform_status": "Operational (Bangladesh Production Core)",
        "total_matters": db.query(Matter).count(),
        "total_documents_drafted": db.query(Document).count(),
        "verified_laws_count": db.query(Law).count(),
        "verified_sections_count": db.query(LawSection).count(),
        "feedback_entries_count": db.query(FeedbackEntry).count(),
        "audit_logs_count": db.query(AuditLog).count(),
        "ingested_documents_count": db.query(IngestedDocument).count(),
        "ingested_lessons_count": db.query(IngestedLesson).count(),
        "active_templates": [
            {"code": "BD_COMMERCIAL_LEASE", "name": "Commercial Lease Agreement (বাণিজ্যিক দোকান/স্পেস চুক্তি)"},
            {"code": "BD_EMPLOYMENT_AGREEMENT", "name": "Employment Agreement (বাংলাদেশ শ্রম আইন অনুযায়ী চুক্তি)"},
            {"code": "BD_LEGAL_NOTICE_NI_ACT", "name": "Section 138 NI Act Demand Notice (চেক ডিজঅনার নোটিশ)"}
        ]
    }

@router.get("/learning")
def get_learning_status(db: Session = Depends(get_db)):
    """Returns the state of user-provided learning materials, chapters, and ingested books."""
    return training_service.get_learning_repository_status(db)

@router.post("/ingest-nasrin-book")
def ingest_nasrin_book(
    req: Optional[NasrinIngestRequest] = None,
    chapter_num: Optional[int] = None,
    ingest_all: bool = False,
    db: Session = Depends(get_db)
):
    """
    Triggers ingestion and knowledge extraction from Dr. Syeda Nasrin's 889-page book.
    If chapter_num is provided, ingests that chapter (1-21).
    If ingest_all is True or no chapter is specified, ingests all 21 chapters across the entire book.
    """
    target_all = (req.ingest_all if req else False) or ingest_all
    target_ch = (req.chapter_num if req and req.chapter_num is not None else chapter_num)

    if target_ch is not None and not target_all:
        return training_service.ingest_nasrin_chapter(db, target_ch)
    else:
        return training_service.ingest_full_nasrin_book(db)

@router.post("/ingest-file")
async def ingest_custom_file(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """
    Accepts arbitrary user-uploaded legal files (PDF, DOCX, TXT),
    extracts text across all pages/chunks, splits into structured lessons,
    and indexes rules into the database.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file uploaded.")
    content = await file.read()
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")
    return training_service.ingest_uploaded_file(db, content, file.filename, title)

@router.get("/ingested-documents")
def list_ingested_documents(db: Session = Depends(get_db)):
    """Lists all ingested documents in the database with their lesson count."""
    return training_service.get_all_ingested_documents(db)

@router.get("/ingested-documents/{doc_id}/lessons")
def get_document_lessons(
    doc_id: str,
    chapter_num: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    """Returns lessons, extracted principles, and model clauses for an ingested document."""
    return training_service.get_document_lessons(db, doc_id, chapter_num)

@router.delete("/ingested-documents/{doc_id}")
def delete_ingested_document(doc_id: str, db: Session = Depends(get_db)):
    """Deletes an ingested document and its lessons."""
    res = training_service.delete_ingested_document(db, doc_id)
    if "error" in res:
        raise HTTPException(status_code=404, detail=res["error"])
    return res

@router.get("/feedback-queue")
def list_feedback_queue(db: Session = Depends(get_db)):
    """Lists feedback entries, lawyer reviews, and system corrections."""
    items = db.query(FeedbackEntry).order_by(FeedbackEntry.created_at.desc()).limit(50).all()
    return [
        {
            "id": i.id,
            "document_id": i.document_id,
            "rating": i.rating,
            "category": i.feedback_category,
            "reviewer_reasoning": i.reviewer_reasoning,
            "created_at": i.created_at.isoformat()
        }
        for i in items
    ]

@router.get("/audit-logs")
def list_audit_logs(db: Session = Depends(get_db)):
    """Lists immutable audit log entries."""
    logs = db.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(100).all()
    return [
        {
            "id": l.id,
            "action": l.action,
            "resource_type": l.resource_type,
            "resource_id": l.resource_id,
            "timestamp": l.timestamp.isoformat()
        }
        for l in logs
    ]

