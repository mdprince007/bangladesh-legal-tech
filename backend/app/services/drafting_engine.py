"""
Drafting engine for Bangladesh legal documents, following the formats and checklists of
Dr. Syeda Nasrin, "Basics of Legal Drafting" (2nd Ed.):

  - Agreements (Ch. 2, p.45-46 checklist; Tenancy sample p.46-48; Share Transfer p.49-52;
    Deed of Partnership p.67-70; MOU p.71-73): dated title line, BETWEEN ... AND party blocks with
    parentage, present/permanent address, NID and the "heirs, successors ... assigns" expression,
    WHEREAS recitals, "NOW THIS AGREEMENT WITNESSETH", numbered "That ..." clauses, schedule,
    IN WITNESS WHEREOF, signatures, witnesses with parentage/address, pages, stamp, thumb impression.
  - Legal notice (Ch. 4, p.120-121 particulars; Sec. 138 sample p.134-136): LEGAL NOTICE
    (Registered with A/D), reference, date, To ... Notice Receivers, From (Advocate),
    For and on behalf of ... Notice Giver, Subject, numbered facts, demand with time limit,
    consequence, copy kept in chamber, signature.

Facts are never invented. Anything the client has not supplied is left as a "……………" blank
(the book's own convention) and listed in `missing` so the user can be asked for it.
"""
import re
from typing import Any, Dict, List, Optional, Tuple

from app.schemas.document import ClauseSelectionItem
from app.services.bangla_text import normalize_digits, parse_bangla_number_words
from app.services.matter_requirements import (
    TEMPLATE_TO_MATTER, is_blank, looks_like_company, missing_requirements, requirements_for,
)

BLANK = "……………………"

# ---------------------------------------------------------------------------
# Numbers and money in the book's style: "Tk. 2,50,000/- (Taka Two Lac Fifty Thousand) only"
# ---------------------------------------------------------------------------
_ONES = ["", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine", "Ten", "Eleven", "Twelve",
         "Thirteen", "Fourteen", "Fifteen", "Sixteen", "Seventeen", "Eighteen", "Nineteen"]
