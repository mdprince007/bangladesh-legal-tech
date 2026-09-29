"""
Bangla text utilities for reading land deeds and legal facts.

Everything here is deterministic so that numbers read from a deed can be cross-checked
(e.g. land area written in digits vs. in words) without trusting any single reader.
"""
import re
import unicodedata
from typing import Any, Dict, List, Optional, Tuple

BN_DIGITS = "০১২৩৪৫৬৭৮৯"
_BN_TO_EN = str.maketrans(BN_DIGITS, "0123456789")
_EN_TO_BN = str.maketrans("0123456789", BN_DIGITS)


def normalize_digits(text: str) -> str:
    """Bengali digits -> ASCII digits."""
    return (text or "").translate(_BN_TO_EN)


def to_bangla_digits(value: Any) -> str:
    return str(value).translate(_EN_TO_BN)


def normalize_bangla(text: str) -> str:
    """
    Canonical form for comparing two readings of the same text:
    NFC, precomposed য়/ড়/ঢ়, no zero-width joiners, collapsed whitespace.
    """
    if not text:
        return ""
    s = unicodedata.normalize("NFC", str(text))
    s = s.replace("য়", "য়").replace("ড়", "ড়").replace("ঢ়", "ঢ়")
    s = s.replace("‌", "").replace("‍", "")
    return re.sub(r"\s+", " ", s).strip()


def comparison_key(text: str) -> str:
    """
    Key used to decide whether two readings agree. Ignores punctuation, spacing and digit script,
    but NOT spelling: 'খাঁন' vs 'খান' are different names in land records and must be flagged.
    """
    s = normalize_digits(normalize_bangla(text)).lower()
    return re.sub(r"[\s\.,;:।\-–—/()\[\]'\"`]+", "", s)


def loose_key(text: str) -> str:
    """Looser key (also ignores chandrabindu and ঊ/উ) used only to find a reading inside noisy OCR text."""
    return comparison_key(text).replace("ঁ", "").replace("ঊ", "উ")


# ---------------------------------------------------------------------------
# Number words (Bangla spoken/written numbers as used in deeds)
# ---------------------------------------------------------------------------
_UNITS_1_TO_99 = [
    "এক", "দুই", "তিন", "চার", "পাঁচ", "ছয়", "সাত", "আট", "নয়", "দশ",
    "এগারো", "বারো", "তেরো", "চৌদ্দ", "পনেরো", "ষোলো", "সতেরো", "আঠারো", "উনিশ", "বিশ",
    "একুশ", "বাইশ", "তেইশ", "চব্বিশ", "পঁচিশ", "ছাব্বিশ", "সাতাশ", "আটাশ", "ঊনত্রিশ", "ত্রিশ",
    "একত্রিশ", "বত্রিশ", "তেত্রিশ", "চৌত্রিশ", "পঁয়ত্রিশ", "ছত্রিশ", "সাঁইত্রিশ", "আটত্রিশ", "ঊনচল্লিশ", "চল্লিশ",
    "একচল্লিশ", "বিয়াল্লিশ", "তেতাল্লিশ", "চুয়াল্লিশ", "পঁয়তাল্লিশ", "ছেচল্লিশ", "সাতচল্লিশ", "আটচল্লিশ", "ঊনপঞ্চাশ", "পঞ্চাশ",
    "একান্ন", "বাহান্ন", "তিপ্পান্ন", "চুয়ান্ন", "পঞ্চান্ন", "ছাপ্পান্ন", "সাতান্ন", "আটান্ন", "ঊনষাট", "ষাট",
    "একষট্টি", "বাষট্টি", "তেষট্টি", "চৌষট্টি", "পঁয়ষট্টি", "ছেষট্টি", "সাতষট্টি", "আটষট্টি", "ঊনসত্তর", "সত্তর",
    "একাত্তর", "বাহাত্তর", "তিয়াত্তর", "চুয়াত্তর", "পঁচাত্তর", "ছিয়াত্তর", "সাতাত্তর", "আটাত্তর", "ঊনআশি", "আশি",
    "একাশি", "বিরাশি", "তিরাশি", "চুরাশি", "পঁচাশি", "ছিয়াশি", "সাতাশি", "অষ্টাশি", "ঊননব্বই", "নব্বই",
    "একানব্বই", "বিরানব্বই", "তিরানব্বই", "চুরানব্বই", "পঁচানব্বই", "ছিয়ানব্বই", "সাতানব্বই", "আটানব্বই", "নিরানব্বই",
]
# Older / regional spellings that appear in handwritten deeds
_VARIANTS = {
    "দু": 2, "দুয়ে": 2, "চারি": 4, "পাচ": 5, "ছ": 6, "ছয়": 6, "নও": 9,
    "এগার": 11, "বার": 12, "তের": 13, "চৌদ্দো": 14, "পনের": 15, "ষোল": 16, "ষোলো": 16, "সতের": 17, "আঠার": 18,
    "শূন্য": 0, "শুন্য": 0,
}
_NUMBER_WORDS: Dict[str, float] = {}
for _i, _w in enumerate(_UNITS_1_TO_99, start=1):
    _NUMBER_WORDS[_w] = _i
