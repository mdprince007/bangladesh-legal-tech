"""
What each kind of document needs before it can be drafted properly, grounded in
Dr. Syeda Nasrin, "Basics of Legal Drafting" (2nd Ed.).

Book, p.45-46 ("Basic things to be contained in any agreement"): name of the agreement, date of
execution, date of enforcement, parties' parents' names, present and permanent address, age,
nationality, legal standi, recitals, rights and liabilities, tenure, consideration, description of
property, termination, default, notice period, dispute settlement, governing law, witnesses,
number of pages, signatures, thumb impression, proper stamp paper.
Book, p.120-121: particulars of a legal notice.

kind:
  "fact"   - only the client can supply it; never filled in by the system
  "term"   - a commercial/legal term; the system may SUGGEST the book's standard wording,
             which the user must accept
"""
from typing import Any, Dict, List, Optional

Req = Dict[str, Any]


def _party(prefix: str, name_key: str, role_bn: str, company_possible: bool = False) -> List[Req]:
    reqs = [
        {"field": name_key, "label_bn": f"{role_bn}র পূর্ণ নাম", "kind": "fact", "critical": True,
         "question_bn": f"{role_bn}র পূর্ণ নাম (জাতীয় পরিচয়পত্র অনুযায়ী) কী?",
         "why_bn": "চুক্তির পক্ষকে সঠিকভাবে শনাক্ত করা না গেলে চুক্তি বলবৎ করা ও মামলায় সমন জারি কঠিন হয় (বই পৃ. ৪৫)।"},
        {"field": f"{prefix}_father", "label_bn": f"{role_bn}র পিতা/স্বামীর নাম", "kind": "fact", "critical": True,
         "question_bn": f"{role_bn}র পিতার (বা স্বামীর) নাম কী?",
         "why_bn": "বই অনুযায়ী প্রতিটি পক্ষের পিতা-মাতার নাম উল্লেখ বাধ্যতামূলক (পৃ. ৪৫)।"},
        {"field": f"{prefix}_mother", "label_bn": f"{role_bn}র মাতার নাম", "kind": "fact", "critical": False,
         "question_bn": f"{role_bn}র মাতার নাম কী?",
         "why_bn": "বইয়ের নমুনায় পিতা ও মাতা উভয়ের নাম দেওয়া হয়েছে (পৃ. ৪৯, ৬৭)।"},
        {"field": f"{prefix}_address", "label_bn": f"{role_bn}র বর্তমান ঠিকানা", "kind": "fact", "critical": True,
         "question_bn": f"{role_bn}র বর্তমান ঠিকানা কী?",
         "why_bn": "নোটিশ পাঠানো ও মামলার জন্য বর্তমান ও স্থায়ী ঠিকানা আবশ্যক (পৃ. ৪৫)।"},
        {"field": f"{prefix}_permanent_address", "label_bn": f"{role_bn}র স্থায়ী ঠিকানা", "kind": "fact", "critical": False,
         "question_bn": f"{role_bn}র স্থায়ী ঠিকানা কী? (বর্তমান ঠিকানার মতো হলে 'একই' লিখুন)",
         "why_bn": "বই অনুযায়ী বর্তমান ও স্থায়ী উভয় ঠিকানা দিতে হবে (পৃ. ৪৫)।"},
        {"field": f"{prefix}_nid", "label_bn": f"{role_bn}র জাতীয় পরিচয়পত্র নং", "kind": "fact", "critical": False,
         "question_bn": f"{role_bn}র জাতীয় পরিচয়পত্র (NID) বা পাসপোর্ট নম্বর কী?",
         "why_bn": "পরিচয় নিশ্চিতকরণে NID উল্লেখ করা হয় (বই পৃ. ৪৯, ৬৭)।"},
    ]
    if company_possible:
        reqs.append({"field": f"{prefix}_representative", "label_bn": f"{role_bn} প্রতিষ্ঠান হলে প্রতিনিধির নাম ও পদবি",
                     "kind": "fact", "critical": False, "only_if_company": prefix,
                     "question_bn": f"{role_bn} যদি কোম্পানি হয়, কে (নাম ও পদবি) বোর্ড রেজুলেশনের মাধ্যমে স্বাক্ষর করবেন?",
                     "why_bn": "প্রতিষ্ঠানের পক্ষে স্বাক্ষরকারীর লোকাস স্ট্যান্ডাই (বোর্ড রেজুলেশন/পাওয়ার অব অ্যাটর্নি) যাচাই আবশ্যক (বই অধ্যায় ১)।"})
    return reqs


