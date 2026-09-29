"use client";

import React, { useEffect, useMemo, useRef, useState } from "react";
import { CheckCircle2, AlertTriangle, XCircle, HelpCircle, ShieldCheck, Eye } from "lucide-react";

const API_BASE = "/api/v1";

type Check = { ok: boolean; message_bn: string };
type Field = {
  field: string;
  title_bn: string;
  critical: boolean;
  value: string | null;
  status: "human_verified" | "machine_agreed" | "needs_review" | "illegible" | "not_found";
  confidence: number;
  alternatives: string[];
  verbatim: string[];
  page: number;
  bbox: number[] | null;
  checks: Check[];
  notes: string[];
  corrected?: boolean;
  previous_machine_value?: string | null;
};

const STATUS_META: Record<Field["status"], { label: string; cls: string }> = {
  human_verified: { label: "✔ যাচাইকৃত", cls: "bg-emerald-100 text-emerald-800 border-emerald-300" },
  machine_agreed: { label: "দুই পাঠ মিলেছে — যাচাই বাকি", cls: "bg-sky-50 text-sky-800 border-sky-200" },
  needs_review: { label: "⚠ যাচাই প্রয়োজন", cls: "bg-amber-50 text-amber-800 border-amber-300" },
  illegible: { label: "⚠ অপাঠ্য", cls: "bg-rose-50 text-rose-800 border-rose-300" },
  not_found: { label: "পাওয়া যায়নি", cls: "bg-slate-100 text-slate-600 border-slate-200" },
};

const GROUPS: Array<{ title: string; keys: string[] }> = [
  { title: "রেজিস্ট্রেশন তথ্য", keys: ["deed_type", "deed_number", "registration_date", "sub_registry_office", "district", "thana"] },
  { title: "পক্ষগণ", keys: ["seller_names", "seller_parentage", "seller_address", "buyer_names", "buyer_parentage", "buyer_address"] },
  { title: "তফসিল", keys: ["mouza", "jl_no", "khatian_cs", "khatian_sa", "khatian_rs", "khatian_bs", "dag_numbers", "land_class", "land_area", "land_area_words", "share"] },
  { title: "চৌহদ্দি", keys: ["boundary_north", "boundary_south", "boundary_east", "boundary_west"] },
  { title: "পণমূল্য ও স্বত্ব", keys: ["consideration_amount", "consideration_words", "stamp_value", "prior_deed", "prior_owner"] },
  { title: "সম্পাদন", keys: ["identifier", "deed_writer", "witnesses"] },
];

