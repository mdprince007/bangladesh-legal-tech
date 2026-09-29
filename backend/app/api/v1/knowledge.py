from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from app.core.database import get_db
from app.models.legal_knowledge import Law, LawSection
from app.services.knowledge_service import KnowledgeService

router = APIRouter()

@router.get("/statutes")
def list_statutes(db: Session = Depends(get_db)):
    """List all verified Bangladesh statutes currently seeded in the knowledge base."""
    laws = db.query(Law).all()
    return [
        {
            "id": law.id,
            "act_name": law.act_name,
            "act_year": law.act_year,
            "act_number": law.act_number,
            "category": law.category,
            "sections_count": len(law.sections)
        }
        for law in laws
    ]

@router.get("/verify-citation")
def verify_citation(act_name: str = Query(...), section: str = Query(...), db: Session = Depends(get_db)):
    """
    Anti-Hallucination Endpoint: Verifies whether an Act and Section officially exist in the BD corpus.
    """
    return KnowledgeService.verify_statutory_reference(act_name, section, db)
