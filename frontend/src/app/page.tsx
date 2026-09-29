"use client";

import React, { useState, useEffect } from "react";
import { 
  FileText, 
  MessageSquare, 
  ShieldAlert, 
  Database, 
  Send, 
  Sparkles, 
  Download, 
  CheckCircle2, 
  AlertTriangle, 
  Cpu, 
  Play, 
  Check, 
  Search,
  Scale,
  Compass,
  ArrowRight,
  Save,
  File
} from "lucide-react";
import DeedVerificationPanel from "./components/DeedVerificationPanel";
import ScenarioComposer from "./components/ScenarioComposer";

const API_BASE = "/api/v1";

interface ClauseItem {
  code: string;
  clause_type: string;
  title: string;
  text_content: string;
  explanation_bangla: string;
  risk_level: string;
  style: string;
  statutory_basis?: string;
  book_reference?: string;
}

interface ReviewIssue {
  id: string;
  issue_type: string;
  severity: string;
  clause_title: string;
  message_bangla: string;
  suggested_fix_bangla: string;
}

interface HealthReport {
  overall_health_score: number;
  completeness_score: number;
  risk_score: number;
  professional_review_recommended: boolean;
  plain_bangla_summary: string;
  issues: ReviewIssue[];
}

interface EvaluationResult {
  case_name: string;
  passed: boolean;
  score: number;
}

const MATTER_CONFIG: Record<string, {
  title: string;
  template_code: string;
  welcome: string;
  sample: string;
  fields: Array<{ key: string; label: string; type: "text" | "money" | "duration" | "months"; default?: string }>;
}> = {
  commercial_lease: {
    title: "বাণিজ্যিক দোকান / স্পেস ভাড়া চুক্তি",
    template_code: "BD_COMMERCIAL_LEASE",
    welcome: "স্বাগতম! বাণিজ্যিক দোকান বা অফিস স্পেস ভাড়ার চুক্তির জন্য তথ্য দিন।",
    sample: "আমি মিরপুর ঢাকায় একটা দোকান ৩ বছরের জন্য ৫০,০০০ টাকা ভাড়ায় দিতে চাই। জামানত ২ লাখ টাকা।",
    fields: [
      { key: "landlord_name", label: "মালিক (Landlord)", type: "text" },
      { key: "tenant_name", label: "ভাড়াটিয়া (Tenant)", type: "text" },
      { key: "premises_address", label: "দোকানের ঠিকানা (Location)", type: "text" },
      { key: "monthly_rent_bdt", label: "মাসিক ভাড়া (Rent)", type: "money" },
      { key: "security_deposit_bdt", label: "অগ্রিম জামানত (Deposit)", type: "money" },
      { key: "duration_months", label: "মেয়াদ (Duration)", type: "duration" },
      { key: "permitted_business_type", label: "ব্যবসার ধরন (Permitted Use)", type: "text", default: "General Commercial Retail / Office" },
      { key: "notice_period_months", label: "নোটিশ পিরিয়ড (Notice)", type: "months", default: "2" },
      { key: "commencement_date", label: "শুরুর তারিখ (Start)", type: "text", default: "01 March 2026" }
    ]
  },
  residential_rent: {
    title: "আবাসিক বাসা / ফ্ল্যাট ভাড়া চুক্তি",
    template_code: "BD_RESIDENTIAL_LEASE",
    welcome: "স্বাগতম! আবাসিক বাসা বা ফ্ল্যাট ভাড়া চুক্তিপত্রের জন্য প্রয়োজনীয় তথ্য দিন।",
    sample: "ধানমন্ডি ফ্ল্যাট ৪-বি, ভাড়া ৩৫ হাজার টাকা, ৭০ হাজার জামানত, ১ বছরের চুক্তি",
    fields: [
      { key: "landlord_name", label: "বাড়িওয়ালা (Landlord)", type: "text" },
      { key: "tenant_name", label: "ভাড়াটিয়া (Tenant)", type: "text" },
      { key: "premises_address", label: "বাসার পূর্ণ ঠিকানা ও ফ্ল্যাট নং", type: "text" },
      { key: "monthly_rent_bdt", label: "মাসিক ভাড়া (Rent)", type: "money" },
      { key: "security_deposit_bdt", label: "অগ্রিম জামানত (Deposit)", type: "money" },
      { key: "duration_months", label: "মেয়াদ (Duration)", type: "duration" },
      { key: "notice_period_months", label: "নোটিশ পিরিয়ড (Notice)", type: "months", default: "2" },
      { key: "commencement_date", label: "শুরুর তারিখ (Start)", type: "text", default: "01 March 2026" }
    ]
  },
  employment_agreement: {
    title: "চাকরির চুক্তিপত্র ও নিয়োগপত্র",
    template_code: "BD_EMPLOYMENT_AGREEMENT",
    welcome: "স্বাগতম! বাংলাদেশ শ্রম আইন ২০০৬ অনুযায়ী চাকরির নিয়োগ চুক্তিপত্র প্রস্তুত করতে তথ্য দিন।",
    sample: "কোম্পানি টেক সল্যুশনস, কর্মচারী তানভীর আহমেদ, পদ সিনিয়র সফটওয়্যার ইঞ্জিনিয়ার, মাসিক বেতন ৮০,০০০ টাকা",
    fields: [
      { key: "employer_name", label: "কোম্পানি / প্রতিষ্ঠান (Employer)", type: "text" },
      { key: "employee_name", label: "কর্মচারীর নাম (Employee)", type: "text" },
      { key: "designation", label: "পদবী (Designation)", type: "text" },
      { key: "monthly_salary_bdt", label: "মাসিক মোট বেতন (Salary)", type: "money" },
      { key: "probation_months", label: "শিক্ষানবিসকাল (Probation)", type: "months" },
      { key: "notice_period_days", label: "নোটিশ পিরিয়ড (Notice Days)", type: "text", default: "30" },
      { key: "joining_date", label: "যোগদানের তারিখ (Joining)", type: "text", default: "01 March 2026" }
    ]
  },
  demand_notice_ni_act: {
    title: "চেক ডিজঅনার আইনি নোটিশ (১৩৮ ধারা)",
    template_code: "BD_LEGAL_NOTICE_NI_ACT",
    welcome: "স্বাগতম! নেগোশিয়েবল ইন্সট্রুমেন্টস অ্যাক্ট ১৩৮ ধারায় চেক ডিজঅনারের আইনি নোটিশ তৈরিতে তথ্য দিন।",
    sample: "প্রাপক মোহাম্মদ রফিক, বিবাদী মো. শামীম, চেক নং CQ-98211, আড়াই লাখ টাকা, ডাচ্-বাংলা ব্যাংক",
    fields: [
      { key: "payee_name", label: "প্রাপক / ক্লায়েন্ট (Payee)", type: "text" },
      { key: "drawer_name", label: "বিবাদী / চেকদাতা (Drawer)", type: "text" },
      { key: "drawer_address", label: "বিবাদীর ঠিকানা (Drawer Address)", type: "text" },
      { key: "cheque_no", label: "চেক নং (Cheque No)", type: "text" },
      { key: "cheque_amount_bdt", label: "টাকার পরিমাণ (Amount)", type: "money" },
      { key: "bank_name", label: "ব্যাংক ও শাখা (Bank)", type: "text" },
      { key: "return_memo_date", label: "ডিজঅনার মেমোর তারিখ", type: "text", default: "25 February 2026" }
    ]
  },
  partnership_deed: {
    title: "অংশীদারি কারবার চুক্তিপত্র (Partnership Deed)",
    template_code: "BD_PARTNERSHIP_DEED",
    welcome: "স্বাগতম! The Partnership Act, 1932 অনুযায়ী অংশীদারি কারবার চুক্তিপত্র প্রস্তুত করতে তথ্য দিন।",
    sample: "ফার্ম ড্রিম ট্রেডার্স, ১ম অংশীদার রফিকুল ইসলাম, ২য় অংশীদার কামাল হোসেন, পাইকারি ব্যবসা, মূলধন ১০ লাখ টাকা, লাভ-ক্ষতি ৫০:৫০",
    fields: [
      { key: "firm_name", label: "ফার্মের নাম (Firm Name)", type: "text" },
      { key: "partner_one", label: "১ম অংশীদার (Partner 1)", type: "text" },
      { key: "partner_two", label: "২য় অংশীদার (Partner 2)", type: "text" },
      { key: "business_nature", label: "ব্যবসার ক্ষেত্র ও প্রকৃতি", type: "text" },
      { key: "capital_contribution", label: "মূলধন অনুপাত (Capital)", type: "text" },
      { key: "profit_sharing_ratio", label: "লাভ-ক্ষতি বণ্টনের অনুপাত", type: "text" },
      { key: "commencement_date", label: "শুরুর তারিখ (Start)", type: "text", default: "01 March 2026" }
    ]
  },
  sale_agreement: {
    title: "স্থাবর সম্পত্তি বিক্রয় বায়না চুক্তি (Sale Agreement)",
    template_code: "BD_SALE_AGREEMENT",
    welcome: "স্বাগতম! Transfer of Property Act 1882 অনুযায়ী জমি বা ফ্ল্যাট বিক্রয় বায়না চুক্তি প্রস্তুত করতে তথ্য দিন।",
    sample: "বিক্রেতা মো. করিম, ক্রেতা মো. শফিক, গুলশান ফ্ল্যাট ১২০২, মোট মূল্য ১ কোটি ২০ লাখ, বায়না ২০ লাখ, রেজিস্ট্রি ৩ মাসের মধ্যে",
    fields: [
      { key: "seller_name", label: "বিক্রেতা (Seller)", type: "text" },
      { key: "buyer_name", label: "ক্রেতা (Buyer)", type: "text" },
      { key: "property_schedule", label: "সম্পত্তির তফশিল (Schedule)", type: "text" },
      { key: "total_price_bdt", label: "মোট বিক্রয়মূল্য (Total Price)", type: "money" },
      { key: "earnest_money_bdt", label: "বায়না অগ্রিম (Earnest Money)", type: "money" },
      { key: "completion_deadline", label: "রেজিস্ট্রি সময়সীমা (Deadline)", type: "text", default: "90 days from execution" }
    ]
  },
  loan_agreement: {
    title: "হাওলাত / অর্থ ঋণ চুক্তিপত্র (Loan Agreement)",
    template_code: "BD_LOAN_AGREEMENT",
    welcome: "স্বাগতম! The Contract Act 1872 অনুযায়ী হাওলাত ও অর্থ ঋণ চুক্তিপত্র তৈরি করতে তথ্য দিন।",
    sample: "ঋণদাতা হাজী আবদুল মতিন, ঋণগ্রহীতা মো. সোহেল, ঋণ ৫ লাখ টাকা, পারিবারিক প্রয়োজনে, পরিশোধ আগামী ৩১ ডিসেম্বরের মধ্যে",
    fields: [
      { key: "lender_name", label: "ঋণদাতা (Lender)", type: "text" },
      { key: "borrower_name", label: "ঋণগ্রহীতা (Borrower)", type: "text" },
      { key: "loan_amount_bdt", label: "ঋণের মূল টাকা (Loan Amount)", type: "money" },
      { key: "loan_purpose", label: "ঋণের উদ্দেশ্য (Purpose)", type: "text" },
      { key: "repayment_deadline", label: "পরিশোধের শেষ তারিখ", type: "text", default: "31 December 2026" },
      { key: "security_details", label: "সিকিউরিটি চেক / জামানত", type: "text", default: "Personal Guarantee / Security Cheque" }
    ]
  },
  nda: {
    title: "গোপনীয়তা চুক্তি (Non-Disclosure Agreement - NDA)",
    template_code: "BD_NDA",
    welcome: "স্বাগতম! বাণিজ্যিক তথ্যের নিরাপত্তা ও মেধা সম্পদ সুরক্ষায় NDA প্রস্তুত করতে তথ্য দিন।",
    sample: "প্রকাশক ইনোভেশন ল্যাব, প্রাপক সল্যুশন আর্কিটেক্টস, সফটওয়্যার সোর্স কোড ও ক্লায়েন্ট ডেটা, মেয়াদ ২ বছর",
    fields: [
      { key: "disclosing_party", label: "তথ্য প্রকাশকারী (Discloser)", type: "text" },
      { key: "receiving_party", label: "তথ্য গ্রহণকারী (Recipient)", type: "text" },
      { key: "confidential_matter", label: "গোপনীয় বিষয় (Subject)", type: "text" },
      { key: "duration_years", label: "মেয়াদ বছর (Duration Years)", type: "text", default: "2" },
      { key: "effective_date", label: "কার্যকরের তারিখ (Start)", type: "text", default: "01 March 2026" }
    ]
  },
  service_agreement: {
    title: "পেশাদার সেবা ও প্রজেক্ট চুক্তি (Service Agreement)",
    template_code: "BD_SERVICE_AGREEMENT",
    welcome: "স্বাগতম! আইটি, সফটওয়্যার বা ভেন্ডর সেবা চুক্তিপত্র প্রস্তুত করতে তথ্য দিন।",
    sample: "ক্লায়েন্ট গ্লোবাল এন্টারপ্রাইজ, সেবা প্রদানকারী কোড ক্রাফট, ইআরপি সফটওয়্যার তৈরি, ফি ৩ লাখ টাকা, হস্তান্তর ২ মাসের মধ্যে",
    fields: [
      { key: "client_name", label: "ক্লায়েন্ট (Client)", type: "text" },
      { key: "service_provider_name", label: "সেবা প্রদানকারী (Provider)", type: "text" },
      { key: "scope_of_work", label: "কাজের পরিধি (Scope of Work)", type: "text" },
      { key: "service_fee_bdt", label: "সেবামূল্য (Service Fee)", type: "money" },
      { key: "delivery_deadline", label: "হস্তান্তরের সময়সীমা (Deadline)", type: "text", default: "60 days" }
    ]
  },
  custom: {
    title: "কাস্টম চুক্তি (Custom Agreement - নিজের মতো)",
    template_code: "BD_CUSTOM_AGREEMENT",
    welcome: "স্বাগতম! আপনি যেকোনো ধরনের চুক্তি বা দলিল তৈরি করতে পারেন। চুক্তির নাম, উভয় পক্ষ এবং মূল শর্তাবলী বলুন।",
    sample: "চুক্তি: পণ্য সরবরাহ চুক্তি, ১ম পক্ষ সুপার স্টোর, ২য় পক্ষ এগ্রো ফার্ম, প্রতি মাসে ৫ টন চাল সরবরাহ, মূল্য ৩ লাখ টাকা, ১৫ দিনের নোটিশে বাতিল",
    fields: [
      { key: "custom_matter_name", label: "চুক্তির নাম (Contract Title)", type: "text" },
      { key: "party_one_name", label: "১ম পক্ষ (First Party)", type: "text" },
      { key: "party_two_name", label: "২য় পক্ষ (Second Party)", type: "text" },
      { key: "purpose_and_consideration", label: "উদ্দেশ্য ও প্রতিদান/মূল্য", type: "text" },
      { key: "obligations_first_party", label: "১ম পক্ষের দায়িত্ব ও করণীয়", type: "text" },
      { key: "obligations_second_party", label: "২য় পক্ষের দায়িত্ব ও ডেলিভারি", type: "text" },
      { key: "breach_and_cure_period", label: "শর্তভঙ্গ ও নোটিশের মেয়াদ (Cure)", type: "text", default: "15 days written cure period" },
      { key: "termination_and_dispute", label: "চুক্তি অবসান ও বিরোধ নিষ্পত্তি", type: "text", default: "Arbitration in Dhaka under Arbitration Act 2001" }
    ]
  }
};