_EXECUTION: List[Req] = [
    {"field": "execution_date", "label_bn": "চুক্তি সম্পাদনের তারিখ", "kind": "fact", "critical": True,
     "question_bn": "চুক্তি কোন তারিখে সই (সম্পাদন) করা হবে?",
     "why_bn": "সম্পাদনের তারিখ ছাড়া চুক্তি অসম্পূর্ণ (বই পৃ. ৪৫)।"},
    {"field": "execution_place", "label_bn": "সম্পাদনের স্থান", "kind": "fact", "critical": False,
     "question_bn": "চুক্তি কোথায় (কোন শহর/এলাকায়) সম্পাদিত হবে?",
     "why_bn": "স্থান উল্লেখ থাকলে এখতিয়ার নির্ধারণ সহজ হয়।"},
    {"field": "witness_one", "label_bn": "১ম সাক্ষীর নাম, পিতা ও ঠিকানা", "kind": "fact", "critical": False,
     "question_bn": "প্রথম সাক্ষীর নাম, পিতার নাম ও ঠিকানা কী?",
     "why_bn": "বই অনুযায়ী সাক্ষীর উপস্থিতিতে সম্পাদনের বিবৃতি ও সাক্ষীর স্বাক্ষর আবশ্যক (পৃ. ৪৫-৪৬)।"},
    {"field": "witness_two", "label_bn": "২য় সাক্ষীর নাম, পিতা ও ঠিকানা", "kind": "fact", "critical": False,
     "question_bn": "দ্বিতীয় সাক্ষীর নাম, পিতার নাম ও ঠিকানা কী?",
     "why_bn": "অন্তত দুইজন সাক্ষী রাখা প্রচলিত (বইয়ের ভাড়াচুক্তির নমুনা, পৃ. ৪৮)।"},
    {"field": "stamp_value_bdt", "label_bn": "নন-জুডিশিয়াল স্ট্যাম্পের মূল্য", "kind": "term", "critical": False,
     "question_bn": "কত টাকার নন-জুডিশিয়াল স্ট্যাম্পে চুক্তি হবে?",
     "why_bn": "আইন নির্ধারিত স্ট্যাম্প ব্যবহার না করলে দলিল সাক্ষ্য হিসেবে গ্রহণযোগ্যতা হারাতে পারে (স্ট্যাম্প আইন ১৮৯৯; বই পৃ. ৪৬)।",
     "suggestion": None},
    {"field": "dispute_forum", "label_bn": "বিরোধ নিষ্পত্তির পদ্ধতি", "kind": "term", "critical": False,
     "question_bn": "বিরোধ হলে সালিশ (Arbitration) নাকি সরাসরি আদালত — কোনটি চান?",
     "why_bn": "বিরোধ নিষ্পত্তি ও প্রযোজ্য আইনের ধারা থাকা আবশ্যক (বই পৃ. ৪৫)।",
     "suggestion": "প্রথমে আলোচনা, ব্যর্থ হলে ৩০ দিনের নোটিশ দিয়ে সালিশ আইন ২০০১ অনুযায়ী সালিশ"},
]

