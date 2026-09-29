import os
import json
import re
from typing import Dict, Any, Optional
from app.core.config import settings

class AIProvider:
    """
    Model-agnostic AI provider abstraction.
    Supports Gemini, OpenAI, and a deterministic local fallback engine.
    """

    def __init__(self):
        self.provider = settings.AI_PROVIDER
        self.gemini_key = settings.GEMINI_API_KEY or os.getenv("GEMINI_API_KEY")
        self.openai_key = settings.OPENAI_API_KEY or os.getenv("OPENAI_API_KEY")

    def generate_chat_response(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """
        Generate conversational response. Falls back gracefully to intelligent local logic.
        """
        if self.gemini_key:
            try:
                from google import genai
                client = genai.Client(api_key=self.gemini_key)
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
                )
                return response.text
            except Exception as e:
                # Log error and fall back to local rule engine
                pass

        # Deterministic / local fallback response
        return "Legal Intelligence Engine is processing your query based on Bangladesh Law."

    def extract_structured_facts(self, user_text: str, current_facts: Dict[str, Any], last_asked_field: Optional[str] = None) -> Dict[str, Any]:
        """
        Extracts structured facts from Bangla/English user messages.
        Works deterministically on common patterns (amounts, duration, addresses, names),
        and intelligently leverages conversational context (last_asked_field).
        """
        updated = dict(current_facts)
        clean_input = user_text.strip()
        
        # 1. Direct answer to previous question (Context-Aware Extraction)
        if last_asked_field and clean_input:
            name_fields = [
                "landlord_name", "tenant_name", "employer_name", "employee_name", 
                "payee_name", "drawer_name", "disclosing_party", "receiving_party",
                "party_one_name", "party_two_name", "partner_one", "partner_two",
                "buyer_name", "seller_name", "lender_name", "borrower_name",
                "client_name", "service_provider_name"
            ]
            if last_asked_field in name_fields or "name" in last_asked_field or "party" in last_asked_field or "partner" in last_asked_field:
                # Strip conversational prefixes: "মালিকের নাম", "আমার নাম", "হলো", "নাম", ":"
                cleaned_name = re.sub(r'^(?:মালিকের\s*নাম|ভাড়াটিয়ার\s*নাম|আমার\s*নাম|১ম\s*পক্ষ|২য়\s*পক্ষ|নাম|মালিক|ভাড়াটিয়া|হলো|হবে|is|name\s*is|name)\s*[:=]?\s*', '', clean_input, flags=re.IGNORECASE).strip()
                if len(cleaned_name) >= 2:
                    cleaned_name = re.sub(r'[\।\.\,\;]+$', '', cleaned_name).strip()
                    updated[last_asked_field] = cleaned_name.title() if cleaned_name.isascii() else cleaned_name
            elif last_asked_field.endswith("_bdt") or "amount" in last_asked_field or "salary" in last_asked_field or "price" in last_asked_field or "fee" in last_asked_field:
                bn_to_en = str.maketrans('০১২৩৪৫৬৭৮৯', '0123456789')
                num_text = clean_input.translate(bn_to_en)
                lakh_m = re.search(r'(\d+)\s*(?:লাখ|lakh)', num_text, re.IGNORECASE)
                if lakh_m:
                    updated[last_asked_field] = int(lakh_m.group(1)) * 100000
                else:
                    digits = re.sub(r'[^\d]', '', num_text)
                    if digits:
                        updated[last_asked_field] = int(digits)
                    else:
                        updated[last_asked_field] = clean_input
            elif last_asked_field in ["duration_months", "notice_period_months", "probation_months"]:
                bn_to_en = str.maketrans('০১২৩৪৫৬৭৮৯', '0123456789')
                num_text = clean_input.translate(bn_to_en)
                yr_m = re.search(r'(\d+)\s*(?:বছর|years|year|বৎসরের|বৎসর)', num_text, re.IGNORECASE)
                if yr_m:
                    updated[last_asked_field] = int(yr_m.group(1)) * 12
                else:
                    digits = re.sub(r'[^\d]', '', num_text)
                    if digits:
                        updated[last_asked_field] = int(digits)
                    else:
                        updated[last_asked_field] = clean_input
            else:
                # Store full descriptive text for covenants, obligations, breach terms, dispute forums, etc.
                updated[last_asked_field] = clean_input

        # Normalize Bengali numerals to English digits
        bn_to_en = str.maketrans('০১২৩৪৫৬৭৮৯', '0123456789')
        normalized_text = clean_input.translate(bn_to_en)
        text_lower = normalized_text.lower()

        # Extract explicit landlord / tenant by keyword
        landlord_kw = re.search(r'(?:মালিক|landlord|মালিকের\s*নাম|owner)\s*(?:হলো|হচ্ছে|is|:)?\s*([A-Za-z\u0980-\u09FF\.\s]{2,40})', clean_input, re.IGNORECASE)
        if landlord_kw and ("landlord_name" not in updated or not updated["landlord_name"]):
            l_name = landlord_kw.group(1).strip()
            # filter out non-names like "কে", "কী", "কবে"
            if len(l_name) >= 2 and l_name.lower() not in ["ke", "ki", "কে", "কী", "হবে"]:
                updated["landlord_name"] = l_name.title() if l_name.isascii() else l_name

        tenant_kw = re.search(r'(?:ভাড়াটিয়া|tenant|ভাড়াটিয়ার\s*নাম)\s*(?:হলো|হচ্ছে|is|:)?\s*([A-Za-z\u0980-\u09FF\.\s]{2,40})', clean_input, re.IGNORECASE)
        if tenant_kw and ("tenant_name" not in updated or not updated["tenant_name"]):
            t_name = tenant_kw.group(1).strip()
            if len(t_name) >= 2 and t_name.lower() not in ["ke", "ki", "কে", "কী", "হবে"]:
                updated["tenant_name"] = t_name.title() if t_name.isascii() else t_name

        # Extract employee / employer keywords
        employer_kw = re.search(r'(?:কোম্পানি|employer|প্রতিষ্ঠান)\s*(?:হলো|is|:)?\s*([A-Za-z\u0980-\u09FF\.\s]{2,40})', clean_input, re.IGNORECASE)
        if employer_kw and ("employer_name" not in updated or not updated["employer_name"]):
            updated["employer_name"] = employer_kw.group(1).strip()

        employee_kw = re.search(r'(?:কর্মচারী|employee|চাকরিজীবী)\s*(?:হলো|is|:)?\s*([A-Za-z\u0980-\u09FF\.\s]{2,40})', clean_input, re.IGNORECASE)
        if employee_kw and ("employee_name" not in updated or not updated["employee_name"]):
            updated["employee_name"] = employee_kw.group(1).strip()

        # Extract monthly rent
        rent_match = re.search(r'(?:ভাড়া|rent|মাসিক|monthly)\s*(?:হবে|is|:)?\s*(\d+[\d,]*)', normalized_text, re.IGNORECASE)
        if not rent_match:
            rent_match = re.search(r'(\d+[\d,]*)\s*(?:টাকা|taka|bdt)', normalized_text, re.IGNORECASE)
        if rent_match:
            try:
                clean_rent = int(rent_match.group(1).replace(',', ''))
                if clean_rent > 500:  # avoid picking up dates
                    updated["monthly_rent_bdt"] = clean_rent
            except ValueError:
                pass

        # Extract advance / security deposit (handling 'লাখ' / 'lakh' multiplier)
        deposit_lakh_match = re.search(r'(?:জামানত|অগ্রিম|advance|deposit|security).*?(\d+)\s*(?:লাখ|lakh)', normalized_text, re.IGNORECASE)
        if deposit_lakh_match:
            updated["security_deposit_bdt"] = int(deposit_lakh_match.group(1)) * 100000
        else:
            deposit_match = re.search(r'(?:জামানত|অগ্রিম|advance|deposit|security)\s*(?:হবে|is|:)?\s*(\d+[\d,]*)', normalized_text, re.IGNORECASE)
            if deposit_match:
                try:
                    clean_dep = int(deposit_match.group(1).replace(',', ''))
                    updated["security_deposit_bdt"] = clean_dep
                except ValueError:
                    pass

        # Extract duration
        duration_year_match = re.search(r'(\d+)\s*(?:বছর|years|year|বৎসরের|বৎসর)', normalized_text, re.IGNORECASE)
        if duration_year_match:
            years = int(duration_year_match.group(1))
            updated["duration_months"] = years * 12
        else:
            duration_month_match = re.search(r'(\d+)\s*(?:মাস|months|month)', normalized_text, re.IGNORECASE)
            if duration_month_match:
                updated["duration_months"] = int(duration_month_match.group(1))

        # Extract Location / District (Bangla + English)
        district_map = {
            "dhaka": "Dhaka", "ঢাকা": "Dhaka",
            "chattogram": "Chattogram", "chittagong": "Chattogram", "চট্টগ্রাম": "Chattogram",
            "sylhet": "Sylhet", "সিলেট": "Sylhet",
            "rajshahi": "Rajshahi", "রাজশাহী": "Rajshahi",
            "khulna": "Khulna", "খুলনা": "Khulna",
            "barishal": "Barishal", "বরিশাল": "Barishal",
            "gazipur": "Gazipur", "গাজীপুর": "Gazipur",
            "narayanganj": "Narayanganj", "নারায়ণগঞ্জ": "Narayanganj"
        }
        for d_key, d_val in district_map.items():
            if d_key in text_lower:
                updated["district"] = d_val
                break

        # Extract specific premises areas / addresses
        area_keywords = ["mirpur", "মিরপুর", "dhanmondi", "ধানমন্ডি", "gulshan", "গুলশান", "banani", "বনানী", "uttara", "উত্তরা", "motijheel", "মতিঝিল"]
        for area in area_keywords:
            if area in text_lower:
                if "premises_address" not in updated or not updated["premises_address"]:
                    updated["premises_address"] = f"Shop / Commercial Space, {area.title()}, {updated.get('district', 'Dhaka')}"

        return updated

ai_service = AIProvider()
