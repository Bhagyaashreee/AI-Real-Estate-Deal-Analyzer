"use client";

import React from "react";
import {
  LayoutDashboard,
  Building2,
  Calculator,
  Search,
  Scale,
  FileText,
  TrendingUp,
  Settings,
  Sparkles,
  Database,
  ShieldCheck,
  ShieldAlert,
} from "lucide-react";

interface SidebarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
}

export default function Sidebar({ activeTab, setActiveTab }: SidebarProps) {
  const navItems = [
    { id: "dashboard", label: "Dashboard", icon: LayoutDashboard },
    { id: "properties", label: "Properties & Ingestion", icon: Building2, badge: "Phase 2" },
    { id: "analysis", label: "Financial Analysis", icon: Calculator, badge: "Phase 3" },
    { id: "ai-advisor", label: "AI Deal Advisor", icon: Sparkles, badge: "Phase 4" },
    { id: "risk-intelligence", label: "Risk & Benchmarks", icon: ShieldAlert, badge: "Phase 5" },
    { id: "screener", label: "Property Screener", icon: Search },
    { id: "compare", label: "Compare Deals", icon: Scale },
    { id: "reports", label: "Investment Reports", icon: FileText, badge: "Phase 6" },
    { id: "trends", label: "City Benchmarks", icon: TrendingUp },
    { id: "settings", label: "Settings", icon: Settings },
  ];

  return (
    <aside className="w-64 border-r border-slate-800/80 bg-[#0B1120]/90 backdrop-blur-md flex flex-col justify-between p-4 shrink-0 h-screen sticky top-0">
      <div>
        {/* Brand Logo & Title */}
        <div className="flex items-center gap-3 px-2 py-3 mb-6">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-emerald-600 to-teal-400 flex items-center justify-center shadow-lg shadow-emerald-500/20">
            <Sparkles className="w-5 h-5 text-slate-950 font-bold" />
          </div>
          <div>
            <div className="flex items-center gap-1.5">
              <span className="font-bold text-base tracking-tight text-white">PropDeal</span>
              <span className="text-xs font-semibold px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                AI INDIA
              </span>
            </div>
            <p className="text-[11px] text-slate-400">Real Estate Deal Intelligence</p>
          </div>
        </div>

        {/* Navigation Section */}
        <nav className="space-y-1">
          <div className="px-2 pb-2 text-[10px] font-semibold uppercase tracking-wider text-slate-400">
            Core Modules
          </div>
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`w-full flex items-center justify-between px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-150 ${
                  isActive
                    ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 shadow-sm"
                    : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
                }`}
              >
                <div className="flex items-center gap-3">
                  <Icon className={`w-4 h-4 ${isActive ? "text-emerald-400" : "text-slate-400"}`} />
                  <span>{item.label}</span>
                </div>
                {item.badge && (
                  <span className="text-[10px] uppercase font-bold px-1.5 py-0.5 rounded bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                    {item.badge}
                  </span>
                )}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Local Environment & Privacy Badge */}
      <div className="rounded-xl bg-slate-900/80 border border-slate-800/90 p-3.5 space-y-2.5">
        <div className="flex items-center justify-between text-xs">
          <span className="text-slate-400 flex items-center gap-1.5 font-medium">
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
            100% Free & Local
          </span>
          <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
        </div>
        <div className="space-y-1 text-[11px] text-slate-400">
          <div className="flex justify-between items-center">
            <span>AI Model:</span>
            <span className="text-slate-200 font-mono text-[10px] bg-slate-800 px-1.5 py-0.5 rounded">
              llama3.2:3b
            </span>
          </div>
          <div className="flex justify-between items-center">
            <span>Database:</span>
            <span className="text-slate-200 font-mono text-[10px] bg-slate-800 px-1.5 py-0.5 rounded flex items-center gap-1">
              <Database className="w-2.5 h-2.5 text-cyan-400" /> SQLite
            </span>
          </div>
          <div className="flex justify-between items-center">
            <span>Currency:</span>
            <span className="text-emerald-400 font-medium">INR (₹)</span>
          </div>
        </div>
      </div>
    </aside>
  );
}