REQUIREMENTS: Dict[str, List[Req]] = {
    "commercial_lease": [
        *_party("landlord", "landlord_name", "মালিক (ভাড়াদাতা)", company_possible=True),
        *_party("tenant", "tenant_name", "ভাড়াটিয়া", company_possible=True),
        {"field": "premises_address", "label_bn": "দোকান/স্পেসের পূর্ণ ঠিকানা", "kind": "fact", "critical": True,
         "question_bn": "দোকান/অফিস স্পেসের পূর্ণ ঠিকানা (হোল্ডিং, রোড, মার্কেট, এলাকা) কী?",
         "why_bn": "তফসিলে সম্পত্তির সুনির্দিষ্ট বর্ণনা না থাকলে উচ্ছেদ/দখল মামলায় সম্পত্তি শনাক্ত করা যায় না (বই পৃ. ৪৮)।"},
        {"field": "floor_area_sft", "label_bn": "আয়তন (বর্গফুট) ও তলা", "kind": "fact", "critical": False,
         "question_bn": "স্পেসটির আয়তন কত বর্গফুট এবং কোন তলায়?",
         "why_bn": "বইয়ের 'SCHEDULE OF SHOP'-এ বর্গফুট ও তলা উল্লেখ করা হয়েছে (পৃ. ৪৮)।"},
        {"field": "monthly_rent_bdt", "label_bn": "মাসিক ভাড়া", "kind": "fact", "critical": True,
         "question_bn": "মাসিক ভাড়া কত টাকা?", "why_bn": "প্রতিদান (Consideration) ছাড়া চুক্তি বৈধ নয় (চুক্তি আইন ১৮৭২, ধারা ১০)।"},
        {"field": "security_deposit_bdt", "label_bn": "অগ্রিম/জামানত", "kind": "fact", "critical": True,
         "question_bn": "অগ্রিম বা জামানত কত টাকা, এবং তা কি মাসিক ভাড়ার সাথে সমন্বয়যোগ্য নাকি মেয়াদ শেষে ফেরতযোগ্য?",
         "why_bn": "অগ্রিম কীভাবে ফেরত/সমন্বয় হবে তা স্পষ্ট না থাকলে পরে বিরোধ হয় (বই পৃ. ৪৭)।"},
        {"field": "duration_months", "label_bn": "চুক্তির মেয়াদ", "kind": "fact", "critical": True,
         "question_bn": "চুক্তির মেয়াদ কত মাস/বছর?", "why_bn": "মেয়াদ (Tenure) উল্লেখ বাধ্যতামূলক; ১ বছরের বেশি হলে রেজিস্ট্রি আবশ্যক (সম্পত্তি হস্তান্তর আইন ধারা ১০৭)।"},
        {"field": "commencement_date", "label_bn": "কার্যকর হওয়ার তারিখ", "kind": "fact", "critical": True,
         "question_bn": "চুক্তি কোন তারিখ থেকে কার্যকর হবে এবং দখল কবে হস্তান্তর হবে?",
         "why_bn": "কার্যকর হওয়ার তারিখ (Date of enforcement) উল্লেখ বাধ্যতামূলক (বই পৃ. ৪৫)।"},
        {"field": "permitted_business_type", "label_bn": "ব্যবসার ধরন", "kind": "fact", "critical": True,
         "question_bn": "স্পেসটিতে কী ধরনের ব্যবসা চলবে?",
         "why_bn": "অনুমোদিত ব্যবহারের বাইরে ব্যবহার চুক্তিভঙ্গ হিসেবে গণ্য করার শর্ত বইয়ের নমুনায় আছে (পৃ. ৪৭)।"},
        {"field": "rent_due_day_of_month", "label_bn": "ভাড়া পরিশোধের শেষ দিন", "kind": "term", "critical": False,
         "question_bn": "প্রতি মাসের কত তারিখের মধ্যে ভাড়া দিতে হবে?", "why_bn": "বইয়ের নমুনায় ১-৭ তারিখের মধ্যে চলতি মাসের ভাড়া (পৃ. ৪৭)।", "suggestion": 7},
        {"field": "rent_escalation_pct", "label_bn": "বার্ষিক ভাড়া বৃদ্ধি (%)", "kind": "term", "critical": False,
         "question_bn": "প্রতি বছর ভাড়া কত শতাংশ বাড়বে? (না বাড়লে ০ লিখুন)", "why_bn": "বইয়ের নমুনায় বার্ষিক ১০% বৃদ্ধি (পৃ. ৪৭)।", "suggestion": 10},
        {"field": "notice_period_months", "label_bn": "চুক্তি অবসানের নোটিশ", "kind": "term", "critical": False,
         "question_bn": "চুক্তি শেষ করতে কত মাস আগে লিখিত নোটিশ দিতে হবে?", "why_bn": "বইয়ের নমুনায় ৯০ দিনের লিখিত নোটিশ (পৃ. ৪৮)।", "suggestion": 3},
        {"field": "stamp_duty_borne_by", "label_bn": "স্ট্যাম্প ও রেজিস্ট্রি খরচ কে বহন করবে", "kind": "term", "critical": False,
         "question_bn": "স্ট্যাম্প ও রেজিস্ট্রেশন খরচ কে দেবে — মালিক, ভাড়াটিয়া নাকি উভয়ে সমান?", "why_bn": "খরচ বহনের দায় স্পষ্ট না থাকলে রেজিস্ট্রি আটকে যায়।", "suggestion": "tenant"},
        *_EXECUTION,
    ],
    "residential_rent": [
        *_party("landlord", "landlord_name", "বাড়িওয়ালা"),
        *_party("tenant", "tenant_name", "ভাড়াটিয়া"),
        {"field": "premises_address", "label_bn": "বাসা/ফ্ল্যাটের পূর্ণ ঠিকানা", "kind": "fact", "critical": True,
         "question_bn": "ফ্ল্যাট/বাসার পূর্ণ ঠিকানা (ফ্ল্যাট নং, তলা, বাড়ি নং, রোড, এলাকা) কী?", "why_bn": "তফসিলে সম্পত্তির সুনির্দিষ্ট বর্ণনা আবশ্যক (বই পৃ. ৪৮)।"},
        {"field": "monthly_rent_bdt", "label_bn": "মাসিক ভাড়া", "kind": "fact", "critical": True,
         "question_bn": "মাসিক ভাড়া কত টাকা?", "why_bn": "প্রতিদান ছাড়া চুক্তি বৈধ নয় (চুক্তি আইন ধারা ১০)।"},
        {"field": "security_deposit_bdt", "label_bn": "অগ্রিম", "kind": "fact", "critical": True,
         "question_bn": "অগ্রিম কত টাকা?", "why_bn": "বাড়িভাড়া নিয়ন্ত্রণ আইন ১৯৯১ অনুযায়ী অগ্রিমের সীমা আছে — পরিমাণ স্পষ্ট থাকা জরুরি।"},
        {"field": "duration_months", "label_bn": "মেয়াদ", "kind": "fact", "critical": True,
         "question_bn": "ভাড়ার মেয়াদ কত মাস/বছর?", "why_bn": "মেয়াদ উল্লেখ বাধ্যতামূলক (বই পৃ. ৪৫)।"},
        {"field": "commencement_date", "label_bn": "শুরুর তারিখ", "kind": "fact", "critical": True,
         "question_bn": "কোন তারিখ থেকে ভাড়া শুরু হবে?", "why_bn": "কার্যকর হওয়ার তারিখ বাধ্যতামূলক (বই পৃ. ৪৫)।"},
        {"field": "rent_due_day_of_month", "label_bn": "ভাড়া পরিশোধের শেষ দিন", "kind": "term", "critical": False,
         "question_bn": "প্রতি মাসের কত তারিখের মধ্যে ভাড়া দিতে হবে?", "why_bn": "বইয়ের নমুনায় ১-৭ তারিখ।", "suggestion": 7},
        {"field": "notice_period_months", "label_bn": "নোটিশ মেয়াদ", "kind": "term", "critical": False,
         "question_bn": "বাসা ছাড়ার জন্য কত মাস আগে নোটিশ দিতে হবে?", "why_bn": "নোটিশ মেয়াদ বাধ্যতামূলক উপাদান (বই পৃ. ৪৫)।", "suggestion": 2},
        *_EXECUTION,
    ],
    "employment_agreement": [
        *_party("employer", "employer_name", "নিয়োগকারী প্রতিষ্ঠান", company_possible=True),
        *_party("employee", "employee_name", "কর্মচারী"),
        {"field": "designation", "label_bn": "পদবি", "kind": "fact", "critical": True, "question_bn": "কোন পদে নিয়োগ?", "why_bn": "দায়িত্ব নির্ধারণে পদবি আবশ্যক।"},
        {"field": "monthly_salary_bdt", "label_bn": "মাসিক মোট বেতন", "kind": "fact", "critical": True, "question_bn": "মাসিক মোট বেতন কত?", "why_bn": "প্রতিদান (Consideration) আবশ্যক।"},
        {"field": "joining_date", "label_bn": "যোগদানের তারিখ", "kind": "fact", "critical": True, "question_bn": "যোগদানের তারিখ কবে?", "why_bn": "কার্যকর তারিখ আবশ্যক (বই পৃ. ৪৫)।"},
        {"field": "work_location", "label_bn": "কর্মস্থল", "kind": "fact", "critical": False, "question_bn": "কর্মস্থল কোথায়?", "why_bn": "কর্মস্থল উল্লেখ থাকলে বদলি সংক্রান্ত বিরোধ কমে।"},
        {"field": "probation_months", "label_bn": "শিক্ষানবিসকাল", "kind": "term", "critical": False, "question_bn": "শিক্ষানবিসকাল কত মাস?", "why_bn": "বাংলাদেশ শ্রম আইন ২০০৬, ধারা ৪ অনুযায়ী শিক্ষানবিসকাল নির্ধারিত।", "suggestion": 3},
        {"field": "notice_period_days", "label_bn": "চাকরি অবসানের নোটিশ (দিন)", "kind": "term", "critical": False, "question_bn": "চাকরি ছাড়তে/অবসানে কত দিনের নোটিশ?", "why_bn": "শ্রম আইন ২০০৬, ধারা ২৬-২৭ অনুযায়ী নোটিশ।", "suggestion": 60},
        *_EXECUTION,
    ],
    "demand_notice_ni_act": [
        *_party("payee", "payee_name", "চেক প্রাপক (মক্কেল)", company_possible=True),
        *_party("drawer", "drawer_name", "চেক দাতা (নোটিশ গ্রহীতা)", company_possible=True),
        {"field": "liability_background", "label_bn": "কী কারণে চেক দেওয়া হয়েছিল", "kind": "fact", "critical": True,
         "question_bn": "কোন দেনা/লেনদেনের বিপরীতে চেকটি দেওয়া হয়েছিল? সংক্ষেপে ঘটনাক্রম বলুন।",
         "why_bn": "নোটিশে ঘটনাক্রম (Statement of facts — chronology) স্পষ্টভাবে থাকতে হবে (বই পৃ. ১২১)।"},
        {"field": "cheque_no", "label_bn": "চেক নম্বর", "kind": "fact", "critical": True, "question_bn": "চেক নম্বর কত?", "why_bn": "চেক শনাক্তকরণে আবশ্যক (বই পৃ. ১৩৬)।"},
        {"field": "cheque_date", "label_bn": "চেকের তারিখ", "kind": "fact", "critical": True, "question_bn": "চেকে কোন তারিখ লেখা?", "why_bn": "চেকের তারিখ থেকে ৬ মাসের মধ্যে ব্যাংকে উপস্থাপন করতে হয় (NI Act ধারা ১৩৮(১)(ক))।"},
        {"field": "cheque_amount_bdt", "label_bn": "চেকের টাকার পরিমাণ", "kind": "fact", "critical": True, "question_bn": "চেকের টাকার পরিমাণ কত?", "why_bn": "দাবিকৃত অর্থ সুনির্দিষ্ট থাকতে হবে।"},
        {"field": "bank_name", "label_bn": "চেকটি যে ব্যাংক-শাখার", "kind": "fact", "critical": True, "question_bn": "চেকটি কোন ব্যাংকের কোন শাখার এবং হিসাব নম্বর কত?", "why_bn": "চেকের বিবরণ সম্পূর্ণ থাকতে হবে (বই পৃ. ১৩৬)।"},
        {"field": "presentation_date", "label_bn": "ব্যাংকে জমা দেওয়ার তারিখ", "kind": "fact", "critical": True, "question_bn": "কোন তারিখে, কোন ব্যাংকে চেকটি জমা দিয়েছিলেন?", "why_bn": "উপস্থাপনের তারিখ ও ব্যাংক নোটিশে উল্লেখ করতে হয় (বই পৃ. ১৩৬)।"},
        {"field": "return_memo_date", "label_bn": "ডিজঅনার মেমোর তারিখ", "kind": "fact", "critical": True, "question_bn": "ব্যাংক কোন তারিখে চেক ফেরত (ডিজঅনার) দিয়েছে?", "why_bn": "ডিজঅনারের তথ্য পাওয়ার ৩০ দিনের মধ্যে নোটিশ পাঠাতে হবে (NI Act ধারা ১৩৮(১)(খ))।"},
        {"field": "dishonour_reason", "label_bn": "ডিজঅনারের কারণ", "kind": "fact", "critical": True, "question_bn": "ফেরত মেমোতে কী কারণ লেখা (যেমন Insufficient Fund)?", "why_bn": "অপরাধ গঠনের জন্য ডিজঅনারের কারণ উল্লেখ আবশ্যক (বই পৃ. ১৩৬)।"},
        {"field": "advocate_name", "label_bn": "নোটিশ প্রেরণকারী আইনজীবী", "kind": "fact", "critical": True, "question_bn": "কোন আইনজীবীর নামে নোটিশ যাবে (নাম, কোর্ট, চেম্বারের ঠিকানা)?", "why_bn": "নোটিশে আইনজীবীর নাম, স্বাক্ষর ও চেম্বারের ঠিকানা থাকতে হবে (বই পৃ. ১২০-১২১)।"},
        {"field": "notice_date", "label_bn": "নোটিশের তারিখ", "kind": "fact", "critical": True, "question_bn": "নোটিশের তারিখ কী হবে?", "why_bn": "নোটিশে তারিখ আবশ্যক (বই পৃ. ১২০)।"},
    ],
    "partnership_deed": [
        *_party("partner_one", "partner_one", "প্রথম অংশীদার"),
        *_party("partner_two", "partner_two", "দ্বিতীয় অংশীদার"),
        {"field": "firm_name", "label_bn": "ফার্মের নাম", "kind": "fact", "critical": True, "question_bn": "অংশীদারি ফার্মের নাম কী?", "why_bn": "ফার্মের নাম ও ঠিকানা আবশ্যক (বই পৃ. ৬৮)।"},
        {"field": "firm_address", "label_bn": "ফার্মের প্রধান কার্যালয়", "kind": "fact", "critical": True, "question_bn": "ফার্মের প্রধান কার্যালয়ের ঠিকানা কী?", "why_bn": "বইয়ের নমুনায় প্রধান ঠিকানা উল্লেখ আছে (পৃ. ৬৮)।"},
        {"field": "business_nature", "label_bn": "ব্যবসার ধরন", "kind": "fact", "critical": True, "question_bn": "কী ব্যবসা হবে?", "why_bn": "ব্যবসার উদ্দেশ্য আইনসম্মত হতে হবে (চুক্তি আইন ধারা ২৩)।"},
        {"field": "capital_contribution", "label_bn": "মূলধন ও অবদান", "kind": "fact", "critical": True, "question_bn": "মোট মূলধন কত এবং কে কত দেবেন?", "why_bn": "মূলধন ও অংশ স্পষ্ট থাকতে হবে (বই পৃ. ৬৮)।"},
        {"field": "profit_sharing_ratio", "label_bn": "লাভ-লোকসান বণ্টন", "kind": "fact", "critical": True, "question_bn": "লাভ-লোকসান কোন অনুপাতে ভাগ হবে?", "why_bn": "বণ্টন অনুপাত না থাকলে অংশীদারি আইন ১৯৩২, ধারা ১৩ অনুযায়ী সমান ভাগ ধরা হয়।"},
        {"field": "bank_signatories", "label_bn": "ব্যাংক হিসাব পরিচালনা", "kind": "term", "critical": False, "question_bn": "ব্যাংক হিসাব কার/কাদের স্বাক্ষরে চলবে?", "why_bn": "বইয়ের নমুনায় যৌথ স্বাক্ষর (পৃ. ৬৯)।", "suggestion": "সকল অংশীদারের যৌথ স্বাক্ষরে"},
        {"field": "commencement_date", "label_bn": "শুরুর তারিখ", "kind": "fact", "critical": True, "question_bn": "অংশীদারি কবে থেকে শুরু?", "why_bn": "কার্যকর তারিখ আবশ্যক।"},
        *_EXECUTION,
    ],
    "sale_agreement": [
        *_party("seller", "seller_name", "বিক্রেতা"),
        *_party("buyer", "buyer_name", "ক্রেতা"),
        {"field": "seller_title_source", "label_bn": "বিক্রেতার মালিকানার উৎস", "kind": "fact", "critical": True, "question_bn": "বিক্রেতা কীভাবে মালিক হয়েছেন (ক্রয় দলিল নং ও সাল / ওয়ারিশ সূত্রে / নামজারি খতিয়ান নং)?", "why_bn": "স্বত্বের ধারাবাহিকতা (বায়া দলিল) উল্লেখ না থাকলে জাল দলিল ও মালিকানা বিরোধের ঝুঁকি থাকে।"},
        {"field": "property_schedule", "label_bn": "সম্পত্তির তফসিল", "kind": "fact", "critical": True, "question_bn": "জেলা, থানা, মৌজা, জে.এল নং, খতিয়ান, দাগ নং ও জমির পরিমাণ কী?", "why_bn": "তফসিল ছাড়া রেজিস্ট্রি হয় না এবং সুনির্দিষ্ট প্রতিকার মামলা করা যায় না।"},
        {"field": "boundaries", "label_bn": "চৌহদ্দি", "kind": "fact", "critical": False, "question_bn": "জমির উত্তর, দক্ষিণ, পূর্ব, পশ্চিমে কী আছে?", "why_bn": "বইয়ের নমুনায় 'Being butted and bounded' অংশে চৌহদ্দি দেওয়া হয়েছে (পৃ. ১২৮)।"},
        {"field": "total_price_bdt", "label_bn": "মোট মূল্য", "kind": "fact", "critical": True, "question_bn": "মোট বিক্রয়মূল্য কত?", "why_bn": "প্রতিদান আবশ্যক।"},
        {"field": "earnest_money_bdt", "label_bn": "বায়নার টাকা", "kind": "fact", "critical": True, "question_bn": "বায়না হিসেবে কত টাকা দেওয়া হচ্ছে/হয়েছে?", "why_bn": "বায়নার পরিমাণ ও প্রাপ্তিস্বীকার আবশ্যক।"},
        {"field": "completion_deadline", "label_bn": "সাফ কবলা রেজিস্ট্রির শেষ সময়", "kind": "fact", "critical": True, "question_bn": "অবশিষ্ট টাকা পরিশোধ ও সাফ কবলা রেজিস্ট্রি কত দিনের মধ্যে?", "why_bn": "সময়সীমা না থাকলে সুনির্দিষ্ট প্রতিকার আইনে দাবি দুর্বল হয়।"},
        *_EXECUTION,
    ],
    "loan_agreement": [
        *_party("lender", "lender_name", "ঋণদাতা"),
        *_party("borrower", "borrower_name", "ঋণগ্রহীতা"),
        {"field": "loan_amount_bdt", "label_bn": "ঋণের পরিমাণ", "kind": "fact", "critical": True, "question_bn": "কত টাকা ঋণ দেওয়া হয়েছে?", "why_bn": "প্রতিদান আবশ্যক।"},
        {"field": "payment_mode", "label_bn": "টাকা কীভাবে দেওয়া হয়েছে", "kind": "fact", "critical": True, "question_bn": "টাকা নগদে নাকি ব্যাংক/চেকে দেওয়া হয়েছে (তারিখসহ)?", "why_bn": "টাকা হস্তান্তরের প্রমাণ না থাকলে আদায় মামলায় প্রমাণ কঠিন।"},
        {"field": "loan_purpose", "label_bn": "ঋণের উদ্দেশ্য", "kind": "fact", "critical": False, "question_bn": "ঋণের উদ্দেশ্য কী?", "why_bn": "উদ্দেশ্য আইনসম্মত হতে হবে (চুক্তি আইন ধারা ২৩)।"},
        {"field": "repayment_deadline", "label_bn": "পরিশোধের সময়সূচি", "kind": "fact", "critical": True, "question_bn": "কবে বা কোন কিস্তিতে টাকা ফেরত দেবেন?", "why_bn": "পরিশোধের সময় নির্ধারিত না থাকলে তামাদি গণনা নিয়ে বিরোধ হয়।"},
        {"field": "security_details", "label_bn": "জামানত", "kind": "fact", "critical": False, "question_bn": "ঋণের বিপরীতে কোনো চেক বা জামানত দেওয়া হয়েছে কি?", "why_bn": "জামানতের বিবরণ স্পষ্ট থাকা উচিত।"},
        *_EXECUTION,
    ],
    "nda": [
        {"field": "disclosing_party", "label_bn": "তথ্য প্রকাশকারী পক্ষ", "kind": "fact", "critical": True, "question_bn": "তথ্য প্রকাশকারী পক্ষের নাম কী?", "why_bn": "পক্ষ শনাক্তকরণ আবশ্যক।"},
        {"field": "disclosing_party_address", "label_bn": "প্রকাশকারীর ঠিকানা", "kind": "fact", "critical": True, "question_bn": "প্রকাশকারী পক্ষের ঠিকানা কী?", "why_bn": "ঠিকানা আবশ্যক (বই পৃ. ৪৫)।"},
        {"field": "receiving_party", "label_bn": "তথ্য গ্রহণকারী পক্ষ", "kind": "fact", "critical": True, "question_bn": "তথ্য গ্রহণকারী পক্ষের নাম কী?", "why_bn": "পক্ষ শনাক্তকরণ আবশ্যক।"},
        {"field": "receiving_party_address", "label_bn": "গ্রহণকারীর ঠিকানা", "kind": "fact", "critical": True, "question_bn": "গ্রহণকারী পক্ষের ঠিকানা কী?", "why_bn": "ঠিকানা আবশ্যক।"},
        {"field": "confidential_matter", "label_bn": "গোপনীয় বিষয়", "kind": "fact", "critical": True, "question_bn": "কোন প্রকল্প/বিষয়ের তথ্য গোপন রাখতে হবে?", "why_bn": "গোপনীয় তথ্যের সংজ্ঞা অস্পষ্ট হলে চুক্তি বলবৎ করা কঠিন।"},
        {"field": "duration_years", "label_bn": "গোপনীয়তার মেয়াদ", "kind": "term", "critical": False, "question_bn": "কত বছর গোপনীয়তা বহাল থাকবে?", "why_bn": "মেয়াদ আবশ্যক।", "suggestion": 3},
        {"field": "effective_date", "label_bn": "কার্যকর তারিখ", "kind": "fact", "critical": True, "question_bn": "কবে থেকে কার্যকর?", "why_bn": "কার্যকর তারিখ আবশ্যক।"},
        *_EXECUTION,
    ],
    "service_agreement": [
        {"field": "client_name", "label_bn": "ক্লায়েন্টের নাম", "kind": "fact", "critical": True, "question_bn": "ক্লায়েন্ট (সেবা গ্রহণকারী) কে?", "why_bn": "পক্ষ শনাক্তকরণ আবশ্যক।"},
        {"field": "client_address", "label_bn": "ক্লায়েন্টের ঠিকানা", "kind": "fact", "critical": True, "question_bn": "ক্লায়েন্টের ঠিকানা কী?", "why_bn": "ঠিকানা আবশ্যক।"},
        {"field": "service_provider_name", "label_bn": "সেবা প্রদানকারীর নাম", "kind": "fact", "critical": True, "question_bn": "সেবা প্রদানকারী কে?", "why_bn": "পক্ষ শনাক্তকরণ আবশ্যক।"},
        {"field": "service_provider_address", "label_bn": "সেবা প্রদানকারীর ঠিকানা", "kind": "fact", "critical": True, "question_bn": "সেবা প্রদানকারীর ঠিকানা কী?", "why_bn": "ঠিকানা আবশ্যক।"},
        {"field": "scope_of_work", "label_bn": "কাজের পরিধি", "kind": "fact", "critical": True, "question_bn": "ঠিক কী কী কাজ/ডেলিভারেবল দিতে হবে?", "why_bn": "প্রত্যেক পক্ষের দায়িত্ব (Performances) স্পষ্ট থাকতে হবে (বই পৃ. ৪৫)।"},
        {"field": "service_fee_bdt", "label_bn": "সেবামূল্য", "kind": "fact", "critical": True, "question_bn": "মোট ফি কত এবং কীভাবে কিস্তিতে পরিশোধ হবে?", "why_bn": "প্রতিদান আবশ্যক।"},
        {"field": "delivery_deadline", "label_bn": "সময়সীমা", "kind": "fact", "critical": True, "question_bn": "কাজ শেষ করার সময়সীমা কবে?", "why_bn": "বিলম্ব (Delay) ধারা প্রয়োগে সময়সীমা আবশ্যক (বই পৃ. ৪৫)।"},
        *_EXECUTION,
    ],
    "custom": [
        {"field": "custom_matter_name", "label_bn": "চুক্তির নাম", "kind": "fact", "critical": True, "question_bn": "চুক্তির শিরোনাম কী?", "why_bn": "চুক্তির নাম আবশ্যক (বই পৃ. ৪৫)।"},
        *_party("party_one", "party_one_name", "প্রথম পক্ষ", company_possible=True),
        *_party("party_two", "party_two_name", "দ্বিতীয় পক্ষ", company_possible=True),
        {"field": "purpose_and_consideration", "label_bn": "উদ্দেশ্য ও প্রতিদান", "kind": "fact", "critical": True, "question_bn": "চুক্তির উদ্দেশ্য কী এবং মোট প্রতিদান/মূল্য কত?", "why_bn": "প্রতিদান ও বৈধ উদ্দেশ্য ছাড়া চুক্তি বৈধ নয় (চুক্তি আইন ধারা ১০, ২৩)।"},
        {"field": "obligations_first_party", "label_bn": "প্রথম পক্ষের দায়িত্ব", "kind": "fact", "critical": True, "question_bn": "প্রথম পক্ষ কী কী করবেন?", "why_bn": "প্রত্যেক পক্ষের দায়িত্ব স্পষ্ট থাকতে হবে (বই পৃ. ৪৫)।"},
        {"field": "obligations_second_party", "label_bn": "দ্বিতীয় পক্ষের দায়িত্ব", "kind": "fact", "critical": True, "question_bn": "দ্বিতীয় পক্ষ কী কী করবেন?", "why_bn": "প্রত্যেক পক্ষের দায়িত্ব স্পষ্ট থাকতে হবে (বই পৃ. ৪৫)।"},
        {"field": "effective_date", "label_bn": "কার্যকর তারিখ", "kind": "fact", "critical": True, "question_bn": "চুক্তি কবে থেকে কার্যকর?", "why_bn": "কার্যকর তারিখ আবশ্যক।"},
        {"field": "breach_and_cure_period", "label_bn": "চুক্তিভঙ্গ ও প্রতিকার", "kind": "term", "critical": False, "question_bn": "চুক্তিভঙ্গ হলে কত দিনের মধ্যে সংশোধনের সুযোগ থাকবে?", "why_bn": "ডিফল্ট ধারা (বই পৃ. ৪৫)।", "suggestion": "লিখিত নোটিশ প্রাপ্তির ১৫ দিনের মধ্যে সংশোধন; অন্যথায় ক্ষতিপূরণসহ চুক্তি বাতিলযোগ্য"},
        {"field": "termination_and_dispute", "label_bn": "অবসান ও বিরোধ নিষ্পত্তি", "kind": "term", "critical": False, "question_bn": "চুক্তি শেষ করার নোটিশ ও বিরোধ নিষ্পত্তির ফোরাম কী?", "why_bn": "অবসান ও বিরোধ নিষ্পত্তি বাধ্যতামূলক উপাদান (বই পৃ. ৪৫)।", "suggestion": "৩০ দিনের লিখিত নোটিশ; বিরোধে সালিশ আইন ২০০১ অনুযায়ী সালিশ"},
        *_EXECUTION,
    ],
}

