"""
Scenario analysis: the user describes the whole situation once (typed or spoken, Bangla or English).
We work out the document type, pull out ONLY the facts the user actually stated, and turn every
gap into a question with the book's reason for needing it.

Facts are never invented. Standard terms from Dr. Syeda Nasrin's book (e.g. 90 days' notice,
no sub-letting) are offered separately as suggestions the user can accept.
"""
import json
import os
import re
from typing import Any, Dict, List, Optional, Tuple

from app.core.config import settings
from app.services.ai_provider import ai_service
from app.services.bangla_text import normalize_bangla, normalize_digits
from app.services.drafting_engine import to_amount
from app.services.matter_requirements import (
    MATTER_TO_TEMPLATE, is_blank, missing_requirements, requirements_for,
)

MATTER_TITLES = {
    "commercial_lease": ("বাণিজ্যিক দোকান / অফিস স্পেস ভাড়া চুক্তিপত্র", "Commercial Tenancy Agreement"),
    "residential_rent": ("আবাসিক বাসা / ফ্ল্যাট ভাড়া চুক্তিপত্র", "Residential Tenancy Agreement"),
    "demand_notice_ni_act": ("চেক ডিজঅনারের আইনি নোটিশ (ধারা ১৩৮)", "Legal Notice u/s 138 NI Act"),
    "sale_agreement": ("স্থাবর সম্পত্তি বিক্রয়ের বায়নাপত্র", "Agreement for Sale"),
    "partnership_deed": ("অংশীদারি কারবারের চুক্তিপত্র", "Deed of Partnership"),
    "loan_agreement": ("হাওলাতনামা / ঋণ চুক্তিপত্র", "Loan Agreement (Hawlatnama)"),
    "employment_agreement": ("চাকরির নিয়োগ চুক্তিপত্র", "Employment Agreement"),
    "nda": ("গোপনীয়তা চুক্তিপত্র", "Non-Disclosure Agreement"),
    "service_agreement": ("সেবা প্রদান চুক্তিপত্র", "Service Agreement"),
    "custom": ("কাস্টম চুক্তিপত্র", "Custom Agreement"),
}

# keyword -> weight, per matter type. The highest total wins; ties/no match -> 'custom'.
_TYPE_KEYWORDS: Dict[str, List[str]] = {
    "demand_notice_ni_act": ["চেক", "cheque", "check bounce", "dishonour", "dishonor", "বাউন্স", "ডিজঅনার", "১৩৮", "138", "ফেরত মেমো"],
    "commercial_lease": ["দোকান", "shop", "commercial", "বাণিজ্যিক", "অফিস স্পেস", "মার্কেট", "শোরুম", "showroom", "গোডাউন", "warehouse"],
    "residential_rent": ["বাসা", "ফ্ল্যাট", "flat", "apartment", "residential", "বাড়িওয়ালা", "পরিবার নিয়ে", "থাকার জন্য"],
    "sale_agreement": ["বায়না", "বিক্রি", "বিক্রয়", "কিনব", "কিনতে", "জমি কেনা", "plot", "sale agreement", "purchase", "সাফ কবলা"],
    "partnership_deed": ["অংশীদার", "partnership", "পার্টনার", "partner", "যৌথ ব্যবসা"],
    "loan_agreement": ["হাওলাত", "ঋণ", "ধার দিয়েছি", "ধার দিব", "loan", "কর্জ"],
    "employment_agreement": ["চাকরি", "নিয়োগ", "employment", "employee", "বেতন", "salary", "কর্মচারী"],
    "nda": ["গোপনীয়তা", "nda", "confidential", "non-disclosure", "নন ডিসক্লোজার"],
    "service_agreement": ["সার্ভিস", "service agreement", "vendor", "ভেন্ডর", "সফটওয়্যার তৈরি", "consultancy", "পরামর্শ সেবা"],
}


def infer_matter_type(text: str) -> str:
    t = (text or "").lower()
    scores = {k: sum(1 for kw in kws if kw.lower() in t) for k, kws in _TYPE_KEYWORDS.items()}
    # a cheque that bounced is a notice matter even if the story mentions rent or a loan
    if scores["demand_notice_ni_act"] >= 2 or (scores["demand_notice_ni_act"] and any(w in t for w in ("বাউন্স", "ডিজঅনার", "dishono", "bounce"))):
        return "demand_notice_ni_act"
    best = max(scores.items(), key=lambda kv: kv[1])
    return best[0] if best[1] > 0 else "custom"


