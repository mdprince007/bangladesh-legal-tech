from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class FeedbackSubmission(BaseModel):
    document_id: Optional[str] = None
    rating: int = Field(..., ge=1, le=5)
    feedback_category: str  # correct, missing_authority, wrong_citation, legally_risky, poor_drafting
    original_text: Optional[str] = None
    corrected_text: Optional[str] = None
    reviewer_reasoning: Optional[str] = None

class EvaluationRunRequest(BaseModel):
    test_suite: str = "commercial_lease_suite"

class EvaluationResultItem(BaseModel):
    case_name: str
    passed: bool
    score: float
    details: Dict[str, Any]

class EvaluationSuiteReport(BaseModel):
    suite_name: str
    total_cases: int
    passed_cases: int
    overall_accuracy_percentage: float
    results: List[EvaluationResultItem]
