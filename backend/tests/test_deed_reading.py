import io
import os

import pytest
from fastapi.testclient import TestClient

os.environ["LOCAL_OCR_ENABLED"] = "0"

from app.main import app  # noqa: E402
from app.services import deed_reading_service as drs  # noqa: E402
from app.services.bangla_text import (  # noqa: E402
    parse_bangla_number_words, parse_land_area, parse_share, comparison_key,
)

client = TestClient(app)


def _f(value, conf=95, legibility="clear", verbatim=None, alts=None):
    return {"value": value, "verbatim": verbatim or value, "legibility": legibility,
            "confidence": conf, "alternatives": alts or [], "page": 0, "bbox": [100, 100, 500, 140]}


BASE_FIELDS = {
    "deed_type": _f("সাফ কবলা"),
    "deed_number": _f("২৯৪৬/১৯৯৩"),
    "registration_date": _f("২০/০৪/১৯৯৩ ইং, ০৭ বৈশাখ ১৪০০ বাং"),
    "seller_names": _f("মোঃ আব্দুর রশিদ খাঁন"),
    "buyer_names": _f("মোঃ ইউনুছ আলী খাঁন"),
    "mouza": _f("রামপুর"),
    "jl_no": _f("৪২"),
    "khatian_sa": _f("৪৫০"),
    "dag_numbers": _f("২৩১৮"),
    "land_area": _f("১২.০০ শতাংশ"),
    "land_area_words": _f("বারো শতাংশ"),
    "share": _f("১৬ আনা"),
    "consideration_amount": _f("৪৮,০০০/- টাকা"),
    "consideration_words": _f("আটচল্লিশ হাজার টাকা মাত্র"),
}


def _pass(overrides=None, model="m"):
    fields = {k: dict(v) for k, v in BASE_FIELDS.items()}
    fields.update(overrides or {})
    return {"fields": fields, "schedule_rows": [], "full_transcription": "…", "model": model}


class FakeVision:
    def __init__(self, a, b):
        self.passes = [a, b]
        self.primary_model, self.secondary_model = "primary", "secondary"

    available = True

    def read(self, paths, model):
        return self.passes.pop(0)


def _read(a, b):
    svc = drs.DeedReadingService()
    svc.vision = FakeVision(a, b)
    return svc.read_deed(["x.jpg"], ["y.jpg"], [(1000, 1400)])


# --- Bangla parsing ---------------------------------------------------------

def test_number_words():
    assert parse_bangla_number_words("আটচল্লিশ হাজার টাকা মাত্র") == 48000
    assert parse_bangla_number_words("সাড়ে বারো শতক") == 12.5
    assert parse_bangla_number_words("এক লক্ষ পঁচিশ হাজার") == 125000
    assert parse_bangla_number_words("পাঁচশত") == 500
    assert parse_bangla_number_words("কোনো সংখ্যা নেই") is None


def test_land_area_and_share():
    assert parse_land_area("১ একর ২০ শতক")["decimals"] == 120
    assert parse_land_area("বারো শতাংশ")["decimals"] == 12
    assert parse_land_area("৫ গণ্ডা")["decimals"] is None  # regional unit is never auto-converted
    assert parse_share("৮ আনা") == 0.5
    assert parse_share("১০ আনা ৩ গণ্ডা") == pytest.approx((10 + 3 / 20) / 16)


def test_spelling_difference_is_not_agreement():
    assert comparison_key("খাঁন") != comparison_key("খান")
    assert comparison_key("২৯৪৬/১৯৯৩") == comparison_key("2946 / 1993")


# --- Reconciliation ---------------------------------------------------------

def test_agreeing_reads_are_machine_agreed_but_not_final():
    report = _read(_pass(), _pass())
    f = report["fields"]
    assert f["deed_number"]["status"] == "machine_agreed"
    assert any(c["ok"] for c in f["land_area"]["checks"])  # digits and words agree
    assert report["summary"]["fully_verified"] is False  # nothing is final until a person confirms