# ---------------------------------------------------------------------------
# Extraction
# ---------------------------------------------------------------------------
def _llm_extract(text: str, matter_type: Optional[str]) -> Optional[Dict[str, Any]]:
    key = settings.GEMINI_API_KEY or os.getenv("GEMINI_API_KEY", "")
    if not key:
        return None
    types_list = ", ".join(MATTER_TITLES.keys())
    if matter_type:
        field_lines = "\n".join(f'- "{r["field"]}": {r["label_bn"]}' for r in requirements_for(matter_type))
    else:
        field_lines = "\n".join(
            f'[{mt}]\n' + "\n".join(f'- "{r["field"]}": {r["label_bn"]}' for r in requirements_for(mt))
            for mt in MATTER_TITLES
        )
    prompt = f"""A client in Bangladesh has described their legal situation (Bangla and/or English, possibly
transcribed from speech, so it may contain filler words and minor transcription errors).

Task:
1. Decide the document type ("matter_type"), one of: {types_list}.
2. Extract ONLY facts the client explicitly stated. Never guess, never fill in typical values.
   Keep names and addresses exactly as the client said them. Amounts as plain numbers in taka
   (e.g. "২ লাখ ৫০ হাজার" -> 250000). Durations in months for *_months fields.
3. For every extracted fact give the exact words from the client's text as evidence.
4. List anything ambiguous or contradictory in "unclear" (in Bangla).

Allowed field keys:
{field_lines}

Client's text:
\"\"\"{text}\"\"\"

Return only JSON: {{"matter_type": str, "facts": {{field: value}}, "evidence": {{field: str}}, "unclear": [str]}}"""
    try:
        from google import genai
        from google.genai import types
        client = genai.Client(api_key=key)
        resp = client.models.generate_content(
            model=os.getenv("SCENARIO_MODEL", "gemini-2.5-flash"),
            contents=prompt,
            config=types.GenerateContentConfig(temperature=0, response_mime_type="application/json"),
        )
        data = json.loads(re.sub(r"^```(?:json)?\s*|\s*```$", "", resp.text.strip()))
        if not isinstance(data.get("facts"), dict):
            return None
        return data
    except Exception:
        return None


_NAME = r"([A-Za-zঀ-৿\.]+(?:\s+[A-Za-zঀ-৿\.]+){0,4})"
_STOP_WORDS = ("দোকান", "ভাড়া", "একটি", "একটা", "টাকা", "বছর", "মাস", "জন্য", "সাথে", "কাছে", "আমার", "আমি", "চুক্তি", "করতে", "দিতে", "নিতে", "হবে", "সাহেব")


def _clean_name(raw: str) -> Optional[str]:
    words = []
    for w in raw.split():
        if any(w.startswith(sw) for sw in _STOP_WORDS):
            break
        words.append(w)
    name = " ".join(words).strip(" ,।.")
    return name if len(name) >= 3 else None


def _amount_after(text: str, keywords: List[str]) -> Optional[int]:
    for kw in keywords:
        kw = normalize_bangla(kw)
        m = re.search(rf"{kw}[^\d০-৯]{{0,25}}([\d০-৯][\d০-৯,\.]*\s*(?:কোটি|লাখ|লক্ষ|হাজার|lakh|lac|crore|thousand)?(?:\s*[\d০-৯]+\s*(?:হাজার|thousand))?)", text, re.IGNORECASE)
        if m:
            return to_amount(m.group(1))
    return None


