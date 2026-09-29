from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.services.ai_provider import ai_service
from app.services.rule_engine import rule_engine
from app.services.knowledge_service import KnowledgeService
from app.schemas.evaluation import EvaluationSuiteReport, EvaluationResultItem

EVALUATION_BENCHMARK_CASES = [
    {
        "case_name": "Commercial Lease Bangla Fact Extraction",
        "category": "extraction",
        "input": "আমি ধানমন্ডিতে একটা দোকান ৩ বছরের জন্য ভাড়া দিতে চাই। মাসিক ভাড়া ৫০,০০০ টাকা এবং জামানত ২ লাখ টাকা।",
        "expected": {
            "duration_months": 36,
            "monthly_rent_bdt": 50000,
            "security_deposit_bdt": 200000,
            "district": "Dhaka"
        }
    },
    {
        "case_name": "Compulsory Registration Rule Enforcement (Lease > 11 months)",
        "category": "rule_engine",
        "facts": {
            "duration_months": 36,
            "monthly_rent_bdt": 40000
        },
        "expected_issue_id": "RULE_REGISTRATION_REQUIRED"
    },
    {
        "case_name": "Anti-Hallucination Statute Guardrail",
        "category": "anti_hallucination",
        "statute_query": ("Transfer of Property Act", "106"),
        "fake_query": ("Transfer of Property Act", "999B"),
        "expected_real_verified": True,
        "expected_fake_verified": False
    },
    {
        "case_name": "Party Contradiction Detection",
        "category": "consistency",
        "facts": {
            "landlord_name": "Abdul Karim",
            "tenant_name": "Abdul Karim"
        },
        "expected_issue_id": "RULE_IDENTICAL_PARTIES"
    }
]

class EvaluationService:
    @staticmethod
    def run_suite(db: Session) -> EvaluationSuiteReport:
        """
        Executes automated AI & legal benchmark test cases to verify system correctness.
        """
        results: List[EvaluationResultItem] = []
        passed_count = 0

        # Case 1: Bangla Fact Extraction
        c1 = EVALUATION_BENCHMARK_CASES[0]
        extracted = ai_service.extract_structured_facts(c1["input"], {})
        c1_passed = (
            extracted.get("duration_months") == c1["expected"]["duration_months"] and
            extracted.get("monthly_rent_bdt") == c1["expected"]["monthly_rent_bdt"] and
            extracted.get("security_deposit_bdt") == c1["expected"]["security_deposit_bdt"]
        )
        if c1_passed:
            passed_count += 1
        results.append(EvaluationResultItem(
            case_name=c1["case_name"],
            passed=c1_passed,
            score=100.0 if c1_passed else 0.0,
            details={"extracted": extracted, "expected": c1["expected"]}
        ))

        # Case 2: Compulsory Registration Rule
        c2 = EVALUATION_BENCHMARK_CASES[1]
        issues_c2 = rule_engine.evaluate_commercial_lease(c2["facts"])
        c2_passed = any(i["id"] == c2["expected_issue_id"] for i in issues_c2)
        if c2_passed:
            passed_count += 1
        results.append(EvaluationResultItem(
            case_name=c2["case_name"],
            passed=c2_passed,
            score=100.0 if c2_passed else 0.0,
            details={"issues_found": [i["id"] for i in issues_c2]}
        ))

        # Case 3: Anti-Hallucination Verification
        c3 = EVALUATION_BENCHMARK_CASES[2]
        real_check = KnowledgeService.verify_statutory_reference(c3["statute_query"][0], c3["statute_query"][1], db)
        fake_check = KnowledgeService.verify_statutory_reference(c3["fake_query"][0], c3["fake_query"][1], db)
        c3_passed = (real_check["verified"] is True) and (fake_check["verified"] is False)
        if c3_passed:
            passed_count += 1
        results.append(EvaluationResultItem(
            case_name=c3["case_name"],
            passed=c3_passed,
            score=100.0 if c3_passed else 0.0,
            details={"real_check": real_check, "fake_check": fake_check}
        ))

        # Case 4: Consistency Check
        c4 = EVALUATION_BENCHMARK_CASES[3]
        issues_c4 = rule_engine.evaluate_commercial_lease(c4["facts"])
        c4_passed = any(i["id"] == c4["expected_issue_id"] for i in issues_c4)
        if c4_passed:
            passed_count += 1
        results.append(EvaluationResultItem(
            case_name=c4["case_name"],
            passed=c4_passed,
            score=100.0 if c4_passed else 0.0,
            details={"issues_found": [i["id"] for i in issues_c4]}
        ))

        total_cases = len(EVALUATION_BENCHMARK_CASES)
        accuracy = (passed_count / total_cases) * 100.0

        return EvaluationSuiteReport(
            suite_name="Legal AI Core Benchmark Suite",
            total_cases=total_cases,
            passed_cases=passed_count,
            overall_accuracy_percentage=accuracy,
            results=results
        )

evaluation_service = EvaluationService()