export default function DeedVerificationPanel({ deed, onUpdated }: { deed: any; onUpdated: (d: any) => void }) {
  const report = deed.reading_report || {};
  const fields: Record<string, Field> = report.fields || {};
  const summary = report.summary || {};
  const pages: string[] = deed.page_images?.length ? deed.page_images : [deed.original_file_path].filter(Boolean);

  const [engine, setEngine] = useState<any>(report.engine || null);
  const [activeKey, setActiveKey] = useState<string | null>(null);
  const [page, setPage] = useState(0);
  const [drafts, setDrafts] = useState<Record<string, string>>({});
  const [saving, setSaving] = useState<string | null>(null);
  const [filter, setFilter] = useState<"pending" | "all">("pending");
  const [showText, setShowText] = useState(false);
  const imgRef = useRef<HTMLImageElement>(null);
  const [natural, setNatural] = useState<{ w: number; h: number } | null>(null);

  useEffect(() => {
    fetch(`${API_BASE}/deeds/engine-status`).then((r) => (r.ok ? r.json() : null)).then((d) => d && setEngine(d)).catch(() => {});
  }, []);

  useEffect(() => {
    setDrafts({});
    setActiveKey(null);
  }, [deed.id]);

  const active = activeKey ? fields[activeKey] : null;
  useEffect(() => {
    if (active && typeof active.page === "number" && active.page < pages.length) setPage(active.page);
  }, [activeKey]); // eslint-disable-line react-hooks/exhaustive-deps

  const counts = summary.counts || {};
  const total = summary.total_fields || Object.keys(fields).length;
  const verified = counts.human_verified || 0;
  const criticalPending: string[] = summary.critical_pending || [];

  const verify = async (key: string, value: string | null) => {
    setSaving(key);
    try {
      const res = await fetch(`${API_BASE}/deeds/${deed.id}/verify-field`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ field_key: key, value, verified_by: "advocate_user" }),
      });
      if (!res.ok) throw new Error(await res.text());
      const updated = await res.json();
      onUpdated(updated);
      setDrafts((d) => {
        const n = { ...d };
        delete n[key];
        return n;
      });
      // Move to the next critical field that still needs a person
      const nextPending: string[] = updated.reading_report?.summary?.critical_pending || [];
      setActiveKey(nextPending.find((k) => k !== key) || null);
    } catch (e) {
      alert("সংরক্ষণ করা যায়নি: " + e);
    } finally {
      setSaving(null);
    }
  };

  const overlay = useMemo(() => {
    if (!active?.bbox || active.page !== page || !natural) return null;
    const [x0, y0, x1, y1] = active.bbox;
    return { left: `${(x0 / natural.w) * 100}%`, top: `${(y0 / natural.h) * 100}%`, width: `${((x1 - x0) / natural.w) * 100}%`, height: `${((y1 - y0) / natural.h) * 100}%` };
  }, [active, page, natural]);

  const visible = (k: string) => {
    const f = fields[k];
    if (!f) return false;
    return filter === "all" || f.status !== "human_verified";
  };

  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5 space-y-4">
      {/* Engine + verification summary */}
      <div className="flex flex-wrap items-start justify-between gap-3 border-b border-slate-100 pb-3">
        <div className="space-y-1 max-w-3xl">
          <h3 className="font-bold text-sm text-slate-900 flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-emerald-700" /> দলিলের প্রতিটি তথ্য যাচাই (Field-by-field Verification)
          </h3>
          <p className="text-xs text-slate-600">
            হাতে লেখা দলিল কোনো মেশিন ১০০% নির্ভুলভাবে পড়তে পারে না। তাই প্রতিটি তথ্য ছবির পাশে দেখিয়ে আপনাকে নিশ্চিত করতে বলা হচ্ছে। আপনি নিশ্চিত না করা পর্যন্ত কোনো তথ্য চূড়ান্ত নয়।
          </p>
          {engine && (
            <p className={`text-[11px] px-2 py-1 rounded border ${engine.mode === "dual_vision" ? "bg-emerald-50 border-emerald-200 text-emerald-900" : "bg-amber-50 border-amber-200 text-amber-900"}`}>
              {engine.message_bn}
            </p>
          )}
          {(report.errors || []).length > 0 && (
            <p className="text-[10px] text-rose-700">পাঠক ত্রুটি: {(report.errors as string[]).join(" | ")}</p>
          )}
        </div>
        <div className="text-right space-y-1">
          <div className={`text-xs font-bold px-3 py-1.5 rounded-lg border ${summary.fully_verified ? "bg-emerald-100 text-emerald-900 border-emerald-300" : "bg-amber-100 text-amber-900 border-amber-300"}`}>
            {summary.fully_verified ? "✔ সকল গুরুত্বপূর্ণ তথ্য যাচাইকৃত" : `যাচাই বাকি: ${criticalPending.length}টি গুরুত্বপূর্ণ তথ্য`}
          </div>
          <div className="text-[11px] text-slate-500">যাচাইকৃত {verified}/{total} · দুই পাঠ মিলেছে {counts.machine_agreed || 0} · যাচাই প্রয়োজন {counts.needs_review || 0} · অপাঠ্য {counts.illegible || 0}</div>
        </div>
      </div>

      {(report.findings || []).length > 0 && (
        <div className="bg-rose-50 border border-rose-200 rounded-lg p-3 text-xs text-rose-900 space-y-1">
          <div className="font-bold flex items-center gap-1"><AlertTriangle className="w-4 h-4" /> স্বয়ংক্রিয় হিসাব-নিকাশে অসঙ্গতি পাওয়া গেছে:</div>
          {(report.findings as any[]).map((f, i) => <div key={i}>• {f.message_bn}</div>)}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
        {/* Page viewer with highlighted region */}
        <div className="lg:col-span-5 space-y-2">
          <div className="flex items-center justify-between text-xs">
            <span className="font-semibold text-slate-700">মূল দলিল {pages.length > 1 ? `(পৃষ্ঠা ${page + 1}/${pages.length})` : ""}</span>
            {pages.length > 1 && (
              <div className="space-x-1">
                {pages.map((_, i) => (
                  <button key={i} onClick={() => setPage(i)} className={`px-2 py-0.5 rounded border ${i === page ? "bg-slate-900 text-white" : "bg-white"}`}>{i + 1}</button>
                ))}
              </div>
            )}
          </div>
          <div className="relative border border-slate-200 rounded-lg overflow-auto max-h-[720px] bg-slate-50">
            {pages[page] ? (
              <div className="relative">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img ref={imgRef} src={pages[page]} alt="deed page" className="w-full h-auto block"
                  onLoad={(e) => setNatural({ w: e.currentTarget.naturalWidth, h: e.currentTarget.naturalHeight })} />
                {overlay && <div className="absolute border-2 border-emerald-500 bg-emerald-400/20 rounded pointer-events-none" style={overlay} />}
              </div>
            ) : (
              <p className="p-6 text-xs text-slate-500">ছবি পাওয়া যায়নি</p>
            )}
          </div>
          {active && (
            <p className="text-[11px] text-slate-600">
              <Eye className="inline w-3.5 h-3.5 mr-1" />
              {active.bbox ? `সবুজ চিহ্নিত অংশে "${active.title_bn}" পড়া হয়েছে — ছবির সাথে মিলিয়ে দেখুন।` : `"${active.title_bn}"-এর অবস্থান চিহ্নিত করা যায়নি — পুরো দলিলে খুঁজে দেখুন।`}
            </p>
          )}
          <button onClick={() => setShowText((s) => !s)} className="text-xs text-blue-700 underline">
            {showText ? "পূর্ণ পাঠ লুকান" : "পূর্ণ দলিলের পাঠ (transcription) দেখুন"}
          </button>
          {showText && (
            <pre className="text-[11px] whitespace-pre-wrap bg-slate-50 border rounded p-2 max-h-72 overflow-auto">
              {report.transcription || "পাঠ পাওয়া যায়নি"}
              {report.transcription_source === "local_ocr" && "\n\n[সতর্কতা: এই পাঠ দুর্বল স্থানীয় OCR থেকে — ভুল থাকতে পারে]"}
            </pre>
          )}
        </div>

        {/* Field list */}
        <div className="lg:col-span-7 space-y-3 max-h-[800px] overflow-auto pr-1">
          <div className="flex items-center gap-2 text-xs">
            <button onClick={() => setFilter("pending")} className={`px-2.5 py-1 rounded border ${filter === "pending" ? "bg-slate-900 text-white" : ""}`}>যাচাই বাকি</button>
            <button onClick={() => setFilter("all")} className={`px-2.5 py-1 rounded border ${filter === "all" ? "bg-slate-900 text-white" : ""}`}>সব তথ্য</button>
          </div>
          {GROUPS.map((g) => {
            const keys = g.keys.filter(visible);
            if (!keys.length) return null;
            return (
              <div key={g.title}>
                <div className="text-[11px] font-bold text-slate-500 uppercase mb-1">{g.title}</div>
                <div className="space-y-2">
                  {keys.map((k) => {
                    const f = fields[k];
                    const meta = STATUS_META[f.status] || STATUS_META.needs_review;
                    const draft = drafts[k] ?? f.value ?? "";
                    const isActive = activeKey === k;
                    const failed = (f.checks || []).filter((c) => !c.ok);
                    const passed = (f.checks || []).filter((c) => c.ok);
                    return (
                      <div key={k} onClick={() => setActiveKey(k)}
                        className={`rounded-lg border p-2.5 text-xs cursor-pointer transition ${isActive ? "border-emerald-500 ring-2 ring-emerald-200" : "border-slate-200 hover:border-slate-300"}`}>
                        <div className="flex items-center justify-between gap-2">
                          <span className="font-semibold text-slate-800">
                            {f.title_bn} {f.critical && <span className="text-rose-600" title="গুরুত্বপূর্ণ তথ্য">*</span>}
                          </span>
                          <span className={`text-[10px] px-1.5 py-0.5 rounded border ${meta.cls}`}>{meta.label}{f.status !== "human_verified" && f.status !== "not_found" ? ` · ${f.confidence}%` : ""}</span>
                        </div>
                        <div className={`mt-1 text-sm ${f.value ? "text-slate-900" : "text-slate-400 italic"}`}>{f.value || "— পাওয়া যায়নি —"}</div>
                        {f.corrected && f.previous_machine_value && (
                          <div className="text-[10px] text-slate-500">মেশিনের পাঠ ছিল: <s>{f.previous_machine_value}</s></div>
                        )}
                        {(f.notes || []).map((n, i) => <div key={i} className="text-[10px] text-slate-500">• {n}</div>)}
                        {failed.map((c, i) => <div key={i} className="text-[10px] text-rose-700 flex items-center gap-1"><XCircle className="w-3 h-3" />{c.message_bn}</div>)}
                        {passed.map((c, i) => <div key={i} className="text-[10px] text-emerald-700 flex items-center gap-1"><CheckCircle2 className="w-3 h-3" />{c.message_bn}</div>)}

                        {isActive && (
                          <div className="mt-2 space-y-2" onClick={(e) => e.stopPropagation()}>
                            {(f.alternatives || []).length > 1 && (
                              <div className="flex flex-wrap gap-1 items-center">
                                <HelpCircle className="w-3.5 h-3.5 text-slate-400" />
                                <span className="text-[10px] text-slate-500">সম্ভাব্য পাঠ:</span>
                                {f.alternatives.map((a) => (
                                  <button key={a} onClick={() => setDrafts((d) => ({ ...d, [k]: a }))} className="text-[11px] px-2 py-0.5 rounded border bg-slate-50 hover:bg-slate-100">{a}</button>
                                ))}
                              </div>
                            )}
                            <input value={draft} onChange={(e) => setDrafts((d) => ({ ...d, [k]: e.target.value }))}
                              placeholder="দলিলে যা লেখা আছে হুবহু লিখুন" className="w-full border rounded px-2 py-1.5 text-sm" />
                            <div className="flex flex-wrap gap-2">
                              <button disabled={saving === k || !draft.trim()} onClick={() => verify(k, draft.trim())}
                                className="bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50 text-white px-3 py-1.5 rounded font-medium">
                                {draft.trim() === (f.value || "") ? "✓ সঠিক — নিশ্চিত করছি" : "সংশোধন করে নিশ্চিত করুন"}
                              </button>
                              <button disabled={saving === k} onClick={() => verify(k, null)}
                                className="bg-white border border-slate-300 hover:bg-slate-50 px-3 py-1.5 rounded">দলিলে এই তথ্য নেই</button>
                            </div>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            );
          })}
          {filter === "pending" && GROUPS.every((g) => !g.keys.some(visible)) && (
            <p className="text-sm text-emerald-800 font-medium">সব তথ্য যাচাই সম্পন্ন হয়েছে।</p>
          )}
        </div>
      </div>
    </div>
  );
}
