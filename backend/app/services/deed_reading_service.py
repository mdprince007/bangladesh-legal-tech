"""
Bangla land-deed reading pipeline.

Goal: never present a wrong reading as fact. A deed is read by independent readers, the readings
are compared field by field, checked against deterministic rules (area in digits vs. words, price in
digits vs. words, share <= 16 আনা, plot-area totals, dates, identical parties ...), and every field
carries a status. Nothing is treated as final until a person confirms it against the image.

Readers:
  1. Vision model pass A  - primary model on the original page images   (Gemini, needs GEMINI_API_KEY)
  2. Vision model pass B  - secondary model on the enhanced page images (independent second read)
  3. Local OCR (EasyOCR)  - offline, weak corroboration only; runs out-of-process

Field statuses:
  human_verified  - confirmed or corrected by a person (the only final state)
  machine_agreed  - both vision passes agree exactly and all checks pass; still awaits human confirmation
  needs_review    - readers disagree, confidence is low, a check failed, or only one reader was available
  illegible       - a reader reported the text as present but unreadable
  not_found       - no reader found this field on the document
"""
import json
import os
import re
import subprocess
import sys
from typing import Any, Dict, List, Optional, Tuple

from app.core.config import settings
from app.services.bangla_text import (
    comparison_key, extract_years, loose_key, normalize_bangla, normalize_digits,
    parse_bangla_number_words, parse_first_number, parse_land_area, parse_share,
)

# (key, Bangla label, group, kind, what the reader should look for)
FIELD_SPECS: List[Tuple[str, str, str, str, str]] = [
    ("deed_type", "দলিলের ধরন", "registration", "text", "type of deed as written, e.g. সাফ কবলা, হেবা, দানপত্র, বণ্টননামা, এওয়াজ"),
    ("deed_number", "দলিল নম্বর", "registration", "id", "registered deed number (দলিল নং), often with year e.g. ২৯৪৬/১৯৯৩"),
    ("registration_date", "রেজিস্ট্রির তারিখ", "registration", "date", "date of registration/execution exactly as written, including বাংলা সন if written"),
    ("sub_registry_office", "সাব-রেজিস্ট্রি অফিস", "registration", "text", "name of the sub-registry office"),
    ("district", "জেলা", "registration", "text", "district (জেলা)"),
    ("thana", "থানা / উপজেলা", "registration", "text", "police station / upazila"),
    ("seller_names", "দাতা / বিক্রেতার নাম", "parties", "name", "full name(s) of the executant(s)/seller(s)/donor(s) exactly as written; separate multiple people with ';'"),
    ("seller_parentage", "দাতার পিতা / স্বামীর নাম", "parties", "name", "father's or husband's name of the seller(s) (পিতা/স্বামী/পিং)"),
    ("seller_address", "দাতার ঠিকানা", "parties", "text", "address of the seller(s) (সাং, ডাকঘর, থানা, জেলা)"),
    ("buyer_names", "গ্রহীতা / ক্রেতার নাম", "parties", "name", "full name(s) of the recipient(s)/buyer(s) exactly as written; separate multiple people with ';'"),
    ("buyer_parentage", "গ্রহীতার পিতা / স্বামীর নাম", "parties", "name", "father's or husband's name of the buyer(s)"),
    ("buyer_address", "গ্রহীতার ঠিকানা", "parties", "text", "address of the buyer(s)"),
    ("mouza", "মৌজা", "schedule", "text", "mouza name in the schedule (তফসিল)"),
    ("jl_no", "জে.এল নং", "schedule", "id", "J.L. number"),
    ("khatian_cs", "সি.এস খতিয়ান নং", "schedule", "id", "C.S. khatian number(s)"),
    ("khatian_sa", "এস.এ খতিয়ান নং", "schedule", "id", "S.A. khatian number(s)"),
    ("khatian_rs", "আর.এস খতিয়ান নং", "schedule", "id", "R.S. khatian number(s)"),
    ("khatian_bs", "বি.এস / সিটি খতিয়ান নং", "schedule", "id", "B.S. / city survey / Dhaka city khatian number(s)"),
    ("dag_numbers", "দাগ নম্বর", "schedule", "id", "plot (দাগ) number(s), keep সাবেক/হাল labels as written"),
    ("land_class", "জমির শ্রেণি", "schedule", "text", "class of land, e.g. নাল, ভিটি, বাড়ি, পুকুর"),
    ("land_area", "জমির পরিমাণ (অংকে)", "schedule", "area", "total land area transferred, written in DIGITS with unit, e.g. ১২.০০ শতাংশ"),
    ("land_area_words", "জমির পরিমাণ (কথায়)", "schedule", "area_words", "total land area written in WORDS if the deed writes it, e.g. বারো শতাংশ"),
    ("share", "হিস্যা / অংশ", "schedule", "share", "share transferred, e.g. ১৬ আনা, ৮ আনা ৩ গণ্ডা, ১/২ অংশ"),
    ("boundary_north", "উত্তরে", "boundaries", "text", "north boundary (উত্তরে)"),
    ("boundary_south", "দক্ষিণে", "boundaries", "text", "south boundary (দক্ষিণে)"),
    ("boundary_east", "পূর্বে", "boundaries", "text", "east boundary (পূর্বে)"),
    ("boundary_west", "পশ্চিমে", "boundaries", "text", "west boundary (পশ্চিমে)"),
    ("consideration_amount", "পণমূল্য (অংকে)", "financial", "amount", "consideration / price in DIGITS, e.g. ৪৮,০০০/- টাকা"),
    ("consideration_words", "পণমূল্য (কথায়)", "financial", "amount_words", "consideration / price in WORDS, e.g. আটচল্লিশ হাজার টাকা মাত্র"),
    ("stamp_value", "স্ট্যাম্প মূল্য", "financial", "amount", "value of the stamp paper"),
    ("prior_deed", "বায়া দলিল (নং ও সাল)", "title", "id", "previous title deed number and year (বায়া দলিল)"),
    ("prior_owner", "পূর্ববর্তী মালিক", "title", "name", "previous owner through whom the seller acquired title"),
    ("identifier", "শনাক্তকারী", "execution", "name", "identifier (সনাক্তকারী) name"),
    ("deed_writer", "দলিল লেখক", "execution", "name", "deed writer (দলিল লেখক / মোহরার) name and licence no."),
    ("witnesses", "সাক্ষীগণ", "execution", "name", "witness names; separate with ';'"),
]
FIELD_LABELS = {k: label for k, label, _, _, _ in FIELD_SPECS}
FIELD_KINDS = {k: kind for k, _, _, kind, _ in FIELD_SPECS}
# Fields where a mistake changes the legal meaning of the deed
CRITICAL_FIELDS = {
    "deed_number", "registration_date", "seller_names", "buyer_names", "mouza", "jl_no",
    "khatian_cs", "khatian_sa", "khatian_rs", "khatian_bs", "dag_numbers", "land_area", "share",
    "consideration_amount",
}

