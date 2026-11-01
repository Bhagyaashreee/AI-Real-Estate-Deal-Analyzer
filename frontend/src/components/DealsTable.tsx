"use client";

import React, { useState, useMemo, useRef, useEffect } from "react";
import { Building, Sparkles, ExternalLink, ArrowUpDown } from "lucide-react";

export interface PropertyDeal {
  id: number;
  title: string;
  city: string;
  locality: string;
  state?: string;
  property_type?: string;
  bedrooms?: number;
  bhk?: number;
  bathrooms?: number;
  built_up_area_sqft?: number;
  area_sqft?: number;
  purchase_price_inr?: number;
  price_inr?: number;
  price_formatted?: string;
  price_per_sqft?: number;
  expected_monthly_rent_inr?: number;
  estimated_monthly_rent_inr?: number;
  rent_formatted?: string;
  gross_rental_yield_pct?: number;
  net_rental_yield_pct?: number;
  monthly_cash_flow_inr?: number;
  estimated_monthly_cash_flow_inr?: number;
  ai_investment_score?: number;
  risk_level?: string;
  valuation_status?: string;
  ai_summary?: string;
  key_highlights?: string;
  is_demo?: boolean;
  listing_source?: string;
  source_url?: string;
  property_age?: string;
  monthly_maintenance_inr?: number;
  listing_date?: string;
  created_at?: string;
  updated_at?: string;
}

interface DealsTableProps {
  properties: PropertyDeal[];
  selectedCity: string;
  onInspectProperty?: (property: PropertyDeal) => void;
}

// Defensive helper: format monthly cash flow preserving valid 0 values
export function formatCashFlow(val?: number | null): { text: string; colorClass: string; isAvailable: boolean } {
  if (val === undefined || val === null || isNaN(val)) {
    return { text: "N/A", colorClass: "text-slate-500", isAvailable: false };
  }
  if (val === 0) {
    return { text: "₹0/mo", colorClass: "text-slate-300", isAvailable: true };
  }
  if (val > 0) {
    return { text: `+₹${Math.round(val).toLocaleString("en-IN")}/mo`, colorClass: "text-emerald-400", isAvailable: true };
  }
  return { text: `-₹${Math.abs(Math.round(val)).toLocaleString("en-IN")}/mo`, colorClass: "text-rose-400", isAvailable: true };
}

// Defensive helper: format price per square foot
export function formatPricePerSqft(val?: number | null): string {
  if (val === undefined || val === null || isNaN(val)) {
    return "N/A";
  }
  return `₹${Math.round(val).toLocaleString("en-IN")}/sq.ft`;
}

// Defensive helper: format rental yield
export function formatYield(val?: number | null): { text: string; colorClass: string } {
  if (val === undefined || val === null || isNaN(val)) {
    return { text: "N/A", colorClass: "text-slate-500" };
  }
  const colorClass =
    val >= 4.0 ? "text-emerald-400" : val >= 3.25 ? "text-cyan-400" : "text-rose-400";
  return { text: `${Number(val).toFixed(2)}%`, colorClass };
}

// Defensive helper: format BHK configuration
export function formatBhk(bhk?: number | null, bedrooms?: number | null): string {
  const v = bhk ?? bedrooms;
  if (v === undefined || v === null || isNaN(v)) {
    return "N/A";
  }
  if (v === 0) {
    return "Studio / Plot";
  }
  return `${v} BHK`;
}

// Defensive helper: format area in sq.ft
export function formatArea(area?: number | null, builtUp?: number | null): string {
  const v = area ?? builtUp;
  if (v === undefined || v === null || isNaN(v)) {
    return "N/A";
  }
  return `${Math.round(v).toLocaleString("en-IN")} sq.ft`;
}

// Defensive helper: format AI deal score
export function formatScore(score?: number | null): string {
  if (score === undefined || score === null || isNaN(score)) {
    return "—";
  }
  return `${score}`;
}

type SortField = "yield" | "cash_flow" | "price" | "score";

