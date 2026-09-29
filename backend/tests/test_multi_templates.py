import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_employment_agreement_generation():
    facts = {
        "employer_name": "Grameen Software Ltd.",
        "employer_address": "Karwan Bazar, Dhaka",
        "employee_name": "Tanvir Hasan",
        "employee_nid": "19942691234567890",
        "employee_address": "Mirpur-2, Dhaka",
        "designation": "Lead Full Stack Architect",
        "monthly_salary_bdt": 95000,
        "probation_months": 3,
        "joining_date": "15 March 2026",
        "notice_days": 30
    }
    res = client.post("/api/v1/drafting/generate", json={
        "template_code": "BD_EMPLOYMENT_AGREEMENT",
        "facts": facts,
        "style_preference": "balanced",
        "language": "en"
    })
    assert res.status_code == 200
    data = res.json()
    assert "Grameen Software Ltd." in data["full_text"]
    assert "Tanvir Hasan" in data["full_text"]
    assert "Lead Full Stack Architect" in data["full_text"]
    assert "Tk. 95,000/-" in data["full_text"]
    assert any(c["code"] == "EMP_APPOINTMENT_ROLE" for c in data["selected_clauses"])

def test_ni_act_138_demand_notice_generation():
    facts = {
        "advocate_name": "Advocate Kamal Hossain, Supreme Court of Bangladesh",
        "chamber_address": "Kakrail, Dhaka",
        "payee_name": "Mohammad Ali",
        "drawer_name": "Subir Kumar Ghosh",
        "drawer_address": "Chawkbazar, Chattogram",
        "cheque_no": "CQ-5544321",
        "cheque_date": "10 February 2026",
        "cheque_amount_bdt": 500000,
        "bank_name": "City Bank PLC, Principal Branch",
        "return_memo_date": "20 February 2026",
        "dishonour_reason": "Insufficient Funds",
        "notice_date": "01 March 2026"
    }
    res = client.post("/api/v1/drafting/generate", json={
        "template_code": "BD_LEGAL_NOTICE_NI_ACT",
        "facts": facts,
        "style_preference": "balanced",
        "language": "en"
    })
    assert res.status_code == 200
    data = res.json()
    assert "Subir Kumar Ghosh" in data["full_text"]
    assert "Mohammad Ali" in data["full_text"]
    assert "CQ-5544321" in data["full_text"]
    assert "Tk. 5,00,000/-" in data["full_text"]
    assert any(c["code"] == "NI_STATUTORY_DEMAND_30_DAYS" for c in data["selected_clauses"])

def test_residential_lease_generation():
    facts = {
        "landlord_name": "Afzal Hossain",
        "tenant_name": "Kabir Ahmed",
        "premises_address": "Flat 4-B, House 22, Road 5, Dhanmondi, Dhaka",
        "monthly_rent_bdt": 35000,
        "security_deposit_bdt": 70000,
        "duration_months": 24,
        "commencement_date": "01 April 2026"
    }
    res = client.post("/api/v1/drafting/generate", json={
        "template_code": "BD_RESIDENTIAL_LEASE",
        "facts": facts,
        "style_preference": "balanced",
        "language": "en"
    })
    assert res.status_code == 200
    data = res.json()
    assert "Afzal Hossain" in data["full_text"]
    assert "Kabir Ahmed" in data["full_text"]
    assert "Tk. 35,000/-" in data["full_text"]
    assert "Premises Rent Control Act, 1991" in data["full_text"]
    assert any(c["code"] == "RES_RENT_RECEIPT" for c in data["selected_clauses"])

