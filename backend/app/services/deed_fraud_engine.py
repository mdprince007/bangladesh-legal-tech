from typing import Dict, Any, List, Tuple

class DeedFraudEngine:
    @staticmethod
    def audit_deed_authenticity(deed_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Runs rigorous Bangladesh property law consistency and fraud detection audits on a deed.
        Returns fraud_risk_score (0-100), risk_level, red_flags, passed_checks, and legal_recommendation.
        """
        red_flags: List[Dict[str, str]] = []
        passed_checks: List[str] = []
        risk_score = 0

        year = deed_data.get("registration_year")
        schedule = deed_data.get("schedule") or {}
        parties = deed_data.get("parties") or {}
        chain = deed_data.get("chain_of_title") or {}
        financials = deed_data.get("financials") or {}
        unclear_texts = deed_data.get("unclear_texts") or []

        # 1. Survey Chronology Check (জরিপ কালানুক্রমিক অসংগতি)
        # CS: 1888-1940, SA: 1956-1962, RS: 1965-1995, BS/City: 1998+
        if year:
            has_rs = bool(schedule.get("khatian_rs"))
            has_bs = bool(schedule.get("khatian_bs"))
            has_sa = bool(schedule.get("khatian_sa"))

            if year < 1956 and (has_sa or has_rs or has_bs):
                risk_score += 45
                red_flags.append({
                    "severity": "CRITICAL",
                    "title": "জরিপের কালানুক্রমিক জালিয়াতি (Impossible Survey Chronology)",
                    "message_bangla": f"দলিলটি {year} সালের দাবি করা হলেও এতে এস.এ বা আর.এস/বি.এস খতিয়ানের উল্লেখ রয়েছে। বাংলাদেশে এস.এ জরিপ ১৯৫৬ সালের পূর্বে এবং আর.এস জরিপ ১৯৬৫ সালের পূর্বে সম্পন্ন হয়নি। এটি একটি সুস্পষ্ট জাল দলিলের লক্ষণ।"
                })
            elif year < 1965 and (has_rs or has_bs):
                risk_score += 35
                red_flags.append({
                    "severity": "HIGH",
                    "title": "আর.এস/বি.এস জরিপের অসময়োপযোগী উপস্থিতি",
                    "message_bangla": f"দলিলটি {year} সালের, অথচ এতে আর.এস/সিটি জরিপ খতিয়ান লিপিবদ্ধ আছে যা এই সালে প্রচলিত ছিল না।"
                })
            else:
                passed_checks.append("জরিপের কালানুক্রমিক সামঞ্জস্য (CS/SA/RS Timeline) সন্তোষজনক।")

        # 2. Chain of Title (বায়া দলিল) Check
        prior_year = chain.get("prior_deed_year")
        if prior_year and year:
            if prior_year >= year:
                risk_score += 50
                red_flags.append({
                    "severity": "CRITICAL",
                    "title": "বায়া দলিলের তারিখের অসংগতি (Chain of Title Anomaly)",
                    "message_bangla": f"বর্তমান দলিলের সাল ({year}) বায়া দলিলের সাল ({prior_year})-এর পূর্ববর্তী বা সমান। আগের দলিলের পূর্বে বর্তমান দলিল সম্পাদিত হতে পারে না।"
                })
            else:
                passed_checks.append(f"বায়া দলিলের ধারাবাহিকতা সঠিক (পূর্ববর্তী দলিল {prior_year} সাল -> বর্তমান দলিল {year} সাল)।")
        elif not chain.get("prior_deed_number") and deed_data.get("deed_type") == "saf_kabala":
            # Saf-kabala without prior title chain
            risk_score += 15
            red_flags.append({
                "severity": "MEDIUM",
                "title": "বায়া দলিলের তথ্যের অনুপস্থিতি",
                "message_bangla": "দলিলটিতে বিক্রেতার মালিকানা অর্জনের পূর্বসূত্র (বায়া দলিল বা পৈত্রিক ওয়ারিশান খতিয়ান) সুস্পষ্টভাবে উল্লেখ নেই।"
            })

        # 3. Share Math Check (আনা-গণ্ডা অংশের গাণিতিক হিসাব)
        transferred_share = schedule.get("share_portion") or ""
        acquired_share = chain.get("acquired_share") or ""
        if "আনা" in str(transferred_share) and "আনা" in str(acquired_share):
            try:
                import re
                t_val = float(re.findall(r'(\d+)', str(transferred_share))[0])
                a_val = float(re.findall(r'(\d+)', str(acquired_share))[0])
                if t_val > a_val:
                    risk_score += 40
                    red_flags.append({
                        "severity": "CRITICAL",
                        "title": "অতিরিক্ত হিস্যা বিক্রয়ের অসংগতি (Over-transfer of Share)",
                        "message_bangla": f"বিক্রেতার স্বত্ব ছিল {acquired_share}, কিন্তু তিনি হস্তান্তর করছেন {transferred_share}। নিজের হিস্যার চেয়ে বেশি জমি বিক্রয় অবৈধ।"
                    })
            except Exception:
                pass

        # 4. Faded & Ambiguous Handwriting Risk (অস্পষ্ট হস্তাক্ষর ঝুঁকি)
        unclear_count = len(unclear_texts)
        if unclear_count >= 3:
            risk_score += 20
            red_flags.append({
                "severity": "HIGH",
                "title": "গুরুত্বপূর্ণ আইনি শব্দ বা নামের অস্পষ্টতা",
                "message_bangla": f"দলিলটির {unclear_count}টি প্রধান অংশে হাতের লেখা অত্যন্ত ঝাপসা বা বিকৃত। বালাম বহির মূল ভলিউম ছাড়া এর পাঠ চূড়ান্ত করা ঝুঁকিপূর্ণ।"
            })
        elif unclear_count > 0:
            risk_score += 10
            red_flags.append({
                "severity": "LOW",
                "title": "কিছু হস্তলিপি অস্পষ্ট",
                "message_bangla": f"{unclear_count}টি স্থানে বিকল্প পাঠ (Alternative Readings) চিহ্নিত করা হয়েছে।"
            })
        else:
            passed_checks.append("দলিলের মূল পাঠ ও পক্ষগণের নাম স্পষ্ট ও পাঠযোগ্য।")

        # 5. Missing Sub-Registry Office or Deed Number
        if not deed_data.get("sub_registry_office") or not deed_data.get("deed_number"):
            risk_score += 15
            red_flags.append({
                "severity": "MEDIUM",
                "title": "দলিল নম্বর বা সাব-রেজিস্ট্রি অফিসের তথ্যে ঘাটতি",
                "message_bangla": "দলিল নম্বর অথবা সংশ্লিষ্ট সাব-রেজিস্ট্রি অফিসের নাম অস্পষ্ট বা অনুল্লেখিত।"
            })
        else:
            passed_checks.append(f"সাব-রেজিস্ট্রি অফিস ({deed_data.get('sub_registry_office')}) ও দলিল নং ({deed_data.get('deed_number')}) সুরক্ষিত।")

        # 6. Attestation / Identifier Check
        if not parties.get("identifier_name"):
            risk_score += 10
            red_flags.append({
                "severity": "LOW",
                "title": "শনাক্তকারীর পূর্ণাঙ্গ তথ্যের ঘাটতি",
                "message_bangla": "দলিল সম্পাদনকালে সনাক্তকারীর পূর্ণাঙ্গ নাম বা ঠিকানা স্পষ্টভাবে পাওয়া যায়নি।"
            })
        else:
            passed_checks.append(f"শনাক্তকারীর বিবরণ লিপিবদ্ধ আছে ({parties.get('identifier_name')})।")

        # Clamp risk score
        risk_score = min(100, max(0, risk_score))

        # Risk level determination
        if risk_score >= 55:
            risk_level = "high_risk_probable_forgery"
            recommendation = (
                "সতর্কতা: দলিলটিতে একাধিক চরম কালানুক্রমিক ও স্বত্বগত অসংগতি রয়েছে যা সাধারণত জাল বা ভুয়া দলিলের ক্ষেত্রে ঘটে। "
                "এই দলিলের ভিত্তিতে কোনো আর্থিক লেনদেন বা বায়না করবেন না। অতিসত্বর সংশ্লিষ্ট সাব-রেজিস্ট্রি অফিসে 'বালাম বহি' (Volume Book) "
                "তল্লাশ দিন এবং এসি ল্যান্ড অফিসে নামজারি প্রস্তাবপত্রের নথিজাত সত্যতা যাচাই করুন।"
            )
        elif risk_score >= 25:
            risk_level = "suspicious"
            recommendation = (
                "পর্যবেক্ষণ: দলিলটিতে কিছু অসংগতি ও অস্পষ্ট হাতের লেখা রয়েছে। বায়া দলিলের ধারাবাহিকতা এবং সাব-রেজিস্ট্রারের সিলমোহর "
                "যাচাইয়ের জন্য মূল দলিল বা সার্টিফাইড নকল (Certified Copy) সংগ্রহ করে তল্লাশি দেওয়ার পরামর্শ দেওয়া হচ্ছে।"
            )
        else:
            risk_level = "low"
            recommendation = (
                "দলিলটির প্রাথমিক আইনি নিরীক্ষা সন্তোষজনক। জরিপের কালানুক্রম ও বায়া দলিলের ধারাবাহিকতা সামঞ্জস্যপূর্ণ। "
                "জমি ক্রয় বা লিজের চূড়ান্ত সিদ্ধান্তের পূর্বে সাব-রেজিস্ট্রি অফিস থেকে গত ১২ বছরের এনইসি (Non-Encumbrance Certificate) "
                "এবং হালসালের ভূমি উন্নয়ন কর (খাজনা) রসিদ যাচাই সম্পন্ন করুন।"
            )

        return {
            "fraud_risk_score": risk_score,
            "fraud_risk_level": risk_level,
            "red_flags": red_flags,
            "passed_checks": passed_checks,
            "legal_recommendation": recommendation
        }

deed_fraud_engine = DeedFraudEngine()
