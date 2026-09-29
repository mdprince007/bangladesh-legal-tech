from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.matter import Matter
from app.schemas.intake import (
    IntakeChatRequest, 
    IntakeChatResponse,
    ScenarioAnalysisRequest,
    ScenarioAnalysisResponse,
    AutofillRequest,
    ScenarioRecheckRequest
)
from app.services.intake_agent import intake_agent
from app.services.scenario_analysis_service import scenario_analysis_service

router = APIRouter()

@router.post("/chat", response_model=IntakeChatResponse)
def process_intake_chat(request: IntakeChatRequest, matter_id: str = None, db: Session = Depends(get_db)):
    """
    Intake chat endpoint: accepts natural language user messages in Bangla/English,
    extracts structured facts, checks completeness, and suggests the next question.
    """
    response = intake_agent.process_message(request)

    # If matter_id provided, persist the updated facts into the matter record
    if matter_id:
        matter = db.query(Matter).filter(Matter.id == matter_id).first()
        if matter:
            matter.facts_data = response.extracted_facts
            db.commit()

    return response

@router.post("/analyze-scenario", response_model=ScenarioAnalysisResponse)
def analyze_full_scenario(request: ScenarioAnalysisRequest, matter_id: str = None, db: Session = Depends(get_db)):
    """
    Full Scenario & Voice Analysis Endpoint:
    Accepts full case narrative (spoken or written in Bangla/English), extracts facts,
    detects critical missing legal items required by Dr. Syeda Nasrin's senior advocate guidelines,
    and returns comprehensive gap analysis with legal impact notes.
    """
    result = scenario_analysis_service.analyze_scenario(
        scenario_text=request.scenario_text,
        requested_matter_type=request.matter_type
    )

    if matter_id:
        matter = db.query(Matter).filter(Matter.id == matter_id).first()
        if matter:
            matter.matter_type = result["matter_type"]
            matter.facts_data = result["extracted_facts"]
            db.commit()

    return result


@router.post("/scenario-recheck", response_model=ScenarioAnalysisResponse)
def recheck_scenario_facts(request: ScenarioRecheckRequest):
    """
    After the user answers some questions (or edits extracted facts), recompute what is still missing
    for this document type according to the book's checklist.
    """
    facts = {k: v for k, v in request.facts.items() if v not in (None, "")}
    return scenario_analysis_service.build_result(request.matter_type, facts, method="manual")

@router.post("/autofill-missing")
def autofill_missing_facts(request: AutofillRequest):
    """
    Adds Dr. Syeda Nasrin's standard TERMS (notice period, rent due day, ...) where empty.
    Facts such as names, amounts and dates are never auto-filled.
    """
    filled = scenario_analysis_service.autofill_facts(
        current_facts=request.facts,
        matter_type=request.matter_type
    )
    return {"facts": filled, "status": "success"}
