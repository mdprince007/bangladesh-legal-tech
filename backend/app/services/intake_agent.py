from typing import Dict, Any, List, Tuple, Optional
from app.services.ai_provider import ai_service
from app.schemas.intake import IntakeChatRequest, IntakeChatResponse

MATTER_FIELD_REGISTRY: Dict[str, List[Tuple[str, str, str]]] = {
    "commercial_lease": [
        ("landlord_name", "মালিকের পূর্ণ নাম কী?", "What is the full legal name of the Landlord?"),
        ("tenant_name", "ভাড়াটিয়ার পূর্ণ নাম কী?", "What is the full legal name of the Tenant?"),
        ("premises_address", "দোকান বা স্পেসের সম্পূর্ণ ঠিকানা ও লোকেশন কোথায়?", "What is the full address/location of the shop or commercial space?"),
        ("monthly_rent_bdt", "মাসিক ভাড়া কত টাকা নির্ধারণ করা হয়েছে?", "What is the monthly rent in BDT?"),
        ("security_deposit_bdt", "অগ্রিম বা জামানত (Security Deposit) বাবদ কত টাকা দেওয়া হবে?", "What is the security deposit/advance amount in BDT?"),
        ("duration_months", "চুক্তির মেয়াদ কত দিন বা কত বছর হবে?", "What is the lease duration (in months or years)?"),
        ("permitted_business_type", "স্পেসটিতে কী ধরনের বাণিজ্যিক ব্যবসা পরিচালনা করা হবে?", "What is the permitted nature of business?"),
        ("notice_period_months", "চুক্তি অবসানের জন্য উভয় পক্ষের জন্য কত মাসের নোটিশ পিরিয়ড কার্যকর থাকবে?", "What is the termination notice period in months?"),
        ("commencement_date", "ভাড়ার চুক্তি কবে থেকে কার্যকর হবে (শুরুর তারিখ)?", "What is the commencement date of the lease?"),
    ],
    "residential_rent": [
        ("landlord_name", "বাড়িওয়ালার (মালিকের) পূর্ণ নাম কী?", "What is the full legal name of the Landlord/House Owner?"),
        ("tenant_name", "ভাড়াটিয়ার পূর্ণ নাম কী?", "What is the full legal name of the Tenant?"),
        ("premises_address", "ভাড়া দেওয়া বাসা বা ফ্ল্যাটের সম্পূর্ণ ঠিকানা (হোল্ডিং, এলাকা, ফ্ল্যাট নং)?", "What is the full address/flat no of the residential apartment?"),
        ("monthly_rent_bdt", "বাসার মাসিক ভাড়া কত টাকা নির্ধারণ করা হয়েছে?", "What is the monthly rent in BDT?"),
        ("security_deposit_bdt", "অগ্রিম জামানত বাবদ কত টাকা দেওয়া হয়েছে বা হবে?", "What is the security deposit/advance amount in BDT?"),
        ("duration_months", "ভাড়ার মেয়াদ কত মাস বা কত বছরের জন্য হবে?", "What is the duration in months or years?"),
        ("notice_period_months", "বাসা ছাড়ার বা খালি করার নোটিশ পিরিয়ড কত মাস থাকবে?", "What is the termination notice period in months?"),
        ("commencement_date", "বাসা ভাড়ার চুক্তি কোন তারিখ থেকে কার্যকর হবে?", "From which date does the tenancy commence?"),
    ],
    "employment_agreement": [
        ("employer_name", "নিয়োগকারী প্রতিষ্ঠান বা কোম্পানির নাম কী?", "What is the legal name of the Employer / Company?"),
        ("employee_name", "কর্মচারীর পূর্ণ নাম কী?", "What is the full legal name of the Employee?"),
        ("designation", "কর্মচারীকে কোন পদে (Designation) নিয়োগ দেওয়া হচ্ছে?", "What is the official job designation/role?"),
        ("monthly_salary_bdt", "মাসিক মোট বেতন (Gross Monthly Salary) কত টাকা?", "What is the gross monthly salary in BDT?"),
        ("probation_months", "শিক্ষানবিসকাল (Probation Period) কত মাস থাকবে?", "What is the probation period in months?"),
        ("notice_period_days", "চাকরি ছাড়া বা অবসানের জন্য কত দিনের লিখিত নোটিশ প্রদান করতে হবে?", "What is the termination notice period in days?"),
        ("joining_date", "চাকরিতে যোগদানের তারিখ (Joining Date) কবে?", "What is the joining date?"),
    ],
    "demand_notice_ni_act": [
        ("payee_name", "যিনি টাকা পাবেন (চেক প্রাপক বা ক্লায়েন্ট)-এর পূর্ণ নাম কী?", "What is the full name of the Payee (Cheque Holder)?"),
        ("drawer_name", "যিনি চেক দিয়েছেন (বিবাদী বা ঋণগ্রহীতা)-এর পূর্ণ নাম কী?", "What is the full name of the Drawer (Cheque Issuer)?"),
        ("drawer_address", "চেক প্রদানকারী বিবাদীর বর্তমান যোগাযোগের ঠিকানা কী?", "What is the postal address of the Cheque Drawer?"),
        ("cheque_no", "ডিজঅনার হওয়া চেকের নম্বর (Cheque No) কত?", "What is the Cheque Number?"),
        ("cheque_amount_bdt", "চেকের টাকার পরিমাণ কত (BDT)?", "What is the dishonoured cheque amount in BDT?"),
        ("bank_name", "চেকটি কোন ব্যাংকের এবং কোন শাখার ছিল?", "Which Bank and Branch was the cheque drawn on?"),
        ("return_memo_date", "ব্যাংক থেকে ডিজঅনার মেমো বা স্লিপ পাওয়ার তারিখ কবে?", "What is the date of the Bank Return Memo?"),
    ],
    "partnership_deed": [
        ("firm_name", "অংশীদারি প্রতিষ্ঠানের (Firm Name) নাম কী হবে?", "What is the name of the Partnership Firm?"),
        ("partner_one", "প্রথম অংশীদারের (Partner 1) পূর্ণ নাম ও ঠিকানা কী?", "What is the full name and address of the First Partner?"),
        ("partner_two", "দ্বিতীয় অংশীদারের (Partner 2) পূর্ণ নাম ও ঠিকানা কী?", "What is the full name and address of the Second Partner?"),
        ("business_nature", "অংশীদারি কারবারের মূল প্রকৃতি বা ব্যবসার ক্ষেত্র কী?", "What is the primary nature/scope of business?"),
        ("capital_contribution", "উভয় অংশীদারের প্রাথমিক মূলধন (Capital) কে কত দিচ্ছেন?", "What is the capital contribution ratio or amount of each partner?"),
        ("profit_sharing_ratio", "লাভ-ক্ষতি বণ্টনের অনুপাত (Profit Sharing Ratio) কী হবে? (যেমন: ৫০:৫০ বা ৬০:৪০)", "What is the profit and loss sharing ratio?"),
        ("commencement_date", "অংশীদারি কারবার কোন তারিখ থেকে কার্যকর শুরু হবে?", "What is the commencement date of the partnership?"),
    ],
    "sale_agreement": [
        ("seller_name", "বিক্রেতার (Seller) পূর্ণ নাম ও ঠিকানা কী?", "What is the full legal name and address of the Seller?"),
        ("buyer_name", "ক্রেতার (Buyer) পূর্ণ নাম ও ঠিকানা কী?", "What is the full legal name and address of the Buyer?"),
        ("property_schedule", "বিক্রয়যোগ্য সম্পত্তির সুনির্দিষ্ট তফশিল (মৌজা, খতিয়ান, দাগ নং, আয়তন বা ফ্ল্যাট বিবরণ) কী?", "What is the legal schedule/description of the property?"),
        ("total_price_bdt", "সম্পত্তির সর্বমোট বিক্রয়মূল্য (Total Sale Price) কত টাকা?", "What is the total agreed sale price in BDT?"),
        ("earnest_money_bdt", "বায়না বাবদ অগ্রিম গৃহীত টাকা (Earnest Money) কত?", "What is the advance earnest money paid in BDT?"),
        ("completion_deadline", "অবশিষ্ট মূল্য পরিশোধ ও দলিল রেজিস্ট্রির সর্বশেষ সময়সীমা কবে?", "What is the deadline for final balance payment and registration?"),
    ],
    "loan_agreement": [
        ("lender_name", "ঋণদাতা বা হাওলাত প্রদানকারীর পূর্ণ নাম ও ঠিকানা কী?", "What is the full name and address of the Lender?"),
        ("borrower_name", "ঋণগ্রহীতার পূর্ণ নাম ও ঠিকানা কী?", "What is the full name and address of the Borrower?"),
        ("loan_amount_bdt", "ঋণ বা হাওলাত দেওয়া মূল টাকার পরিমাণ কত?", "What is the principal loan amount in BDT?"),
        ("loan_purpose", "ঋণ গ্রহণের মূল উদ্দেশ্য কী?", "What is the stated purpose of the loan?"),
        ("repayment_deadline", "টাকা সম্পূর্ণ পরিশোধ বা ফেরতের নির্ধারিত শেষ তারিখ কবে?", "What is the due date or schedule for loan repayment?"),
        ("security_details", "ঋণের বিপরীতে কোনো সিকিউরিটি চেক বা জামানত দেওয়া হয়েছে কি?", "Are there security cheques or collateral provided?"),
    ],
    "nda": [
        ("disclosing_party", "তথ্য প্রকাশকারী পক্ষের (Disclosing Party) নাম কী?", "What is the name of the Disclosing Party?"),
        ("receiving_party", "তথ্য গ্রহণকারী পক্ষের (Receiving Party) নাম কী?", "What is the name of the Receiving Party?"),
        ("confidential_matter", "গোপনীয় বিষয় বা প্রজেক্টের সংক্ষিপ্ত বিবরণ কী?", "What is the subject matter of the confidential information?"),
        ("duration_years", "গোপনীয়তা বজায় রাখার বাধ্যবাধকতা কত বছর বহাল থাকবে?", "What is the confidentiality term in years?"),
        ("effective_date", "চুক্তিটি কোন তারিখ থেকে কার্যকর হবে?", "What is the effective date of the NDA?"),
    ],
    "service_agreement": [
        ("client_name", "ক্লায়েন্ট বা সেবা গ্রহণকারীর নাম কী?", "What is the legal name of the Client?"),
        ("service_provider_name", "সেবা প্রদানকারী ব্যক্তি বা প্রতিষ্ঠানের নাম কী?", "What is the name of the Service Provider?"),
        ("scope_of_work", "প্রদেয় কাজের পরিধি ও ডেলিভারেবলস কী কী?", "What is the scope of work and key deliverables?"),
        ("service_fee_bdt", "সেবামূল্য বা প্রজেক্ট ফি কত এবং পেমেন্ট মাইলস্টোন কী?", "What is the total service fee and payment milestone structure?"),
        ("delivery_deadline", "কাজ সম্পূর্ণ হস্তান্তরের চূড়ান্ত সময়সীমা কবে?", "What is the final delivery deadline or timeline?"),
    ],
    "custom": [
        ("custom_matter_name", "চুক্তির নাম বা শিরোনাম কী নির্ধারণ করতে চান? (যেমন: সরবরাহ চুক্তি, কমিশন চুক্তি, কনসালটেন্সি চুক্তি, গাড়ি বিক্রয় বায়না ইত্যাদি)", "What is the title/type of this agreement?"),
        ("party_one_name", "প্রথম পক্ষের (১ম পক্ষ) পূর্ণ নাম ও ঠিকানা কী?", "What is the full name and address of the First Party?"),
        ("party_two_name", "দ্বিতীয় পক্ষের (২য় পক্ষ) পূর্ণ নাম ও ঠিকানা কী?", "What is the full name and address of the Second Party?"),
        ("purpose_and_consideration", "চুক্তির মূল উদ্দেশ্য এবং আর্থিক প্রতিদান বা বিনিময় কী? (কী কারণে চুক্তি হচ্ছে এবং মোট লেনদেন বা মূল্য কত?)", "What is the core object and financial consideration of this agreement?"),
        ("obligations_first_party", "১ম পক্ষের সুনির্দিষ্ট দায়িত্ব, করণীয় ও দায় কী কী?", "What are the specific covenants and obligations of the First Party?"),
        ("obligations_second_party", "২য় পক্ষের সুনির্দিষ্ট দায়িত্ব, ডেলিভারেবলস ও দায় কী কী?", "What are the specific covenants and obligations of the Second Party?"),
        ("breach_and_cure_period", "কোনো পক্ষ শর্ত ভঙ্গ করলে নোটিশের মেয়াদ (Cure Period) ও ক্ষতিপূরণের নিয়ম কী হবে?", "What is the default cure period (e.g. 15 days) and breach consequences?"),
        ("termination_and_dispute", "চুক্তি অবসানের নোটিশ পিরিয়ড এবং কোনো বিরোধ দেখা দিলে সালিশি বা নিষ্পত্তির ফোরাম কী হবে?", "What is the termination notice period and dispute resolution forum (e.g. Arbitration in Dhaka)?"),
    ]
}