AGREEMENT_MIN_CONFIDENCE = 80


def _vision_prompt() -> str:
    field_lines = "\n".join(f'- "{k}": {desc}' for k, _, _, _, desc in FIELD_SPECS)
    return f"""You are transcribing a scanned Bangladeshi land deed (দলিল). It may be handwritten in Bangla,
decades old, faded, stained or written in cursive deed-writer script. The pages are given in order.

Accuracy is more important than completeness. A wrong value is far worse than a missing one,
because this deed decides who owns land.

Rules:
1. Copy text exactly as written. Keep the original spelling, Bangla digits and abbreviations
   (মোঃ, মোসাম্মৎ, সাং, পিং, দাগ নং). Do not correct spelling, translate, modernise or complete names.
2. If any character is uncertain, write [?] in its place in "verbatim" and set "legibility" to "partial".
   Never replace an unclear character with a plausible guess.
3. If the field does not appear anywhere, set "legibility": "absent" and "value": null.
   If it appears but cannot be read, set "legibility": "illegible" and "value": null.
4. "value" is your best reading of the field (same script as the deed). "verbatim" is the exact
   characters you see, with [?] for unclear characters.
5. "alternatives": other plausible readings of unclear handwriting (empty list if none).
6. "confidence": honest probability 0-100 that "value" is correct character by character.
7. "page": 0-based page index. "bbox": [x0, y0, x1, y1] of where you read it, scaled 0-1000 on that page.
8. Numbers written both in digits and in words must be reported separately in the digit field and the
   words field. Do not compute or convert anything.
9. "schedule_rows": one row per schedule (তফসিল) line: khatian, dag, area exactly as written.
10. "full_transcription": the whole deed transcribed line by line (use [?] for unclear characters).

Fields:
{field_lines}

Return only JSON of this shape:
{{
  "fields": {{
    "<field key>": {{"value": str|null, "verbatim": str|null, "legibility": "clear"|"partial"|"illegible"|"absent",
                     "confidence": int, "alternatives": [str], "page": int, "bbox": [int, int, int, int]}}
  }},
  "schedule_rows": [{{"khatian": str, "dag": str, "area": str}}],
  "full_transcription": str,
  "notes": str
}}"""


def _parse_json(text: str) -> Optional[Dict[str, Any]]:
    if not text:
        return None
    t = text.strip()
    t = re.sub(r"^```(?:json)?\s*|\s*```$", "", t)
    try:
        return json.loads(t)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", t, re.DOTALL)
        if m:
            try:
                return json.loads(m.group(0))
            except json.JSONDecodeError:
                return None
    return None


