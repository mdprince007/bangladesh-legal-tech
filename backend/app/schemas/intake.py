from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class IntakeMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str

class IntakeChatRequest(BaseModel):
    matter_type: str = Field(default="commercial_lease")
    current_facts: Dict[str, Any] = Field(default_factory=dict)
    conversation_history: List[IntakeMessage] = Field(default_factory=list)
    user_input: str
    last_asked_field: Optional[str] = None

class IntakeChatResponse(BaseModel):
    assistant_reply: str
    assistant_reply_bangla: str
    extracted_facts: Dict[str, Any]
    completion_percentage: int
    missing_critical_fields: List[str]
    is_ready_for_drafting: bool
    current_field_asked: Optional[str] = None
    next_suggested_question: Optional[str] = None

class ScenarioAnalysisRequest(BaseModel):
    scenario_text: str = Field(..., description="Full case scenario description in plain Bangla or English")
    matter_type: Optional[str] = Field(default=None, description="Optional forced matter type (e.g. commercial_lease, residential_rent, etc.)")
    language: Optional[str] = Field(default="bn", description="Preferred output language ('bn' or 'en')")

class ScenarioQuestion(BaseModel):
    field: str
    label_bn: str
    question_bn: str
    why_bn: str
    kind: str                      # "fact" (only the client knows) or "term" (book suggestion available)
    critical: bool = False
    suggestion: Any = None

class ScenarioAnalysisResponse(BaseModel):
    matter_type: str
    template_code: str
    matter_title_bn: str
    matter_title_en: str
    extracted_facts: Dict[str, Any]
    evidence: Dict[str, Any] = {}          # the client's own words each fact was taken from
    unclear: List[str] = []
    questions: List[ScenarioQuestion] = []        # facts still needed from the client
    suggested_terms: List[ScenarioQuestion] = []  # standard book terms the client may accept
    missing_items: List[ScenarioQuestion] = []
    completeness_percentage: int
    is_ready_for_drafting: bool
    autofilled_facts: Dict[str, Any]
    senior_counsel_notes_bn: List[str]
    extraction_method: str = "rules"
    field_labels: Dict[str, str] = {}

class ScenarioRecheckRequest(BaseModel):
    matter_type: str
    facts: Dict[str, Any] = Field(default_factory=dict)

class AutofillRequest(BaseModel):
    facts: Dict[str, Any] = Field(default_factory=dict)
    matter_type: str = Field(default="commercial_lease")
