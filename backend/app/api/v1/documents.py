import os
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.config import settings
from app.models.document import Document, DocumentVersion
from app.schemas.document import (
    DocumentDetailResponse, 
    ClauseSelectionItem,
    DocumentUpdateRequest,
    DocumentListItem,
    DocumentVersionItem
)
from app.services.export_service import export_service

router = APIRouter()


def _audit_fields(doc: Document) -> dict:
    audit = doc.draft_audit or {}
    return {
        "missing_information": audit.get("missing_information", []),
        "book_checklist": audit.get("book_checklist", []),
        "drafting_warnings": audit.get("drafting_warnings", []),
        "template_code": audit.get("template_code"),
    }

@router.get("/", response_model=List[DocumentListItem])
def list_documents(db: Session = Depends(get_db)):
    """
    Returns all generated legal documents and contracts.
    """
    docs = db.query(Document).order_by(Document.created_at.desc()).all()
    return [
        DocumentListItem(
            id=d.id,
            title=d.title,
            status=d.status,
            language=d.language,
            matter_id=d.matter_id,
            created_at=d.created_at.isoformat(),
            docx_url=f"/api/v1/documents/{d.id}/export/docx",
            pdf_url=f"/api/v1/documents/{d.id}/export/pdf"
        )
        for d in docs
    ]

@router.get("/{document_id}", response_model=DocumentDetailResponse)
def get_document(document_id: str, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    selected_clauses = [
        ClauseSelectionItem(**c) if isinstance(c, dict) else c
        for c in (doc.selected_clauses or [])
    ]

    return DocumentDetailResponse(
        id=doc.id,
        matter_id=doc.matter_id,
        title=doc.title,
        status=doc.status,
        language=doc.language,
        structured_facts=doc.structured_facts or {},
        selected_clauses=selected_clauses,
        full_text=doc.full_text,
        docx_url=f"/api/v1/documents/{doc.id}/export/docx",
        pdf_url=f"/api/v1/documents/{doc.id}/export/pdf",
        created_at=doc.created_at.isoformat(),
        book_grounding_score=doc.book_grounding_score,
        book_chapter_reference=doc.book_chapter_reference,
        book_applied_rules=doc.book_applied_rules or [],
        **_audit_fields(doc)
    )

@router.put("/{document_id}", response_model=DocumentDetailResponse)
def update_document(document_id: str, data: DocumentUpdateRequest, db: Session = Depends(get_db)):
    """
    Updates document full_text, saves a new version in DocumentVersion history,
    and automatically re-exports updated DOCX & PDF files.
    """
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # Update document text
    doc.full_text = data.full_text
    doc.status = "lawyer_customized"

    # Determine next version number
    current_versions = db.query(DocumentVersion).filter(DocumentVersion.document_id == doc.id).count()
    next_version_num = current_versions + 1

    new_version = DocumentVersion(
        document_id=doc.id,
        version_num=next_version_num,
        full_text=data.full_text,
        structured_facts=doc.structured_facts or {},
        change_summary=data.change_summary or f"Version {next_version_num} manual customization"
    )
    db.add(new_version)

    # Re-export DOCX and PDF
    storage_dir = os.path.abspath(settings.STORAGE_DIR)
    docx_file = os.path.join(storage_dir, f"{doc.id}.docx")
    pdf_file = os.path.join(storage_dir, f"{doc.id}.pdf")

    export_service.generate_docx(doc.title, doc.full_text, docx_file)
    export_service.generate_pdf(doc.title, doc.full_text, pdf_file)

    doc.docx_path = docx_file
    doc.pdf_path = pdf_file
    db.commit()
    db.refresh(doc)

    selected_clauses = [
        ClauseSelectionItem(**c) if isinstance(c, dict) else c
        for c in (doc.selected_clauses or [])
    ]

    return DocumentDetailResponse(
        id=doc.id,
        matter_id=doc.matter_id,
        title=doc.title,
        status=doc.status,
        language=doc.language,
        structured_facts=doc.structured_facts or {},
        selected_clauses=selected_clauses,
        full_text=doc.full_text,
        docx_url=f"/api/v1/documents/{doc.id}/export/docx",
        pdf_url=f"/api/v1/documents/{doc.id}/export/pdf",
        created_at=doc.created_at.isoformat(),
        book_grounding_score=doc.book_grounding_score,
        book_chapter_reference=doc.book_chapter_reference,
        book_applied_rules=doc.book_applied_rules or [],
        **_audit_fields(doc)
    )

@router.get("/{document_id}/versions", response_model=List[DocumentVersionItem])
def get_document_versions(document_id: str, db: Session = Depends(get_db)):
    """
    Retrieves full chronological revision and version history for the document.
    """
    versions = (
        db.query(DocumentVersion)
        .filter(DocumentVersion.document_id == document_id)
        .order_by(DocumentVersion.version_num.desc())
        .all()
    )
    return [
        DocumentVersionItem(
            id=v.id,
            version_num=v.version_num,
            change_summary=v.change_summary,
            created_at=v.created_at.isoformat()
        )
        for v in versions
    ]

@router.get("/{document_id}/export/docx")
def download_docx(document_id: str, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc or not doc.docx_path or not os.path.exists(doc.docx_path):
        raise HTTPException(status_code=404, detail="DOCX file not generated or not found")
    return FileResponse(
        doc.docx_path,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=f"{doc.title.replace(' ', '_')}.docx"
    )

@router.get("/{document_id}/export/pdf")
def download_pdf(document_id: str, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc or not doc.pdf_path or not os.path.exists(doc.pdf_path):
        raise HTTPException(status_code=404, detail="PDF file not generated or not found")
    return FileResponse(
        doc.pdf_path,
        media_type="application/pdf",
        filename=f"{doc.title.replace(' ', '_')}.pdf"
    )