for _w, _v in _VARIANTS.items():
    _NUMBER_WORDS[_w] = _v
_NUMBER_WORDS.update({"দেড়": 1.5, "আড়াই": 2.5})

_MODIFIERS = {"সাড়ে": 0.5, "সোয়া": 0.25, "পৌনে": -0.25}
_HUNDRED = {"শত", "শো", "শ", "শতাধিক"}
_SCALES = {"হাজার": 1_000, "লক্ষ": 100_000, "লাখ": 100_000, "লক্ষ্য": 100_000, "কোটি": 10_000_000}
_DECIMAL_WORDS = {"দশমিক", "পয়েন্ট", "পয়েন্ট"}
_FILLER = {"মাত্র", "টাকা", "টাকার", "পয়সা", "শতাংশ", "শতক", "একর", "কাঠা", "বিঘা", "ও", "এবং", "সহ"}


def _word_key(w: str) -> str:
    return normalize_bangla(w).replace("ঁ", "").replace("ঊ", "উ")


_NUMBER_KEYS = {_word_key(k): v for k, v in _NUMBER_WORDS.items()}
_MODIFIER_KEYS = {_word_key(k): v for k, v in _MODIFIERS.items()}
_SCALE_KEYS = {_word_key(k): v for k, v in _SCALES.items()}
_HUNDRED_KEYS = {_word_key(k) for k in _HUNDRED}
_DECIMAL_KEYS = {_word_key(k) for k in _DECIMAL_WORDS}
_FILLER_KEYS = {_word_key(k) for k in _FILLER}


def _tokenize_number_words(text: str) -> List[str]:
    s = normalize_bangla(text)
    s = re.sub(r"[,\.।;:()\[\]/\-–—]", " ", s)
    # Split glued scale words: "পাঁচশত" -> "পাঁচ শত", "তিনহাজার" -> "তিন হাজার"
    # (not inside land units such as 'শতক'/'শতাংশ')
    s = re.sub(r"(?<=[ঀ-৿])(শত|শো|হাজার|লক্ষ|লাখ|কোটি)(?!ক|াংশ|াধিক|্)", r" \1 ", s)
    return [t for t in s.split() if t]