# Alias for backwards compatibility
CRITICAL_FIELDS = MATTER_FIELD_REGISTRY["commercial_lease"]

class IntakeAgent:
    @staticmethod
    def process_message(request: IntakeChatRequest) -> IntakeChatResponse:
        """
        Processes conversational legal intake step-by-step.
        Extracts facts using last_asked_field context, calculates completion percentage,
        and selects the next targeted question with current_field_asked.
        """
        matter_type = request.matter_type or "commercial_lease"
        fields = MATTER_FIELD_REGISTRY.get(matter_type, MATTER_FIELD_REGISTRY.get("custom", MATTER_FIELD_REGISTRY["commercial_lease"]))

        current_facts = dict(request.current_facts)

        # Extract structured facts from user's current message with last_asked_field context
        updated_facts = ai_service.extract_structured_facts(
            request.user_input, 
            current_facts, 
            last_asked_field=request.last_asked_field
        )

        # Check critical fields
        missing_fields: List[str] = []
        next_question_bn: Optional[str] = None
        next_question_en: Optional[str] = None
        next_field_key: Optional[str] = None

        for field_key, q_bn, q_en in fields:
            val = updated_facts.get(field_key)
            if val is None or val == "" or val == 0:
                missing_fields.append(field_key)
                if not next_question_bn:
                    next_question_bn = q_bn
                    next_question_en = q_en
                    next_field_key = field_key

        total_critical = len(fields)
        completed_critical = total_critical - len(missing_fields)
        completion_percentage = int((completed_critical / total_critical) * 100) if total_critical > 0 else 100

        is_ready = len(missing_fields) == 0

        doc_labels = {
            "commercial_lease": "বাণিজ্যিক ভাড়ার চুক্তি",
            "residential_rent": "আবাসিক বাসা ভাড়ার চুক্তি",
            "employment_agreement": "কর্মসংস্থান ও চাকরির চুক্তি",
            "demand_notice_ni_act": "চেক ডিজঅনার আইনি নোটিশ",
            "partnership_deed": "অংশীদারি কারবার চুক্তিপত্র (Partnership Deed)",
            "sale_agreement": "সম্পত্তি বিক্রয় বায়না চুক্তিপত্র (Sale Agreement)",
            "loan_agreement": "হাওলাত / অর্থ ঋণ চুক্তিপত্র (Loan Agreement)",
            "nda": "গোপনীয়তা চুক্তি (Non-Disclosure Agreement)",
            "service_agreement": "পেশাদার সেবা ও প্রজেক্ট চুক্তিপত্র (Service Agreement)",
            "custom": updated_facts.get("custom_matter_name") or "কাস্টমাইজড চুক্তিপত্র (Custom Agreement)"
        }
        doc_label_bn = doc_labels.get(matter_type, updated_facts.get("custom_matter_name") or "চুক্তিপত্র")

        if is_ready:
            reply_bn = f"আপনার '{doc_label_bn}'-এর প্রয়োজনীয় যাবতীয় আইনি ধারা ও শর্তাবলী সংগৃহীত হয়েছে! এখন সম্পূর্ণ লিগ্যাল ড্রাফট তৈরি করা যাবে।"
            reply_en = f"All essential legal terms and covenants for '{doc_label_bn}' have been gathered! The draft agreement is ready to be generated."
        else:
            reply_bn = f"তথ্যটি সংরক্ষিত হয়েছে (অগ্রগতি: {completion_percentage}%)। পরবর্তী আইনি প্রশ্ন:\n{next_question_bn}"
            reply_en = f"Details updated ({completion_percentage}% complete). Next legal inquiry:\n{next_question_en}"

        return IntakeChatResponse(
            assistant_reply=reply_en,
            assistant_reply_bangla=reply_bn,
            extracted_facts=updated_facts,
            completion_percentage=completion_percentage,
            missing_critical_fields=missing_fields,
            is_ready_for_drafting=is_ready,
            current_field_asked=next_field_key,
            next_suggested_question=next_question_bn or "সব আইনি তথ্য সংগৃহীত হয়েছে।"
        )

intake_agent = IntakeAgent()
