from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.models.legal_knowledge import Law, LawSection

VERIFIED_PROBLEM_PLAYBOOKS = {
    "cheque_dishonour": {
        "title": "চেক ডিজঅনার ও বকেয়া টাকা আদায় (Cheque Dishonour Dispute)",
        "keywords": ["চেক", "cheque", "dishonour", "বাউন্স", "bounce", "টাকা দিচ্ছে না", "ধারের টাকা", "পাওনা টাকা"],
        "applicable_laws": [
            "The Negotiable Instruments Act, 1881 (Section 138 & 140)",
            "The Code of Criminal Procedure, 1898",
            "The Limitation Act, 1908"
        ],
        "roadmap_steps": [
            {
                "step_no": 1,
                "title": "ব্যাংক ডিজঅনার মেমো ও প্রমাণ সংগ্রহ",
                "timeline": "চেক মেয়াদের (৬ মাস) মধ্যে",
                "action": "চেকটি ব্যাংকে জমা দিয়ে ব্যাংক কর্মকর্তা কর্তৃক স্বাক্ষরিত 'Cheque Return Memo' (ডিজঅনার স্লিপ) সংগ্রহ করুন। স্লিপে প্রত্যাখ্যাত হওয়ার কারণ (যেমন: Insufficient Funds) স্পষ্ট থাকতে হবে।"
            },
            {
                "step_no": 2,
                "title": "সংবিধিবদ্ধ আইনি ডিমান্ড নোটিশ প্রেরণ (Statutory Legal Notice)",
                "timeline": "মেমো পাওয়ার দিন থেকে ৩০ দিনের মধ্যে",
                "action": "কোনো বিজ্ঞ আইনজীবীর মাধ্যমে রেজিস্ট্রি ডাকযোগে (AD সহ) অথবা সরাসরি রসিদ নিয়ে দেনাদারকে ১৩৮(খ) ধারা অনুযায়ী ৩০ দিনের মধ্যে টাকা পরিশোধের চূড়ান্ত আইনি নোটিশ পাঠান।"
            },
            {
                "step_no": 3,
                "title": "৩০ দিনের সংবিধিবদ্ধ অপেক্ষা",
                "timeline": "নোটিশ জারির পর থেকে ৩০ দিন",
                "action": "আইন অনুযায়ী দেনাদারকে টাকা পরিশোধের জন্য ৩০ দিন সময় দিতে হবে। এই ৩০ দিন অতিবাহিত না হওয়া পর্যন্ত আদালতে মামলা দায়ের করা যাবে না।"
            },
            {
                "step_no": 4,
                "title": "ম্যাজিস্ট্রেট আদালতে ফৌজদারি মামলা দায়ের (C.R. Case)",
                "timeline": "৩০ দিন শেষ হওয়ার পরবর্তী ৩০ দিনের মধ্যে (তামাদি)",
                "action": "উক্ত ৩০ দিনের মধ্যে টাকা না দিলে সংশ্লিষ্ট এলাকার চিফ মেট্রোপলিটন/জুডিশিয়াল ম্যাজিস্ট্রেট আদালতে ১৩৮ ধারায় সি.আর. মামলা দায়ের করুন। মনে রাখবেন, ৩০ দিন পার হওয়ার পর মামলা করলে তামাদি দোষে খারিজ হয়ে যাবে।"
            }
        ],
        "document_checklist": [
            "মূল ব্যাংক চেক (Original Dishonoured Cheque)",
            "ব্যাংক ডিজঅনার মেমো (Bank Return Memo)",
            "আইনি নোটিশের কপি ও ডাক রসিদ (Postal Receipt with A/D)",
            "লেনদেনের কোনো চুক্তিপত্র, ভাউচার বা প্রমাণক (যদি থাকে)"
        ],
        "risks_and_cautions": [
            "তামাদি মেয়াদ (Limitation Period) অত্যন্ত কঠোর। নোটিশ পাঠানো বা মামলা করায় ১ দিন দেরি হলেও আদালতের এখতিয়ার নষ্ট হতে পারে।",
            "চেকটি অবশ্যই কোনো বৈধ ঋণের দায় (Legal Enforceable Debt) মেটানোর উদ্দেশ্যে দেওয়া হতে হবে।"
        ],
        "recommended_action": "draft_legal_notice_ni_138"
    },
    "tenant_eviction": {
        "title": "ভাড়াটিয়া উচ্ছেদ ও বকেয়া ভাড়া আদায় (Commercial/Residential Eviction)",
        "keywords": ["দোকান ছাড়ছে না", "বাসা ছাড়ছে না", "উচ্ছেদ", "evict", "eviction", "ভাড়া দিচ্ছে না", "দোকান দখল", "ভাড়াটিয়া"],
        "applicable_laws": [
            "The Transfer of Property Act, 1882 (Section 106 & 111)",
            "The Premises Rent Control Act, 1991 (বাড়ি ভাড়া নিয়ন্ত্রণ আইন, ১৯৯১)",
            "The Code of Civil Procedure, 1908"
        ],
        "roadmap_steps": [
            {
                "step_no": 1,
                "title": "চুক্তিপত্র ও বকেয়ার হিসাব নিরীক্ষা",
                "timeline": "তাৎক্ষণিক",
                "action": "বিদ্যমান ভাড়ার চুক্তিপত্রের মেয়াদ, নোটিশ শর্ত এবং বকেয়া ভাড়ার সুনির্দিষ্ট হিসাব ও রসিদ প্রস্তুত করুন।"
            },
            {
                "step_no": 2,
                "title": "চুক্তি অবসানের আনুষ্ঠানিক আইনি নোটিশ (Termination Notice)",
                "timeline": "চুক্তি অনুযায়ী (সাধারণত ১ থেকে ২ মাস পূর্বে)",
                "action": "সম্পত্তি হস্তান্তর আইনের ১০৬ ধারা অনুযায়ী লিখিত নোটিশ দিয়ে নির্দিষ্ট মেয়াদের মধ্যে দখল খালি করে দেওয়ার নির্দেশ দিন। নোটিশে স্পষ্ট তারিখ উল্লেখ করুন।"
            },
            {
                "step_no": 3,
                "title": "বিকল্প বিরোধ নিষ্পত্তি ও স্থানীয় সালিশ (ADR)",
                "timeline": "নোটিশ চলাকালীন",
                "action": "মারামারি বা জোরপূর্বক তালা দেওয়া যাবে না। স্থানীয় গণ্যমান্য ব্যক্তি, মার্কেট সমিতি বা ওয়ার্ড কাউন্সিলরের মাধ্যমে মধ্যস্থতার চেষ্টা করুন।"
            },
            {
                "step_no": 4,
                "title": "ভাড়া আদালত বা দেওয়ানি আদালতে উচ্ছেদ মামলা (Eviction Suit)",
                "timeline": "নোটিশের মেয়াদ শেষ হওয়ার পর",
                "action": "ভাড়াটিয়া স্বেচ্ছায় জায়গা না ছাড়লে দেওয়ানি আদালতে ভাড়া নিয়ন্ত্রণ আইনের আওতায় উচ্ছেদ ও বকেয়া ভাড়া আদায়ের মামলা দায়ের করতে হবে।"
            }
        ],
        "document_checklist": [
            "মূল ভাড়ার চুক্তিপত্র (Tenancy/Lease Agreement)",
            "বকেয়া ভাড়া ও ইউটিলিটি বিলের প্রমাণক",
            "দোকান/বাড়ির মালিকানার দলিল ও খতিয়ান",
            "প্রেরিত উচ্ছেদ নোটিশ ও জবানবন্দি"
        ],
        "risks_and_cautions": [
            "কখনোই আইন নিজের হাতে তুলে নিয়ে জোরপূর্বক ভাড়াটিয়ার বিদ্যুৎ/পানি বিচ্ছিন্ন করা বা মালামাল ফেলে দিয়ে তালা দেওয়া যাবে না। এতে ভাড়াটিয়া আপনার বিরুদ্ধে ফৌজদারি মামলা (দণ্ডবিধি ৪৪৮/৪২৭/৫০৬ ধারা) করার সুযোগ পাবে।",
            "সর্বদা বৈধ আইনি নোটিশ দিয়ে নিয়মতান্ত্রিকভাবে আদালতে এগোতে হবে।"
        ],
        "recommended_action": "draft_commercial_lease_termination_notice"
    },
    "wrongful_termination": {
        "title": "চাকরি থেকে অন্যায় বরখাস্ত ও বকেয়া বেতন আদায় (Employment Grievance)",
        "keywords": ["চাকরি থেকে বের", "বরখাস্ত", "বেতন দিচ্ছে না", "terminate", "fired", "শ্রমিক", "employee", "অফিস থেকে বের"],
        "applicable_laws": [
            "The Bangladesh Labour Act, 2006 (Section 23, 24, 26, 33)",
            "The Bangladesh Labour Rules, 2015"
        ],
        "roadmap_steps": [
            {
                "step_no": 1,
                "title": "নিয়োগপত্র ও টার্মিনেশন লেটার সংরক্ষণ",
                "timeline": "তাৎক্ষণিক",
                "action": "নিয়োগপত্র (Appointment Letter), পরিচয়পত্র, বেতন স্লিপ এবং কোম্পানি কর্তৃক প্রদত্ত বরখাস্তের চিঠির কপি সংরক্ষণ করুন।"
            },
            {
                "step_no": 2,
                "title": "মালিকের কাছে লিখিত অভিযোগ বা গ্রিভেন্স নোটিশ (Section 33 Grievance)",
                "timeline": "ঘটনার ৩০ দিনের মধ্যে",
                "action": "বাংলাদেশ শ্রম আইন ২০০৬-এর ৩৩ ধারা অনুযায়ী লিখিত অভিযোগ দায়ের করে মালিক বরাবর রেজিস্ট্রি ডাকযোগে পাঠান।"
            },
            {
                "step_no": 3,
                "title": "মালিকের সিদ্ধান্তের জন্য অপেক্ষা",
                "timeline": "অভিযোগ প্রাপ্তির ৩০ দিন",
                "action": "মালিককে সিদ্ধান্ত জানানোর জন্য ৩০ দিন সময় দিতে হবে। মালিক সমাধান না করলে বা সিদ্ধান্ত অসন্তোষজনক হলে পরবর্তী পদক্ষেপে যেতে হবে।"
            },
            {
                "step_no": 4,
                "title": "শ্রম আদালতে মামলা দায়ের (Labour Court Complaint)",
                "timeline": "মালিকের সময় শেষ হওয়ার পরবর্তী ৩০ দিনের মধ্যে",
                "action": "সংশ্লিষ্ট শ্রম আদালতে (Labour Court) ৩৩(৩) ধারায় আনুষ্ঠানিক দরখাস্ত দায়ের করে পুনর্বহাল বা উপযুক্ত ক্ষতিপূরণ ও বকেয়া বেতন দাবি করুন।"
            }
        ],
        "document_checklist": [
            "নিয়োগপত্র বা চাকরির চুক্তিপত্র (Appointment Letter)",
            "সার্ভিস বুক বা উপস্থিতি ও বেতনের প্রমাণ",
            "বরখাস্তের চিঠি (যদি থাকে)",
            "৩৩ ধারার অভিযোগপত্র ও ডাক রসিদ"
        ],
        "risks_and_cautions": [
            "শ্রম আইনের ৩৩ ধারার ৩০ দিনের সময়সীমা অত্যন্ত কঠোর। অভিযোগ না পাঠিয়ে সরাসরি শ্রম আদালতে গেলে মামলা অগ্রাহ্য হতে পারে।"
        ],
        "recommended_action": "draft_employment_grievance_notice"
    }
}

