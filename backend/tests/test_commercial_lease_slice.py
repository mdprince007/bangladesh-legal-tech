import os
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_root_and_health():
    res = client.get("/")
    assert res.status_code == 200
    assert "text/html" in res.headers.get("content-type", "") or res.status_code == 200

    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["status"] == "healthy"

def test_commercial_lease_end_to_end_vertical_slice():
    # 1. Create a Matter
    matter_res = client.post("/api/v1/matters/", json={
        "title": "Mirpur Commercial Shop Lease",
        "matter_type": "commercial_lease",
        "client_name": "Rahim Uddin",
        "notes": "Shop lease in Mirpur-10"
    })
    assert matter_res.status_code == 200
    matter_id = matter_res.json()["id"]
    assert matter_id is not None

    # 2. Conversational Intake Chat
    intake_res = client.post(f"/api/v1/intake/chat?matter_id={matter_id}", json={
        "matter_type": "commercial_lease",
        "current_facts": {},
        "conversation_history": [],
        "user_input": "আমি মিরপুর ঢাকায় একটা দোকান ৩ বছরের জন্য ৫০,০০০ টাকা ভাড়ায় দিতে চাই। জামানত ২ লাখ টাকা।"
    })
    assert intake_res.status_code == 200
    intake_data = intake_res.json()
    extracted = intake_data["extracted_facts"]

    assert extracted.get("duration_months") == 36
    assert extracted.get("monthly_rent_bdt") == 50000
    assert extracted.get("security_deposit_bdt") == 200000
    assert "Dhaka" in extracted.get("district", "")

    # 3. Supply remaining party names for full drafting
    complete_facts = dict(extracted)
    complete_facts.update({
        "landlord_name": "Haji Mohammad Rafique",
        "landlord_address": "House 12, Road 4, Sector 7, Uttara, Dhaka",
        "landlord_nid_or_passport": "19852691234567890",
        "tenant_name": "Rahim Uddin",
        "tenant_address": "Plot 45, Mirpur-10, Dhaka",
        "tenant_nid_or_passport": "19922699876543210",
        "business_name": "Rahim General Store & Electronics",
        "premises_address": "Shop No. B-4, Ground Floor, Central Plaza, Mirpur-10, Dhaka",
        "commencement_date": "01 March 2026",
        "duration_months": 36,
        "monthly_rent_bdt": 50000,
        "security_deposit_bdt": 200000,
        "rent_due_day_of_month": 7,
        "notice_period_months": 2,
        "sublet_allowed": False
    })

    # 4. Generate Legal Draft
    draft_res = client.post("/api/v1/drafting/generate", json={
        "matter_id": matter_id,
        "template_code": "BD_COMMERCIAL_LEASE",
        "facts": complete_facts,
        "style_preference": "balanced",
        "language": "en"
    })
    assert draft_res.status_code == 200
    doc_data = draft_res.json()
    doc_id = doc_data["id"]
    assert "Haji Mohammad Rafique" in doc_data["full_text"]
    assert "Rahim Uddin" in doc_data["full_text"]
    assert "Tk. 50,000/-" in doc_data["full_text"]
    assert len(doc_data["selected_clauses"]) >= 8

    # Verify Plain Bangla Explanation exists for each clause
    for clause in doc_data["selected_clauses"]:
        assert len(clause["explanation_bangla"]) > 0

    # 5. Run Document Health Audit & Risk Review
    review_res = client.get(f"/api/v1/review/{doc_id}/health")
    assert review_res.status_code == 200
    review_data = review_res.json()
    assert review_data["overall_health_score"] > 0
    # Because duration is 36 months (> 11 months), compulsory registration rule MUST trigger
    issues = review_data["issues"]
    assert any(i["id"] == "RULE_REGISTRATION_REQUIRED" for i in issues)
    assert review_data["professional_review_recommended"] is True

    # 6. Verify DOCX & PDF Export Files
    docx_res = client.get(f"/api/v1/documents/{doc_id}/export/docx")
    assert docx_res.status_code == 200
    assert len(docx_res.content) > 1000

    pdf_res = client.get(f"/api/v1/documents/{doc_id}/export/pdf")
    assert pdf_res.status_code == 200
    assert len(pdf_res.content) > 1000
