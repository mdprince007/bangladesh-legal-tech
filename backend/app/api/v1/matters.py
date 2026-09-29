from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from app.core.database import get_db
from app.models.matter import Matter
from app.models.organization import Organization
from app.models.user import User

router = APIRouter()

class MatterCreate(BaseModel):
    title: str
    matter_type: str = "commercial_lease"
    client_name: Optional[str] = None
    notes: Optional[str] = None

class MatterResponse(BaseModel):
    id: str
    title: str
    matter_type: str
    client_name: Optional[str]
    status: str
    facts_data: Dict[str, Any]
    created_at: str

@router.post("/", response_model=MatterResponse)
def create_matter(data: MatterCreate, db: Session = Depends(get_db)):
    # Ensure default organization and demo user exist for frictionless use
    org = db.query(Organization).first()
    if not org:
        org = Organization(name="Default Law Office", org_type="law_firm")
        db.add(org)
        db.commit()
        db.refresh(org)

    user = db.query(User).first()
    if not user:
        user = User(
            org_id=org.id,
            email="lawyer@legalai.bd",
            full_name="Advocate M. Rahman",
            hashed_password="mock_hashed_password",
            role="lawyer",
            is_verified_lawyer=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    matter = Matter(
        org_id=org.id,
        user_id=user.id,
        title=data.title,
        matter_type=data.matter_type,
        client_name=data.client_name,
        status="active",
        notes=data.notes,
        facts_data={}
    )
    db.add(matter)
    db.commit()
    db.refresh(matter)

    return MatterResponse(
        id=matter.id,
        title=matter.title,
        matter_type=matter.matter_type,
        client_name=matter.client_name,
        status=matter.status,
        facts_data=matter.facts_data or {},
        created_at=matter.created_at.isoformat()
    )

@router.get("/", response_model=List[MatterResponse])
def list_matters(db: Session = Depends(get_db)):
    matters = db.query(Matter).order_by(Matter.created_at.desc()).all()
    return [
        MatterResponse(
            id=m.id,
            title=m.title,
            matter_type=m.matter_type,
            client_name=m.client_name,
            status=m.status,
            facts_data=m.facts_data or {},
            created_at=m.created_at.isoformat()
        )
        for m in matters
    ]