def parse_bangla_number_words(text: str) -> Optional[float]:
    """
    Parses a Bangla number written in words, e.g.
    'আটচল্লিশ হাজার টাকা মাত্র' -> 48000, 'সাড়ে বারো শতক' -> 12.5,
    'এক লক্ষ পঁচিশ হাজার' -> 125000, 'বারো দশমিক পাঁচ শূন্য' -> 12.5.
    Returns None if no number word is present or an unknown word sits inside the number.
    """
    tokens = _tokenize_number_words(text)
    total = 0.0
    group = 0.0
    found = False
    pending_modifier = 0.0
    decimal_digits: Optional[List[str]] = None

    for raw in tokens:
        tok = _word_key(raw)
        if decimal_digits is not None:
            if tok in _NUMBER_KEYS and _NUMBER_KEYS[tok] < 10 and float(_NUMBER_KEYS[tok]).is_integer():
                decimal_digits.append(str(int(_NUMBER_KEYS[tok])))
                continue
            break
        if tok in _MODIFIER_KEYS:
            pending_modifier = _MODIFIER_KEYS[tok]
            continue
        if tok in _NUMBER_KEYS:
            group += _NUMBER_KEYS[tok] + pending_modifier
            pending_modifier = 0.0
            found = True
        elif tok in _HUNDRED_KEYS:
            group = (group or 1) * 100
            found = True
        elif tok in _SCALE_KEYS:
            total += (group or 1) * _SCALE_KEYS[tok]
            group = 0.0
            found = True
        elif tok in _DECIMAL_KEYS:
            decimal_digits = []
        elif tok in _FILLER_KEYS:
            continue
        elif found:
            # an unknown word after the number started ends the number phrase
            break

    if not found:
        return None
    value = total + group
    if decimal_digits:
        value = float(f"{int(value)}.{''.join(decimal_digits)}")
    return value


def parse_first_number(text: str) -> Optional[float]:
    """First numeric value written in digits (Bangla or ASCII), tolerant of lakh-style commas and '/-'."""
    s = normalize_digits(text or "")
    m = re.search(r"\d[\d,]*(?:\.\d+)?", s)
    if not m:
        return None
    try:
        return float(m.group(0).replace(",", ""))
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# Land area
# ---------------------------------------------------------------------------
# Factor to convert each unit into decimals (শতাংশ). 1 acre = 100 decimals = 43,560 sft.
LAND_UNITS: List[Tuple[str, float, Optional[str]]] = [
    ("অযুতাংশ", 0.01, None),
    ("শতাংশ", 1.0, None),
    ("শতক", 1.0, None),
    ("ডেসিমাল", 1.0, None),
    ("ডেসিমেল", 1.0, None),
    ("decimal", 1.0, None),
    ("একর", 100.0, None),
    ("acre", 100.0, None),
    ("বিঘা", 33.0, "বিঘার মাপ অঞ্চলভেদে ভিন্ন (প্রমিত ১ বিঘা = ৩৩ শতাংশ ধরা হয়েছে) — স্থানীয় মাপ যাচাই করুন"),
    ("কাঠা", 1.65, "১ কাঠা = ৭২০ বর্গফুট = প্রায় ১.৬৫ শতাংশ ধরা হয়েছে — স্থানীয় মাপ যাচাই করুন"),
    ("ছটাক", 0.103, "১ ছটাক = ৪৫ বর্গফুট ধরা হয়েছে"),
    ("বর্গফুট", 1 / 435.6, None),
    ("sft", 1 / 435.6, None),
]
_REGIONAL_UNITS = ["গণ্ডা", "কানি", "দোন", "কড়া"]


