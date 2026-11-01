"use client";

import React, { useState, useEffect } from "react";
import {
  Calculator,
  Building2,
  TrendingUp,
  PieChart as PieIcon,
  BarChart3,
  Landmark,
  Percent,
  IndianRupee,
  ShieldCheck,
  AlertTriangle,
  CheckCircle2,
  Info,
  Calendar,
  Scale,
  Sparkles,
  RefreshCw,
  Sliders,
  ChevronDown,
  ChevronUp,
  Layers,
  ArrowRight,
  Bot,
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
  PieChart,
  Pie,
  Cell,
  AreaChart,
  Area,
} from "recharts";
import { PropertyDeal } from "./DealsTable";
import AIDealAdvisor from "./AIDealAdvisor";

interface FinancialAnalysisViewProps {
  apiBase: string;
  initialTab?: "single" | "ai" | "compare";
}

export default function FinancialAnalysisView({
  apiBase,
  initialTab = "single",
}: FinancialAnalysisViewProps) {
  const [properties, setProperties] = useState<PropertyDeal[]>([]);
  const [selectedPropertyId, setSelectedPropertyId] = useState<number | null>(null);
  const [analysisData, setAnalysisData] = useState<any>(null);
  const [loadingProperties, setLoadingProperties] = useState(true);
  const [calculating, setCalculating] = useState(false);
  const [activeSubTab, setActiveSubTab] = useState<"single" | "ai" | "compare">(initialTab);

  useEffect(() => {
    if (initialTab) {
      setActiveSubTab(initialTab);
    }
  }, [initialTab]);

  // Calculator Parameters
  const [downPaymentPct, setDownPaymentPct] = useState(20.0);
  const [interestRatePct, setInterestRatePct] = useState(8.5);
  const [tenureYears, setTenureYears] = useState(20);
  const [vacancyRatePct, setVacancyRatePct] = useState(5.0);
  const [stampDutyRatePct, setStampDutyRatePct] = useState(6.0);
  const [registrationRatePct, setRegistrationRatePct] = useState(1.0);
  const [brokerageRatePct, setBrokerageRatePct] = useState(1.0);
  const [renovationInr, setRenovationInr] = useState(0);
  const [appreciationRatePct, setAppreciationRatePct] = useState<number | "">("");

  // Comparison State
  const [comparePropertyIds, setComparePropertyIds] = useState<number[]>([]);
  const [compareData, setCompareData] = useState<any>(null);
  const [comparing, setComparing] = useState(false);
  const [aiCompareData, setAiCompareData] = useState<any>(null);
  const [generatingAiCompare, setGeneratingAiCompare] = useState(false);
  const [aiCompareError, setAiCompareError] = useState<string | null>(null);

  const runAIComparison = async () => {
    if (comparePropertyIds.length < 2) return;
    setGeneratingAiCompare(true);
    setAiCompareError(null);
    try {
      const res = await fetch(`${apiBase}/api/v1/ai/compare-analysis`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ property_ids: comparePropertyIds }),
      });
      if (res.ok) {
        const data = await res.json();
        setAiCompareData(data);
      } else {
        const err = await res.json();
        setAiCompareError(err.detail || "AI comparison failed.");
      }
    } catch {
      setAiCompareError("Failed to connect to local AI service. Verify Ollama is running.");
    } finally {
      setGeneratingAiCompare(false);
    }
  };

  // Transparency Drawer
  const [showTransparency, setShowTransparency] = useState(false);

  // 1. Fetch available properties list
  useEffect(() => {
    const loadProperties = async () => {
      setLoadingProperties(true);
      try {
        const res = await fetch(`${apiBase}/api/v1/properties?page=1&page_size=100`, {
          cache: "no-store",
        });
        if (res.ok) {
          const data = await res.json();
          const items = data.items || [];
          setProperties(items);
          if (items.length > 0) {
            setSelectedPropertyId(items[0].id);
            // Default 3 for comparison
            setComparePropertyIds(items.slice(0, Math.min(3, items.length)).map((p: any) => p.id));
          }
        }
      } catch (err) {
        console.error("Failed to load properties:", err);
      } finally {
        setLoadingProperties(false);
      }
    };
    loadProperties();
  }, [apiBase]);

  // 2. Run Single Property Financial Calculation
  const runCalculation = async (propId: number) => {
    if (!propId) return;
    setCalculating(true);
    try {
      const payload: any = {
        down_payment_pct: downPaymentPct,
        annual_interest_rate_pct: interestRatePct,
        tenure_years: tenureYears,
        vacancy_rate_pct: vacancyRatePct,
        stamp_duty_rate_pct: stampDutyRatePct,
        registration_rate_pct: registrationRatePct,
        brokerage_rate_pct: brokerageRatePct,
        renovation_expenses_inr: renovationInr,
      };
      if (appreciationRatePct !== "") {
        payload.annual_appreciation_rate_pct = Number(appreciationRatePct);
      }

      const res = await fetch(`${apiBase}/api/v1/analysis/${propId}/calculate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (res.ok) {
        const data = await res.json();
        setAnalysisData(data);
      }
    } catch (err) {
      console.error("Analysis calculation error:", err);
    } finally {
      setCalculating(false);
    }
  };

  useEffect(() => {
    if (selectedPropertyId) {
      runCalculation(selectedPropertyId);
    }
  }, [
    selectedPropertyId,
    downPaymentPct,
    interestRatePct,
    tenureYears,
    vacancyRatePct,
    stampDutyRatePct,
    registrationRatePct,
    brokerageRatePct,
    renovationInr,
    appreciationRatePct,
  ]);

  // 3. Run Comparison Calculation
  const runComparison = async () => {
    if (comparePropertyIds.length === 0) return;
    setComparing(true);
    try {
      const payload = {
        property_ids: comparePropertyIds,
        down_payment_pct: downPaymentPct,
        annual_interest_rate_pct: interestRatePct,
        tenure_years: tenureYears,
        vacancy_rate_pct: vacancyRatePct,
      };
      const res = await fetch(`${apiBase}/api/v1/analysis/compare`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (res.ok) {
        const data = await res.json();
        setCompareData(data);
      }
    } catch (err) {
      console.error("Comparison error:", err);
    } finally {
      setComparing(false);
    }
  };

  useEffect(() => {
    if (activeSubTab === "compare" && comparePropertyIds.length > 0) {
      runComparison();
    }
  }, [activeSubTab, comparePropertyIds, downPaymentPct, interestRatePct, tenureYears, vacancyRatePct]);

  const selectedProp = properties.find((p) => p.id === selectedPropertyId);

  // Color Palette Constants
  const PIE_COLORS = ["#10b981", "#06b6d4", "#6366f1", "#f59e0b", "#8b5cf6"];

  // Prepare Chart Data
  const acquisitionChartData = analysisData
    ? [
        { name: "Purchase Price", value: analysisData.acquisition_costs.purchase_price_inr },
        { name: "Stamp Duty", value: analysisData.acquisition_costs.stamp_duty_inr },
        { name: "Registration", value: analysisData.acquisition_costs.registration_charges_inr },
        { name: "Brokerage", value: analysisData.acquisition_costs.brokerage_inr },
        { name: "Renovation", value: analysisData.acquisition_costs.renovation_expenses_inr },
      ].filter((item) => item.value > 0)
    : [];

  const cashFlowCashData = analysisData
    ? [
        {
          category: "Monthly Inflow & Outflows",
          grossRent: analysisData.operating_finances.gross_monthly_rent_inr,
          maintenance: analysisData.operating_finances.monthly_maintenance_inr,
          vacancyLoss: analysisData.operating_finances.vacancy_loss_monthly_inr,
          emi: analysisData.loan_metrics.monthly_emi_inr,
          netCashFlow: analysisData.returns.monthly_net_cash_flow_inr,
        },
      ]
    : [];

  // 5-Year Cumulative Cash Flow Projection
  const projectionData = analysisData
    ? [1, 2, 3, 4, 5].map((year) => {
        const cumulativeCashFlow = analysisData.returns.annual_net_cash_flow_inr * year;
        const cumulativeRent = analysisData.operating_finances.annual_gross_rent_inr * year;
        return {
          year: `Year ${year}`,
          cumulativeCashFlow,
          cumulativeRent,
        };
      })
    : [];

  return (
    <div className="space-y-6">
      {/* View Header & Mode Switcher */}
      <div className="flex flex-col md:flex-row md:items-center justify-between pb-3 border-b border-slate-800/80 gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold text-white tracking-tight">
              Real Estate Financial Modeling & Deal Analytics
            </h1>
            <span className="text-[10px] font-bold uppercase px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              Deterministic Engine
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Transparent reducing-balance debt service, acquisition closing costs, net operating income (NOI), and cash-on-cash ROI.
          </p>
        </div>

        {/* Mode Switcher Tabs */}
        <div className="flex items-center gap-1.5 p-1 rounded-xl bg-slate-900 border border-slate-800 self-start md:self-auto text-xs">
          <button
            onClick={() => setActiveSubTab("single")}
            className={`px-3.5 py-1.5 rounded-lg font-medium transition-colors flex items-center gap-1.5 ${
              activeSubTab === "single"
                ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30"
                : "text-slate-400 hover:text-white"
            }`}
          >
            <Calculator className="w-3.5 h-3.5" />
            <span>Single Property Model</span>
          </button>
          <button
            onClick={() => setActiveSubTab("ai")}
            className={`px-3.5 py-1.5 rounded-lg font-medium transition-colors flex items-center gap-1.5 ${
              activeSubTab === "ai"
                ? "bg-indigo-500/20 text-indigo-300 border border-indigo-500/30"
                : "text-slate-400 hover:text-white"
            }`}
          >
            <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
            <span>AI Deal Advisor</span>
            <span className="text-[9px] uppercase px-1 py-0.2 bg-indigo-500/20 text-indigo-300 rounded border border-indigo-500/30">
              Local AI
            </span>
          </button>
          <button
            onClick={() => setActiveSubTab("compare")}
            className={`px-3.5 py-1.5 rounded-lg font-medium transition-colors flex items-center gap-1.5 ${
              activeSubTab === "compare"
                ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30"
                : "text-slate-400 hover:text-white"
            }`}
          >
            <Scale className="w-3.5 h-3.5" />
            <span>Property Comparison</span>
          </button>
        </div>
      </div>

      {activeSubTab === "single" ? (
        <>
          {/* Top Selection & Calculator Controls Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Property Selector & Info Card */}
            <div className="rounded-xl bg-slate-900/80 border border-slate-800/80 p-5 space-y-4 shadow-sm">
              <div className="flex items-center justify-between pb-3 border-b border-slate-800/70">
                <div className="flex items-center gap-2">
                  <Building2 className="w-4 h-4 text-emerald-400" />
                  <h3 className="text-sm font-semibold text-white">Select Property</h3>
                </div>
                {selectedProp && (selectedProp as any).is_demo && (
                  <span className="text-[9px] font-bold uppercase px-1.5 py-0.5 rounded bg-amber-500/10 text-amber-400 border border-amber-500/20">
                    DEMO DATA
                  </span>
                )}
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1.5">
                  Target Indian Real Estate Asset
                </label>
                <select
                  value={selectedPropertyId || ""}
                  onChange={(e) => setSelectedPropertyId(parseInt(e.target.value))}
                  disabled={loadingProperties}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-emerald-500"
                >
                  {properties.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.city} - {p.locality} | {p.bhk} BHK ({p.price_formatted})
                    </option>
                  ))}
                </select>
              </div>

              {selectedProp && (
                <div className="space-y-2.5 p-3 rounded-lg bg-slate-950/60 border border-slate-800/80 text-xs">
                  <div className="font-semibold text-white line-clamp-1">{selectedProp.title}</div>
                  <div className="grid grid-cols-2 gap-2 text-slate-400 text-[11px]">
                    <div>
                      <span>City / Locality:</span>
                      <p className="text-slate-200 font-medium">
                        {selectedProp.locality}, {selectedProp.city}
                      </p>
                    </div>
                    <div>
                      <span>Config & Area:</span>
                      <p className="text-slate-200 font-medium">
                        {selectedProp.bhk} BHK ({selectedProp.area_sqft} sq.ft)
                      </p>
                    </div>
                    <div>
                      <span>Asking Price:</span>
                      <p className="text-emerald-400 font-bold">{selectedProp.price_formatted}</p>
                    </div>
                    <div>
                      <span>Expected Rent:</span>
                      <p className="text-cyan-400 font-bold">{selectedProp.rent_formatted}</p>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Configurable Loan & Acquisition Controls */}
            <div className="lg:col-span-2 rounded-xl bg-slate-900/80 border border-slate-800/80 p-5 space-y-4 shadow-sm">
              <div className="flex items-center justify-between pb-3 border-b border-slate-800/70">
                <div className="flex items-center gap-2">
                  <Sliders className="w-4 h-4 text-cyan-400" />
                  <h3 className="text-sm font-semibold text-white">Financial & Loan Assumptions</h3>
                </div>
                <span className="text-[10px] text-slate-400">Customizable reducing-balance terms</span>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
                {/* Down Payment % */}
                <div>
                  <div className="flex justify-between items-center mb-1">
                    <label className="text-[11px] text-slate-300">Down Payment</label>
                    <span className="text-emerald-400 font-bold">{downPaymentPct}%</span>
                  </div>
                  <input
                    type="number"
                    min="0"
                    max="100"
                    step="1"
                    value={downPaymentPct}
                    onChange={(e) => setDownPaymentPct(parseFloat(e.target.value) || 0)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-md px-2.5 py-1.5 text-white font-mono"
                  />
                </div>

                {/* Interest Rate % */}
                <div>
                  <div className="flex justify-between items-center mb-1">
                    <label className="text-[11px] text-slate-300">Interest Rate</label>
                    <span className="text-cyan-400 font-bold">{interestRatePct}%</span>
                  </div>
                  <input
                    type="number"
                    min="0"
                    max="25"
                    step="0.1"
                    value={interestRatePct}
                    onChange={(e) => setInterestRatePct(parseFloat(e.target.value) || 0)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-md px-2.5 py-1.5 text-white font-mono"
                  />
                </div>

                {/* Loan Tenure */}
                <div>
                  <div className="flex justify-between items-center mb-1">
                    <label className="text-[11px] text-slate-300">Tenure (Years)</label>
                    <span className="text-indigo-400 font-bold">{tenureYears} yrs</span>
                  </div>
                  <input
                    type="number"
                    min="1"
                    max="40"
                    value={tenureYears}
                    onChange={(e) => setTenureYears(parseInt(e.target.value) || 1)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-md px-2.5 py-1.5 text-white font-mono"
                  />
                </div>

                {/* Vacancy Rate % */}
                <div>
                  <div className="flex justify-between items-center mb-1">
                    <label className="text-[11px] text-slate-300">Vacancy Reserve</label>
                    <span className="text-amber-400 font-bold">{vacancyRatePct}%</span>
                  </div>
                  <input
                    type="number"
                    min="0"
                    max="50"
                    step="0.5"
                    value={vacancyRatePct}
                    onChange={(e) => setVacancyRatePct(parseFloat(e.target.value) || 0)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-md px-2.5 py-1.5 text-white font-mono"
                  />
                </div>

                {/* Stamp Duty % */}
                <div>
                  <label className="block text-[11px] text-slate-400 mb-1">Stamp Duty (%)</label>
                  <input
                    type="number"
                    min="0"
                    max="20"
                    step="0.1"
                    value={stampDutyRatePct}
                    onChange={(e) => setStampDutyRatePct(parseFloat(e.target.value) || 0)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-md px-2.5 py-1.5 text-white font-mono"
                  />
                </div>

                {/* Registration Fee % */}
                <div>
                  <label className="block text-[11px] text-slate-400 mb-1">Registration (%)</label>
                  <input
                    type="number"
                    min="0"
                    max="10"
                    step="0.1"
                    value={registrationRatePct}
                    onChange={(e) => setRegistrationRatePct(parseFloat(e.target.value) || 0)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-md px-2.5 py-1.5 text-white font-mono"
                  />
                </div>

                {/* Brokerage % */}
                <div>
                  <label className="block text-[11px] text-slate-400 mb-1">Brokerage (%)</label>
                  <input
                    type="number"
                    min="0"
                    max="10"
                    step="0.1"
                    value={brokerageRatePct}
                    onChange={(e) => setBrokerageRatePct(parseFloat(e.target.value) || 0)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-md px-2.5 py-1.5 text-white font-mono"
                  />
                </div>

                {/* Renovation (₹) */}
                <div>
                  <label className="block text-[11px] text-slate-400 mb-1">Renovation (₹)</label>
                  <input
                    type="number"
                    min="0"
                    step="50000"
                    value={renovationInr}
                    onChange={(e) => setRenovationInr(parseFloat(e.target.value) || 0)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-md px-2.5 py-1.5 text-white font-mono"
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Financial KPI Cards Row */}
          {analysisData && (
            <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-3">
              {/* 1. Gross Rental Yield */}
              <div className="rounded-xl bg-slate-900/80 border border-slate-800/80 p-3.5 shadow-sm">
                <div className="flex items-center justify-between text-slate-400 text-[11px] mb-1">
                  <span>Gross Yield</span>
                  <Percent className="w-3.5 h-3.5 text-cyan-400" />
                </div>
                <div className="text-xl font-bold text-white">
                  {analysisData.returns.gross_rental_yield_pct}%
                </div>
                <span className="text-[10px] text-slate-400">Annual rent / Price</span>
              </div>

              {/* 2. Net Rental Yield */}
              <div className="rounded-xl bg-slate-900/80 border border-slate-800/80 p-3.5 shadow-sm">
                <div className="flex items-center justify-between text-slate-400 text-[11px] mb-1">
                  <span>Net Yield</span>
                  <Percent className="w-3.5 h-3.5 text-emerald-400" />
                </div>
                <div className="text-xl font-bold text-emerald-400">
                  {analysisData.returns.net_rental_yield_pct}%
                </div>
                <span className="text-[10px] text-slate-400">NOI / Total Cost</span>
              </div>

              {/* 3. Monthly Cash Flow */}
              <div className="rounded-xl bg-slate-900/80 border border-slate-800/80 p-3.5 shadow-sm">
                <div className="flex items-center justify-between text-slate-400 text-[11px] mb-1">
                  <span>Monthly Cash Flow</span>
                  <IndianRupee className="w-3.5 h-3.5 text-indigo-400" />
                </div>
                <div
                  className={`text-xl font-bold ${
                    analysisData.returns.monthly_net_cash_flow_inr >= 0
                      ? "text-emerald-400"
                      : "text-rose-400"
                  }`}
                >
                  {analysisData.returns.monthly_net_cash_flow_inr >= 0 ? "+" : ""}₹
                  {analysisData.returns.monthly_net_cash_flow_inr?.toLocaleString("en-IN")}
                </div>
                <span className="text-[10px] text-slate-400">After EMI & Maint</span>
              </div>

              {/* 4. Cash-on-Cash Return */}
              <div className="rounded-xl bg-slate-900/80 border border-slate-800/80 p-3.5 shadow-sm">
                <div className="flex items-center justify-between text-slate-400 text-[11px] mb-1">
                  <span>Cash-on-Cash ROI</span>
                  <TrendingUp className="w-3.5 h-3.5 text-emerald-400" />
                </div>
                <div
                  className={`text-xl font-bold ${
                    analysisData.returns.cash_on_cash_roi_pct >= 0
                      ? "text-white"
                      : "text-rose-400"
                  }`}
                >
                  {analysisData.returns.cash_on_cash_roi_pct}%
                </div>
                <span className="text-[10px] text-slate-400">Cash Flow / Equity</span>
              </div>

              {/* 5. Monthly EMI */}
              <div className="rounded-xl bg-slate-900/80 border border-slate-800/80 p-3.5 shadow-sm">
                <div className="flex items-center justify-between text-slate-400 text-[11px] mb-1">
                  <span>Monthly EMI</span>
                  <Landmark className="w-3.5 h-3.5 text-amber-400" />
                </div>
                <div className="text-xl font-bold text-white font-mono">
                  ₹{analysisData.loan_metrics.monthly_emi_inr?.toLocaleString("en-IN")}
                </div>
                <span className="text-[10px] text-slate-400">
                  {tenureYears} yrs @ {interestRatePct}%
                </span>
              </div>

              {/* 6. Investment Score & Classification */}
              <div className="rounded-xl bg-slate-900/80 border border-slate-800/80 p-3.5 shadow-sm">
                <div className="flex items-center justify-between text-slate-400 text-[11px] mb-1">
                  <span>Deal Score</span>
                  <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
                </div>
                <div className="flex items-baseline gap-1.5">
                  <div className="text-xl font-bold text-white">
                    {analysisData.deal_score.overall_score}
                  </div>
                  <span className="text-[10px] text-slate-400">/ 100</span>
                </div>
                <span
                  className={`text-[9px] font-bold uppercase px-1.5 py-0.5 rounded border inline-block mt-0.5 ${
                    analysisData.deal_score.classification === "Excellent Deal"
                      ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                      : analysisData.deal_score.classification === "Good Deal"
                      ? "bg-cyan-500/10 text-cyan-400 border-cyan-500/20"
                      : analysisData.deal_score.classification === "Average Deal"
                      ? "bg-amber-500/10 text-amber-400 border-amber-500/20"
                      : "bg-rose-500/10 text-rose-400 border-rose-500/20"
                  }`}
                >
                  {analysisData.deal_score.classification}
                </span>
              </div>
            </div>
          )}

          {/* Sensitivity & Scenario Stress Testing */}
          {analysisData && analysisData.returns?.sensitivity_scenarios && (
            <div className="rounded-xl bg-slate-900/80 border border-slate-800/80 p-5 shadow-sm space-y-4">
              <div className="flex items-center justify-between pb-3 border-b border-slate-800/70">
                <div className="flex items-center gap-2">
                  <Sliders className="w-4 h-4 text-cyan-400" />
                  <h3 className="text-sm font-semibold text-white">
                    Scenario Analysis & Stress Testing
                  </h3>
                </div>
                <span className="text-[11px] text-slate-400">
                  Deterministic simulation of market shocks & interest shifts
                </span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {(["conservative", "base", "optimistic"] as const).map((key) => {
                  const sc = analysisData.returns.sensitivity_scenarios[key];
                  if (!sc) return null;
                  const isConservative = key === "conservative";
                  const isOptimistic = key === "optimistic";
                  return (
                    <div
                      key={key}
                      className={`p-4 rounded-xl border ${
                        isConservative
                          ? "bg-rose-950/20 border-rose-800/40"
                          : isOptimistic
                          ? "bg-emerald-950/20 border-emerald-800/40"
                          : "bg-slate-950/60 border-slate-800/80"
                      } space-y-3`}
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-semibold text-xs text-white">{sc.scenario_name}</span>
                        <span
                          className={`text-[10px] font-bold uppercase px-2 py-0.5 rounded ${
                            isConservative
                              ? "bg-rose-500/10 text-rose-400 border border-rose-500/20"
                              : isOptimistic
                              ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                              : "bg-cyan-500/10 text-cyan-400 border border-cyan-500/20"
                          }`}
                        >
                          {sc.badge}
                        </span>
                      </div>

                      <div className="space-y-1.5 text-xs">
                        <div className="flex justify-between text-slate-400">
                          <span>Rent / Vacancy:</span>
                          <span className="text-white font-mono">
                            ₹{sc.monthly_rent_inr?.toLocaleString("en-IN")} ({sc.vacancy_rate_pct}%)
                          </span>
                        </div>
                        <div className="flex justify-between text-slate-400">
                          <span>Interest Rate:</span>
                          <span className="text-white font-mono">{sc.interest_rate_pct}%</span>
                        </div>
                        <div className="flex justify-between text-slate-400">
                          <span>Monthly NOI:</span>
                          <span className="text-white font-mono">
                            ₹{sc.monthly_noi_inr?.toLocaleString("en-IN")}
                          </span>
                        </div>
                        <div className="flex justify-between text-slate-400 pt-1 border-t border-slate-800/60">
                          <span>Net Cash Flow:</span>
                          <span
                            className={`font-bold font-mono ${
                              sc.monthly_net_cash_flow_inr >= 0 ? "text-emerald-400" : "text-rose-400"
                            }`}
                          >
                            {sc.monthly_net_cash_flow_inr >= 0 ? "+" : ""}₹
                            {sc.monthly_net_cash_flow_inr?.toLocaleString("en-IN")}/mo
                          </span>
                        </div>
                        <div className="flex justify-between text-slate-400">
                          <span>Gross / Net Yield:</span>
                          <span className="text-white font-mono">
                            {sc.gross_rental_yield_pct}% / {sc.net_rental_yield_pct}%
                          </span>
                        </div>
                        <div className="flex justify-between text-slate-400">
                          <span>Cash-on-Cash ROI:</span>
                          <span
                            className={`font-bold font-mono ${
                              sc.cash_on_cash_roi_pct >= 0 ? "text-white" : "text-rose-400"
                            }`}
                          >
                            {sc.cash_on_cash_roi_pct}%
                          </span>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Visualizations Grid */}
          {analysisData && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Chart 1: Acquisition Cost Composition */}
              <div className="rounded-xl bg-slate-900/70 border border-slate-800/80 p-5 shadow-sm">
                <div className="flex items-center justify-between pb-3 border-b border-slate-800/60">
                  <div className="flex items-center gap-2">
                    <PieIcon className="w-4 h-4 text-cyan-400" />
                    <h3 className="text-sm font-semibold text-white">Total Acquisition Cost Breakdown</h3>
                  </div>
                  <span className="text-xs font-mono font-bold text-white">
                    ₹{analysisData.acquisition_costs.total_acquisition_cost_inr?.toLocaleString("en-IN")}
                  </span>
                </div>

                <div className="h-64 w-full mt-2">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={acquisitionChartData}
                        dataKey="value"
                        nameKey="name"
                        cx="50%"
                        cy="50%"
                        outerRadius={80}
                        innerRadius={45}
                        paddingAngle={3}
                      >
                        {acquisitionChartData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={PIE_COLORS[index % PIE_COLORS.length]} />
                        ))}
                      </Pie>
                      <Tooltip
                        content={({ active, payload }) => {
                          if (active && payload && payload.length) {
                            const data = payload[0];
                            return (
                              <div className="bg-slate-950 border border-slate-800 p-2.5 rounded-lg text-xs shadow-xl">
                                <span className="font-semibold text-white">{data.name}:</span>
                                <span className="font-mono text-emerald-400 font-bold ml-1.5">
                                  ₹{Number(data.value).toLocaleString("en-IN")}
                                </span>
                              </div>
                            );
                          }
                          return null;
                        }}
                      />
                      <Legend
                        verticalAlign="bottom"
                        wrapperStyle={{ fontSize: "11px", color: "#94a3b8" }}
                      />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
              </div>

              {/* Chart 2: 5-Year Cumulative Cash Flow Forecast */}
              <div className="rounded-xl bg-slate-900/70 border border-slate-800/80 p-5 shadow-sm">
                <div className="flex items-center justify-between pb-3 border-b border-slate-800/60">
                  <div className="flex items-center gap-2">
                    <BarChart3 className="w-4 h-4 text-emerald-400" />
                    <h3 className="text-sm font-semibold text-white">
                      5-Year Cumulative Cash Flow Forecast
                    </h3>
                  </div>
                  <span className="text-xs text-slate-400">
                    Break-even: {analysisData.returns.break_even.summary}
                  </span>
                </div>

                <div className="h-64 w-full mt-2">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={projectionData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                      <defs>
                        <linearGradient id="cashFlowGrad" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#10b981" stopOpacity={0.4} />
                          <stop offset="95%" stopColor="#10b981" stopOpacity={0.0} />
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                      <XAxis dataKey="year" tick={{ fill: "#94a3b8", fontSize: 11 }} />
                      <YAxis
                        tick={{ fill: "#94a3b8", fontSize: 11 }}
                        tickFormatter={(v) => `₹${(v / 100000).toFixed(0)}L`}
                      />
                      <Tooltip
                        content={({ active, payload }) => {
                          if (active && payload && payload.length) {
                            return (
                              <div className="bg-slate-950 border border-slate-800 p-2.5 rounded-lg text-xs shadow-xl">
                                <p className="font-semibold text-white">{payload[0].payload.year}</p>
                                <p className="text-emerald-400 font-mono mt-1">
                                  Cumulative Cash Flow: ₹
                                  {Number(payload[0].value).toLocaleString("en-IN")}
                                </p>
                              </div>
                            );
                          }
                          return null;
                        }}
                      />
                      <Area
                        type="monotone"
                        dataKey="cumulativeCashFlow"
                        stroke="#10b981"
                        fillOpacity={1}
                        fill="url(#cashFlowGrad)"
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </div>
          )}

          {/* Deal Assessment & Risk Analysis Panel */}
          {analysisData && (
            <div className="rounded-xl bg-slate-900/80 border border-slate-800/80 p-5 shadow-sm space-y-4">
              <div className="flex items-center justify-between pb-3 border-b border-slate-800/70">
                <div className="flex items-center gap-2">
                  <ShieldCheck className="w-4 h-4 text-emerald-400" />
                  <h3 className="text-sm font-semibold text-white">
                    Deal Assessment & Factor Analysis
                  </h3>
                </div>
                <span className="text-xs text-slate-400">
                  {analysisData.deal_score.explanation}
                </span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Positive Drivers */}
                <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800/80 space-y-2.5">
                  <span className="text-xs font-semibold text-emerald-400 flex items-center gap-1.5 uppercase tracking-wider">
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    Positive Return Drivers ({analysisData.deal_score.positive_factors.length})
                  </span>
                  {analysisData.deal_score.positive_factors.length > 0 ? (
                    <ul className="space-y-1.5 text-xs text-slate-300">
                      {analysisData.deal_score.positive_factors.map((f: string, i: number) => (
                        <li key={i} className="flex items-start gap-2">
                          <span className="text-emerald-400 font-bold">&bull;</span>
                          <span>{f}</span>
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p className="text-xs text-slate-500">No prominent positive yield drivers.</p>
                  )}
                </div>

                {/* Risk Flags & Negative Drivers */}
                <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800/80 space-y-2.5">
                  <span className="text-xs font-semibold text-amber-400 flex items-center gap-1.5 uppercase tracking-wider">
                    <AlertTriangle className="w-3.5 h-3.5" />
                    Risk Flags & Cautions ({analysisData.deal_score.risk_flags.length})
                  </span>
                  {analysisData.deal_score.risk_flags.length > 0 ? (
                    <ul className="space-y-1.5 text-xs text-slate-300">
                      {analysisData.deal_score.risk_flags.map((rf: string, i: number) => (
                        <li key={i} className="flex items-start gap-2">
                          <span className="text-rose-400 font-bold">&bull;</span>
                          <span className="text-rose-300">{rf}</span>
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p className="text-xs text-emerald-400/90 flex items-center gap-1.5">
                      <CheckCircle2 className="w-3.5 h-3.5" /> No critical risk flags detected under standard parameters.
                    </p>
                  )}
                </div>
              </div>

              {/* Scoring Sub-Metrics Bar */}
              <div className="pt-2">
                <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block mb-2">
                  Scoring Component Breakdown (0 to 100 scale):
                </span>
                <div className="grid grid-cols-2 sm:grid-cols-6 gap-2 text-center text-xs">
                  <div className="p-2 rounded bg-slate-950 border border-slate-800">
                    <span className="text-[10px] text-slate-400 block">Gross Yield</span>
                    <span className="font-bold text-cyan-300 font-mono">
                      {analysisData.deal_score.metric_scores.gross_yield_score}
                    </span>
                  </div>
                  <div className="p-2 rounded bg-slate-950 border border-slate-800">
                    <span className="text-[10px] text-slate-400 block">Net Yield</span>
                    <span className="font-bold text-emerald-300 font-mono">
                      {analysisData.deal_score.metric_scores.net_yield_score}
                    </span>
                  </div>
                  <div className="p-2 rounded bg-slate-950 border border-slate-800">
                    <span className="text-[10px] text-slate-400 block">Cash Flow</span>
                    <span className="font-bold text-indigo-300 font-mono">
                      {analysisData.deal_score.metric_scores.cash_flow_score}
                    </span>
                  </div>
                  <div className="p-2 rounded bg-slate-950 border border-slate-800">
                    <span className="text-[10px] text-slate-400 block">Debt Coverage</span>
                    <span className="font-bold text-amber-300 font-mono">
                      {analysisData.deal_score.metric_scores.debt_burden_score}
                    </span>
                  </div>
                  <div className="p-2 rounded bg-slate-950 border border-slate-800">
                    <span className="text-[10px] text-slate-400 block">Expense Ratio</span>
                    <span className="font-bold text-teal-300 font-mono">
                      {analysisData.deal_score.metric_scores.expense_ratio_score}
                    </span>
                  </div>
                  <div className="p-2 rounded bg-slate-950 border border-slate-800">
                    <span className="text-[10px] text-slate-400 block">Data Quality</span>
                    <span className="font-bold text-slate-300 font-mono">
                      {analysisData.deal_score.metric_scores.data_completeness_score}
                    </span>
                  </div>
                </div>
              </div>

              {/* Disclaimer */}
              <div className="p-3 rounded-lg bg-slate-950/40 border border-slate-800/60 text-[11px] text-slate-400 flex items-center gap-2">
                <Info className="w-4 h-4 text-slate-500 shrink-0" />
                <span>{analysisData.deal_score.disclaimer}</span>
              </div>
            </div>
          )}

          {/* Financial Transparency Drawer */}
          <div className="rounded-xl bg-slate-900/60 border border-slate-800/80 p-4 shadow-sm">
            <button
              onClick={() => setShowTransparency(!showTransparency)}
              className="w-full flex items-center justify-between text-xs font-semibold text-slate-300 hover:text-white transition-colors"
            >
              <div className="flex items-center gap-2">
                <Info className="w-4 h-4 text-cyan-400" />
                <span>Financial Transparency & Formula Details</span>
              </div>
              {showTransparency ? (
                <ChevronUp className="w-4 h-4 text-slate-400" />
              ) : (
                <ChevronDown className="w-4 h-4 text-slate-400" />
              )}
            </button>

            {showTransparency && analysisData && (
              <div className="mt-4 pt-4 border-t border-slate-800/80 space-y-3 text-xs text-slate-300">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 font-mono text-[11px]">
                  <div className="p-3 rounded bg-slate-950 border border-slate-800">
                    <span className="text-cyan-400 font-bold block mb-1">Gross Rental Yield:</span>
                    <code>{analysisData.transparency_notes.gross_rental_yield_formula}</code>
                  </div>
                  <div className="p-3 rounded bg-slate-950 border border-slate-800">
                    <span className="text-emerald-400 font-bold block mb-1">Net Rental Yield:</span>
                    <code>{analysisData.transparency_notes.net_rental_yield_formula}</code>
                  </div>
                  <div className="p-3 rounded bg-slate-950 border border-slate-800">
                    <span className="text-indigo-400 font-bold block mb-1">Monthly Cash Flow:</span>
                    <code>{analysisData.transparency_notes.monthly_cash_flow_formula}</code>
                  </div>
                  <div className="p-3 rounded bg-slate-950 border border-slate-800">
                    <span className="text-amber-400 font-bold block mb-1">Reducing Balance EMI:</span>
                    <code>{analysisData.transparency_notes.emi_formula}</code>
                  </div>
                </div>

                <div className="space-y-1 text-[11px] text-slate-400">
                  <span className="font-semibold text-slate-300 block">Model Assumptions:</span>
                  <ul className="list-disc pl-4 space-y-0.5">
                    {analysisData.transparency_notes.assumptions.map((a: string, i: number) => (
                      <li key={i}>{a}</li>
                    ))}
                  </ul>
                </div>
              </div>
            )}
          </div>
        </>
      ) : activeSubTab === "ai" ? (
        <AIDealAdvisor
          apiBase={apiBase}
          property={selectedProp || null}
          financialAnalysis={analysisData}
        />
      ) : (
        /* ======================================================================
           Tab 2: Property Comparison Matrix (Up to 4 Properties)
           ====================================================================== */
        <div className="space-y-6">
          {/* Comparison Selector Controls */}
          <div className="p-5 rounded-xl bg-slate-900/80 border border-slate-800/80 space-y-3 shadow-sm">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Scale className="w-4 h-4 text-emerald-400" />
                <h3 className="text-sm font-semibold text-white">Compare Real Estate Opportunities</h3>
              </div>
              <span className="text-xs text-slate-400">
                Selected {comparePropertyIds.length} of 4 properties
              </span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-2.5">
              {properties.map((p) => {
                const isSelected = comparePropertyIds.includes(p.id);
                return (
                  <button
                    key={p.id}
                    onClick={() => {
                      if (isSelected) {
                        setComparePropertyIds(comparePropertyIds.filter((id) => id !== p.id));
                      } else if (comparePropertyIds.length < 4) {
                        setComparePropertyIds([...comparePropertyIds, p.id]);
                      }
                    }}
                    className={`p-2.5 rounded-lg border text-left transition-all text-xs ${
                      isSelected
                        ? "bg-emerald-500/15 border-emerald-500/40 text-emerald-200"
                        : "bg-slate-950/60 border-slate-800 text-slate-400 hover:text-white"
                    }`}
                  >
                    <div className="font-semibold text-white truncate">{p.title}</div>
                    <div className="text-[11px] text-slate-400 mt-0.5">
                      {p.city} &bull; {p.price_formatted} &bull; {p.gross_rental_yield_pct}%
                    </div>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Comparison Table */}
          {compareData && compareData.items && (
            <div className="rounded-xl bg-slate-900/80 border border-slate-800/80 overflow-hidden shadow-sm">
              <div className="p-4 border-b border-slate-800/70 flex items-center justify-between">
                <h3 className="text-sm font-semibold text-white">
                  Side-by-Side Investment Metrics Matrix
                </h3>
                <span className="text-xs text-slate-400">
                  Uniform Loan: {downPaymentPct}% down, {interestRatePct}% rate, {tenureYears} yrs
                </span>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse text-xs">
                  <thead>
                    <tr className="border-b border-slate-800 bg-slate-950/50 text-slate-400">
                      <th className="py-3 px-4 font-medium">Metric</th>
                      {compareData.items.map((item: any) => (
                        <th key={item.property_id} className="py-3 px-4 font-semibold text-white">
                          <div className="truncate max-w-[200px]">{item.title}</div>
                          <div className="text-[11px] text-slate-400 font-normal">
                            {item.locality}, {item.city}
                          </div>
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 text-slate-300">
                    <tr>
                      <td className="py-3 px-4 font-medium text-slate-400">Purchase Price</td>
                      {compareData.items.map((item: any) => (
                        <td key={item.property_id} className="py-3 px-4 font-bold text-white">
                          {item.price_formatted}
                        </td>
                      ))}
                    </tr>
                    <tr>
                      <td className="py-3 px-4 font-medium text-slate-400">Acquisition Cost</td>
                      {compareData.items.map((item: any) => (
                        <td key={item.property_id} className="py-3 px-4 font-mono">
                          ₹{item.total_acquisition_cost_inr?.toLocaleString("en-IN")}
                        </td>
                      ))}
                    </tr>
                    <tr>
                      <td className="py-3 px-4 font-medium text-slate-400">Expected Monthly Rent</td>
                      {compareData.items.map((item: any) => (
                        <td key={item.property_id} className="py-3 px-4 font-medium text-cyan-400 font-mono">
                          {item.rent_formatted}
                        </td>
                      ))}
                    </tr>
                    <tr>
                      <td className="py-3 px-4 font-medium text-slate-400">Monthly Home Loan EMI</td>
                      {compareData.items.map((item: any) => (
                        <td key={item.property_id} className="py-3 px-4 font-mono text-slate-300">
                          ₹{item.monthly_emi_inr?.toLocaleString("en-IN")}/mo
                        </td>
                      ))}
                    </tr>
                    <tr>
                      <td className="py-3 px-4 font-medium text-slate-400">Gross Rental Yield</td>
                      {compareData.items.map((item: any) => (
                        <td
                          key={item.property_id}
                          className={`py-3 px-4 font-bold ${
                            item.gross_rental_yield_pct >= 4.0
                              ? "text-emerald-400"
                              : item.gross_rental_yield_pct >= 3.25
                              ? "text-cyan-400"
                              : "text-rose-400"
                          }`}
                        >
                          {item.gross_rental_yield_pct}%
                        </td>
                      ))}
                    </tr>
                    <tr>
                      <td className="py-3 px-4 font-medium text-slate-400">Net Rental Yield</td>
                      {compareData.items.map((item: any) => (
                        <td key={item.property_id} className="py-3 px-4 font-bold text-emerald-400">
                          {item.net_rental_yield_pct}%
                        </td>
                      ))}
                    </tr>
                    <tr>
                      <td className="py-3 px-4 font-medium text-slate-400">Net Monthly Cash Flow</td>
                      {compareData.items.map((item: any) => (
                        <td
                          key={item.property_id}
                          className={`py-3 px-4 font-bold ${
                            item.monthly_net_cash_flow_inr >= 0 ? "text-emerald-400" : "text-rose-400"
                          }`}
                        >
                          {item.monthly_net_cash_flow_inr >= 0 ? "+" : ""}₹
                          {item.monthly_net_cash_flow_inr?.toLocaleString("en-IN")}/mo
                        </td>
                      ))}
                    </tr>
                    <tr>
                      <td className="py-3 px-4 font-medium text-slate-400">Cash-on-Cash ROI</td>
                      {compareData.items.map((item: any) => (
                        <td key={item.property_id} className="py-3 px-4 font-bold text-white">
                          {item.cash_on_cash_roi_pct}%
                        </td>
                      ))}
                    </tr>
                    <tr>
                      <td className="py-3 px-4 font-medium text-slate-400">Deal Score & Status</td>
                      {compareData.items.map((item: any) => (
                        <td key={item.property_id} className="py-3 px-4">
                          <div className="flex items-center gap-2">
                            <span className="font-bold text-white px-2 py-0.5 rounded bg-slate-800">
                              {item.investment_score}
                            </span>
                            <span
                              className={`text-[10px] font-bold uppercase px-1.5 py-0.5 rounded border ${
                                item.classification === "Excellent Deal"
                                  ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                                  : item.classification === "Good Deal"
                                  ? "bg-cyan-500/10 text-cyan-400 border-cyan-500/20"
                                  : item.classification === "Average Deal"
                                  ? "bg-amber-500/10 text-amber-400 border-amber-500/20"
                                  : "bg-rose-500/10 text-rose-400 border-rose-500/20"
                              }`}
                            >
                              {item.classification}
                            </span>
                          </div>
                        </td>
                      ))}
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Comparative Chart */}
          {compareData && compareData.items && (
            <div className="rounded-xl bg-slate-900/80 border border-slate-800/80 p-5 shadow-sm">
              <h3 className="text-sm font-semibold text-white mb-4">
                Gross Rental Yield vs Cash-on-Cash Return Comparison
              </h3>
              <div className="h-64 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={compareData.items} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                    <XAxis
                      dataKey="locality"
                      tick={{ fill: "#94a3b8", fontSize: 11 }}
                      tickFormatter={(v, i) => `${compareData.items[i]?.city} (${v})`}
                    />
                    <YAxis unit="%" tick={{ fill: "#94a3b8", fontSize: 11 }} />
                    <Tooltip
                      content={({ active, payload }) => {
                        if (active && payload && payload.length) {
                          const d = payload[0].payload;
                          return (
                            <div className="bg-slate-950 border border-slate-800 p-2.5 rounded-lg text-xs shadow-xl">
                              <p className="font-semibold text-white">{d.title}</p>
                              <p className="text-cyan-400 mt-1">Gross Yield: {d.gross_rental_yield_pct}%</p>
                              <p className="text-emerald-400">Cash-on-Cash ROI: {d.cash_on_cash_roi_pct}%</p>
                              <p className="text-slate-300">Score: {d.investment_score}/100 ({d.classification})</p>
                            </div>
                          );
                        }
                        return null;
                      }}
                    />
                    <Legend wrapperStyle={{ fontSize: "11px", color: "#94a3b8" }} />
                    <Bar dataKey="gross_rental_yield_pct" name="Gross Yield (%)" fill="#06b6d4" radius={[4, 4, 0, 0]} />
                    <Bar dataKey="cash_on_cash_roi_pct" name="Cash-on-Cash ROI (%)" fill="#10b981" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}

          {/* AI Multi-Property Comparative Insights */}
          {compareData && compareData.items && compareData.items.length >= 2 && (
            <div className="rounded-xl bg-slate-900/80 border border-slate-800/80 p-5 shadow-sm space-y-4">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-3 border-b border-slate-800/70 gap-3">
                <div className="flex items-center gap-2">
                  <Sparkles className="w-4 h-4 text-indigo-400" />
                  <h3 className="text-sm font-semibold text-white">
                    Local AI Deal Comparative Analysis
                  </h3>
                  <span className="text-[10px] px-2 py-0.5 rounded-full bg-indigo-500/10 text-indigo-300 border border-indigo-500/20 font-mono">
                    llama3.2:3b
                  </span>
                </div>

                <button
                  onClick={runAIComparison}
                  disabled={generatingAiCompare}
                  className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold flex items-center gap-2 disabled:bg-slate-800 disabled:text-slate-500 transition-colors"
                >
                  <Sparkles className={`w-3.5 h-3.5 ${generatingAiCompare ? "animate-spin" : ""}`} />
                  <span>{generatingAiCompare ? "Analyzing Trade-offs..." : "Generate AI Comparison"}</span>
                </button>
              </div>

              {aiCompareError && (
                <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs">
                  {aiCompareError}
                </div>
              )}

              {generatingAiCompare && (
                <div className="p-6 text-center text-xs text-slate-400 space-y-2">
                  <Sparkles className="w-6 h-6 mx-auto text-indigo-400 animate-spin" />
                  <p>Comparing ticket sizes, yields, and risk profiles across selected deals with llama3.2:3b...</p>
                </div>
              )}

              {aiCompareData && !generatingAiCompare && (
                <div className="space-y-4 text-xs">
                  {/* Top Pick Banner */}
                  <div className="p-4 rounded-xl bg-gradient-to-r from-emerald-950/40 via-slate-950 to-slate-900 border border-emerald-500/30 flex items-start gap-3">
                    <div className="p-2 rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 shrink-0">
                      <CheckCircle2 className="w-5 h-5" />
                    </div>
                    <div className="space-y-1">
                      <span className="text-[10px] font-bold uppercase tracking-wider text-emerald-400">
                        AI Top Pick Recommendation
                      </span>
                      <div className="text-sm font-bold text-white">
                        {aiCompareData.top_pick_title}
                      </div>
                      <p className="text-slate-300 text-xs leading-relaxed">
                        {aiCompareData.verdict_summary}
                      </p>
                    </div>
                  </div>

                  {/* Executive Comparison */}
                  <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800/80 space-y-1">
                    <span className="font-semibold text-white block">Executive Comparison:</span>
                    <p className="text-slate-300 leading-relaxed">{aiCompareData.executive_comparison}</p>
                  </div>

                  {/* Property Insights Grid */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {aiCompareData.comparative_insights?.map((ins: any, i: number) => (
                      <div key={i} className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800/80 space-y-1.5">
                        <div className="font-semibold text-white text-xs truncate">{ins.title}</div>
                        <div className="text-[11px] text-emerald-400">
                          <span className="font-semibold text-slate-400">Strength: </span>{ins.primary_strength}
                        </div>
                        <div className="text-[11px] text-amber-400">
                          <span className="font-semibold text-slate-400">Risk/Drag: </span>{ins.primary_risk}
                        </div>
                        <div className="text-[11px] text-cyan-300">
                          <span className="font-semibold text-slate-400">Best For: </span>{ins.investor_suitability}
                        </div>
                      </div>
                    ))}
                  </div>

                  {/* Tradeoffs */}
                  {aiCompareData.key_tradeoffs?.length > 0 && (
                    <div className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800/80 space-y-1.5">
                      <span className="font-semibold text-white block">Key Financial Trade-offs:</span>
                      <ul className="space-y-1 text-slate-300">
                        {aiCompareData.key_tradeoffs.map((t: string, i: number) => (
                          <li key={i} className="flex items-start gap-2">
                            <span className="text-indigo-400 font-bold">&bull;</span>
                            <span>{t}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
