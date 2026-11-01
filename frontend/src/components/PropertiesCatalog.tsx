"use client";

import React, { useState, useEffect } from "react";
import {
  Search,
  Filter,
  Plus,
  FileSpreadsheet,
  RefreshCw,
  LayoutGrid,
  Table as TableIcon,
  ChevronLeft,
  ChevronRight,
  Database,
  ArrowUpDown,
  Sparkles,
} from "lucide-react";
import PropertyCard from "./PropertyCard";
import DealsTable, { PropertyDeal } from "./DealsTable";
import AddPropertyModal from "./AddPropertyModal";
import PropertyDetailsModal from "./PropertyDetailsModal";
import CSVImportModal from "./CSVImportModal";

interface PropertiesCatalogProps {
  apiBase: string;
}

export default function PropertiesCatalog({ apiBase }: PropertiesCatalogProps) {
  const [properties, setProperties] = useState<PropertyDeal[]>([]);
  const [loading, setLoading] = useState(true);
  const [viewMode, setViewMode] = useState<"grid" | "table">("grid");

  // Filter and Search states
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCity, setSelectedCity] = useState("All Cities");
  const [selectedType, setSelectedType] = useState("All");
  const [selectedBhk, setSelectedBhk] = useState<number | null>(null);
  const [minPrice, setMinPrice] = useState<number | "">("");
  const [maxPrice, setMaxPrice] = useState<number | "">("");
  const [sortBy, setSortBy] = useState("created_at");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");

  // Pagination states
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(9);
  const [totalPages, setTotalPages] = useState(1);
  const [totalCount, setTotalCount] = useState(0);

  // Modals state
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [isDetailsModalOpen, setIsDetailsModalOpen] = useState(false);
  const [isCsvModalOpen, setIsCsvModalOpen] = useState(false);
  const [selectedProperty, setSelectedProperty] = useState<PropertyDeal | null>(null);
  const [propertyToEdit, setPropertyToEdit] = useState<PropertyDeal | null>(null);

  // Seeder state
  const [seeding, setSeeding] = useState(false);

  const fetchProperties = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      params.append("page", page.toString());
      params.append("page_size", pageSize.toString());
      params.append("sort_by", sortBy);
      params.append("sort_order", sortOrder);

      if (selectedCity && selectedCity !== "All Cities") {
        params.append("city", selectedCity);
      }
      if (selectedType && selectedType !== "All") {
        params.append("property_type", selectedType);
      }
      if (selectedBhk !== null) {
        params.append("min_bedrooms", selectedBhk.toString());
        params.append("max_bedrooms", selectedBhk.toString());
      }
      if (minPrice !== "") {
        params.append("min_price", minPrice.toString());
      }
      if (maxPrice !== "") {
        params.append("max_price", maxPrice.toString());
      }
      if (searchQuery.trim()) {
        params.append("locality", searchQuery.trim());
      }

      const res = await fetch(`${apiBase}/api/v1/properties?${params.toString()}`, {
        cache: "no-store",
      });
      if (res.ok) {
        const data = await res.json();
        const mappedItems: PropertyDeal[] = (data.items || []).map((item: any) => ({
          ...item,
          monthly_cash_flow_inr: item.monthly_cash_flow_inr ?? item.estimated_monthly_cash_flow_inr,
          estimated_monthly_cash_flow_inr: item.estimated_monthly_cash_flow_inr ?? item.monthly_cash_flow_inr,
          estimated_monthly_rent_inr: item.estimated_monthly_rent_inr ?? item.expected_monthly_rent_inr,
          expected_monthly_rent_inr: item.expected_monthly_rent_inr ?? item.estimated_monthly_rent_inr,
          bhk: item.bhk ?? item.bedrooms ?? 1,
          area_sqft: item.area_sqft ?? item.built_up_area_sqft,
          price_inr: item.price_inr ?? item.purchase_price_inr,
        }));
        setProperties(mappedItems);
        setTotalPages(data.total_pages || 1);
        setTotalCount(data.total || 0);
      }
    } catch {
      // Backend offline fallback handled silently
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProperties();
  }, [page, selectedCity, selectedType, selectedBhk, sortBy, sortOrder, pageSize]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    fetchProperties();
  };

  const handleSeedData = async () => {
    setSeeding(true);
    try {
      const res = await fetch(`${apiBase}/api/v1/properties/seed`, {
        method: "POST",
      });
      if (res.ok) {
        await fetchProperties();
      }
    } catch (err) {
      console.error("Seeding error:", err);
    } finally {
      setSeeding(false);
    }
  };

  const handleDeleteProperty = async (id: number) => {
    if (!window.confirm(`Are you sure you want to delete property #${id}?`)) {
      return;
    }
    try {
      const res = await fetch(`${apiBase}/api/v1/properties/${id}`, {
        method: "DELETE",
      });
      if (res.ok) {
        fetchProperties();
      }
    } catch (err) {
      console.error("Delete error:", err);
    }
  };

  const cities = [
    "All Cities",
    "Hyderabad",
    "Bengaluru",
    "Chennai",
    "Pune",
    "Mumbai",
    "Guntur",
    "Vijayawada",
    "Visakhapatnam",
  ];

  const propertyTypes = ["All", "Apartment", "Villa", "Independent House", "Commercial", "Plot"];

  return (
    <div className="space-y-6">
      {/* Top Action & Ingestion Bar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-slate-800/60">
        <div>
          <h2 className="text-xl font-bold text-white tracking-tight">Property Management & Data Ingestion</h2>
          <p className="text-xs text-slate-400 mt-1">
            Browse, filter, manually create, or bulk-import verified Indian real estate listings.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2.5">
          {/* Seed Demo Properties Button */}
          <button
            onClick={handleSeedData}
            disabled={seeding}
            title="Populate simulated Indian properties (safe, skips duplicates)"
            className="px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-700/80 hover:bg-slate-800 text-slate-300 text-xs font-medium transition-colors flex items-center gap-1.5 disabled:opacity-50"
          >
            <Database className={`w-3.5 h-3.5 text-cyan-400 ${seeding ? "animate-spin" : ""}`} />
            <span>{seeding ? "Seeding..." : "Load Demo Catalog"}</span>
          </button>

          {/* CSV Import Button */}
          <button
            onClick={() => setIsCsvModalOpen(true)}
            className="px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-700/80 hover:bg-slate-800 text-slate-300 text-xs font-medium transition-colors flex items-center gap-1.5"
          >
            <FileSpreadsheet className="w-3.5 h-3.5 text-emerald-400" />
            <span>Import CSV</span>
          </button>

          {/* Add Property Button */}
          <button
            onClick={() => {
              setPropertyToEdit(null);
              setIsAddModalOpen(true);
            }}
            className="px-3.5 py-1.5 rounded-lg bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-400 hover:to-teal-500 text-slate-950 font-semibold text-xs shadow-md shadow-emerald-500/10 transition-all flex items-center gap-1.5"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Add Property</span>
          </button>

          {/* View Toggle */}
          <div className="flex items-center bg-slate-900 border border-slate-800 rounded-lg p-0.5">
            <button
              onClick={() => setViewMode("grid")}
              className={`p-1.5 rounded-md text-xs transition-colors ${
                viewMode === "grid" ? "bg-slate-800 text-emerald-400" : "text-slate-400 hover:text-white"
              }`}
              title="Grid View"
            >
              <LayoutGrid className="w-4 h-4" />
            </button>
            <button
              onClick={() => setViewMode("table")}
              className={`p-1.5 rounded-md text-xs transition-colors ${
                viewMode === "table" ? "bg-slate-800 text-emerald-400" : "text-slate-400 hover:text-white"
              }`}
              title="Table View"
            >
              <TableIcon className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="p-4 rounded-xl bg-slate-900/70 border border-slate-800/80 space-y-3.5 shadow-sm">
        {/* Row 1: Search & City Pills */}
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-3">
          <form onSubmit={handleSearchSubmit} className="relative flex-1 max-w-md">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Filter by locality or micro-market..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-lg pl-9 pr-4 py-1.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500"
            />
          </form>

          {/* City Pills */}
          <div className="flex items-center gap-1.5 overflow-x-auto pb-1 text-xs">
            {cities.map((city) => (
              <button
                key={city}
                onClick={() => {
                  setSelectedCity(city);
                  setPage(1);
                }}
                className={`px-2.5 py-1 rounded-md font-medium whitespace-nowrap transition-colors ${
                  selectedCity === city
                    ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30"
                    : "bg-slate-950/80 text-slate-400 hover:text-white border border-slate-800"
                }`}
              >
                {city}
              </button>
            ))}
          </div>
        </div>

        {/* Row 2: Secondary Filters (Type, BHK, Price, Sort) */}
        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-6 gap-2.5 pt-2 border-t border-slate-800/60 text-xs">
          {/* Property Type Filter */}
          <div>
            <label className="block text-[10px] text-slate-400 mb-1">Property Type</label>
            <select
              value={selectedType}
              onChange={(e) => {
                setSelectedType(e.target.value);
                setPage(1);
              }}
              className="w-full bg-slate-950 border border-slate-800 rounded-md px-2 py-1 text-slate-200 focus:outline-none focus:border-emerald-500"
            >
              {propertyTypes.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
          </div>

          {/* BHK Filter */}
          <div>
            <label className="block text-[10px] text-slate-400 mb-1">Bedrooms (BHK)</label>
            <select
              value={selectedBhk === null ? "all" : selectedBhk}
              onChange={(e) => {
                setSelectedBhk(e.target.value === "all" ? null : parseInt(e.target.value));
                setPage(1);
              }}
              className="w-full bg-slate-950 border border-slate-800 rounded-md px-2 py-1 text-slate-200 focus:outline-none focus:border-emerald-500"
            >
              <option value="all">Any BHK</option>
              <option value="1">1 BHK</option>
              <option value="2">2 BHK</option>
              <option value="3">3 BHK</option>
              <option value="4">4+ BHK</option>
            </select>
          </div>

          {/* Min Price */}
          <div>
            <label className="block text-[10px] text-slate-400 mb-1">Min Price (₹)</label>
            <input
              type="number"
              placeholder="e.g. 5000000"
              value={minPrice}
              onChange={(e) => {
                setMinPrice(e.target.value === "" ? "" : parseFloat(e.target.value));
                setPage(1);
              }}
              className="w-full bg-slate-950 border border-slate-800 rounded-md px-2 py-1 text-slate-200 focus:outline-none focus:border-emerald-500 font-mono"
            />
          </div>

          {/* Max Price */}
          <div>
            <label className="block text-[10px] text-slate-400 mb-1">Max Price (₹)</label>
            <input
              type="number"
              placeholder="e.g. 20000000"
              value={maxPrice}
              onChange={(e) => {
                setMaxPrice(e.target.value === "" ? "" : parseFloat(e.target.value));
                setPage(1);
              }}
              className="w-full bg-slate-950 border border-slate-800 rounded-md px-2 py-1 text-slate-200 focus:outline-none focus:border-emerald-500 font-mono"
            />
          </div>

          {/* Sort By */}
          <div>
            <label className="block text-[10px] text-slate-400 mb-1">Sort By</label>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-md px-2 py-1 text-slate-200 focus:outline-none focus:border-emerald-500"
            >
              <option value="created_at">Date Added</option>
              <option value="price_inr">Purchase Price</option>
              <option value="gross_rental_yield_pct">Rental Yield</option>
              <option value="expected_monthly_rent_inr">Monthly Rent</option>
              <option value="built_up_area_sqft">Built-up Area</option>
            </select>
          </div>

          {/* Sort Order */}
          <div>
            <label className="block text-[10px] text-slate-400 mb-1">Order</label>
            <button
              onClick={() => setSortOrder(sortOrder === "asc" ? "desc" : "asc")}
              className="w-full bg-slate-950 border border-slate-800 rounded-md px-2 py-1 text-slate-200 flex items-center justify-between hover:bg-slate-800 transition-colors"
            >
              <span>{sortOrder === "asc" ? "Ascending" : "Descending"}</span>
              <ArrowUpDown className="w-3.5 h-3.5 text-slate-400" />
            </button>
          </div>
        </div>
      </div>

      {/* Listings Display: Grid or Table */}
      {loading ? (
        <div className="h-64 rounded-xl bg-slate-900/60 border border-slate-800 flex items-center justify-center text-xs text-slate-400">
          <RefreshCw className="w-4 h-4 animate-spin text-emerald-400 mr-2" />
          <span>Loading properties catalog...</span>
        </div>
      ) : properties.length === 0 ? (
        <div className="rounded-xl bg-slate-900/60 border border-slate-800 p-12 text-center space-y-3">
          <Database className="w-10 h-10 text-slate-600 mx-auto" />
          <h3 className="text-base font-semibold text-white">No Properties Found</h3>
          <p className="text-xs text-slate-400 max-w-sm mx-auto">
            Try adjusting your search criteria, or load simulated Indian properties to test the analyzer.
          </p>
          <button
            onClick={handleSeedData}
            className="px-4 py-1.5 rounded-lg bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 text-xs font-medium transition-colors inline-flex items-center gap-1.5"
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>Load 24 Demo Properties</span>
          </button>
        </div>
      ) : viewMode === "grid" ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {properties.map((prop) => (
            <PropertyCard
              key={prop.id}
              property={prop}
              onViewDetails={(p) => {
                setSelectedProperty(p);
                setIsDetailsModalOpen(true);
              }}
              onEdit={(p) => {
                setPropertyToEdit(p);
                setIsAddModalOpen(true);
              }}
              onDelete={handleDeleteProperty}
            />
          ))}
        </div>
      ) : (
        <DealsTable
          properties={properties}
          selectedCity={selectedCity}
          onInspectProperty={(p) => {
            setSelectedProperty(p);
            setIsDetailsModalOpen(true);
          }}
        />
      )}

      {/* Pagination Bar */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between p-3.5 rounded-xl bg-slate-900/70 border border-slate-800 text-xs">
          <span className="text-slate-400">
            Showing Page <span className="font-semibold text-white">{page}</span> of{" "}
            <span className="font-semibold text-white">{totalPages}</span> ({totalCount} total listings)
          </span>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page <= 1}
              className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 disabled:opacity-40 transition-colors"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <span className="px-2 font-mono text-emerald-400 font-semibold">{page}</span>
            <button
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={page >= totalPages}
              className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 disabled:opacity-40 transition-colors"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {/* Modals */}
      <AddPropertyModal
        isOpen={isAddModalOpen}
        onClose={() => setIsAddModalOpen(false)}
        onSuccess={fetchProperties}
        propertyToEdit={propertyToEdit}
        apiBase={apiBase}
      />

      <PropertyDetailsModal
        isOpen={isDetailsModalOpen}
        onClose={() => setIsDetailsModalOpen(false)}
        property={selectedProperty}
        onEdit={(p) => {
          setPropertyToEdit(p);
          setIsAddModalOpen(true);
        }}
        onDelete={handleDeleteProperty}
      />

      <CSVImportModal
        isOpen={isCsvModalOpen}
        onClose={() => setIsCsvModalOpen(false)}
        onSuccess={fetchProperties}
        apiBase={apiBase}
      />
    </div>
  );
}

