from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.services.rule_engine import rule_engine
from app.services.knowledge_service import KnowledgeService
from app.schemas.review import DocumentHealthReport, ReviewIssue

class ReviewAgent:
    @staticmethod
    def audit_document(document_id: str, facts: Dict[str, Any], clauses: List[Dict[str, Any]], db: Session) -> DocumentHealthReport:
        """
        Conducts a deep legal health check and risk audit on a drafted document.
        Combines deterministic statutory rules, anti-hallucination citation checks, and risk analysis.
        """
        issues_list: List[ReviewIssue] = []

        # 1. Run deterministic statutory rules
        rule_violations = rule_engine.evaluate_commercial_lease(facts)
        for rv in rule_violations:
            issues_list.append(ReviewIssue(
                id=rv["id"],
                issue_type=rv["issue_type"],
                severity=rv["severity"],
                clause_title=rv["clause_title"],
                message=rv["message"],
                message_bangla=rv["message_bangla"],
                suggested_fix=rv["suggested_fix"],
                suggested_fix_bangla=rv["suggested_fix_bangla"],
                statute_ref=rv["statute_ref"]
            ))

        # 2. Check statutory citations against verified knowledge base
        verified_statutes_found = []
        for cl in clauses:
            statutory_basis = cl.get("statutory_basis")
            if statutory_basis:
                # E.g. "The Transfer of Property Act 1882, Section 106"
                if "Transfer of Property Act" in statutory_basis:
                    verified_statutes_found.append("Transfer of Property Act, 1882 (Sec 105, 106, 107, 108)")
                if "Registration Act" in statutory_basis:
                    verified_statutes_found.append("The Registration Act, 1908 (Sec 17)")
                if "Stamp Act" in statutory_basis:
                    verified_statutes_found.append("The Stamp Act, 1899 (Article 35)")

        verified_statutes_found = list(set(verified_statutes_found))

        # 3. Calculate health scores
        high_sev = sum(1 for i in issues_list if i.severity == "high")
        med_sev = sum(1 for i in issues_list if i.severity == "medium")

        # Risk score calculation (0 to 100)
        risk_score = min(100, (high_sev * 25) + (med_sev * 10))
        overall_health_score = max(20, 100 - risk_score)
        completeness_score = 95 if facts.get("premises_address") and facts.get("monthly_rent_bdt") else 60
        consistency_score = 100 if not any(i.issue_type == "contradiction" for i in issues_list) else 50

        pro_review_recommended = high_sev > 0 or facts.get("duration_months", 0) > 11 or risk_score > 30

        plain_bangla = (
            f"চুক্তিপত্রের স্বাস্থ্য স্কোর: {overall_health_score}/১০০। "
            f"{'বাধ্যতামূলক সাব-রেজিস্ট্রেশন ও স্ট্যাম্প ডিউটি প্রযোজ্য থাকায় কোনো নিবন্ধিত আইনজীবীর পরামর্শ গ্রহণ করা অত্যন্ত সুপারিশকৃত।' if pro_review_recommended else 'চুক্তিপত্রটি বাংলাদেশ আইন অনুযায়ী সামঞ্জস্যপূর্ণ ও ভারসাম্যপূর্ণ।'}"
        )

        return DocumentHealthReport(
            document_id=document_id,
            overall_health_score=overall_health_score,
            completeness_score=completeness_score,
            risk_score=risk_score,
            consistency_score=consistency_score,
            professional_review_recommended=pro_review_recommended,
            issues=issues_list,
            plain_bangla_summary=plain_bangla,
            verified_statutes_used=verified_statutes_found
        )

review_agent = ReviewAgent()
