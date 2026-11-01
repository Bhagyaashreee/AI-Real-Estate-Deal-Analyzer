"use client";

import React from "react";
import { Percent, Building2, TrendingUp, IndianRupee, ArrowUpRight } from "lucide-react";

interface KpiData {
  total_deals_analyzed: number;
  average_rental_yield_pct: number;
  undervalued_opportunities: number;
  average_portfolio_ticket_formatted: string;
  top_yielding_city: string;
  benchmark_national_yield_pct: number;
}

interface KpiCardsProps {
  data?: KpiData;
}

export default function KpiCards({ data }: KpiCardsProps) {
  const avgYield = data?.average_rental_yield_pct ?? 4.21;
  const benchmarkYield = data?.benchmark_national_yield_pct ?? 3.25;
  const yieldDelta = (avgYield - benchmarkYield).toFixed(2);
  const totalDeals = data?.total_deals_analyzed ?? 5;
  const undervaluedDeals = data?.undervalued_opportunities ?? 3;
  const avgTicket = data?.average_portfolio_ticket_formatted ?? "₹1.82 Cr";

  const cards = [
    {
      title: "Average Gross Rental Yield",
      value: `${avgYield}%`,
      subtitle: `+${yieldDelta}% vs India Benchmark (${benchmarkYield}%)`,
      icon: Percent,
      accent: "text-emerald-400",
      badgeColor: "bg-emerald-500/10 text-emerald-300 border-emerald-500/20",
    },
    {
      title: "Deals Analyzed",
      value: `${totalDeals}`,
      subtitle: "Across Bangalore, Mumbai, Pune & HYD",
      icon: Building2,
      accent: "text-cyan-400",
      badgeColor: "bg-cyan-500/10 text-cyan-300 border-cyan-500/20",
    },
    {
      title: "Undervalued Opportunities",
      value: `${undervaluedDeals} Deals`,
      subtitle: "Positive cash flow & high yield spread",
      icon: TrendingUp,
      accent: "text-emerald-400",
      badgeColor: "bg-emerald-500/10 text-emerald-300 border-emerald-500/20",
    },
    {
      title: "Average Portfolio Ticket",
      value: avgTicket,
      subtitle: `Top yielding micro-market: ${data?.top_yielding_city ?? "Pune"}`,
      icon: IndianRupee,
      accent: "text-indigo-400",
      badgeColor: "bg-indigo-500/10 text-indigo-300 border-indigo-500/20",
    },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
      {cards.map((card, idx) => {
        const Icon = card.icon;
        return (
          <div
            key={idx}
            className="rounded-xl bg-slate-900/70 border border-slate-800/80 p-4 hover:border-slate-700/80 transition-all shadow-sm"
          >
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-medium text-slate-400">{card.title}</span>
              <div className="p-2 rounded-lg bg-slate-800/60 border border-slate-700/50">
                <Icon className={`w-4 h-4 ${card.accent}`} />
              </div>
            </div>
            <div className="flex items-baseline justify-between">
              <div className="text-2xl font-bold tracking-tight text-white">{card.value}</div>
              <ArrowUpRight className="w-4 h-4 text-slate-400" />
            </div>
            <div className="mt-2 text-[11px] text-slate-400 flex items-center gap-1.5">
              <span>{card.subtitle}</span>
            </div>
          </div>
        );
      })}
    </div>
  );
}

