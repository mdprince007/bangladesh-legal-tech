"use client";

import React, { useState, useEffect } from "react";
import {
  Shield,
  BookOpen,
  Terminal,
  Sparkles,
  CheckCircle,
  ArrowLeft,
  UploadCloud,
  Database,
  RefreshCw,
  Trash2,
  Eye,
  X,
  Loader2,
  FileText
} from "lucide-react";
import Link from "next/link";

const API_BASE = "/api/v1";

const CHAPTERS = [
  { num: 1, title: "অধ্যায় ১: ড্রাফটিংয়ের প্রাথমিক প্রস্তুতি ও সত্যনিষ্ঠতা (পৃষ্ঠা ২৩-৪৩)" },
  { num: 2, title: "অধ্যায় ২: রেজিস্টার্ড ও আন-রেজিস্টার্ড চুক্তিপত্র - ৯টি নমুনা (পৃষ্ঠা ৪৪-৯৭)" },
  { num: 3, title: "অধ্যায় ৩: লিগ্যাল ওপিনিয়ন ও জমির সত্ত্ব যাচাই (পৃষ্ঠা ৯৮-১১৮)" },
  { num: 4, title: "অধ্যায় ৪: লিগ্যাল নোটিশ ও ১৩৮ ধারা নোটিশ (পৃষ্ঠা ১১৯-১৩৬)" },
  { num: 5, title: "অধ্যায় ৫: আইনজীবী প্রত্যয়নপত্র ও নন-এনকামব্রেন্স (পৃষ্ঠা ১৩৭-১৪৮)" },
  { num: 6, title: "অধ্যায় ৬: আরজি (Plaint) ও লিখিত জবাব (পৃষ্ঠা ১৪৯-১৭৪)" },
  { num: 7, title: "অধ্যায় ৭: অন্তর্বর্তীকালীন নিষেধাজ্ঞা ও আরজি খারিজ (পৃষ্ঠা ১৭৫-২১৩)" },
  { num: 8, title: "অধ্যায় ৮: আপিল বিভাগের দরখাস্ত ও সিভিল পিটিশন - CP/CMP (পৃষ্ঠা ২১৪-২৯৯)" },
  { num: 9, title: "অধ্যায় ৯: রিট পিটিশন ও এফিডেভিট-ইন-অপোজিশন - Art. 102 (পৃষ্ঠা ৩০০-৩৬৫)" },
  { num: 10, title: "অধ্যায় ১০: প্রথম আপিল, মিস আপিল ও স্টে দরখাস্ত - FMA/FA (পৃষ্ঠা ৩৬৬-৪০২)" },
  { num: 11, title: "অধ্যায় ১১: সিভিল রিভিশন - Section 115 CPC (পৃষ্ঠা ৪০৩-৪৪৪)" },
  { num: 12, title: "অধ্যায় ১২: জিডি (GD), এফআইআর (FIR) ও সিআর মামলা (পৃষ্ঠা ৪৪৫-৪৫২)" },
  { num: 13, title: "অধ্যায় ১৩: ৪৯৮ ধারা আগাম ও নিয়মিত জামিন, ফৌজদারি রিভিশন (পৃষ্ঠা ৪৫৩-৫৪৪)" },
  { num: 14, title: "অধ্যায় ১৪: মামলা বাতিল ও ৫৬১এ ধারা দরখাস্ত - Quashment (পৃষ্ঠা ৫৪৫-৫৬৩)" },
  { num: 15, title: "অধ্যায় ১৫: তামাদি মার্জনা - Section 5 Limitation Act (পৃষ্ঠা ৫৬৪-৫৮২)" },
  { num: 16, title: "অধ্যায় ১৬: আদালত অবমাননা দরখাস্ত - Contempt Petition (পৃষ্ঠা ৫৮৩-৬০৯)" },
  { num: 17, title: "অধ্যায় ১৭: আয়কর রেফারেন্স, ভ্যাট আপিল ও কাস্টমস রিভিশন (পৃষ্ঠা ৬১০-৬৬৬)" },
  { num: 18, title: "অধ্যায় ১৮: কোম্পানি গঠন - MoA ও AoA খসড়া (পৃষ্ঠা ৬৬৭-৭৪৬)" },
  { num: 19, title: "অধ্যায় ১৯: কোম্পানি মামলা ও সংখ্যালঘু শেয়ারহোল্ডার প্রতিকার - ২৩৩ ধারা (পৃষ্ঠা ৭৪৭-৮০১)" },
  { num: 20, title: "অধ্যায় ২০: ব্যাংক ঋণ, চার্জ রেজিস্ট্রেশন ও ব্যক্তিগত গ্যারান্টি (পৃষ্ঠা ৮০২-৮৪৩)" },
  { num: 21, title: "অধ্যায় ২১: বিবিধ দেওয়ানি ও রিট কার্যবিধি দরখাস্ত - LCR, সংশোধনী (পৃষ্ঠা ৮৪৪-৮৮৯)" }
];