def test_intake_chat_name_extraction_loop_fix():
    # 1. First user message gives general lease premise
    res1 = client.post("/api/v1/intake/chat", json={
        "matter_type": "commercial_lease",
        "current_facts": {},
        "conversation_history": [],
        "user_input": "আমি মিরপুর ঢাকায় একটা দোকান ৩ বছরের জন্য ভাড়া দিতে চাই। মাসিক ভাড়া ৫০,০০০ টাকা এবং জামানত ২ লাখ টাকা।"
    })
    assert res1.status_code == 200
    data1 = res1.json()
    facts1 = data1["extracted_facts"]
    assert facts1.get("monthly_rent_bdt") == 50000
    assert facts1.get("security_deposit_bdt") == 200000
    assert facts1.get("duration_months") == 36
    # It should ask for landlord_name
    assert data1["current_field_asked"] == "landlord_name"
    assert "মালিকের পূর্ণ নাম" in data1["assistant_reply_bangla"]

    # 2. User responds with just "Md Delowar" or "md polash" with last_asked_field="landlord_name"
    res2 = client.post("/api/v1/intake/chat", json={
        "matter_type": "commercial_lease",
        "current_facts": facts1,
        "conversation_history": [],
        "user_input": "md polash",
        "last_asked_field": "landlord_name"
    })
    assert res2.status_code == 200
    data2 = res2.json()
    facts2 = data2["extracted_facts"]
    # Verify landlord_name is extracted and NOT lost
    assert facts2.get("landlord_name") == "Md Polash"
    # Verify it does NOT ask for landlord name again! It should ask for tenant_name
    assert data2["current_field_asked"] == "tenant_name"
    assert "ভাড়াটিয়ার পূর্ণ নাম" in data2["assistant_reply_bangla"]

    # 3. User responds in Bengali "এমডি দেলোয়ার"
    res3 = client.post("/api/v1/intake/chat", json={
        "matter_type": "commercial_lease",
        "current_facts": facts2,
        "conversation_history": [],
        "user_input": "ভাড়াটিয়া হলো এমডি দেলোয়ার",
        "last_asked_field": "tenant_name"
    })
    assert res3.status_code == 200
    data3 = res3.json()
    facts3 = data3["extracted_facts"]
    assert "এমডি দেলোয়ার" in facts3.get("tenant_name", "")
    # premises_address was already extracted in step 1 ('Shop / Commercial Space, Mirpur, Dhaka')
    # So next missing field is permitted_business_type
    assert data3["current_field_asked"] == "permitted_business_type"

def test_multi_matter_intake_flow():
    # Test Employment Agreement Intake
    res = client.post("/api/v1/intake/chat", json={
        "matter_type": "employment_agreement",
        "current_facts": {},
        "conversation_history": [],
        "user_input": "কোম্পানি টেক সল্যুশনস লিমিটেড",
        "last_asked_field": "employer_name"
    })
    assert res.status_code == 200
    data = res.json()
    assert "employer_name" in data["extracted_facts"]
    assert data["current_field_asked"] == "employee_name"

def test_partnership_deed_generation():
    facts = {
        "firm_name": "Bengal Agro Traders",
        "partner_one": "Rahim Chowdhury",
        "partner_two": "Karim Mia",
        "business_nature": "Wholesale agricultural trading and distribution",
        "capital_contribution": "BDT 1,000,000 contributed equally (50:50)",
        "profit_sharing_ratio": "50% to Rahim Chowdhury, 50% to Karim Mia",
        "commencement_date": "01 April 2026",
        "district": "Dhaka"
    }
    res = client.post("/api/v1/drafting/generate", json={
        "template_code": "BD_PARTNERSHIP_DEED",
        "facts": facts,
        "style_preference": "balanced",
        "language": "en"
    })
    assert res.status_code == 200
    data = res.json()
    assert "Bengal Agro Traders" in data["full_text"]
    assert "The Partnership Act, 1932" in data["full_text"]
    assert any(c["code"] == "PART_CAPITAL_PROFIT" for c in data["selected_clauses"])

def test_sale_agreement_generation():
    facts = {
        "seller_name": "Sultana Razia",
        "buyer_name": "Mustafizur Rahman",
        "property_schedule": "Mouza Gulshan, Khatian 402, Plot 110, Flat 5-A (1800 sq ft)",
        "total_price_bdt": 15000000,
        "earnest_money_bdt": 3000000,
        "completion_deadline": "31 May 2026",
        "district": "Dhaka"
    }
    res = client.post("/api/v1/drafting/generate", json={
        "template_code": "BD_SALE_AGREEMENT",
        "facts": facts,
        "style_preference": "balanced",
        "language": "en"
    })
    assert res.status_code == 200
    data = res.json()
    assert "Sultana Razia" in data["full_text"]
    assert "Mustafizur Rahman" in data["full_text"]
    assert "Tk. 1,50,00,000/-" in data["full_text"]
    assert "Specific Relief Act, 1877" in data["full_text"]
    assert any(c["code"] == "SALE_SPECIFIC_PERFORMANCE_DEFAULT" for c in data["selected_clauses"])

def test_loan_agreement_generation():
    facts = {
        "lender_name": "Dr. Shamsul Huda",
        "borrower_name": "Tariqul Islam",
        "loan_amount_bdt": 500000,
        "loan_purpose": "Urgent working capital expansion",
        "repayment_deadline": "31 December 2026",
        "security_details": "Cheque No CQ-991244 of Sonali Bank PLC",
        "district": "Dhaka"
    }
    res = client.post("/api/v1/drafting/generate", json={
        "template_code": "BD_LOAN_AGREEMENT",
        "facts": facts,
        "style_preference": "balanced",
        "language": "en"
    })
    assert res.status_code == 200
    data = res.json()
    assert "Dr. Shamsul Huda" in data["full_text"]
    assert "Tariqul Islam" in data["full_text"]
    assert "Tk. 5,00,000/-" in data["full_text"]
    assert "The Negotiable Instruments Act, 1881" in data["full_text"]

