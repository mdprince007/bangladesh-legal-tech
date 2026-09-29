"use client";

import React, { useEffect, useRef, useState } from "react";
import { Mic, MicOff, Sparkles, CheckCircle2, AlertTriangle, HelpCircle, FileText } from "lucide-react";

const API_BASE = "/api/v1";

const MATTER_OPTIONS: Array<[string, string]> = [
  ["", "স্বয়ংক্রিয়ভাবে বুঝে নিন"],
  ["commercial_lease", "বাণিজ্যিক দোকান/অফিস ভাড়া"],
  ["residential_rent", "বাসা/ফ্ল্যাট ভাড়া"],
  ["demand_notice_ni_act", "চেক ডিজঅনার নোটিশ (১৩৮ ধারা)"],
  ["sale_agreement", "জমি/ফ্ল্যাট বিক্রয় বায়নাপত্র"],
  ["partnership_deed", "অংশীদারি চুক্তি"],
  ["loan_agreement", "হাওলাত / ঋণ চুক্তি"],
  ["employment_agreement", "চাকরির চুক্তি"],
  ["nda", "গোপনীয়তা চুক্তি (NDA)"],
  ["service_agreement", "সেবা চুক্তি"],
  ["custom", "অন্যান্য / কাস্টম চুক্তি"],
];

type Question = { field: string; label_bn: string; question_bn: string; why_bn: string; kind: string; critical: boolean; suggestion: any };