class AdvisoryService:
    @staticmethod
    def provide_advisory_roadmap(user_problem_text: str, db: Session) -> Dict[str, Any]:
        """
        Legal Problem Solver & Step-by-Step Procedural Advisory Engine.
        Strict Zero-Guesswork: If verified Bangladesh legal authority is unavailable,
        it explicitly refuses to guess and flags as a knowledge gap.
        """
        text_lower = user_problem_text.lower()
        matched_playbook = None

        for key, playbook in VERIFIED_PROBLEM_PLAYBOOKS.items():
            for kw in playbook["keywords"]:
                if kw in text_lower or kw in user_problem_text:
                    matched_playbook = playbook
                    break
            if matched_playbook:
                break

        if not matched_playbook:
            # Zero-Guesswork Guardrail triggered
            return {
                "status": "UNVERIFIED_KNOWLEDGE_GAP",
                "verified": False,
                "problem_input": user_problem_text,
                "message_bangla": (
                    "⚠️ [যাচাইকৃত তথ্য অনুপস্থিত / Zero Guesswork Policy]\n\n"
                    "আপনার উল্লেখিত এই সুনির্দিষ্ট সমস্যার বিষয়ে বাংলাদেশ আইনের কোনো সরকারি বা যাচাইকৃত কার্যপ্রণালী "
                    "বর্তমানে আমাদের ডাটাবেজে আনুষ্ঠানিকভাবে সংযুক্ত করা হয়নি।\n\n"
                    "কোনো ভুল পরামর্শ বা অনুমানের মাধ্যমে আপনার আইনগত ক্ষতি এড়াতে আমরা আন্দাজে কোনো উত্তর দিচ্ছি না। "
                    "বিষয়টি আমাদের লিগ্যাল নলেজ ইম্প্রুভমেন্ট ও ট্রেইনিং প্যানেলে রেকর্ড করা হয়েছে যাতে অনুমোদিত আইনজীবী "
                    "দ্বারা এটি পরীক্ষা করে সিস্টেমে যুক্ত করা যায়।"
                ),
                "suggested_next_step": "অনুগ্রহ করে কোনো নিবন্ধিত আইনজীবীর সাথে সরাসরি পরামর্শ করুন অথবা অ্যাডমিন প্যানেলে নতুন আইন ও নথিপত্র আপলোড করে সিস্টেমকে ট্রেইন করুন।"
            }

        return {
            "status": "VERIFIED_ROADMAP",
            "verified": True,
            "problem_input": user_problem_text,
            "dispute_title": matched_playbook["title"],
            "applicable_laws": matched_playbook["applicable_laws"],
            "roadmap_steps": matched_playbook["roadmap_steps"],
            "document_checklist": matched_playbook["document_checklist"],
            "risks_and_cautions": matched_playbook["risks_and_cautions"],
            "recommended_action": matched_playbook["recommended_action"]
        }

advisory_service = AdvisoryService()
