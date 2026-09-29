import io
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.deed_fraud_engine import deed_fraud_engine

client = TestClient(app)

def test_sample_deeds_retrieval():
    res = client.get("/api/v1/deeds/samples")
    assert res.status_code == 200
    samples = res.json()
    assert len(samples) >= 3
    
    titles = [s["deed_title"] for s in samples]
    assert any("১৯৭৪" in t for t in titles)
    assert any("১৯৮৮" in t for t in titles)
    assert any("জাল" in t for t in titles)

def test_sample_deed_detail_and_unclear_words():
    res = client.get("/api/v1/deeds/samples/sample-deed-1974-saf-kabala")
    assert res.status_code == 200
    deed = res.json()
    assert deed["deed_type"] == "saf_kabala"
    assert deed["mouza"] == "কাফরুল"
    assert deed["schedule"]["transferred_area_decimals"] == 10.5
    assert len(deed["unclear_texts"]) > 0
    
    # Check unclear text item structure
    unclear = deed["unclear_texts"][0]
    assert "term_location" in unclear
    assert "alternatives" in unclear
    assert unclear["confidence_score"] > 0

def test_deed_fraud_engine_detects_chronology_and_overtransfer():
    # Test forged deed detection
    res = client.get("/api/v1/deeds/samples/sample-deed-1952-fake-forgery")
    assert res.status_code == 200
    fake = res.json()
    assert fake["fraud_risk_score"] >= 50
    assert fake["fraud_risk_level"] == "high_risk_probable_forgery"
    
    flags = [f["title"] for f in fake["fraud_assessment"]["red_flags"]]
    assert any("কালানুক্রমিক" in f for f in flags)
    assert any("বায়া দলিলের" in f for f in flags)
    assert "সতর্কতা" in fake["fraud_assessment"]["legal_recommendation"]

def test_deed_upload_and_enhancement():
    # Create fake deed file in memory
    from PIL import Image
    img_byte_arr = io.BytesIO()
    img = Image.new("RGB", (300, 400), color=(240, 230, 210))
    img.save(img_byte_arr, format="JPEG")
    img_byte_arr.seek(0)

    files = {"file": ("uploaded_saf_kabala_1980.jpg", img_byte_arr, "image/jpeg")}
    data = {"deed_type": "saf_kabala"}
    res = client.post("/api/v1/deeds/upload", files=files, data=data)
    assert res.status_code == 200
    out = res.json()
    assert out["id"] is not None
    assert out["deed_type"] == "saf_kabala"
    # A blank page must not produce invented values
    assert out["schedule"]["mouza"] is None
    assert out["parties"]["first_party_name"] is None
    report = out["reading_report"]
    assert report["fields"]["land_area"]["status"] == "not_found"
    assert report["summary"]["fully_verified"] is False
    assert out["docx_url"] is not None
    assert out["pdf_url"] is not None
    assert out["enhanced_image_path"] is not None

    # Test list endpoint
    list_res = client.get("/api/v1/deeds/")
    assert list_res.status_code == 200
    items = list_res.json()
    assert any(i["id"] == out["id"] for i in items)

    # Test update and re-audit endpoint
    update_res = client.put(f"/api/v1/deeds/{out['id']}", json={
        "parties": {"first_party_name": "হাজী আব্দুল মতিন", "second_party_name": "মোঃ দেলোয়ার হোসেন"},
        "schedule": {"mouza": "উত্তরা", "khatian_rs": "৯৮০", "transferred_area_decimals": 12.0}
    })
    assert update_res.status_code == 200
    updated = update_res.json()
    assert updated["parties"]["first_party_name"] == "হাজী আব্দুল মতিন"
    assert updated["parties"]["second_party_name"] == "মোঃ দেলোয়ার হোসেন"
    assert updated["schedule"]["mouza"] == "উত্তরা"