_TENS = ["", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"]


def _below_hundred(n: int) -> str:
    if n < 20:
        return _ONES[n]
    return _TENS[n // 10] + ("-" + _ONES[n % 10] if n % 10 else "")


def words_en(n: int) -> str:
    """Indian numbering in words (Crore, Lac, Thousand, Hundred) as used in Bangladeshi deeds."""
    if n == 0:
        return "Zero"
    parts = []
    for value, name in ((10_000_000, "Crore"), (100_000, "Lac"), (1_000, "Thousand"), (100, "Hundred")):
        if n >= value:
            q = n // value
            parts.append(f"{words_en(q) if q >= 100 else _below_hundred(q)} {name}")
            n %= value
    if n:
        parts.append(_below_hundred(n))
    return " ".join(parts)


def indian_commas(n: int) -> str:
    s = str(int(n))
    if len(s) <= 3:
        return s
    head, tail = s[:-3], s[-3:]
    groups = []
    while len(head) > 2:
        groups.insert(0, head[-2:])
        head = head[:-2]
    if head:
        groups.insert(0, head)
    return ",".join(groups + [tail])


def to_amount(value: Any) -> Optional[int]:
    """Understands 50000, '50,000', '৫০,০০০', '২ লাখ', '1.5 crore', 'আটচল্লিশ হাজার'."""
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return int(round(value))
    s = normalize_digits(str(value)).lower().replace(",", "")
    mults = {"কোটি": 10_000_000, "crore": 10_000_000, "লাখ": 100_000, "লক্ষ": 100_000, "lakh": 100_000,
             "lac": 100_000, "হাজার": 1_000, "thousand": 1_000}
    pairs = re.findall(r"(\d+(?:\.\d+)?)\s*(কোটি|crore|লাখ|লক্ষ|lakh|lac|হাজার|thousand)?", s)
    if pairs:
        if any(unit for _, unit in pairs):
            # compound amounts such as '২ লাখ ৫০ হাজার' = 2,50,000: add every number that carries a unit
            return int(round(sum(float(num) * mults[unit] for num, unit in pairs if unit)))
        return int(round(float(pairs[0][0])))
    w = parse_bangla_number_words(s)
    return int(round(w)) if w is not None else None


def to_int(value: Any) -> Optional[int]:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return int(value)
    m = re.search(r"\d+", normalize_digits(str(value)))
    return int(m.group(0)) if m else None


def number_with_words(n: Optional[int], unit: str) -> str:
    """'3 (Three) years' / '30 (Thirty) days'."""
    if n is None:
        return f"{BLANK} {unit}"
    return f"{n} ({words_en(n)}) {unit}"


def period_from_months(months: Optional[int]) -> str:
    if months is None:
        return f"{BLANK} months"
    if months % 12 == 0:
        years = months // 12
        return number_with_words(years, "year" if years == 1 else "years")
    return number_with_words(months, "month" if months == 1 else "months")


def _relation(given: Any, name: str) -> Optional[str]:
    """son / daughter / wife — from an explicit fact, else from a clear honorific in the name."""
    g = str(given or "").strip().lower()
    if g in ("son", "পুত্র", "ছেলে"):
        return "son"
    if g in ("daughter", "কন্যা", "মেয়ে"):
        return "daughter"
    if g in ("wife", "স্ত্রী"):
        return "wife"
    n = f" {str(name or '').lower()} "
    male = re.search(r"\s(md\.?|mohammad|muhammad|mohammed|mr\.?)\s", n) or any(t in n for t in ("মোঃ", "মোহাম্মদ", "জনাব"))
    female = (re.search(r"\s(mst\.?|mosammat|mrs\.?|ms\.?|miss)\s", n)
              or re.search(r"\s(begum|khatun|akter|akhter|nesa|nessa)\s", n)
              or any(t in n for t in ("মোছাঃ", "মোসাম্মৎ", "বেগম", "খাতুন", "আক্তার")))
    if male and not female:
        return "son"
    if female and not male:
        return "daughter"
    return None


def ordinal(n: Optional[int]) -> str:
    if n is None:
        return BLANK
    suffix = "th" if 10 <= n % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


class Draft:
    """Collects the document and records every blank so nothing is silently invented."""

    def __init__(self, facts: Dict[str, Any], style: str):
        self.facts = facts or {}
        self.style = style
        self.missing: Dict[str, str] = {}
        self.warnings: List[str] = []
        self.clauses: List[ClauseSelectionItem] = []

    def get(self, key: str, label: Optional[str] = None, fallback_keys: Tuple[str, ...] = ()) -> str:
        for k in (key, *fallback_keys):
            v = self.facts.get(k)
            if not is_blank(v):
                return str(v).strip()
        self.missing[key] = label or key
        return BLANK

    def has(self, key: str) -> bool:
        return not is_blank(self.facts.get(key))

    def taka(self, key: str, label: Optional[str] = None) -> str:
        amount = to_amount(self.facts.get(key))
        if amount is None:
            self.missing[key] = label or key
            return f"Tk. {BLANK}/- (Taka {BLANK}) only"
        return f"Tk. {indian_commas(amount)}/- (Taka {words_en(amount)}) only"

    def clause(self, code: str, clause_type: str, title: str, text: str, explanation_bn: str,
               basis: Optional[str] = None, book_ref: Optional[str] = None, risk: str = "low"):
        self.clauses.append(ClauseSelectionItem(
            code=code, clause_type=clause_type, title=title, text_content=text,
            explanation_bangla=explanation_bn, risk_level=risk, style=self.style,
            statutory_basis=basis, book_reference=book_ref,
        ))

    # --- building blocks ---------------------------------------------------
    def party_block(self, prefix: str, name_key: str, role: str, side: str) -> str:
        name = self.get(name_key, f"{role} name")
        if looks_like_company(name):
            rep = self.get(f"{prefix}_representative", f"{role} authorised representative")
            addr = self.get(f"{prefix}_address", f"{role} registered office")
            return (
                f"{name}, a company incorporated under the laws of Bangladesh, having its registered office at "
                f"{addr}, represented by {rep}, duly authorised by a Resolution of its Board of Directors dated "
                f"{self.facts.get(prefix + '_board_resolution_date') or BLANK}, hereinafter referred to as the {role} "
                f"(which expression shall, unless repugnant to the context, mean and include its successors-in-interest, "
                f"legal representatives, administrators and assigns) of the {side} PART."
            )
        father = self.get(f"{prefix}_father", f"{role} father's/husband's name")
        mother = self.facts.get(f"{prefix}_mother")
        present = self.get(f"{prefix}_address", f"{role} present address")
        permanent = self.facts.get(f"{prefix}_permanent_address")
        if is_blank(permanent) or str(permanent).strip() in ("একই", "same", "Same"):
            permanent_txt = "same as present address" if not is_blank(permanent) else BLANK
        else:
            permanent_txt = str(permanent)
        nid = self.facts.get(f"{prefix}_nid") or BLANK
        dob = self.facts.get(f"{prefix}_dob") or BLANK
        relation = _relation(self.facts.get(f"{prefix}_relation"), name)
        if relation is None:
            relation = "son/daughter/wife"
            self.missing[f"{prefix}_relation"] = f"{role}: son / daughter / wife of the named parent"
        parent_txt = f"{relation} of {father}" + (f" and {mother}" if not is_blank(mother) and relation != "wife" else "")
        return (
            f"{name}, {parent_txt}, present address: {present}, permanent address: {permanent_txt}, "
            f"date of birth: {dob}, by nationality Bangladeshi, National ID No. {nid}, hereinafter referred to as the "
            f"{role} (which expression shall, unless repugnant to the context, mean and include his/her heirs, "
            f"successors, legal representatives, executors, administrators and assigns) of the {side} PART."
        )

    def witness_block(self) -> str:
        w1 = self.facts.get("witness_one") or "Name: ………………  Son/daughter of: ………………  Address: ………………  NID: ………………"
        w2 = self.facts.get("witness_two") or "Name: ………………  Son/daughter of: ………………  Address: ………………  NID: ………………"
        return f"1. {w1}\n   Signature: ____________________\n\n2. {w2}\n   Signature: ____________________"

    def execution_line(self, title: str) -> str:
        date = self.get("execution_date", "execution date")
        place = self.facts.get("execution_place") or self.facts.get("district") or BLANK
        return f"This {title} is made and executed on this the {date} of the Christian Era at {place}."

    def render_clauses(self) -> str:
        out = []
        for i, c in enumerate(self.clauses, start=1):
            body = c.text_content.strip()
            out.append(f"{i}. {c.title}\n{body}")
        return "\n\n".join(out)

    # Book p.45: closing clauses every agreement needs
    def common_closing_clauses(self, doc_name: str, pages_hint: str = BLANK):
        forum = self.facts.get("dispute_forum")
        if forum:
            dispute = f"That any dispute or difference arising out of or in connection with this {doc_name} shall be resolved as follows: {forum}."
        else:
            dispute = (
                f"That any dispute or difference arising out of or in connection with this {doc_name} shall first be "
                f"attempted to be settled amicably. If not so settled, either party shall serve 30 (Thirty) days' notice "
                f"in writing upon the other for amicable settlement, failing which the dispute shall be referred to "
                f"arbitration under the Arbitration Act, 2001, or to the Court of competent jurisdiction in Bangladesh."
            )
        self.clause("GEN_GOVERNING_LAW_DISPUTE", "dispute", "GOVERNING LAW AND DISPUTE SETTLEMENT",
                    f"That this {doc_name} and the interpretation of its terms shall be governed by and construed in accordance with the laws of Bangladesh.\n{dispute}",
                    "বাংলাদেশের আইন প্রযোজ্য; প্রথমে আলোচনা, এরপর ৩০ দিনের নোটিশ, তারপর সালিশ বা আদালত। বইয়ের শেয়ার হস্তান্তর নমুনার ধারা ১২ অনুসরণ করা হয়েছে (পৃ. ৫১)।",
                    "The Arbitration Act, 2001; The Contract Act, 1872", "অধ্যায় ২, পৃ. ৪৫ ও ৫১")
        self.clause("GEN_AMENDMENT_WAIVER", "general", "AMENDMENT, WAIVER AND ENTIRE AGREEMENT",
                    f"That the terms and conditions of this {doc_name} shall not be amended or altered except by mutual agreement in writing signed by both parties. "
                    f"No failure or delay by either party in exercising any right hereunder shall operate as a waiver thereof. "
                    f"This {doc_name} constitutes the entire understanding of the parties and supersedes all previous discussions and writings on the subject matter.",
                    "লিখিত সম্মতি ছাড়া কোনো শর্ত পরিবর্তন করা যাবে না; পূর্বের সকল আলোচনা এই চুক্তি দ্বারা প্রতিস্থাপিত।",
                    "The Contract Act, 1872", "অধ্যায় ২, পৃ. ৪৮ (ধারা ১৫) ও পৃ. ৫১ (ধারা ১০)")
        self.clause("GEN_VOLUNTARY_BINDING", "general", "VOLUNTARY EXECUTION AND BINDING EFFECT",
                    f"That this {doc_name} has been executed by the parties voluntarily, in sound health and mind, having understood its contents, "
                    f"without any coercion, undue influence, fraud or misrepresentation, and the same shall be binding upon the parties hereto "
                    f"and their respective heirs, successors-in-interest, legal representatives and permitted assigns.",
                    "চুক্তিটি স্বেচ্ছায়, সুস্থ মস্তিষ্কে, কোনো চাপ বা প্রতারণা ছাড়া সম্পাদিত এবং উত্তরাধিকারীদের উপরও বাধ্যকর।",
                    "The Contract Act, 1872, Sections 10, 14-19", "অধ্যায় ২, পৃ. ৪৫ ও ৫১ (ধারা ১১, ১৩)")
        stamp = self.facts.get("stamp_value_bdt")
        stamp_txt = f"Tk. {indian_commas(to_amount(stamp))}/-" if to_amount(stamp) else f"Tk. {BLANK}/-"
        self.clause("GEN_EXECUTION_COPIES", "general", "COPIES, PAGES AND STAMP",
                    f"That this {doc_name} is composed of {pages_hint} pages, executed in 2 (two) originals on non-judicial stamp paper of {stamp_txt}, "
                    f"each party retaining one original, and each page shall bear the signatures and thumb impressions of the parties.",
                    "চুক্তির পৃষ্ঠা সংখ্যা, মূল কপির সংখ্যা ও স্ট্যাম্পের মূল্য উল্লেখ থাকতে হবে এবং প্রতি পৃষ্ঠায় স্বাক্ষর ও টিপসই দিতে হবে (বই পৃ. ৪৫-৪৬)।",
                    "The Stamp Act, 1899", "অধ্যায় ২, পৃ. ৪৫-৪৬ ও ৪৮ (ধারা ১৬)")

    def agreement(self, title: str, first_role: str, second_role: str, first_party: str, second_party: str,
                  recitals: List[str], schedule: Optional[str] = None, doc_name: str = "Agreement",
                  first_sign: Optional[str] = None, second_sign: Optional[str] = None) -> str:
        rec = ";\n\n".join(("WHEREAS, " if i == 0 else "AND WHEREAS, ") + r.rstrip(";. ") for i, r in enumerate(recitals)) + ";"
        parts = [
            title.upper(),
            "",
            self.execution_line(doc_name),
            "",
            "BETWEEN",
            "",
            first_party,
            f"……..{first_role}",
            "",
            "AND",
            "",
            second_party,
            f"……..{second_role}",
            "",
            rec,
            "",
            f"NOW THIS {doc_name.upper()} WITNESSETH AND IT IS HEREBY AGREED AND DECLARED BY AND BETWEEN THE PARTIES HERETO AS FOLLOWS:",
            "",
            self.render_clauses(),
        ]
        if schedule:
            parts += ["", schedule]
        parts += [
            "",
            f"IN WITNESS WHEREOF, the parties hereto have set and subscribed their respective hands and seals on this {doc_name} "
            f"with their free will and consent on the day, month and year first above written, in the presence of the following witnesses.",
            "",
            f"Signature of the {first_sign or first_role}: ____________________",
            "",
            f"Signature of the {second_sign or second_role}: ____________________",
            "",
            "WITNESSES:",
            self.witness_block(),
            "",
            f"Drafted and prepared by: {self.facts.get('drafted_by') or BLANK}, Advocate",
            "",
            "(Please put signature and thumb impression of the parties on each page.)",
        ]
        return "\n".join(parts)


def _lease_schedule(d: Draft, heading: str) -> str:
    premises = d.get("premises_address", "premises address")
    area = d.facts.get("floor_area_sft")
    floor = d.facts.get("floor") or d.facts.get("shop_or_unit_no")
    bounds = d.facts.get("boundaries_schedule") or d.facts.get("boundaries")
    lines = [heading, ""]
    lines.append(
        f"All that premises measuring more or less {area or BLANK} square feet"
        f"{' on the ' + str(floor) if floor else ''} situated at {premises}"
        f"{', District- ' + str(d.facts['district']) if d.has('district') else ''}, together with the right to use common passages, "
        f"stairs and lift (if any), but excluding the main structure and roof which shall remain with the Lessor."
    )
    if bounds:
        lines.append(f"Being butted and bounded: {bounds}")
    return "\n".join(lines)


class DraftingEngine:
    # ------------------------------------------------------------------ leases
    @staticmethod
    def assemble_commercial_lease(facts: Dict[str, Any], style: str = "balanced", language: str = "en"):
        d = Draft(facts, style)
        months = to_int(facts.get("duration_months"))
        notice_m = to_int(facts.get("notice_period_months"))
        due_day = to_int(facts.get("rent_due_day_of_month"))
        esc = to_int(facts.get("rent_escalation_pct"))
        commence = d.get("commencement_date", "commencement date")
        business = d.get("permitted_business_type", "permitted business")

        d.clause("LEASE_DEMISE_TERM", "term", "TERM AND POSSESSION",
                 f"That this Agreement is made and executed for a period of {period_from_months(months)} commencing on {commence}, "
                 f"on which date the Lessor shall hand over vacant and peaceful possession of the Schedule Premises to the Tenant. "
                 f"The tenancy may be renewed only by mutual agreement in writing executed at least 60 (Sixty) days before expiry of the term.",
                 "চুক্তির মেয়াদ, শুরুর তারিখ ও দখল হস্তান্তর। নবায়ন শুধু উভয় পক্ষের লিখিত সম্মতিতে (বইয়ের ভাড়াচুক্তি নমুনা, ধারা ১)।",
                 "The Transfer of Property Act, 1882, Sections 105 & 107", "অধ্যায় ২, পৃ. ৪৭ (ধারা ১)")
        deposit_adjust = str(facts.get("deposit_adjustable") or "").lower() in ("yes", "true", "হ্যাঁ", "adjustable", "সমন্বয়যোগ্য")
        d.clause("LEASE_SECURITY_DEPOSIT", "deposit", "ADVANCE / SECURITY DEPOSIT",
                 f"That the Tenant shall pay to the Lessor a sum of {d.taka('security_deposit_bdt', 'security deposit')} as advance on the day of execution of this Agreement, "
                 f"against which the Lessor shall issue a written acknowledgement receipt. "
                 + ("The said advance shall be adjusted against the monthly rent in equal instalments as agreed between the parties."
                    if deposit_adjust else
                    "The said advance shall not bear any interest, shall not be deducted for any purpose during the term, and shall be refunded to the Tenant "
                    "within 30 (Thirty) days of expiry or earlier termination of this Agreement upon delivery of vacant possession, after deducting only "
                    "lawful unpaid rent and utility bills, if any."),
                 "অগ্রিমের পরিমাণ, প্রাপ্তি রসিদ এবং মেয়াদ শেষে ফেরতের শর্ত (বই পৃ. ৪৭, ধারা ২ ও ৮)।",
                 "The Contract Act, 1872, Section 73", "অধ্যায় ২, পৃ. ৪৭ (ধারা ২, ৮)")
        d.clause("LEASE_RENT_PAYMENT", "rent", "MONTHLY RENT",
                 f"That the Tenant shall pay to the Lessor a monthly rent of {d.taka('monthly_rent_bdt', 'monthly rent')} for the Schedule Premises, "
                 f"payable for the current month between the 1st day and the {ordinal(due_day)} day of each English calendar month, by cheque, bank transfer "
                 f"or against a signed money receipt of the Lessor. The said amount is the basic rent exclusive of all charges, bills and other expenses.",
                 "মাসিক ভাড়া, পরিশোধের সময়সীমা ও রসিদ। ভাড়া মূল ভাড়া; বিল আলাদা (বই পৃ. ৪৭, ধারা ৩)।",
                 "The Contract Act, 1872, Section 10", "অধ্যায় ২, পৃ. ৪৭ (ধারা ৩)")
        d.clause("LEASE_UTILITIES_OUTGOINGS", "utilities", "UTILITIES AND SERVICE CHARGES",
                 "That the Tenant shall pay all charges and bills for electricity, gas, water, service charge, and any other utility consumed in the Schedule Premises "
                 "during the tenancy directly to the concerned authorities, and shall hand over the clearance receipts to the Lessor at the time of vacating. "
                 "Municipal holding tax and land development tax shall be borne by the Lessor.",
                 "বিদ্যুৎ, গ্যাস, পানি ও সার্ভিস চার্জ ভাড়াটিয়া দেবেন; হোল্ডিং ট্যাক্স মালিক দেবেন।",
                 None, "অধ্যায় ২, পৃ. ৪৭ (ধারা ৩)")
        if esc is not None and esc > 0:
            d.clause("LEASE_RENT_ESCALATION", "rent", "ANNUAL INCREMENT OF RENT",
                     f"That the monthly rent shall be increased at the rate of {esc}% ({words_en(esc)} percent) upon completion of every 12 (Twelve) months of the tenancy.",
                     f"প্রতি বছর ভাড়া {esc}% হারে বৃদ্ধি পাবে (বই পৃ. ৪৭, ধারা ৪)।", None, "অধ্যায় ২, পৃ. ৪৭ (ধারা ৪)")
        elif esc is None:
            d.missing["rent_escalation_pct"] = "annual rent increment (%)"
        d.clause("LEASE_PERMITTED_USE", "use", "PERMITTED USE",
                 f"That the Tenant shall use the Schedule Premises only for the purpose of {business} and for no other purpose. "
                 f"Use of the Schedule Premises for any other purpose shall be treated as a breach of this Agreement.",
                 "শুধু অনুমোদিত ব্যবসার জন্য ব্যবহার; অন্য কাজে ব্যবহার চুক্তিভঙ্গ (বই পৃ. ৪৭, ধারা ৭)।",
                 "The Transfer of Property Act, 1882, Section 108", "অধ্যায় ২, পৃ. ৪৭ (ধারা ৭)")
        late_pct = to_int(facts.get("late_payment_interest_pct"))
        d.clause("LEASE_LATE_PAYMENT", "default", "DEFAULT IN PAYMENT OF RENT",
                 "That if the Tenant fails to pay the rent within the stipulated time for 3 (Three) consecutive months, the Lessor shall be at liberty "
                 + (f"to charge interest at the rate of {late_pct}% on each month's unpaid rent, and " if late_pct else "")
                 + "to terminate this Agreement by serving notice in writing and to recover the arrears in accordance with law.",
                 "টানা ৩ মাস ভাড়া বকেয়া থাকলে মালিক চুক্তি বাতিল ও বকেয়া আদায় করতে পারবেন (বই পৃ. ৪৭, ধারা ৯)।",
                 "The Transfer of Property Act, 1882, Section 111", "অধ্যায় ২, পৃ. ৪৭ (ধারা ৯)", risk="medium")
        d.clause("LEASE_ALTERATIONS", "maintenance", "INTERIOR DECORATION AND REPAIRS",
                 "That the Tenant shall be at liberty to carry out interior decoration of the Schedule Premises at its own cost without causing any harm or crack to "
                 "the main structure. Any damage to the main structure caused by the Tenant shall be repaired at the cost of the Tenant. "
                 "Major and structural repairs not caused by the Tenant shall be carried out by the Lessor.",
                 "মূল কাঠামোর ক্ষতি না করে ভেতরের সাজসজ্জা করা যাবে; কাঠামোর ক্ষতি হলে ভাড়াটিয়া মেরামত করবেন (বই পৃ. ৪৮, ধারা ১০)।",
                 "The Transfer of Property Act, 1882, Section 108", "অধ্যায় ২, পৃ. ৪৮ (ধারা ১০)")
        d.clause("LEASE_SUBLETTING", "restriction", "NO SUB-LETTING AND LAWFUL USE",
                 "That the Tenant shall not sub-let, assign or part with possession of the Schedule Premises or any part thereof, and shall not use it for any illegal, "
                 "immoral or prohibited purpose; the Tenant shall be solely responsible for any such activity.",
                 "সাবলেট নিষিদ্ধ এবং বেআইনি কাজে ব্যবহার করা যাবে না (বই পৃ. ৪৮, ধারা ১১)।",
                 "The Transfer of Property Act, 1882, Section 108(j)", "অধ্যায় ২, পৃ. ৪৮ (ধারা ১১)")
        d.clause("LEASE_CARE_INSPECTION", "maintenance", "CARE AND INSPECTION",
                 "That the Tenant shall use the Schedule Premises with good care and caution, and the Lessor shall have the right to inspect the Schedule Premises "
                 "from time to time at a reasonable hour in the presence of the Tenant after giving prior intimation.",
                 "ভাড়াটিয়া যত্নসহকারে ব্যবহার করবেন; মালিক আগাম জানিয়ে পরিদর্শন করতে পারবেন (বই পৃ. ৪৮, ধারা ১২)।",
                 None, "অধ্যায় ২, পৃ. ৪৮ (ধারা ১২)")
        notice_days = notice_m * 30 if notice_m else None
        d.clause("LEASE_TERMINATION_NOTICE", "termination", "TERMINATION AND HANDOVER",
                 f"That either party may terminate this Agreement by serving {number_with_words(notice_days, 'days')} prior notice in writing upon the other party. "
                 f"If the Tenant breaches any term of this Agreement, the Lessor shall be at liberty to take legal action against the Tenant in accordance with law. "
                 f"Upon expiry or termination, the Tenant shall hand over vacant and peaceful possession of the Schedule Premises in the same condition as received, "
                 f"reasonable wear and tear excepted.",
                 "চুক্তি অবসানে লিখিত নোটিশ, চুক্তিভঙ্গে আইনি ব্যবস্থা এবং মেয়াদ শেষে খালি দখল হস্তান্তর (বই পৃ. ৪৮, ধারা ১৩-১৪)।",
                 "The Transfer of Property Act, 1882, Sections 106 & 111", "অধ্যায় ২, পৃ. ৪৮ (ধারা ১৩, ১৪)")
        if notice_m is None:
            d.missing["notice_period_months"] = "termination notice period"
        borne = str(facts.get("stamp_duty_borne_by") or "").lower()
        borne_txt = {"tenant": "the Tenant", "landlord": "the Lessor", "lessor": "the Lessor", "equal": "both parties equally",
                     "both": "both parties equally"}.get(borne, BLANK)
        if months and months > 12:
            reg = (f"That since the term of this lease exceeds one year, this Agreement shall be executed on non-judicial stamp paper of the prescribed value "
                   f"and registered with the concerned Sub-Registry Office as required by Section 107 of the Transfer of Property Act, 1882 and Section 17 of the "
                   f"Registration Act, 1908. The stamp duty and registration costs shall be borne by {borne_txt}.")
            risk = "high"
        else:
            reg = (f"That this Agreement shall be executed on non-judicial stamp paper of the prescribed value under the Stamp Act, 1899, and the stamp costs "
                   f"shall be borne by {borne_txt}.")
            risk = "low"
        d.clause("LEASE_REGISTRATION_STAMP", "compliance", "STAMP AND REGISTRATION", reg,
                 "১ বছরের বেশি মেয়াদের লিজ রেজিস্ট্রি বাধ্যতামূলক; খরচ কে দেবে তা নির্ধারিত (সম্পত্তি হস্তান্তর আইন ধারা ১০৭, রেজিস্ট্রেশন আইন ধারা ১৭)।",
                 "The Registration Act, 1908, Section 17; The Transfer of Property Act, 1882, Section 107; The Stamp Act, 1899", "অধ্যায় ২, পৃ. ৪৫-৪৬",
                 risk=risk)
        if months and months > 12:
            d.warnings.append("মেয়াদ ১ বছরের বেশি — চুক্তিটি সাব-রেজিস্ট্রি অফিসে রেজিস্ট্রি করতে হবে, নইলে আদালতে লিজের প্রমাণ হিসেবে গ্রহণযোগ্য নাও হতে পারে (রেজিস্ট্রেশন আইন ধারা ৪৯)।")
        d.common_closing_clauses("Agreement")
        d.clauses[-4].code = "LEASE_GOVERNING_LAW"  # keep the historical code for the dispute clause

        landlord = d.party_block("landlord", "landlord_name", "FIRST PARTY/LESSOR", "ONE")
        tenant = d.party_block("tenant", "tenant_name", "SECOND PARTY/TENANT", "OTHER")
        recitals = [
            f"the First Party/Lessor is the absolute owner and possessor of the premises more fully described in the Schedule below (hereinafter referred to as the 'Schedule Premises') "
            f"{('having acquired the same by ' + str(facts['landlord_title_source'])) if d.has('landlord_title_source') else ''} and is desirous of letting out the same on monthly rent",
            f"the Second Party/Tenant has approached the First Party to take the Schedule Premises on rent for the purpose of {business}, and the First Party has agreed to let out the same",
            "both the parties have agreed to reduce the terms and conditions of the tenancy into writing",
        ]
        text = d.agreement("COMMERCIAL TENANCY AGREEMENT", "FIRST PARTY/LESSOR", "SECOND PARTY/TENANT", landlord, tenant,
                           [r.replace("  ", " ") for r in recitals], _lease_schedule(d, "SCHEDULE OF THE PREMISES"), "Agreement",
                           "FIRST PARTY/LESSOR", "SECOND PARTY/TENANT")
        return _finish(d, text)

    @staticmethod
    def assemble_residential_lease(facts: Dict[str, Any], style: str = "balanced", language: str = "en"):
        d = Draft(facts, style)
        months = to_int(facts.get("duration_months"))
        notice_m = to_int(facts.get("notice_period_months"))
        due_day = to_int(facts.get("rent_due_day_of_month"))
        commence = d.get("commencement_date", "commencement date")
        rent = to_amount(facts.get("monthly_rent_bdt"))
        advance = to_amount(facts.get("security_deposit_bdt"))

        d.clause("RES_DEMISE_TERM", "term", "TERM AND POSSESSION",
                 f"That the Lessor hereby lets out the Schedule Premises to the Tenant for residential purpose only for a period of {period_from_months(months)} "
                 f"commencing on {commence}, on which date vacant possession shall be handed over to the Tenant.",
                 "শুধু আবাসিক ব্যবহারের জন্য ভাড়া, মেয়াদ ও দখল হস্তান্তরের তারিখ।",
                 "The Transfer of Property Act, 1882, Section 105", "অধ্যায় ২, পৃ. ৪৭ (ধারা ১)")
        d.clause("RES_RENT_RECEIPT", "rent", "MONTHLY RENT AND RENT RECEIPT",
                 f"That the Tenant shall pay a monthly rent of {d.taka('monthly_rent_bdt', 'monthly rent')} for the current month within the {ordinal(due_day)} day "
                 f"of each English calendar month, and the Lessor shall issue a signed rent receipt for every payment as required by Section 13 of the "
                 f"Premises Rent Control Act, 1991.",
                 "প্রতি মাসের নির্দিষ্ট তারিখে ভাড়া এবং প্রতিবার লিখিত রসিদ দেওয়া বাধ্যতামূলক (বাড়িভাড়া নিয়ন্ত্রণ আইন ১৯৯১, ধারা ১৩)।",
                 "The Premises Rent Control Act, 1991, Section 13", "অধ্যায় ২, পৃ. ৪৭ (ধারা ৩)")
        d.clause("RES_SECURITY_ADVANCE", "deposit", "ADVANCE",
                 f"That the Tenant has paid/shall pay an advance of {d.taka('security_deposit_bdt', 'advance')} on execution of this Agreement against a written receipt, "
                 f"which shall be refunded or adjusted at the time of vacating the Schedule Premises after deduction of lawful dues, if any.",
                 "অগ্রিম প্রাপ্তির রসিদ এবং বাসা ছাড়ার সময় ফেরত/সমন্বয়ের শর্ত।",
                 "The Premises Rent Control Act, 1991, Section 10", "অধ্যায় ২, পৃ. ৪৭ (ধারা ২, ৮)",
                 risk="medium" if (rent and advance and advance > rent) else "low")
        if rent and advance and advance > rent:
            d.warnings.append("অগ্রিম এক মাসের ভাড়ার বেশি। বাড়িভাড়া নিয়ন্ত্রণ আইন ১৯৯১-এর ধারা ১০ অগ্রিম/প্রিমিয়াম গ্রহণ সীমিত করে — চুক্তি করার আগে আইনজীবীর সাথে যাচাই করুন।")
        d.clause("RES_UTILITIES_BILLS", "utilities", "UTILITY BILLS AND SERVICE CHARGE",
                 "That the Tenant shall pay the electricity, gas and water bills and service charge of the Schedule Premises during the tenancy, and the Lessor shall pay "
                 "the municipal holding tax.", "বিদ্যুৎ, গ্যাস, পানি ও সার্ভিস চার্জ ভাড়াটিয়া; হোল্ডিং ট্যাক্স মালিক।", None, "অধ্যায় ২, পৃ. ৪৭")
        d.clause("RES_USE_CARE", "restriction", "USE, CARE AND NO SUB-LETTING",
                 "That the Tenant shall use the Schedule Premises for the residence of the Tenant's family only, shall keep it in good and clean condition, shall not "
                 "make any structural alteration, shall not sub-let it, and shall not use it for any illegal or immoral purpose. The Lessor may inspect the premises "
                 "at a reasonable hour after prior intimation.",
                 "শুধু পরিবারের বসবাস, যত্নসহকারে ব্যবহার, কাঠামো পরিবর্তন ও সাবলেট নিষিদ্ধ (বই পৃ. ৪৮, ধারা ১০-১২)।",
                 "The Transfer of Property Act, 1882, Section 108", "অধ্যায় ২, পৃ. ৪৮ (ধারা ১০-১২)")
        d.clause("RES_TERMINATION_NOTICE", "termination", "TERMINATION AND VACATING",
                 f"That either party may terminate this tenancy by giving {number_with_words(notice_m, 'month' if notice_m == 1 else 'months')} prior notice in writing. "
                 f"On expiry or termination, the Tenant shall hand over vacant possession of the Schedule Premises along with the keys and clearance of all utility bills.",
                 "লিখিত নোটিশ দিয়ে চুক্তি অবসান এবং বিল পরিশোধ করে চাবিসহ খালি দখল হস্তান্তর।",
                 "The Transfer of Property Act, 1882, Section 106", "অধ্যায় ২, পৃ. ৪৮ (ধারা ১৪)")
        if notice_m is None:
            d.missing["notice_period_months"] = "notice period"
        if months and months > 12:
            d.clause("RES_REGISTRATION", "compliance", "REGISTRATION",
                     "That since the term of this tenancy exceeds one year, this Agreement shall be registered under Section 17 of the Registration Act, 1908 read with "
                     "Section 107 of the Transfer of Property Act, 1882.",
                     "১ বছরের বেশি মেয়াদ হলে রেজিস্ট্রি বাধ্যতামূলক।", "The Registration Act, 1908, Section 17", "অধ্যায় ২, পৃ. ৪৫", risk="high")
        d.common_closing_clauses("Agreement")
        landlord = d.party_block("landlord", "landlord_name", "FIRST PARTY/LESSOR", "ONE")
        tenant = d.party_block("tenant", "tenant_name", "SECOND PARTY/TENANT", "OTHER")
        recitals = [
            "the First Party/Lessor is the absolute owner and possessor of the residential premises described in the Schedule below (hereinafter the 'Schedule Premises') and wants to let it out on monthly rent",
            "the Second Party/Tenant wants to take the Schedule Premises on rent for residential purpose",
            "both the parties want to execute this Tenancy Agreement on the following terms and conditions",
        ]
        text = d.agreement("RESIDENTIAL TENANCY AGREEMENT", "FIRST PARTY/LESSOR", "SECOND PARTY/TENANT", landlord, tenant, recitals,
                           _lease_schedule(d, "SCHEDULE OF THE PREMISES"), "Agreement")
        return _finish(d, text)

    # ------------------------------------------------------------- employment
    @staticmethod
    def assemble_employment_agreement(facts: Dict[str, Any], style: str = "balanced", language: str = "en"):
        d = Draft(facts, style)
        designation = d.get("designation", "designation")
        joining = d.get("joining_date", "joining date")
        probation = to_int(facts.get("probation_months"))
        notice_days = to_int(facts.get("notice_period_days"))
        location = facts.get("work_location") or BLANK
        d.clause("EMP_APPOINTMENT_ROLE", "appointment", "APPOINTMENT",
                 f"That the Employer hereby appoints the Employee as {designation}"
                 f"{' in the ' + str(facts['department']) + ' department' if d.has('department') else ''}, posted at {location}, with effect from {joining}. "
                 f"The Employee shall perform the duties assigned from time to time by the Employer consistent with the said position.",
                 "পদবি, কর্মস্থল ও যোগদানের তারিখসহ নিয়োগ।", "The Bangladesh Labour Act, 2006, Section 5", None)
        d.clause("EMP_PROBATION_CONFIRMATION", "probation", "PROBATION AND CONFIRMATION",
                 f"That the Employee shall be on probation for {number_with_words(probation, 'months')} from the date of joining, subject to the provisions of "
                 f"Section 4 of the Bangladesh Labour Act, 2006 where applicable. On satisfactory completion of probation, the Employee shall be confirmed in writing.",
                 "শিক্ষানবিসকাল এবং সন্তোষজনক হলে লিখিত স্থায়ীকরণ (শ্রম আইন ২০০৬, ধারা ৪)।", "The Bangladesh Labour Act, 2006, Section 4", None)
        if probation is None:
            d.missing["probation_months"] = "probation period"
        d.clause("EMP_COMPENSATION_SALARY", "compensation", "SALARY AND BENEFITS",
                 f"That the Employee shall be paid a gross monthly salary of {d.taka('monthly_salary_bdt', 'gross monthly salary')}"
                 f"{' (' + str(facts['salary_breakdown']) + ')' if d.has('salary_breakdown') else ''}, payable within the 7th working day of the following month, "
                 f"subject to deduction of income tax at source as per law. Festival bonus and other benefits shall be as per the Employer's policy and applicable law.",
                 "মাসিক বেতন, পরিশোধের সময় এবং উৎসে কর কর্তন।", "The Bangladesh Labour Act, 2006, Section 123", None)
        d.clause("EMP_WORKING_HOURS", "conditions", "WORKING HOURS",
                 "That the working hours, weekly holiday and overtime shall be as per the Employer's rules and the Bangladesh Labour Act, 2006, where applicable.",
                 "কর্মঘণ্টা, সাপ্তাহিক ছুটি ও ওভারটাইম আইন ও প্রতিষ্ঠানের নীতিমালা অনুযায়ী।", "The Bangladesh Labour Act, 2006, Sections 100-103", None)
        d.clause("EMP_LEAVE_ENTITLEMENT", "leave", "LEAVE",
                 "That the Employee shall be entitled to casual leave, sick leave, annual leave and festival holidays as per the Employer's leave policy, which shall not be "
                 "less than the entitlements under the Bangladesh Labour Act, 2006 where applicable.",
                 "নৈমিত্তিক, অসুস্থতা, বার্ষিক ও উৎসব ছুটি আইনের চেয়ে কম হবে না।", "The Bangladesh Labour Act, 2006, Sections 115-118", None)
        d.clause("EMP_CONFIDENTIALITY_IP", "confidentiality", "CONFIDENTIALITY AND INTELLECTUAL PROPERTY",
                 "That the Employee shall keep confidential all business information of the Employer during and after employment, and all work product created in the "
                 "course of employment shall belong to the Employer. During employment the Employee shall not engage in any competing business without written consent.",
                 "গোপনীয়তা ও কাজের মেধাস্বত্ব প্রতিষ্ঠানের; চাকরিকালে প্রতিযোগী ব্যবসা নিষেধ। চাকরি শেষে ব্যবসা নিষেধ চুক্তি আইনের ২৭ ধারায় সাধারণত অকার্যকর — তাই যুক্ত করা হয়নি।",
                 "The Contract Act, 1872, Section 27", None, risk="medium")
        d.clause("EMP_TERMINATION_NOTICE", "termination", "TERMINATION",
                 f"That either party may terminate this employment by giving {number_with_words(notice_days, 'days')} notice in writing or salary in lieu thereof, "
                 f"subject to Sections 26 and 27 of the Bangladesh Labour Act, 2006 where applicable. The Employer may terminate the employment for misconduct after "
                 f"due process in accordance with law. On separation the Employee shall return all property and documents of the Employer.",
                 "লিখিত নোটিশ বা নোটিশের বদলে বেতন দিয়ে চাকরি অবসান; অসদাচরণে আইনানুগ প্রক্রিয়ায় বরখাস্ত।",
                 "The Bangladesh Labour Act, 2006, Sections 23, 26 & 27", None, risk="medium")
        if notice_days is None:
            d.missing["notice_period_days"] = "termination notice (days)"
        d.common_closing_clauses("Agreement")
        employer = d.party_block("employer", "employer_name", "FIRST PARTY/EMPLOYER", "ONE")
        employee = d.party_block("employee", "employee_name", "SECOND PARTY/EMPLOYEE", "OTHER")
        recitals = [
            f"the Employer is desirous of appointing a suitable person to the position of {designation}",
            "the Employee has represented that he/she possesses the required qualification and experience and has agreed to accept the appointment",
            "the parties want to record the terms and conditions of employment in writing",
        ]
        text = d.agreement("EMPLOYMENT AGREEMENT", "FIRST PARTY/EMPLOYER", "SECOND PARTY/EMPLOYEE", employer, employee, recitals, None, "Agreement")
        return _finish(d, text)

    # --------------------------------------------------------------- NI Act
    @staticmethod
    def assemble_demand_notice_ni_act(facts: Dict[str, Any], style: str = "balanced", language: str = "en"):
        d = Draft(facts, style)
        drawer = d.get("drawer_name", "notice receiver (drawer) name")
        drawer_father = facts.get("drawer_father")
        drawer_addr = d.get("drawer_address", "drawer address")
        payee = d.get("payee_name", "client (payee) name")
        payee_father = facts.get("payee_father")
        payee_addr = d.get("payee_address", "client address")
        advocate = d.get("advocate_name", "advocate name")
        adv_court = facts.get("advocate_court") or "Advocate, Supreme Court of Bangladesh"
        adv_addr = facts.get("advocate_address") or BLANK
        cheque_no = d.get("cheque_no", "cheque number")
        cheque_date = d.get("cheque_date", "cheque date")
        bank = d.get("bank_name", "drawee bank and branch")
        account = facts.get("account_no") or BLANK
        amount = d.taka("cheque_amount_bdt", "cheque amount")
        presented = d.get("presentation_date", "date of presentation")
        presenting_bank = facts.get("presentation_bank") or BLANK
        returned = d.get("return_memo_date", "date of dishonour memo")
        reason = d.get("dishonour_reason", "reason of dishonour")
        background = d.get("liability_background", "background of the liability")

        d.clause("NI_FACTS_STATEMENT", "facts", "STATEMENT OF FACTS",
                 f"That you the Notice Receiver owe a legally enforceable debt/liability to our client in the following circumstances: {background}.",
                 "দেনার উৎস ও ঘটনাক্রম স্পষ্ট ভাষায় (বই পৃ. ১২১: Statement of facts — chronology)।",
                 "The Negotiable Instruments Act, 1881, Section 138", "অধ্যায় ৪, পৃ. ১২০-১২১")
        d.clause("NI_CHEQUE_ISSUED", "facts", "ISSUANCE OF CHEQUE",
                 f"That in discharge of the said liability you issued Cheque No. {cheque_no} dated {cheque_date} for {amount} drawn on {bank}, Account No. {account}, in favour of our client.",
                 "চেকের নম্বর, তারিখ, অংক, ব্যাংক ও হিসাব নম্বর (বই পৃ. ১৩৬, অনুচ্ছেদ ৫)।",
                 "The Negotiable Instruments Act, 1881, Section 138", "অধ্যায় ৪, পৃ. ১৩৬")
        d.clause("NI_DISHONOUR_MEMO", "facts", "PRESENTATION AND DISHONOUR",
                 f"That our client presented the said cheque for encashment through {presenting_bank} on {presented}, within the period of its validity, but the same was "
                 f"returned unpaid on {returned} with the remark \"{reason}\", and our client was informed of the dishonour by the bank's return memo.",
                 "চেক জমা দেওয়ার তারিখ ও ব্যাংক, ডিজঅনারের তারিখ ও কারণ (বই পৃ. ১৩৬, অনুচ্ছেদ ৬)।",
                 "The Negotiable Instruments Act, 1881, Section 138(1)(a)", "অধ্যায় ৪, পৃ. ১৩৬")
        d.clause("NI_OFFENCE", "facts", "OFFENCE",
                 "That dishonour of the cheque on the aforesaid ground is an offence punishable under Section 138 read with Sections 140 and 141 of the Negotiable "
                 "Instruments Act, 1881, and you are liable to be dealt with in accordance with law.",
                 "ডিজঅনার ধারা ১৩৮, ১৪০ ও ১৪১ অনুযায়ী দণ্ডনীয় অপরাধ (বই পৃ. ১৩৬, অনুচ্ছেদ ৭)।",
                 "The Negotiable Instruments Act, 1881, Sections 138, 140 & 141", "অধ্যায় ৪, পৃ. ১৩৬")
        d.clause("NI_STATUTORY_DEMAND_30_DAYS", "demand", "DEMAND",
                 f"That, therefore, by this notice under Section 138(1)(b) of the Negotiable Instruments Act, 1881, you are called upon to pay the said amount of {amount} "
                 f"to our client within 30 (Thirty) days of receipt of this notice, failing which we have clear instruction from our client to initiate legal proceedings "
                 f"against you in the appropriate Court of Law under Sections 138, 140 and 141 of the Negotiable Instruments Act, 1881, and the risk, responsibility and "
                 f"costs of such proceedings shall lie entirely upon you.",
                 "নোটিশ প্রাপ্তির ৩০ দিনের মধ্যে টাকা পরিশোধের দাবি; অন্যথায় মামলা (ধারা ১৩৮(১)(গ)); ৩০ দিন পার হলে পরবর্তী ১ মাসের মধ্যে মামলা করতে হবে (ধারা ১৪১(খ))।",
                 "The Negotiable Instruments Act, 1881, Sections 138(1)(b)-(c) & 141(b)", "অধ্যায় ৪, পৃ. ১৩৬", risk="high")
        ref = facts.get("notice_reference") or f"LN/{BLANK}"
        date = d.get("notice_date", "notice date")
        clauses_txt = "\n\n".join(f"{i}. {c.text_content}" for i, c in enumerate(d.clauses, start=1))
        text = "\n".join([
            "LEGAL NOTICE",
            "(REGISTERED WITH A/D)",
            "",
            f"Ref: {ref}",
            f"Date: {date}",
            "",
            "To:",
            f"{drawer}{', son/daughter of ' + str(drawer_father) if drawer_father else ''}",
            f"{drawer_addr}",
            "……..NOTICE RECEIVER",
            "",
            "From:",
            f"{advocate}",
            f"{adv_court}",
            f"{adv_addr}",
            "",
            "For and on behalf of:",
            f"{payee}{', son/daughter of ' + str(payee_father) if payee_father else ''}",
            f"{payee_addr}",
            "(Henceforth referred to as 'our client')",
            "……..NOTICE GIVER",
            "",
            "Subject: Legal Notice under Sections 138 and 140 of the Negotiable Instruments Act, 1881.",
            "",
            "Dear Sir/Madam,",
            "",
            "Under instruction of our above-named client, we serve this Legal Notice upon you as under:—",
            "",
            clauses_txt,
            "",
            "A copy of this Legal Notice is kept in our Chamber for further reference.",
            "",
            "Thanking you,",
            "",
            "Yours sincerely,",
            "",
            "",
            f"({advocate})",
            f"{adv_court}",
            "",
            "Enclosure: Photocopy of the dishonoured cheque and the bank's return memo.",
        ])
        _ni_timeline_warnings(d)
        return _finish(d, text)

    # ------------------------------------------------------------ partnership
    @staticmethod
    def assemble_partnership_deed(facts: Dict[str, Any], style: str = "balanced", language: str = "en"):
        d = Draft(facts, style)
        firm = d.get("firm_name", "firm name")
        firm_addr = d.get("firm_address", "firm principal office")
        business = d.get("business_nature", "nature of business")
        capital = d.get("capital_contribution", "capital contribution")
        ratio = d.get("profit_sharing_ratio", "profit & loss sharing ratio")
        commence = d.get("commencement_date", "commencement date")
        signatories = facts.get("bank_signatories") or "the joint signatures of all the partners"
        d.clause("PART_NAME_OFFICE", "constitution", "NAME, OFFICE AND BUSINESS",
                 f"That the partners hereby become and shall continue as partners in the business of {business} under the name and style of \"{firm}\", having its "
                 f"principal office at {firm_addr}, with liberty to open branches elsewhere in Bangladesh by mutual consent. The partnership shall commence on "
                 f"{commence} and shall be a partnership at will unless otherwise agreed in writing.",
                 "ফার্মের নাম, প্রধান কার্যালয়, ব্যবসা ও শুরুর তারিখ (বই পৃ. ৬৮, ধারা ১-৪)।",
                 "The Partnership Act, 1932, Sections 4 & 7", "অধ্যায় ২, পৃ. ৬৮")
        d.clause("PART_CAPITAL_PROFIT", "financial", "CAPITAL, ACCOUNTS AND PROFIT",
                 f"That the capital of the partnership shall be {capital}. Proper books of account shall be maintained at the principal office and, at the end of each "
                 f"financial year, the profit and loss account and balance sheet shall be prepared and signed by all the partners in token of correctness. "
                 f"The net profit or loss so ascertained shall be shared and borne by the partners in the ratio of {ratio}.",
                 "মূলধন, হিসাব সংরক্ষণ, বার্ষিক হিসাবে সকলের স্বাক্ষর এবং লাভ-লোকসান বণ্টনের অনুপাত (বই পৃ. ৬৮, ধারা ৫-৬)।",
                 "The Partnership Act, 1932, Section 13", "অধ্যায় ২, পৃ. ৬৮")
        d.clause("PART_BANKING_ACCOUNTS", "banking", "BANK ACCOUNTS",
                 f"That the bank accounts of the firm shall be opened in the name of the firm and operated by {signatories}; all cheques and financial documents shall be "
                 f"signed accordingly.", "ব্যাংক হিসাব ফার্মের নামে এবং নির্ধারিত স্বাক্ষরে পরিচালিত হবে (বই পৃ. ৬৯, ধারা ৭)।",
                 "The Partnership Act, 1932", "অধ্যায় ২, পৃ. ৬৯")
        d.clause("PART_DUTIES", "conduct", "DUTIES OF PARTNERS",
                 "That every partner shall be just and faithful to the other partners, render true accounts, attend diligently to the business, not carry on any "
                 "competing business on his/her own account without the written consent of the others, and not do anything which causes loss or harm to the reputation "
                 "of the firm. Personal drawings shall be recorded in the respective partner's ledger account.",
                 "অংশীদারদের বিশ্বস্ততা, সঠিক হিসাব, প্রতিযোগী ব্যবসা নিষেধ ও ব্যক্তিগত উত্তোলনের হিসাব (বই পৃ. ৬৯-৭০, ধারা ১৪-১৫, ২৭)।",
                 "The Partnership Act, 1932, Sections 9 & 16", "অধ্যায় ২, পৃ. ৬৯-৭০")
        d.clause("PART_DISSOLUTION_RETIREMENT", "exit", "RETIREMENT, DEATH AND DISSOLUTION",
                 "That a partner desiring to retire shall give 3 (Three) months' prior notice in writing, and the remaining partners shall have the pre-emptive right to "
                 "purchase the retiring partner's share, to be exercised within 1 (One) month of receipt of the notice. Death or insanity of a partner shall not dissolve "
                 "the partnership; the legal heir(s) may be inducted as partner(s) with the mutual approval of the other partners, failing which the share of the deceased, "
                 "with adjusted capital, shall be paid to the legal heirs. On dissolution, the assets shall be applied first in payment of the firm's liabilities and the "
                 "surplus or deficit shall be shared in the profit-sharing ratio.",
                 "৩ মাসের নোটিশে অবসর, অন্যদের অগ্রক্রয় অধিকার, মৃত্যুতে ফার্ম বিলুপ্ত নয়, বিলুপ্তিতে হিসাব নিষ্পত্তি (বই পৃ. ৬৯-৭০, ধারা ১১, ১৮-১৯, ২৩)।",
                 "The Partnership Act, 1932, Sections 32, 42 & 48", "অধ্যায় ২, পৃ. ৬৯-৭০")
        d.clause("PART_DISPUTE_ARBITRATION", "dispute", "ARBITRATION AND APPLICABLE LAW",
                 "That any difference between the partners touching the partnership shall be referred first to mediation and, failing settlement, to arbitration under "
                 "the Arbitration Act, 2001. All matters not provided for herein shall be governed by The Partnership Act, 1932. The partners shall register the firm with "
                 "the Registrar of Joint Stock Companies and Firms, as an unregistered firm cannot sue to enforce contractual rights (Section 69).",
                 "বিরোধে সালিশ; অন্য সব বিষয়ে অংশীদারি আইন ১৯৩২; ফার্ম নিবন্ধন করা উচিত (ধারা ৫৮, ৬৯)।",
                 "The Partnership Act, 1932, Sections 58 & 69; The Arbitration Act, 2001", "অধ্যায় ২, পৃ. ৬৯-৭০ (ধারা ২০, ২৮-২৯)")
        d.common_closing_clauses("Deed of Partnership")
        d.clauses = [c for c in d.clauses if c.code != "GEN_GOVERNING_LAW_DISPUTE"]
        p1 = d.party_block("partner_one", "partner_one", "PARTNER NO. 1", "FIRST")
        p2 = d.party_block("partner_two", "partner_two", "PARTNER NO. 2", "SECOND")
        recitals = [
            f"all the aforesaid parties are interested in carrying on the business of {business} together under the name and style \"{firm}\"",
            "capital, skill and co-operation are required for the said business and the parties have agreed to contribute the same on mutual understanding",
            "it is necessary to reduce into writing the terms and conditions agreed upon",
        ]
        text = d.agreement("DEED OF PARTNERSHIP", "PARTNER NO. 1", "PARTNER NO. 2", p1, p2, recitals, None, "Deed of Partnership")
        return _finish(d, text)

    # ------------------------------------------------------------------ sale
    @staticmethod
    def assemble_sale_agreement(facts: Dict[str, Any], style: str = "balanced", language: str = "en"):
        d = Draft(facts, style)
        total = d.taka("total_price_bdt", "total price")
        earnest = d.taka("earnest_money_bdt", "earnest money")
        t, e = to_amount(facts.get("total_price_bdt")), to_amount(facts.get("earnest_money_bdt"))
        balance = f"Tk. {indian_commas(t - e)}/- (Taka {words_en(t - e)}) only" if (t and e is not None and t >= e) else f"Tk. {BLANK}/- (Taka {BLANK}) only"
        if t and e and e > t:
            d.warnings.append("বায়নার টাকা মোট মূল্যের চেয়ে বেশি — তথ্য যাচাই করুন।")
        deadline = d.get("completion_deadline", "completion deadline")
        title_src = d.get("seller_title_source", "seller's source of title")
        d.clause("SALE_CONSIDERATION_BAYANA", "consideration", "CONSIDERATION AND EARNEST MONEY",
                 f"That the total consideration of the Schedule Property is fixed at {total}, out of which the Purchaser has paid {earnest} to the Vendor as earnest money "
                 f"(bayna) on execution of this Agreement, the receipt whereof the Vendor hereby acknowledges. The balance of {balance} shall be paid at the time of "
                 f"execution and registration of the sale deed.",
                 "মোট মূল্য, বায়নার টাকা প্রাপ্তিস্বীকার এবং অবশিষ্ট টাকা পরিশোধের সময়।", "The Contract Act, 1872, Section 10", None)
        d.clause("SALE_TITLE_WARRANTY", "warranty", "TITLE AND ENCUMBRANCE",
                 f"That the Vendor declares that the Vendor is the absolute owner in possession of the Schedule Property having acquired it by {title_src}, the name of the "
                 f"Vendor stands mutated in the record of rights, and the property is free from all encumbrances, charges, mortgages, liens, attachments, litigation and "
                 f"claims of any third party. The Vendor shall hand over to the Purchaser for inspection the original title deeds, chain deeds (bia dolil), khatian, "
                 f"mutation (namjari) and DCR, up-to-date land development tax receipts and a non-encumbrance certificate. If any defect in title is found, the Vendor "
                 f"shall cure it at the Vendor's own cost, failing which the Vendor shall refund the earnest money.",
                 "বিক্রেতার মালিকানার উৎস, দায়মুক্তির ঘোষণা এবং মূল দলিল, খতিয়ান, নামজারি, খাজনা রসিদ ও এনইসি প্রদর্শনের দায়িত্ব।",
                 "The Transfer of Property Act, 1882, Section 55", None, risk="high")
        d.clause("SALE_REGISTRATION_COMPLIANCE", "compliance", "REGISTRATION OF THIS AGREEMENT AND OF THE SALE DEED",
                 f"That this Agreement for sale shall be presented for registration within 30 (Thirty) days of its execution as required by Section 17A of the "
                 f"Registration Act, 1908. The Vendor shall execute and register the sale deed (saf kabala) in favour of the Purchaser or the Purchaser's nominee on or "
                 f"before {deadline} upon receipt of the balance consideration, and shall deliver peaceful possession of the Schedule Property on the date of registration. "
                 f"The registration costs of the sale deed shall be borne by {facts.get('registration_cost_borne_by') or 'the Purchaser'}.",
                 "বায়নাপত্র সম্পাদনের ৩০ দিনের মধ্যে রেজিস্ট্রি বাধ্যতামূলক (রেজিস্ট্রেশন আইন ধারা ১৭এ); নির্ধারিত সময়ে সাফ কবলা রেজিস্ট্রি ও দখল হস্তান্তর।",
                 "The Registration Act, 1908, Section 17A", None, risk="high")
        d.clause("SALE_SPECIFIC_PERFORMANCE_DEFAULT", "default", "DEFAULT",
                 f"That if the Vendor fails or refuses to execute and register the sale deed within the stipulated time despite the Purchaser's readiness and willingness, "
                 f"the Purchaser shall be entitled to enforce this Agreement by a suit for specific performance under the Specific Relief Act, 1877 (subject to Section "
                 f"21A thereof) and/or to recover the earnest money with compensation. If the Purchaser fails to pay the balance consideration within the stipulated time, "
                 f"the Vendor may cancel this Agreement by notice in writing, and the earnest money shall be dealt with as follows: "
                 f"{facts.get('earnest_forfeiture_terms') or BLANK}.",
                 "বিক্রেতা রেজিস্ট্রি না করলে ক্রেতা সুনির্দিষ্ট প্রতিকার আইনে মামলা করতে পারবেন; ক্রেতা টাকা না দিলে বায়নার টাকার বিষয়ে শর্ত।",
                 "The Specific Relief Act, 1877, Sections 12 & 21A", None, risk="high")
        if not d.has("earnest_forfeiture_terms"):
            d.missing["earnest_forfeiture_terms"] = "what happens to earnest money if purchaser defaults"
        d.common_closing_clauses("Agreement")
        vendor = d.party_block("seller", "seller_name", "FIRST PARTY/VENDOR", "ONE")
        buyer = d.party_block("buyer", "buyer_name", "SECOND PARTY/PURCHASER", "OTHER")
        schedule = "\n".join([
            "SCHEDULE OF THE PROPERTY",
            "",
            f"{d.get('property_schedule', 'property schedule (district, thana, mouza, J.L. no., khatian, dag, area)')}",
            f"Being butted and bounded: {facts.get('boundaries') or 'On the North: ……………  On the South: ……………  On the East: ……………  On the West: ……………'}",
        ])
        recitals = [
            f"the First Party/Vendor is the absolute owner in possession of the property described in the Schedule below (hereinafter the 'Schedule Property') having acquired it by {title_src}",
            "the Vendor is desirous of selling the Schedule Property and the Second Party/Purchaser has agreed to purchase the same free from all encumbrances",
            "the parties have agreed upon the consideration and want to record the terms of sale in writing pending execution and registration of the sale deed",
        ]
        text = d.agreement("AGREEMENT FOR SALE (BAYNANAMA)", "FIRST PARTY/VENDOR", "SECOND PARTY/PURCHASER", vendor, buyer, recitals, schedule, "Agreement")
        return _finish(d, text)

    # ------------------------------------------------------------------ loan
    @staticmethod
    def assemble_loan_agreement(facts: Dict[str, Any], style: str = "balanced", language: str = "en"):
        d = Draft(facts, style)
        amount = d.taka("loan_amount_bdt", "loan amount")
        mode = d.get("payment_mode", "mode of payment of the loan")
        purpose = facts.get("loan_purpose") or BLANK
        repay = d.get("repayment_deadline", "repayment schedule")
        security = facts.get("security_details")
        d.clause("LOAN_AMOUNT_DISBURSAL", "consideration", "LOAN AND ACKNOWLEDGEMENT",
                 f"That the Lender has advanced to the Borrower a loan (hawlat) of {amount} by {mode} for the purpose of {purpose}, and the Borrower hereby acknowledges "
                 f"the receipt of the said amount in full.",
                 "ঋণের পরিমাণ, প্রদানের মাধ্যম ও উদ্দেশ্য এবং ঋণগ্রহীতার প্রাপ্তিস্বীকার।", "The Contract Act, 1872, Sections 10 & 25", "অধ্যায় ২০")
        d.clause("LOAN_REPAYMENT_SCHEDULE", "repayment", "REPAYMENT",
                 f"That the Borrower shall repay the said loan to the Lender as follows: {repay}. Every repayment shall be made against a written receipt signed by the Lender "
                 f"or through bank transfer.",
                 "পরিশোধের সময়সূচি এবং প্রতিটি পরিশোধের লিখিত রসিদ।", "The Limitation Act, 1908", "অধ্যায় ২০")
        interest = facts.get("interest_rate")
        d.clause("LOAN_INTEREST", "financial", "INTEREST",
                 (f"That the loan shall carry interest at the rate of {interest} per annum." if interest else
                  "That the loan is interest-free (qard-e-hasana) and no interest or profit shall be payable on it."),
                 "সুদের হার বা সুদমুক্ত ঋণ — স্পষ্ট উল্লেখ।", None, None)
        d.clause("LOAN_SECURITY_COLLATERAL", "security", "SECURITY",
                 (f"That as security for repayment the Borrower has delivered the following to the Lender: {security}. " if security else
                  "That no security has been furnished for this loan other than the personal covenant of the Borrower. ")
                 + "The Borrower shall also execute a Demand Promissory Note in favour of the Lender for the loan amount simultaneously with this Agreement.",
                 "জামানতের বিবরণ এবং একসাথে ডিমান্ড প্রমিসরি নোট সম্পাদন (বই অধ্যায় ২০, পৃ. ৮০৭)।",
                 "The Negotiable Instruments Act, 1881, Section 4", "অধ্যায় ২০, পৃ. ৮০৭")
        d.clause("LOAN_DEFAULT_LEGAL_RECOURSE", "default", "DEFAULT",
                 "That if the Borrower fails to repay any amount on its due date, the entire outstanding amount shall become immediately due, and the Lender shall be "
                 "entitled to recover the same with costs by a money suit and, where any cheque issued by the Borrower is dishonoured, to proceed under Section 138 of "
                 "The Negotiable Instruments Act, 1881, in accordance with law.",
                 "কিস্তি খেলাপ হলে সম্পূর্ণ টাকা তাৎক্ষণিক পরিশোধযোগ্য; অর্থ আদায় মামলা বা চেক ডিজঅনার হলে ধারা ১৩৮-এর প্রতিকার।",
                 "The Negotiable Instruments Act, 1881, Section 138; The Code of Civil Procedure, 1908", "অধ্যায় ৪, পৃ. ১৩১-১৩৬", risk="medium")
        d.common_closing_clauses("Agreement")
        lender = d.party_block("lender", "lender_name", "FIRST PARTY/LENDER", "ONE")
        borrower = d.party_block("borrower", "borrower_name", "SECOND PARTY/BORROWER", "OTHER")
        recitals = [
            f"the Borrower requested the Lender for a loan of {amount} for the purpose of {purpose}",
            "the Lender has agreed to advance the said loan on the terms and conditions hereinafter contained",
        ]
        text = d.agreement("LOAN AGREEMENT (HAWLATNAMA)", "FIRST PARTY/LENDER", "SECOND PARTY/BORROWER", lender, borrower, recitals, None, "Agreement")
        return _finish(d, text)

    # ------------------------------------------------------------------- NDA
    @staticmethod
    def assemble_nda(facts: Dict[str, Any], style: str = "balanced", language: str = "en"):
        d = Draft(facts, style)
        subject = d.get("confidential_matter", "subject matter of confidential information")
        years = to_int(facts.get("duration_years"))
        effective = d.get("effective_date", "effective date")
        d.clause("NDA_CONFIDENTIAL_INFO_DEF", "definition", "CONFIDENTIAL INFORMATION",
                 f"That 'Confidential Information' means all information, in any form, disclosed by the Disclosing Party to the Receiving Party in connection with {subject}, "
                 f"including business, technical, financial and customer information, but excludes information which (a) is or becomes public without breach of this "
                 f"Agreement, (b) was lawfully known to the Receiving Party before disclosure, (c) is lawfully received from a third party without restriction, or "
                 f"(d) is independently developed without use of the Confidential Information.",
                 "গোপনীয় তথ্যের সংজ্ঞা এবং ব্যতিক্রম।", None, None)
        d.clause("NDA_NON_DISCLOSURE_DUTY", "obligation", "OBLIGATIONS OF THE RECEIVING PARTY",
                 "That the Receiving Party shall use the Confidential Information solely for the stated purpose, shall not disclose it to any person except its employees "
                 "or advisers who need to know and are bound by similar obligations, shall protect it with at least reasonable care, and shall return or destroy it on "
                 "written request. Disclosure required by law or order of a court shall not be a breach, provided prompt prior notice is given to the Disclosing Party.",
                 "শুধু নির্ধারিত উদ্দেশ্যে ব্যবহার, প্রয়োজন ছাড়া প্রকাশ নিষেধ, অনুরোধে ফেরত/ধ্বংস; আইনানুগ প্রকাশ ব্যতিক্রম।", None, None)
        d.clause("NDA_INJUNCTIVE_RELIEF", "remedy", "REMEDIES",
                 "That any breach of this Agreement may cause irreparable loss to the Disclosing Party, who shall be entitled to seek injunction under the Specific Relief "
                 "Act, 1877 in addition to compensation under Section 73 of The Contract Act, 1872.",
                 "চুক্তিভঙ্গে নিষেধাজ্ঞা ও ক্ষতিপূরণ।", "The Specific Relief Act, 1877, Sections 54-57; The Contract Act, 1872, Section 73", None, risk="medium")
        d.clause("NDA_SURVIVAL_TERM", "term", "TERM",
                 f"That this Agreement shall come into force on {effective} and the obligations of confidentiality shall continue for {number_with_words(years, 'years')} "
                 f"from the date of the last disclosure.", "কার্যকর তারিখ ও গোপনীয়তার মেয়াদ।", None, None)
        if years is None:
            d.missing["duration_years"] = "confidentiality period (years)"
        d.common_closing_clauses("Agreement")
        first = f"{d.get('disclosing_party', 'disclosing party')}, of {d.get('disclosing_party_address', 'disclosing party address')}, hereinafter referred to as the DISCLOSING PARTY (which expression shall include its successors and permitted assigns) of the ONE PART."
        second = f"{d.get('receiving_party', 'receiving party')}, of {d.get('receiving_party_address', 'receiving party address')}, hereinafter referred to as the RECEIVING PARTY (which expression shall include its successors and permitted assigns) of the OTHER PART."
        recitals = [f"the parties wish to discuss and evaluate {subject}, for which the Disclosing Party may disclose Confidential Information to the Receiving Party",
                    "the Receiving Party has agreed to keep such information confidential on the following terms"]
        text = d.agreement("NON-DISCLOSURE AGREEMENT", "DISCLOSING PARTY", "RECEIVING PARTY", first, second, recitals, None, "Agreement")
        return _finish(d, text)

    # --------------------------------------------------------------- service
    @staticmethod
    def assemble_service_agreement(facts: Dict[str, Any], style: str = "balanced", language: str = "en"):
        d = Draft(facts, style)
        scope = d.get("scope_of_work", "scope of work")
        fee = d.get("service_fee_bdt", "service fee and payment milestones")
        fee_amt = to_amount(facts.get("service_fee_bdt"))
        fee_txt = f"Tk. {indian_commas(fee_amt)}/- (Taka {words_en(fee_amt)}) only" if fee_amt and str(facts.get("service_fee_bdt")).strip().replace(",", "").isdigit() else fee
        deadline = d.get("delivery_deadline", "delivery deadline")
        d.clause("SRV_SCOPE_DELIVERABLES", "scope", "SCOPE OF WORK",
                 f"That the Service Provider shall render the following services and deliverables to the Client: {scope}, and shall complete the same on or before {deadline}.",
                 "কাজের পরিধি, ডেলিভারেবল ও সময়সীমা।", None, "অধ্যায় ২, পৃ. ৪৫")
        d.clause("SRV_FEES_TAXES", "payment", "FEES AND TAXES",
                 f"That in consideration of the services the Client shall pay {fee_txt}. Applicable VAT and income tax shall be deducted at source by the Client as per "
                 f"prevailing laws, and certificates of such deduction shall be provided to the Service Provider.",
                 "সেবামূল্য, পরিশোধ পদ্ধতি এবং উৎসে ভ্যাট/কর কর্তন।", "The Value Added Tax and Supplementary Duty Act, 2012; The Income Tax Act, 2023", None)
        d.clause("SRV_ACCEPTANCE_DELAY", "delay", "ACCEPTANCE AND DELAY",
                 "That the Client shall review each deliverable within 7 (Seven) days of submission and either accept it or point out deficiencies in writing. If the "
                 "Service Provider fails to deliver within the agreed time for reasons attributable to it, the Client may, after 15 (Fifteen) days' written notice, "
                 "terminate this Agreement and recover payments made for undelivered work.",
                 "ডেলিভারেবল গ্রহণ পদ্ধতি এবং বিলম্বে প্রতিকার (বই পৃ. ৪৫: Delay clause)।", "The Contract Act, 1872, Sections 55 & 73", "অধ্যায় ২, পৃ. ৪৫", risk="medium")
        d.clause("SRV_IP_OWNERSHIP", "ip", "INTELLECTUAL PROPERTY AND CONFIDENTIALITY",
                 "That upon full payment all deliverables created specifically for the Client shall belong to the Client, and each party shall keep the other's "
                 "confidential information confidential during and after the term of this Agreement.",
                 "সম্পূর্ণ মূল্য পরিশোধের পর কাজের মেধাস্বত্ব ক্লায়েন্টের; উভয় পক্ষ গোপনীয়তা রক্ষা করবে।", "The Copyright Act, 2023", None)
        d.clause("SRV_TERMINATION_BREACH", "termination", "TERMINATION AND FORCE MAJEURE",
                 "That either party may terminate this Agreement if the other commits a material breach and fails to remedy it within 15 (Fifteen) days of written notice. "
                 "Neither party shall be liable for delay or failure caused by force majeure events beyond its reasonable control, such as natural disaster, war, "
                 "epidemic or government restriction, provided prompt written notice is given.",
                 "গুরুতর চুক্তিভঙ্গে ১৫ দিনের নোটিশে অবসান; দৈব-দুর্বিপাকে দায় নেই (বই পৃ. ৪৫: Force majeure)।", "The Contract Act, 1872, Section 56", "অধ্যায় ২, পৃ. ৪৫")
        d.common_closing_clauses("Agreement")
        first = f"{d.get('client_name', 'client name')}, of {d.get('client_address', 'client address')}, hereinafter referred to as the CLIENT (which expression shall include its successors and permitted assigns) of the ONE PART."
        second = f"{d.get('service_provider_name', 'service provider name')}, of {d.get('service_provider_address', 'service provider address')}, hereinafter referred to as the SERVICE PROVIDER (which expression shall include its successors and permitted assigns) of the OTHER PART."
        recitals = ["the Client requires the services described herein and the Service Provider has represented that it has the necessary skill and resources",
                    "the parties want to record the terms on which the services shall be rendered"]
        text = d.agreement("SERVICE AGREEMENT", "CLIENT", "SERVICE PROVIDER", first, second, recitals, None, "Agreement")
        return _finish(d, text)

    # ---------------------------------------------------------------- custom
    @staticmethod
    def assemble_custom_agreement(facts: Dict[str, Any], custom_title: Optional[str] = None, style: str = "balanced", language: str = "en"):
        d = Draft(facts, style)
        title = (custom_title or facts.get("custom_matter_name") or "AGREEMENT").strip()
        purpose = d.get("purpose_and_consideration", "purpose and consideration")
        ob1 = d.get("obligations_first_party", "obligations of the first party")
        ob2 = d.get("obligations_second_party", "obligations of the second party")
        effective = d.get("effective_date", "effective date", fallback_keys=("execution_date",))
        cure = facts.get("breach_and_cure_period") or "That if either party commits a breach and fails to remedy it within 15 (Fifteen) days of written notice, the aggrieved party may terminate this Agreement and claim compensation"
        term = facts.get("termination_and_dispute")
        d.clause("CUSTOM_RECITALS_CONSIDERATION", "consideration", "OBJECT AND CONSIDERATION",
                 f"That this Agreement shall come into effect on {effective}. The object and consideration of this Agreement are: {purpose}.",
                 "চুক্তির উদ্দেশ্য, প্রতিদান ও কার্যকর তারিখ (চুক্তি আইন ধারা ১০, ২৩)।", "The Contract Act, 1872, Sections 10 & 23", "অধ্যায় ২, পৃ. ৪৫")
        d.clause("CUSTOM_COVENANTS_PARTY_ONE", "obligation", "OBLIGATIONS OF THE FIRST PARTY", f"That the First Party shall: {ob1}.",
                 "প্রথম পক্ষের দায়িত্ব।", "The Contract Act, 1872, Section 37", "অধ্যায় ২, পৃ. ৪৫")
        d.clause("CUSTOM_COVENANTS_PARTY_TWO", "obligation", "OBLIGATIONS OF THE SECOND PARTY", f"That the Second Party shall: {ob2}.",
                 "দ্বিতীয় পক্ষের দায়িত্ব।", "The Contract Act, 1872, Section 37", "অধ্যায় ২, পৃ. ৪৫")
        d.clause("CUSTOM_BREACH_REMEDIES", "default", "DEFAULT AND COMPENSATION",
                 f"{cure.rstrip('.')}. The party in breach shall be liable to compensate the other for loss caused thereby in accordance with Section 73 of The Contract Act, 1872.",
                 "চুক্তিভঙ্গে সংশোধনের সময় ও ক্ষতিপূরণ (বই পৃ. ৪৫: Default & Compensation)।", "The Contract Act, 1872, Section 73", "অধ্যায় ২, পৃ. ৪৫", risk="medium")
        d.clause("CUSTOM_TERMINATION", "termination", "TERMINATION",
                 f"That {term.rstrip('.') if term else 'either party may terminate this Agreement by giving 30 (Thirty) days prior notice in writing to the other party'}.",
                 "চুক্তি অবসানের নোটিশ (বই পৃ. ৪৫: Notice period)।", "The Contract Act, 1872", "অধ্যায় ২, পৃ. ৪৫")
        if facts.get("special_stipulations"):
            d.clause("CUSTOM_SPECIAL_STIPULATIONS", "special", "SPECIAL CONDITIONS", f"That {facts['special_stipulations']}.",
                     "বিশেষ শর্তাবলী।", None, None)
        d.common_closing_clauses("Agreement")
        d.clauses[-4].code = "CUSTOM_DISPUTE_JURISDICTION"
        p1 = d.party_block("party_one", "party_one_name", "FIRST PARTY", "ONE")
        p2 = d.party_block("party_two", "party_two_name", "SECOND PARTY", "OTHER")
        recitals = [f"the parties have agreed to enter into this {title} for the purpose of {purpose}",
                    "the parties want to reduce the terms and conditions agreed between them into writing"]
        text = d.agreement(title, "FIRST PARTY", "SECOND PARTY", p1, p2, recitals, None, "Agreement")
        return _finish(d, text)

    # -------------------------------------------------------------- metadata
    @staticmethod
    def get_grounding_metadata(template_code: str, facts: Dict[str, Any], clauses: List[ClauseSelectionItem]) -> Dict[str, Any]:
        matter = TEMPLATE_TO_MATTER.get((template_code or "").upper(), "custom")
        refs = {
            "commercial_lease": "অধ্যায় ২: চুক্তিপত্র — মৌলিক উপাদান (পৃ. ৪৫-৪৬) ও ভাড়াচুক্তির নমুনা (পৃ. ৪৬-৪৮)",
            "residential_rent": "অধ্যায় ২: চুক্তিপত্র — মৌলিক উপাদান (পৃ. ৪৫-৪৬) ও ভাড়াচুক্তির নমুনা (পৃ. ৪৬-৪৮)",
            "demand_notice_ni_act": "অধ্যায় ৪: লিগ্যাল নোটিশের উপাদান (পৃ. ১২০-১২১) ও ধারা ১৩৮-এর নোটিশ নমুনা (পৃ. ১৩৪-১৩৬)",
            "partnership_deed": "অধ্যায় ২: অংশীদারি দলিলের নমুনা (পৃ. ৬৭-৭০)",
            "sale_agreement": "অধ্যায় ২: চুক্তিপত্র — মৌলিক উপাদান (পৃ. ৪৫-৪৬); সম্পত্তির বর্ণনা ও চৌহদ্দি (পৃ. ১২৭-১২৮)",
            "loan_agreement": "অধ্যায় ২ (পৃ. ৪৫-৪৬) ও অধ্যায় ২০: ঋণ সংক্রান্ত দলিল (ডিমান্ড প্রমিসরি নোট)",
        }
        audit = book_checklist(matter, facts or {}, clauses)
        ok = sum(1 for a in audit if a["ok"])
        score = int(round(100 * ok / len(audit))) if audit else 0
        return {
            "book_grounding_score": score,
            "book_chapter_reference": refs.get(matter, "অধ্যায় ২: চুক্তিপত্র — মৌলিক উপাদান (পৃ. ৪৫-৪৬)"),
            "book_applied_rules": [f"{'✔' if a['ok'] else '✘'} {a['item_bn']}" + (f" — {a['note_bn']}" if a.get("note_bn") else "") for a in audit],
        }


def _ni_timeline_warnings(d: Draft):
    """Section 138(1)(a)/(b) timelines, checked only when both dates are clearly parseable."""
    from datetime import datetime

    def parse(v):
        if is_blank(v):
            return None
        s = normalize_digits(str(v)).strip()
        for fmt in ("%d.%m.%Y", "%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d", "%d %B %Y", "%d %b %Y", "%B %d, %Y"):
            try:
                return datetime.strptime(s, fmt)
            except ValueError:
                continue
        return None

    cheque, presented, returned, notice = (parse(d.facts.get(k)) for k in ("cheque_date", "presentation_date", "return_memo_date", "notice_date"))
    if cheque and presented and (presented - cheque).days > 183:
        d.warnings.append("চেকের তারিখ থেকে ৬ মাস পার হওয়ার পর ব্যাংকে জমা দেওয়া হয়েছে — ধারা ১৩৮(১)(ক) অনুযায়ী মামলা টিকবে না।")
    if returned and notice and (notice - returned).days > 30:
        d.warnings.append("ডিজঅনারের তথ্য পাওয়ার ৩০ দিন পার হয়ে গেছে — ধারা ১৩৮(১)(খ) অনুযায়ী নোটিশ সময়মতো নয়; অবিলম্বে আইনজীবীর পরামর্শ নিন।")
    elif returned and not notice:
        d.warnings.append("ডিজঅনারের তথ্য পাওয়ার ৩০ দিনের মধ্যে নোটিশ পাঠাতে হবে (ধারা ১৩৮(১)(খ))।")


def book_checklist(matter: str, facts: Dict[str, Any], clauses: List[ClauseSelectionItem]) -> List[Dict[str, Any]]:
    """Checks the draft against the book's 'basic things to be contained' lists (p.45-46, p.120-121)."""
    codes = {c.code for c in clauses}
    types = {c.clause_type for c in clauses}
    missing = {r["field"] for r in missing_requirements(matter, facts)}
    reqs = {r["field"]: r for r in requirements_for(matter)}

    def fields_ok(*keys):
        present = [k for k in keys if k in reqs]
        return all(k not in missing for k in present) if present else True

    party_keys = [k for k, r in reqs.items() if "নাম" in r["label_bn"] and r["kind"] == "fact" and r.get("critical")]
    parent_keys = [k for k in reqs if k.endswith("_father")]
    addr_keys = [k for k in reqs if k.endswith("_address") and not k.endswith("permanent_address")]

    if matter == "demand_notice_ni_act":
        items = [
            ("নোটিশের শিরোনাম ও 'Registered with A/D'", True),
            ("তারিখ", fields_ok("notice_date")),
            ("নোটিশ গ্রহীতার নাম ও সঠিক ঠিকানা", fields_ok("drawer_name", "drawer_address")),
            ("প্রেরক আইনজীবীর নাম", fields_ok("advocate_name")),
            ("মক্কেলের নাম ও ঠিকানা (For and on behalf of)", fields_ok("payee_name", "payee_address")),
            ("বিষয় (Subject)", True),
            ("ঘটনাক্রম (Statement of facts — chronology)", fields_ok("liability_background")),
            ("চেকের পূর্ণ বিবরণ (নং, তারিখ, অংক, ব্যাংক)", fields_ok("cheque_no", "cheque_date", "cheque_amount_bdt", "bank_name")),
            ("উপস্থাপন ও ডিজঅনারের তারিখ ও কারণ", fields_ok("presentation_date", "return_memo_date", "dishonour_reason")),
            ("দাবি ও সময়সীমা (৩০ দিন)", "NI_STATUTORY_DEMAND_30_DAYS" in codes),
            ("অন্যথায় আইনি ব্যবস্থার স্পষ্ট বিবৃতি", "NI_STATUTORY_DEMAND_30_DAYS" in codes),
            ("চেম্বারে কপি সংরক্ষণের বিবৃতি ও আইনজীবীর স্বাক্ষর", True),
        ]
    else:
        items = [
            ("চুক্তির নাম", True),
            ("সম্পাদনের তারিখ", fields_ok("execution_date")),
            ("কার্যকর হওয়ার তারিখ", fields_ok("commencement_date", "joining_date", "effective_date")),
            ("পক্ষগণের পূর্ণ নাম", fields_ok(*party_keys)),
            ("পক্ষগণের পিতা/মাতার নাম", fields_ok(*parent_keys)),
            ("পক্ষগণের বর্তমান ও স্থায়ী ঠিকানা", fields_ok(*addr_keys)),
            ("উত্তরাধিকারী/স্থলাভিষিক্ত অন্তর্ভুক্তির বাক্য", True),
            ("পটভূমি (Recitals — WHEREAS)", True),
            ("উভয় পক্ষের অধিকার ও দায়িত্ব", len(clauses) >= 5),
            ("প্রতিদান (Consideration)", fields_ok("monthly_rent_bdt", "monthly_salary_bdt", "total_price_bdt", "loan_amount_bdt", "service_fee_bdt", "capital_contribution", "purpose_and_consideration")),
            ("মেয়াদ (Tenure)", fields_ok("duration_months", "duration_years") if matter in ("commercial_lease", "residential_rent", "nda") else True),
            ("চুক্তির অবসান ও নোটিশ মেয়াদ", "termination" in types or "exit" in types),
            ("খেলাপ ও ক্ষতিপূরণ", "default" in types or matter in ("partnership_deed", "nda", "employment_agreement", "residential_rent")),
            ("বিরোধ নিষ্পত্তি ও প্রযোজ্য আইন", "dispute" in types),
            ("স্বেচ্ছায় সম্পাদন ও বাধ্যবাধকতা", "GEN_VOLUNTARY_BINDING" in codes),
            ("সম্পত্তির তফসিল", fields_ok("premises_address", "property_schedule") if matter in ("commercial_lease", "residential_rent", "sale_agreement") else True),
            ("সাক্ষীগণের নাম ও ঠিকানা", fields_ok("witness_one", "witness_two")),
            ("পৃষ্ঠা সংখ্যা, স্ট্যাম্প ও প্রতি পৃষ্ঠায় টিপসই", "GEN_EXECUTION_COPIES" in codes),
        ]
    return [{"item_bn": name, "ok": bool(ok), "note_bn": None if ok else "তথ্য অনুপস্থিত — নিচের প্রশ্নের উত্তর দিন"} for name, ok in items]


class _DraftOutput(tuple):
    """(text, clauses) that also carries the Draft, so callers can read blanks and warnings."""
    draft: "Draft"


def _finish(d: Draft, text: str):
    d.text = text
    out = _DraftOutput((text, d.clauses))
    out.draft = d
    return out


class DraftResult:
    """Full result including blanks and warnings, used by the API."""

    def __init__(self, text: str, clauses: List[ClauseSelectionItem], missing: List[Dict[str, Any]], warnings: List[str], checklist: List[Dict[str, Any]]):
        self.text, self.clauses, self.missing, self.warnings, self.checklist = text, clauses, missing, warnings, checklist


def build_draft(template_code: str, facts: Dict[str, Any], style: str = "balanced", language: str = "en") -> DraftResult:
    """Generates the draft and reports every blank as a question grounded in the book."""
    code = (template_code or "BD_CUSTOM_AGREEMENT").upper()
    matter = TEMPLATE_TO_MATTER.get(code, "custom")
    fn = {
        "commercial_lease": DraftingEngine.assemble_commercial_lease,
        "residential_rent": DraftingEngine.assemble_residential_lease,
        "employment_agreement": DraftingEngine.assemble_employment_agreement,
        "demand_notice_ni_act": DraftingEngine.assemble_demand_notice_ni_act,
        "partnership_deed": DraftingEngine.assemble_partnership_deed,
        "sale_agreement": DraftingEngine.assemble_sale_agreement,
        "loan_agreement": DraftingEngine.assemble_loan_agreement,
        "nda": DraftingEngine.assemble_nda,
        "service_agreement": DraftingEngine.assemble_service_agreement,
    }.get(matter)
    if fn:
        out = fn(facts, style, language)
    else:
        out = DraftingEngine.assemble_custom_agreement(facts, facts.get("custom_matter_name"), style, language)
    text, clauses = out
    d = out.draft
    reqs = {r["field"]: r for r in requirements_for(matter)}
    missing = []
    for r in missing_requirements(matter, facts):
        missing.append({"field": r["field"], "label_bn": r["label_bn"], "question_bn": r["question_bn"], "why_bn": r["why_bn"],
                        "kind": r["kind"], "critical": r.get("critical", False), "suggestion": r.get("suggestion")})
    for key, label in d.missing.items():
        if key not in reqs and not any(m["field"] == key for m in missing):
            missing.append({"field": key, "label_bn": label, "question_bn": f"{label} কী হবে?", "why_bn": "ড্রাফটে এই স্থান ফাঁকা রাখা হয়েছে।",
                            "kind": "fact", "critical": False, "suggestion": None})
    return DraftResult(text, clauses, missing, d.warnings, book_checklist(matter, facts, clauses))


drafting_engine = DraftingEngine()
