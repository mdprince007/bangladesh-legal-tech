import os
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.config import settings
from app.models.document import Document, DocumentVersion
from app.models.organization import Organization
from app.schemas.document import DraftGenerationRequest, DocumentDetailResponse
from app.services.drafting_engine import build_draft, drafting_engine
from app.services.export_service import export_service
from app.services.matter_requirements import TEMPLATE_TO_MATTER

router = APIRouter()

_TITLE_KEYS = {
    "commercial_lease": ("Commercial Tenancy Agreement", "tenant_name"),
    "residential_rent": ("Residential Tenancy Agreement", "tenant_name"),
    "employment_agreement": ("Employment Agreement", "employee_name"),
    "demand_notice_ni_act": ("Legal Notice u/s 138 NI Act", "drawer_name"),
    "partnership_deed": ("Deed of Partnership", "firm_name"),
    "sale_agreement": ("Agreement for Sale", "buyer_name"),
    "loan_agreement": ("Loan Agreement (Hawlatnama)", "borrower_name"),
    "nda": ("Non-Disclosure Agreement", "receiving_party"),
    "service_agreement": ("Service Agreement", "service_provider_name"),
}


def _document_title(code: str, facts: dict) -> str:
    matter = TEMPLATE_TO_MATTER.get(code)
    if matter in _TITLE_KEYS:
        name, key = _TITLE_KEYS[matter]
        who = facts.get(key)
        return f"{name} - {who}" if who else f"{name} - Draft"
    custom = facts.get("custom_matter_name") or "Deed of Agreement"
    who = facts.get("party_one_name") or facts.get("first_party_name")
    return f"{custom} - {who}" if who else f"{custom} - Draft"


@router.post("/generate", response_model=DocumentDetailResponse)
def generate_draft(request: DraftGenerationRequest, db: Session = Depends(get_db)):
    """
    Generates a legal document in the format of Dr. Syeda Nasrin's "Basics of Legal Drafting".
    Values the client has not supplied are left as blanks and returned as questions
    (missing_information) — nothing is invented. Also returns the book checklist audit and legal warnings.
    """
    org = db.query(Organization).first()
    if not org:
        org = Organization(name="Default Law Office", org_type="law_firm")
        db.add(org)
        db.commit()
        db.refresh(org)

    code = (request.template_code or "BD_COMMERCIAL_LEASE").upper()
    if code not in TEMPLATE_TO_MATTER and request.facts.get("custom_matter_name"):
        code = "BD_CUSTOM_AGREEMENT"
    result = build_draft(code, request.facts, request.style_preference, request.language)
    doc_title = _document_title(code, request.facts)
    grounding = drafting_engine.get_grounding_metadata(code, request.facts, result.clauses)
    audit = {
        "template_code": code,
        "missing_information": result.missing,
        "book_checklist": result.checklist,
        "drafting_warnings": result.warnings,
    }

    document = Document(
        org_id=org.id,
        matter_id=request.matter_id,
        title=doc_title,
        status="draft",
        language=request.language,
        structured_facts=request.facts,
        selected_clauses=[c.model_dump() for c in result.clauses],
        full_text=result.text,
        book_grounding_score=grounding.get("book_grounding_score"),
        book_chapter_reference=grounding.get("book_chapter_reference"),
        book_applied_rules=grounding.get("book_applied_rules"),
        draft_audit=audit,
    )
    db.add(document)
    db.commit()
    db.refresh(document)

    db.add(DocumentVersion(
        document_id=document.id,
        version_num=1,
        full_text=result.text,
        structured_facts=request.facts,
        change_summary="Initial draft generated in the book's format",
    ))

    storage_dir = os.path.abspath(settings.STORAGE_DIR)
    docx_file = os.path.join(storage_dir, f"{document.id}.docx")
    pdf_file = os.path.join(storage_dir, f"{document.id}.pdf")
    export_service.generate_docx(doc_title, result.text, docx_file)
    export_service.generate_pdf(doc_title, result.text, pdf_file)
    document.docx_path = docx_file
    document.pdf_path = pdf_file
    db.commit()

    return DocumentDetailResponse(
        id=document.id,
        matter_id=document.matter_id,
        title=document.title,
        status=document.status,
        language=document.language,
        structured_facts=document.structured_facts,
        selected_clauses=result.clauses,
        full_text=document.full_text,
        docx_url=f"/api/v1/documents/{document.id}/export/docx",
        pdf_url=f"/api/v1/documents/{document.id}/export/pdf",
        created_at=document.created_at.isoformat(),
        book_grounding_score=document.book_grounding_score,
        book_chapter_reference=document.book_chapter_reference,
        book_applied_rules=document.book_applied_rules,
        **audit,
    )