def _rule_extract(text: str, matter_type: str) -> Tuple[Dict[str, Any], Dict[str, str]]:
    """Conservative pattern-based extraction used when no language model is configured."""
    facts: Dict[str, Any] = {}
    evidence: Dict[str, str] = {}
    t = normalize_bangla(text)
    nt = normalize_digits(t)

    def put(key, value, ev):
        if value not in (None, "") and key not in facts:
            facts[key] = value
            evidence[key] = ev.strip()[:120]

    rent = _amount_after(t, ["মাসিক ভাড়া", "ভাড়া", "rent"])
    if rent and rent >= 500:
        put("monthly_rent_bdt", rent, f"ভাড়া … {rent}")
    dep = _amount_after(t, ["জামানত", "অগ্রিম", "advance", "security deposit", "deposit"])
    if dep:
        put("security_deposit_bdt", dep, f"অগ্রিম … {dep}")
    m = re.search(r"(\d+)\s*(বছর|বৎসর|year)", nt, re.IGNORECASE)
    if m:
        put("duration_months", int(m.group(1)) * 12, m.group(0))
    else:
        m = re.search(r"(\d+)\s*(মাসের জন্য|মাস মেয়াদ|months?)", nt, re.IGNORECASE)
        if m:
            put("duration_months", int(m.group(1)), m.group(0))

    party_patterns = {
        "landlord_name": [rf"(?:মালিক|বাড়িওয়ালা|landlord|owner)\s*(?:হলেন|হলো|হচ্ছেন|is|:)?\s*(?:জনাব\s*)?{_NAME}"],
        "tenant_name": [rf"(?:ভাড়াটিয়া|tenant)\s*(?:হলেন|হলো|হচ্ছেন|is|:)?\s*(?:জনাব\s*)?{_NAME}"],
        "employer_name": [rf"(?:কোম্পানি|প্রতিষ্ঠান|employer)\s*(?:হলো|is|:)?\s*{_NAME}"],
        "employee_name": [rf"(?:কর্মচারী|employee)\s*(?:হলেন|হলো|is|:)?\s*{_NAME}"],
        "drawer_name": [rf"{_NAME}\s*(?:আমাকে|আমার কাছে)?\s*(?:একটি|একটা)?\s*চেক\s*(?:দিয়েছেন|দিয়েছে|দেয়)"],
        "seller_name": [rf"(?:বিক্রেতা|seller)\s*(?:হলেন|হলো|is|:)?\s*{_NAME}"],
        "buyer_name": [rf"(?:ক্রেতা|buyer)\s*(?:হলেন|হলো|is|:)?\s*{_NAME}"],
        "lender_name": [rf"(?:ঋণদাতা|lender)\s*(?:হলেন|হলো|is|:)?\s*{_NAME}"],
        "borrower_name": [rf"(?:ঋণগ্রহীতা|borrower)\s*(?:হলেন|হলো|is|:)?\s*{_NAME}"],
    }
    allowed = {r["field"] for r in requirements_for(matter_type)}
    for key, pats in party_patterns.items():
        if key not in allowed:
            continue
        for pat in pats:
            mm = re.search(normalize_bangla(pat), t, re.IGNORECASE)
            if mm:
                name = _clean_name(mm.group(1))
                if name:
                    put(key, name, mm.group(0))
                    break

    if "cheque_no" in allowed:
        mm = re.search(r"(?:চেক\s*(?:নং|নম্বর)|cheque\s*no\.?)\s*[:\-]?\s*([A-Za-z0-9\-]+)", nt, re.IGNORECASE)
        if mm:
            put("cheque_no", mm.group(1), mm.group(0))
        amt = _amount_after(t, ["চেকের", "চেক", "cheque"])
        if amt and amt >= 100:
            put("cheque_amount_bdt", amt, f"চেক … {amt}")
        for bank in ["সোনালী", "জনতা", "অগ্রণী", "রূপালী", "ডাচ-বাংলা", "ব্র্যাক", "সিটি", "ইসলামী", "ইস্টার্ন", "পূবালী", "উত্তরা", "প্রাইম", "ঢাকা ব্যাংক",
                     "Sonali", "Janata", "Agrani", "Dutch-Bangla", "BRAC", "City Bank", "Islami", "Eastern", "Pubali", "Prime"]:
            mm = re.search(rf"({re.escape(bank)}[^,।\n]{{0,40}})", t, re.IGNORECASE)
            if mm:
                put("bank_name", mm.group(1).strip(), mm.group(0))
                break
        for kw, key in (("insufficient", "dishonour_reason"), ("পর্যাপ্ত টাকা নেই", "dishonour_reason"), ("টাকা না থাকায়", "dishonour_reason")):
            if kw in t.lower():
                put(key, "Insufficient Fund", kw)
    if "total_price_bdt" in allowed:
        put("total_price_bdt", _amount_after(t, ["মোট মূল্য", "দাম", "মূল্য", "price"]), "মূল্য")
        put("earnest_money_bdt", _amount_after(t, ["বায়না", "earnest"]), "বায়না")
    if "loan_amount_bdt" in allowed:
        put("loan_amount_bdt", _amount_after(t, ["ঋণ", "ধার", "হাওলাত", "loan"]), "ঋণ")
    if "monthly_salary_bdt" in allowed:
        put("monthly_salary_bdt", _amount_after(t, ["বেতন", "salary"]), "বেতন")

    # A full address only if the client actually gave one (holding/road/shop no.); an area name alone is just a hint
    if "premises_address" in allowed:
        # Only the address parts themselves: "দোকান নং ১২, রোড নং ৩" (+ area name if mentioned)
        label = r"(?:দোকান|ফ্ল্যাট|বাড়ি|বাসা|হোল্ডিং|রোড|ব্লক|সেক্টর|লেন|shop|flat|house|holding|road|block|sector|lane)"
        part = rf"{label}\s*(?:নং|নম্বর|no\.?|#)?\s*[:\-]?\s*[0-9০-৯][0-9০-৯A-Za-z/\-]*"
        parts = [normalize_bangla(p.group(0)).strip() for p in re.finditer(normalize_bangla(part), t, re.IGNORECASE)]
        area_found = None
        for area in ["মিরপুর", "গুলশান", "বনানী", "ধানমন্ডি", "উত্তরা", "মতিঝিল", "তেজগাঁও", "মোহাম্মদপুর", "বাড্ডা", "যাত্রাবাড়ী",
                     "Mirpur", "Gulshan", "Banani", "Dhanmondi", "Uttara", "Motijheel"]:
            mm = re.search(normalize_bangla(area) + r"[\s\-]*[0-9০-৯]*", t)
            if mm:
                area_found = mm.group(0).strip()
                break
        if parts:
            address = ", ".join(dict.fromkeys(parts)) + (f", {area_found}" if area_found else "")
            put("premises_address", address, "; ".join(parts))
        elif area_found:
            evidence["_area_hint"] = area_found
    for d in ["ঢাকা", "চট্টগ্রাম", "সিলেট", "রাজশাহী", "খুলনা", "বরিশাল", "রংপুর", "ময়মনসিংহ", "গাজীপুর", "নারায়ণগঞ্জ", "কুমিল্লা"]:
        if normalize_bangla(d) in t:
            put("district", d, d)
            break

    # Fields the intake extractor already understands (keeps behaviour consistent with the chat)
    try:
        chat = ai_service.extract_structured_facts(text, {})
        for k in ("landlord_name", "tenant_name", "employer_name", "employee_name"):
            if k in allowed and chat.get(k) and k not in facts:
                name = _clean_name(str(chat[k]))
                if name:
                    put(k, name, str(chat[k]))
    except Exception:
        pass
    return {k: v for k, v in facts.items() if k in allowed or k == "district"}, evidence


