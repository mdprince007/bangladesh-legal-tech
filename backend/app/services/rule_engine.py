from typing import Dict, Any, List
from app.schemas.commercial_lease import CommercialLeaseFacts

class RuleEngine:
    @staticmethod
    def evaluate_commercial_lease(facts: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Executes deterministic Bangladesh legal rules on extracted commercial lease facts.
        """
        issues = []

        # Rule 1: Compulsory Registration check (Registration Act 1908, Sec 17 & TP Act 1882, Sec 107)
        duration_months = facts.get("duration_months", 0)
        if duration_months > 11:
            issues.append({
                "id": "RULE_REGISTRATION_REQUIRED",
                "issue_type": "statutory_caution",
                "severity": "high",
                "clause_title": "Duration & Compulsory Registration (মেয়াদ ও বাধ্যতামূলক রেজিস্ট্রেশন)",
                "message": f"Lease duration is {duration_months} months (exceeding 11 months). Under Section 17 of The Registration Act, 1908 and Section 107 of The Transfer of Property Act, 1882, this lease agreement CANNOT be executed on mere un-registered stamp paper. It must be executed on proper non-judicial stamp paper and registered with the Sub-Registry Office to be admissible as evidence of lease in court.",
                "message_bangla": f"ভাড়ার মেয়াদ {duration_months} মাস (১১ মাসের বেশি)। সম্পত্তি হস্তান্তর আইনের ১০৭ ধারা এবং রেজিস্ট্রেশন আইন ১৯০৮-এর ১৭ ধারা অনুযায়ী ১ বছরের অধিক মেয়াদের চুক্তি বাধ্যতামূলকভাবে রেজিস্ট্রি করতে হবে। অন্যথায় বিরোধ দেখা দিলে এটি আদালতে অকাট্য প্রমাণ হিসেবে গণ্য হবে না।",
                "suggested_fix": "Add a specific clause regarding compulsory registration and designate who will bear the registration fee and stamp duty.",
                "suggested_fix_bangla": "চুক্তিতে স্পষ্ট রেজিস্ট্রেশন ক্লজ যুক্ত করুন এবং সাব-রেজিস্ট্রি ফি কে দেবে তা নির্ধারণ করুন।",
                "statute_ref": "The Registration Act 1908, Section 17 & The Transfer of Property Act 1882, Section 107"
            })

        # Rule 2: Notice period check (Section 106, Transfer of Property Act 1882)
        notice_months = facts.get("notice_period_months", 0)
        if notice_months < 1:
            issues.append({
                "id": "RULE_NOTICE_TOO_SHORT",
                "issue_type": "statutory_caution",
                "severity": "medium",
                "clause_title": "Termination Notice Period (চুক্তি সমাপ্তির নোটিশ)",
                "message": "Notice period for commercial lease termination is less than 1 month. Under Section 106 of The Transfer of Property Act 1882, reasonable written notice is required. A minimum 30 to 60 days notice is strongly recommended for commercial premises.",
                "message_bangla": "বাণিজ্যিক চুক্তির সমাপ্তির নোটিশ মেয়াদ ১ মাসের কম। দোকান বা অফিসের ক্ষেত্রে স্বাভাবিক কার্যক্রম গুটিয়ে নিতে ন্যূনতম ১ থেকে ২ মাসের লিখিত নোটিশের শর্ত রাখা উচিত।",
                "suggested_fix": "Increase termination notice period to at least 1 or 2 months.",
                "suggested_fix_bangla": "নোটিশ পিরিয়ড বাড়িয়ে অন্তত ১ বা ২ মাস করুন।",
                "statute_ref": "The Transfer of Property Act 1882, Section 106"
            })

        # Rule 3: Security deposit refund terms
        deposit = facts.get("security_deposit_bdt", 0)
        monthly_rent = facts.get("monthly_rent_bdt", 0)
        if deposit > 0 and monthly_rent > 0:
            ratio = deposit / monthly_rent
            if ratio > 24:
                issues.append({
                    "id": "RULE_HIGH_ADVANCE_EXPOSURE",
                    "issue_type": "financial_risk",
                    "severity": "medium",
                    "clause_title": "Security Deposit / Advance Exposure (অগ্রিম জামানত ঝুঁকি)",
                    "message": f"Security deposit is {deposit:,} BDT, which is over {int(ratio)} months of rent. Ensure clear terms on whether this is refundable upon vacation or adjustable against monthly rent, and document previous utility dues clearance.",
                    "message_bangla": f"অগ্রিম জামানতের পরিমাণ {deposit:,} টাকা, যা মাসিক ভাড়ার চেয়ে {int(ratio)} গুণের বেশি। দোকান ছাড়ার কত দিনের মধ্যে এই টাকা ফেরত পাওয়া যাবে এবং ইউটিলিটি বিল কীভাবে সমন্বয় হবে তা স্পষ্টভাবে উল্লেখ থাকা আবশ্যক।",
                    "suggested_fix": "Specify that security deposit must be refunded within 30 days of handover, less legitimate utility arrears.",
                    "suggested_fix_bangla": "দোকান হস্তান্তর ও ইউটিলিটি বিল ছাড়পত্রের ৩০ দিনের মধ্যে জামানত ফেরতের সুস্পষ্ট শর্ত রাখুন।",
                    "statute_ref": "The Contract Act 1872, Section 73"
                })

        # Rule 4: Consistency check: Parties cannot have identical names unless explicitly designated
        landlord = (facts.get("landlord_name") or "").strip().lower()
        tenant = (facts.get("tenant_name") or "").strip().lower()
        if landlord and tenant and landlord == tenant:
            issues.append({
                "id": "RULE_IDENTICAL_PARTIES",
                "issue_type": "contradiction",
                "severity": "high",
                "clause_title": "Party Identification Error (পক্ষ পরিচিতি অসঙ্গতি)",
                "message": "Landlord name and Tenant name are identical. A person cannot lease commercial property to themselves in an individual capacity.",
                "message_bangla": "মালিক এবং ভাড়াটিয়ার নাম একই দেওয়া হয়েছে। কোনো ব্যক্তি নিজেকে নিজে বাণিজ্যিক ভাড়া চুক্তি সম্পাদন করতে পারেন না।",
                "suggested_fix": "Provide distinct legal names for the Landlord (Lessor) and Tenant (Lessee).",
                "suggested_fix_bangla": "মালিক এবং ভাড়াটিয়ার সঠিক ভিন্ন নাম প্রদান করুন।",
                "statute_ref": "The Contract Act 1872, Section 10"
            })

        return issues

rule_engine = RuleEngine()