def test_disagreement_needs_review_with_both_readings():
    report = _read(_pass(), _pass({"seller_names": _f("মোঃ আব্দুর রহিম খাঁন")}))
    f = report["fields"]["seller_names"]
    assert f["status"] == "needs_review"
    assert "মোঃ আব্দুর রশিদ খাঁন" in f["alternatives"] and "মোঃ আব্দুর রহিম খাঁন" in f["alternatives"]


def test_area_digits_words_mismatch_is_flagged():
    wrong = {"land_area": _f("১৫.০০ শতাংশ")}
    report = _read(_pass(wrong), _pass(wrong))
    f = report["fields"]["land_area"]
    assert f["status"] == "needs_review"
    assert any(not c["ok"] and "মিলছে না" in c["message_bn"] for c in f["checks"])
    assert any("জমির পরিমাণ" in x["message_bn"] for x in report["findings"])


def test_price_mismatch_and_impossible_share():
    bad = {"consideration_words": _f("আটান্ন হাজার টাকা মাত্র"), "share": _f("১৮ আনা")}
    report = _read(_pass(bad), _pass(bad))
    assert report["fields"]["consideration_amount"]["status"] == "needs_review"
    assert report["fields"]["share"]["status"] == "needs_review"


def test_uncertain_marker_and_illegible():
    partial = {"dag_numbers": _f("২৩[?]৮", legibility="partial")}
    illegible = {"mouza": {"value": None, "legibility": "illegible", "confidence": 0}}
    report = _read(_pass({**partial, **illegible}), _pass({**partial, **illegible}))
    assert report["fields"]["dag_numbers"]["status"] == "needs_review"
    assert report["fields"]["mouza"]["status"] == "illegible"
    assert report["fields"]["mouza"]["value"] is None


def test_identical_parties_flagged():
    same = {"buyer_names": _f("মোঃ আব্দুর রশিদ খাঁন")}
    report = _read(_pass(same), _pass(same))
    assert report["fields"]["buyer_names"]["status"] == "needs_review"


def test_single_reader_never_machine_agreed():
    report = _read(_pass(), {"error": "quota", "model": "secondary"})
    assert all(f["status"] != "machine_agreed" for f in report["fields"].values())
    assert report["errors"]


def test_human_verification_settles_critical_fields():
    report = _read(_pass(), _pass())
    for key, f in report["fields"].items():
        if f["critical"]:
            report = drs.DeedReadingService.apply_human_verification(report, key, f["value"], "tester")
    assert report["summary"]["fully_verified"] is True


# --- API: upload, then a person corrects a field ----------------------------

def test_upload_then_verify_field(monkeypatch):
    fake = FakeVision(_pass({"land_area": _f("১৫.০০ শতাংশ")}), _pass())
    monkeypatch.setattr(drs.deed_reading_service, "vision", fake)

    from PIL import Image
    buf = io.BytesIO()
    Image.new("RGB", (600, 800), color=(250, 245, 230)).save(buf, format="JPEG")
    buf.seek(0)
    res = client.post("/api/v1/deeds/upload", files={"file": ("my_deed.jpg", buf, "image/jpeg")})
    assert res.status_code == 200
    deed = res.json()
    area = deed["reading_report"]["fields"]["land_area"]
    assert area["status"] == "needs_review"
    assert deed["schedule"]["mouza"] == "রামপুর"
    assert deed["page_images"]

    res = client.post(f"/api/v1/deeds/{deed['id']}/verify-field",
                      json={"field_key": "land_area", "value": "১২.০০ শতাংশ", "verified_by": "tester"})
    assert res.status_code == 200
    updated = res.json()
    f = updated["reading_report"]["fields"]["land_area"]
    assert f["status"] == "human_verified" and f["corrected"] is True
    assert updated["schedule"]["transferred_area_decimals"] == 12
    assert any(c["ok"] for c in f["checks"])  # now agrees with the area in words

    corrections = client.get("/api/v1/deeds/dev/corrections").json()
    assert any(c["deed_id"] == deed["id"] and c["field_key"] == "land_area" for c in corrections)

    status = client.get("/api/v1/deeds/engine-status").json()
    assert status["mode"] in ("dual_vision", "local_ocr_only", "manual_only")
