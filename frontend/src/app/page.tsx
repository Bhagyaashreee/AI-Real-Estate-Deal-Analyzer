"use client";

import React, { useState, useEffect } from "react";
import Sidebar from "@/components/Sidebar";
import Header from "@/components/Header";
import KpiCards from "@/components/KpiCards";
import YieldChart from "@/components/YieldChart";
import DealsTable, { PropertyDeal } from "@/components/DealsTable";
import HealthBanner from "@/components/HealthBanner";
import PropertiesCatalog from "@/components/PropertiesCatalog";
import AddPropertyModal from "@/components/AddPropertyModal";
import PropertyDetailsModal from "@/components/PropertyDetailsModal";
import FinancialAnalysisView from "@/components/FinancialAnalysisView";
import RiskIntelligenceView from "@/components/RiskIntelligenceView";
import PdfReportsView from "@/components/PdfReportsView";
import {
  Sparkles,
  ArrowRight,
  ShieldCheck,
  ShieldAlert,
  Flame,
  PieChart,
  Building2,
  Plus,
  FileSpreadsheet,
  Calculator,
  Scale,
  FileText,
} from "lucide-react";

const FALLBACK_PROPERTIES: PropertyDeal[] = [
  {
    id: 1,
    title: "3 BHK Luxury Apartment in Brigade Cornerstone Utopia",
    city: "Bengaluru",
    locality: "Whitefield",
    property_type: "Apartment",
    bhk: 3,
    area_sqft: 1650,
    price_inr: 14500000,
    price_formatted: "₹1.45 Cr",
    price_per_sqft: 8788,
    estimated_monthly_rent_inr: 52000,
    rent_formatted: "₹52,000/mo",
    gross_rental_yield_pct: 4.30,
    net_rental_yield_pct: 3.75,
    monthly_cash_flow_inr: 14500,
    ai_investment_score: 88,
    risk_level: "Low",
    valuation_status: "Undervalued",
    key_highlights: "High rental demand from IT corridor, metro connectivity",
  },
  {
    id: 2,
    title: "2 BHK Sea-Facing High Rise Apartment",
    city: "Mumbai",
    locality: "Bandra West",
    property_type: "Apartment",
    bhk: 2,
    area_sqft: 920,
    price_inr: 38000000,
    price_formatted: "₹3.80 Cr",
    price_per_sqft: 41304,
    estimated_monthly_rent_inr: 88000,
    rent_formatted: "₹88,000/mo",
    gross_rental_yield_pct: 2.78,
    net_rental_yield_pct: 2.25,
    monthly_cash_flow_inr: -12000,
    ai_investment_score: 64,
    risk_level: "Moderate",
    valuation_status: "Overpriced",
    key_highlights: "Premium capital appreciation zone, modest rental yield",
  },
  {
    id: 3,
    title: "3 BHK Gated Community Villa in Financial District",
    city: "Hyderabad",
    locality: "Gachibowli / Hitec City",
    property_type: "Villa",
    bhk: 3,
    area_sqft: 2200,
    price_inr: 19500000,
    price_formatted: "₹1.95 Cr",
    price_per_sqft: 8864,
    estimated_monthly_rent_inr: 78000,
    rent_formatted: "₹78,000/mo",
    gross_rental_yield_pct: 4.80,
    net_rental_yield_pct: 4.15,
    monthly_cash_flow_inr: 22000,
    ai_investment_score: 91,
    risk_level: "Low",
    valuation_status: "Undervalued",
    key_highlights: "Exceptional rental yield, proximity to multinational tech parks",
  },
  {
    id: 4,
    title: "2.5 BHK Golf Course Road Apartment",
    city: "Gurugram",
    locality: "Sector 54",
    property_type: "Apartment",
    bhk: 2,
    area_sqft: 1400,
    price_inr: 21000000,
    price_formatted: "₹2.10 Cr",
    price_per_sqft: 15000,
    estimated_monthly_rent_inr: 65000,
    rent_formatted: "₹65,000/mo",
    gross_rental_yield_pct: 3.71,
    net_rental_yield_pct: 3.10,
    monthly_cash_flow_inr: 5000,
    ai_investment_score: 77,
    risk_level: "Moderate",
    valuation_status: "Fair Value",
    key_highlights: "Rapid infrastructure development, high expat tenant base",
  },
  {
    id: 5,
    title: "2 BHK Modern Smart Home in IT Park Hub",
    city: "Pune",
    locality: "Hinjewadi Phase 1",
    property_type: "Apartment",
    bhk: 2,
    area_sqft: 1050,
    price_inr: 8200000,
    price_formatted: "₹82.00 L",
    price_per_sqft: 7810,
    estimated_monthly_rent_inr: 34000,
    rent_formatted: "₹34,000/mo",
    gross_rental_yield_pct: 4.98,
    net_rental_yield_pct: 4.35,
    monthly_cash_flow_inr: 11500,
    ai_investment_score: 93,
    risk_level: "Low",
    valuation_status: "Undervalued",
    key_highlights: "Top tier gross rental yield, affordable ticket size for investors",
  },
];

