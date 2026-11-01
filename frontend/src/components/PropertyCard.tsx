"use client";

import React from "react";
import { Building2, MapPin, Bed, Bath, Maximize2, Percent, IndianRupee, Sparkles, ExternalLink, Edit2, Trash2 } from "lucide-react";
import { PropertyDeal } from "./DealsTable";

interface PropertyCardProps {
  property: PropertyDeal;
  onViewDetails: (property: PropertyDeal) => void;
  onEdit: (property: PropertyDeal) => void;
  onDelete: (id: number) => void;
}

export default function PropertyCard({ property, onViewDetails, onEdit, onDelete }: PropertyCardProps) {
  const isUndervalued = property.valuation_status === "Undervalued";
  const isOverpriced = property.valuation_status === "Overpriced";

  // City-specific thematic gradient for visual polish
  const getCityGradient = (city: string) => {
    switch (city.toLowerCase()) {
      case "hyderabad":
        return "from-cyan-950/70 via-slate-900 to-slate-950";
      case "bengaluru":
        return "from-emerald-950/70 via-slate-900 to-slate-950";
      case "mumbai":
        return "from-blue-950/70 via-slate-900 to-slate-950";
      case "pune":
        return "from-purple-950/70 via-slate-900 to-slate-950";
      case "chennai":
        return "from-amber-950/70 via-slate-900 to-slate-950";
      default:
        return "from-teal-950/70 via-slate-900 to-slate-950";
    }
  };

  return (
    <div className="rounded-xl bg-slate-900/80 border border-slate-800/80 hover:border-slate-700/80 transition-all shadow-sm overflow-hidden flex flex-col justify-between group">
      <div>
        {/* Card Header & Visual Placeholder */}
        <div className={`p-4 bg-gradient-to-br ${getCityGradient(property.city)} border-b border-slate-800/60 relative`}>
          <div className="flex items-center justify-between gap-2 mb-2">
            <span className="text-[10px] font-bold uppercase px-2 py-0.5 rounded bg-slate-800/90 text-slate-300 border border-slate-700/60">
              {property.property_type || "Apartment"}
            </span>

            <div className="flex items-center gap-1.5">
              {(property as any).is_demo && (
                <span className="text-[9px] font-bold uppercase px-1.5 py-0.5 rounded bg-amber-500/10 text-amber-400 border border-amber-500/20">
                  DEMO DATA
                </span>
              )}
              <span
                className={`text-[10px] font-bold uppercase px-2 py-0.5 rounded border ${
                  isUndervalued
                    ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                    : isOverpriced
                    ? "bg-rose-500/10 text-rose-400 border-rose-500/20"
                    : "bg-amber-500/10 text-amber-400 border-amber-500/20"
                }`}
              >
                {property.valuation_status}
              </span>
            </div>
          </div>

          <h3 className="font-semibold text-sm text-white line-clamp-1 group-hover:text-emerald-300 transition-colors">
            {property.title}
          </h3>

          <div className="flex items-center gap-1.5 text-xs text-slate-400 mt-1">
            <MapPin className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
            <span className="truncate">
              {property.locality}, {property.city}
              {(property as any).state ? `, ${(property as any).state}` : ""}
            </span>
          </div>
        </div>

        {/* Pricing & Key Metrics Row */}
        <div className="p-4 space-y-3">
          <div className="flex items-baseline justify-between">
            <div>
              <span className="text-[11px] text-slate-400">Purchase Price</span>
              <div className="text-lg font-bold text-white tracking-tight">
                {property.price_formatted}
              </div>
            </div>
            <div className="text-right">
              <span className="text-[11px] text-slate-400">Price/sq.ft</span>
              <div className="text-xs font-mono font-medium text-slate-300">
                ₹{property.price_per_sqft?.toLocaleString("en-IN") || "-"}
              </div>
            </div>
          </div>

          {/* Rental & Yield Metrics */}
          <div className="grid grid-cols-2 gap-2 p-2.5 rounded-lg bg-slate-950/60 border border-slate-800/80 text-xs">
            <div>
              <span className="text-[10px] text-slate-400 block">Expected Rent</span>
              <span className="font-semibold text-emerald-400 font-mono">
                {property.rent_formatted}
              </span>
            </div>
            <div>
              <span className="text-[10px] text-slate-400 block">Gross Yield</span>
              <span
                className={`font-bold flex items-center gap-1 ${
                  property.gross_rental_yield_pct != null
                    ? property.gross_rental_yield_pct >= 4.0
                      ? "text-emerald-400"
                      : property.gross_rental_yield_pct >= 3.25
                      ? "text-cyan-400"
                      : "text-rose-400"
                    : "text-slate-400"
                }`}
              >
                <Percent className="w-3 h-3" />
                {property.gross_rental_yield_pct != null ? `${property.gross_rental_yield_pct}%` : "N/A"}
              </span>
            </div>
          </div>

          {/* Configuration badges */}
          <div className="flex items-center justify-between text-xs text-slate-400 pt-1">
            <div className="flex items-center gap-3">
              <span className="flex items-center gap-1">
                <Bed className="w-3.5 h-3.5 text-slate-400" />
                {property.bhk} BHK
              </span>
              <span className="flex items-center gap-1">
                <Bath className="w-3.5 h-3.5 text-slate-400" />
                {(property as any).bathrooms || 1} Bath
              </span>
              <span className="flex items-center gap-1">
                <Maximize2 className="w-3.5 h-3.5 text-slate-400" />
                {property.area_sqft} sq.ft
              </span>
            </div>
            <div className="flex items-center gap-1 text-[11px] font-bold text-indigo-300 bg-indigo-500/10 px-1.5 py-0.5 rounded border border-indigo-500/20">
              <Sparkles className="w-2.5 h-2.5" />
              Score {property.ai_investment_score}
            </div>
          </div>
        </div>
      </div>

      {/* Card Actions Footer */}
      <div className="p-3 bg-slate-950/50 border-t border-slate-800/60 flex items-center justify-between text-xs">
        <button
          onClick={() => onViewDetails(property)}
          className="text-xs px-2.5 py-1 rounded bg-slate-800/80 hover:bg-emerald-500/20 hover:text-emerald-300 hover:border-emerald-500/30 border border-slate-700/60 text-slate-300 transition-colors inline-flex items-center gap-1"
        >
          <span>View Details</span>
          <ExternalLink className="w-3 h-3" />
        </button>

        <div className="flex items-center gap-1">
          <button
            onClick={() => onEdit(property)}
            title="Edit Property"
            className="p-1.5 rounded hover:bg-slate-800 text-slate-400 hover:text-slate-200 transition-colors"
          >
            <Edit2 className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={() => onDelete(property.id)}
            title="Delete Property"
            className="p-1.5 rounded hover:bg-rose-500/10 text-slate-400 hover:text-rose-400 transition-colors"
          >
            <Trash2 className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    </div>
  );
}

