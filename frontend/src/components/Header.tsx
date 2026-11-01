"use client";

import React from "react";
import { Search, Plus, MapPin, Activity, CheckCircle2, AlertCircle } from "lucide-react";

interface HeaderProps {
  selectedCity: string;
  setSelectedCity: (city: string) => void;
  backendOnline: boolean | null;
  onRefreshHealth: () => void;
  onAddProperty?: () => void;
}

export default function Header({
  selectedCity,
  setSelectedCity,
  backendOnline,
  onRefreshHealth,
  onAddProperty,
}: HeaderProps) {
  const cities = ["All Cities", "Bengaluru", "Mumbai", "Pune", "Hyderabad", "Gurugram"];

  return (
    <header className="h-16 border-b border-slate-800/80 bg-[#090D16]/80 backdrop-blur-md px-6 flex items-center justify-between sticky top-0 z-30">
      {/* Search Bar */}
      <div className="flex items-center gap-4 flex-1 max-w-md">
        <div className="relative w-full">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search micro-market (e.g. Whitefield, Bandra, Gachibowli)..."
            className="w-full bg-slate-900/90 border border-slate-800/90 rounded-lg pl-9 pr-4 py-1.5 text-xs text-slate-200 placeholder-slate-400 focus:outline-none focus:border-emerald-500/50 transition-colors"
          />
        </div>
      </div>

      {/* City Selector & System Status */}
      <div className="flex items-center gap-4">
        {/* City Filter Pills */}
        <div className="hidden lg:flex items-center gap-1.5 bg-slate-900/80 border border-slate-800/80 p-1 rounded-lg">
          <MapPin className="w-3.5 h-3.5 text-slate-400 ml-1.5" />
          {cities.map((city) => (
            <button
              key={city}
              onClick={() => setSelectedCity(city)}
              className={`text-xs px-2.5 py-1 rounded-md transition-colors font-medium ${
                selectedCity === city
                  ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              {city}
            </button>
          ))}
        </div>

        {/* Live Backend Connection Status */}
        <button
          onClick={onRefreshHealth}
          title="Click to check FastAPI & Ollama connection"
          className="flex items-center gap-2 px-3 py-1.5 rounded-lg border border-slate-800 bg-slate-900/60 hover:bg-slate-800/80 transition-colors text-xs"
        >
          {backendOnline === true ? (
            <>
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
              </span>
              <span className="text-emerald-400 font-medium">FastAPI Live</span>
            </>
          ) : backendOnline === false ? (
            <>
              <AlertCircle className="w-3.5 h-3.5 text-rose-400" />
              <span className="text-rose-400 font-medium">Backend Offline</span>
            </>
          ) : (
            <>
              <Activity className="w-3.5 h-3.5 text-amber-400 animate-spin" />
              <span className="text-amber-400 font-medium">Connecting...</span>
            </>
          )}
        </button>

        {/* Primary Action Button */}
        <button
          onClick={onAddProperty}
          className="flex items-center gap-1.5 bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-400 hover:to-teal-500 text-slate-950 font-semibold px-3.5 py-1.5 rounded-lg text-xs shadow-md shadow-emerald-500/10 transition-all cursor-pointer"
        >
          <Plus className="w-3.5 h-3.5 font-bold" />
          <span>Add / Analyze Deal</span>
        </button>
      </div>
    </header>
  );
}

