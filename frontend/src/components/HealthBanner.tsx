"use client";

import React, { useState } from "react";
import { CheckCircle2, AlertTriangle, RefreshCw, Cpu, Database, Server, ChevronDown, ChevronUp } from "lucide-react";

interface HealthData {
  status?: string;
  timestamp?: string;
  service?: string;
  version?: string;
  database?: {
    type?: string;
    status?: string;
  };
  ai_engine?: {
    status?: string;
    base_url?: string;
    target_model?: string;
    model_ready?: boolean;
    installed_models?: string[];
    hint?: string;
  };
}

interface HealthBannerProps {
  health: HealthData | null;
  loading: boolean;
  onRefresh: () => void;
}

export default function HealthBanner({ health, loading, onRefresh }: HealthBannerProps) {
  const [showDetails, setShowDetails] = useState(false);

  const isHealthy = health?.status === "healthy";
  const isDbConnected = health?.database?.status === "connected";
  const isAiReady = health?.ai_engine?.model_ready === true;

  return (
    <div className="rounded-xl bg-slate-900/60 border border-slate-800/80 p-4 shadow-sm">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div
            className={`w-3 h-3 rounded-full shrink-0 ${
              isHealthy ? "bg-emerald-500 shadow-md shadow-emerald-500/50" : "bg-amber-500 animate-pulse"
            }`}
          />
          <div>
            <div className="flex items-center gap-2">
              <h4 className="text-xs font-semibold text-white">Full-Stack System Diagnostic</h4>
              <span
                className={`text-[10px] font-bold px-1.5 py-0.5 rounded uppercase ${
                  isHealthy
                    ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                    : "bg-amber-500/10 text-amber-400 border border-amber-500/20"
                }`}
              >
                {health?.status ?? "Connecting"}
              </span>
            </div>
            <p className="text-[11px] text-slate-400 mt-0.5">
              Local FastAPI backend, SQLite database & Ollama (llama3.2:3b) health verification
            </p>
          </div>
        </div>

        {/* Diagnostic Badges */}
        <div className="flex items-center gap-2 text-xs">
          {/* FastAPI Badge */}
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-slate-800/70 border border-slate-700/60 text-slate-300">
            <Server className="w-3 h-3 text-cyan-400" />
            <span>FastAPI:</span>
            <span className={health ? "text-emerald-400 font-semibold" : "text-amber-400"}>
              {health ? "Online" : "Checking"}
            </span>
          </div>

          {/* SQLite Badge */}
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-slate-800/70 border border-slate-700/60 text-slate-300">
            <Database className="w-3 h-3 text-emerald-400" />
            <span>SQLite:</span>
            <span className={isDbConnected ? "text-emerald-400 font-semibold" : "text-amber-400"}>
              {isDbConnected ? "Ready" : "Pending"}
            </span>
          </div>

          {/* Ollama AI Badge */}
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-slate-800/70 border border-slate-700/60 text-slate-300">
            <Cpu className="w-3 h-3 text-indigo-400" />
            <span>Ollama:</span>
            <span className={isAiReady ? "text-emerald-400 font-semibold" : "text-amber-400"}>
              {isAiReady ? "llama3.2:3b" : health?.ai_engine?.status ?? "Checking"}
            </span>
          </div>

          <button
            onClick={onRefresh}
            disabled={loading}
            className="p-1.5 rounded-md bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700/60 transition-colors disabled:opacity-50"
            title="Refresh System Health"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin text-emerald-400" : ""}`} />
          </button>

          <button
            onClick={() => setShowDetails(!showDetails)}
            className="p-1.5 rounded-md bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700/60 transition-colors"
            title="Toggle Raw JSON Details"
          >
            {showDetails ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
          </button>
        </div>
      </div>

      {/* Raw Diagnostic JSON Drawer */}
      {showDetails && (
        <div className="mt-3 pt-3 border-t border-slate-800/80">
          <div className="text-[10px] uppercase font-semibold text-slate-400 mb-1">
            Raw Health Payload from FastAPI:
          </div>
          <pre className="p-2.5 rounded bg-slate-950 border border-slate-800 text-[11px] font-mono text-emerald-300 overflow-x-auto">
            {JSON.stringify(health, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
}

