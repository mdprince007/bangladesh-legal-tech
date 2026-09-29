import pytest
from app.services.rule_engine import rule_engine

def test_rule_compulsory_registration():
    # Lease duration 12 months (> 11 months)
    facts = {"duration_months": 12, "monthly_rent_bdt": 20000}
    issues = rule_engine.evaluate_commercial_lease(facts)
    assert any(i["id"] == "RULE_REGISTRATION_REQUIRED" for i in issues)

    # Lease duration 11 months -> should NOT trigger compulsory registration
    facts_short = {"duration_months": 11, "monthly_rent_bdt": 20000}
    issues_short = rule_engine.evaluate_commercial_lease(facts_short)
    assert not any(i["id"] == "RULE_REGISTRATION_REQUIRED" for i in issues_short)

def test_rule_party_contradiction():
    facts = {
        "landlord_name": "Rahim Uddin",
        "tenant_name": "Rahim Uddin",
        "monthly_rent_bdt": 30000
    }
    issues = rule_engine.evaluate_commercial_lease(facts)
    assert any(i["id"] == "RULE_IDENTICAL_PARTIES" for i in issues)

def test_rule_notice_period():
    facts = {"notice_period_months": 0}
    issues = rule_engine.evaluate_commercial_lease(facts)
    assert any(i["id"] == "RULE_NOTICE_TOO_SHORT" for i in issues)