export default function Home() {
  const [activeTab, setActiveTab] = useState("dashboard");
  const [selectedCity, setSelectedCity] = useState("All Cities");
  const [healthData, setHealthData] = useState<any>(null);
  const [healthLoading, setHealthLoading] = useState(false);
  const [kpiData, setKpiData] = useState<any>(null);
  const [properties, setProperties] = useState<PropertyDeal[]>(FALLBACK_PROPERTIES);
  const [isHeaderAddOpen, setIsHeaderAddOpen] = useState(false);
  const [selectedInspectProp, setSelectedInspectProp] = useState<PropertyDeal | null>(null);
  const [isInspectOpen, setIsInspectOpen] = useState(false);

  const apiBase = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  const fetchHealthAndData = async () => {
    setHealthLoading(true);
    try {
      // 1. Fetch health endpoint
      const healthRes = await fetch(`${apiBase}/api/v1/health`, {
        cache: "no-store",
      });
      if (healthRes.ok) {
        const data = await healthRes.json();
        setHealthData(data);
      } else {
        setHealthData(null);
      }

      // 2. Fetch properties summary
      const summaryRes = await fetch(`${apiBase}/api/v1/properties/summary`, {
        cache: "no-store",
      });
      if (summaryRes.ok) {
        const sumData = await summaryRes.json();
        setKpiData(sumData.kpis);
      }

      // 3. Fetch properties list
      const propRes = await fetch(`${apiBase}/api/v1/properties?page=1&page_size=8`, {
        cache: "no-store",
      });
      if (propRes.ok) {
        const propList = await propRes.json();
        if (propList.items && Array.isArray(propList.items) && propList.items.length > 0) {
          const mapped: PropertyDeal[] = propList.items.map((item: any) => ({
            ...item,
            monthly_cash_flow_inr: item.monthly_cash_flow_inr ?? item.estimated_monthly_cash_flow_inr,
            estimated_monthly_cash_flow_inr: item.estimated_monthly_cash_flow_inr ?? item.monthly_cash_flow_inr,
            estimated_monthly_rent_inr: item.estimated_monthly_rent_inr ?? item.expected_monthly_rent_inr,
            expected_monthly_rent_inr: item.expected_monthly_rent_inr ?? item.estimated_monthly_rent_inr,
            bhk: item.bhk ?? item.bedrooms ?? 1,
            area_sqft: item.area_sqft ?? item.built_up_area_sqft,
            price_inr: item.price_inr ?? item.purchase_price_inr,
          }));
          setProperties(mapped);
        }
      }
    } catch {
      // If backend is not currently running, retain smooth UI with local fallback
      setHealthData(null);
    } finally {
      setHealthLoading(false);
    }
  };

  useEffect(() => {
    fetchHealthAndData();
  }, []);

  return (
    <div className="flex min-h-screen bg-[#090D16]">
      {/* Sidebar */}
      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Top Header */}
        <Header
          selectedCity={selectedCity}
          setSelectedCity={setSelectedCity}
          backendOnline={healthData ? healthData.status === "healthy" : healthLoading ? null : false}
          onRefreshHealth={fetchHealthAndData}
          onAddProperty={() => setIsHeaderAddOpen(true)}
        />

        {/* Dynamic Body Content based on Active Tab */}
        <main className="flex-1 p-4 sm:p-6 max-w-7xl xl:max-w-[1440px] 2xl:max-w-[1600px] w-full mx-auto space-y-6 min-w-0">
          {activeTab === "properties" || activeTab === "screener" ? (
            <PropertiesCatalog apiBase={apiBase} />
          ) : activeTab === "analysis" ? (
            <FinancialAnalysisView apiBase={apiBase} initialTab="single" />
          ) : activeTab === "ai-advisor" ? (
            <FinancialAnalysisView apiBase={apiBase} initialTab="ai" />
          ) : activeTab === "compare" ? (
            <FinancialAnalysisView apiBase={apiBase} initialTab="compare" />
          ) : activeTab === "risk-intelligence" || activeTab === "trends" ? (
            <RiskIntelligenceView apiBase={apiBase} />
          ) : activeTab === "reports" ? (
            <PdfReportsView apiBase={apiBase} />
          ) : (
            <>
              {/* Welcome Banner / Overview */}
              <div className="flex flex-col md:flex-row md:items-center justify-between pb-2 border-b border-slate-800/60 gap-4">
                <div>
                  <div className="flex items-center gap-2">
                    <h1 className="text-xl font-bold text-white tracking-tight">
                      Indian Property Investment Intelligence
                    </h1>
                    <span className="text-xs px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-medium flex items-center gap-1">
                      <Flame className="w-3 h-3" /> Tier-1 Yields Active
                    </span>
                  </div>
                  <p className="text-xs text-slate-400 mt-1">
                    Real-time rental yield benchmarking, cash flow analysis & AI-driven deal scoring in ₹ (INR).
                  </p>
                </div>

                {/* Quick Action Pills */}
                <div className="flex items-center gap-2.5">
                  <button
                    onClick={() => setActiveTab("properties")}
                    className="px-3 py-1.5 rounded-lg bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 text-xs font-medium transition-colors flex items-center gap-1.5"
                  >
                    <Building2 className="w-3.5 h-3.5" />
                    <span>Properties</span>
                  </button>
                  <button
                    onClick={() => setActiveTab("analysis")}
                    className="px-3 py-1.5 rounded-lg bg-indigo-500/10 hover:bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 text-xs font-medium transition-colors flex items-center gap-1.5"
                  >
                    <Calculator className="w-3.5 h-3.5" />
                    <span>Deal Engine</span>
                  </button>
                  <button
                    onClick={() => setActiveTab("ai-advisor")}
                    className="px-3 py-1.5 rounded-lg bg-emerald-500/15 hover:bg-emerald-500/25 text-emerald-300 border border-emerald-500/30 text-xs font-semibold transition-colors flex items-center gap-1.5"
                  >
                    <Sparkles className="w-3.5 h-3.5 text-emerald-400" />
                    <span>AI Advisor</span>
                  </button>
                  <button
                    onClick={() => setActiveTab("compare")}
                    className="px-3 py-1.5 rounded-lg bg-cyan-500/10 hover:bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 text-xs font-medium transition-colors flex items-center gap-1.5"
                  >
                    <Scale className="w-3.5 h-3.5" />
                    <span>Compare</span>
                  </button>
                  <button
                    onClick={() => setActiveTab("risk-intelligence")}
                    className="px-3 py-1.5 rounded-lg bg-rose-500/10 hover:bg-rose-500/20 text-rose-300 border border-rose-500/30 text-xs font-medium transition-colors flex items-center gap-1.5"
                  >
                    <ShieldAlert className="w-3.5 h-3.5 text-rose-400" />
                    <span>Risk & Stress Test</span>
                  </button>
                  <button
                    onClick={() => setActiveTab("reports")}
                    className="px-3 py-1.5 rounded-lg bg-indigo-500/15 hover:bg-indigo-500/25 text-indigo-300 border border-indigo-500/30 text-xs font-semibold transition-colors flex items-center gap-1.5"
                  >
                    <FileText className="w-3.5 h-3.5 text-indigo-400" />
                    <span>PDF Reports</span>
                  </button>
                  <span className="text-xs font-mono px-2.5 py-1.5 rounded-md bg-slate-900 border border-slate-800 text-slate-300 flex items-center gap-1.5">
                    <Sparkles className="w-3 h-3 text-indigo-400" />
                    llama3.2:3b
                  </span>
                </div>
              </div>

              {/* Metric KPI Cards */}
              <KpiCards data={kpiData} />

              {/* Analytics Chart & Deal Highlight Card Grid */}
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Yield vs Benchmark Chart */}
                <div className="lg:col-span-2">
                  <YieldChart />
                </div>

                {/* Micro-Market Quick Intelligence Card */}
                <div className="rounded-xl bg-slate-900/70 border border-slate-800/80 p-5 flex flex-col justify-between shadow-sm">
                  <div>
                    <div className="flex items-center justify-between pb-3 border-b border-slate-800/70">
                      <div className="flex items-center gap-2">
                        <PieChart className="w-4 h-4 text-cyan-400" />
                        <h3 className="text-sm font-semibold text-white">Investment Thesis</h3>
                      </div>
                      <span className="text-[10px] font-bold uppercase text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded">
                        Q4 Insight
                      </span>
                    </div>

                    <div className="mt-4 space-y-3.5 text-xs text-slate-300">
                      <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800/80">
                        <div className="font-semibold text-white flex items-center justify-between">
                          <span>Highest Yield Hub</span>
                          <span className="text-emerald-400 font-bold">4.98% Gross</span>
                        </div>
                        <p className="text-[11px] text-slate-400 mt-1">
                          Hinjewadi, Pune presents the highest capital-to-rental efficiency driven by tech workforce demand.
                        </p>
                      </div>

                      <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800/80">
                        <div className="font-semibold text-white flex items-center justify-between">
                          <span>Compressed Yield Zone</span>
                          <span className="text-rose-400 font-bold">2.78% Gross</span>
                        </div>
                        <p className="text-[11px] text-slate-400 mt-1">
                          Bandra West, Mumbai trades at high capital multiples, requiring long holding periods for IRR recovery.
                        </p>
                      </div>
                    </div>
                  </div>

                  <div className="mt-4 pt-3 border-t border-slate-800/60 flex items-center justify-between text-xs text-slate-400">
                    <span className="flex items-center gap-1.5">
                      <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
                      Local AI Verified
                    </span>
                    <button
                      onClick={() => setActiveTab("properties")}
                      className="text-emerald-400 hover:text-emerald-300 font-medium inline-flex items-center gap-1"
                    >
                      <span>Explore {kpiData?.total_deals_analyzed ?? "24"} Properties</span>
                      <ArrowRight className="w-3 h-3" />
                    </button>
                  </div>
                </div>
              </div>

              {/* Analyzed Properties Table */}
              <DealsTable
                properties={properties}
                selectedCity={selectedCity}
                onInspectProperty={(p) => {
                  setSelectedInspectProp(p);
                  setIsInspectOpen(true);
                }}
              />

              {/* Full-Stack Health & Diagnostic Status */}
              <HealthBanner
                health={healthData}
                loading={healthLoading}
                onRefresh={fetchHealthAndData}
              />
            </>
          )}
        </main>
      </div>

      {/* Global Add Property Modal from Header */}
      <AddPropertyModal
        isOpen={isHeaderAddOpen}
        onClose={() => setIsHeaderAddOpen(false)}
        onSuccess={fetchHealthAndData}
        apiBase={apiBase}
      />

      {/* Property Details Modal from Dashboard DealsTable */}
      <PropertyDetailsModal
        property={selectedInspectProp}
        isOpen={isInspectOpen}
        onClose={() => setIsInspectOpen(false)}
      />
    </div>
  );
}