def parse_land_area(text: str) -> Dict[str, Any]:
    """
    Parses a land area such as '১২.৫০ শতাংশ', '১ একর ২০ শতক', 'দেড় কাঠা'.
    Returns {'decimals': float|None, 'parts': [...], 'notes': [...], 'from_words': bool}.
    Area in words is parsed too, so digits and words can be compared.
    """
    result: Dict[str, Any] = {"decimals": None, "parts": [], "notes": [], "from_words": False}
    if not text:
        return result
    s = normalize_digits(normalize_bangla(text))

    unit_alt = "|".join(re.escape(u) for u, _, _ in LAND_UNITS)
    total = 0.0
    for m in re.finditer(rf"(\d[\d,]*(?:\.\d+)?)\s*({unit_alt})", s, re.IGNORECASE):
        qty = float(m.group(1).replace(",", ""))
        unit = m.group(2).lower()
        factor, note = next((f, n) for u, f, n in LAND_UNITS if u.lower() == unit)
        total += qty * factor
        result["parts"].append({"quantity": qty, "unit": m.group(2), "decimals": round(qty * factor, 4)})
        if note and note not in result["notes"]:
            result["notes"].append(note)

    if not result["parts"]:
        # Area written only in words, e.g. 'বারো শতক' / 'সাড়ে তিন কাঠা'
        for unit, factor, note in LAND_UNITS:
            idx = s.find(unit)
            if idx > 0:
                qty = parse_bangla_number_words(s[:idx].split(",")[-1])
                if qty is not None:
                    total += qty * factor
                    result["parts"].append({"quantity": qty, "unit": unit, "decimals": round(qty * factor, 4)})
                    result["from_words"] = True
                    if note:
                        result["notes"].append(note)
                    break

    for ru in _REGIONAL_UNITS:
        if ru in s:
            result["notes"].append(f"'{ru}' আঞ্চলিক একক — শতাংশে রূপান্তর স্বয়ংক্রিয়ভাবে করা হয়নি, হাতে যাচাই করুন")

    if result["parts"]:
        result["decimals"] = round(total, 4)
    return result


# ---------------------------------------------------------------------------
# Share (হিস্যা): আনা - গণ্ডা - কড়া - ক্রান্তি, out of ১৬ আনা
# ---------------------------------------------------------------------------
_SHARE_UNITS = [("আনা", 1.0), ("গণ্ডা", 1 / 20), ("গন্ডা", 1 / 20), ("কড়া", 1 / 80), ("কড়া", 1 / 80), ("ক্রান্তি", 1 / 240), ("কান্তি", 1 / 240)]


def parse_share(text: str) -> Optional[float]:
    """
    Returns the share as a fraction of the whole (16 আনা = 1.0), or None if not parseable.
    Supports '৮ আনা', '১০ আনা ৩ গণ্ডা ২ কড়া', '১/২ অংশ'.
    """
    if not text:
        return None
    s = normalize_digits(normalize_bangla(text))
    annas = 0.0
    found = False
    for unit, factor in _SHARE_UNITS:
        for m in re.finditer(rf"(\d+(?:\.\d+)?)\s*{unit}", s):
            annas += float(m.group(1)) * factor
            found = True
    if found:
        return annas / 16.0
    frac = re.search(r"(\d+)\s*/\s*(\d+)\s*(?:অংশ|হিস্যা|ভাগ)", s)
    if frac and int(frac.group(2)) != 0:
        return int(frac.group(1)) / int(frac.group(2))
    return None


# ---------------------------------------------------------------------------
# Dates / years
# ---------------------------------------------------------------------------
def extract_years(text: str) -> Dict[str, List[int]]:
    """Finds Gregorian (খ্রিঃ/ইং) and Bengali-calendar (বাং/বঙ্গাব্দ) years in a date string."""
    s = normalize_digits(normalize_bangla(text or ""))
    greg, beng = [], []
    for m in re.finditer(r"(\d{4})\s*(বাং|বঙ্গাব্দ|সাল\s*বাং)", s):
        beng.append(int(m.group(1)))
    for m in re.finditer(r"\b(1[89]\d{2}|20\d{2})\b", s):
        y = int(m.group(1))
        if y not in beng:
            greg.append(y)
    # Two-part dates like 20/04/1993 or 20.04.93
    for m in re.finditer(r"\b\d{1,2}[\./-]\d{1,2}[\./-](\d{2,4})\b", s):
        y = int(m.group(1))
        if y < 100:
            y += 1900 if y > 30 else 2000
        if y not in greg and y not in beng:
            greg.append(y)
    return {"gregorian": greg, "bengali": beng}
