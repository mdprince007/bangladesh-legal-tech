import pytest
from app.core.database import SessionLocal
from app.services.knowledge_service import KnowledgeService

def test_anti_hallucination_real_vs_fake():
    db = SessionLocal()
    try:
        # Real statute verification
        real_check = KnowledgeService.verify_statutory_reference("Transfer of Property Act", "106", db)
        assert real_check["verified"] is True
        assert real_check["status_badge"] == "VERIFIED_AUTHORITY"
        assert "3158" in real_check["source_url"]

        # Fake hallucinated section verification
        fake_check = KnowledgeService.verify_statutory_reference("Transfer of Property Act", "999Z", db)
        assert fake_check["verified"] is False
        assert fake_check["status_badge"] == "UNVERIFIED_AUTHORITY_WARNING"
        assert fake_check["source_url"] is None
    finally:
        db.close()