export default function ScenarioComposer({ onDraft }: { onDraft: (matterType: string, templateCode: string, facts: Record<string, any>) => Promise<void> | void }) {
  const [text, setText] = useState("");
  const [interim, setInterim] = useState("");
  const [listening, setListening] = useState(false);
  const [lang, setLang] = useState<"bn-BD" | "en-US">("bn-BD");
  const [speechSupported, setSpeechSupported] = useState(true);
  const [forcedType, setForcedType] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any | null>(null);
  const [facts, setFacts] = useState<Record<string, any>>({});
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [acceptedTerms, setAcceptedTerms] = useState<Record<string, boolean>>({});
  const recRef = useRef<any>(null);

  useEffect(() => {
    const SR = typeof window !== "undefined" ? (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition : null;
    setSpeechSupported(!!SR);
    return () => recRef.current?.stop?.();
  }, []);

  const toggleMic = () => {
    const SR = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SR) return;
    if (listening) {
      recRef.current?.stop();
      return;
    }
    const rec = new SR();
    rec.lang = lang;
    rec.continuous = true;
    rec.interimResults = true;
    rec.onresult = (e: any) => {
      let finalText = "";
      let interimText = "";
      for (let i = e.resultIndex; i < e.results.length; i++) {
        const t = e.results[i][0].transcript;
        if (e.results[i].isFinal) finalText += t;
        else interimText += t;
      }
      if (finalText) setText((prev) => (prev ? prev.trimEnd() + " " : "") + finalText.trim());
      setInterim(interimText);
    };
    rec.onerror = (e: any) => {
      if (e.error === "not-allowed") alert("মাইক্রোফোন ব্যবহারের অনুমতি দিন (ব্রাউজারের ঠিকানা বারের পাশে মাইক আইকন)।");
      setListening(false);
    };
    rec.onend = () => {
      setListening(false);
      setInterim("");
    };
    recRef.current = rec;
    rec.start();
    setListening(true);
  };

  const applyResult = (data: any) => {
    setResult(data);
    setFacts(data.extracted_facts || {});
    const acc: Record<string, boolean> = {};
    (data.suggested_terms || []).forEach((t: Question) => {
      if (t.suggestion !== null && t.suggestion !== undefined) acc[t.field] = true;
    });
    setAcceptedTerms(acc);
  };

  const analyze = async (matterType?: string) => {
    if (!text.trim()) return;
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/intake/analyze-scenario`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ scenario_text: text, matter_type: (matterType ?? forcedType) || null }),
      });
      if (!res.ok) throw new Error(await res.text());
      applyResult(await res.json());
      setAnswers({});
    } catch (e) {
      alert("বিশ্লেষণে ত্রুটি: " + e);
    } finally {
      setLoading(false);
    }
  };

  const mergedFacts = () => {
    const merged: Record<string, any> = { ...facts };
    Object.entries(answers).forEach(([k, v]) => {
      if (v && v.trim()) merged[k] = v.trim();
    });
    (result?.suggested_terms || []).forEach((t: Question) => {
      if (acceptedTerms[t.field] && (merged[t.field] === undefined || merged[t.field] === "")) merged[t.field] = t.suggestion;
    });
    return merged;
  };

  const recheck = async () => {
    if (!result) return;
    const merged = mergedFacts();
    const res = await fetch(`${API_BASE}/intake/scenario-recheck`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ matter_type: result.matter_type, facts: merged }),
    });
    if (res.ok) {
      const data = await res.json();
      applyResult({ ...data, evidence: result.evidence, unclear: result.unclear, extraction_method: result.extraction_method });
      setFacts(merged);
      setAnswers({});
    }
  };

  const draft = async () => {
    if (!result) return;
    const merged = mergedFacts();
    const criticalLeft = (result.questions || []).filter((q: Question) => q.critical && !(answers[q.field] || "").trim());
    if (criticalLeft.length && !confirm(`${criticalLeft.length}টি অত্যাবশ্যক তথ্য এখনো দেওয়া হয়নি। খসড়ায় সেগুলো '……' ফাঁকা থাকবে। তবুও খসড়া তৈরি করবেন?`)) return;
    await onDraft(result.matter_type, result.template_code, merged);
  };

  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5 space-y-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="font-bold text-sm text-slate-900 flex items-center gap-2"><Sparkles className="w-4 h-4 text-emerald-600" /> পুরো ঘটনা একবারে বলুন বা লিখুন</h2>
          <p className="text-xs text-slate-500">বাংলা বা ইংরেজিতে পুরো পরিস্থিতি লিখুন অথবা মাইকে বলুন। সিস্টেম বুঝে নেবে কোন দলিল লাগবে, কোন তথ্য পাওয়া গেছে এবং বইয়ের নিয়ম অনুযায়ী কী কী তথ্য এখনো দরকার।</p>
        </div>
        <div className="flex items-center gap-2 text-xs">
          <select value={forcedType} onChange={(e) => setForcedType(e.target.value)} className="border rounded-lg px-2 py-1.5 bg-white">
            {MATTER_OPTIONS.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
          </select>
        </div>
      </div>

      <div className="relative">
        <textarea value={text} onChange={(e) => setText(e.target.value)} rows={5}
          placeholder="যেমন: আমি মিরপুর ১০-এ আমার দোকানটি (দোকান নং ১২, বাড়ি নং ৫, রোড ৩) ৩ বছরের জন্য জনাব রহিম উদ্দিনের কাছে ভাড়া দিতে চাই। মাসিক ভাড়া ৫০ হাজার টাকা, অগ্রিম ৩ লাখ টাকা। তিনি ফার্মেসি চালাবেন। ১ জানুয়ারি ২০২৭ থেকে শুরু…"
          className="w-full border border-slate-300 rounded-lg p-3 text-sm leading-relaxed focus:ring-2 focus:ring-emerald-500 outline-none" />
        {interim && <p className="text-xs text-slate-400 italic mt-1">শুনছি: {interim}</p>}
      </div>

      <div className="flex flex-wrap items-center gap-2">
        {speechSupported ? (
          <>
            <button onClick={toggleMic} className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-semibold text-white ${listening ? "bg-rose-600 animate-pulse" : "bg-slate-800 hover:bg-slate-900"}`}>
              {listening ? <MicOff className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
              {listening ? "থামান" : "মাইকে বলুন"}
            </button>
            <select value={lang} onChange={(e) => setLang(e.target.value as any)} disabled={listening} className="text-xs border rounded-lg px-2 py-2 bg-white">
              <option value="bn-BD">বাংলা</option>
              <option value="en-US">English</option>
            </select>
          </>
        ) : (
          <span className="text-[11px] text-amber-700">ভয়েস ইনপুটের জন্য Chrome বা Edge ব্রাউজার ব্যবহার করুন।</span>
        )}
        <button onClick={() => analyze()} disabled={loading || !text.trim()} className="bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50 text-white text-xs font-semibold px-4 py-2 rounded-lg">
          {loading ? "বিশ্লেষণ চলছে…" : "বিশ্লেষণ করুন"}
        </button>
      </div>

      {result && (
        <div className="space-y-4 border-t border-slate-100 pt-4">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div>
              <div className="text-sm font-bold text-slate-900">{result.matter_title_bn} <span className="text-slate-500 font-normal">({result.matter_title_en})</span></div>
              <div className="text-[11px] text-slate-500">বিশ্লেষণ পদ্ধতি: {result.extraction_method === "language_model" ? "ভাষা মডেল (উন্নত)" : result.extraction_method === "rules" ? "নিয়মভিত্তিক (সীমিত)" : "আপনার দেওয়া উত্তর"}</div>
            </div>
            <div className="w-56">
              <div className="flex justify-between text-[11px] text-slate-600"><span>তথ্যের পূর্ণতা</span><span>{result.completeness_percentage}%</span></div>
              <div className="h-2 bg-slate-100 rounded"><div className={`h-2 rounded ${result.is_ready_for_drafting ? "bg-emerald-500" : "bg-amber-500"}`} style={{ width: `${result.completeness_percentage}%` }} /></div>
            </div>
          </div>

          <ul className="text-xs text-slate-700 space-y-1">
            {(result.senior_counsel_notes_bn || []).map((n: string, i: number) => <li key={i}>• {n}</li>)}
          </ul>
          {(result.unclear || []).length > 0 && (
            <div className="bg-amber-50 border border-amber-200 rounded-lg p-2.5 text-xs text-amber-900">
              <div className="font-semibold flex items-center gap-1"><AlertTriangle className="w-3.5 h-3.5" /> অস্পষ্ট বা পরস্পরবিরোধী:</div>
              {result.unclear.map((u: string, i: number) => <div key={i}>• {u}</div>)}
            </div>
          )}

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <div>
              <h3 className="text-xs font-bold text-slate-700 mb-2 flex items-center gap-1"><CheckCircle2 className="w-4 h-4 text-emerald-600" /> আপনার বর্ণনা থেকে পাওয়া তথ্য (সংশোধন করা যাবে)</h3>
              {Object.keys(facts).length === 0 && <p className="text-xs text-slate-500">কোনো নির্দিষ্ট তথ্য পাওয়া যায়নি — ডানের প্রশ্নগুলোর উত্তর দিন।</p>}
              <div className="space-y-2">
                {Object.entries(facts).map(([k, v]) => (
                  <div key={k} className="text-xs">
                    <label className="text-slate-500 block">{result.field_labels?.[k] || k}</label>
                    <input value={String(v ?? "")} onChange={(e) => setFacts((f) => ({ ...f, [k]: e.target.value }))} className="w-full border rounded px-2 py-1" />
                    {result.evidence?.[k] && <span className="text-[10px] text-slate-400">আপনার কথা: “{result.evidence[k]}”</span>}
                  </div>
                ))}
              </div>
            </div>

            <div>
              <h3 className="text-xs font-bold text-slate-700 mb-2 flex items-center gap-1"><HelpCircle className="w-4 h-4 text-amber-600" /> যে তথ্য এখনো দরকার ({(result.questions || []).length}টি)</h3>
              <div className="space-y-2 max-h-[420px] overflow-auto pr-1">
                {(result.questions || []).map((q: Question) => (
                  <div key={q.field} className={`rounded-lg border p-2 text-xs ${q.critical ? "border-amber-300 bg-amber-50/40" : "border-slate-200"}`}>
                    <div className="font-semibold text-slate-800">{q.question_bn} {q.critical && <span className="text-rose-600">*</span>}</div>
                    <div className="text-[10px] text-slate-500 mb-1">কেন দরকার: {q.why_bn}</div>
                    <input value={answers[q.field] || ""} onChange={(e) => setAnswers((a) => ({ ...a, [q.field]: e.target.value }))} className="w-full border rounded px-2 py-1" placeholder="উত্তর লিখুন" />
                  </div>
                ))}
              </div>
            </div>
          </div>

          {(result.suggested_terms || []).length > 0 && (
            <div>
              <h3 className="text-xs font-bold text-slate-700 mb-1">বইয়ের প্রস্তাবিত শর্ত (আপনার সম্মতিতেই যুক্ত হবে)</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                {result.suggested_terms.map((t: Question) => (
                  <div key={t.field} className="border rounded-lg p-2 text-xs">
                    <div className="font-semibold text-slate-800">{t.label_bn}</div>
                    <div className="text-[10px] text-slate-500">{t.why_bn}</div>
                    {t.suggestion !== null && t.suggestion !== undefined && (
                      <label className="flex items-center gap-1.5 mt-1">
                        <input type="checkbox" checked={!!acceptedTerms[t.field]} onChange={(e) => setAcceptedTerms((a) => ({ ...a, [t.field]: e.target.checked }))} />
                        প্রস্তাব গ্রহণ: <strong>{String(t.suggestion)}</strong>
                      </label>
                    )}
                    <input value={answers[t.field] || ""} onChange={(e) => setAnswers((a) => ({ ...a, [t.field]: e.target.value }))} className="w-full border rounded px-2 py-1 mt-1" placeholder="নিজের মতো লিখতে চাইলে" />
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="flex flex-wrap gap-2">
            <button onClick={recheck} className="border border-slate-300 hover:bg-slate-50 text-xs font-semibold px-4 py-2 rounded-lg">উত্তরগুলো যাচাই করুন</button>
            <button onClick={draft} className="bg-slate-900 hover:bg-slate-800 text-white text-xs font-semibold px-4 py-2 rounded-lg flex items-center gap-1.5"><FileText className="w-4 h-4" /> বইয়ের ফরম্যাটে খসড়া তৈরি করুন</button>
          </div>
        </div>
      )}
    </div>
  );
}
