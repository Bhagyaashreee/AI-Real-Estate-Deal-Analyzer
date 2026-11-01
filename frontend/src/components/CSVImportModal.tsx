"use client";

import React, { useState, useRef } from "react";
import {
  X,
  UploadCloud,
  FileText,
  Download,
  AlertCircle,
  CheckCircle2,
  RefreshCw,
  AlertTriangle,
  FileSpreadsheet,
} from "lucide-react";

interface CSVImportRowError {
  row_number: number;
  property_title?: string;
  error: string;
}

interface CSVImportResult {
  total_rows: number;
  successful_imports: number;
  failed_imports: number;
  skipped_duplicates: number;
  errors: CSVImportRowError[];
}

interface CSVImportModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
  apiBase: string;
}

export default function CSVImportModal({
  isOpen,
  onClose,
  onSuccess,
  apiBase,
}: CSVImportModalProps) {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState<CSVImportResult | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  if (!isOpen) return null;

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const selected = e.target.files[0];
      if (!selected.name.toLowerCase().endsWith(".csv")) {
        setErrorMessage("Please select a valid CSV (.csv) file");
        setFile(null);
        return;
      }
      setFile(selected);
      setErrorMessage(null);
      setResult(null);
    }
  };

  const handleDownloadTemplate = () => {
    window.open(`${apiBase}/api/v1/properties/template-csv`, "_blank");
  };

  const handleUpload = async () => {
    if (!file) {
      setErrorMessage("Please choose a CSV file first");
      return;
    }

    setUploading(true);
    setErrorMessage(null);
    setResult(null);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch(`${apiBase}/api/v1/properties/import-csv`, {
        method: "POST",
        body: formData,
      });

      if (!res.ok) {
        const errorJson = await res.json().catch(() => ({}));
        throw new Error(errorJson.detail || "Failed to import CSV file");
      }

      const resData: CSVImportResult = await res.json();
      setResult(resData);
      if (resData.successful_imports > 0) {
        onSuccess();
      }
    } catch (err: any) {
      setErrorMessage(err.message || "Failed to process CSV file");
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4 overflow-y-auto">
      <div className="relative w-full max-w-2xl bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl overflow-hidden my-8">
        {/* Header */}
        <div className="p-5 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
              <FileSpreadsheet className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-semibold text-white">Import Properties via CSV</h2>
              <p className="text-xs text-slate-400">
                Bulk ingest property listings with data validation & duplicate protection
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

        {/* Modal Body */}
        <div className="p-6 space-y-5">
          {/* Action Row: Template Download */}
          <div className="flex items-center justify-between p-3 rounded-xl bg-slate-950/60 border border-slate-800 text-xs">
            <div className="flex items-center gap-2 text-slate-300">
              <FileText className="w-4 h-4 text-emerald-400" />
              <span>Need a reference format? Download our pre-formatted template:</span>
            </div>
            <button
              onClick={handleDownloadTemplate}
              className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-emerald-300 font-medium border border-slate-700/80 transition-colors flex items-center gap-1.5 shrink-0"
            >
              <Download className="w-3.5 h-3.5" />
              <span>Sample CSV Template</span>
            </button>
          </div>

          {/* Upload Drop Area */}
          <div
            onClick={() => fileInputRef.current?.click()}
            className="border-2 border-dashed border-slate-800 hover:border-emerald-500/50 rounded-2xl p-6 text-center cursor-pointer transition-colors bg-slate-950/40 hover:bg-slate-950/80 group"
          >
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileChange}
              accept=".csv"
              className="hidden"
            />
            <div className="w-12 h-12 mx-auto mb-3 rounded-full bg-slate-800/80 flex items-center justify-center text-slate-400 group-hover:text-emerald-400 transition-colors">
              <UploadCloud className="w-6 h-6" />
            </div>
            {file ? (
              <div>
                <p className="text-sm font-semibold text-emerald-300">{file.name}</p>
                <p className="text-xs text-slate-400 mt-1">
                  {(file.size / 1024).toFixed(1)} KB &bull; Click to change file
                </p>
              </div>
            ) : (
              <div>
                <p className="text-sm font-medium text-slate-300">
                  Click to select a CSV file or drag and drop here
                </p>
                <p className="text-xs text-slate-500 mt-1">Accepts standard .csv UTF-8 format</p>
              </div>
            )}
          </div>

          {/* Error Message */}
          {errorMessage && (
            <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{errorMessage}</span>
            </div>
          )}

          {/* Validation Results Drawer */}
          {result && (
            <div className="rounded-xl bg-slate-950/70 border border-slate-800 p-4 space-y-3">
              <h4 className="text-xs font-semibold text-white uppercase tracking-wider">
                Ingestion Diagnostic Summary
              </h4>

              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
                <div className="p-2.5 rounded-lg bg-slate-900 border border-slate-800">
                  <span className="text-slate-400 text-[10px] block">Total Processed</span>
                  <span className="text-base font-bold text-white">{result.total_rows}</span>
                </div>
                <div className="p-2.5 rounded-lg bg-emerald-500/10 border border-emerald-500/20">
                  <span className="text-emerald-400 text-[10px] block">Successful</span>
                  <span className="text-base font-bold text-emerald-300">
                    {result.successful_imports}
                  </span>
                </div>
                <div className="p-2.5 rounded-lg bg-amber-500/10 border border-amber-500/20">
                  <span className="text-amber-400 text-[10px] block">Skipped Duplicates</span>
                  <span className="text-base font-bold text-amber-300">
                    {result.skipped_duplicates}
                  </span>
                </div>
                <div className="p-2.5 rounded-lg bg-rose-500/10 border border-rose-500/20">
                  <span className="text-rose-400 text-[10px] block">Invalid Rows</span>
                  <span className="text-base font-bold text-rose-300">
                    {result.failed_imports - result.skipped_duplicates}
                  </span>
                </div>
              </div>

              {/* Granular Row Errors Table */}
              {result.errors && result.errors.length > 0 && (
                <div className="mt-3">
                  <span className="text-[11px] font-semibold text-rose-300 flex items-center gap-1.5 mb-2">
                    <AlertTriangle className="w-3.5 h-3.5" />
                    Validation & Duplicate Warnings ({result.errors.length}):
                  </span>
                  <div className="max-h-48 overflow-y-auto rounded-lg border border-slate-800 divide-y divide-slate-800/80 text-xs">
                    {result.errors.map((err, idx) => (
                      <div key={idx} className="p-2 bg-slate-900/60 flex items-start gap-2">
                        <span className="px-1.5 py-0.5 rounded bg-slate-800 text-[10px] font-mono text-slate-300 shrink-0">
                          Row #{err.row_number}
                        </span>
                        <div className="text-slate-300">
                          {err.property_title && (
                            <span className="font-semibold text-white mr-1.5">
                              {err.property_title}:
                            </span>
                          )}
                          <span className="text-rose-300">{err.error}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Modal Footer */}
        <div className="p-4 bg-slate-950/70 border-t border-slate-800 flex items-center justify-end gap-3">
          <button
            onClick={onClose}
            disabled={uploading}
            className="px-4 py-2 rounded-lg text-xs font-medium text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            {result?.successful_imports ? "Done" : "Cancel"}
          </button>
          <button
            onClick={handleUpload}
            disabled={!file || uploading}
            className="px-5 py-2 rounded-lg text-xs font-semibold bg-gradient-to-r from-cyan-500 to-emerald-600 hover:from-cyan-400 hover:to-emerald-500 text-slate-950 shadow-md shadow-cyan-500/20 transition-all disabled:opacity-50 flex items-center gap-1.5"
          >
            {uploading ? (
              <>
                <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                <span>Ingesting...</span>
              </>
            ) : (
              <>
                <UploadCloud className="w-3.5 h-3.5" />
                <span>Start Ingestion</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}

