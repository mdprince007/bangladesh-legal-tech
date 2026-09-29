import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_advisory_cheque_dishonour_verified():
    res = client.post("/api/v1/advisory/resolve", json={
        "problem_description": "আমার পাওনাদার আমাকে একটা ৩ লাখ টাকার চেক দিয়েছিল, ব্যাংকে বাউন্স করেছে টাকা পাচ্ছি না"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["verified"] is True
    assert data["status"] == "VERIFIED_ROADMAP"
    assert "Negotiable Instruments Act" in str(data["applicable_laws"])
    assert len(data["roadmap_steps"]) >= 4
    # Check step 1, 2, 3, 4
    assert any("ডিজঅনার মেমো" in s["title"] for s in data["roadmap_steps"])
    assert any("আইনি ডিমান্ড নোটিশ" in s["title"] for s in data["roadmap_steps"])

def test_advisory_zero_guesswork_unverified():
    # An absurd or unverified question where legal authority does not exist
    res = client.post("/api/v1/advisory/resolve", json={
        "problem_description": "মহাকাশে এলিয়েনের সাথে জমি নিয়ে মারামারি হচ্ছে"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["verified"] is False
    assert data["status"] == "UNVERIFIED_KNOWLEDGE_GAP"
    assert "Zero Guesswork Policy" in data["message_bangla"]

def test_admin_stats_and_learning():
    res = client.get("/api/v1/admin/stats")
    assert res.status_code == 200
    data = res.json()
    assert "Operational" in data["platform_status"]
    assert data["verified_sections_count"] > 0

    learning_res = client.get("/api/v1/admin/learning")
    assert learning_res.status_code == 200
    learning_data = learning_res.json()
    assert learning_data["total_files"] >= 1
    assert any("Nasrin-book.pdf" in f["file_name"] for f in learning_data["files"])

def test_admin_ingest_nasrin_book():
    # Ingest full book (all 21 chapters)
    res = client.post("/api/v1/admin/ingest-nasrin-book", json={"ingest_all": True})
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["total_pages"] == 889
    assert data["total_chapters"] == 21
    assert data["total_lessons_created"] >= 100
    assert len(data["core_rules_extracted"]) >= 5

def test_admin_ingest_specific_chapter():
    # Ingest chapter 2 specifically
    res = client.post("/api/v1/admin/ingest-nasrin-book", json={"chapter_num": 2, "ingest_all": False})
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["chapter_num"] == 2
    assert "Agreements" in data["chapter_title"]
    assert len(data["core_rules_extracted"]) >= 4
    assert data["lessons_created"] >= 5

def test_admin_ingest_custom_file_and_management():
    # Test uploading custom legal file
    file_content = b"""Chapter 1: Bangladesh Labor Act Industrial Safety
Every establishment must maintain proper fire exits and safety measures under Section 61 of the Bangladesh Labor Act, 2006.
It is agreed that safety compliance is mandatory for all shifts.

Chapter 2: Working Hours and Overtime
Under Section 100, no adult worker shall normally work more than 8 hours in any day.
Overtime wages must be paid at double the ordinary rate of wages under Section 108.
"""
    files = {"file": ("labor_safety_guidelines.txt", file_content, "text/plain")}
    data = {"title": "Bangladesh Labor Safety & Hours Guidelines"}

    upload_res = client.post("/api/v1/admin/ingest-file", files=files, data=data)
    assert upload_res.status_code == 200
    upload_data = upload_res.json()
    assert upload_data["status"] == "success"
    assert upload_data["total_lessons"] >= 2
    doc_id = upload_data["document_id"]

    # Verify listing of ingested documents
    list_res = client.get("/api/v1/admin/ingested-documents")
    assert list_res.status_code == 200
    docs = list_res.json()
    assert any(d["id"] == doc_id for d in docs)

    # Verify lessons retrieval
    lessons_res = client.get(f"/api/v1/admin/ingested-documents/{doc_id}/lessons")
    assert lessons_res.status_code == 200
    lessons = lessons_res.json()
    assert len(lessons) >= 2
    assert any("Labor Act" in l["lesson_title"] for l in lessons)

    # Clean up / Delete document
    del_res = client.delete(f"/api/v1/admin/ingested-documents/{doc_id}")
    assert del_res.status_code == 200
    assert del_res.json()["status"] == "success"

