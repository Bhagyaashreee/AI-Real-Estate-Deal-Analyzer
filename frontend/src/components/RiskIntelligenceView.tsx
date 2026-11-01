"use client";

import React, { useState, useEffect } from "react";
import {
  ShieldAlert,
  ShieldCheck,
  AlertTriangle,
  Sliders,
  Scale,
  Sparkles,
  RefreshCw,
  TrendingDown,
  TrendingUp,
  CheckCircle2,
  Info,
  Landmark,
  Building2,
  Percent,
  IndianRupee,
  Layers,
  ChevronDown,
  ChevronUp,
  Search,
  Upload,
  Calendar,
  FileSpreadsheet,
} from "lucide-react";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  Cell,
} from "recharts";
import { PropertyDeal } from "./DealsTable";

interface RiskIntelligenceViewProps {
  apiBase: string;
}

export default function RiskIntelligenceView({ apiBase }: RiskIntelligenceViewProps) {
  const [properties, setProperties] = useState<PropertyDeal[]>([]);
  const [selectedPropertyId, setSelectedPropertyId] = useState<number | null>(null);
  const [activeTab, setActiveTab] = useState<"overview" | "simulator" | "benchmarks" | "ai-risk">("overview");

  // Loading states
  const [loadingProps, setLoadingProps] = useState(true);
  const [loadingRisk, setLoadingRisk] = useState(false);
  const [loadingSim, setLoadingSim] = useState(false);
  const [loadingBench, setLoadingBench] = useState(false);

  // Risk Data
  const [riskData, setRiskData] = useState<any>(null);

  // Simulator Data
  const [simData, setSimData] = useState<any>(null);
  const [simPrice, setSimPrice] = useState<number | "">("");
  const [simRent, setSimRent] = useState<number | "">("");
  const [simVacancy, setSimVacancy] = useState(5.0);
  const [simInterest, setSimInterest] = useState(8.5);
  const [simDownPayment, setSimDownPayment] = useState(20.0);
  const [simTenure, setSimTenure] = useState(20);

  // Benchmarks Data
  const [benchmarks, setBenchmarks] = useState<any[]>([]);
  const [benchmarkFilterCity, setBenchmarkFilterCity] = useState("All Cities");
  const [propertyBenchmark, setPropertyBenchmark] = useState<any>(null);
  const [benchProvenance, setBenchProvenance] = useState<Record<string, number>>({});

  // AI Risk Explanation State
  const [aiRiskExplanation, setAiRiskExplanation] = useState<any>(null);
  const [generatingAiRisk, setGeneratingAiRisk] = useState(false);
  const [aiRiskError, setAiRiskError] = useState<string | null>(null);

  // Load properties
  useEffect(() => {
    const fetchProps = async () => {
      setLoadingProps(true);
      try {
        const res = await fetch(`${apiBase}/api/v1/properties?page=1&page_size=100`, { cache: "no-store" });
        if (res.ok) {
          const data = await res.json();
          const items = data.items || [];
          setProperties(items);
          if (items.length > 0 && !selectedPropertyId) {
            setSelectedPropertyId(items[0].id);
          }
        }
      } catch (e) {
        console.error("Failed to load properties:", e);
      } finally {
        setLoadingProps(false);
      }
    };
    fetchProps();
  }, [apiBase]);

  // Load benchmarks
  const fetchBenchmarks = async (city?: string) => {
    setLoadingBench(true);
    try {
      const qCity = city && city !== "All Cities" ? `&city=${encodeURIComponent(city)}` : "";
      const res = await fetch(`${apiBase}/api/v1/benchmarks?page=1&page_size=50${qCity}`, { cache: "no-store" });
      if (res.ok) {
        const data = await res.json();
        setBenchmarks(data.items || []);
        setBenchProvenance(data.provenance_summary || {});
      }
    } catch (e) {
      console.error("Failed to load benchmarks:", e);
    } finally {
      setLoadingBench(false);
    }
  };

  useEffect(() => {
    fetchBenchmarks(benchmarkFilterCity);
  }, [apiBase, benchmarkFilterCity]);

  // Load risk assessment when property changes
  const fetchRiskAssessment = async (propId: number) => {
    setLoadingRisk(true);
    try {
      const res = await fetch(`${apiBase}/api/v1/risk/${propId}/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
      });
      if (res.ok) {
        const data = await res.json();
        setRiskData(data);
      }
    } catch (e) {
      console.error("Risk analysis error:", e);
    } finally {
      setLoadingRisk(false);
    }
  };

  // Load simulation when property changes
  const fetchSimulation = async (propId: number, customInputs?: any) => {
    setLoadingSim(true);
    try {
      const res = await fetch(`${apiBase}/api/v1/risk/${propId}/simulate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: customInputs ? JSON.stringify(customInputs) : undefined,
      });
      if (res.ok) {
        const data = await res.json();
        setSimData(data);
      }
    } catch (e) {
      console.error("Simulation error:", e);
    } finally {
      setLoadingSim(false);
    }
  };

  // Match benchmark for current property
  const fetchPropertyBenchmark = async (prop: PropertyDeal) => {
    try {
      const res = await fetch(
        `${apiBase}/api/v1/benchmarks/match?city=${encodeURIComponent(prop.city)}&locality=${encodeURIComponent(
          prop.locality
        )}&property_type=${encodeURIComponent(prop.property_type || "Apartment")}`,
        { cache: "no-store" }
      );
      if (res.ok) {
        const data = await res.json();
        setPropertyBenchmark(data);
      } else {
        setPropertyBenchmark(null);
      }
    } catch {
      setPropertyBenchmark(null);
    }
  };

  useEffect(() => {
    if (selectedPropertyId) {
      fetchRiskAssessment(selectedPropertyId);
      fetchSimulation(selectedPropertyId);
      const prop = properties.find((p) => p.id === selectedPropertyId);
      if (prop) {
        fetchPropertyBenchmark(prop);
        setSimPrice(prop.price_inr ?? (prop as any).purchase_price_inr ?? "");
        setSimRent(prop.estimated_monthly_rent_inr ?? (prop as any).expected_monthly_rent_inr ?? "");
      }
      setAiRiskExplanation(null);
      setAiRiskError(null);
    }
  }, [selectedPropertyId]);

  // Apply custom what-if inputs
  const handleApplyCustomSimulation = () => {
    if (!selectedPropertyId) return;
    const customPayload: any = {
      vacancy_rate_pct: simVacancy,
      annual_interest_rate_pct: simInterest,
      down_payment_pct: simDownPayment,
      tenure_years: simTenure,
    };
    if (simPrice !== "") customPayload.purchase_price_inr = Number(simPrice);
    if (simRent !== "") customPayload.expected_monthly_rent_inr = Number(simRent);

    fetchSimulation(selectedPropertyId, customPayload);
  };

  // Run AI Risk Explanation
  const handleRunAiRiskExplanation = async () => {
    if (!selectedPropertyId) return;
    setGeneratingAiRisk(true);
    setAiRiskError(null);

    try {
      const res = await fetch(`${apiBase}/api/v1/risk/${selectedPropertyId}/ai-explain`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
      });
      if (res.ok) {
        const data = await res.json();
        setAiRiskExplanation(data);
      } else {
        const err = await res.json();
        setAiRiskError(err.detail || "AI Risk explanation failed. Ensure Ollama is running.");
      }
    } catch {
      setAiRiskError("Failed to connect to local AI service. Verify Ollama is running.");
    } finally {
      setGeneratingAiRisk(false);
    }
  };

  const selectedProp = properties.find((p) => p.id === selectedPropertyId);

  return (
    <div className="space-y-6">
      {/* Top Header & Property Selector */}
      <div className="flex flex-col md:flex-row md:items-center justify-between pb-3 border-b border-slate-800/80 gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold text-white tracking-tight">
              Advanced Risk Intelligence & Market Benchmarking
            </h1>
            <span className="text-[10px] font-bold uppercase px-2 py-0.5 rounded bg-rose-500/10 text-rose-400 border border-rose-500/20">
              Risk Architecture
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Separates calculated financial risks from data confidence and mandatory legal verification.
          </p>
        </div>

        {/* Property Selector */}
        <div className="flex items-center gap-3">
          <span className="text-xs text-slate-400">Target Property:</span>
          <select
            value={selectedPropertyId || ""}
            onChange={(e) => setSelectedPropertyId(Number(e.target.value))}
            className="bg-slate-900 border border-slate-700/80 rounded-lg px-3 py-1.5 text-xs text-white focus:outline-none focus:border-emerald-500 max-w-[280px] truncate"
          >
            {properties.map((p) => (
              <option key={p.id} value={p.id}>
                {p.title} ({p.city})
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Navigation Sub-Tabs */}
      <div className="flex items-center gap-1.5 p-1 rounded-xl bg-slate-900 border border-slate-800 text-xs overflow-x-auto">
        <button
          onClick={() => setActiveTab("overview")}
          className={`px-3.5 py-1.5 rounded-lg font-medium transition-colors flex items-center gap-1.5 shrink-0 ${
            activeTab === "overview"
              ? "bg-rose-500/20 text-rose-300 border border-rose-500/30"
              : "text-slate-400 hover:text-white"
          }`}
        >
          <ShieldAlert className="w-3.5 h-3.5" />
          <span>Risk Overview & Breakdown</span>
        </button>
        <button
          onClick={() => setActiveTab("simulator")}
          className={`px-3.5 py-1.5 rounded-lg font-medium transition-colors flex items-center gap-1.5 shrink-0 ${
            activeTab === "simulator"
              ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/30"
              : "text-slate-400 hover:text-white"
          }`}
        >
          <Sliders className="w-3.5 h-3.5" />
          <span>What-If Stress Simulator</span>
        </button>
        <button
          onClick={() => setActiveTab("benchmarks")}
          className={`px-3.5 py-1.5 rounded-lg font-medium transition-colors flex items-center gap-1.5 shrink-0 ${
            activeTab === "benchmarks"
              ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30"
              : "text-slate-400 hover:text-white"
          }`}
        >
          <Scale className="w-3.5 h-3.5" />
          <span>Market Benchmarking</span>
        </button>
        <button
          onClick={() => setActiveTab("ai-risk")}
          className={`px-3.5 py-1.5 rounded-lg font-medium transition-colors flex items-center gap-1.5 shrink-0 ${
            activeTab === "ai-risk"
              ? "bg-indigo-500/20 text-indigo-300 border border-indigo-500/30"
              : "text-slate-400 hover:text-white"
          }`}
        >
          <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
          <span>AI Risk Officer</span>
          <span className="text-[9px] uppercase px-1 py-0.2 bg-indigo-500/20 text-indigo-300 rounded border border-indigo-500/30">
            llama3.2
          </span>
        </button>
      </div>

      {/* ======================================================================
          SUB-TAB 1: RISK OVERVIEW & THREE-SCORE GAUGES
          ====================================================================== */}
      {activeTab === "overview" && (
        <div className="space-y-6">
          {/* Three Core Independent Scores Grid */}
          {riskData && (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {/* Score 1: Investment Attractiveness */}
              <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800/80 shadow-sm space-y-2">
                <div className="flex items-center justify-between text-xs text-slate-400">
                  <span>1. Investment Attractiveness</span>
                  <Percent className="w-3.5 h-3.5 text-emerald-400" />
                </div>
                <div className="flex items-baseline gap-2">
                  <span className="text-3xl font-extrabold text-white">
                    {riskData.investment_attractiveness_score}
                  </span>
                  <span className="text-xs text-slate-400">/ 100</span>
                </div>
                <p className="text-[11px] text-slate-400">
                  Measures cash flow buffer, gross rental yield, and return efficiency.
                </p>
              </div>

              {/* Score 2: Risk Exposure */}
              <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800/80 shadow-sm space-y-2">
                <div className="flex items-center justify-between text-xs text-slate-400">
                  <span>2. Risk Exposure Score</span>
                  <ShieldAlert className="w-3.5 h-3.5 text-rose-400" />
                </div>
                <div className="flex items-baseline gap-2">
                  <span
                    className={`text-3xl font-extrabold ${
                      riskData.risk_exposure_score >= 60
                        ? "text-rose-400"
                        : riskData.risk_exposure_score >= 40
                        ? "text-amber-400"
                        : "text-emerald-400"
                    }`}
                  >
                    {riskData.risk_exposure_score}
                  </span>
                  <span className="text-xs text-slate-400">/ 100</span>
                  <span
                    className={`text-[10px] font-bold uppercase px-2 py-0.5 rounded border ml-auto ${
                      riskData.overall_risk_level.includes("High") || riskData.overall_risk_level.includes("Critical")
                        ? "bg-rose-500/10 text-rose-400 border-rose-500/20"
                        : riskData.overall_risk_level.includes("Elevated")
                        ? "bg-amber-500/10 text-amber-400 border-amber-500/20"
                        : "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                    }`}
                  >
                    {riskData.overall_risk_level}
                  </span>
                </div>
                <p className="text-[11px] text-slate-400">
                  Weighted financial, debt, rental volatility, and legal risk exposure.
                </p>
              </div>

              {/* Score 3: Data Confidence */}
              <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800/80 shadow-sm space-y-2">
                <div className="flex items-center justify-between text-xs text-slate-400">
                  <span>3. Data Confidence Score</span>
                  <CheckCircle2 className="w-3.5 h-3.5 text-cyan-400" />
                </div>
                <div className="flex items-baseline gap-2">
                  <span
                    className={`text-3xl font-extrabold ${
                      riskData.data_confidence_score >= 75
                        ? "text-cyan-400"
                        : riskData.data_confidence_score >= 50
                        ? "text-amber-400"
                        : "text-slate-400"
                    }`}
                  >
                    {riskData.data_confidence_score}
                  </span>
                  <span className="text-xs text-slate-400">/ 100</span>
                  <span className="text-[10px] font-bold uppercase px-2 py-0.5 rounded bg-cyan-500/10 text-cyan-300 border border-cyan-500/20 ml-auto">
                    {riskData.data_confidence_level}
                  </span>
                </div>
                <p className="text-[11px] text-slate-400">
                  Evaluates completeness, source URLs, and micro-market benchmark coverage.
                </p>
              </div>
            </div>
          )}

          {/* Critical Red Flags Banner */}
          {riskData?.critical_red_flags?.length > 0 && (
            <div className="p-4 rounded-xl bg-rose-950/30 border border-rose-800/50 space-y-2">
              <span className="text-xs font-bold text-rose-400 flex items-center gap-1.5 uppercase tracking-wider">
                <AlertTriangle className="w-4 h-4" />
                Critical Deal Flags Detected ({riskData.critical_red_flags.length})
              </span>
              <ul className="space-y-1 text-xs text-rose-300">
                {riskData.critical_red_flags.map((flag: string, i: number) => (
                  <li key={i} className="flex items-start gap-2">
                    <span className="font-bold text-rose-400">&bull;</span>
                    <span>{flag}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* 5-Category Risk Breakdown Grid */}
          {riskData && (
            <div className="space-y-4">
              <h3 className="text-sm font-semibold text-white">Multi-Dimensional Risk Breakdown</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {Object.entries(riskData.categories || {}).map(([key, cat]: [string, any]) => (
                  <div
                    key={key}
                    className="p-4 rounded-xl bg-slate-900/80 border border-slate-800/80 flex flex-col justify-between space-y-3"
                  >
                    <div>
                      <div className="flex items-center justify-between pb-2 border-b border-slate-800/60">
                        <span className="font-semibold text-xs text-white">{cat.category_name}</span>
                        <span
                          className={`text-[10px] font-bold uppercase px-2 py-0.5 rounded border ${
                            cat.risk_level === "Severe"
                              ? "bg-rose-500/10 text-rose-400 border-rose-500/20"
                              : cat.risk_level === "Elevated"
                              ? "bg-amber-500/10 text-amber-400 border-amber-500/20"
                              : "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                          }`}
                        >
                          {cat.risk_level} ({cat.score})
                        </span>
                      </div>

                      <div className="mt-3 space-y-2 text-xs">
                        <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider block">
                          Identified Factors:
                        </span>
                        <ul className="space-y-1 text-slate-300">
                          {cat.factors?.slice(0, 3).map((f: string, i: number) => (
                            <li key={i} className="flex items-start gap-1.5 text-[11px]">
                              <span className="text-slate-500">&bull;</span>
                              <span>{f}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    </div>

                    <div className="pt-2 border-t border-slate-800/60">
                      <span className="text-[10px] font-semibold text-emerald-400 uppercase tracking-wider block mb-1">
                        Mitigation Step:
                      </span>
                      <p className="text-[11px] text-slate-400">
                        {cat.mitigation_steps?.[0] || "Execute routine legal and financial audits."}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* External Legal Verification Checklist */}
          {riskData?.external_verification_checklist && (
            <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800/80 space-y-2">
              <span className="text-xs font-semibold text-white uppercase tracking-wider block">
                Mandatory Due-Diligence Checklist (Physical & Legal):
              </span>
              <ul className="grid grid-cols-1 md:grid-cols-2 gap-2 text-xs text-slate-300">
                {riskData.external_verification_checklist.map((item: string, i: number) => (
                  <li key={i} className="flex items-start gap-2 p-2 rounded bg-slate-950/40 border border-slate-800/60">
                    <CheckCircle2 className="w-3.5 h-3.5 text-cyan-400 shrink-0 mt-0.5" />
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
              <div className="pt-2 text-[11px] text-slate-400 flex items-center gap-1.5">
                <Info className="w-3.5 h-3.5 text-slate-500" />
                <span>Notice: Antigravity AI does not verify legal deeds. Physical title searches are mandatory.</span>
              </div>
            </div>
          )}
        </div>
      )}

      {/* ======================================================================
          SUB-TAB 2: WHAT-IF SIMULATOR & 6 STRESS SCENARIOS
          ====================================================================== */}
      {activeTab === "simulator" && (
        <div className="space-y-6">
          {/* Interactive Input Form */}
          <div className="p-5 rounded-xl bg-slate-900/80 border border-slate-800/80 space-y-4 shadow-sm">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800/70">
              <div className="flex items-center gap-2">
                <Sliders className="w-4 h-4 text-cyan-400" />
                <h3 className="text-sm font-semibold text-white">What-If Custom Stress Model</h3>
              </div>
              <button
                onClick={handleApplyCustomSimulation}
                className="px-3 py-1.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-slate-950 font-bold text-xs transition-colors"
              >
                Apply Custom Parameters
              </button>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-3 text-xs">
              <div>
                <label className="text-[11px] text-slate-400 block mb-1">Purchase Price (₹)</label>
                <input
                  type="number"
                  value={simPrice}
                  onChange={(e) => setSimPrice(Number(e.target.value))}
                  className="w-full bg-slate-950 border border-slate-800 rounded px-2.5 py-1.5 text-white font-mono"
                />
              </div>
              <div>
                <label className="text-[11px] text-slate-400 block mb-1">Monthly Rent (₹)</label>
                <input
                  type="number"
                  value={simRent}
                  onChange={(e) => setSimRent(Number(e.target.value))}
                  className="w-full bg-slate-950 border border-slate-800 rounded px-2.5 py-1.5 text-white font-mono"
                />
              </div>
              <div>
                <label className="text-[11px] text-slate-400 block mb-1">Vacancy Rate (%)</label>
                <input
                  type="number"
                  step="0.5"
                  value={simVacancy}
                  onChange={(e) => setSimVacancy(Number(e.target.value))}
                  className="w-full bg-slate-950 border border-slate-800 rounded px-2.5 py-1.5 text-white font-mono"
                />
              </div>
              <div>
                <label className="text-[11px] text-slate-400 block mb-1">Loan Interest (%)</label>
                <input
                  type="number"
                  step="0.25"
                  value={simInterest}
                  onChange={(e) => setSimInterest(Number(e.target.value))}
                  className="w-full bg-slate-950 border border-slate-800 rounded px-2.5 py-1.5 text-white font-mono"
                />
              </div>
              <div>
                <label className="text-[11px] text-slate-400 block mb-1">Down Payment (%)</label>
                <input
                  type="number"
                  value={simDownPayment}
                  onChange={(e) => setSimDownPayment(Number(e.target.value))}
                  className="w-full bg-slate-950 border border-slate-800 rounded px-2.5 py-1.5 text-white font-mono"
                />
              </div>
              <div>
                <label className="text-[11px] text-slate-400 block mb-1">Tenure (Years)</label>
                <input
                  type="number"
                  value={simTenure}
                  onChange={(e) => setSimTenure(Number(e.target.value))}
                  className="w-full bg-slate-950 border border-slate-800 rounded px-2.5 py-1.5 text-white font-mono"
                />
              </div>
            </div>
          </div>

          {/* 6 Preconfigured Scenario Cards */}
          {simData?.scenarios && (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {simData.scenarios.map((sc: any) => {
                const isPositive = sc.monthly_cash_flow_inr >= 0;
                return (
                  <div
                    key={sc.scenario_id}
                    className="p-4 rounded-xl bg-slate-900/80 border border-slate-800/80 space-y-3 flex flex-col justify-between"
                  >
                    <div>
                      <div className="flex items-center justify-between pb-2 border-b border-slate-800/60">
                        <span className="font-semibold text-xs text-white truncate max-w-[180px]">
                          {sc.scenario_name}
                        </span>
                        <span className="text-[10px] font-bold uppercase px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                          {sc.badge}
                        </span>
                      </div>
                      <p className="text-[11px] text-slate-400 mt-2 leading-relaxed">
                        {sc.description}
                      </p>
                    </div>

                    <div className="space-y-1.5 text-xs pt-2 border-t border-slate-800/60">
                      <div className="flex justify-between text-slate-400">
                        <span>Net Monthly Cash Flow:</span>
                        <span className={`font-mono font-bold ${isPositive ? "text-emerald-400" : "text-rose-400"}`}>
                          {isPositive ? "+" : ""}₹{sc.monthly_cash_flow_inr?.toLocaleString("en-IN")}/mo
                        </span>
                      </div>
                      <div className="flex justify-between text-slate-400">
                        <span>Gross / Net Yield:</span>
                        <span className="font-mono text-white">
                          {sc.gross_rental_yield_pct}% / {sc.net_rental_yield_pct}%
                        </span>
                      </div>
                      <div className="flex justify-between text-slate-400">
                        <span>Monthly EMI:</span>
                        <span className="font-mono text-slate-300">
                          ₹{sc.monthly_emi_inr?.toLocaleString("en-IN")}/mo
                        </span>
                      </div>
                      <div className="flex justify-between text-slate-400">
                        <span>Risk Exposure:</span>
                        <span className={`text-[10px] font-bold uppercase ${sc.risk_score >= 60 ? "text-rose-400" : "text-emerald-400"}`}>
                          {sc.risk_level} ({sc.risk_score})
                        </span>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}

          {/* Scenario Comparison Chart */}
          {simData?.scenarios && (
            <div className="p-5 rounded-xl bg-slate-900/80 border border-slate-800/80 shadow-sm">
              <h3 className="text-sm font-semibold text-white mb-4">
                Stress-Test Monthly Net Cash Flow Comparison (₹/month)
              </h3>
              <div className="h-64 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={simData.scenarios} margin={{ top: 10, right: 10, left: 10, bottom: 20 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                    <XAxis
                      dataKey="badge"
                      tick={{ fill: "#94a3b8", fontSize: 11 }}
                      interval={0}
                    />
                    <YAxis tick={{ fill: "#94a3b8", fontSize: 11 }} />
                    <Tooltip
                      content={({ active, payload }) => {
                        if (active && payload && payload.length) {
                          const d = payload[0].payload;
                          return (
                            <div className="bg-slate-950 border border-slate-800 p-2.5 rounded text-xs shadow-xl">
                              <p className="font-bold text-white">{d.scenario_name}</p>
                              <p className="text-emerald-400 font-mono mt-1">
                                Cash Flow: ₹{Number(d.monthly_cash_flow_inr).toLocaleString("en-IN")}/mo
                              </p>
                              <p className="text-cyan-400">Gross Yield: {d.gross_rental_yield_pct}%</p>
                              <p className="text-slate-400">Risk: {d.risk_level} ({d.risk_score}/100)</p>
                            </div>
                          );
                        }
                        return null;
                      }}
                    />
                    <Bar dataKey="monthly_cash_flow_inr" name="Monthly Cash Flow (₹)" radius={[4, 4, 0, 0]}>
                      {simData.scenarios.map((entry: any, index: number) => (
                        <Cell
                          key={`cell-${index}`}
                          fill={entry.monthly_cash_flow_inr >= 0 ? "#10b981" : "#f43f5e"}
                        />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}
        </div>
      )}

      {/* ======================================================================
          SUB-TAB 3: MARKET BENCHMARKING
          ====================================================================== */}
      {activeTab === "benchmarks" && (
        <div className="space-y-6">
          {/* Target Property vs Benchmark Comparison Card */}
          {selectedProp && (
            <div className="p-5 rounded-xl bg-slate-900/80 border border-slate-800/80 shadow-sm space-y-4">
              <div className="flex items-center justify-between pb-3 border-b border-slate-800/70">
                <div className="flex items-center gap-2">
                  <Scale className="w-4 h-4 text-emerald-400" />
                  <h3 className="text-sm font-semibold text-white">
                    Property vs Locality Benchmark Alignment
                  </h3>
                </div>
                {propertyBenchmark ? (
                  <span
                    className={`text-[10px] font-bold uppercase px-2 py-0.5 rounded border ${
                      propertyBenchmark.is_demo
                        ? "bg-amber-500/10 text-amber-300 border-amber-500/20"
                        : "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                    }`}
                  >
                    {propertyBenchmark.verification_status} ({propertyBenchmark.data_source})
                  </span>
                ) : (
                  <span className="text-[10px] text-slate-400 italic">Insufficient market data for this locality</span>
                )}
              </div>

              {propertyBenchmark ? (
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs">
                  <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800">
                    <span className="text-slate-400 block text-[11px]">Property Price / sq ft</span>
                    <span className="text-base font-bold text-white font-mono">
                      ₹{selectedProp.price_per_sqft?.toLocaleString("en-IN")}
                    </span>
                    <span className="text-[10px] text-slate-400 block mt-0.5">
                      Benchmark: ₹{propertyBenchmark.avg_price_per_sqft?.toLocaleString("en-IN")}
                    </span>
                  </div>

                  <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800">
                    <span className="text-slate-400 block text-[11px]">Price Premium / Discount</span>
                    {(() => {
                      if (
                        selectedProp.price_per_sqft == null ||
                        propertyBenchmark.avg_price_per_sqft == null ||
                        propertyBenchmark.avg_price_per_sqft <= 0
                      ) {
                        return <span className="text-base font-bold font-mono text-slate-500">N/A</span>;
                      }
                      const diffPct =
                        ((selectedProp.price_per_sqft - propertyBenchmark.avg_price_per_sqft) /
                          propertyBenchmark.avg_price_per_sqft) *
                        100;
                      const isPremium = diffPct > 0;
                      return (
                        <span
                          className={`text-base font-bold font-mono ${
                            isPremium ? "text-amber-400" : "text-emerald-400"
                          }`}
                        >
                          {isPremium ? "+" : ""}
                          {diffPct.toFixed(1)}% {isPremium ? "Premium" : "Discount"}
                        </span>
                      );
                    })()}
                    <span className="text-[10px] text-slate-400 block mt-0.5">vs Locality Average</span>
                  </div>

                  <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800">
                    <span className="text-slate-400 block text-[11px]">Gross Rental Yield</span>
                    <span className="text-base font-bold text-emerald-400 font-mono">
                      {selectedProp.gross_rental_yield_pct}%
                    </span>
                    <span className="text-[10px] text-slate-400 block mt-0.5">
                      Benchmark: {propertyBenchmark.avg_gross_rental_yield_pct}%
                    </span>
                  </div>

                  <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800">
                    <span className="text-slate-400 block text-[11px]">Benchmark Price Band</span>
                    <span className="text-xs font-mono text-slate-300 block mt-1">
                      ₹{propertyBenchmark.min_price_per_sqft?.toLocaleString("en-IN")} - ₹
                      {propertyBenchmark.max_price_per_sqft?.toLocaleString("en-IN")}
                    </span>
                    <span className="text-[10px] text-slate-400 block">Captured: {propertyBenchmark.collection_date}</span>
                  </div>
                </div>
              ) : (
                <div className="p-4 rounded-lg bg-slate-950/40 border border-slate-800 text-xs text-slate-400">
                  <p>
                    No historical survey or user-uploaded dataset matches <strong>{selectedProp.locality}, {selectedProp.city}</strong>.
                    Upload a benchmark CSV or add local survey data below to compare against market standards.
                  </p>
                </div>
              )}
            </div>
          )}

          {/* Benchmark Directory Section */}
          <div className="p-5 rounded-xl bg-slate-900/80 border border-slate-800/80 space-y-4 shadow-sm">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-3 border-b border-slate-800/70 gap-3">
              <div>
                <h3 className="text-sm font-semibold text-white">Market Benchmarking Directory</h3>
                <p className="text-xs text-slate-400 mt-0.5">
                  Showing {benchmarks.length} regional survey points ({benchProvenance.simulated_demo || 0} simulated, {benchProvenance.user_submitted || 0} user-submitted, {benchProvenance.verified_market || 0} verified).
                </p>
              </div>

              {/* City Filter */}
              <div className="flex items-center gap-2">
                <span className="text-xs text-slate-400">City:</span>
                <select
                  value={benchmarkFilterCity}
                  onChange={(e) => setBenchmarkFilterCity(e.target.value)}
                  className="bg-slate-950 border border-slate-800 rounded px-2.5 py-1 text-xs text-white"
                >
                  <option value="All Cities">All Cities</option>
                  <option value="Hyderabad">Hyderabad</option>
                  <option value="Bengaluru">Bengaluru</option>
                  <option value="Pune">Pune</option>
                  <option value="Mumbai">Mumbai</option>
                  <option value="Chennai">Chennai</option>
                  <option value="Visakhapatnam">Visakhapatnam</option>
                  <option value="Vijayawada">Vijayawada</option>
                  <option value="Guntur">Guntur</option>
                </select>
              </div>
            </div>

            {/* Benchmarks Table */}
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse text-xs">
                <thead>
                  <tr className="border-b border-slate-800 text-slate-400 bg-slate-950/40">
                    <th className="py-2.5 px-3">City & Locality</th>
                    <th className="py-2.5 px-3">Property Type</th>
                    <th className="py-2.5 px-3">Avg Price / sq ft</th>
                    <th className="py-2.5 px-3">Avg Rent (₹/mo)</th>
                    <th className="py-2.5 px-3">Benchmark Yield</th>
                    <th className="py-2.5 px-3">Provenance & Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 text-slate-300">
                  {benchmarks.map((b) => (
                    <tr key={b.id} className="hover:bg-slate-800/30">
                      <td className="py-2.5 px-3">
                        <span className="font-semibold text-white block">{b.locality}</span>
                        <span className="text-[10px] text-slate-400">{b.city}</span>
                      </td>
                      <td className="py-2.5 px-3 text-slate-300">{b.property_type}</td>
                      <td className="py-2.5 px-3 font-mono font-medium text-white">
                        ₹{b.avg_price_per_sqft?.toLocaleString("en-IN")}
                      </td>
                      <td className="py-2.5 px-3 font-mono text-cyan-300">
                        ₹{b.avg_monthly_rent_inr?.toLocaleString("en-IN")}
                      </td>
                      <td className="py-2.5 px-3 font-bold text-emerald-400">
                        {b.avg_gross_rental_yield_pct}%
                      </td>
                      <td className="py-2.5 px-3">
                        <span
                          className={`text-[10px] font-bold uppercase px-2 py-0.5 rounded border ${
                            b.is_demo
                              ? "bg-amber-500/10 text-amber-300 border-amber-500/20"
                              : "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                          }`}
                        >
                          {b.verification_status}
                        </span>
                        <span className="text-[10px] text-slate-400 block mt-0.5 truncate max-w-[150px]">
                          {b.data_source}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* ======================================================================
          SUB-TAB 4: AI RISK ADVISOR (OLLAMA LLAMA3.2:3B)
          ====================================================================== */}
      {activeTab === "ai-risk" && (
        <div className="space-y-6">
          <div className="p-5 rounded-xl bg-slate-900/80 border border-slate-800/80 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <div className="flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-indigo-400" />
                <h3 className="text-sm font-semibold text-white">Local AI Risk Intelligence Officer</h3>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-indigo-500/10 text-indigo-300 border border-indigo-500/20">
                  llama3.2:3b
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-1">
                Generates qualitative risk synthesis, key sensitivity assumptions, and an objective due diligence roadmap.
              </p>
            </div>

            <button
              onClick={handleRunAiRiskExplanation}
              disabled={generatingAiRisk}
              className="px-4 py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 disabled:bg-slate-800 disabled:text-slate-500 text-white font-semibold text-xs flex items-center gap-2 transition-colors shadow-lg shadow-indigo-500/20"
            >
              <Sparkles className={`w-3.5 h-3.5 ${generatingAiRisk ? "animate-spin" : ""}`} />
              <span>{generatingAiRisk ? "Analyzing Risk Vectors..." : "Synthesize AI Risk Report"}</span>
            </button>
          </div>

          {aiRiskError && (
            <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs">
              {aiRiskError}
            </div>
          )}

          {generatingAiRisk && (
            <div className="p-8 rounded-xl bg-slate-900/80 border border-slate-800 text-center space-y-3">
              <Sparkles className="w-8 h-8 mx-auto text-indigo-400 animate-spin" />
              <p className="text-sm font-semibold text-white">Synthesizing Risk Vectors with llama3.2:3b...</p>
              <p className="text-xs text-slate-400">
                Evaluating debt burden, downside scenarios, and benchmark provenance on local CPU.
              </p>
            </div>
          )}

          {aiRiskExplanation && !generatingAiRisk && (
            <div className="space-y-4 text-xs">
              {/* Executive Risk Synthesis */}
              <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800/80 space-y-2">
                <span className="font-semibold text-white uppercase tracking-wider block">
                  Executive Risk Synthesis:
                </span>
                <p className="text-slate-300 leading-relaxed">
                  {aiRiskExplanation.executive_risk_summary}
                </p>
              </div>

              {/* Biggest Risks & Sensitive Assumptions */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="p-4 rounded-xl bg-rose-950/20 border border-rose-800/40 space-y-2">
                  <span className="font-semibold text-rose-400 uppercase tracking-wider block">
                    Critical Risk Vectors ({aiRiskExplanation.biggest_risks?.length || 0}):
                  </span>
                  <ul className="space-y-1.5 text-slate-300">
                    {aiRiskExplanation.biggest_risks?.map((r: string, i: number) => (
                      <li key={i} className="flex items-start gap-1.5">
                        <span className="text-rose-400 font-bold">&bull;</span>
                        <span>{r}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                <div className="p-4 rounded-xl bg-amber-950/20 border border-amber-800/40 space-y-2">
                  <span className="font-semibold text-amber-400 uppercase tracking-wider block">
                    Sensitive Financial Assumptions:
                  </span>
                  <ul className="space-y-1.5 text-slate-300">
                    {aiRiskExplanation.sensitive_assumptions?.map((a: string, i: number) => (
                      <li key={i} className="flex items-start gap-1.5">
                        <span className="text-amber-400 font-bold">&bull;</span>
                        <span>{a}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>

              {/* Downside & Benchmark Commentary */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800/80 space-y-1.5">
                  <span className="font-semibold text-cyan-400 uppercase tracking-wider block">
                    Downside Stress Scenarios:
                  </span>
                  <p className="text-slate-300 leading-relaxed">
                    {aiRiskExplanation.downside_scenarios_interpretation}
                  </p>
                </div>

                <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800/80 space-y-1.5">
                  <span className="font-semibold text-emerald-400 uppercase tracking-wider block">
                    Benchmark Alignment:
                  </span>
                  <p className="text-slate-300 leading-relaxed">
                    {aiRiskExplanation.benchmark_comparison_analysis}
                  </p>
                </div>
              </div>

              {/* Actionable Due Diligence Checklist */}
              <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800/80 space-y-2">
                <span className="font-semibold text-white uppercase tracking-wider block">
                  Mandatory Due-Diligence Checklist:
                </span>
                <ul className="space-y-1 text-slate-300">
                  {aiRiskExplanation.data_verification_checklist?.map((c: string, i: number) => (
                    <li key={i} className="flex items-start gap-2">
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0 mt-0.5" />
                      <span>{c}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