// Explicit column width distribution summing to exactly 100%
const COLUMN_WIDTHS = [
  "24%", // 1. Property & Micro-Market
  "9%",  // 2. City
  "9%",  // 3. Config & Area
  "11%", // 4. Price (INR)
  "10%", // 5. Est. Rent
  "8%",  // 6. Gross Yield
  "11%", // 7. Cash Flow
  "8%",  // 8. AI Score
  "10%", // 9. Valuation
  "10%", // 10. Actions
] as const;

export default function DealsTable({ properties, selectedCity, onInspectProperty }: DealsTableProps) {
  const [sortField, setSortField] = useState<SortField>("yield");
  const [sortAsc, setSortAsc] = useState<boolean>(false);
  const scrollContainerRef = useRef<HTMLDivElement>(null);

  // Guarantee that table scroll starts flush on the left (scrollLeft = 0)
  useEffect(() => {
    if (scrollContainerRef.current) {
      scrollContainerRef.current.scrollLeft = 0;
    }
  }, [selectedCity, properties]);

  // 1. Filter by selected city
  const filtered = useMemo(() => {
    const list = selectedCity === "All Cities"
      ? properties
      : properties.filter((p) => p.city && p.city.toLowerCase() === selectedCity.toLowerCase());

    // 2. Sort properties defensively
    return [...list].sort((a, b) => {
      let valA = 0;
      let valB = 0;

      switch (sortField) {
        case "yield":
          valA = a.gross_rental_yield_pct ?? -999;
          valB = b.gross_rental_yield_pct ?? -999;
          break;
        case "cash_flow":
          valA = a.monthly_cash_flow_inr ?? a.estimated_monthly_cash_flow_inr ?? -999999999;
          valB = b.monthly_cash_flow_inr ?? b.estimated_monthly_cash_flow_inr ?? -999999999;
          break;
        case "price":
          valA = a.price_inr ?? a.purchase_price_inr ?? 0;
          valB = b.price_inr ?? b.purchase_price_inr ?? 0;
          break;
        case "score":
          valA = a.ai_investment_score ?? 0;
          valB = b.ai_investment_score ?? 0;
          break;
      }

      return sortAsc ? valA - valB : valB - valA;
    });
  }, [properties, selectedCity, sortField, sortAsc]);

  const toggleSort = (field: SortField) => {
    if (sortField === field) {
      setSortAsc(!sortAsc);
    } else {
      setSortField(field);
      setSortAsc(false);
    }
  };

  return (
    <div className="w-full rounded-xl bg-slate-900/70 border border-slate-800/80 shadow-sm overflow-hidden min-w-0">
      {/* Table Card Header */}
      <div className="p-4 sm:p-5 border-b border-slate-800/70 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <Building className="w-4 h-4 text-emerald-400 shrink-0" />
            <h3 className="text-sm font-semibold text-white tracking-tight">Analyzed Investment Opportunities</h3>
          </div>
          <p className="text-xs text-slate-400 mt-0.5">
            Showing {filtered.length} properties evaluated with local llama3.2:3b metrics
          </p>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <span className="text-xs text-slate-400">Sort by:</span>
          <button
            onClick={() => toggleSort("yield")}
            className={`flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs border transition-colors ${
              sortField === "yield"
                ? "bg-emerald-500/10 text-emerald-300 border-emerald-500/30"
                : "bg-slate-800/70 text-slate-300 border-slate-700/60 hover:bg-slate-700/60"
            }`}
          >
            <span>Rental Yield</span>
            <ArrowUpDown className="w-3 h-3 text-slate-400" />
          </button>
          <button
            onClick={() => toggleSort("cash_flow")}
            className={`flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs border transition-colors ${
              sortField === "cash_flow"
                ? "bg-emerald-500/10 text-emerald-300 border-emerald-500/30"
                : "bg-slate-800/70 text-slate-300 border-slate-700/60 hover:bg-slate-700/60"
            }`}
          >
            <span>Cash Flow</span>
            <ArrowUpDown className="w-3 h-3 text-slate-400" />
          </button>
        </div>
      </div>

      {/* Responsive table container with visible custom scrollbar and left-alignment guarantee */}
      <div
        ref={scrollContainerRef}
        className="overflow-x-auto w-full custom-table-scrollbar"
      >
        <table className="w-full min-w-[960px] table-fixed text-left border-collapse text-xs">
          <colgroup>{COLUMN_WIDTHS.map((width, idx) => <col key={idx} style={{ width }} />)}</colgroup>

          <thead>
            <tr className="border-b border-slate-800/80 bg-slate-950/50 text-slate-400 font-medium select-none">
              <th className="py-3 pl-5 pr-3">Property & Micro-Market</th>
              <th className="py-3 px-2.5">City</th>
              <th className="py-3 px-2.5">Config & Area</th>
              <th
                className="py-3 px-2.5 cursor-pointer hover:text-white transition-colors"
                onClick={() => toggleSort("price")}
                title="Click to sort by purchase price"
              >
                <div className="flex items-center gap-1">
                  <span>Price (INR)</span>
                  <ArrowUpDown className="w-2.5 h-2.5 text-slate-500" />
                </div>
              </th>
              <th className="py-3 px-2.5">Est. Rent</th>
              <th
                className="py-3 px-2.5 cursor-pointer hover:text-white transition-colors"
                onClick={() => toggleSort("yield")}
                title="Click to sort by gross rental yield"
              >
                <div className="flex items-center gap-1">
                  <span>Gross Yield</span>
                  <ArrowUpDown className="w-2.5 h-2.5 text-slate-500" />
                </div>
              </th>
              <th
                className="py-3 px-2.5 cursor-pointer hover:text-white transition-colors"
                onClick={() => toggleSort("cash_flow")}
                title="Click to sort by monthly cash flow"
              >
                <div className="flex items-center gap-1">
                  <span>Cash Flow</span>
                  <ArrowUpDown className="w-2.5 h-2.5 text-slate-500" />
                </div>
              </th>
              <th
                className="py-3 px-2 cursor-pointer hover:text-white transition-colors"
                onClick={() => toggleSort("score")}
                title="Click to sort by AI score"
              >
                <div className="flex items-center gap-1">
                  <span>AI Score</span>
                  <ArrowUpDown className="w-2.5 h-2.5 text-slate-500" />
                </div>
              </th>
              <th className="py-3 px-2.5">Valuation</th>
              <th className="py-3 pl-2 pr-5 text-right">Actions</th>
            </tr>
          </thead>

          <tbody className="divide-y divide-slate-800/60 text-slate-300">
            {filtered.length === 0 ? (
              <tr>
                <td colSpan={10} className="py-8 text-center text-slate-500 text-xs">
                  No properties found for the selected filter.
                </td>
              </tr>
            ) : (
              filtered.map((item) => {
                const isUndervalued = item.valuation_status === "Undervalued";
                const isOverpriced = item.valuation_status === "Overpriced";

                // Resolve cash flow defensively
                const rawCashFlow = item.monthly_cash_flow_inr ?? item.estimated_monthly_cash_flow_inr;
                const cashFlow = formatCashFlow(rawCashFlow);

                // Resolve price & price per sqft defensively
                const pricePerSqft = formatPricePerSqft(item.price_per_sqft);
                const priceFormatted =
                  item.price_formatted ||
                  (item.price_inr != null
                    ? `₹${Math.round(item.price_inr).toLocaleString("en-IN")}`
                    : item.purchase_price_inr != null
                    ? `₹${Math.round(item.purchase_price_inr).toLocaleString("en-IN")}`
                    : "N/A");

                // Resolve rent formatted defensively
                const rawRent = item.estimated_monthly_rent_inr ?? item.expected_monthly_rent_inr;
                const rentFormatted =
                  item.rent_formatted ||
                  (rawRent != null ? `₹${Math.round(rawRent).toLocaleString("en-IN")}/mo` : "N/A");

                // Resolve gross yield defensively
                const yieldMetric = formatYield(item.gross_rental_yield_pct);

                // Resolve BHK & Area defensively
                const bhkText = formatBhk(item.bhk, item.bedrooms);
                const areaText = formatArea(item.area_sqft, item.built_up_area_sqft);

                // Resolve score defensively
                const scoreText = formatScore(item.ai_investment_score);

                return (
                  <tr
                    key={item.id}
                    className="hover:bg-slate-800/30 transition-colors group"
                  >
                    {/* 1. Property Title & Locality (Guaranteed visible left padding) */}
                    <td className="py-3 pl-5 pr-3 overflow-hidden">
                      <div className="flex items-center gap-1.5 min-w-0">
                        <span
                          className="font-semibold text-white truncate hover:text-emerald-300 transition-colors cursor-pointer"
                          title={item.title || "Untitled Listing"}
                          onClick={() => onInspectProperty?.(item)}
                        >
                          {item.title || "Untitled Listing"}
                        </span>
                        {item.is_demo && (
                          <span className="text-[9px] font-bold uppercase px-1.5 py-0.5 rounded bg-purple-500/10 text-purple-400 border border-purple-500/20 shrink-0">
                            DEMO
                          </span>
                        )}
                      </div>
                      <div
                        className="text-[11px] text-slate-400 truncate mt-0.5"
                        title={item.locality || item.city || "Micro-market not specified"}
                      >
                        {item.locality || item.city || "Micro-market not specified"}
                      </div>
                    </td>

                    {/* 2. City */}
                    <td className="py-3 px-2.5 font-medium text-slate-300 whitespace-nowrap overflow-hidden text-ellipsis">
                      {item.city || "N/A"}
                    </td>

                    {/* 3. Config & Area */}
                    <td className="py-3 px-2.5 whitespace-nowrap">
                      <span className="text-slate-200 font-medium block">{bhkText}</span>
                      <span className="text-slate-400 text-[11px] block">{areaText}</span>
                    </td>

                    {/* 4. Price (INR) & Per sqft */}
                    <td className="py-3 px-2.5 whitespace-nowrap">
                      <div className="font-semibold text-white">{priceFormatted}</div>
                      <div className="text-[11px] text-slate-400 font-mono">{pricePerSqft}</div>
                    </td>

                    {/* 5. Estimated Rent */}
                    <td className="py-3 px-2.5 font-medium text-slate-300 whitespace-nowrap font-mono">
                      {rentFormatted}
                    </td>

                    {/* 6. Gross Yield */}
                    <td className="py-3 px-2.5 whitespace-nowrap">
                      <span className={`font-bold font-mono ${yieldMetric.colorClass}`}>
                        {yieldMetric.text}
                      </span>
                    </td>

                    {/* 7. Cash Flow */}
                    <td className="py-3 px-2.5 whitespace-nowrap">
                      <span className={`font-medium font-mono ${cashFlow.colorClass}`}>
                        {cashFlow.text}
                      </span>
                    </td>

                    {/* 8. AI Score */}
                    <td className="py-3 px-2 whitespace-nowrap">
                      <div className="flex items-center gap-1.5">
                        <div className="w-6 h-6 rounded-md bg-slate-800 border border-slate-700/60 flex items-center justify-center font-bold text-white text-[11px] shrink-0">
                          {scoreText}
                        </div>
                        <Sparkles className="w-2.5 h-2.5 text-indigo-400 shrink-0" />
                      </div>
                    </td>

                    {/* 9. Valuation Status */}
                    <td className="py-3 px-2.5 whitespace-nowrap">
                      <span
                        className={`px-2 py-0.5 rounded-full text-[10px] font-semibold uppercase tracking-wider inline-block border ${
                          isUndervalued
                            ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                            : isOverpriced
                            ? "bg-rose-500/10 text-rose-400 border-rose-500/20"
                            : "bg-amber-500/10 text-amber-400 border-amber-500/20"
                        }`}
                      >
                        {item.valuation_status || "Fair Value"}
                      </span>
                    </td>

                    {/* 10. Actions (Guaranteed visible right padding) */}
                    <td className="py-3 pl-2 pr-5 text-right whitespace-nowrap">
                      <button
                        onClick={() => onInspectProperty?.(item)}
                        className="text-xs px-2.5 py-1 rounded bg-slate-800/80 hover:bg-emerald-500/20 hover:text-emerald-300 hover:border-emerald-500/30 border border-slate-700/60 text-slate-300 transition-all inline-flex items-center gap-1 font-medium"
                      >
                        <span>Inspect</span>
                        <ExternalLink className="w-3 h-3" />
                      </button>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
