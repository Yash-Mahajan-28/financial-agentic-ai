import React, { useState, useEffect } from "react";
import { UploadCloud, FileText, CheckCircle2, AlertCircle, Loader2, ArrowRight } from "lucide-react";
import { Card, Badge, Button, Modal } from "../components/ui";
import { api } from "../services/api";
import { AccountItem } from "../types";

export default function UploadPage() {
  const [accounts, setAccounts] = useState<AccountItem[]>([]);
  const [selectedAccount, setSelectedAccount] = useState<string>("");
  const [period, setPeriod] = useState<string>("2026-01 to 2026-03");
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState<{ message: string; upload_id: string; job_id: string; status: string } | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadAccounts() {
      try {
        const accs = await api.getAccounts();
        setAccounts(accs);
        if (accs.length > 0) {
          setSelectedAccount(accs[0].account_id);
        }
      } catch (err) {
        console.error("Failed to load accounts", err);
      }
    }
    loadAccounts();
  }, []);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setError(null);
    }
  };

  const handleUpload = async () => {
    if (!file || !selectedAccount) {
      setError("Please select an account and a statement file.");
      return;
    }

    setUploading(true);
    setError(null);
    setResult(null);

    try {
      const res = await api.uploadStatement(file, selectedAccount, period);
      setResult(res);
      setFile(null);
    } catch (err: any) {
      setError(err.message || "Upload and normalization failed.");
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="p-8 max-w-5xl mx-auto space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-ink tracking-tight">Statement Ingestion & Normalization</h1>
        <p className="text-sm text-muted mt-1">
          Upload UTF-8 CSV statements or text-based PDF statements for multi-tier normalization and classification.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Upload Form */}
        <Card className="md:col-span-2 space-y-5" title="Upload Bank Statement">
          {/* Account Selector */}
          <div>
            <label className="block text-xs font-semibold text-ink mb-1.5">Destination Account</label>
            <select
              value={selectedAccount}
              onChange={(e) => setSelectedAccount(e.target.value)}
              className="w-full px-3 py-2 text-sm rounded-lg border border-line bg-canvas text-ink focus:outline-none focus:ring-2 focus:ring-accent"
            >
              {accounts.map((a) => (
                <option key={a.account_id} value={a.account_id}>
                  {a.account_name} ({a.account_number_masked}) - {a.account_type}
                </option>
              ))}
            </select>
          </div>

          {/* Statement Period */}
          <div>
            <label className="block text-xs font-semibold text-ink mb-1.5">Statement Period</label>
            <input
              type="text"
              value={period}
              onChange={(e) => setPeriod(e.target.value)}
              placeholder="e.g. 2026-01 to 2026-03"
              className="w-full px-3 py-2 text-sm rounded-lg border border-line bg-canvas text-ink focus:outline-none focus:ring-2 focus:ring-accent"
            />
          </div>

          {/* Drag & Drop Area */}
          <div className="border-2 border-dashed border-line rounded-xl p-8 flex flex-col items-center justify-center text-center bg-sunken/40 hover:bg-sunken/70 transition-colors">
            <UploadCloud className="h-10 w-10 text-accent mb-3" />
            <p className="text-sm font-semibold text-ink">
              {file ? file.name : "Drag & drop your statement here, or browse"}
            </p>
            <p className="text-xs text-muted mt-1">Supports .csv (strict schema) and text-based .pdf up to 10 MB</p>
            <input
              type="file"
              id="fileInput"
              accept=".csv,.pdf"
              onChange={handleFileChange}
              className="hidden"
            />
            <label htmlFor="fileInput" className="mt-4">
              <span className="inline-flex items-center px-4 py-2 rounded-lg bg-surface border border-line text-xs font-semibold text-ink hover:bg-sunken cursor-pointer shadow-sm">
                Select File
              </span>
            </label>
          </div>

          {error && (
            <div className="p-3 rounded-lg bg-fail-soft text-fail text-xs flex items-center gap-2">
              <AlertCircle className="h-4 w-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {result && (
            <div className="p-4 rounded-lg bg-pass-soft text-pass text-xs space-y-1">
              <div className="flex items-center gap-2 font-semibold">
                <CheckCircle2 className="h-4 w-4 shrink-0" />
                <span>Upload Normalized Successfully!</span>
              </div>
              <p className="text-muted">{result.message}</p>
              <p className="text-[11px] text-faint">Job Reference: {result.job_id} | Status: {result.status}</p>
            </div>
          )}

          <Button
            onClick={handleUpload}
            loading={uploading}
            disabled={!file}
            className="w-full"
          >
            Normalize and Process Statement
          </Button>
        </Card>

        {/* Requirements & Schema Guide */}
        <div className="space-y-4">
          <Card title="Supported CSV Schema">
            <p className="text-xs text-muted mb-3">
              Statements must contain exact positive decimal amounts and direction:
            </p>
            <div className="p-3 rounded-lg bg-sunken font-mono text-[11px] text-ink overflow-x-auto space-y-1">
              <div className="text-muted font-bold">date,description,amount,direction,currency,reference,balance</div>
              <div>2026-03-04,SWIGGY ORDER,450.00,DEBIT,INR,UPI001,25550.00</div>
              <div>2026-03-05,SALARY,50000.00,CREDIT,INR,SAL001,75550.00</div>
            </div>
          </Card>

          <Card title="Ingestion Guardrails">
            <ul className="text-xs text-muted space-y-2 list-disc list-inside">
              <li>Ambiguous date formats (e.g. 03/04/2026) are rejected.</li>
              <li>Scanned PDFs without extractable text trigger OCR_REQUIRED.</li>
              <li>SHA-256 duplicate digest prevents double-counting.</li>
              <li>Balance mismatches trigger reconciliation warnings.</li>
            </ul>
          </Card>
        </div>
      </div>
    </div>
  );
}