TEMPLATE_TO_MATTER = {
    "BD_COMMERCIAL_LEASE": "commercial_lease", "COMMERCIAL_LEASE": "commercial_lease",
    "BD_RESIDENTIAL_LEASE": "residential_rent", "RESIDENTIAL_RENT": "residential_rent",
    "BD_EMPLOYMENT_AGREEMENT": "employment_agreement", "EMPLOYMENT_AGREEMENT": "employment_agreement",
    "BD_LEGAL_NOTICE_NI_ACT": "demand_notice_ni_act", "DEMAND_NOTICE_NI_ACT": "demand_notice_ni_act", "LEGAL_NOTICE": "demand_notice_ni_act",
    "BD_PARTNERSHIP_DEED": "partnership_deed", "PARTNERSHIP_DEED": "partnership_deed", "PARTNERSHIP": "partnership_deed",
    "BD_SALE_AGREEMENT": "sale_agreement", "SALE_AGREEMENT": "sale_agreement", "PROPERTY_SALE": "sale_agreement", "LAND_SALE": "sale_agreement",
    "BD_LOAN_AGREEMENT": "loan_agreement", "LOAN_AGREEMENT": "loan_agreement", "HAWLAT_NAMA": "loan_agreement", "MONEY_LOAN": "loan_agreement",
    "BD_NDA": "nda", "NDA": "nda", "NON_DISCLOSURE": "nda",
    "BD_SERVICE_AGREEMENT": "service_agreement", "SERVICE_AGREEMENT": "service_agreement", "VENDOR_AGREEMENT": "service_agreement",
    "BD_CUSTOM_AGREEMENT": "custom", "CUSTOM_AGREEMENT": "custom", "CUSTOM": "custom",
}

