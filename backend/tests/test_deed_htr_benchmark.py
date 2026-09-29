import pytest
import os
import cv2
import numpy as np
from fastapi.testclient import TestClient
from app.main import app
from app.services.deed_cv_pipeline import deed_cv_pipeline
from app.services.deed_htr_engine import deed_htr_engine

client = TestClient(app)

SAMPLE_DEED_PATH = r"C:\Users\Lenovo\.gemini\antigravity\brain\f5b387fc-eb28-4e1b-9940-b3291f442234\.user_uploaded\media_1789496843822.jpg"

def test_cv_pipeline_image_quality():
    """Phase 3: Verify Image Quality Analysis detects resolution, blur, contrast, and skew."""
    if not os.path.exists(SAMPLE_DEED_PATH):
        pytest.skip("Sample deed image not found on local path")

    report = deed_cv_pipeline.analyze_image_quality(SAMPLE_DEED_PATH)
    assert report["width"] == 526
    assert report["height"] == 845
    assert report["estimated_dpi"] > 50
    assert report["blur_metric"] > 0
    assert report["contrast_std"] > 0
    assert "quality_level" in report
    assert "quality_badge_bn" in report
    assert len(report["warnings"]) > 0  # Should warn about low resolution 61 DPI

def test_cv_pipeline_line_segmentation():
    """Phase 8: Verify Handwritten Text Line Segmentation returns line coordinates."""
    if not os.path.exists(SAMPLE_DEED_PATH):
        pytest.skip("Sample deed image not found on local path")

    img = cv2.imread(SAMPLE_DEED_PATH)
    lines = deed_cv_pipeline.segment_handwritten_lines(img)
    assert len(lines) >= 10, f"Expected at least 10 lines, got {len(lines)}"

    for line in lines:
        assert "line_index" in line
        assert "bbox" in line
        assert len(line["bbox"]) == 4
        x1, y1, x2, y2 = line["bbox"]
        assert x2 > x1
        assert y2 > y1
        assert line["height_px"] >= 10

def test_cer_and_wer_computation():
    """Phase 23: Verify Character Error Rate (CER) and Word Error Rate (WER) metrics."""
    ref = "মোঃ আব্দুর রশিদ খাঁন"
    hyp_exact = "মোঃ আব্দুর রশিদ খাঁন"
    assert deed_htr_engine.calculate_cer(ref, hyp_exact) == 0.0
    assert deed_htr_engine.calculate_wer(ref, hyp_exact) == 0.0

    # 1 substitution in name (রশিদ -> রহিম)
    hyp_sub = "মোঃ আব্দুর রহিম খাঁন"
    cer = deed_htr_engine.calculate_cer(ref, hyp_sub)
    wer = deed_htr_engine.calculate_wer(ref, hyp_sub)
    assert 0.0 < cer < 0.25
    assert wer == 0.25  # 1 out of 4 words

def test_bangla_numeral_parsing():
    """Phase 15: Verify specialized Bengali & English numeral parser."""
    assert deed_htr_engine.parse_bangla_number("১২.৫০ শতক") == 12.50
    assert deed_htr_engine.parse_bangla_number("দাগ নং ২৩১৮") == 2318.0
    assert deed_htr_engine.parse_bangla_number("মূল্য ৪৮০০০ টাকা") == 48000.0

def test_structured_fields_traceability():
    """Phase 14 & 27: Verify all 21 fields exist with bounding boxes and no fake hallucination."""
    if not os.path.exists(SAMPLE_DEED_PATH):
        pytest.skip("Sample deed image not found on local path")

    img = cv2.imread(SAMPLE_DEED_PATH)
    lines = deed_cv_pipeline.segment_handwritten_lines(img)
    zones = deed_cv_pipeline.detect_document_layout_zones(img)
    fields = deed_htr_engine.extract_structured_deed_fields(img, lines, zones, SAMPLE_DEED_PATH, "media_1789496843822.jpg")

    required_fields = [
        "DOCUMENT_NUMBER", "DATE", "BUYER", "SELLER", "DONOR", "RECIPIENT",
        "FATHER_OR_HUSBAND", "ADDRESS", "MOUZA", "JL_NUMBER", "KHATIAN_NUMBER",
        "DAG_NUMBER", "LAND_AREA", "LAND_UNIT", "LAND_CLASS", "NORTH_BOUNDARY",
        "SOUTH_BOUNDARY", "EAST_BOUNDARY", "WEST_BOUNDARY", "PRICE", "REGISTRATION_OFFICE", "WITNESSES"
    ]

    for rf in required_fields:
        assert rf in fields, f"Field {rf} missing from extracted fields"
        f_data = fields[rf]
        assert "value" in f_data
        assert "confidence" in f_data
        assert "status" in f_data
        assert "bbox" in f_data
        assert len(f_data["bbox"]) == 4

def test_deed_correction_and_dev_endpoints():
    """Phase 20 & 24: Test correction recording and developer crop evaluation."""
    # 1. Test sample deed retrieval
    res = client.get("/api/v1/deeds/samples")
    assert res.status_code == 200
    samples = res.json()
    assert len(samples) > 0
    sample_id = samples[0]["id"]

    # 2. Add correction
    corr_payload = {
        "deed_id": sample_id,
        "field_key": "LAND_AREA",
        "line_index": 12,
        "source_bbox": [50, 400, 450, 430],
        "ai_prediction": "১২.০০ শতক",
        "human_correction": "১২.৫০ শতক",
        "confidence": 100,
        "verified_by": "advocate_test"
    }
    corr_res = client.post(f"/api/v1/deeds/{sample_id}/corrections", json=corr_payload)
    assert corr_res.status_code == 200
    assert corr_res.json()["status"] == "saved"

    # 3. List corrections for training dataset export
    list_res = client.get("/api/v1/deeds/dev/corrections")
    assert list_res.status_code == 200
    assert len(list_res.json()) >= 1

    # 4. Developer crop test
    dummy_crop = np.zeros((40, 200, 3), dtype=np.uint8)
    _, enc = cv2.imencode(".jpg", dummy_crop)
    crop_res = client.post(
        "/api/v1/deeds/dev/crop-test",
        files={"file": ("line_crop.jpg", enc.tobytes(), "image/jpeg")},
        data={"ground_truth": "মৌজা রামপুর", "field_key": "MOUZA"}
    )
    assert crop_res.status_code == 200
    dev_data = crop_res.json()
    assert "passes" in dev_data
    assert "best_prediction" in dev_data
    assert "cer" in dev_data