class GeminiVisionReader:
    """Reads deed page images with a Gemini vision model and returns the parsed JSON (or an error)."""

    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY or os.getenv("GEMINI_API_KEY", "")
        self.primary_model = os.getenv("DEED_VISION_MODEL", "gemini-2.5-pro")
        self.secondary_model = os.getenv("DEED_VISION_MODEL_SECONDARY", "gemini-2.5-flash")

    @property
    def available(self) -> bool:
        return bool(self.api_key)

    def read(self, image_paths: List[str], model: str) -> Dict[str, Any]:
        if not self.available:
            return {"error": "GEMINI_API_KEY not configured"}
        try:
            from google import genai
            from google.genai import types
            client = genai.Client(api_key=self.api_key)
            parts = []
            for p in image_paths:
                with open(p, "rb") as f:
                    mime = "image/png" if p.lower().endswith(".png") else "image/jpeg"
                    parts.append(types.Part.from_bytes(data=f.read(), mime_type=mime))
            parts.append(_vision_prompt())
            resp = client.models.generate_content(
                model=model,
                contents=parts,
                config=types.GenerateContentConfig(temperature=0, response_mime_type="application/json"),
            )
            data = _parse_json(resp.text)
            if not data or "fields" not in data:
                return {"error": "vision model returned unparseable output", "model": model}
            data["model"] = model
            return data
        except Exception as e:  # network, quota, auth ...
            return {"error": f"{type(e).__name__}: {e}"[:300], "model": model}


def run_local_ocr(image_paths: List[str], timeout: int = 240) -> Dict[str, Any]:
    """Runs EasyOCR in a child process. Returns {'pages': [...]} or {'error': ...}."""
    if os.getenv("LOCAL_OCR_ENABLED", "1") != "1":
        return {"error": "local OCR disabled"}
    try:
        import importlib.util
        if importlib.util.find_spec("easyocr") is None:
            return {"error": "easyocr not installed"}
    except Exception:
        return {"error": "easyocr not installed"}
    backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    try:
        proc = subprocess.run(
            [sys.executable, "-m", "app.services.local_ocr_worker", *image_paths],
            cwd=backend_dir, capture_output=True, timeout=timeout,
            env={**os.environ, "PYTHONIOENCODING": "utf-8"},
        )
    except subprocess.TimeoutExpired:
        return {"error": "local OCR timed out"}
    if proc.returncode != 0:
        return {"error": f"local OCR process failed (exit {proc.returncode}); usually not enough free memory"}
    data = _parse_json(proc.stdout.decode("utf-8", errors="replace"))
    return data or {"error": "local OCR returned no output"}


# Label patterns for pulling candidate readings out of (noisy) local OCR text. The deed-word patterns
# tolerate common OCR slips (e.g. 'দলিল' read as 'দালল').
_OCR_FIELD_PATTERNS: List[Tuple[str, str]] = [
    ("deed_number", r"(?:দ\S{0,2}ল\S{0,2}ল?\s*(?:নং|নম্বর)|deed\s*no\.?)\s*[:\-]?\s*([০-৯0-9][০-৯0-9/\s\-]{0,14}[০-৯0-9])"),
    ("sub_registry_office", r"সাব[\-\s]?রে\S*\s*অ\S*স\s*[:\-]?\s*([^,;।\n]{2,40})"),
    ("district", r"জেলা\s*[:\-]\s*([^\s,;।\n]{2,20})"),
    ("seller_names", r"(?:দাতা|বিক্রেতা)\s*[:\-]\s*([^,;।\n]{3,80})"),
    ("buyer_names", r"(?:গ্রহীতা|ক্রেতা)\s*[:\-]\s*([^,;।\n]{3,80})"),
    ("mouza", r"[ময]ৌজা\s*[:\-;]?\s*([^\s,;।\n]{2,30})"),
    ("jl_no", r"জে\.?\s*এল\.?\s*(?:নং)?\s*[:\-]?\s*([০-৯0-9]{1,5})"),
    ("khatian_cs", r"সি\.?\s*এস\.?\s*খত\S*\s*(?:নং)?\s*[:\-]?\s*([০-৯0-9][০-৯0-9/,\s]{0,20})"),
    ("khatian_sa", r"এস\.?\s*এ\.?\s*খত\S*\s*(?:নং)?\s*[:\-]?\s*([০-৯0-9][০-৯0-9/,\s]{0,20})"),
    ("khatian_rs", r"আর\.?\s*এস\.?\s*খত\S*\s*(?:নং)?\s*[:\-]?\s*([০-৯0-9][০-৯0-9/,\s]{0,20})"),
    ("khatian_bs", r"বি\.?\s*এস\.?\s*খত\S*\s*(?:নং)?\s*[:\-]?\s*([০-৯0-9][০-৯0-9/,\s]{0,20})"),
    ("dag_numbers", r"দাগ\s*(?:নং)?\s*[:\-]?\s*([০-৯0-9][০-৯0-9/,\s]{0,20})"),
    ("land_area", r"([০-৯0-9]+(?:[\.\s][০-৯0-9]+)?\s*(?:শতাংশ|শতক|একর|অযুতাংশ|কাঠা|বিঘা))"),
    ("consideration_amount", r"পণ\s*মূল্য\s*[:\-]?\s*([০-৯0-9][০-৯0-9,\.]*\s*/?-?)"),
]