export default function AdminPage() {
  const [stats, setStats] = useState<any>(null);
  const [ingestedDocs, setIngestedDocs] = useState<any[]>([]);
  const [selectedChapter, setSelectedChapter] = useState(1);
  const [loadingIngestFull, setLoadingIngestFull] = useState(false);
  const [loadingIngestChapter, setLoadingIngestChapter] = useState(false);
  const [ingestBanner, setIngestBanner] = useState<any>(null);

  // Custom File Upload States
  const [customFile, setCustomFile] = useState<File | null>(null);
  const [customTitle, setCustomTitle] = useState("");
  const [uploading, setUploading] = useState(false);
  const [uploadBanner, setUploadBanner] = useState<any>(null);

  // Lessons Modal States
  const [activeModalDoc, setActiveModalDoc] = useState<any>(null);
  const [modalLessons, setModalLessons] = useState<any[]>([]);
  const [loadingLessons, setLoadingLessons] = useState(false);

  useEffect(() => {
    fetchStats();
    fetchIngestedDocs();
  }, []);

  const fetchStats = async () => {
    try {
      const res = await fetch(`${API_BASE}/admin/stats`);
      if (res.ok) setStats(await res.json());
    } catch (e) {}
  };

  const fetchIngestedDocs = async () => {
    try {
      const res = await fetch(`${API_BASE}/admin/ingested-documents`);
      if (res.ok) setIngestedDocs(await res.json());
    } catch (e) {}
  };

  const triggerIngestFull = async () => {
    setLoadingIngestFull(true);
    setIngestBanner(null);
    try {
      const res = await fetch(`${API_BASE}/admin/ingest-nasrin-book`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ingest_all: true })
      });
      if (res.ok) {
        const data = await res.json();
        setIngestBanner({
          title: "সম্পূর্ণ ৮৮৯ পৃষ্ঠার বই ইনজেস্ট সফল (All 21 Chapters)",
          message: data.message,
          rules: data.core_rules_extracted || []
        });
        fetchStats();
        fetchIngestedDocs();
      }
    } catch (e) {}
    setLoadingIngestFull(false);
  };

  const triggerIngestChapter = async () => {
    setLoadingIngestChapter(true);
    setIngestBanner(null);
    try {
      const res = await fetch(`${API_BASE}/admin/ingest-nasrin-book`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ chapter_num: selectedChapter, ingest_all: false })
      });
      if (res.ok) {
        const data = await res.json();
        setIngestBanner({
          title: `অধ্যায় ${selectedChapter}: ${data.chapter_title}`,
          message: data.message,
          rules: data.core_rules_extracted || []
        });
        fetchStats();
        fetchIngestedDocs();
      }
    } catch (e) {}
    setLoadingIngestChapter(false);
  };

  const handleCustomFileUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!customFile) return;

    setUploading(true);
    setUploadBanner(null);

    const formData = new FormData();
    formData.append("file", customFile);
    if (customTitle.trim()) {
      formData.append("title", customTitle.trim());
    }

    try {
      const res = await fetch(`${API_BASE}/admin/ingest-file`, {
        method: "POST",
        body: formData
      });
      if (res.ok) {
        const data = await res.json();
        setUploadBanner({
          title: data.message,
          details: `নথি: ${data.title} | মোট লেসন: ${data.total_lessons} টি | পৃষ্ঠা: ${data.total_pages}`
        });
        setCustomFile(null);
        setCustomTitle("");
        fetchStats();
        fetchIngestedDocs();
      }
    } catch (e) {}
    setUploading(false);
  };

  const viewDocLessons = async (doc: any) => {
    setActiveModalDoc(doc);
    setLoadingLessons(true);
    setModalLessons([]);
    try {
      const res = await fetch(`${API_BASE}/admin/ingested-documents/${doc.id}/lessons`);
      if (res.ok) {
        setModalLessons(await res.json());
      }
    } catch (e) {}
    setLoadingLessons(false);
  };

  const deleteDoc = async (docId: string) => {
    if (!confirm("আপনি কি নিশ্চিত যে এই নথিটি এবং এর তৈরি হওয়া সকল লেসন মুছে ফেলতে চান?")) return;
    try {
      const res = await fetch(`${API_BASE}/admin/ingested-documents/${docId}`, { method: "DELETE" });
      if (res.ok) {
        fetchStats();
        fetchIngestedDocs();
      }
    } catch (e) {}
  };

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100 flex flex-col font-sans">
      {/* Header */}
      <header className="bg-slate-950 border-b border-slate-800 h-16 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 h-full flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-9 h-9 rounded-lg bg-emerald-600 flex items-center justify-center font-bold text-white shadow">
              <Shield className="w-5 h-5" />
            </div>
            <div>
              <span className="font-bold text-base text-white">সুপার অ্যাডমিন ও সিস্টেম নলেজ হাব (Admin Portal)</span>
              <p className="text-xs text-slate-400">Bangladesh Legal Operating System • Full Multi-Chapter & File Ingestion</p>
            </div>
          </div>
          <div className="flex items-center space-x-3">
            <Link href="/" className="text-xs bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 px-3 py-1.5 rounded-lg flex items-center space-x-1 transition">
              <ArrowLeft className="w-3.5 h-3.5" />
              <span>মূল প্ল্যাটফর্মে ফিরুন</span>
            </Link>
            <a href="/docs" target="_blank" rel="noreferrer" className="text-xs bg-emerald-700 hover:bg-emerald-600 text-white font-medium px-3 py-1.5 rounded-lg flex items-center space-x-1 transition">
              <Terminal className="w-3.5 h-3.5" />
              <span>Swagger API Docs</span>
            </a>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-8 flex-1 w-full space-y-6">
        {/* Metrics Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-slate-800 border border-slate-700 rounded-xl p-4">
            <span className="text-xs text-slate-400">সক্রিয় আইনি বিষয় (Matters)</span>
            <div className="text-3xl font-bold text-white mt-1">{stats?.total_matters || 0}</div>
            <span className="text-[10px] text-emerald-400">আইসোলেটেড ক্লায়েন্ট রেকর্ড</span>
          </div>
          <div className="bg-slate-800 border border-slate-700 rounded-xl p-4">
            <span className="text-xs text-slate-400">প্রস্তুতকৃত চুক্তিপত্র (Documents)</span>
            <div className="text-3xl font-bold text-white mt-1">{stats?.total_documents_drafted || 0}</div>
            <span className="text-[10px] text-emerald-400">DOCX ও PDF জেনারেটেড</span>
          </div>
          <div className="bg-slate-800 border border-slate-700 rounded-xl p-4">
            <span className="text-xs text-slate-400">ইনজেস্টেড নলেজ লেসন (Lessons)</span>
            <div className="text-3xl font-bold text-emerald-400 mt-1">{stats?.ingested_lessons_count || "১১০+"}</div>
            <span className="text-[10px] text-slate-400">২১টি অধ্যায় ও কাস্টম নথি</span>
          </div>
          <div className="bg-slate-800 border border-slate-700 rounded-xl p-4">
            <span className="text-xs text-slate-400">অডিট লগ এন্ট্রি (Audit Logs)</span>
            <div className="text-3xl font-bold text-white mt-1">{stats?.audit_logs_count || 0}</div>
            <span className="text-[10px] text-slate-400">Tamper-Resistant History</span>
          </div>
        </div>

        {/* Section 1: Dr. Syeda Nasrin's Book (Full Book Ingest + Chapter Selector) */}
        <div className="bg-slate-800 border border-slate-700 rounded-xl p-6 shadow-lg space-y-5">
          <div className="flex flex-col md:flex-row md:items-center justify-between pb-4 border-b border-slate-700 gap-4">
            <div className="flex items-center space-x-3">
              <div className="p-2.5 rounded-lg bg-emerald-950 border border-emerald-800 text-emerald-400">
                <BookOpen className="w-6 h-6" />
              </div>
              <div>
                <h2 className="text-base font-semibold text-white">বই ইনজেকশন: Basics of Legal Drafting (ড. সৈয়দা নাসরিন, সুপ্রিম কোর্ট)</h2>
                <p className="text-xs text-slate-400">ফাইল: <code className="text-emerald-300 font-mono">c:/legeldraft/learning/Nasrin-book.pdf</code> (৮৮৯ পৃষ্ঠা • ২১টি অধ্যায়)</p>
              </div>
            </div>

            <button
              onClick={triggerIngestFull}
              disabled={loadingIngestFull}
              className="bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-xs px-4 py-2.5 rounded-lg flex items-center space-x-2 transition shadow shrink-0"
            >
              {loadingIngestFull ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
              <span>{loadingIngestFull ? "সম্পূর্ণ ৮৮৯ পৃষ্ঠা ইনজেস্ট হচ্ছে..." : "সম্পূর্ণ বই ইনজেস্ট করুন (All 21 Chapters)"}</span>
            </button>
          </div>

          {/* Single Chapter Selector */}
          <div className="bg-slate-900 border border-slate-800 rounded-lg p-4 flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div className="flex-1">
              <label className="block text-xs font-medium text-slate-300 mb-1">সুনির্দিষ্ট অধ্যায় নির্বাচন করে ইনজেস্ট করুন:</label>
              <select
                value={selectedChapter}
                onChange={(e) => setSelectedChapter(Number(e.target.value))}
                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-xs text-slate-100 focus:outline-none focus:ring-1 focus:ring-emerald-500"
              >
                {CHAPTERS.map((ch) => (
                  <option key={ch.num} value={ch.num}>{ch.title}</option>
                ))}
              </select>
            </div>
            <button
              onClick={triggerIngestChapter}
              disabled={loadingIngestChapter}
              className="bg-slate-800 hover:bg-slate-700 text-emerald-400 border border-emerald-800 hover:border-emerald-600 font-semibold text-xs px-4 py-2.5 rounded-lg flex items-center space-x-2 transition shadow shrink-0 self-end md:self-auto"
            >
              {loadingIngestChapter ? <Loader2 className="w-4 h-4 animate-spin" /> : <BookOpen className="w-4 h-4" />}
              <span>{loadingIngestChapter ? "প্রসেসিং..." : "শুধুমাত্র নির্বাচিত অধ্যায় ইনজেস্ট করুন"}</span>
            </button>
          </div>

          {/* Real-time Ingestion Result Box */}
          {ingestBanner && (
            <div className="p-4 rounded-lg bg-slate-900 border border-emerald-900/60 space-y-3">
              <div className="flex items-center justify-between">
                <h4 className="text-xs font-bold text-emerald-400 flex items-center space-x-1.5">
                  <CheckCircle className="w-4 h-4" />
                  <span>{ingestBanner.title}</span>
                </h4>
                <span className="text-[10px] bg-emerald-950 border border-emerald-800 text-emerald-300 px-2 py-0.5 rounded">সফল</span>
              </div>
              <p className="text-xs text-slate-300">{ingestBanner.message}</p>
              {ingestBanner.rules && ingestBanner.rules.length > 0 && (
                <div className="space-y-1">
                  <span className="text-[11px] font-semibold text-slate-400">এক্সট্রাক্টকৃত ড্রাফটিং নীতি ও নিয়মাবলী:</span>
                  <ul className="text-xs space-y-1.5 text-slate-300 list-disc list-inside bg-slate-950/60 p-3 rounded border border-slate-800">
                    {ingestBanner.rules.slice(0, 8).map((r: string, idx: number) => (
                      <li key={idx}>{r}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Section 2: Arbitrary Custom File Upload (PDF, DOCX, TXT) */}
        <div className="bg-slate-800 border border-slate-700 rounded-xl p-6 shadow-lg space-y-4">
          <div className="flex items-center space-x-3 pb-3 border-b border-slate-700">
            <div className="p-2.5 rounded-lg bg-sky-950 border border-sky-800 text-sky-400">
              <UploadCloud className="w-6 h-6" />
            </div>
            <div>
              <h2 className="text-base font-semibold text-white">নতুন আইনি নথি বা ফাইল আপলোড ও ইনজেস্ট করুন (Upload Custom Legal File)</h2>
              <p className="text-xs text-slate-400">সমর্থিত ফরম্যাট: PDF, DOCX, TXT (অটোমেটিক লেসন ও রুল চ্যঙ্কিং)</p>
            </div>
          </div>

          <form onSubmit={handleCustomFileUpload} className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="md:col-span-2 space-y-3">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">নথির শিরোনাম (ঐচ্ছিক):</label>
                <input
                  type="text"
                  value={customTitle}
                  onChange={(e) => setCustomTitle(e.target.value)}
                  placeholder="যেমন: বাংলাদেশ শ্রম আইন নির্দেশিকা ২০২৬"
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-sky-500"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">ফাইল নির্বাচন করুন (Choose PDF / DOCX / TXT):</label>
                <input
                  type="file"
                  accept=".pdf,.docx,.doc,.txt,.md"
                  onChange={(e) => {
                    if (e.target.files && e.target.files.length > 0) {
                      setCustomFile(e.target.files[0]);
                    }
                  }}
                  className="w-full text-xs text-slate-400 file:mr-3 file:py-2 file:px-3 file:rounded-lg file:border-0 file:text-xs file:font-semibold file:bg-slate-700 file:text-slate-200 hover:file:bg-slate-600 bg-slate-900 border border-slate-700 rounded-lg p-1"
                />
              </div>
            </div>
            <div className="flex flex-col justify-end">
              <button
                type="submit"
                disabled={uploading || !customFile}
                className="w-full bg-sky-600 hover:bg-sky-500 disabled:opacity-50 text-white font-semibold text-xs px-4 py-2.5 rounded-lg flex items-center justify-center space-x-2 transition shadow"
              >
                {uploading ? <Loader2 className="w-4 h-4 animate-spin" /> : <FileText className="w-4 h-4" />}
                <span>{uploading ? "আপলোড ও ইনজেস্ট চলছে..." : "ফাইল আপলোড ও ইনজেস্ট করুন"}</span>
              </button>
            </div>
          </form>

          {uploadBanner && (
            <div className="p-3 rounded-lg bg-slate-900 border border-sky-900/60 text-xs space-y-1">
              <p className="text-sky-300 font-semibold">{uploadBanner.title}</p>
              <p className="text-slate-400">{uploadBanner.details}</p>
            </div>
          )}
        </div>

        {/* Section 3: Ingested Documents Table & Lessons Viewer */}
        <div className="bg-slate-800 border border-slate-700 rounded-xl p-6 shadow-lg space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-700">
            <div className="flex items-center space-x-3">
              <div className="p-2.5 rounded-lg bg-emerald-950 border border-emerald-800 text-emerald-400">
                <Database className="w-6 h-6" />
              </div>
              <div>
                <h2 className="text-base font-semibold text-white">ইনজেস্টেড আইনি ডাটাবেস ও লেসন ভিউয়ার (Indexed Documents & Lessons)</h2>
                <p className="text-xs text-slate-400">সিস্টেমে সক্রিয় নথিসমূহ এবং তৈরি হওয়া মোট লেসনের তালিকা</p>
              </div>
            </div>
            <button
              onClick={() => { fetchStats(); fetchIngestedDocs(); }}
              className="text-xs bg-slate-900 hover:bg-slate-700 border border-slate-700 text-slate-300 px-3 py-1.5 rounded-lg flex items-center space-x-1 transition"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              <span>রিফ্রেশ</span>
            </button>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-300">
              <thead className="bg-slate-900/80 text-slate-400 uppercase font-semibold border-b border-slate-700">
                <tr>
                  <th className="p-3">নথির শিরোনাম (Title)</th>
                  <th className="p-3">সোর্স ফাইল</th>
                  <th className="p-3">সাইজ / পৃষ্ঠা</th>
                  <th className="p-3">মোট লেসন</th>
                  <th className="p-3">স্ট্যাটাস</th>
                  <th className="p-3 text-right">অ্যাকশন</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-700/60">
                {ingestedDocs.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="p-4 text-center text-slate-500">
                      কোনো ইনজেস্টেড নথি পাওয়া যায়নি। ওপরের বাটনে ক্লিক করে ইনজেস্ট করুন।
                    </td>
                  </tr>
                ) : (
                  ingestedDocs.map((doc) => (
                    <tr key={doc.id} className="hover:bg-slate-750 transition">
                      <td className="p-3 font-semibold text-white">{doc.title}</td>
                      <td className="p-3 font-mono text-slate-400">{doc.source_file}</td>
                      <td className="p-3">{doc.file_size_mb} MB • {doc.total_pages} পৃ.</td>
                      <td className="p-3">
                        <span className="bg-emerald-950 border border-emerald-800 text-emerald-400 font-bold px-2 py-0.5 rounded">
                          {doc.total_lessons} টি লেসন
                        </span>
                      </td>
                      <td className="p-3"><span className="text-emerald-400">ইনডেক্সড</span></td>
                      <td className="p-3 text-right space-x-2">
                        <button
                          onClick={() => viewDocLessons(doc)}
                          className="bg-slate-900 hover:bg-slate-700 text-slate-200 px-2.5 py-1 rounded border border-slate-700 text-[11px] inline-flex items-center space-x-1"
                        >
                          <Eye className="w-3 h-3" />
                          <span>লেসন দেখুন</span>
                        </button>
                        {doc.source_file !== "Nasrin-book.pdf" && (
                          <button
                            onClick={() => deleteDoc(doc.id)}
                            className="bg-rose-950 hover:bg-rose-900 text-rose-300 border border-rose-800 px-2.5 py-1 rounded text-[11px] inline-flex items-center space-x-1"
                          >
                            <Trash2 className="w-3 h-3" />
                            <span>ডিলিট</span>
                          </button>
                        )}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </main>

      {/* Lessons Detail Modal */}
      {activeModalDoc && (
        <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-700 rounded-xl max-w-4xl w-full max-h-[85vh] flex flex-col shadow-2xl">
            <div className="p-4 border-b border-slate-800 flex items-center justify-between">
              <div>
                <h3 className="font-bold text-sm text-white">{activeModalDoc.title}</h3>
                <p className="text-xs text-slate-400">মোট লেসন: {modalLessons.length} টি</p>
              </div>
              <button
                onClick={() => setActiveModalDoc(null)}
                className="text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="p-5 overflow-y-auto space-y-4 text-xs flex-1">
              {loadingLessons ? (
                <div className="flex items-center justify-center py-10 space-x-2 text-slate-400">
                  <Loader2 className="w-5 h-5 animate-spin" />
                  <span>লেসনসমূহ লোড হচ্ছে...</span>
                </div>
              ) : modalLessons.length === 0 ? (
                <p className="text-slate-500 text-center py-10">কোনো লেসন পাওয়া যায়নি।</p>
              ) : (
                modalLessons.map((l, idx) => (
                  <div key={l.id} className="p-4 rounded-lg bg-slate-950/80 border border-slate-800 space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-emerald-400 text-sm">{idx + 1}. {l.lesson_title}</span>
                      <span className="text-[10px] bg-slate-800 text-slate-400 px-2 py-0.5 rounded">
                        {l.category} {l.page_start ? `• পৃ. ${l.page_start}-${l.page_end}` : ""}
                      </span>
                    </div>
                    <p className="text-slate-300 text-xs">{l.content_summary}</p>
                    {l.key_principles && l.key_principles.length > 0 && (
                      <div className="mt-2">
                        <span className="text-[11px] font-semibold text-slate-400">আইনি নীতিমালা (Key Rules):</span>
                        <ul className="list-disc list-inside space-y-1 text-slate-300 text-xs mt-1">
                          {l.key_principles.map((p: string, pIdx: number) => (
                            <li key={pIdx}>{p}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                    {l.sample_clauses && l.sample_clauses.length > 0 && (
                      <div className="mt-2 bg-slate-900 p-2.5 rounded border border-slate-800">
                        <span className="text-[11px] font-semibold text-amber-400">নমুনা ক্লজ বা ড্রাফট কাঠামো:</span>
                        <div className="text-[11px] font-mono text-slate-300 mt-1 space-y-1">
                          {l.sample_clauses.map((c: string, cIdx: number) => (
                            <div key={cIdx}>• {c}</div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}

      {/* Footer */}
      <footer className="bg-slate-950 border-t border-slate-800 py-3 text-center text-xs text-slate-500">
        বাংলাদেশ লিগ্যাল ইন্টেলিজেন্স অ্যাডমিন প্যানেল • Super Admin Mode Active
      </footer>
    </div>
  );
}

