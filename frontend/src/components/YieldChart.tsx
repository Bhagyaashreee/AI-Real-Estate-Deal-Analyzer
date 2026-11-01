"use client";

import React, { useState, useEffect } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
  Cell,
} from "recharts";
import { BarChart3, TrendingUp, Sparkles } from "lucide-react";

const chartData = [
  { locality: "Hinjewadi (Pune)", yieldPct: 4.98, rent: "₹34k/mo", status: "Undervalued" },
  { locality: "Gachibowli (HYD)", yieldPct: 4.80, rent: "₹78k/mo", status: "Undervalued" },
  { locality: "Whitefield (BLR)", yieldPct: 4.30, rent: "₹52k/mo", status: "Undervalued" },
  { locality: "Sec 54 (Gurugram)", yieldPct: 3.71, rent: "₹65k/mo", status: "Fair Value" },
  { locality: "Bandra W (Mumbai)", yieldPct: 2.78, rent: "₹88k/mo", status: "Overpriced" },
];

export default function YieldChart() {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    return (
      <div className="h-72 w-full bg-slate-900/60 rounded-xl border border-slate-800 flex items-center justify-center text-slate-400 text-xs">
        Loading analytics engine...
      </div>
    );
  }

  return (
    <div className="rounded-xl bg-slate-900/70 border border-slate-800/80 p-5 shadow-sm">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-slate-800/60 gap-2">
        <div>
          <div className="flex items-center gap-2">
            <BarChart3 className="w-4 h-4 text-emerald-400" />
            <h3 className="text-sm font-semibold text-white">Micro-market Rental Yields vs Indian Benchmark</h3>
          </div>
          <p className="text-xs text-slate-400 mt-0.5">
            Gross annual rental return (%) across analyzed Indian commercial & residential hubs
          </p>
        </div>
        <div className="flex items-center gap-2 text-xs">
          <span className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-emerald-500/10 text-emerald-300 border border-emerald-500/20 font-medium">
            <Sparkles className="w-3 h-3" />
            Benchmark: 3.25%
          </span>
        </div>
      </div>

      <div className="h-64 w-full mt-4">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
            <XAxis
              dataKey="locality"
              tick={{ fill: "#94a3b8", fontSize: 11 }}
              axisLine={{ stroke: "#334155" }}
              tickLine={false}
            />
            <YAxis
              tick={{ fill: "#94a3b8", fontSize: 11 }}
              axisLine={{ stroke: "#334155" }}
              tickLine={false}
              unit="%"
              domain={[0, 6]}
            />
            <Tooltip
              content={({ active, payload }) => {
                if (active && payload && payload.length) {
                  const data = payload[0].payload;
                  return (
                    <div className="bg-slate-950/95 border border-slate-800 p-2.5 rounded-lg shadow-xl text-xs">
                      <p className="font-semibold text-white">{data.locality}</p>
                      <p className="text-emerald-400 font-medium mt-1">
                        Gross Yield: <span className="font-bold">{data.yieldPct}%</span>
                      </p>
                      <p className="text-slate-400">Est. Rent: {data.rent}</p>
                      <p className="text-slate-400 mt-0.5">
                        Valuation:{" "}
                        <span
                          className={`font-semibold ${
                            data.status === "Undervalued"
                              ? "text-emerald-400"
                              : data.status === "Overpriced"
                              ? "text-rose-400"
                              : "text-amber-400"
                          }`}
                        >
                          {data.status}
                        </span>
                      </p>
                    </div>
                  );
                }
                return null;
              }}
            />
            <ReferenceLine
              y={3.25}
              stroke="#f59e0b"
              strokeDasharray="4 4"
              label={{
                value: "National Avg 3.25%",
                position: "insideTopRight",
                fill: "#f59e0b",
                fontSize: 10,
              }}
            />
            <Bar dataKey="yieldPct" radius={[6, 6, 0, 0]}>
              {chartData.map((entry, index) => (
                <Cell
                  key={`cell-${index}`}
                  fill={
                    entry.yieldPct >= 4.0
                      ? "#10b981"
                      : entry.yieldPct >= 3.25
                      ? "#06b6d4"
                      : "#f43f5e"
                  }
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="flex items-center justify-between pt-3 border-t border-slate-800/60 text-[11px] text-slate-400">
        <div className="flex items-center gap-4">
          <span className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-sm bg-emerald-500 inline-block" /> High Yield (&gt;4%)
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-sm bg-cyan-500 inline-block" /> Moderate (3.25% - 4%)
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-sm bg-rose-500 inline-block" /> Compressed (&lt;3.25%)
          </span>
        </div>
        <span className="flex items-center gap-1 text-slate-400">
          <TrendingUp className="w-3.5 h-3.5 text-emerald-400" /> Hinjewadi leads at 4.98%
        </span>
      </div>
    </div>
  );
}

