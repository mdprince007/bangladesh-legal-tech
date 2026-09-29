from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class DraftGenerationRequest(BaseModel):
    matter_id: Optional[str] = None
    template_code: str = "BD_COMMERCIAL_LEASE"
    facts: Dict[str, Any]
    style_preference: str = "balanced"  # balanced, landlord_friendly, tenant_friendly
    language: str = "en"                # en, bn

class ClauseSelectionItem(BaseModel):
    code: str
    clause_type: str
    title: str
    text_content: str
    explanation_bangla: str
    risk_level: str
    style: str
    statutory_basis: Optional[str] = None
    book_reference: Optional[str] = None

class DocumentDetailResponse(BaseModel):
    id: str
    matter_id: Optional[str]
    title: str
    status: str
    language: str
    structured_facts: Dict[str, Any]
    selected_clauses: List[ClauseSelectionItem]
    full_text: str
    docx_url: Optional[str] = None
    pdf_url: Optional[str] = None
    created_at: str
    book_grounding_score: Optional[int] = None
    book_chapter_reference: Optional[str] = None
    book_applied_rules: Optional[List[str]] = None
    # Book-grounded completeness audit: blanks left in the draft, checklist, legal warnings
    missing_information: List[Dict[str, Any]] = []
    book_checklist: List[Dict[str, Any]] = []
    drafting_warnings: List[str] = []
    template_code: Optional[str] = None

class DocumentUpdateRequest(BaseModel):
    full_text: str
    change_summary: Optional[str] = "Manual customization in Drafting Studio"

class DocumentListItem(BaseModel):
    id: str
    title: str
    status: str
    language: str
    matter_id: Optional[str] = None
    created_at: str
    docx_url: Optional[str] = None
    pdf_url: Optional[str] = None

class DocumentVersionItem(BaseModel):
    id: str
    version_num: int
    change_summary: Optional[str] = None
    created_at: str