class ScenarioAnalysisService:
    infer_matter_type = staticmethod(infer_matter_type)

    @classmethod
    def analyze_scenario(cls, scenario_text: str, requested_matter_type: Optional[str] = None) -> Dict[str, Any]:
        text = (scenario_text or "").strip()
        llm = _llm_extract(text, requested_matter_type)
        if llm:
            matter_type = requested_matter_type or llm.get("matter_type") or infer_matter_type(text)
            if matter_type not in MATTER_TITLES:
                matter_type = infer_matter_type(text)
            allowed = {r["field"] for r in requirements_for(matter_type)}
            facts = {k: v for k, v in (llm.get("facts") or {}).items() if k in allowed and not is_blank(v)}
            for k, v in list(facts.items()):
                if k.endswith("_bdt"):
                    amt = to_amount(v)
                    if amt is None:
                        facts.pop(k)
                    else:
                        facts[k] = amt
            evidence = {k: v for k, v in (llm.get("evidence") or {}).items() if k in facts}
            unclear = [u for u in (llm.get("unclear") or []) if isinstance(u, str)]
            method = "language_model"
        else:
            matter_type = requested_matter_type or infer_matter_type(text)
            facts, evidence = _rule_extract(text, matter_type)
            unclear = []
            hint = evidence.pop("_area_hint", None)
            if hint:
                unclear.append(f"এলাকা '{hint}' উল্লেখ আছে, কিন্তু পূর্ণ ঠিকানা (হোল্ডিং/দোকান নং, রোড) দেওয়া হয়নি।")
            method = "rules"

        return cls.build_result(matter_type, facts, evidence, unclear, method)

    @staticmethod
    def build_result(matter_type: str, facts: Dict[str, Any], evidence: Optional[Dict[str, str]] = None,
                     unclear: Optional[List[str]] = None, method: str = "manual") -> Dict[str, Any]:
        reqs = requirements_for(matter_type)
        missing = missing_requirements(matter_type, facts)
        questions = [m for m in missing if m["kind"] == "fact"]
        terms = [m for m in missing if m["kind"] == "term"]
        critical_missing = [q for q in questions if q.get("critical")]
        fact_reqs = [r for r in reqs if r["kind"] == "fact"]
        answered = len(fact_reqs) - len(questions)
        completeness = int(round(100 * answered / len(fact_reqs))) if fact_reqs else 100
        title_bn, title_en = MATTER_TITLES.get(matter_type, MATTER_TITLES["custom"])

        suggested = {t["field"]: t["suggestion"] for t in terms if t.get("suggestion") is not None}
        notes = [
            f"'{title_bn}'-এর জন্য বইয়ের নির্দেশনা অনুযায়ী {len(fact_reqs)}টি তথ্য প্রয়োজন; আপনার বর্ণনা থেকে {answered}টি পাওয়া গেছে।",
            (f"খসড়া তৈরির আগে {len(critical_missing)}টি অত্যাবশ্যক তথ্য জানা দরকার — নিচের প্রশ্নগুলোর উত্তর দিন।"
             if critical_missing else "সব অত্যাবশ্যক তথ্য পাওয়া গেছে — খসড়া তৈরি করা যাবে। বাকি প্রশ্নের উত্তর দিলে খসড়া আরও পূর্ণাঙ্গ হবে।"),
            "কোনো তথ্য অনুমান করে বসানো হয়নি। যে তথ্য জানা নেই, খসড়ায় তা '……' ফাঁকা থাকবে।",
        ]
        if method == "rules":
            notes.append("উন্নত বোঝার জন্য (যেকোনো ভাষা/কথ্যরীতি) GEMINI_API_KEY সেট করুন — এখন নিয়মভিত্তিক বিশ্লেষণ চলছে, তাই কিছু তথ্য ধরা নাও পড়তে পারে।")

        def item(m):
            return {"field": m["field"], "label_bn": m["label_bn"], "question_bn": m["question_bn"], "why_bn": m["why_bn"],
                    "kind": m["kind"], "critical": m.get("critical", False), "suggestion": m.get("suggestion")}

        return {
            "matter_type": matter_type,
            "template_code": MATTER_TO_TEMPLATE.get(matter_type, "BD_CUSTOM_AGREEMENT"),
            "matter_title_bn": title_bn,
            "matter_title_en": title_en,
            "extracted_facts": facts,
            "evidence": evidence or {},
            "unclear": unclear or [],
            "questions": [item(q) for q in questions],
            "suggested_terms": [item(t) for t in terms],
            "missing_items": [item(m) for m in missing],
            "completeness_percentage": completeness,
            "is_ready_for_drafting": not critical_missing,
            "autofilled_facts": {**suggested, **facts},
            "senior_counsel_notes_bn": notes,
            "extraction_method": method,
            "field_labels": {r["field"]: r["label_bn"] for r in reqs},
        }

    @staticmethod
    def autofill_facts(current_facts: Dict[str, Any], matter_type: str) -> Dict[str, Any]:
        """Adds the book's standard TERMS only (notice period, rent due day ...). Facts are never filled in."""
        filled = dict(current_facts)
        for r in requirements_for(matter_type):
            if r["kind"] == "term" and r.get("suggestion") is not None and is_blank(filled.get(r["field"])):
                filled[r["field"]] = r["suggestion"]
        return filled


scenario_analysis_service = ScenarioAnalysisService()
