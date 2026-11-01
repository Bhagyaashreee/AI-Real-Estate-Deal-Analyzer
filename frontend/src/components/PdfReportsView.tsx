"use client";

import React, { useState, useEffect } from "react";
import {
  FileText,
  Download,
  Eye,
  Sparkles,
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
  Printer,
  ExternalLink,
  ShieldAlert,
  Building2,
  TrendingUp,
  Sliders,
  Layers,
  ChevronDown,
  ChevronUp,
  FileCheck,
  Info,
} from "lucide-react";
import { PropertyDeal } from "./DealsTable";

interface PdfReportsViewProps {
  apiBase: string;
}

export default function PdfReportsView({ apiBase }: PdfReportsViewProps) {
  const [properties, setProperties] = useState<PropertyDeal[]>([]);
  const [selectedPropertyId, setSelectedPropertyId] = useState<number | null>(null);
  const [loadingProps, setLoadingProps] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [generationStep, setGenerationStep] = useState("");
  const [pdfUrl, setPdfUrl] = useState<string | null>(null);
  const [reportMetadata, setReportMetadata] = useState<any>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Configuration options
  const [includeAi, setIncludeAi] = useState(true);
  const [includeFinancials, setIncludeFinancials] = useState(true);
  const [includeRisk, setIncludeRisk] = useState(true);
  const [includeBenchmarks, setIncludeBenchmarks] = useState(true);
  const [includeScenarios, setIncludeScenarios] = useState(true);

  // Advanced underwriting parameters
  const [showAdvancedParams, setShowAdvancedParams] = useState(false);
  const [downPaymentPct, setDownPaymentPct] = useState(20.0);
  const [interestRatePct, setInterestRatePct] = useState(8.5);
  const [tenureYears, setTenureYears] = useState(20);
  const [vacancyRatePct, setVacancyRatePct] = useState(5.0);
  const [stampDutyPct, setStampDutyPct] = useState(6.0);

  // Ollama health status
  const [ollamaOnline, setOllamaOnline] = useState<boolean | null>(null);

  // 1. Fetch properties & Ollama status on mount
  useEffect(() => {
    async function init() {
      setLoadingProps(true);
      try {
        // Fetch properties list
        const res = await fetch(`${apiBase}/api/v1/properties?page=1&page_size=50`);
        if (res.ok) {
          const data = await res.json();
          if (data.items && data.items.length > 0) {
            setProperties(data.items);
            setSelectedPropertyId(data.items[0].id);
          }
        }

        // Check AI status
        const aiRes = await fetch(`${apiBase}/api/v1/ai/status`);
        if (aiRes.ok) {
          const aiData = await aiRes.json();
          setOllamaOnline(aiData.ollama_reachable);
        } else {
          setOllamaOnline(false);
        }
      } catch {
        setOllamaOnline(false);
      } finally {
        setLoadingProps(false);
      }
    }
    init();
  }, [apiBase]);

  const selectedProperty = properties.find((p) => p.id === selectedPropertyId) || properties[0];

  // 2. Generate or Refresh Report
  const handleGenerateReport = async () => {
    if (!selectedPropertyId) return;

    setGenerating(true);
    setErrorMsg(null);
    setPdfUrl(null);
    setReportMetadata(null);

    try {
      setGenerationStep("Validating deterministic financial models...");
      await new Promise((r) => setTimeout(r, 400));

      setGenerationStep("Computing 5-category risk breakdown & stress matrices...");
      await new Promise((r) => setTimeout(r, 400));

      setGenerationStep("Rendering headless Matplotlib scenario comparison chart...");
      await new Promise((r) => setTimeout(r, 400));

      setGenerationStep("Compiling ReportLab Platypus 10-page A4 document...");

      const payload = {
        include_ai: includeAi,
        down_payment_pct: downPaymentPct,
        annual_interest_rate_pct: interestRatePct,
        tenure_years: tenureYears,
        vacancy_rate_pct: vacancyRatePct,
        custom_stamp_duty_pct: stampDutyPct,
        return_pdf_direct: false,
      };

      const res = await fetch(`${apiBase}/api/v1/reports/${selectedPropertyId}/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        throw new Error(`Report generation failed with status ${res.status}`);
      }

      const meta = await res.json();
      setReportMetadata(meta);

      // Direct stream URL for inline preview
      const previewUrl = `${apiBase}/api/v1/reports/${selectedPropertyId}/pdf?t=${Date.now()}`;
      setPdfUrl(previewUrl);
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to generate PDF report.");
    } finally {
      setGenerating(false);
      setGenerationStep("");
    }
  };

  const directDownloadUrl = selectedPropertyId ? `${apiBase}/api/v1/reports/${selectedPropertyId}/pdf` : "#";

  return (
    <div className="space-y-6">
      {/* Top Banner & Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between pb-4 border-b border-slate-800/60 gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
              <FileText className="w-5 h-5 text-indigo-400" />
              <span>Investment Report Studio</span>
            </h1>
            <span className="text-xs px-2 py-0.5 rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 font-medium">
              Phase 6 • ReportLab Engine
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Generate publication-ready, 10-page institutional investment memoranda with deterministic formulas, stress charts, and local AI intelligence.
          </p>
        </div>

        {/* Status Indicators */}
        <div className="flex items-center gap-2.5">
          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-xs">
            <span className="text-slate-400">Local AI Engine:</span>
            {ollamaOnline === true ? (
              <span className="text-emerald-400 font-medium flex items-center gap-1">
                <CheckCircle2 className="w-3.5 h-3.5" /> llama3.2:3b Online
              </span>
            ) : (
              <span className="text-amber-400 font-medium flex items-center gap-1">
                <Info className="w-3.5 h-3.5" /> Deterministic Mode
              </span>
            )}
          </div>

          <a
            href={directDownloadUrl}
            target="_blank"
            rel="noopener noreferrer"
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-colors ${
              selectedPropertyId
                ? "bg-emerald-600 hover:bg-emerald-500 text-white shadow-sm shadow-emerald-600/20"
                : "bg-slate-800 text-slate-500 cursor-not-allowed"
            }`}
          >
            <Download className="w-3.5 h-3.5" />
            <span>Quick PDF</span>
          </a>
        </div>
      </div>

      {/* Property Selector Strip */}
      <div className="rounded-xl bg-slate-900/80 border border-slate-800 p-4 space-y-3">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <label className="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
            <Building2 className="w-3.5 h-3.5 text-cyan-400" />
            <span>Select Target Subject Property</span>
          </label>
          <span className="text-[11px] text-slate-500">
            {properties.length} listings available in local SQLite database
          </span>
        </div>

        {loadingProps ? (
          <div className="h-10 bg-slate-800/50 rounded-lg animate-pulse" />
        ) : (
          <select
            value={selectedPropertyId || ""}
            onChange={(e) => {
              setSelectedPropertyId(Number(e.target.value));
              setPdfUrl(null);
              setReportMetadata(null);
            }}
            className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3.5 py-2.5 text-xs text-white focus:outline-none focus:border-indigo-500 transition-colors"
          >
            {properties.map((p) => (
              <option key={p.id} value={p.id}>
                {p.title} — {p.locality}, {p.city} ({p.price_formatted} • {p.gross_rental_yield_pct}% Gross Yield)
                {p.is_demo ? " [DEMO]" : ""}
              </option>
            ))}
          </select>
        )}

        {/* Selected Property Quick Glance */}
        {selectedProperty && (
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 pt-2 border-t border-slate-800/60 text-xs">
            <div className="p-2 rounded bg-slate-950/60 border border-slate-800/80">
              <span className="text-[10px] text-slate-500 block">Purchase Price</span>
              <span className="text-slate-200 font-bold">{selectedProperty.price_formatted}</span>
            </div>
            <div className="p-2 rounded bg-slate-950/60 border border-slate-800/80">
              <span className="text-[10px] text-slate-500 block">Expected Rent</span>
              <span className="text-slate-200 font-bold">{selectedProperty.rent_formatted}</span>
            </div>
            <div className="p-2 rounded bg-slate-950/60 border border-slate-800/80">
              <span className="text-[10px] text-slate-500 block">Gross Yield</span>
              <span className="text-emerald-400 font-bold">{selectedProperty.gross_rental_yield_pct}%</span>
            </div>
            <div className="p-2 rounded bg-slate-950/60 border border-slate-800/80">
              <span className="text-[10px] text-slate-500 block">Data Provenance</span>
              <span className="text-indigo-400 font-medium">
                {selectedProperty.is_demo ? "Simulated Demo" : selectedProperty.listing_source || "User Listing"}
              </span>
            </div>
          </div>
        )}
      </div>

      {/* Main Workspace: 2-Column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Column: Configuration & Controls (4 cols) */}
        <div className="lg:col-span-4 space-y-4">
          <div className="rounded-xl bg-slate-900/80 border border-slate-800 p-4 space-y-4">
            <div className="flex items-center justify-between pb-2 border-b border-slate-800/80">
              <h2 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-1.5">
                <Sliders className="w-3.5 h-3.5 text-indigo-400" />
                <span>Report Sections</span>
              </h2>
              <span className="text-[10px] font-bold text-indigo-400 bg-indigo-500/10 px-2 py-0.5 rounded">
                10 Pages A4
              </span>
            </div>

            {/* Section Toggles */}
            <div className="space-y-2.5 text-xs text-slate-300">
              <label className="flex items-center justify-between p-2 rounded-lg bg-slate-950/50 border border-slate-800/80 hover:border-slate-700 cursor-pointer transition-colors">
                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={includeFinancials}
                    onChange={(e) => setIncludeFinancials(e.target.checked)}
                    className="rounded border-slate-700 text-indigo-500 focus:ring-0"
                  />
                  <span>Financial Returns & NOI</span>
                </div>
                <span className="text-[10px] text-slate-500">Page 4</span>
              </label>

              <label className="flex items-center justify-between p-2 rounded-lg bg-slate-950/50 border border-slate-800/80 hover:border-slate-700 cursor-pointer transition-colors">
                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={includeRisk}
                    onChange={(e) => setIncludeRisk(e.target.checked)}
                    className="rounded border-slate-700 text-indigo-500 focus:ring-0"
                  />
                  <span>5-Category Risk Engine</span>
                </div>
                <span className="text-[10px] text-slate-500">Page 6</span>
              </label>

              <label className="flex items-center justify-between p-2 rounded-lg bg-slate-950/50 border border-slate-800/80 hover:border-slate-700 cursor-pointer transition-colors">
                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={includeBenchmarks}
                    onChange={(e) => setIncludeBenchmarks(e.target.checked)}
                    className="rounded border-slate-700 text-indigo-500 focus:ring-0"
                  />
                  <span>Micro-Market Benchmarks</span>
                </div>
                <span className="text-[10px] text-slate-500">Page 7</span>
              </label>

              <label className="flex items-center justify-between p-2 rounded-lg bg-slate-950/50 border border-slate-800/80 hover:border-slate-700 cursor-pointer transition-colors">
                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={includeScenarios}
                    onChange={(e) => setIncludeScenarios(e.target.checked)}
                    className="rounded border-slate-700 text-indigo-500 focus:ring-0"
                  />
                  <span>What-If Stress & Chart</span>
                </div>
                <span className="text-[10px] text-slate-500">Page 8</span>
              </label>

              <label className="flex items-center justify-between p-2 rounded-lg bg-slate-950/50 border border-slate-800/80 hover:border-slate-700 cursor-pointer transition-colors">
                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={includeAi}
                    onChange={(e) => setIncludeAi(e.target.checked)}
                    className="rounded border-slate-700 text-indigo-500 focus:ring-0"
                  />
                  <span>AI Due-Diligence Roadmap</span>
                </div>
                <span className="text-[10px] text-slate-500">Page 9</span>
              </label>
            </div>

            {/* Advanced Underwriting Overrides Accordion */}
            <div className="pt-2 border-t border-slate-800/80">
              <button
                type="button"
                onClick={() => setShowAdvancedParams(!showAdvancedParams)}
                className="w-full flex items-center justify-between text-xs font-semibold text-slate-400 hover:text-slate-200 transition-colors py-1"
              >
                <span className="flex items-center gap-1.5">
                  <Sliders className="w-3 h-3 text-cyan-400" />
                  <span>Custom Underwriting Inputs</span>
                </span>
                {showAdvancedParams ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
              </button>

              {showAdvancedParams && (
                <div className="mt-3 space-y-3 p-3 rounded-lg bg-slate-950/70 border border-slate-800/80 text-xs text-slate-300">
                  <div className="space-y-1">
                    <div className="flex justify-between">
                      <span className="text-slate-400">Down Payment</span>
                      <span className="font-mono text-white">{downPaymentPct}%</span>
                    </div>
                    <input
                      type="range"
                      min="10"
                      max="50"
                      step="5"
                      value={downPaymentPct}
                      onChange={(e) => setDownPaymentPct(Number(e.target.value))}
                      className="w-full accent-indigo-500"
                    />
                  </div>

                  <div className="space-y-1">
                    <div className="flex justify-between">
                      <span className="text-slate-400">Interest Rate</span>
                      <span className="font-mono text-white">{interestRatePct}%</span>
                    </div>
                    <input
                      type="range"
                      min="6.5"
                      max="12.0"
                      step="0.25"
                      value={interestRatePct}
                      onChange={(e) => setInterestRatePct(Number(e.target.value))}
                      className="w-full accent-indigo-500"
                    />
                  </div>

                  <div className="space-y-1">
                    <div className="flex justify-between">
                      <span className="text-slate-400">Tenure</span>
                      <span className="font-mono text-white">{tenureYears} Years</span>
                    </div>
                    <input
                      type="range"
                      min="5"
                      max="30"
                      step="5"
                      value={tenureYears}
                      onChange={(e) => setTenureYears(Number(e.target.value))}
                      className="w-full accent-indigo-500"
                    />
                  </div>

                  <div className="space-y-1">
                    <div className="flex justify-between">
                      <span className="text-slate-400">Vacancy Allowance</span>
                      <span className="font-mono text-white">{vacancyRatePct}%</span>
                    </div>
                    <input
                      type="range"
                      min="0"
                      max="20"
                      step="1"
                      value={vacancyRatePct}
                      onChange={(e) => setVacancyRatePct(Number(e.target.value))}
                      className="w-full accent-indigo-500"
                    />
                  </div>
                </div>
              )}
            </div>

            {/* Action Button */}
            <button
              onClick={handleGenerateReport}
              disabled={generating || !selectedPropertyId}
              className={`w-full py-2.5 rounded-lg text-xs font-bold transition-all duration-150 flex items-center justify-center gap-2 ${
                generating || !selectedPropertyId
                  ? "bg-indigo-900/40 text-indigo-400/50 cursor-not-allowed border border-indigo-800/30"
                  : "bg-indigo-600 hover:bg-indigo-500 text-white shadow-md shadow-indigo-600/25 border border-indigo-500/30 active:scale-[0.99]"
              }`}
            >
              {generating ? (
                <>
                  <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                  <span>Synthesizing Document...</span>
                </>
              ) : (
                <>
                  <FileText className="w-3.5 h-3.5" />
                  <span>Generate 10-Page PDF Report</span>
                </>
              )}
            </button>

            {/* Live Progress Bar when generating */}
            {generating && (
              <div className="p-3 rounded-lg bg-indigo-950/40 border border-indigo-800/50 space-y-2">
                <div className="flex items-center justify-between text-[11px] text-indigo-300">
                  <span className="flex items-center gap-1.5 font-medium">
                    <RefreshCw className="w-3 h-3 animate-spin text-indigo-400" />
                    <span>ReportLab Platypus Build</span>
                  </span>
                  <span className="font-mono text-[10px]">Processing</span>
                </div>
                <p className="text-[11px] text-slate-300 font-mono animate-pulse">{generationStep}</p>
                <div className="w-full h-1.5 bg-slate-800 rounded-full overflow-hidden">
                  <div className="h-full bg-gradient-to-r from-indigo-500 to-teal-400 rounded-full animate-[pulse_1s_infinite]" style={{ width: "85%" }} />
                </div>
              </div>
            )}

            {errorMsg && (
              <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-start gap-2">
                <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
                <span>{errorMsg}</span>
              </div>
            )}
          </div>

          {/* Document Architecture Blueprint Card */}
          <div className="rounded-xl bg-slate-900/60 border border-slate-800 p-4 space-y-3">
            <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
              <Layers className="w-3.5 h-3.5 text-cyan-400" />
              <span>Standard Report Blueprint</span>
            </h3>

            <div className="space-y-1.5 text-[11px] text-slate-400">
              <div className="flex items-center justify-between py-1 border-b border-slate-800/60">
                <span>Page 1: Cover & Tri-Score Summary</span>
                <span className="text-emerald-400 font-mono">Cover</span>
              </div>
              <div className="flex items-center justify-between py-1 border-b border-slate-800/60">
                <span>Page 2: Executive Investment Summary</span>
                <span className="text-slate-300 font-mono">Verdict</span>
              </div>
              <div className="flex items-center justify-between py-1 border-b border-slate-800/60">
                <span>Page 3: Property Specs & Attributes</span>
                <span className="text-slate-300 font-mono">Catalog</span>
              </div>
              <div className="flex items-center justify-between py-1 border-b border-slate-800/60">
                <span>Page 4: Financial Modeling & NOI</span>
                <span className="text-indigo-400 font-mono">Returns</span>
              </div>
              <div className="flex items-center justify-between py-1 border-b border-slate-800/60">
                <span>Page 5: Loan Amortization Schedule</span>
                <span className="text-slate-300 font-mono">Debt</span>
              </div>
              <div className="flex items-center justify-between py-1 border-b border-slate-800/60">
                <span>Page 6: 5-Category Risk Decomposition</span>
                <span className="text-rose-400 font-mono">Risk</span>
              </div>
              <div className="flex items-center justify-between py-1 border-b border-slate-800/60">
                <span>Page 7: Micro-Market Benchmarks</span>
                <span className="text-cyan-400 font-mono">Comp</span>
              </div>
              <div className="flex items-center justify-between py-1 border-b border-slate-800/60">
                <span>Page 8: What-If Stress Bar Chart</span>
                <span className="text-amber-400 font-mono">Chart</span>
              </div>
              <div className="flex items-center justify-between py-1 border-b border-slate-800/60">
                <span>Page 9: AI Due-Diligence Roadmap</span>
                <span className="text-emerald-400 font-mono">AI/Expert</span>
              </div>
              <div className="flex items-center justify-between py-1">
                <span>Page 10: Formulas & Disclaimers</span>
                <span className="text-slate-400 font-mono">Legal</span>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column: PDF Preview Canvas & Inspection (8 cols) */}
        <div className="lg:col-span-8 space-y-4">
          <div className="rounded-xl bg-slate-900/80 border border-slate-800 p-4 space-y-3">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-3 border-b border-slate-800/80 gap-3">
              <div className="flex items-center gap-2">
                <FileCheck className="w-4 h-4 text-emerald-400" />
                <h2 className="text-sm font-bold text-white">Live PDF Report Preview</h2>
              </div>

              {/* Action Toolbar */}
              <div className="flex items-center gap-2">
                {pdfUrl ? (
                  <>
                    <a
                      href={pdfUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="px-2.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium transition-colors flex items-center gap-1"
                    >
                      <ExternalLink className="w-3.5 h-3.5" />
                      <span>Full Window</span>
                    </a>
                    <a
                      href={directDownloadUrl}
                      download
                      className="px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold transition-colors flex items-center gap-1.5 shadow-sm shadow-emerald-600/20"
                    >
                      <Download className="w-3.5 h-3.5" />
                      <span>Download PDF</span>
                    </a>
                  </>
                ) : (
                  <button
                    onClick={handleGenerateReport}
                    className="px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold transition-colors flex items-center gap-1.5"
                  >
                    <Eye className="w-3.5 h-3.5" />
                    <span>Load Preview</span>
                  </button>
                )}
              </div>
            </div>

            {/* PDF Viewer Frame */}
            <div className="w-full bg-slate-950 rounded-lg border border-slate-800/80 overflow-hidden min-h-[640px] flex flex-col justify-center items-center relative">
              {pdfUrl ? (
                <iframe
                  src={pdfUrl}
                  title="PDF Investment Report Preview"
                  className="w-full h-[680px] rounded-lg border-0"
                />
              ) : generating ? (
                <div className="text-center p-8 space-y-3">
                  <RefreshCw className="w-8 h-8 text-indigo-400 animate-spin mx-auto" />
                  <p className="text-sm font-semibold text-white">Synthesizing 10-Page Investment Report</p>
                  <p className="text-xs text-slate-400 max-w-sm">{generationStep || "Compiling ReportLab flowables..."}</p>
                </div>
              ) : (
                <div className="text-center p-12 space-y-4 max-w-md">
                  <div className="w-14 h-14 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center mx-auto text-indigo-400">
                    <FileText className="w-7 h-7" />
                  </div>
                  <div>
                    <h3 className="text-sm font-bold text-white">No PDF Report Loaded</h3>
                    <p className="text-xs text-slate-400 mt-1">
                      Click the button below to compile and preview the institutional 10-page investment report for{" "}
                      <span className="text-slate-200 font-semibold">{selectedProperty?.title || "the selected listing"}</span>.
                    </p>
                  </div>
                  <button
                    onClick={handleGenerateReport}
                    className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold transition-all shadow-md shadow-indigo-600/20 inline-flex items-center gap-1.5"
                  >
                    <FileText className="w-3.5 h-3.5" />
                    <span>Compile 10-Page Report</span>
                  </button>
                </div>
              )}
            </div>

            {/* Report Metadata Footer Strip */}
            {reportMetadata && (
              <div className="p-3 rounded-lg bg-slate-950/70 border border-slate-800 flex flex-wrap items-center justify-between gap-3 text-xs text-slate-400">
                <div className="flex items-center gap-3">
                  <span>
                    File: <strong className="text-slate-200">{reportMetadata.file_name}</strong>
                  </span>
                  <span>•</span>
                  <span>
                    Size: <strong className="text-slate-200">{(reportMetadata.file_size_bytes / 1024).toFixed(1)} KB</strong>
                  </span>
                  <span>•</span>
                  <span>
                    Pages: <strong className="text-emerald-400">{reportMetadata.page_count} Pages</strong>
                  </span>
                </div>
                <div className="text-[11px] text-slate-500">
                  Certified deterministic layout • Zero cloud leakage
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