def test_custom_agreement_generation():
    facts = {
        "custom_matter_name": "Software Supply and Integration Agreement",
        "party_one_name": "Apex Enterprise Ltd.",
        "party_one_role": "Client",
        "party_two_name": "CodeWorks Bangladesh",
        "party_two_role": "Developer",
        "purpose_and_consideration": "Development of customized logistics ERP for BDT 750,000",
        "obligations_first_party": "Provide timely system specifications and approve milestone sprints",
        "obligations_second_party": "Deliver bug-free code modules with 99.9% uptime warranty",
        "breach_and_cure_period": "15 days formal cure notice, followed by liquidated damages under Section 73",
        "termination_and_dispute": "30 days notice; binding arbitration in Dhaka under Arbitration Act 2001",
        "district": "Dhaka"
    }
    res = client.post("/api/v1/drafting/generate", json={
        "template_code": "BD_CUSTOM_AGREEMENT",
        "facts": facts,
        "style_preference": "balanced",
        "language": "en"
    })
    assert res.status_code == 200
    data = res.json()
    assert "SOFTWARE SUPPLY AND INTEGRATION AGREEMENT" in data["full_text"]
    assert "Apex Enterprise Ltd." in data["full_text"]
    assert "CodeWorks Bangladesh" in data["full_text"]
    assert "The Contract Act, 1872" in data["full_text"]
    assert any(c["code"] == "CUSTOM_BREACH_REMEDIES" for c in data["selected_clauses"])

def test_custom_contract_intake_flow():
    # 1. First prompt asks for custom title
    res1 = client.post("/api/v1/intake/chat", json={
        "matter_type": "custom",
        "current_facts": {},
        "conversation_history": [],
        "user_input": "আমি একটা পণ্য সরবরাহ চুক্তি করতে চাই",
        "last_asked_field": None
    })
    assert res1.status_code == 200
    data1 = res1.json()
    assert data1["current_field_asked"] == "custom_matter_name"

    # 2. User provides custom title
    res2 = client.post("/api/v1/intake/chat", json={
        "matter_type": "custom",
        "current_facts": {},
        "conversation_history": [],
        "user_input": "বার্ষিক পণ্য সরবরাহ ও বিতরণ চুক্তি",
        "last_asked_field": "custom_matter_name"
    })
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["extracted_facts"]["custom_matter_name"] == "বার্ষিক পণ্য সরবরাহ ও বিতরণ চুক্তি"
    assert data2["current_field_asked"] == "party_one_name"

def test_document_update_and_versioning():
    # 1. Generate a draft
    facts = {
        "landlord_name": "Rahim Uddin",
        "tenant_name": "Karim Sheikh",
        "premises_address": "Dhanmondi, Dhaka",
        "monthly_rent_bdt": 40000,
        "security_deposit_bdt": 80000,
        "duration_months": 24
    }
    res = client.post("/api/v1/drafting/generate", json={
        "template_code": "BD_COMMERCIAL_LEASE",
        "facts": facts,
        "style_preference": "balanced",
        "language": "en"
    })
    assert res.status_code == 200
    doc_data = res.json()
    doc_id = doc_data["id"]

    # 2. Update document via PUT /api/v1/documents/{doc_id}
    updated_text = doc_data["full_text"] + "\n\nADDITIONAL STIPULATION: Tenant permitted rooftop garden access."
    res_update = client.put(f"/api/v1/documents/{doc_id}", json={
        "full_text": updated_text,
        "change_summary": "Added rooftop garden covenant"
    })
    assert res_update.status_code == 200
    updated_data = res_update.json()
    assert "ADDITIONAL STIPULATION: Tenant permitted rooftop garden access." in updated_data["full_text"]

    # 3. Check version history via GET /api/v1/documents/{doc_id}/versions
    res_versions = client.get(f"/api/v1/documents/{doc_id}/versions")
    assert res_versions.status_code == 200
    versions = res_versions.json()
    assert len(versions) >= 2
    assert any(v["version_num"] == 2 for v in versions)

    # 4. Check list documents via GET /api/v1/documents/
    res_list = client.get("/api/v1/documents/")
    assert res_list.status_code == 200
    docs_list = res_list.json()
    assert any(d["id"] == doc_id for d in docs_list)