def _ocr_candidate_pass(ocr_lines: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    Turns local OCR lines into candidate field readings. Used only when no vision model is available;
    every such field stays 'needs_review' because local OCR is not reliable on handwriting.
    """
    if not ocr_lines:
        return None
    fields: Dict[str, Any] = {}
    parentage: List[Tuple[Dict[str, Any], str]] = []
    for line in ocr_lines:
        text = normalize_bangla(line.get("text", ""))
        conf = int(min(60, float(line.get("conf", 0)) * 100))
        for key, pat in _OCR_FIELD_PATTERNS:
            if key in fields:
                continue
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                value = m.group(1).strip(" ,;:-")
                if value:
                    fields[key] = {"value": value, "verbatim": text, "legibility": "partial", "confidence": conf,
                                   "alternatives": [], "page": line.get("page", 0), "bbox_px": line.get("bbox")}
        for m in re.finditer(r"পিতা\s*[:\-]?\s*([^,;।\n]{3,50})", text):
            parentage.append((line, m.group(1).strip(" ,;:-")))
    for key, (line, value) in zip(("seller_parentage", "buyer_parentage"), parentage):
        fields[key] = {"value": value, "verbatim": line.get("text"), "legibility": "partial",
                       "confidence": int(min(60, float(line.get("conf", 0)) * 100)), "alternatives": [],
                       "page": line.get("page", 0), "bbox_px": line.get("bbox")}
    if not fields:
        return None
    return {"fields": fields, "schedule_rows": [], "model": "local_ocr", "notes": "স্থানীয় OCR থেকে সম্ভাব্য পাঠ"}


def _field_from_pass(data: Optional[Dict[str, Any]], key: str) -> Dict[str, Any]:
    if not data or "error" in data:
        return {}
    f = (data.get("fields") or {}).get(key) or {}
    value = f.get("value")
    if isinstance(value, (int, float)):
        value = str(value)
    if isinstance(value, str):
        value = normalize_bangla(value) or None
    return {
        "value": value,
        "verbatim": f.get("verbatim"),
        "legibility": f.get("legibility") or ("absent" if value is None else "clear"),
        "confidence": int(f.get("confidence") or 0),
        "alternatives": [normalize_bangla(a) for a in (f.get("alternatives") or []) if isinstance(a, str) and a.strip()],
        "page": int(f.get("page") or 0),
        "bbox": f.get("bbox") if isinstance(f.get("bbox"), list) and len(f.get("bbox")) == 4 else None,
        "bbox_px": f.get("bbox_px"),
        "source": data.get("model"),
    }


def _has_uncertain_marker(text: Optional[str]) -> bool:
    return bool(text) and "[?]" in text


def _ocr_support(value: Optional[str], ocr_text_key: str) -> Optional[bool]:
    """True if the reading (or its digits) appears in the local OCR text; None if nothing to compare."""
    if not value or not ocr_text_key:
        return None
    digits = re.sub(r"\D", "", normalize_digits(value))
    if len(digits) >= 2:
        return digits in re.sub(r"\D", "", ocr_text_key)
    key = loose_key(value)
    return key in ocr_text_key if len(key) >= 4 else None


def reconcile_field(key: str, a: Dict[str, Any], b: Dict[str, Any], single_reader: bool, ocr_key: str) -> Dict[str, Any]:
    va, vb = a.get("value"), b.get("value")
    readings = [r for r in (a, b) if r]
    alternatives: List[str] = []
    for r in readings:
        for v in [r.get("value"), *r.get("alternatives", [])]:
            if v and v not in alternatives:
                alternatives.append(v)

    legibilities = {r.get("legibility") for r in readings}
    notes: List[str] = []

    if not readings:
        status, value, conf = "not_found", None, 0
    elif all(r.get("legibility") == "absent" and not r.get("value") for r in readings):
        status, value, conf = "not_found", None, 0
    elif "illegible" in legibilities and not (va or vb):
        status, value, conf = "illegible", None, 0
        notes.append("পাঠক এই অংশ অস্পষ্ট/অপাঠ্য বলে চিহ্নিত করেছে — মূল দলিল বা বালাম বহি থেকে পড়ুন")
    elif single_reader:
        r = readings[0]
        status, value, conf = "needs_review", r.get("value"), r.get("confidence", 0)
        if r.get("source") == "local_ocr":
            notes.append("শুধু স্থানীয় OCR-এর সম্ভাব্য পাঠ — হাতের লেখায় এটি প্রায়ই ভুল করে; ছবির সাথে অক্ষর ধরে মিলিয়ে দেখুন")
        else:
            notes.append("মাত্র একটি পাঠক উপলব্ধ ছিল — দ্বিতীয় স্বাধীন পাঠ ছাড়া নিশ্চিত করা যায়নি")
    elif va and vb and comparison_key(va) == comparison_key(vb):
        conf = min(a.get("confidence", 0), b.get("confidence", 0))
        value = va
        clean = a.get("legibility") == "clear" and b.get("legibility") == "clear" and not (
            _has_uncertain_marker(a.get("verbatim")) or _has_uncertain_marker(b.get("verbatim")))
        if clean and conf >= AGREEMENT_MIN_CONFIDENCE:
            status = "machine_agreed"
            notes.append("দুটি স্বাধীন পাঠ হুবহু মিলেছে")
        else:
            status = "needs_review"
            notes.append("দুটি পাঠ মিলেছে, তবে হাতের লেখা আংশিক অস্পষ্ট বা আস্থা কম")
    else:
        value = va or vb
        conf = min(a.get("confidence", 0) or 0, b.get("confidence", 0) or 0) // 2
        status = "needs_review"
        if va and vb:
            notes.append(f"দুই পাঠে ভিন্নতা: '{va}' বনাম '{vb}'")
        else:
            notes.append("একটি পাঠ এই তথ্য পায়নি — অন্য পাঠের মান যাচাই করুন")
        if "illegible" in legibilities or "partial" in legibilities:
            notes.append("হাতের লেখা আংশিক অস্পষ্ট")

    src = a if (a.get("bbox") or a.get("bbox_px")) else b
    support = _ocr_support(value, ocr_key)
    if support is True:
        notes.append("স্থানীয় OCR-এও এই পাঠ পাওয়া গেছে (দুর্বল সমর্থন)")

    return {
        "field": key,
        "title_bn": FIELD_LABELS.get(key, key),
        "kind": FIELD_KINDS.get(key, "text"),
        "critical": key in CRITICAL_FIELDS,
        "value": value,
        "status": status,
        "confidence": int(conf or 0),
        "alternatives": alternatives[:5],
        "verbatim": [r.get("verbatim") for r in readings if r.get("verbatim")],
        "page": (src or {}).get("page", 0),
        "bbox_norm": (src or {}).get("bbox"),
        "bbox": (src or {}).get("bbox_px"),
        "ocr_support": support,
        "checks": [],
        "notes": notes,
    }


def _add_check(field: Dict[str, Any], ok: bool, message: str):
    field["checks"].append({"ok": ok, "message_bn": message})
    if not ok and field["status"] == "machine_agreed":
        field["status"] = "needs_review"


def run_consistency_checks(fields: Dict[str, Dict[str, Any]], schedule_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Deterministic legal/arithmetical checks. Mutates field statuses; returns document-level findings."""
    findings: List[Dict[str, Any]] = []

    def val(k):
        return (fields.get(k) or {}).get("value")

    # 1. Land area: digits vs words
    area_d = parse_land_area(val("land_area") or "")
    area_w = parse_land_area(val("land_area_words") or "")
    for k, parsed in (("land_area", area_d), ("land_area_words", area_w)):
        for note in parsed["notes"]:
            _add_check(fields[k], False, note)
    if area_d["decimals"] is not None and area_w["decimals"] is not None:
        if abs(area_d["decimals"] - area_w["decimals"]) < 0.001:
            msg = f"অংকে ও কথায় লেখা জমির পরিমাণ মিলেছে ({area_d['decimals']:g} শতাংশ)"
            _add_check(fields["land_area"], True, msg)
            _add_check(fields["land_area_words"], True, msg)
        else:
            msg = f"অংকে ({area_d['decimals']:g} শতাংশ) ও কথায় ({area_w['decimals']:g} শতাংশ) লেখা জমির পরিমাণ মিলছে না"
            _add_check(fields["land_area"], False, msg)
            _add_check(fields["land_area_words"], False, msg)
            findings.append({"severity": "high", "message_bn": msg})
    elif val("land_area") and area_d["decimals"] is None:
        _add_check(fields["land_area"], False, "জমির পরিমাণ থেকে সংখ্যা ও একক (শতাংশ/একর/কাঠা) আলাদা করা যায়নি")
    if area_d["decimals"] is not None:
        if area_d["decimals"] <= 0:
            _add_check(fields["land_area"], False, "জমির পরিমাণ শূন্য — সঠিক নয়")
        elif area_d["decimals"] > 10000:
            _add_check(fields["land_area"], False, "জমির পরিমাণ ১০০ একরের বেশি — অস্বাভাবিক, পুনরায় পড়ুন")

    # 2. Sum of schedule rows vs total area
    row_total, rows_parsed = 0.0, 0
    for row in schedule_rows or []:
        parsed = parse_land_area(str(row.get("area") or ""))
        if parsed["decimals"] is not None:
            row_total += parsed["decimals"]
            rows_parsed += 1
    if rows_parsed >= 2 and area_d["decimals"] is not None:
        if abs(row_total - area_d["decimals"]) < 0.01:
            _add_check(fields["land_area"], True, f"তফসিলের দাগওয়ারি জমির যোগফল ({row_total:g}) মোট পরিমাণের সাথে মিলেছে")
        else:
            msg = f"তফসিলের দাগওয়ারি জমির যোগফল ({row_total:g} শতাংশ) মোট পরিমাণের ({area_d['decimals']:g} শতাংশ) সাথে মিলছে না"
            _add_check(fields["land_area"], False, msg)
            findings.append({"severity": "high", "message_bn": msg})

    # 3. Consideration: digits vs words
    amt_d = parse_first_number(val("consideration_amount") or "")
    amt_w = parse_bangla_number_words(val("consideration_words") or "")
    if amt_d is not None and amt_w is not None:
        if abs(amt_d - amt_w) < 0.5:
            msg = f"অংকে ও কথায় লেখা পণমূল্য মিলেছে ({amt_d:,.0f} টাকা)"
            _add_check(fields["consideration_amount"], True, msg)
            _add_check(fields["consideration_words"], True, msg)
        else:
            msg = f"অংকে ({amt_d:,.0f}) ও কথায় ({amt_w:,.0f}) লেখা পণমূল্য মিলছে না"
            _add_check(fields["consideration_amount"], False, msg)
            _add_check(fields["consideration_words"], False, msg)
            findings.append({"severity": "high", "message_bn": msg})

    # 4. Share must not exceed 16 আনা
    share = parse_share(val("share") or "")
    if val("share"):
        if share is None:
            _add_check(fields["share"], False, "হিস্যা আনা-গণ্ডা বা ভগ্নাংশে বোঝা যায়নি")
        elif share > 1.0 + 1e-9:
            msg = "হিস্যা ১৬ আনার বেশি — অসম্ভব, পুনরায় পড়ুন"
            _add_check(fields["share"], False, msg)
            findings.append({"severity": "high", "message_bn": msg})
        else:
            _add_check(fields["share"], True, f"হিস্যা ১৬ আনার মধ্যে ({share * 16:g} আনা)")

    # 5. Dates: Gregorian vs Bengali year, deed-number year vs registration year
    years = extract_years(val("registration_date") or "")
    if years["gregorian"] and years["bengali"]:
        g, bn = years["gregorian"][0], years["bengali"][0]
        if g - bn in (593, 594):
            _add_check(fields["registration_date"], True, "খ্রিষ্টাব্দ ও বঙ্গাব্দ সাল সামঞ্জস্যপূর্ণ")
        else:
            _add_check(fields["registration_date"], False, f"খ্রিষ্টাব্দ {g} ও বঙ্গাব্দ {bn} সামঞ্জস্যপূর্ণ নয় (পার্থক্য ৫৯৩/৫৯৪ হওয়ার কথা)")
    for g in years["gregorian"]:
        if g < 1800 or g > 2100:
            _add_check(fields["registration_date"], False, f"সাল {g} অসম্ভব")
    deed_no = normalize_digits(val("deed_number") or "")
    m = re.search(r"/\s*(\d{2,4})\b", deed_no)
    if m and years["gregorian"]:
        y = int(m.group(1))
        y = y + (1900 if y > 30 else 2000) if y < 100 else y
        if y != years["gregorian"][0]:
            _add_check(fields["deed_number"], False, f"দলিল নম্বরের সাল ({y}) ও রেজিস্ট্রির সাল ({years['gregorian'][0]}) ভিন্ন")

    # 6. Seller and buyer must differ; names must not contain digits
    s_key, b_key = comparison_key(val("seller_names") or ""), comparison_key(val("buyer_names") or "")
    if s_key and b_key and s_key == b_key:
        msg = "দাতা ও গ্রহীতার নাম হুবহু এক — পুনরায় পড়ুন"
        _add_check(fields["seller_names"], False, msg)
        _add_check(fields["buyer_names"], False, msg)
        findings.append({"severity": "high", "message_bn": msg})
    for k in ("seller_names", "buyer_names", "seller_parentage", "buyer_parentage"):
        v = val(k)
        # strip list enumerators such as '১।', '2.', '৩)' before looking for stray digits
        if v and re.search(r"[0-9০-৯]", re.sub(r"[০-৯0-9]+\s*[\.\)।/]", "", v)):
            _add_check(fields[k], False, "নামের মধ্যে সংখ্যা পাওয়া গেছে — ভুল পাঠের লক্ষণ")

    # 7. Survey numbers must contain digits
    for k in ("jl_no", "khatian_cs", "khatian_sa", "khatian_rs", "khatian_bs", "dag_numbers", "deed_number"):
        v = val(k)
        if v and not re.search(r"[0-9০-৯]", v):
            _add_check(fields[k], False, "নম্বরে কোনো অংক পাওয়া যায়নি")

    return findings


def _denormalize_bboxes(fields: Dict[str, Dict[str, Any]], page_sizes: List[Tuple[int, int]]):
    for f in fields.values():
        bn = f.get("bbox_norm")
        page = f.get("page") or 0
        if bn and 0 <= page < len(page_sizes):
            w, h = page_sizes[page]
            try:
                x0, y0, x1, y1 = [max(0, min(1000, int(v))) for v in bn]
                f["bbox"] = [int(x0 * w / 1000), int(y0 * h / 1000), int(x1 * w / 1000), int(y1 * h / 1000)]
            except (TypeError, ValueError):
                f["bbox"] = None


def summarize(fields: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    counts = {s: 0 for s in ("human_verified", "machine_agreed", "needs_review", "illegible", "not_found")}
    for f in fields.values():
        counts[f["status"]] = counts.get(f["status"], 0) + 1
    # A critical field is settled only when a person has confirmed it — including confirming that it is
    # genuinely absent from the deed (verified with an empty value). "Not found by the machine" is not enough.
    critical_open = [k for k, f in fields.items() if f["critical"] and f["status"] != "human_verified"]
    critical_missing = [k for k, f in fields.items() if f["critical"] and f["status"] == "not_found"]
    return {
        "counts": counts,
        "total_fields": len(fields),
        "critical_pending": critical_open,
        "critical_not_found": critical_missing,
        "fully_verified": not critical_open,
    }


class DeedReadingService:
    def __init__(self):
        self.vision = GeminiVisionReader()

    def engine_status(self) -> Dict[str, Any]:
        import importlib.util
        local = importlib.util.find_spec("easyocr") is not None and os.getenv("LOCAL_OCR_ENABLED", "1") == "1"
        mode = "dual_vision" if self.vision.available else ("local_ocr_only" if local else "manual_only")
        return {
            "mode": mode,
            "vision_available": self.vision.available,
            "primary_model": self.vision.primary_model if self.vision.available else None,
            "secondary_model": self.vision.secondary_model if self.vision.available else None,
            "local_ocr_available": local,
            "message_bn": {
                "dual_vision": "উচ্চ নির্ভুলতা মোড: দুটি স্বাধীন ভিশন মডেল দলিল পড়ছে, পাঠ মিলিয়ে দেখা হচ্ছে। তবুও প্রতিটি গুরুত্বপূর্ণ তথ্য মানুষের যাচাই প্রয়োজন।",
                "local_ocr_only": "সীমিত মোড: শুধু স্থানীয় OCR চালু। হাতে লেখা বাংলা দলিলে এটি নির্ভরযোগ্য নয় — প্রতিটি তথ্য নিজে পড়ে বসাতে হবে। উচ্চ নির্ভুলতার জন্য GEMINI_API_KEY সেট করুন।",
                "manual_only": "কোনো স্বয়ংক্রিয় পাঠক চালু নেই। তথ্যগুলো ছবির পাশে দেখে নিজে বসাতে হবে। GEMINI_API_KEY সেট করুন।",
            }[mode],
        }

    def read_deed(self, page_paths: List[str], enhanced_paths: Optional[List[str]] = None,
                  page_sizes: Optional[List[Tuple[int, int]]] = None) -> Dict[str, Any]:
        enhanced_paths = enhanced_paths or page_paths
        page_sizes = page_sizes or []
        errors: List[str] = []

        pass_a = pass_b = None
        if self.vision.available:
            pass_a = self.vision.read(page_paths, self.vision.primary_model)
            pass_b = self.vision.read(enhanced_paths, self.vision.secondary_model)
            for p in (pass_a, pass_b):
                if p and "error" in p:
                    errors.append(f"{p.get('model')}: {p['error']}")
        ok_passes = [p for p in (pass_a, pass_b) if p and "error" not in p]

        ocr = run_local_ocr(page_paths)
        ocr_lines: List[Dict[str, Any]] = []
        if "error" in ocr:
            errors.append(f"local OCR: {ocr['error']}")
        else:
            for pi, page in enumerate(ocr.get("pages", [])):
                for line in page.get("lines", []):
                    ocr_lines.append({**line, "page": pi})
        ocr_key = loose_key(" ".join(l["text"] for l in ocr_lines))

        if not ok_passes:
            candidate = _ocr_candidate_pass(ocr_lines)
            if candidate:
                ok_passes = [candidate]
        single = len(ok_passes) < 2
        a = ok_passes[0] if ok_passes else None
        b = ok_passes[1] if len(ok_passes) > 1 else None
        fields: Dict[str, Dict[str, Any]] = {}
        for key, *_ in FIELD_SPECS:
            fields[key] = reconcile_field(key, _field_from_pass(a, key), _field_from_pass(b, key), single, ocr_key)

        schedule_rows = (a or {}).get("schedule_rows") or []
        findings = run_consistency_checks(fields, schedule_rows)
        _denormalize_bboxes(fields, page_sizes)

        transcriptions = [p.get("full_transcription") for p in ok_passes if p.get("full_transcription")]
        ok_passes = [p for p in ok_passes if p.get("model") != "local_ocr"] or ok_passes
        return {
            "engine": self.engine_status(),
            "passes": [{"model": p.get("model"), "notes": p.get("notes")} for p in ok_passes],
            "errors": errors,
            "fields": fields,
            "schedule_rows": schedule_rows,
            "findings": findings,
            "transcription": transcriptions[0] if transcriptions else "\n".join(l["text"] for l in ocr_lines),
            "transcription_source": "vision" if transcriptions else ("local_ocr" if ocr_lines else None),
            "ocr_lines": ocr_lines[:400],
            "summary": summarize(fields),
        }

    @staticmethod
    def apply_human_verification(report: Dict[str, Any], field_key: str, value: Optional[str], verified_by: str) -> Dict[str, Any]:
        """Marks one field as confirmed/corrected by a person, then re-runs all checks."""
        fields = report.get("fields") or {}
        if field_key not in fields:
            raise KeyError(field_key)
        f = fields[field_key]
        previous = f.get("value")
        f["value"] = normalize_bangla(value) if value else None
        f["status"] = "human_verified"
        f["verified_by"] = verified_by
        f["corrected"] = comparison_key(previous or "") != comparison_key(value or "")
        f["previous_machine_value"] = previous
        # Re-run checks from a clean slate; human-verified fields keep their status but show check results
        for fld in fields.values():
            fld["checks"] = []
        report["findings"] = run_consistency_checks(fields, report.get("schedule_rows") or [])
        report["summary"] = summarize(fields)
        return report


def report_to_legacy_record(report: Dict[str, Any]) -> Dict[str, Any]:
    """Maps the reading report onto the existing DeedRecord columns. Unknown values stay None (never invented)."""
    f = report.get("fields") or {}

    def v(k):
        return (f.get(k) or {}).get("value")

    years = extract_years(v("registration_date") or "")
    reg_year = years["gregorian"][0] if years["gregorian"] else None
    area = parse_land_area(v("land_area") or v("land_area_words") or "")
    prior = v("prior_deed")
    prior_years = extract_years(prior or "")
    prior_m = re.search(r"/\s*(\d{4})", normalize_digits(prior or ""))
    prior_year = int(prior_m.group(1)) if prior_m else (prior_years["gregorian"][0] if prior_years["gregorian"] else None)

    deed_type_raw = (v("deed_type") or "")
    deed_type = "saf_kabala"
    if "হেবা" in deed_type_raw:
        deed_type = "heba"
    elif "দান" in deed_type_raw:
        deed_type = "danpatra"
    elif "বণ্টন" in deed_type_raw or "বন্টন" in deed_type_raw:
        deed_type = "bonton_nama"
    elif "এওয়াজ" in deed_type_raw or "বিনিময়" in deed_type_raw:
        deed_type = "ewaz"
    elif not deed_type_raw:
        deed_type = "unknown"

    unclear = []
    for k, fld in f.items():
        if fld["status"] in ("needs_review", "illegible"):
            unclear.append({
                "term_location": fld["title_bn"],
                "raw_ocr_snippet": (fld.get("verbatim") or [""])[0] or "",
                "extracted_reading": fld.get("value") or "[অপাঠ্য]",
                "confidence_score": fld.get("confidence", 0),
                "alternatives": fld.get("alternatives") or [],
                "guidance": "; ".join(fld.get("notes", []) + [c["message_bn"] for c in fld.get("checks", []) if not c["ok"]]),
            })

    conf_values = [fld["confidence"] for fld in f.values() if fld["status"] != "not_found"]
    overall = int(sum(conf_values) / len(conf_values)) if conf_values else 0
    return {
        "deed_type": deed_type,
        "deed_number": v("deed_number"),
        "registration_year": reg_year,
        "registration_date": v("registration_date"),
        "sub_registry_office": v("sub_registry_office"),
        "district": v("district"),
        "thana": v("thana"),
        "mouza": v("mouza"),
        "jl_number": v("jl_no"),
        "parties": {
            "first_party_name": v("seller_names"),
            "first_party_father": v("seller_parentage"),
            "first_party_address": v("seller_address"),
            "second_party_name": v("buyer_names"),
            "second_party_father": v("buyer_parentage"),
            "second_party_address": v("buyer_address"),
            "identifier_name": v("identifier"),
            "deed_writer_name": v("deed_writer"),
            "witnesses": v("witnesses"),
        },
        "schedule": {
            "mouza": v("mouza"),
            "jl_no": v("jl_no"),
            "khatian_cs": v("khatian_cs"),
            "khatian_sa": v("khatian_sa"),
            "khatian_rs": v("khatian_rs"),
            "khatian_bs": v("khatian_bs"),
            "dag_former": v("dag_numbers"),
            "dag_current": None,
            "land_class": v("land_class"),
            "transferred_area_decimals": area["decimals"],
            "transferred_area_bangla": v("land_area") or v("land_area_words"),
            "share_portion": v("share"),
        },
        "boundaries": {
            "north": v("boundary_north"),
            "south": v("boundary_south"),
            "east": v("boundary_east"),
            "west": v("boundary_west"),
        },
        "financials": {
            "consideration_amount_bdt": parse_first_number(v("consideration_amount") or ""),
            "consideration_in_words": v("consideration_words"),
            "stamp_value_bdt": parse_first_number(v("stamp_value") or ""),
        },
        "chain_of_title": {
            "prior_deed_number": prior,
            "prior_deed_year": prior_year,
            "prior_owner_name": v("prior_owner"),
            "acquired_share": None,
        },
        "unclear_texts": unclear,
        "overall_confidence_score": overall,
        "clarity_rating": "high" if overall >= 85 else "moderate" if overall >= 60 else "faded_unclear",
    }


deed_reading_service = DeedReadingService()
