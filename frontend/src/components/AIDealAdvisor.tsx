"use client";

import React, { useState, useEffect, useRef } from "react";
import {
  Sparkles,
  Bot,
  Send,
  ShieldCheck,
  AlertTriangle,
  CheckCircle2,
  Info,
  RefreshCw,
  Trash2,
  Landmark,
  IndianRupee,
  TrendingUp,
  Percent,
  Layers,
  ChevronDown,
  ChevronUp,
  MessageSquare,
  Building2,
  FileText,
} from "lucide-react";
import { PropertyDeal } from "./DealsTable";

interface AIDealAdvisorProps {
  apiBase: string;
  property: PropertyDeal | null;
  financialAnalysis: any;
}

export default function AIDealAdvisor({
  apiBase,
  property,
  financialAnalysis,
}: AIDealAdvisorProps) {
  // AI Status
  const [aiStatus, setAiStatus] = useState<any>(null);
  const [checkingStatus, setCheckingStatus] = useState(false);

  // Structured Analysis State
  const [analysis, setAnalysis] = useState<any>(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [analysisError, setAnalysisError] = useState<string | null>(null);

  // Chat State
  const [messages, setMessages] = useState<Array<{ role: string; content: string }>>([]);
  const [inputMessage, setInputMessage] = useState("");
  const [sendingChat, setSendingChat] = useState(false);
  const chatBottomRef = useRef<HTMLDivElement>(null);

  // Fetch AI status
  const checkStatus = async () => {
    setCheckingStatus(true);
    try {
      const res = await fetch(`${apiBase}/api/v1/ai/status`, { cache: "no-store" });
      if (res.ok) {
        const data = await res.json();
        setAiStatus(data);
      } else {
        setAiStatus(null);
      }
    } catch {
      setAiStatus(null);
    } finally {
      setCheckingStatus(false);
    }
  };

  useEffect(() => {
    checkStatus();
  }, [apiBase]);

  // Reset analysis when selected property changes
  useEffect(() => {
    setAnalysis(null);
    setAnalysisError(null);
    setMessages([
      {
        role: "assistant",
        content: property
          ? `Hello! I am your local AI Deal Advisor. I have loaded the deterministic financial metrics for **${property.title}** in ${property.locality}, ${property.city}. Ask me any question about its yields, cash flow, debt burden, or risk profile.`
          : "Select a property to start AI investment advisory.",
      },
    ]);
  }, [property?.id]);

  // Scroll to bottom of chat
  useEffect(() => {
    chatBottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, sendingChat]);

  // Run Structured AI Analysis
  const runAIAnalysis = async () => {
    if (!property) return;
    setAnalyzing(true);
    setAnalysisError(null);

    try {
      const res = await fetch(`${apiBase}/api/v1/ai/analyze/${property.id}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
      });

      if (res.ok) {
        const data = await res.json();
        setAnalysis(data);
      } else {
        const err = await res.json();
        setAnalysisError(
          err.detail || `AI analysis failed with HTTP ${res.status}. Ensure Ollama is running.`
        );
      }
    } catch (e: any) {
      setAnalysisError(
        "Could not connect to backend AI service. Ensure Ollama is running locally via `ollama serve`."
      );
    } finally {
      setAnalyzing(false);
    }
  };

  // Send message to Property AI Chat
  const handleSendMessage = async (textToSend?: string) => {
    const query = (textToSend || inputMessage).trim();
    if (!query || !property || sendingChat) return;

    const newHistory = [...messages, { role: "user", content: query }];
    setMessages(newHistory);
    setInputMessage("");
    setSendingChat(true);

    try {
      const res = await fetch(`${apiBase}/api/v1/ai/chat/${property.id}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: query,
          history: newHistory.filter((m) => m.role !== "system"),
        }),
      });

      if (res.ok) {
        const data = await res.json();
        setMessages((prev) => [
          ...prev,
          { role: "assistant", content: data.response },
        ]);
      } else {
        const err = await res.json();
        setMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            content: `⚠️ Error from AI assistant: ${err.detail || "Inference failed."}`,
          },
        ]);
      }
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: "⚠️ Failed to reach local AI service. Verify that Ollama is running locally.",
        },
      ]);
    } finally {
      setSendingChat(false);
    }
  };

  if (!property) {
    return (
      <div className="rounded-xl bg-slate-900/60 border border-slate-800 p-8 text-center text-slate-400">
        <Building2 className="w-10 h-10 mx-auto text-slate-600 mb-3" />
        <p className="text-sm">Please select a property to activate the AI Deal Advisor.</p>
      </div>
    );
  }

  const isOllamaOnline = aiStatus?.status === "online" && aiStatus?.inference_ready;

  return (
    <div className="space-y-6">
      {/* AI Header & Local Daemon Status Bar */}
      <div className="rounded-xl bg-slate-900/80 border border-slate-800/90 p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4 shadow-sm">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
            <Sparkles className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-sm font-bold text-white">Local AI Investment Advisor</h3>
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-indigo-500/10 text-indigo-300 border border-indigo-500/20 font-mono">
                llama3.2:3b
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              100% Free & Local • Deterministic Grounding • Zero Cloud APIs
            </p>
          </div>
        </div>

        {/* AI Daemon Status Pill */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-950 border border-slate-800 text-xs">
            <span
              className={`h-2 w-2 rounded-full ${
                isOllamaOnline ? "bg-emerald-500 animate-pulse" : "bg-rose-500"
              }`}
            />
            <span className="text-slate-300">
              {checkingStatus
                ? "Checking Ollama..."
                : isOllamaOnline
                ? "Ollama Ready"
                : "Ollama Offline"}
            </span>
          </div>

          <button
            onClick={checkStatus}
            disabled={checkingStatus}
            title="Refresh AI Status"
            className="p-2 rounded-lg bg-slate-800/80 hover:bg-slate-700 text-slate-300 border border-slate-700/60 transition-colors"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${checkingStatus ? "animate-spin" : ""}`} />
          </button>
        </div>
      </div>

      {/* Ollama Offline Warning Banner */}
      {!isOllamaOnline && !checkingStatus && (
        <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-300 text-xs flex items-start gap-3">
          <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
          <div>
            <span className="font-semibold block">Local Ollama Service Unavailable</span>
            <p className="text-amber-300/80 mt-0.5">
              Ensure Ollama is running locally on port 11434 with `llama3.2:3b`. You can start it in
              PowerShell using <code className="bg-slate-900 px-1 py-0.5 rounded font-mono">ollama serve</code> and verify with <code className="bg-slate-900 px-1 py-0.5 rounded font-mono">ollama list</code>.
            </p>
          </div>
        </div>
      )}

      {/* Main Grid: Structured Analysis (Left 2 cols) & Live Chat (Right 1 col) */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Structured AI Report */}
        <div className="lg:col-span-2 space-y-6">
          {/* Action Trigger Card */}
          <div className="rounded-xl bg-slate-900/70 border border-slate-800/80 p-5 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <h4 className="text-sm font-semibold text-white">Automated Deal Interpretation</h4>
              <p className="text-xs text-slate-400 mt-1">
                Generate an objective executive summary, investment verdict, and risk analysis grounded in
                the deterministic financial formulas.
              </p>
            </div>

            <button
              onClick={runAIAnalysis}
              disabled={analyzing || !isOllamaOnline}
              className={`px-4 py-2.5 rounded-lg text-xs font-semibold flex items-center justify-center gap-2 transition-all ${
                analyzing || !isOllamaOnline
                  ? "bg-slate-800 text-slate-500 cursor-not-allowed border border-slate-700/50"
                  : "bg-gradient-to-r from-emerald-600 to-teal-500 hover:from-emerald-500 hover:to-teal-400 text-slate-950 font-bold shadow-lg shadow-emerald-500/20"
              }`}
            >
              <Sparkles className={`w-4 h-4 ${analyzing ? "animate-spin" : ""}`} />
              <span>{analyzing ? "Analyzing with llama3.2:3b..." : "Generate AI Analysis"}</span>
            </button>
          </div>

          {/* Analysis Error Message */}
          {analysisError && (
            <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 shrink-0" />
              <span>{analysisError}</span>
            </div>
          )}

          {/* Analysis Loading State */}
          {analyzing && (
            <div className="rounded-xl bg-slate-900/80 border border-slate-800/90 p-8 text-center space-y-4">
              <div className="w-10 h-10 mx-auto rounded-full bg-indigo-500/10 border border-indigo-500/30 flex items-center justify-center animate-spin">
                <Sparkles className="w-5 h-5 text-indigo-400" />
              </div>
              <div className="space-y-1">
                <p className="text-sm font-semibold text-white">
                  Local Ollama LLM is Evaluating Investment Deal...
                </p>
                <p className="text-xs text-slate-400 max-w-md mx-auto">
                  Interpreting gross/net yields, reducing-balance debt burden, and sensitivity stress scenarios using llama3.2:3b on CPU.
                </p>
              </div>
            </div>
          )}

          {/* Structured Analysis Result View */}
          {analysis && !analyzing && (
            <div className="space-y-5">
              {/* Verdict & Executive Summary */}
              <div className="rounded-xl bg-slate-900/80 border border-slate-800/80 p-5 shadow-sm space-y-4">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-3 border-b border-slate-800/70 gap-2">
                  <div className="flex items-center gap-2">
                    <ShieldCheck className="w-4 h-4 text-emerald-400" />
                    <h3 className="text-sm font-semibold text-white">Investment Verdict</h3>
                  </div>
                  <span
                    className={`px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider inline-block border ${
                      analysis.verdict === "Strong Potential"
                        ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                        : analysis.verdict === "Potential with Caution"
                        ? "bg-cyan-500/10 text-cyan-400 border-cyan-500/20"
                        : analysis.verdict === "Weak Investment"
                        ? "bg-amber-500/10 text-amber-400 border-amber-500/20"
                        : "bg-rose-500/10 text-rose-400 border-rose-500/20"
                    }`}
                  >
                    {analysis.verdict}
                  </span>
                </div>

                <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800/80">
                  <p className="text-xs font-semibold text-slate-200">
                    {analysis.verdict_rationale}
                  </p>
                </div>

                <div className="space-y-1 text-xs text-slate-300">
                  <span className="font-semibold text-white block">Executive Summary:</span>
                  <p className="leading-relaxed text-slate-300">{analysis.executive_summary}</p>
                </div>
              </div>

              {/* Strengths & Weaknesses Grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Strengths */}
                <div className="p-4 rounded-xl bg-emerald-950/20 border border-emerald-800/40 space-y-2.5">
                  <span className="text-xs font-semibold text-emerald-400 flex items-center gap-1.5 uppercase tracking-wider">
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    Investment Strengths ({analysis.investment_strengths.length})
                  </span>
                  <ul className="space-y-1.5 text-xs text-slate-300">
                    {analysis.investment_strengths.map((s: string, idx: number) => (
                      <li key={idx} className="flex items-start gap-2">
                        <span className="text-emerald-400 font-bold">&bull;</span>
                        <span>{s}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                {/* Weaknesses */}
                <div className="p-4 rounded-xl bg-rose-950/20 border border-rose-800/40 space-y-2.5">
                  <span className="text-xs font-semibold text-rose-400 flex items-center gap-1.5 uppercase tracking-wider">
                    <AlertTriangle className="w-3.5 h-3.5" />
                    Investment Bottlenecks ({analysis.investment_weaknesses.length})
                  </span>
                  <ul className="space-y-1.5 text-xs text-slate-300">
                    {analysis.investment_weaknesses.map((w: string, idx: number) => (
                      <li key={idx} className="flex items-start gap-2">
                        <span className="text-rose-400 font-bold">&bull;</span>
                        <span>{w}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>

              {/* 3-Tier Risk Analysis */}
              <div className="rounded-xl bg-slate-900/80 border border-slate-800/80 p-5 shadow-sm space-y-4">
                <div className="flex items-center gap-2 pb-3 border-b border-slate-800/70">
                  <AlertTriangle className="w-4 h-4 text-amber-400" />
                  <h3 className="text-sm font-semibold text-white">Three-Tier Risk Architecture</h3>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs">
                  {/* Category A */}
                  <div className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800/80 space-y-2">
                    <span className="text-[11px] font-bold text-amber-400 block uppercase tracking-wider">
                      A. Numerical Calculation Risks
                    </span>
                    <ul className="space-y-1 text-slate-300">
                      {analysis.risks.calculated_risks.map((r: string, i: number) => (
                        <li key={i} className="flex items-start gap-1.5">
                          <span className="text-amber-400">&bull;</span>
                          <span>{r}</span>
                        </li>
                      ))}
                    </ul>
                  </div>

                  {/* Category B */}
                  <div className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800/80 space-y-2">
                    <span className="text-[11px] font-bold text-cyan-400 block uppercase tracking-wider">
                      B. Information Gap Risks
                    </span>
                    <ul className="space-y-1 text-slate-300">
                      {analysis.risks.information_gap_risks.map((r: string, i: number) => (
                        <li key={i} className="flex items-start gap-1.5">
                          <span className="text-cyan-400">&bull;</span>
                          <span>{r}</span>
                        </li>
                      ))}
                    </ul>
                  </div>

                  {/* Category C */}
                  <div className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800/80 space-y-2">
                    <span className="text-[11px] font-bold text-rose-400 block uppercase tracking-wider">
                      C. External Verification Required
                    </span>
                    <ul className="space-y-1 text-slate-300">
                      {analysis.risks.external_verification_required.map((r: string, i: number) => (
                        <li key={i} className="flex items-start gap-1.5">
                          <span className="text-rose-400">&bull;</span>
                          <span>{r}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              </div>

              {/* Analytical Perspectives */}
              <div className="rounded-xl bg-slate-900/80 border border-slate-800/80 p-5 shadow-sm space-y-3.5 text-xs text-slate-300">
                <span className="text-xs font-semibold text-white uppercase tracking-wider block pb-2 border-b border-slate-800">
                  Analytical Deep-Dive
                </span>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">
                  <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800/80">
                    <span className="font-semibold text-cyan-400 block mb-1">Rental Yield Analysis</span>
                    <p>{analysis.rental_income_analysis}</p>
                  </div>
                  <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800/80">
                    <span className="font-semibold text-amber-400 block mb-1">Loan & Debt Burden</span>
                    <p>{analysis.loan_burden_analysis}</p>
                  </div>
                  <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800/80">
                    <span className="font-semibold text-indigo-400 block mb-1">Cash Flow & Break-Even</span>
                    <p>{analysis.cash_flow_interpretation}</p>
                  </div>
                  <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800/80">
                    <span className="font-semibold text-emerald-400 block mb-1">Stress Test Interpretation</span>
                    <p>{analysis.scenario_analysis_summary}</p>
                  </div>
                </div>
              </div>

              {/* Recommendations & Disclaimers */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800/80 space-y-2">
                  <span className="text-xs font-semibold text-white uppercase tracking-wider block">
                    Investor Action Items
                  </span>
                  <ul className="space-y-1.5 text-xs text-slate-300">
                    {analysis.recommendations.map((rec: string, i: number) => (
                      <li key={i} className="flex items-start gap-1.5">
                        <span className="text-emerald-400 font-bold">&bull;</span>
                        <span>{rec}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800/80 space-y-2">
                  <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block">
                    Important Disclaimers
                  </span>
                  <ul className="space-y-1.5 text-[11px] text-slate-400">
                    {analysis.disclaimers.map((d: string, i: number) => (
                      <li key={i} className="flex items-start gap-1.5">
                        <span className="text-slate-500">&bull;</span>
                        <span>{d}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Right Column: Grounded AI Chat Assistant */}
        <div className="space-y-4">
          <div className="rounded-xl bg-slate-900/90 border border-slate-800/90 flex flex-col h-[740px] shadow-sm overflow-hidden">
            {/* Chat Top Bar */}
            <div className="p-3.5 border-b border-slate-800 flex items-center justify-between bg-slate-950/60">
              <div className="flex items-center gap-2">
                <Bot className="w-4 h-4 text-emerald-400" />
                <div>
                  <span className="text-xs font-bold text-white block">Property AI Chat</span>
                  <span className="text-[10px] text-slate-400 truncate max-w-[180px] block">
                    {property.locality}, {property.city}
                  </span>
                </div>
              </div>

              <button
                onClick={() =>
                  setMessages([
                    {
                      role: "assistant",
                      content: `Conversation reset. I am ready to answer queries for ${property.title}.`,
                    },
                  ])
                }
                title="Clear Chat History"
                className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-slate-200 text-xs transition-colors"
              >
                <Trash2 className="w-3.5 h-3.5" />
              </button>
            </div>

            {/* Chat Message Stream */}
            <div className="flex-1 p-3.5 overflow-y-auto space-y-3 text-xs">
              {messages.map((m, idx) => {
                const isUser = m.role === "user";
                return (
                  <div
                    key={idx}
                    className={`flex flex-col ${isUser ? "items-end" : "items-start"}`}
                  >
                    <span className="text-[10px] text-slate-400 mb-1 px-1">
                      {isUser ? "You" : "Deal Advisor (llama3.2:3b)"}
                    </span>
                    <div
                      className={`p-3 rounded-2xl max-w-[90%] leading-relaxed ${
                        isUser
                          ? "bg-emerald-600 text-slate-950 font-medium rounded-tr-none"
                          : "bg-slate-950 border border-slate-800 text-slate-200 rounded-tl-none whitespace-pre-line"
                      }`}
                    >
                      {m.content}
                    </div>
                  </div>
                );
              })}

              {sendingChat && (
                <div className="flex items-start gap-2">
                  <div className="p-3 rounded-2xl rounded-tl-none bg-slate-950 border border-slate-800 text-slate-400 text-xs flex items-center gap-2">
                    <span className="h-2 w-2 rounded-full bg-emerald-400 animate-ping" />
                    <span>Thinking locally...</span>
                  </div>
                </div>
              )}
              <div ref={chatBottomRef} />
            </div>

            {/* Quick Prompt Pills */}
            <div className="p-2 border-t border-slate-800/80 bg-slate-950/40 space-y-1.5">
              <span className="text-[10px] text-slate-400 px-1 block">Suggested Queries:</span>
              <div className="flex flex-wrap gap-1.5">
                {[
                  "Why is the cash flow at this level?",
                  "What if interest rate increases by 1%?",
                  "Is this suitable for a first-time investor?",
                  "Explain the rental yield benchmark.",
                ].map((promptText, i) => (
                  <button
                    key={i}
                    disabled={sendingChat || !isOllamaOnline}
                    onClick={() => handleSendMessage(promptText)}
                    className="text-[11px] px-2 py-1 rounded bg-slate-800/70 hover:bg-emerald-500/10 hover:text-emerald-300 hover:border-emerald-500/30 border border-slate-700/60 text-slate-300 text-left transition-colors truncate max-w-full"
                  >
                    {promptText}
                  </button>
                ))}
              </div>
            </div>

            {/* Chat Input Footer */}
            <div className="p-3 border-t border-slate-800 bg-slate-950/80 flex items-center gap-2">
              <input
                type="text"
                placeholder={
                  isOllamaOnline
                    ? "Ask about yields, cash flow, debt burden..."
                    : "Ollama is currently offline..."
                }
                disabled={!isOllamaOnline || sendingChat}
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") handleSendMessage();
                }}
                className="flex-1 bg-slate-900 border border-slate-700/80 rounded-lg px-3 py-2 text-xs text-white placeholder-slate-400 focus:outline-none focus:border-emerald-500 disabled:opacity-50"
              />
              <button
                disabled={!inputMessage.trim() || sendingChat || !isOllamaOnline}
                onClick={() => handleSendMessage()}
                className="p-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 disabled:bg-slate-800 disabled:text-slate-600 text-slate-950 transition-colors font-bold"
              >
                <Send className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