def test_book_grounding_compliance():
    """
    Verifies that generated documents provide Dr. Syeda Nasrin's book grounding score (>=90%),
    chapter references, applied rules list, and clause-level book citations.
    """
    res = client.post("/api/v1/drafting/generate", json={
        "template_code": "BD_COMMERCIAL_LEASE",
        "facts": {
            "landlord_name": "Rahim Chowdhury",
            "tenant_name": "Karim Traders Ltd",
            "premises_address": "Shop 4, Banani, Dhaka",
            "monthly_rent_bdt": 45000,
            "security_deposit_bdt": 135000,
            "duration_months": 24
        },
        "style_preference": "balanced",
        "language": "en"
    })
    assert res.status_code == 200
    data = res.json()

    # Verify book grounding score
    assert data["book_grounding_score"] is not None
    assert data["book_grounding_score"] < 100  # sparse facts: honest checklist score
    from app.services.bangla_text import normalize_bangla
    assert normalize_bangla("অধ্যায় ২") in normalize_bangla(data["book_chapter_reference"])
    assert len(data["book_applied_rules"]) >= 3
    missing_fields = {m["field"] for m in data["missing_information"]}
    assert {"execution_date", "landlord_father", "commencement_date"} <= missing_fields
    assert "Rahim Chowdhury" in data["full_text"] and "……" in data["full_text"]

    # Verify each clause has a book reference
    clauses = data["selected_clauses"]
    assert len(clauses) > 0
    for clause in clauses:
        assert clause["book_reference"] is not None
        assert normalize_bangla("অধ্যায়") in normalize_bangla(clause["book_reference"])

    # Verify retrieval via GET /api/v1/documents/{id}
    doc_id = data["id"]
    get_res = client.get(f"/api/v1/documents/{doc_id}")
    assert get_res.status_code == 200
    get_data = get_res.json()
    assert get_data["book_grounding_score"] == data["book_grounding_score"]
    assert get_data["book_chapter_reference"] == data["book_chapter_reference"]
    assert len(get_data["book_applied_rules"]) == len(data["book_applied_rules"])






def test_complete_facts_follow_book_format():
    facts = {
        "landlord_name": "Rahim Chowdhury", "landlord_father": "Late Abdul Chowdhury", "landlord_address": "House 5, Road 2, Banani, Dhaka",
        "landlord_permanent_address": "same", "tenant_name": "Karim Uddin", "tenant_father": "Abdul Karim", "tenant_address": "Mirpur-10, Dhaka",
        "tenant_permanent_address": "same", "premises_address": "Shop 4, Ground Floor, Banani Super Market, Dhaka", "monthly_rent_bdt": 45000,
        "security_deposit_bdt": 135000, "duration_months": 24, "commencement_date": "01.01.2027", "permitted_business_type": "pharmacy",
        "execution_date": "20.12.2026", "witness_one": "Md. Salam, son of Md. Kalam, Mirpur, Dhaka", "witness_two": "Md. Jamal, son of Md. Kamal, Uttara, Dhaka",
        "notice_period_months": 3, "rent_escalation_pct": 10, "rent_due_day_of_month": 7,
    }
    data = client.post("/api/v1/drafting/generate", json={"template_code": "BD_COMMERCIAL_LEASE", "facts": facts}).json()
    text = data["full_text"]
    assert data["book_grounding_score"] == 100
    for marker in ["BETWEEN", "……..FIRST PARTY/LESSOR", "WHEREAS", "NOW THIS AGREEMENT WITNESSETH", "IN WITNESS WHEREOF",
                   "Tk. 45,000/- (Taka Forty-Five Thousand) only", "Tk. 1,35,000/- (Taka One Lac Thirty-Five Thousand) only",
                   "2 (Two) years", "90 (Ninety) days", "Section 107 of the Transfer of Property Act, 1882", "heirs, successors"]:
        assert marker in text, marker
    assert not [m for m in data["missing_information"] if m["critical"]]
    assert data["drafting_warnings"]


def test_ni_notice_follows_book_format_and_timeline():
    facts = {"payee_name": "Subir Kumar Ghosh", "payee_address": "Dhanmondi, Dhaka", "drawer_name": "Mohammad Ali", "drawer_address": "Uttara, Dhaka",
             "cheque_no": "CQ-5544321", "cheque_date": "01.01.2026", "cheque_amount_bdt": 500000, "bank_name": "Sonali Bank PLC, Motijheel Branch",
             "presentation_date": "10.01.2026", "return_memo_date": "12.01.2026", "dishonour_reason": "Insufficient Fund",
             "liability_background": "the Notice Receiver borrowed the said amount on 01.10.2025 for business purpose",
             "advocate_name": "Md. Rahman", "notice_date": "20.03.2026"}
    data = client.post("/api/v1/drafting/generate", json={"template_code": "BD_LEGAL_NOTICE_NI_ACT", "facts": facts}).json()
    text = data["full_text"]
    for marker in ["LEGAL NOTICE", "(REGISTERED WITH A/D)", "……..NOTICE RECEIVER", "For and on behalf of:", "Subject: Legal Notice under Sections 138 and 140",
                   "within 30 (Thirty) days of receipt of this notice", "A copy of this Legal Notice is kept in our Chamber"]:
        assert marker in text, marker
    assert len(data["drafting_warnings"]) >= 1  # notice sent more than 30 days after dishonour
