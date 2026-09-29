from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class ReviewIssue(BaseModel):
    id: str
    issue_type: str        # contradiction, missing_clause, financial_risk, statutory_caution, ambiguity
    severity: str          # high, medium, low
    clause_title: str
    message: str
    message_bangla: str
    suggested_fix: str
    suggested_fix_bangla: str
    statute_ref: Optional[str] = None

class DocumentHealthReport(BaseModel):
    document_id: str
    overall_health_score: int       # 0 - 100
    completeness_score: int         # 0 - 100
    risk_score: int                 # 0 - 100
    consistency_score: int          # 0 - 100
    professional_review_recommended: bool
    issues: List[ReviewIssue]
    plain_bangla_summary: str
    verified_statutes_used: List[str]
