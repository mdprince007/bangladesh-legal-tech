from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.advisory_service import advisory_service

router = APIRouter()

class ProblemAdvisoryRequest(BaseModel):
    problem_description: str

@router.post("/resolve")
@router.post("/solve-problem", include_in_schema=False)  # legacy path used by older frontend builds
def resolve_legal_problem(data: ProblemAdvisoryRequest, db: Session = Depends(get_db)):
    """
    Legal Problem Solver: Takes an everyday legal problem description in Bangla or English,
    provides step-by-step procedure, applicable BD laws, required documents, and risks.
    Enforces strict zero-guesswork if unverified.
    """
    return advisory_service.provide_advisory_roadmap(data.problem_description, db)