MATTER_TO_TEMPLATE = {
    "commercial_lease": "BD_COMMERCIAL_LEASE", "residential_rent": "BD_RESIDENTIAL_LEASE",
    "employment_agreement": "BD_EMPLOYMENT_AGREEMENT", "demand_notice_ni_act": "BD_LEGAL_NOTICE_NI_ACT",
    "partnership_deed": "BD_PARTNERSHIP_DEED", "sale_agreement": "BD_SALE_AGREEMENT",
    "loan_agreement": "BD_LOAN_AGREEMENT", "nda": "BD_NDA", "service_agreement": "BD_SERVICE_AGREEMENT",
    "custom": "BD_CUSTOM_AGREEMENT",
}


def is_blank(value: Any) -> bool:
    return value is None or (isinstance(value, str) and not value.strip()) or value == []


def looks_like_company(name: Optional[str]) -> bool:
    n = (name or "").lower()
    return any(k in n for k in ("ltd", "limited", "plc", "লিমিটেড", "কোম্পানি", "company", "bank", "ব্যাংক", "corporation"))


def requirements_for(matter_type: str) -> List[Req]:
    return REQUIREMENTS.get(matter_type, REQUIREMENTS["custom"])


def missing_requirements(matter_type: str, facts: Dict[str, Any], include_terms: bool = True) -> List[Req]:
    missing = []
    for req in requirements_for(matter_type):
        if req.get("only_if_company"):
            name_req = next((r for r in requirements_for(matter_type) if r["field"].startswith(req["only_if_company"]) and "নাম" in r["label_bn"]), None)
            if not name_req or not looks_like_company(facts.get(name_req["field"])):
                continue
        if req["kind"] == "term" and not include_terms:
            continue
        # Parentage, NID and permanent address apply to natural persons, not to a company party
        person_only = ("_father", "_mother", "_nid", "_permanent_address", "_relation")
        if req["field"].endswith(person_only):
            prefix = req["field"].rsplit("_", 1)[0].replace("_permanent", "")
            name_val = facts.get(f"{prefix}_name", facts.get(prefix))
            if looks_like_company(name_val):
                continue
        if is_blank(facts.get(req["field"])):
            missing.append(req)
    return missing
