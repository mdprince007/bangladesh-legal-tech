import os

os.environ["GEMINI_API_KEY"] = ""

from fastapi.testclient import TestClient  # noqa: E402
from app.main import app  # noqa: E402

client = TestClient(app)


def _analyze(text, matter_type=None):
    res = client.post("/api/v1/intake/analyze-scenario", json={"scenario_text": text, "matter_type": matter_type})
    assert res.status_code == 200
    return res.json()


def test_commercial_scenario_extracts_only_stated_facts():
    data = _analyze("আমি মিরপুরে একটা দোকান ৩ বছরের জন্য ভাড়া দিতে চাই। মাসিক ভাড়া ২ লাখ ৫০ হাজার টাকা এবং অগ্রিম ১০ লাখ টাকা।")
    assert data["matter_type"] == "commercial_lease"
    f = data["extracted_facts"]
    assert f["monthly_rent_bdt"] == 250000
    assert f["security_deposit_bdt"] == 1000000
    assert f["duration_months"] == 36
    # nothing about names or dates was said -> they must be questions, not invented values
    assert "landlord_name" not in f and "commencement_date" not in f
    q = {x["field"] for x in data["questions"]}
    assert {"landlord_name", "tenant_name", "commencement_date", "execution_date"} <= q
    assert data["is_ready_for_drafting"] is False
    assert all(x["why_bn"] for x in data["questions"])


def test_cheque_scenario_never_invents_cheque_details():
    data = _analyze("রহিম সাহেব আমাকে একটা চেক দিয়েছিলেন, সেটা বাউন্স করেছে।")
    assert data["matter_type"] == "demand_notice_ni_act"
    f = data["extracted_facts"]
    for invented in ("cheque_no", "bank_name", "cheque_amount_bdt"):
        assert invented not in f
    assert "cheque_no" in {x["field"] for x in data["questions"]}


def test_autofill_adds_terms_not_facts():
    res = client.post("/api/v1/intake/autofill-missing", json={"facts": {}, "matter_type": "commercial_lease"})
    filled = res.json()["facts"]
    assert filled.get("notice_period_months") == 3
    for fact in ("monthly_rent_bdt", "security_deposit_bdt", "landlord_name", "commencement_date"):
        assert fact not in filled


def test_recheck_after_answers_becomes_ready():
    base = {
        "landlord_name": "Md. Karim", "landlord_father": "Abdul", "landlord_address": "Dhaka",
        "tenant_name": "Md. Rahim", "tenant_father": "Abdul", "tenant_address": "Dhaka",
        "premises_address": "Shop 1, Mirpur", "monthly_rent_bdt": 50000, "security_deposit_bdt": 100000,
        "duration_months": 12, "commencement_date": "01.01.2027", "permitted_business_type": "pharmacy",
        "execution_date": "20.12.2026",
    }
    res = client.post("/api/v1/intake/scenario-recheck", json={"matter_type": "commercial_lease", "facts": base})
    data = res.json()
    assert data["is_ready_for_drafting"] is True
    assert not [q for q in data["questions"] if q["critical"]]


def test_unknown_story_falls_back_to_custom():
    data = _analyze("আমরা দুই পক্ষ একটি বিশেষ বোঝাপড়া লিখিত রাখতে চাই।")
    assert data["matter_type"] == "custom"
