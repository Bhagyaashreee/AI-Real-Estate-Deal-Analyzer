"use client";

import React, { useState, useEffect } from "react";
import { X, Building2, MapPin, IndianRupee, Bed, Bath, Maximize2, Tag, Calendar, Link as LinkIcon, AlertCircle, CheckCircle2 } from "lucide-react";
import { PropertyDeal } from "./DealsTable";

interface AddPropertyModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
  propertyToEdit?: PropertyDeal | null;
  apiBase: string;
}

export default function AddPropertyModal({
  isOpen,
  onClose,
  onSuccess,
  propertyToEdit,
  apiBase,
}: AddPropertyModalProps) {
  const [formData, setFormData] = useState({
    title: "",
    city: "Hyderabad",
    locality: "",
    state: "Telangana",
    property_type: "Apartment",
    bedrooms: 2,
    bathrooms: 2,
    built_up_area_sqft: 1200,
    purchase_price_inr: 8500000,
    expected_monthly_rent_inr: 32000,
    monthly_maintenance_inr: 2500,
    property_age: "0-2 years",
    listing_source: "Manual Entry",
    source_url: "",
    listing_date: "",
    is_demo: false,
  });

  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  // Populate form if editing
  useEffect(() => {
    if (propertyToEdit) {
      setFormData({
        title: propertyToEdit.title || "",
        city: propertyToEdit.city || "Hyderabad",
        locality: propertyToEdit.locality || "",
        state: (propertyToEdit as any).state || "",
        property_type: propertyToEdit.property_type || "Apartment",
        bedrooms: propertyToEdit.bhk || 2,
        bathrooms: (propertyToEdit as any).bathrooms || 2,
        built_up_area_sqft: propertyToEdit.area_sqft || 1200,
        purchase_price_inr: propertyToEdit.price_inr || 8500000,
        expected_monthly_rent_inr: propertyToEdit.estimated_monthly_rent_inr || 32000,
        monthly_maintenance_inr: (propertyToEdit as any).monthly_maintenance_inr || 2500,
        property_age: (propertyToEdit as any).property_age || "0-2 years",
        listing_source: (propertyToEdit as any).listing_source || "Manual Entry",
        source_url: (propertyToEdit as any).source_url || "",
        listing_date: (propertyToEdit as any).listing_date || new Date().toISOString().split("T")[0],
        is_demo: (propertyToEdit as any).is_demo || false,
      });
    } else {
      setFormData({
        title: "",
        city: "Hyderabad",
        locality: "",
        state: "Telangana",
        property_type: "Apartment",
        bedrooms: 2,
        bathrooms: 2,
        built_up_area_sqft: 1200,
        purchase_price_inr: 8500000,
        expected_monthly_rent_inr: 32000,
        monthly_maintenance_inr: 2500,
        property_age: "0-2 years",
        listing_source: "Manual Entry",
        source_url: "",
        listing_date: new Date().toISOString().split("T")[0],
        is_demo: false,
      });
    }
    setErrorMsg(null);
  }, [propertyToEdit, isOpen]);

  if (!isOpen) return null;

  // Currency helper for live input feedback
  const formatInrHelper = (val: number) => {
    if (!val || val <= 0) return "₹0";
    if (val >= 10000000) {
      return `₹${(val / 10000000).toFixed(2)} Cr`;
    } else if (val >= 100000) {
      return `₹${(val / 100000).toFixed(2)} Lakhs`;
    }
    return `₹${val.toLocaleString("en-IN")}`;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);

    // Validation
    if (!formData.title.trim() || formData.title.trim().length < 3) {
      setErrorMsg("Property title must be at least 3 characters long");
      return;
    }
    if (!formData.city.trim()) {
      setErrorMsg("City is required");
      return;
    }
    if (!formData.locality.trim()) {
      setErrorMsg("Locality is required");
      return;
    }
    if (formData.built_up_area_sqft <= 0) {
      setErrorMsg("Built-up area must be strictly positive");
      return;
    }
    if (formData.purchase_price_inr <= 0) {
      setErrorMsg("Purchase price must be strictly positive");
      return;
    }
    if (formData.expected_monthly_rent_inr < 0) {
      setErrorMsg("Expected monthly rent cannot be negative");
      return;
    }
    if (formData.monthly_maintenance_inr < 0) {
      setErrorMsg("Monthly maintenance cannot be negative");
      return;
    }

    setSubmitting(true);
    try {
      const url = propertyToEdit
        ? `${apiBase}/api/v1/properties/${propertyToEdit.id}`
        : `${apiBase}/api/v1/properties`;
      const method = propertyToEdit ? "PUT" : "POST";

      const res = await fetch(url, {
        method,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(formData),
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || "Failed to save property. Please check input values.");
      }

      onSuccess();
      onClose();
    } catch (err: any) {
      setErrorMsg(err.message || "An unexpected error occurred");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4 overflow-y-auto">
      <div className="relative w-full max-w-2xl bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl overflow-hidden my-8">
        {/* Header */}
        <div className="p-5 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              <Building2 className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-semibold text-white">
                {propertyToEdit ? "Edit Property Listing" : "Add Property Listing"}
              </h2>
              <p className="text-xs text-slate-400">
                Indian real estate financial and physical attributes
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-white transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Error Banner */}
        {errorMsg && (
          <div className="mx-6 mt-4 p-3 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{errorMsg}</span>
          </div>
        )}

        {/* Form Body */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {/* Property Title */}
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">
              Property Title *
            </label>
            <input
              type="text"
              required
              placeholder="e.g. 3 BHK Gated High-Rise in Gachibowli"
              value={formData.title}
              onChange={(e) => setFormData({ ...formData, title: e.target.value })}
              className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3.5 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500 transition-colors"
            />
          </div>

          {/* Location Row: City, Locality, State */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">City *</label>
              <select
                value={formData.city}
                onChange={(e) => setFormData({ ...formData, city: e.target.value })}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-emerald-500"
              >
                <option value="Hyderabad">Hyderabad</option>
                <option value="Bengaluru">Bengaluru</option>
                <option value="Chennai">Chennai</option>
                <option value="Pune">Pune</option>
                <option value="Mumbai">Mumbai</option>
                <option value="Guntur">Guntur</option>
                <option value="Vijayawada">Vijayawada</option>
                <option value="Visakhapatnam">Visakhapatnam</option>
                <option value="Other">Other</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Locality *</label>
              <input
                type="text"
                required
                placeholder="e.g. Whitefield, Hitec City"
                value={formData.locality}
                onChange={(e) => setFormData({ ...formData, locality: e.target.value })}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-emerald-500"
              >
              </input>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">State</label>
              <input
                type="text"
                placeholder="e.g. Telangana"
                value={formData.state}
                onChange={(e) => setFormData({ ...formData, state: e.target.value })}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-emerald-500"
              />
            </div>
          </div>

          {/* Property Type, Bedrooms, Bathrooms, Area */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Type</label>
              <select
                value={formData.property_type}
                onChange={(e) => setFormData({ ...formData, property_type: e.target.value })}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-emerald-500"
              >
                <option value="Apartment">Apartment</option>
                <option value="Villa">Villa</option>
                <option value="Independent House">Independent House</option>
                <option value="Commercial">Commercial</option>
                <option value="Plot">Plot</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Bedrooms (BHK)</label>
              <input
                type="number"
                min="0"
                max="20"
                value={formData.bedrooms}
                onChange={(e) => setFormData({ ...formData, bedrooms: parseInt(e.target.value) || 0 })}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-emerald-500"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Bathrooms</label>
              <input
                type="number"
                min="0"
                max="20"
                value={formData.bathrooms}
                onChange={(e) => setFormData({ ...formData, bathrooms: parseInt(e.target.value) || 0 })}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-emerald-500"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Area (sq.ft) *</label>
              <input
                type="number"
                min="1"
                required
                value={formData.built_up_area_sqft}
                onChange={(e) => setFormData({ ...formData, built_up_area_sqft: parseFloat(e.target.value) || 0 })}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-emerald-500"
              />
            </div>
          </div>

          {/* Financials Row: Price, Rent, Maintenance */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 p-3.5 rounded-xl bg-slate-950/60 border border-slate-800">
            <div>
              <div className="flex justify-between items-center mb-1">
                <label className="text-xs font-medium text-slate-300">Purchase Price (₹) *</label>
                <span className="text-[10px] text-emerald-400 font-bold">
                  {formatInrHelper(formData.purchase_price_inr)}
                </span>
              </div>
              <input
                type="number"
                min="1"
                required
                value={formData.purchase_price_inr}
                onChange={(e) => setFormData({ ...formData, purchase_price_inr: parseFloat(e.target.value) || 0 })}
                className="w-full bg-slate-900 border border-slate-700/80 rounded-lg px-3 py-2 text-xs text-white font-mono focus:outline-none focus:border-emerald-500"
              />
            </div>

            <div>
              <div className="flex justify-between items-center mb-1">
                <label className="text-xs font-medium text-slate-300">Expected Rent (₹/mo)</label>
                <span className="text-[10px] text-cyan-400 font-bold">
                  {formatInrHelper(formData.expected_monthly_rent_inr)}
                </span>
              </div>
              <input
                type="number"
                min="0"
                value={formData.expected_monthly_rent_inr}
                onChange={(e) => setFormData({ ...formData, expected_monthly_rent_inr: parseFloat(e.target.value) || 0 })}
                className="w-full bg-slate-900 border border-slate-700/80 rounded-lg px-3 py-2 text-xs text-white font-mono focus:outline-none focus:border-emerald-500"
              />
            </div>

            <div>
              <div className="flex justify-between items-center mb-1">
                <label className="text-xs font-medium text-slate-300">Maintenance (₹/mo)</label>
                <span className="text-[10px] text-slate-400 font-bold">
                  {formatInrHelper(formData.monthly_maintenance_inr)}
                </span>
              </div>
              <input
                type="number"
                min="0"
                value={formData.monthly_maintenance_inr}
                onChange={(e) => setFormData({ ...formData, monthly_maintenance_inr: parseFloat(e.target.value) || 0 })}
                className="w-full bg-slate-900 border border-slate-700/80 rounded-lg px-3 py-2 text-xs text-white font-mono focus:outline-none focus:border-emerald-500"
              />
            </div>
          </div>

          {/* Age, Source, Listing URL */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Property Age</label>
              <select
                value={formData.property_age}
                onChange={(e) => setFormData({ ...formData, property_age: e.target.value })}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-emerald-500"
              >
                <option value="New / Under Construction">New / Under Construction</option>
                <option value="0-2 years">0-2 years</option>
                <option value="3-5 years">3-5 years</option>
                <option value="5-10 years">5-10 years</option>
                <option value="10+ years">10+ years</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Listing Source</label>
              <input
                type="text"
                placeholder="e.g. MagicBricks, Owner Direct"
                value={formData.listing_source}
                onChange={(e) => setFormData({ ...formData, listing_source: e.target.value })}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-emerald-500"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Source URL</label>
              <input
                type="url"
                placeholder="https://..."
                value={formData.source_url}
                onChange={(e) => setFormData({ ...formData, source_url: e.target.value })}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-emerald-500"
              />
            </div>
          </div>

          {/* Actions Footer */}
          <div className="pt-4 border-t border-slate-800 flex items-center justify-end gap-3">
            <button
              type="button"
              onClick={onClose}
              disabled={submitting}
              className="px-4 py-2 rounded-lg text-xs font-medium text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="px-5 py-2 rounded-lg text-xs font-semibold bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-400 hover:to-teal-500 text-slate-950 shadow-md shadow-emerald-500/20 transition-all disabled:opacity-50"
            >
              {submitting ? "Saving..." : propertyToEdit ? "Update Property" : "Create Property"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