export default function Home() {
  const [activeTab, setActiveTab] = useState<"advisory" | "intake" | "drafting" | "review" | "knowledge" | "deed">("advisory");
  const [matterType, setMatterType] = useState("commercial_lease");
  const [lastAskedField, setLastAskedField] = useState<string | null>(null);
  const [customTitle, setCustomTitle] = useState("");
  const [chatMessages, setChatMessages] = useState<Array<{ role: string; content: string }>>([
    {
      role: "assistant",
      content: "স্বাগতম! আপনি কী ধরনের চুক্তি প্রস্তুত করতে চান? উদাহরণ: 'আমি মিরপুর ঢাকায় একটা দোকান ৩ বছরের জন্য ৫০,০০০ টাকা ভাড়ায় দিতে চাই। জামানত ২ লাখ টাকা।'"
    }
  ]);
  const [userInput, setUserInput] = useState("");
  const [currentFacts, setCurrentFacts] = useState<Record<string, any>>({});
  const [completionPct, setCompletionPct] = useState(0);


  // Deed Intelligence State
  const [currentDeed, setCurrentDeed] = useState<any | null>(null);
  const [isEnhancedContrast, setIsEnhancedContrast] = useState(true);
  const [deedLoading, setDeedLoading] = useState(false);
  const [isEditingDeed, setIsEditingDeed] = useState(false);
  const [deedEditForm, setDeedEditForm] = useState<any>({
    first_party_name: "",
    second_party_name: "",
    mouza: "",
    registration_year: 1993,
    deed_number: "",
    khatian_sa: "",
    dag_current: "",
    transferred_area_decimals: 10
  });

  // Problem Advisory State
  const [advisoryProblem, setAdvisoryProblem] = useState("");
  const [advisoryLoading, setAdvisoryLoading] = useState(false);
  const [advisoryResult, setAdvisoryResult] = useState<any | null>(null);

  // Drafting state
  const [documentId, setDocumentId] = useState<string | null>(null);
  const [docTitle, setDocTitle] = useState("Commercial Lease Agreement");
  const [fullText, setFullText] = useState("চুক্তিপত্র এখনো প্রস্তুত হয়নি। প্রথমে 'আইনি সাক্ষাৎকার' ট্যাবে তথ্য দিয়ে 'Generate Draft' ক্লিক করুন।");
  const [selectedClauses, setSelectedClauses] = useState<ClauseItem[]>([]);
  const [docxUrl, setDocxUrl] = useState<string | null>(null);
  const [pdfUrl, setPdfUrl] = useState<string | null>(null);
  const [docVersion, setDocVersion] = useState(1);
  const [bookGroundingScore, setBookGroundingScore] = useState<number | null>(null);
  const [bookChapterRef, setBookChapterRef] = useState<string | null>(null);
  const [bookAppliedRules, setBookAppliedRules] = useState<string[]>([]);
  const [missingInfo, setMissingInfo] = useState<any[]>([]);
  const [bookChecklist, setBookChecklist] = useState<any[]>([]);
  const [draftWarnings, setDraftWarnings] = useState<string[]>([]);
  const [lastDraftRequest, setLastDraftRequest] = useState<{ templateCode: string; facts: Record<string, any> } | null>(null);
  const [missingAnswers, setMissingAnswers] = useState<Record<string, string>>({});

  const handleSaveDocumentEdits = async () => {
    if (!documentId) {
      alert("প্রথমে একটি চুক্তিপত্র ড্রাফট তৈরি করুন।");
      return;
    }
    try {
      const res = await fetch(`${API_BASE}/documents/${documentId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          full_text: fullText,
          change_summary: "Manual customization in Drafting Studio"
        })
      });
      if (res.ok) {
        const doc = await res.json();
        setDocVersion(v => v + 1);
        setFullText(doc.full_text);
        setDocxUrl(doc.docx_url);
        setPdfUrl(doc.pdf_url);
        const reviewRes = await fetch(`${API_BASE}/review/${doc.id}/health`);
        if (reviewRes.ok) {
          const revData = await reviewRes.json();
          setHealthReport(revData);
        }
        alert("চুক্তিপত্র সফলভাবে সংরক্ষিত হয়েছে এবং নতুন সংস্করণ তৈরি হয়েছে!");
      } else {
        alert("সংরক্ষণ ব্যর্থ হয়েছে।");
      }
    } catch (e) {
      alert("সংরক্ষণে ত্রুটি হয়েছে: " + e);
    }
  };

  // Review state
  const [healthReport, setHealthReport] = useState<HealthReport | null>(null);

  // Knowledge & Eval state
  const [statutes, setStatutes] = useState<any[]>([]);
  const [verifyAct, setVerifyAct] = useState("Transfer of Property Act");
  const [verifySec, setVerifySec] = useState("106");
  const [verifyResult, setVerifyResult] = useState<any | null>(null);
  const [evalResults, setEvalResults] = useState<EvaluationResult[]>([]);
  const [evalAccuracy, setEvalAccuracy] = useState<number>(100);
  const [feedbackNote, setFeedbackNote] = useState("");

  useEffect(() => {
    fetchStatutes();
    runLiveBenchmark();
    loadSampleDeed("sample-deed-1974-saf-kabala");
  }, []);


  const loadSampleDeed = async (sampleId: string) => {
    setDeedLoading(true);
    try {
      const res = await fetch(`${API_BASE}/deeds/samples/${sampleId}`);
      if (!res.ok) throw new Error("Deed not found");
      const data = await res.json();
      setCurrentDeed(data);
      setIsEnhancedContrast(true);
    } catch (e) {
      alert("দলিল লোড করতে সমস্যা হয়েছে: " + e);
    } finally {
      setDeedLoading(false);
    }
  };

    const openEditDeedModal = () => {
    if (!currentDeed) return;
    setDeedEditForm({
      deed_title: currentDeed.deed_title || "",
      deed_number: currentDeed.deed_number || "",
      registration_year: currentDeed.registration_year || 1993,
      mouza: currentDeed.mouza || currentDeed.schedule?.mouza || "",
      first_party_name: currentDeed.parties?.first_party_name || "",
      second_party_name: currentDeed.parties?.second_party_name || "",
      khatian_sa: currentDeed.schedule?.khatian_sa || "",
      dag_current: currentDeed.schedule?.dag_current || "",
      transferred_area_decimals: currentDeed.schedule?.transferred_area_decimals || 0
    });
    setIsEditingDeed(true);
  };

  const handleSaveDeedEdits = async () => {
    if (!currentDeed?.id) return;
    setDeedLoading(true);
    try {
      const payload: any = {
        deed_title: deedEditForm.deed_title,
        deed_number: deedEditForm.deed_number,
        registration_year: parseInt(deedEditForm.registration_year) || undefined,
        mouza: deedEditForm.mouza,
        parties: {
          first_party_name: deedEditForm.first_party_name,
          second_party_name: deedEditForm.second_party_name
        },
        schedule: {
          mouza: deedEditForm.mouza,
          khatian_sa: deedEditForm.khatian_sa,
          dag_current: deedEditForm.dag_current,
          transferred_area_decimals: parseFloat(deedEditForm.transferred_area_decimals) || 0,
          transferred_area_bangla: `${deedEditForm.transferred_area_decimals} শতক`
        }
      };
      const res = await fetch(`${API_BASE}/deeds/${currentDeed.id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      if (res.ok) {
        const data = await res.json();
        setCurrentDeed(data);
        setIsEditingDeed(false);
        alert("দলিলের সংশোধিত তথ্য সফলভাবে সংরক্ষিত হয়েছে এবং ফ্রড অডিট স্কোর আপডেট হয়েছে!");
      } else {
        alert("সংরক্ষণ ব্যর্থ হয়েছে।");
      }
    } catch (err) {
      alert("ত্রুটি: " + err);
    } finally {
      setDeedLoading(false);
    }
  };

  const handleDeedUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const formData = new FormData();
    formData.append("file", file);
    setDeedLoading(true);
    try {
      const res = await fetch(`${API_BASE}/deeds/upload`, {
        method: "POST",
        body: formData
      });
      if (!res.ok) throw new Error("Upload failed");
      const data = await res.json();
      setCurrentDeed(data);
      setIsEnhancedContrast(true);
      alert("দলিল সফলভাবে ডিজিটাইজড হয়েছে এবং জাল দলিল নিরীক্ষা সম্পন্ন হয়েছে!");
    } catch (err) {
      alert("দলিল বিশ্লেষণে ত্রুটি: " + err);
    } finally {
      setDeedLoading(false);
    }
  };

  const handleSolveProblem = async (problemOverride?: string) => {
    const text = (problemOverride || advisoryProblem).trim();
    if (!text) return;
    if (problemOverride) setAdvisoryProblem(problemOverride);
    setAdvisoryLoading(true);
    try {
      const res = await fetch(`${API_BASE}/advisory/resolve`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ problem_description: text })
      });
      if (res.ok) {
        const data = await res.json();
        setAdvisoryResult(data);
      }
    } catch (e) {
      alert("সমস্যা বিশ্লেষণে ত্রুটি হয়েছে।");
    } finally {
      setAdvisoryLoading(false);
    }
  };

  const changeMatterType = (type: string) => {
    setMatterType(type);
    setCurrentFacts({});
    setLastAskedField(null);
    setCompletionPct(0);
    setCustomTitle("");
    const cfg = MATTER_CONFIG[type] || MATTER_CONFIG.commercial_lease;
    setChatMessages([
      {
        role: "assistant",
        content: `${cfg.welcome} উদাহরণ: "${cfg.sample}"`
      }
    ]);
  };

  const fetchStatutes = async () => {
    try {
      const res = await fetch(`${API_BASE}/knowledge/statutes`);
      if (res.ok) {
        const data = await res.json();
        setStatutes(data);
      }
    } catch (e) {}
  };

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!userInput.trim()) return;

    const newMessages = [...chatMessages, { role: "user", content: userInput }];
    setChatMessages(newMessages);
    const textToSend = userInput;
    setUserInput("");

    try {
      const res = await fetch(`${API_BASE}/intake/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          matter_type: matterType,
          current_facts: currentFacts,
          conversation_history: [],
          user_input: textToSend,
          last_asked_field: lastAskedField
        })
      });

      if (res.ok) {
        const data = await res.json();
        setCurrentFacts(data.extracted_facts);
        setLastAskedField(data.current_field_asked);
        setCompletionPct(data.completion_percentage);
        setChatMessages([...newMessages, { role: "assistant", content: data.assistant_reply_bangla || data.assistant_reply }]);
      }
    } catch (err) {
      setChatMessages([...newMessages, { role: "assistant", content: "সার্ভারে সংযোগে সমস্যা হয়েছে।" }]);
    }
  };

  const generateDraft = async (templateCode: string, payloadFacts: Record<string, any>) => {
    try {
      const res = await fetch(`${API_BASE}/drafting/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          template_code: templateCode,
          facts: payloadFacts,
          style_preference: "balanced",
          language: "en"
        })
      });

      if (!res.ok) throw new Error(await res.text());
      const doc = await res.json();
      setDocumentId(doc.id);
      setDocTitle(doc.title);
      setFullText(doc.full_text);
      setSelectedClauses(doc.selected_clauses || []);
      setDocxUrl(doc.docx_url);
      setPdfUrl(doc.pdf_url);
      setDocVersion(1);
      setBookGroundingScore(doc.book_grounding_score ?? null);
      setBookChapterRef(doc.book_chapter_reference || null);
      setBookAppliedRules(doc.book_applied_rules || []);
      setMissingInfo(doc.missing_information || []);
      setBookChecklist(doc.book_checklist || []);
      setDraftWarnings(doc.drafting_warnings || []);
      setLastDraftRequest({ templateCode, facts: payloadFacts });
      setMissingAnswers({});

      const reviewRes = await fetch(`${API_BASE}/review/${doc.id}/health`);
      if (reviewRes.ok) {
        const revData = await reviewRes.json();
        setHealthReport(revData);
      }
      setActiveTab("drafting");
    } catch (err) {
      alert("ড্রাফট তৈরিতে সমস্যা হয়েছে: " + err);
    }
  };

  const triggerDraftGeneration = async () => {
    const cfg = MATTER_CONFIG[matterType] || MATTER_CONFIG.commercial_lease;
    const payloadFacts = { ...currentFacts };
    if (matterType === "custom" && customTitle && !payloadFacts.custom_matter_name) {
      payloadFacts.custom_matter_name = customTitle;
    }
    await generateDraft(cfg.template_code, payloadFacts);
  };

  const draftFromScenario = async (type: string, templateCode: string, facts: Record<string, any>) => {
    if (MATTER_CONFIG[type]) setMatterType(type);
    setCurrentFacts(facts);
    await generateDraft(templateCode, facts);
  };

  const regenerateWithAnswers = async () => {
    if (!lastDraftRequest) return;
    const facts = { ...lastDraftRequest.facts };
    Object.entries(missingAnswers).forEach(([k, v]) => {
      if (v && v.trim()) facts[k] = v.trim();
    });
    setCurrentFacts(facts);
    await generateDraft(lastDraftRequest.templateCode, facts);
  };

  const checkCitation = async () => {
    try {
      const res = await fetch(`${API_BASE}/knowledge/verify-citation?act_name=${encodeURIComponent(verifyAct)}&section=${encodeURIComponent(verifySec)}`);
      if (res.ok) {
        const data = await res.json();
        setVerifyResult(data);
      }
    } catch (e) {}
  };

  const runLiveBenchmark = async () => {
    try {
      const res = await fetch(`${API_BASE}/evaluation/benchmark/run`, { method: "POST" });
      if (res.ok) {
        const data = await res.json();
        setEvalAccuracy(data.overall_accuracy_percentage);
        setEvalResults(data.results || []);
      }
    } catch (e) {}
  };

  const submitFeedback = async () => {
    if (!feedbackNote.trim()) return;
    try {
      await fetch(`${API_BASE}/evaluation/feedback`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          rating: 5,
          feedback_category: "correct",
          reviewer_reasoning: feedbackNote
        })
      });
      alert("মতামত সংরক্ষিত হয়েছে!");
      setFeedbackNote("");
    } catch (e) {}
  };

  return (
    <div className="min-h-screen flex flex-col bg-slate-50 font-sans text-slate-800">
      {/* Top Header */}
      <header className="bg-slate-900 text-white border-b border-slate-800 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-lg bg-emerald-600 flex items-center justify-center font-bold text-xl text-white shadow-md">
              <Scale className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-bold text-lg tracking-tight">আইন-AI (Ain-AI)</span>
                <span className="text-xs bg-emerald-900 text-emerald-300 font-semibold px-2 py-0.5 rounded border border-emerald-700">
                  Bangladesh Legal OS
                </span>
              </div>
              <p className="text-xs text-slate-400">Verified Legal Knowledge • Structured Drafting • Risk Engine</p>
            </div>
          </div>

          <div className="flex items-center space-x-4">
            <div className="hidden md:flex items-center bg-slate-800 rounded-lg px-3 py-1.5 border border-slate-700 text-xs">
              <span className="text-slate-400 mr-2">সক্রিয় বিষয়:</span>
              <span className="font-semibold text-emerald-400">Mirpur Commercial Shop Lease</span>
              <span className="ml-2 w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
            </div>
            <div className="border-l border-slate-700 pl-4">
              <span className="text-xs bg-sky-950 text-sky-300 border border-sky-800 px-2.5 py-1 rounded-full font-medium">
                Advocate Workspace
              </span>
            </div>
          </div>
        </div>
      </header>

      {/* Tab Navigation */}
      <nav className="bg-white border-b border-slate-200 shadow-sm overflow-x-auto">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex space-x-8">
          <button
            onClick={() => setActiveTab("advisory")}
            className={`py-3 px-1 text-sm flex items-center space-x-2 transition whitespace-nowrap ${
              activeTab === "advisory" ? "border-b-2 border-amber-600 text-amber-600 font-semibold" : "text-slate-600 hover:text-slate-900"
            }`}
          >
            <Compass className="w-4 h-4 text-amber-600" />
            <span>১. আইনি সমস্যা ও ধাপভিত্তিক সমাধান (Problem Advisory)</span>
          </button>
          <button
            onClick={() => setActiveTab("intake")}
            className={`py-3 px-1 text-sm flex items-center space-x-2 transition whitespace-nowrap ${
              activeTab === "intake" ? "border-b-2 border-emerald-600 text-emerald-600 font-semibold" : "text-slate-600 hover:text-slate-900"
            }`}
          >
            <MessageSquare className="w-4 h-4" />
            <span>২. আইনি সাক্ষাৎকার (Intake Chat)</span>
          </button>
          <button
            onClick={() => setActiveTab("drafting")}
            className={`py-3 px-1 text-sm flex items-center space-x-2 transition whitespace-nowrap ${
              activeTab === "drafting" ? "border-b-2 border-emerald-600 text-emerald-600 font-semibold" : "text-slate-600 hover:text-slate-900"
            }`}
          >
            <FileText className="w-4 h-4" />
            <span>৩. ড্রাফটিং স্টুডিও ও ধারা বিশ্লেষণ (Studio)</span>
          </button>
          <button
            onClick={() => setActiveTab("review")}
            className={`py-3 px-1 text-sm flex items-center space-x-2 transition whitespace-nowrap ${
              activeTab === "review" ? "border-b-2 border-emerald-600 text-emerald-600 font-semibold" : "text-slate-600 hover:text-slate-900"
            }`}
          >
            <ShieldAlert className="w-4 h-4" />
            <span>৪. ঝুঁকি ও স্বাস্থ্য অডিট (Risk & Health)</span>
          </button>
          <button
            onClick={() => setActiveTab("knowledge")}
            className={`py-3 px-1 text-sm flex items-center space-x-2 transition whitespace-nowrap ${
              activeTab === "knowledge" ? "border-b-2 border-emerald-600 text-emerald-600 font-semibold" : "text-slate-600 hover:text-slate-900"
            }`}
          >
            <Database className="w-4 h-4" />
            <span>৫. আইন ভাণ্ডার ও মূল্যায়ন (Knowledge & Eval)</span>
          </button>
          <button
            onClick={() => {
              setActiveTab("deed");
              if (!currentDeed) {
                loadSampleDeed("sample-deed-1974-saf-kabala");
              }
            }}
            className={`py-3 px-1 text-sm flex items-center space-x-2 transition whitespace-nowrap ${
              activeTab === "deed" ? "border-b-2 border-emerald-600 text-emerald-600 font-semibold" : "text-slate-600 hover:text-slate-900"
            }`}
          >
            <Scale className="w-4 h-4 text-emerald-600" />
            <span>৬. দলিল ডিজিটালাইজার ও জাল দলিল যাচাই (Deed Intelligence)</span>
          </button>
        </div>
      </nav>

      {/* Main Container */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 flex-1 w-full">
        {/* ================= TAB 0: ADVISORY ================= */}
        {activeTab === "advisory" && (
          <div className="space-y-6">
            <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
              <div className="flex items-center space-x-3 mb-4">
                <div className="p-2.5 rounded-lg bg-amber-100 text-amber-800">
                  <Compass className="w-6 h-6" />
                </div>
                <div>
                  <h2 className="text-base font-bold text-slate-800">আইনি সমস্যা সমাধান ও ধাপভিত্তিক পরামর্শক (Legal Problem Solver)</h2>
                  <p className="text-xs text-slate-500">আপনার সমস্যাটি সহজ ভাষায় লিখুন। সিস্টেম আপনাকে ধাপে ধাপে কী করতে হবে, কোন আইনে বিচার হবে এবং কী ঝুঁকি রয়েছে তার দিকনির্দেশনা দেবে।</p>
                </div>
              </div>

              <div className="space-y-3">
                <textarea
                  rows={3}
                  value={advisoryProblem}
                  onChange={(e) => setAdvisoryProblem(e.target.value)}
                  placeholder="আপনার সমস্যাটি বিস্তারিত লিখুন (যেমন: 'আমার পাওনাদার আমাকে একটা ৫ লাখ টাকার চেক দিয়েছিল, ব্যাংকে বাউন্স করেছে। এখন কীভাবে টাকা আদায় করব?')..."
                  className="w-full border border-slate-300 rounded-lg p-3 text-sm focus:outline-none focus:ring-2 focus:ring-amber-500 transition"
                />

                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="flex items-center space-x-2 text-xs">
                    <span className="text-slate-400">সাধারণ সমস্যা বাছাই:</span>
                    <button
                      type="button"
                      onClick={() => handleSolveProblem("চেক বাউন্স করেছে, ব্যাংকে টাকা নাই")}
                      className="bg-slate-100 hover:bg-slate-200 text-slate-700 px-2.5 py-1 rounded border border-slate-200 transition"
                    >
                      চেক ডিজঅনার
                    </button>
                    <button
                      type="button"
                      onClick={() => handleSolveProblem("ভাড়াটিয়া চুক্তি শেষ হলেও দোকান ছাড়ছে না এবং ভাড়া দিচ্ছে না")}
                      className="bg-slate-100 hover:bg-slate-200 text-slate-700 px-2.5 py-1 rounded border border-slate-200 transition"
                    >
                      ভাড়াটিয়া উচ্ছেদ
                    </button>
                    <button
                      type="button"
                      onClick={() => handleSolveProblem("কোম্পানি নোটিশ ও পাওনা না দিয়ে হঠাৎ চাকরি থেকে বের করে দিয়েছে")}
                      className="bg-slate-100 hover:bg-slate-200 text-slate-700 px-2.5 py-1 rounded border border-slate-200 transition"
                    >
                      অন্যায় বরখাস্ত
                    </button>
                    <button
                      type="button"
                      onClick={() => handleSolveProblem("মহাকাশে এলিয়েনের সাথে জমি নিয়ে বিরোধ হয়েছে")}
                      className="bg-rose-50 hover:bg-rose-100 text-rose-700 px-2.5 py-1 rounded border border-rose-200 transition"
                    >
                      জিরো-গেসিং টেস্ট
                    </button>
                  </div>

                  <button
                    type="button"
                    onClick={() => handleSolveProblem()}
                    disabled={advisoryLoading}
                    className="bg-amber-600 hover:bg-amber-700 text-white font-semibold px-5 py-2 rounded-lg text-sm flex items-center space-x-2 shadow transition disabled:opacity-50"
                  >
                    <Compass className="w-4 h-4" />
                    <span>{advisoryLoading ? "বিশ্লেষণ চলছে..." : "আইনি সমাধান ও ধাপগুলো দেখুন"}</span>
                  </button>
                </div>
              </div>
            </div>

            {/* Advisory Output */}
            {advisoryResult && !advisoryResult.verified && (
              <div className="bg-amber-50 rounded-xl border border-amber-200 p-6 space-y-3">
                <p className="text-sm text-amber-900 whitespace-pre-line">{advisoryResult.message_bangla}</p>
                {advisoryResult.suggested_next_step && (
                  <p className="text-xs text-amber-800">{advisoryResult.suggested_next_step}</p>
                )}
              </div>
            )}

            {advisoryResult && advisoryResult.verified && (
              <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 space-y-6">
                <div className="border-b border-slate-100 pb-3 flex items-center justify-between">
                  <div>
                    <span className="text-[10px] font-bold text-emerald-700 bg-emerald-100 px-2 py-0.5 rounded">বাংলাদেশ আইনের সুনির্দিষ্ট পথনকশা</span>
                    <h3 className="text-base font-bold text-slate-900 mt-1">{advisoryResult.dispute_title}</h3>
                  </div>
                  <button
                    onClick={() => setActiveTab("intake")}
                    className="bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold px-3.5 py-2 rounded-lg flex items-center space-x-1 shadow transition"
                  >
                    <span>সরাসরি খসড়া ড্রাফট করুন</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </button>
                </div>

                <div>
                  <span className="text-xs font-semibold text-slate-600 block mb-1.5">প্রযোজ্য বাংলাদেশ আইন ও সংবিধিবদ্ধ বিধান:</span>
                  <div className="flex flex-wrap gap-2">
                    {(advisoryResult.applicable_laws || []).map((l: string, i: number) => (
                      <span key={i} className="text-xs bg-slate-100 text-slate-800 border border-slate-200 font-medium px-2.5 py-1 rounded-md">
                        ⚖️ {l}
                      </span>
                    ))}
                  </div>
                </div>

                <div className="space-y-3">
                  <span className="text-xs font-semibold text-slate-800 block">ধাপভিত্তিক করণীয় (Action Steps):</span>
                  <div className="space-y-2.5">
                    {(advisoryResult.roadmap_steps || []).map((st: any, i: number) => (
                      <div key={i} className="p-4 rounded-lg bg-slate-50 border border-slate-200">
                        <div className="flex items-center justify-between mb-1">
                          <span className="font-bold text-xs text-slate-900">ধাপ {st.step_no}: {st.title}</span>
                          <span className="text-[10px] bg-amber-100 text-amber-800 font-semibold px-2 py-0.5 rounded">সময়সীমা: {st.timeline}</span>
                        </div>
                        <p className="text-xs text-slate-700 leading-relaxed">{st.action}</p>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                  <div className="p-4 rounded-lg bg-blue-50/50 border border-blue-100">
                    <h4 className="font-bold text-blue-900 mb-2">প্রয়োজনীয় প্রমাণ ও নথিপত্র চেকলিস্ট:</h4>
                    <ul className="space-y-1.5 text-slate-700">
                      {(advisoryResult.document_checklist || []).map((d: string, i: number) => (
                        <li key={i} className="flex items-center space-x-1.5"><span>📄</span><span>{d}</span></li>
                      ))}
                    </ul>
                  </div>
                  <div className="p-4 rounded-lg bg-amber-50/50 border border-amber-200">
                    <h4 className="font-bold text-amber-900 mb-2">সতর্কতা ও আইনগত ঝুঁকি:</h4>
                    <ul className="space-y-1.5 text-slate-800">
                      {(advisoryResult.risks_and_cautions || []).map((r: string, i: number) => (
                        <li key={i} className="flex items-start space-x-1.5"><span className="text-amber-500">⚠️</span><span>{r}</span></li>
                      ))}
                    </ul>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* ================= TAB 1: INTAKE ================= */}
        {activeTab === "intake" && (
          <div className="space-y-6">
          <ScenarioComposer onDraft={draftFromScenario} />
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 bg-white rounded-xl shadow-sm border border-slate-200 flex flex-col h-[650px]">
              <div className="p-4 border-b border-slate-100 flex items-center justify-between bg-slate-50 rounded-t-xl">
                <div>
                  <h2 className="font-semibold text-sm text-slate-800">AI Legal Intake Interview</h2>
                  <p className="text-xs text-slate-500">বাংলা ও ইংরেজিতে স্বাভাবিক কথপোকথনের মাধ্যমে ফ্যাক্ট এক্সট্রাকশন</p>
                </div>
                <div className="flex flex-col items-end space-y-1">
                  <div className="flex items-center space-x-2">
                    <label className="text-xs text-slate-500 font-medium hidden sm:inline">দলিলের ধরন:</label>
                    <select
                      value={matterType}
                      onChange={(e) => changeMatterType(e.target.value)}
                      className="text-xs font-semibold bg-white border border-slate-300 rounded-lg px-2.5 py-1.5 text-slate-800 focus:ring-2 focus:ring-emerald-500 outline-none shadow-sm cursor-pointer"
                    >
                      <option value="commercial_lease">১. বাণিজ্যিক দোকান / স্পেস ভাড়া চুক্তি</option>
                      <option value="residential_rent">২. আবাসিক বাসা / ফ্ল্যাট ভাড়া চুক্তি</option>
                      <option value="employment_agreement">৩. চাকরির চুক্তিপত্র (শ্রম আইন ২০০৬)</option>
                      <option value="demand_notice_ni_act">৪. চেক ডিজঅনার আইনি নোটিশ (১৩৮ ধারা)</option>
                      <option value="partnership_deed">৫. অংশীদারি কারবার চুক্তি (Partnership Deed)</option>
                      <option value="sale_agreement">৬. স্থাবর সম্পত্তি বিক্রয় বায়না চুক্তি (Sale Agreement)</option>
                      <option value="loan_agreement">৭. হাওলাত / অর্থ ঋণ চুক্তিপত্র (Loan Agreement)</option>
                      <option value="nda">৮. গোপনীয়তা চুক্তি (Non-Disclosure Agreement - NDA)</option>
                      <option value="service_agreement">৯. পেশাদার সেবা ও প্রজেক্ট চুক্তি (Service Agreement)</option>
                      <option value="custom">✨ ১০. কাস্টম চুক্তি (Custom Agreement - যেকোনো চুক্তি টাইপ করুন)</option>
                    </select>
                  </div>
                  {matterType === "custom" && (
                    <div className="w-full">
                      <input
                        type="text"
                        value={customTitle}
                        onChange={(e) => {
                          setCustomTitle(e.target.value);
                          setCurrentFacts(prev => ({ ...prev, custom_matter_name: e.target.value }));
                        }}
                        placeholder="চুক্তির নাম টাইপ করুন (যেমন: সরবরাহ চুক্তি, কমিশন চুক্তি)..."
                        className="w-full bg-amber-50 border border-amber-300 rounded px-2.5 py-1 text-xs text-slate-800 focus:outline-none focus:ring-1 focus:ring-amber-500 shadow-sm"
                      />
                    </div>
                  )}
                </div>
              </div>

              <div className="flex-1 p-4 overflow-y-auto space-y-4">
                {chatMessages.map((m, idx) => (
                  <div key={idx} className={`flex items-start space-x-3 ${m.role === "user" ? "justify-end" : ""}`}>
                    {m.role !== "user" && (
                      <div className="w-8 h-8 rounded-full bg-emerald-600 text-white flex items-center justify-center text-xs font-bold shrink-0">
                        আইন
                      </div>
                    )}
                    <div
                      className={`p-3 text-sm max-w-lg shadow-sm rounded-2xl ${
                        m.role === "user" ? "bg-emerald-600 text-white rounded-tr-none" : "bg-slate-100 text-slate-800 rounded-tl-none leading-relaxed"
                      }`}
                    >
                      {m.content}
                    </div>
                    {m.role === "user" && (
                      <div className="w-8 h-8 rounded-full bg-slate-800 text-white flex items-center justify-center text-xs font-bold shrink-0">
                        আপনি
                      </div>
                    )}
                  </div>
                ))}
              </div>

              <div className="p-3 border-t border-slate-100 bg-white rounded-b-xl">
                <form onSubmit={handleSendMessage} className="flex items-center space-x-2">
                  <input
                    type="text"
                    value={userInput}
                    onChange={(e) => setUserInput(e.target.value)}
                    placeholder="আপনার তথ্য বা উত্তর লিখুন..."
                    className="flex-1 border border-slate-300 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 transition"
                  />
                  <button type="submit" className="bg-emerald-600 hover:bg-emerald-700 text-white px-5 py-2.5 rounded-lg text-sm font-medium flex items-center space-x-1 shadow transition">
                    <span>পাঠান</span>
                    <Send className="w-4 h-4" />
                  </button>
                </form>
                <div className="flex items-center space-x-2 mt-2">
                  <span className="text-xs text-slate-400">কুইক স্যাম্পল:</span>
                  <button
                    type="button"
                    onClick={() => setUserInput(MATTER_CONFIG[matterType]?.sample || "")}
                    className="text-xs text-emerald-600 hover:underline bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200 truncate max-w-md text-left"
                  >
                    {MATTER_CONFIG[matterType]?.sample}
                  </button>
                </div>
              </div>
            </div>

            {/* Facts Panel */}
            <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5 flex flex-col justify-between h-[650px] overflow-y-auto">
              <div>
                <div className="flex items-center justify-between pb-3 border-b border-slate-100 mb-4">
                  <h3 className="font-semibold text-sm text-slate-800 flex items-center space-x-2">
                    <Cpu className="w-4 h-4 text-emerald-600" />
                    <span>সংগৃহীত কাঠামোগত তথ্য (Facts)</span>
                  </h3>
                  <span className="text-xs font-bold px-2 py-0.5 rounded bg-emerald-100 text-emerald-800">
                    {completionPct}% সম্পূর্ণ
                  </span>
                </div>

                <div className="w-full bg-slate-100 rounded-full h-2 mb-4">
                  <div className="bg-emerald-600 h-2 rounded-full transition-all duration-300" style={{ width: `${completionPct}%` }}></div>
                </div>

                <div className="space-y-3 text-xs">
                  {MATTER_CONFIG[matterType]?.fields.map((f) => {
                    const val = currentFacts[f.key];
                    const isSet = val !== undefined && val !== null && val !== "";
                    let displayVal = "অপেক্ষারত...";
                    if (isSet) {
                      if (f.type === "money") {
                        displayVal = `${Number(val).toLocaleString()} টাকা`;
                      } else if (f.type === "duration") {
                        displayVal = `${val} মাস (${(Number(val) / 12).toFixed(1)} বছর)`;
                      } else if (f.type === "months") {
                        displayVal = `${val} মাস`;
                      } else {
                        displayVal = val;
                      }
                    } else if (f.default) {
                      displayVal = `${f.default} (স্বাভাবিক)`;
                    }

                    return (
                      <div
                        key={f.key}
                        className={`p-2.5 rounded-lg transition ${
                          isSet ? "bg-emerald-50/50 border border-emerald-200" : "bg-slate-50 border border-slate-100"
                        }`}
                      >
                        <span className="text-slate-500 block text-[11px]">{f.label}:</span>
                        <span className={`font-semibold text-xs ${isSet ? "text-emerald-900" : "text-slate-600"}`}>
                          {displayVal}
                        </span>
                      </div>
                    );
                  })}
                </div>
              </div>

              <div className="pt-4 border-t border-slate-100">
                <button
                  onClick={triggerDraftGeneration}
                  className="w-full bg-slate-900 hover:bg-slate-800 text-white font-medium py-3 px-4 rounded-lg text-sm flex items-center justify-center space-x-2 shadow transition"
                >
                  <Sparkles className="w-4 h-4 text-emerald-400" />
                  <span>খসড়া চুক্তিপত্র তৈরি করুন (Generate Draft)</span>
                </button>
              </div>
            </div>
          </div>
          </div>
        )}

        {/* ================= TAB 2: DRAFTING STUDIO ================= */}
        {activeTab === "drafting" && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 bg-white rounded-xl shadow-sm border border-slate-200 flex flex-col h-[700px]">
              <div className="p-4 border-b border-slate-100 flex items-center justify-between bg-slate-50 rounded-t-xl">
                <div className="flex items-center space-x-2">
                  <FileText className="w-5 h-5 text-sky-600" />
                  <h2 className="font-semibold text-sm text-slate-800">{docTitle}</h2>
                  <span className="text-[10px] bg-sky-100 text-sky-800 font-bold px-2 py-0.5 rounded">v{docVersion}</span>
                </div>
                <div className="flex items-center space-x-2">
                  <button
                    type="button"
                    onClick={handleSaveDocumentEdits}
                    className="text-xs bg-emerald-600 hover:bg-emerald-700 text-white font-semibold px-3 py-1.5 rounded flex items-center space-x-1 shadow-sm transition cursor-pointer"
                  >
                    <Save className="w-3.5 h-3.5" />
                    <span>সংরক্ষণ (Save Edits)</span>
                  </button>
                  {docxUrl && (
                    <a href={docxUrl} target="_blank" rel="noreferrer" className="text-xs bg-blue-50 text-blue-700 hover:bg-blue-100 border border-blue-200 font-semibold px-3 py-1.5 rounded flex items-center space-x-1 transition">
                      <Download className="w-3.5 h-3.5" />
                      <span>Word (.DOCX)</span>
                    </a>
                  )}
                  {pdfUrl && (
                    <a href={pdfUrl} target="_blank" rel="noreferrer" className="text-xs bg-rose-50 text-rose-700 hover:bg-rose-100 border border-rose-200 font-semibold px-3 py-1.5 rounded flex items-center space-x-1 transition">
                      <File className="w-3.5 h-3.5" />
                      <span>PDF</span>
                    </a>
                  )}
                </div>
              </div>

              {/* Dr. Syeda Nasrin Grounding Stamp */}
              <div className="px-4 py-3 bg-gradient-to-r from-emerald-50 via-teal-50 to-emerald-100 border-b border-emerald-200 flex flex-wrap items-center justify-between gap-3">
                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 rounded-xl bg-emerald-600 text-white flex flex-col items-center justify-center font-extrabold shadow-sm">
                    <span className="text-xs leading-none">{bookGroundingScore ?? "–"}%</span>
                    <span className="text-[8px] font-normal uppercase tracking-tight">বই স্কোর</span>
                  </div>
                  <div>
                    <div className="flex items-center space-x-2">
                      <span className="text-xs font-bold text-emerald-950">ড. সৈয়দা নাসরিনের ড্রাফটিং বই অনুসারী সনদ (Legal Drafting Grounded)</span>
                      <span className="text-[10px] bg-emerald-700 text-white font-semibold px-2 py-0.5 rounded-full shadow-xs">
                        যাচাইকৃত ড্রাফট
                      </span>
                    </div>
                    <p className="text-[11px] text-emerald-800 font-medium mt-0.5">
                      📖 বই রেফারেন্স: <span className="font-semibold text-emerald-950">{bookChapterRef || "—"}</span>
                    </p>
                  </div>
                </div>

                <div className="flex items-center space-x-2">
                  <span className="text-[11px] bg-white/90 border border-emerald-300 text-emerald-800 font-medium px-2.5 py-1 rounded-lg shadow-2xs">
                    ✓ {bookChecklist.length > 0 ? `বইয়ের চেকলিস্ট: ${bookChecklist.filter((c: any) => c.ok).length}/${bookChecklist.length}` : "খসড়া তৈরি হয়নি"}
                  </span>
                </div>
              </div>

              <textarea
                value={fullText}
                onChange={(e) => setFullText(e.target.value)}
                className="flex-1 p-6 font-mono text-xs leading-relaxed text-slate-800 bg-white border-0 focus:outline-none focus:ring-1 focus:ring-sky-400 resize-none whitespace-pre-wrap"
                placeholder="চুক্তিপত্র এখনো প্রস্তুত হয়নি। প্রথমে 'আইনি সাক্ষাৎকার' ট্যাবে তথ্য দিয়ে 'Generate Draft' ক্লিক করুন।"
              />
            </div>

            {/* Clause Breakdown */}
            <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5 h-[700px] flex flex-col">
              <div className="pb-3 border-b border-slate-100 mb-3">
                <h3 className="font-semibold text-sm text-slate-800">ধারাভিত্তিক বিশ্লেষণ ও সহজ বাংলায় ব্যাখ্যা</h3>
                <p className="text-xs text-slate-500 mt-0.5">ড. সৈয়দা নাসরিনের বইয়ের ধারা ও আইনি ভিত্তি বিশ্লেষণ</p>
              </div>

              {draftWarnings.length > 0 && (
                <div className="mb-3 p-3 bg-rose-50 border border-rose-200 rounded-lg text-xs text-rose-900 space-y-1">
                  <div className="font-bold">⚠ আইনি সতর্কতা</div>
                  {draftWarnings.map((w, i) => <div key={i}>• {w}</div>)}
                </div>
              )}

              {missingInfo.length > 0 && (
                <div className="mb-3 p-3 bg-amber-50 border border-amber-200 rounded-lg text-xs space-y-2 max-h-72 overflow-y-auto">
                  <div className="font-bold text-amber-900">খসড়ায় {missingInfo.length}টি স্থান ফাঁকা (……) — উত্তর দিয়ে খসড়া পূর্ণ করুন</div>
                  {missingInfo.map((m: any) => (
                    <div key={m.field}>
                      <div className="font-semibold text-slate-800">{m.question_bn} {m.critical && <span className="text-rose-600">*</span>}</div>
                      <div className="text-[10px] text-slate-500">{m.why_bn}</div>
                      <input
                        value={missingAnswers[m.field] || ""}
                        onChange={(e) => setMissingAnswers((a) => ({ ...a, [m.field]: e.target.value }))}
                        placeholder={m.suggestion !== null && m.suggestion !== undefined ? `বইয়ের প্রস্তাব: ${m.suggestion}` : "উত্তর লিখুন"}
                        className="w-full border rounded px-2 py-1 mt-0.5 bg-white"
                      />
                    </div>
                  ))}
                  <button onClick={regenerateWithAnswers} className="w-full bg-slate-900 hover:bg-slate-800 text-white font-semibold py-1.5 rounded">উত্তরসহ খসড়া পুনরায় তৈরি করুন</button>
                </div>
              )}

              {bookAppliedRules.length > 0 && (
                <div className="mb-3 p-3 bg-emerald-50/50 border border-emerald-200 rounded-lg text-xs">
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="font-bold text-slate-800 text-[11px]">বই থেকে প্রযুক্ত মূল আইনি নীতি ও রুলস:</span>
                    <span className="text-[10px] font-bold text-emerald-800 bg-emerald-100 px-1.5 py-0.5 rounded">
                      {bookGroundingScore ?? "–"}% বইয়ের চেকলিস্ট পূরণ
                    </span>
                  </div>
                  <ul className="space-y-1 text-[11px] text-slate-700">
                    {bookAppliedRules.map((r, idx) => (
                      <li key={idx} className="flex items-start space-x-1.5">
                        <span className={`leading-tight ${r.startsWith("✘") ? "text-rose-700" : ""}`}>{r}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              <div className="flex-1 overflow-y-auto space-y-3 pr-1">
                {selectedClauses.map((cl, i) => (
                  <div key={i} className="p-3 rounded-lg border border-slate-200 hover:border-sky-500 bg-white transition">
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-semibold text-xs text-slate-900">{cl.title}</span>
                      <span className={`text-[10px] px-1.5 py-0.5 rounded font-medium ${cl.risk_level === "high" ? "bg-rose-100 text-rose-700" : "bg-slate-100 text-slate-600"}`}>
                        {cl.risk_level.toUpperCase()} RISK
                      </span>
                    </div>
                    <p className="text-xs text-emerald-900 bg-emerald-50 p-2 rounded border border-emerald-100 mb-1 leading-relaxed">
                      <strong>সহজ বাংলায়:</strong> {cl.explanation_bangla}
                    </p>
                    <div className="text-[10px] text-slate-500">
                      <span>আইনি ভিত্তি: </span>
                      <span className="font-medium text-slate-700">{cl.statutory_basis}</span>
                    </div>
                    {cl.book_reference && (
                      <div className="mt-1.5 text-[10px] text-emerald-800 bg-emerald-50/90 px-2 py-1 rounded border border-emerald-200 flex items-center space-x-1">
                        <span className="font-bold text-emerald-900">📖 বই রেফারেন্স:</span>
                        <span>{cl.book_reference}</span>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* ================= TAB 3: REVIEW & HEALTH ================= */}
        {activeTab === "review" && healthReport && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm">
                <span className="text-xs text-slate-500 font-medium">সামগ্রিক স্বাস্থ্য স্কোর</span>
                <div className="text-3xl font-bold text-slate-800 mt-2">{healthReport.overall_health_score}/১০০</div>
                <p className="text-xs text-emerald-600 font-medium mt-1">আইনি মানদণ্ড অনুসরণকৃত</p>
              </div>
              <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm">
                <span className="text-xs text-slate-500 font-medium">সম্পূর্ণতা স্কোর</span>
                <div className="text-3xl font-bold text-slate-800 mt-2">{healthReport.completeness_score}/১০০</div>
                <p className="text-xs text-slate-500 mt-1">আবশ্যকীয় তথ্য সংরক্ষিত</p>
              </div>
              <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm">
                <span className="text-xs text-slate-500 font-medium">ঝুঁকি স্কোর</span>
                <div className="text-3xl font-bold text-amber-600 mt-2">{healthReport.risk_score}/১০০</div>
                <p className="text-xs text-amber-600 font-medium mt-1">মাঝারি আইনি সতর্কতা</p>
              </div>
              <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm">
                <span className="text-xs text-slate-500 font-medium">আইনজীবী পর্যালোচনা</span>
                <div className="mt-2">
                  <span className="inline-block text-xs font-semibold px-2.5 py-1 rounded bg-amber-100 text-amber-800">
                    {healthReport.professional_review_recommended ? "সুপারিশকৃত (Recommended)" : "ঐচ্ছিক"}
                  </span>
                </div>
                <p className="text-xs text-slate-400 mt-1">সাব-রেজিস্ট্রি বাধ্যতামূলক</p>
              </div>
            </div>

            <div className="bg-amber-50 rounded-xl border border-amber-200 p-4">
              <div className="flex items-start space-x-3">
                <AlertTriangle className="w-5 h-5 text-amber-700 shrink-0 mt-0.5" />
                <div>
                  <h4 className="text-sm font-semibold text-amber-900">আইনি অডিট সারসংক্ষেপ (বাংলায়):</h4>
                  <p className="text-xs text-amber-800 mt-1 leading-relaxed">{healthReport.plain_bangla_summary}</p>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
              <div className="p-4 border-b border-slate-100 bg-slate-50 flex items-center justify-between">
                <h3 className="font-semibold text-sm text-slate-800">চিহ্নিত আইনি অসঙ্গতি ও প্রতিকার</h3>
                <span className="text-xs font-semibold px-2 py-0.5 rounded bg-slate-200 text-slate-700">
                  {healthReport.issues.length}টি বিষয়
                </span>
              </div>
              <div className="p-4 space-y-4">
                {healthReport.issues.map((issue, idx) => (
                  <div key={idx} className="p-3 rounded-lg border border-slate-200 bg-slate-50 text-xs">
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-semibold text-slate-900">{issue.clause_title}</span>
                      <span className="text-[10px] bg-rose-100 text-rose-700 font-bold px-2 py-0.5 rounded">
                        {issue.severity.toUpperCase()}
                      </span>
                    </div>
                    <p className="text-slate-700 mb-1 leading-relaxed">{issue.message_bangla}</p>
                    <div className="p-2 bg-white rounded border border-slate-200 text-emerald-700 font-medium">
                      💡 প্রতিকার: {issue.suggested_fix_bangla}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* ================= TAB 4: KNOWLEDGE & EVALUATION ================= */}
        {activeTab === "knowledge" && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5">
              <div className="flex items-center justify-between pb-3 border-b border-slate-100 mb-4">
                <div>
                  <h3 className="font-semibold text-sm text-slate-800">যাচাইকৃত বাংলাদেশ আইন ভাণ্ডার</h3>
                  <p className="text-xs text-slate-500">সরকারি সূত্র (bdlaws.minlaw.gov.bd) অনুযায়ী সংরক্ষিত ধারা</p>
                </div>
                <span className="text-xs bg-emerald-100 text-emerald-800 font-semibold px-2 py-0.5 rounded">
                  Verified Legal Corpus
                </span>
              </div>

              <div className="space-y-3 max-h-[350px] overflow-y-auto">
                {statutes.map((s, i) => (
                  <div key={i} className="p-2.5 rounded-lg border border-slate-100 bg-slate-50 flex items-center justify-between text-xs">
                    <div>
                      <span className="font-semibold text-slate-800">{s.act_name} ({s.act_year})</span>
                      <span className="text-[10px] text-slate-500 block">{s.act_number}</span>
                    </div>
                    <span className="text-[10px] bg-sky-100 text-sky-800 font-semibold px-2 py-0.5 rounded">
                      {s.sections_count} Sections
                    </span>
                  </div>
                ))}
              </div>

              <div className="mt-6 pt-4 border-t border-slate-100">
                <h4 className="text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">
                  🛡️ অ্যান্টি-হ্যালুসিনেশন সাইটেশন ভেরিফায়ার:
                </h4>
                <div className="flex items-center space-x-2 text-xs">
                  <input
                    type="text"
                    value={verifyAct}
                    onChange={(e) => setVerifyAct(e.target.value)}
                    className="border rounded px-2.5 py-1.5 flex-1"
                    placeholder="Act Name"
                  />
                  <input
                    type="text"
                    value={verifySec}
                    onChange={(e) => setVerifySec(e.target.value)}
                    className="border rounded px-2.5 py-1.5 w-20"
                    placeholder="Section"
                  />
                  <button onClick={checkCitation} className="bg-slate-800 hover:bg-slate-900 text-white font-medium px-3 py-1.5 rounded">
                    যাচাই করুন
                  </button>
                </div>
                {verifyResult && (
                  <div className={`mt-2 text-xs p-2 rounded border ${verifyResult.verified ? "bg-emerald-50 text-emerald-800 border-emerald-200" : "bg-rose-50 text-rose-800 border-rose-200"}`}>
                    {verifyResult.verified ? (
                      <div>✅ <strong>যাচাইকৃত:</strong> {verifyResult.act_name}, Section {verifyResult.section} ({verifyResult.title})</div>
                    ) : (
                      <div>❌ <strong>সতর্কতা:</strong> [Authority Not Verified] - ধারাটি সরকারি ডাটাবেজে পাওয়া যায়নি।</div>
                    )}
                  </div>
                )}
              </div>
            </div>

            {/* AI Evaluation */}
            <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5 flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between pb-3 border-b border-slate-100 mb-4">
                  <div>
                    <h3 className="font-semibold text-sm text-slate-800">AI ইভ্যালুয়েশন ও রিগ্রেশন বেঞ্চমার্ক</h3>
                    <p className="text-xs text-slate-500">ফ্যাক্ট এক্সট্রাকশন ও লিগ্যাল রুল সঠিকতা পরিমাপ</p>
                  </div>
                  <button onClick={runLiveBenchmark} className="bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-medium px-3 py-1.5 rounded flex items-center space-x-1 shadow transition">
                    <Play className="w-3.5 h-3.5" />
                    <span>বেঞ্চমার্ক চালান</span>
                  </button>
                </div>

                <div className="bg-slate-50 border border-slate-200 rounded-lg p-4 mb-4 flex items-center justify-between">
                  <div>
                    <span className="text-xs text-slate-500 font-medium">বেঞ্চমার্ক একিউরেসি</span>
                    <div className="text-2xl font-bold text-emerald-600">{evalAccuracy.toFixed(0)}%</div>
                  </div>
                  <span className="text-xs bg-emerald-100 text-emerald-800 font-semibold px-2 py-1 rounded">
                    {evalResults.filter(r => r.passed).length} / {evalResults.length} টেস্ট পাস
                  </span>
                </div>

                <div className="space-y-2 text-xs max-h-[220px] overflow-y-auto">
                  {evalResults.map((r, i) => (
                    <div key={i} className="p-2 rounded bg-slate-50 border border-slate-100 flex items-center justify-between">
                      <span className="text-slate-700">{r.case_name}</span>
                      <span className={`font-bold text-[10px] px-2 py-0.5 rounded ${r.passed ? "text-emerald-600 bg-emerald-50" : "text-rose-600 bg-rose-50"}`}>
                        {r.passed ? "PASSED (100%)" : "FAILED"}
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="mt-4 pt-4 border-t border-slate-100">
                <h4 className="text-xs font-semibold text-slate-700 mb-2">আইনজীবী মতামত ও সিস্টেম সংশোধন:</h4>
                <div className="flex items-center space-x-2">
                  <input
                    type="text"
                    value={feedbackNote}
                    onChange={(e) => setFeedbackNote(e.target.value)}
                    placeholder="আপনার কোনো আইনি সংশোধন বা নোট লিখুন..."
                    className="border rounded px-2.5 py-1.5 text-xs flex-1"
                  />
                  <button onClick={submitFeedback} className="bg-sky-600 hover:bg-sky-700 text-white font-medium text-xs px-3 py-1.5 rounded">
                    জমা দিন
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ================= TAB 6: DEED INTELLIGENCE & FRAUD DETECTION ================= */}
        {activeTab === "deed" && (
          <div className="space-y-6">
            {/* Header & Sample Selector */}
            <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
              <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-100 pb-4 mb-4">
                <div className="flex items-center space-x-3">
                  <div className="p-2.5 rounded-lg bg-emerald-100 text-emerald-800">
                    <Scale className="w-6 h-6" />
                  </div>
                  <div>
                    <h2 className="text-base font-bold text-slate-800">ঐতিহাসিক দলিল ডিজিটালাইজার ও জাল দলিল শনাক্তকরণ (Land Deed Intelligence)</h2>
                    <p className="text-xs text-slate-500">পুরনো হস্তলিখিত দলিল, সাফ-কবলা, হেবা ও বায়া দলিলের অস্পষ্ট লেখা উদ্ধার, পূর্ণাঙ্গ তফশিল নিষ্কাশন এবং ৮টি সংবিধিবদ্ধ জালিয়াতি নিরীক্ষা।</p>
                  </div>
                </div>

                <div className="flex items-center space-x-2">
                  <label className="cursor-pointer bg-slate-900 hover:bg-slate-800 text-white font-medium text-xs px-3.5 py-2 rounded-lg flex items-center space-x-1.5 shadow transition">
                    <span>নতুন দলিল আপলোড (Scan PDF/Image)</span>
                    <input type="file" className="hidden" accept="image/*,application/pdf" onChange={handleDeedUpload} />
                  </label>
                </div>
              </div>

              <div className="flex flex-wrap items-center gap-2">
                <span className="text-xs font-semibold text-slate-500">পরীক্ষামূলক ঐতিহাসিক দলিল বাছাই:</span>
                <button
                  type="button"
                  onClick={() => loadSampleDeed("sample-deed-1974-saf-kabala")}
                  className="bg-emerald-50 hover:bg-emerald-100 text-emerald-800 border border-emerald-200 text-xs px-3 py-1.5 rounded-lg font-medium transition flex items-center space-x-1.5"
                >
                  <span>📜 ১৯৭৪ হস্তলিখিত সাফ-কবলা (১০.৫ শতক)</span>
                  <span className="text-[10px] bg-emerald-200 text-emerald-900 px-1.5 py-0.2 rounded font-bold">খাঁটি দলিল</span>
                </button>
                <button
                  type="button"
                  onClick={() => loadSampleDeed("sample-deed-1988-heba-bil-ewaz")}
                  className="bg-sky-50 hover:bg-sky-100 text-sky-800 border border-sky-200 text-xs px-3 py-1.5 rounded-lg font-medium transition flex items-center space-x-1.5"
                >
                  <span>📜 ১৯৮৮ হেবা-বিল-এওয়াজ (১৫ শতক)</span>
                  <span className="text-[10px] bg-sky-200 text-sky-900 px-1.5 py-0.2 rounded font-bold">পারিবারিক দান</span>
                </button>
                <button
                  type="button"
                  onClick={() => loadSampleDeed("sample-deed-1952-fake-forgery")}
                  className="bg-rose-50 hover:bg-rose-100 text-rose-800 border border-rose-200 text-xs px-3 py-1.5 rounded-lg font-medium transition flex items-center space-x-1.5"
                >
                  <span>⚠️ ১৯৫২ সন্দেহজনক দলিল (জরিপ জালিয়াতি)</span>
                  <span className="text-[10px] bg-rose-200 text-rose-900 px-1.5 py-0.2 rounded font-bold">জাল সনাক্ত</span>
                </button>
                {deedLoading && <span className="text-xs text-slate-500 animate-pulse">প্রসেসিং হচ্ছে...</span>}
              </div>
            </div>

            {currentDeed?.reading_report?.fields && (
              <DeedVerificationPanel deed={currentDeed} onUpdated={setCurrentDeed} />
            )}

            {/* 3-Panel Studio */}
            {currentDeed ? (
              <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
                {/* Panel 1: Scan & Contrast Viewer (4 cols) */}
                <div className="lg:col-span-4 bg-white rounded-xl shadow-sm border border-slate-200 p-4 flex flex-col h-[750px]">
                  <div className="flex items-center justify-between pb-3 border-b border-slate-100 mb-3">
                    <div>
                      <h3 className="font-bold text-xs text-slate-800">দলিল স্ক্যান ও হস্তলিপি ভিউয়ার</h3>
                      <p className="text-[10px] text-slate-400">অস্পষ্ট কালি ও প্রাচীন কাগজের দাগ দূরীকরণ</p>
                    </div>
                    <button
                      type="button"
                      onClick={() => setIsEnhancedContrast(!isEnhancedContrast)}
                      className={`text-[11px] px-2.5 py-1 rounded border font-medium transition ${
                        isEnhancedContrast
                          ? "bg-emerald-100 hover:bg-emerald-200 text-emerald-800 border-emerald-300"
                          : "bg-slate-100 hover:bg-slate-200 text-slate-700 border-slate-300"
                      }`}
                    >
                      {isEnhancedContrast ? "এনহ্যান্সড মোড (ON)" : "মূল স্ক্যান (Original)"}
                    </button>
                  </div>

                  <div className="flex-1 bg-slate-900 rounded-lg overflow-hidden relative flex items-center justify-center border border-slate-300">
                    <img
                      src={
                        isEnhancedContrast
                          ? currentDeed.enhanced_image_path || currentDeed.original_file_path
                          : currentDeed.original_file_path || currentDeed.enhanced_image_path
                      }
                      alt="Deed Scan"
                      className="max-h-full max-w-full object-contain p-2"
                    />
                    <div className="absolute top-3 right-3 bg-slate-900/80 backdrop-blur-xs text-white text-[10px] font-bold px-2.5 py-1 rounded border border-slate-700">
                      অপটিক্যাল স্পষ্টতা: {currentDeed.overall_confidence_score}%
                    </div>
                  </div>

                  <div className="mt-3 p-3 bg-amber-50/70 border border-amber-200 rounded-lg max-h-48 overflow-y-auto">
                    <div className="flex items-center justify-between mb-1.5">
                      <span className="text-[11px] font-bold text-amber-900 flex items-center space-x-1">
                        <Search className="w-3.5 h-3.5 text-amber-700" />
                        <span>অস্পষ্ট ও হাতের লেখা বিশ্লেষণ (Zero-Hallucination):</span>
                      </span>
                      <span className="text-[10px] bg-amber-200 text-amber-800 px-1.5 py-0.2 rounded font-bold">
                        {(currentDeed.unclear_texts || []).length}টি চিহ্নিত
                      </span>
                    </div>
                    <div className="space-y-2 text-[11px]">
                      {(currentDeed.unclear_texts || []).length > 0 ? (
                        currentDeed.unclear_texts.map((u: any, idx: number) => (
                          <div key={idx} className="p-2 bg-white rounded border border-amber-200 text-[11px]">
                            <div className="flex items-center justify-between font-bold text-amber-950 mb-0.5">
                              <span>{u.term_location}</span>
                              <span className="text-[10px] bg-amber-100 px-1.5 py-0.2 rounded font-mono">{u.confidence_score}% Confidence</span>
                            </div>
                            <p className="text-slate-600 mb-1">
                              <strong>মূল অপটিক্যাল পাঠ:</strong> <span className="font-mono text-rose-700 bg-rose-50 px-1 rounded">{u.raw_ocr_snippet}</span> ➔ <strong>উদ্ধারকৃত:</strong> <span className="text-emerald-800 font-bold">{u.extracted_reading}</span>
                            </p>
                            <p className="text-[10px] text-slate-500"><strong>বিকল্প সম্ভাবনা:</strong> {u.alternatives.join(" | ")}</p>
                            <p className="text-[10px] text-amber-800 mt-1 italic">{u.guidance}</p>
                          </div>
                        ))
                      ) : (
                        <p className="text-emerald-800 font-medium">কোনো অস্পষ্ট বা দুর্বোধ্য হাতের লেখা পাওয়া যায়নি। সম্পূর্ণ পাঠ স্পষ্ট।</p>
                      )}
                    </div>
                  </div>
                </div>

                {/* Panel 2: Digitized Structured Land Schedule (5 cols) */}
                <div className="lg:col-span-5 bg-white rounded-xl shadow-sm border border-slate-200 p-5 flex flex-col h-[750px]">
                  <div className="flex items-center justify-between pb-3 border-b border-slate-100 mb-3">
                    <div>
                      <h3 className="font-bold text-sm text-slate-900">{currentDeed.deed_title}</h3>
                      <p className="text-xs text-slate-500">নিবন্ধিত দলিল ও সম্পত্তির পূর্ণাঙ্গ তফশিল</p>
                    </div>
                    <div className="flex items-center space-x-1.5">
                      <button
                        type="button"
                        onClick={openEditDeedModal}
                        className="text-xs bg-emerald-700 hover:bg-emerald-800 text-white font-medium px-2.5 py-1 rounded shadow transition flex items-center space-x-1"
                      >
                        <Save className="w-3.5 h-3.5" />
                        <span>তথ্য সংশোধন ও রি-অডিট</span>
                      </button>
                      {currentDeed.docx_url && (
                        <a href={currentDeed.docx_url} target="_blank" rel="noreferrer" className="text-xs bg-blue-50 text-blue-700 hover:bg-blue-100 border border-blue-200 px-2.5 py-1 rounded font-medium transition">
                          Word (.DOCX)
                        </a>
                      )}
                      {currentDeed.pdf_url && (
                        <a href={currentDeed.pdf_url} target="_blank" rel="noreferrer" className="text-xs bg-rose-50 text-rose-700 hover:bg-rose-100 border border-rose-200 px-2.5 py-1 rounded font-medium transition">
                          PDF
                        </a>
                      )}
                    </div>
                  </div>

                  <div className="flex-1 overflow-y-auto space-y-4 pr-1 text-xs">
                    {/* Header Metadata */}
                    <div className="grid grid-cols-2 gap-2 bg-slate-50 p-3 rounded-lg border border-slate-100">
                      <div><span className="text-slate-500 block text-[10px]">দলিল নম্বর:</span><span className="font-semibold text-slate-800">{currentDeed.deed_number || "অনুল্লেখিত"}</span></div>
                      <div><span className="text-slate-500 block text-[10px]">রেজিস্ট্রেশন সাল:</span><span className="font-semibold text-slate-800">{currentDeed.registration_year ? `${currentDeed.registration_year} খ্রিঃ` : "অজ্ঞাত"}</span></div>
                      <div><span className="text-slate-500 block text-[10px]">সাব-রেজিস্ট্রি অফিস:</span><span className="font-semibold text-slate-800">{`${currentDeed.sub_registry_office || "পাওয়া যায়নি"}, ${currentDeed.district || "জেলা পাওয়া যায়নি"}`}</span></div>
                      <div><span className="text-slate-500 block text-[10px]">দলিলের শ্রেণি:</span><span className="font-semibold text-emerald-800 uppercase">{currentDeed.deed_type?.replace("_", " ")}</span></div>
                    </div>

                    {/* Parties Card */}
                    <div className="border border-slate-200 rounded-lg p-3">
                      <span className="font-bold text-slate-800 text-[11px] block border-b border-slate-100 pb-1 mb-2">পক্ষগণের বিবরণ (Parties):</span>
                      <div className="space-y-2">
                        <div className="p-2 bg-slate-50 rounded">
                          <span className="text-slate-500 block text-[10px]">১ম পক্ষ (দাতা / বিক্রেতা):</span>
                          <span className="font-bold text-slate-900 block">{currentDeed.parties?.first_party_name || "পাওয়া যায়নি"}</span>
                          <span className="text-slate-600 block text-[11px]">পিতা: {currentDeed.parties?.first_party_father || "পাওয়া যায়নি"}</span>
                          <span className="text-slate-500 block text-[10px]">{currentDeed.parties?.first_party_address || ""}</span>
                        </div>
                        <div className="p-2 bg-slate-50 rounded">
                          <span className="text-slate-500 block text-[10px]">২য় পক্ষ (গ্রহীতা / ক্রেতা):</span>
                          <span className="font-bold text-slate-900 block">{currentDeed.parties?.second_party_name || "পাওয়া যায়নি"}</span>
                          <span className="text-slate-600 block text-[11px]">পিতা: {currentDeed.parties?.second_party_father || "পাওয়া যায়নি"}</span>
                          <span className="text-slate-500 block text-[10px]">{currentDeed.parties?.second_party_address || ""}</span>
                        </div>
                      </div>
                    </div>

                    {/* Land Schedule Card */}
                    <div className="border border-emerald-200 bg-emerald-50/30 rounded-lg p-3">
                      <span className="font-bold text-emerald-950 text-[11px] block border-b border-emerald-200/80 pb-1 mb-2">সম্পত্তির পূর্ণাঙ্গ তফশিল (Land Schedule):</span>
                      <div className="grid grid-cols-2 gap-2 text-[11px]">
                        <div><span className="text-slate-500">মৌজা: </span><span className="font-semibold text-slate-800">{currentDeed.schedule?.mouza || currentDeed.mouza || "-"}</span></div>
                        <div><span className="text-slate-500">জে.এল নং: </span><span className="font-semibold text-slate-800">{currentDeed.schedule?.jl_no || currentDeed.jl_number || "-"}</span></div>
                        <div><span className="text-slate-500">সি.এস খতিয়ান: </span><span className="font-semibold text-slate-800">{currentDeed.schedule?.khatian_cs || "-"}</span></div>
                        <div><span className="text-slate-500">এস.এ খতিয়ান: </span><span className="font-semibold text-slate-800">{currentDeed.schedule?.khatian_sa || "-"}</span></div>
                        <div><span className="text-slate-500">আর.এস খতিয়ান: </span><span className="font-semibold text-slate-800">{currentDeed.schedule?.khatian_rs || "-"}</span></div>
                        <div><span className="text-slate-500">বি.এস / সিটি: </span><span className="font-semibold text-slate-800">{currentDeed.schedule?.khatian_bs || "-"}</span></div>
                        <div><span className="text-slate-500">সাবেক দাগ: </span><span className="font-semibold text-slate-800">{currentDeed.schedule?.dag_former || "-"}</span></div>
                        <div><span className="text-slate-500">হাল দাগ: </span><span className="font-semibold text-slate-800">{currentDeed.schedule?.dag_current || "-"}</span></div>
                        <div><span className="text-slate-500">জমির শ্রেণি: </span><span className="font-semibold text-slate-800">{currentDeed.schedule?.land_class || "-"}</span></div>
                        <div><span className="text-slate-500">জমির পরিমাণ: </span><span className="font-bold text-emerald-800">{currentDeed.schedule?.transferred_area_bangla || (currentDeed.schedule?.transferred_area_decimals != null ? `${currentDeed.schedule.transferred_area_decimals} শতাংশ` : "পাওয়া যায়নি")}</span></div>
                        <div className="col-span-2"><span className="text-slate-500">হস্তান্তরিত হিস্যা: </span><span className="font-semibold text-slate-800">{currentDeed.schedule?.share_portion || "পাওয়া যায়নি"}</span></div>
                      </div>
                    </div>

                    {/* Boundaries Card */}
                    <div className="border border-slate-200 rounded-lg p-3">
                      <span className="font-bold text-slate-800 text-[11px] block border-b border-slate-100 pb-1 mb-2">চৌহদ্দি (Four Boundaries):</span>
                      <div className="grid grid-cols-2 gap-2 text-[11px]">
                        <div className="p-1.5 bg-slate-50 rounded"><strong>উত্তর:</strong> <span>{currentDeed.boundaries?.north || "-"}</span></div>
                        <div className="p-1.5 bg-slate-50 rounded"><strong>দক্ষিণ:</strong> <span>{currentDeed.boundaries?.south || "-"}</span></div>
                        <div className="p-1.5 bg-slate-50 rounded"><strong>পূর্ব:</strong> <span>{currentDeed.boundaries?.east || "-"}</span></div>
                        <div className="p-1.5 bg-slate-50 rounded"><strong>পশ্চিম:</strong> <span>{currentDeed.boundaries?.west || "-"}</span></div>
                      </div>
                    </div>

                    {/* Chain of Title */}
                    <div className="border border-slate-200 rounded-lg p-3">
                      <span className="font-bold text-slate-800 text-[11px] block border-b border-slate-100 pb-1 mb-2">স্বত্বের ধারাবাহিকতা ও বায়া দলিল (Chain of Title):</span>
                      <div className="text-[11px] space-y-1">
                        <div><span className="text-slate-500">পূর্ববর্তী বায়া দলিল নং:</span> <span className="font-semibold text-slate-800">{currentDeed.chain_of_title?.prior_deed_number || "অনুল্লেখিত"}</span></div>
                        <div><span className="text-slate-500">পূর্ববর্তী বায়া দলিলের সাল:</span> <span className="font-semibold text-slate-800">{currentDeed.chain_of_title?.prior_deed_year ? `${currentDeed.chain_of_title?.prior_deed_year} খ্রিঃ` : "-"}</span></div>
                        <div><span className="text-slate-500">পূর্ববর্তী মালিকের নাম:</span> <span className="font-semibold text-slate-800">{currentDeed.chain_of_title?.prior_owner_name || "-"}</span></div>
                        <div><span className="text-slate-500">মালিকানা অর্জনের সূত্র:</span> <span className="font-semibold text-slate-800">{currentDeed.chain_of_title?.succession_type || "-"}</span></div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Panel 3: Fraud & Authenticity Audit (3 cols) */}
                <div className="lg:col-span-3 bg-white rounded-xl shadow-sm border border-slate-200 p-5 flex flex-col h-[750px]">
                  <div className="pb-3 border-b border-slate-100 mb-3">
                    <h3 className="font-bold text-xs text-slate-800">জাল দলিল ও সত্যতা নিরীক্ষা</h3>
                    <p className="text-[10px] text-slate-400">৮টি কালানুক্রমিক ও সংবিধিবদ্ধ রুলস চেক</p>
                  </div>

                  <div className="flex-1 overflow-y-auto space-y-4 pr-1">
                    {/* Fraud Risk Gauge */}
                    <div
                      className={`p-4 rounded-xl border flex flex-col items-center justify-center text-center ${
                        (currentDeed.fraud_risk_score ?? 0) >= 50
                          ? "bg-rose-50 border-rose-200"
                          : (currentDeed.fraud_risk_score ?? 0) >= 25
                          ? "bg-amber-50 border-amber-200"
                          : "bg-emerald-50 border-emerald-200"
                      }`}
                    >
                      <span className="text-[10px] uppercase font-bold text-slate-500 tracking-wider">জাল দলিল ঝুঁকি স্কোর</span>
                      <div className="flex items-baseline space-x-1 mt-1">
                        <span
                          className={`text-3xl font-extrabold ${
                            (currentDeed.fraud_risk_score ?? 0) >= 50
                              ? "text-rose-700"
                              : (currentDeed.fraud_risk_score ?? 0) >= 25
                              ? "text-amber-700"
                              : "text-emerald-800"
                          }`}
                        >
                          {currentDeed.fraud_risk_score ?? 0}
                        </span>
                        <span className="text-xs text-slate-400">/১০০</span>
                      </div>
                      <span
                        className={`mt-2 text-xs font-bold px-3 py-0.5 rounded-full ${
                          (currentDeed.fraud_risk_score ?? 0) >= 50
                            ? "bg-rose-200 text-rose-900"
                            : (currentDeed.fraud_risk_score ?? 0) >= 25
                            ? "bg-amber-200 text-amber-900"
                            : "bg-emerald-200 text-emerald-900"
                        }`}
                      >
                        {(currentDeed.fraud_risk_score ?? 0) >= 50
                          ? "⚠️ চরম ঝুঁকি • জাল দলিলের লক্ষণ (PROBABLE FORGERY)"
                          : (currentDeed.fraud_risk_score ?? 0) >= 25
                          ? "সন্দেহজনক দলিল (SUSPICIOUS)"
                          : "✓ ঝুঁকিমুক্ত ও খাঁটি দলিল (AUTHENTIC)"}
                      </span>
                    </div>

                    {/* Red Flags Warning Card */}
                    <div className="space-y-2">
                      <span className="text-[11px] font-bold text-slate-700 block">চিহ্নিত আইনি অসংগতি ও রেড ফ্ল্যাগ:</span>
                      <div className="space-y-2">
                        {(currentDeed.fraud_assessment?.red_flags || []).length > 0 ? (
                          currentDeed.fraud_assessment.red_flags.map((f: any, i: number) => (
                            <div key={i} className="p-2.5 rounded-lg bg-rose-50 border border-rose-200 text-xs">
                              <span className="font-bold text-rose-900 block text-[11px] mb-0.5">⚠️ {f.title}</span>
                              <p className="text-[10px] text-rose-800 leading-relaxed">{f.message_bangla}</p>
                            </div>
                          ))
                        ) : (
                          <div className="p-2 bg-emerald-50 rounded border border-emerald-200 text-emerald-800 text-[11px]">কোনো জালিয়াতি বা অসঙ্গতি পাওয়া যায়নি।</div>
                        )}
                      </div>
                    </div>

                    {/* Passed Rules List */}
                    <div className="space-y-1.5">
                      <span className="text-[11px] font-bold text-slate-700 block">যাচাইকৃত সঠিক আইনি শর্ত:</span>
                      <ul className="space-y-1 text-[11px] text-slate-600">
                        {(currentDeed.fraud_assessment?.passed_checks || []).map((p: string, i: number) => (
                          <li key={i} className="flex items-start space-x-1.5">
                            <span className="text-emerald-600 font-bold">✓</span>
                            <span>{p}</span>
                          </li>
                        ))}
                      </ul>
                    </div>

                    {/* Legal Recommendation Box */}
                    <div className="p-3 rounded-lg bg-slate-50 border border-slate-200">
                      <span className="text-[11px] font-bold text-slate-800 block mb-1 flex items-center space-x-1">
                        <Scale className="w-3.5 h-3.5 text-sky-700" />
                        <span>আইনজীবী পরামর্শ (Counsel Advice):</span>
                      </span>
                      <p className="text-[11px] text-slate-600 leading-relaxed">
                        {currentDeed.fraud_assessment?.legal_recommendation || "সাব-রেজিস্ট্রি অফিসের বালাম বহির সাথে মিলিয়ে যাচাই করুন।"}
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            ) : (
              <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-12 text-center text-slate-500">
                দলিল ডেটা লোড হচ্ছে অথবা কোনো দলিল নির্বাচন করা হয়নি। উপরে উল্লিখিত বোতামে ক্লিক করুন।
              </div>
            )}
          </div>
        )}
      
        {/* Deed Edit Modal */}
        {isEditingDeed && (
          <div className="fixed inset-0 bg-black/60 backdrop-blur-xs z-50 flex items-center justify-center p-4">
            <div className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-2xl border border-slate-200 max-h-[90vh] overflow-y-auto">
              <div className="flex items-center justify-between border-b pb-3 mb-4">
                <div>
                  <h3 className="font-bold text-sm text-slate-900">দলিলের পাঠ ও তফশিল তথ্য সংশোধন</h3>
                  <p className="text-xs text-slate-500">হস্তলিপির পাঠ সংশোধন করুন। সিস্টেম তাৎক্ষণিক ৮টি রুলসে পুনঃনিরীক্ষা করবে।</p>
                </div>
                <button
                  type="button"
                  onClick={() => setIsEditingDeed(false)}
                  className="text-slate-400 hover:text-slate-600 text-sm font-bold"
                >
                  ✕
                </button>
              </div>

              <div className="space-y-3 text-xs">
                <div>
                  <label className="font-semibold text-slate-700 block mb-1">দলিলের শিরোনাম:</label>
                  <input
                    type="text"
                    value={deedEditForm.deed_title || ""}
                    onChange={(e) => setDeedEditForm({ ...deedEditForm, deed_title: e.target.value })}
                    className="w-full border rounded-lg p-2"
                  />
                </div>
                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <label className="font-semibold text-slate-700 block mb-1">দলিল নম্বর:</label>
                    <input
                      type="text"
                      value={deedEditForm.deed_number || ""}
                      onChange={(e) => setDeedEditForm({ ...deedEditForm, deed_number: e.target.value })}
                      className="w-full border rounded-lg p-2"
                    />
                  </div>
                  <div>
                    <label className="font-semibold text-slate-700 block mb-1">রেজিস্ট্রেশন সাল:</label>
                    <input
                      type="number"
                      value={deedEditForm.registration_year || 1993}
                      onChange={(e) => setDeedEditForm({ ...deedEditForm, registration_year: e.target.value })}
                      className="w-full border rounded-lg p-2"
                    />
                  </div>
                </div>

                <div className="p-3 bg-slate-50 rounded-lg border space-y-2">
                  <span className="font-bold text-slate-800 block text-[11px]">পক্ষগণের নাম সংশোধন:</span>
                  <div>
                    <label className="text-[11px] text-slate-600 block">১ম পক্ষ (দাতা / বিক্রেতা):</label>
                    <input
                      type="text"
                      value={deedEditForm.first_party_name || ""}
                      onChange={(e) => setDeedEditForm({ ...deedEditForm, first_party_name: e.target.value })}
                      className="w-full border rounded p-1.5 text-xs bg-white"
                      placeholder="দাতার সঠিক নাম লিখুন..."
                    />
                  </div>
                  <div>
                    <label className="text-[11px] text-slate-600 block">২য় পক্ষ (গ্রহীতা / ক্রেতা):</label>
                    <input
                      type="text"
                      value={deedEditForm.second_party_name || ""}
                      onChange={(e) => setDeedEditForm({ ...deedEditForm, second_party_name: e.target.value })}
                      className="w-full border rounded p-1.5 text-xs bg-white"
                      placeholder="গ্রহীতার সঠিক নাম লিখুন..."
                    />
                  </div>
                </div>

                <div className="p-3 bg-emerald-50/50 rounded-lg border border-emerald-200 space-y-2">
                  <span className="font-bold text-emerald-950 block text-[11px]">তফশিল ও খতিয়ান তথ্য:</span>
                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <label className="text-[11px] text-slate-600 block">মৌজার নাম:</label>
                      <input
                        type="text"
                        value={deedEditForm.mouza || ""}
                        onChange={(e) => setDeedEditForm({ ...deedEditForm, mouza: e.target.value })}
                        className="w-full border rounded p-1.5 text-xs bg-white"
                      />
                    </div>
                    <div>
                      <label className="text-[11px] text-slate-600 block">এস.এ / আর.এস খতিয়ান:</label>
                      <input
                        type="text"
                        value={deedEditForm.khatian_sa || ""}
                        onChange={(e) => setDeedEditForm({ ...deedEditForm, khatian_sa: e.target.value })}
                        className="w-full border rounded p-1.5 text-xs bg-white"
                      />
                    </div>
                    <div>
                      <label className="text-[11px] text-slate-600 block">হাল দাগ নম্বর:</label>
                      <input
                        type="text"
                        value={deedEditForm.dag_current || ""}
                        onChange={(e) => setDeedEditForm({ ...deedEditForm, dag_current: e.target.value })}
                        className="w-full border rounded p-1.5 text-xs bg-white"
                      />
                    </div>
                    <div>
                      <label className="text-[11px] text-slate-600 block">জমির পরিমাণ (শতক):</label>
                      <input
                        type="number"
                        step="0.1"
                        value={deedEditForm.transferred_area_decimals || 0}
                        onChange={(e) => setDeedEditForm({ ...deedEditForm, transferred_area_decimals: e.target.value })}
                        className="w-full border rounded p-1.5 text-xs bg-white"
                      />
                    </div>
                  </div>
                </div>

                <div className="flex items-center justify-end space-x-2 pt-3 border-t">
                  <button
                    type="button"
                    onClick={() => setIsEditingDeed(false)}
                    className="px-3 py-1.5 rounded border border-slate-300 text-slate-700 hover:bg-slate-50"
                  >
                    বাতিল
                  </button>
                  <button
                    type="button"
                    onClick={handleSaveDeedEdits}
                    className="px-4 py-1.5 rounded bg-emerald-600 hover:bg-emerald-700 text-white font-semibold flex items-center space-x-1.5 shadow"
                  >
                    <Save className="w-3.5 h-3.5" />
                    <span>সংরক্ষণ ও পুনঃনিরীক্ষা</span>
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

      </main>

      <footer className="bg-white border-t border-slate-200 py-3 text-center text-xs text-slate-400">
        বাংলাদেশ লিগ্যাল ইন্টেলিজেন্স অ্যান্ড অপারেশনস প্ল্যাটফর্ম • সর্বস্বত্ব সংরক্ষিত ২০২৬ • Verified Bangladesh Legal Sources Only
      </footer>
    </div>
  );
}
