"use client";

import React from "react";
import {
  X,
  Building2,
  MapPin,
  Bed,
  Bath,
  Maximize2,
  IndianRupee,
  Percent,
  TrendingUp,
  ShieldCheck,
  Calendar,
  ExternalLink,
  Edit2,
  Trash2,
  Info,
} from "lucide-react";
import { PropertyDeal } from "./DealsTable";

interface PropertyDetailsModalProps {
  property: PropertyDeal | null;
  isOpen: boolean;
  onClose: () => void;
  onEdit?: (property: PropertyDeal) => void;
  onDelete?: (id: number) => void;
}

export default function PropertyDetailsModal({
  property,
  isOpen,
  onClose,
  onEdit,
  onDelete,
}: PropertyDetailsModalProps) {
  if (!isOpen || !property) return null;

  const propAny = property as any;
  const isUndervalued = property.valuation_status === "Undervalued";
  const isOverpriced = property.valuation_status === "Overpriced";

  const monthlyRent = property.estimated_monthly_rent_inr ?? propAny.expected_monthly_rent_inr ?? null;
  const annualRent = monthlyRent != null ? monthlyRent * 12 : null;
  const monthlyMaint = propAny.monthly_maintenance_inr ?? 0;
  const annualMaint = monthlyMaint * 12;
  const cashFlow = property.monthly_cash_flow_inr ?? propAny.estimated_monthly_cash_flow_inr ?? null;
  const hasCashFlow = cashFlow != null && !isNaN(cashFlow);
  const isPositiveCashFlow = hasCashFlow && cashFlow >= 0;

  return (
    <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4 overflow-y-auto">
      <div className="relative w-full max-w-3xl bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl overflow-hidden my-8">
        {/* Modal Top Bar */}
        <div className="p-5 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              <Building2 className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-[10px] font-bold uppercase px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                  {property.property_type || "Apartment"}
                </span>
                {propAny.is_demo && (
                  <span className="text-[10px] font-bold uppercase px-2 py-0.5 rounded bg-amber-500/10 text-amber-400 border border-amber-500/20">
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
              <h2 className="text-base font-semibold text-white mt-1">{property.title}</h2>
              <div className="flex items-center gap-1.5 text-xs text-slate-400 mt-0.5">
                <MapPin className="w-3.5 h-3.5 text-emerald-400" />
                <span>
                  {property.locality}, {property.city}
                  {propAny.state ? `, ${propAny.state}` : ""}
                </span>
              </div>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-1.5 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-white transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Content */}
        <div className="p-6 space-y-5 max-h-[75vh] overflow-y-auto">
          {/* Key Financial Overview Cards */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="p-3.5 rounded-xl bg-slate-950/70 border border-slate-800">
              <span className="text-[11px] text-slate-400">Purchase Price</span>
              <div className="text-lg font-bold text-white mt-0.5">{property.price_formatted}</div>
              <span className="text-[10px] text-slate-500 font-mono">
                ₹{property.price_per_sqft?.toLocaleString("en-IN")}/sq.ft
              </span>
            </div>

            <div className="p-3.5 rounded-xl bg-slate-950/70 border border-slate-800">
              <span className="text-[11px] text-slate-400">Monthly Rent</span>
              <div className="text-lg font-bold text-emerald-400 mt-0.5">{property.rent_formatted}</div>
              <span className="text-[10px] text-slate-500">
                {annualRent != null ? `₹${Math.round(annualRent).toLocaleString("en-IN")}/yr` : "N/A"}
              </span>
            </div>

            <div className="p-3.5 rounded-xl bg-slate-950/70 border border-slate-800">
              <span className="text-[11px] text-slate-400">Gross Rental Yield</span>
              <div className="text-lg font-bold text-cyan-400 mt-0.5">
                {property.gross_rental_yield_pct}%
              </div>
              <span className="text-[10px] text-slate-500">
                Net: {property.net_rental_yield_pct ?? "-"}%
              </span>
            </div>

            <div className="p-3.5 rounded-xl bg-slate-950/70 border border-slate-800">
              <span className="text-[11px] text-slate-400">Monthly Cash Flow</span>
              <div
                className={`text-lg font-bold mt-0.5 ${
                  !hasCashFlow
                    ? "text-slate-500"
                    : cashFlow > 0
                    ? "text-emerald-400"
                    : cashFlow === 0
                    ? "text-slate-300"
                    : "text-rose-400"
                }`}
              >
                {hasCashFlow
                  ? `${cashFlow > 0 ? "+" : cashFlow < 0 ? "-" : ""}₹${Math.abs(Math.round(cashFlow)).toLocaleString("en-IN")}`
                  : "N/A"}
              </div>
              <span className="text-[10px] text-slate-500">Net of maintenance</span>
            </div>
          </div>

          {/* Physical Specifications */}
          <div className="rounded-xl bg-slate-950/50 border border-slate-800/80 p-4">
            <h4 className="text-xs font-semibold text-slate-200 mb-3 uppercase tracking-wider">
              Physical Specifications
            </h4>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs">
              <div>
                <span className="text-slate-400 block text-[11px]">Bedrooms</span>
                <span className="font-semibold text-white flex items-center gap-1.5 mt-0.5">
                  <Bed className="w-3.5 h-3.5 text-slate-400" />
                  {property.bhk} BHK
                </span>
              </div>
              <div>
                <span className="text-slate-400 block text-[11px]">Bathrooms</span>
                <span className="font-semibold text-white flex items-center gap-1.5 mt-0.5">
                  <Bath className="w-3.5 h-3.5 text-slate-400" />
                  {propAny.bathrooms || 1} Baths
                </span>
              </div>
              <div>
                <span className="text-slate-400 block text-[11px]">Built-up Area</span>
                <span className="font-semibold text-white flex items-center gap-1.5 mt-0.5">
                  <Maximize2 className="w-3.5 h-3.5 text-slate-400" />
                  {property.area_sqft} sq.ft
                </span>
              </div>
              <div>
                <span className="text-slate-400 block text-[11px]">Property Age</span>
                <span className="font-semibold text-white mt-0.5 block">
                  {propAny.property_age || "N/A"}
                </span>
              </div>
            </div>
          </div>

          {/* Financial Breakdown Table */}
          <div className="rounded-xl bg-slate-950/50 border border-slate-800/80 p-4 text-xs">
            <h4 className="font-semibold text-slate-200 mb-3 uppercase tracking-wider text-[11px]">
              Detailed Financial Inflow & Outflow (INR ₹)
            </h4>
            <div className="space-y-2 text-slate-300">
              <div className="flex justify-between py-1.5 border-b border-slate-800/60">
                <span className="text-slate-400">Total Purchase Ticket</span>
                <span className="font-mono font-semibold text-white">
                  ₹{property.price_inr?.toLocaleString("en-IN")}
                </span>
              </div>
              <div className="flex justify-between py-1.5 border-b border-slate-800/60">
                <span className="text-slate-400">Price per Square Foot</span>
                <span className="font-mono text-white">
                  ₹{property.price_per_sqft?.toLocaleString("en-IN")}/sq.ft
                </span>
              </div>
              <div className="flex justify-between py-1.5 border-b border-slate-800/60">
                <span className="text-slate-400">Expected Monthly Rent</span>
                <span className="font-mono text-emerald-400">
                  +₹{property.estimated_monthly_rent_inr?.toLocaleString("en-IN")}/mo
                </span>
              </div>
              <div className="flex justify-between py-1.5 border-b border-slate-800/60">
                <span className="text-slate-400">Monthly Society Maintenance</span>
                <span className="font-mono text-slate-400">
                  -₹{(propAny.monthly_maintenance_inr || 0).toLocaleString("en-IN")}/mo
                </span>
              </div>
              <div className="flex justify-between py-1.5 border-b border-slate-800/60 font-semibold">
                <span className="text-slate-300">Net Monthly Cash Flow</span>
                <span
                  className={`font-mono ${
                    !hasCashFlow
                      ? "text-slate-500"
                      : cashFlow > 0
                      ? "text-emerald-400"
                      : cashFlow === 0
                      ? "text-slate-300"
                      : "text-rose-400"
                  }`}
                >
                  {hasCashFlow
                    ? `${cashFlow > 0 ? "+" : cashFlow < 0 ? "-" : ""}₹${Math.abs(Math.round(cashFlow)).toLocaleString("en-IN")}/mo`
                    : "N/A"}
                </span>
              </div>
              <div className="flex justify-between py-1.5">
                <span className="text-slate-400">Annual Rental Income</span>
                <span className="font-mono text-white">
                  {annualRent != null ? `₹${Math.round(annualRent).toLocaleString("en-IN")}` : "N/A"}
                </span>
              </div>
            </div>
          </div>

          {/* Provenance & Source Information */}
          <div className="rounded-xl bg-slate-950/50 border border-slate-800/80 p-4 text-xs space-y-2">
            <h4 className="font-semibold text-slate-200 uppercase tracking-wider text-[11px]">
              Listing Provenance & Source
            </h4>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-slate-300">
              <div>
                <span className="text-slate-400 block text-[11px]">Listing Source</span>
                <span className="font-medium text-white">{propAny.listing_source || "Manual Entry"}</span>
              </div>
              <div>
                <span className="text-slate-400 block text-[11px]">Listing Date</span>
                <span className="font-medium text-white">{propAny.listing_date || "N/A"}</span>
              </div>
              {propAny.source_url && (
                <div className="sm:col-span-2">
                  <span className="text-slate-400 block text-[11px]">Source URL</span>
                  <a
                    href={propAny.source_url}
                    target="_blank"
                    rel="noreferrer"
                    className="text-emerald-400 hover:underline flex items-center gap-1 truncate"
                  >
                    <span>{propAny.source_url}</span>
                    <ExternalLink className="w-3 h-3 shrink-0" />
                  </a>
                </div>
              )}
            </div>

            {propAny.is_demo && (
              <div className="mt-2 p-2.5 rounded bg-amber-500/10 border border-amber-500/20 text-amber-300 text-[11px] flex items-center gap-2">
                <Info className="w-4 h-4 shrink-0" />
                <span>
                  Notice: This listing is simulated DEMO DATA created for local testing and valuation analysis.
                </span>
              </div>
            )}
          </div>
        </div>

        {/* Modal Action Buttons Footer */}
        <div className="p-4 bg-slate-950/70 border-t border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-2">
            {onEdit && (
              <button
                onClick={() => {
                  onClose();
                  onEdit(property);
                }}
                className="px-3.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium border border-slate-700 transition-colors flex items-center gap-1.5"
              >
                <Edit2 className="w-3.5 h-3.5" />
                <span>Edit Property</span>
              </button>
            )}
            {onDelete && (
              <button
                onClick={() => {
                  onClose();
                  onDelete(property.id);
                }}
                className="px-3.5 py-1.5 rounded-lg bg-rose-500/10 hover:bg-rose-500/20 text-rose-300 text-xs font-medium border border-rose-500/30 transition-colors flex items-center gap-1.5"
              >
                <Trash2 className="w-3.5 h-3.5" />
                <span>Delete Property</span>
              </button>
            )}
          </div>

          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}

