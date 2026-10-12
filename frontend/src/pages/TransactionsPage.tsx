import React, { useState, useEffect } from "react";
import { Search, Download, Filter, Eye, ChevronLeft, ChevronRight, Check } from "lucide-react";
import { Card, Badge, Button, Modal, LoadingState } from "../components/ui";
import { api } from "../services/api";
import { Transaction, PaginatedTransactions } from "../types";

const CATEGORIES = [
  "ALL",
  "Food & Dining",
  "Groceries",
  "Utilities",
  "Housing & Rent",
  "Transportation",
  "Entertainment",
  "Health & Fitness",
  "Shopping",
  "Investments",
  "Income",
  "Debt Settlement"
];

export default function TransactionsPage() {
  const [data, setData] = useState<PaginatedTransactions | null>(null);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("ALL");
  const [month, setMonth] = useState("2026-03");
  const [loading, setLoading] = useState(true);
  const [selectedTx, setSelectedTx] = useState<Transaction | null>(null);
  const [overrideModal, setOverrideModal] = useState<Transaction | null>(null);
  const [newCategory, setNewCategory] = useState("");
  const [applyMerchant, setApplyMerchant] = useState(false);
  const [updating, setUpdating] = useState(false);

  const fetchTx = async () => {
    setLoading(true);
    try {
      const res = await api.getTransactions({
        page,
        page_size: 20,
        month: month || undefined,
        category: category !== "ALL" ? category : undefined,
        search: search || undefined
      });
      setData(res);
    } catch (err) {
      console.error("Failed to load transactions", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTx();
  }, [page, month, category]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    fetchTx();
  };

  const handleApplyOverride = async () => {
    if (!overrideModal || !newCategory) return;
    setUpdating(true);
    try {
      await api.updateTransactionCategory(overrideModal.transaction_id, newCategory, applyMerchant);
      setOverrideModal(null);
      fetchTx();
    } catch (err) {
      console.error("Failed to update category", err);
    } finally {
      setUpdating(false);
    }
  };

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-6">
      {/* Header & Controls */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-ink tracking-tight">Approved Ledger</h1>
          <p className="text-sm text-muted mt-1">
            Normalized transaction records with category overrides and source provenance.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <a href={api.getExportCsvUrl(month)} download>
            <Button variant="secondary" size="sm" className="gap-2">
              <Download className="h-4 w-4" />
              Export CSV (Protected)
            </Button>
          </a>
        </div>
      </div>

      {/* Filters Bar */}
      <Card className="p-4">
        <form onSubmit={handleSearchSubmit} className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3">
          <div className="relative">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted" />
            <input
              type="text"
              placeholder="Search narrative or ref..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-9 pr-3 py-2 text-xs rounded-lg border border-line bg-canvas text-ink focus:outline-none focus:ring-2 focus:ring-accent"
            />
          </div>

          <div>
            <select
              value={month}
              onChange={(e) => { setMonth(e.target.value); setPage(1); }}
              className="w-full px-3 py-2 text-xs rounded-lg border border-line bg-canvas text-ink focus:outline-none"
            >
              <option value="2026-03">March 2026</option>
              <option value="2026-02">February 2026</option>
              <option value="2026-01">January 2026</option>
              <option value="">All Statement Months</option>
            </select>
          </div>

          <div>
            <select
              value={category}
              onChange={(e) => { setCategory(e.target.value); setPage(1); }}
              className="w-full px-3 py-2 text-xs rounded-lg border border-line bg-canvas text-ink focus:outline-none"
            >
              {CATEGORIES.map((c) => (
                <option key={c} value={c}>{c}</option>
              ))}
            </select>
          </div>

          <Button type="submit" variant="primary" size="sm">
            Filter Ledger
          </Button>
        </form>
      </Card>

      {/* Transactions Table */}
      <Card className="p-0 overflow-hidden">
        {loading ? (
          <div className="p-12"><LoadingState message="Loading transactions..." /></div>
        ) : !data || data.items.length === 0 ? (
          <div className="p-12 text-center text-xs text-muted">No transactions matching filter criteria.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="border-b border-line bg-sunken/50 text-muted font-semibold">
                  <th className="py-3 px-4">Date</th>
                  <th className="py-3 px-4">Description</th>
                  <th className="py-3 px-4">Category</th>
                  <th className="py-3 px-4">Type</th>
                  <th className="py-3 px-4">Reference</th>
                  <th className="py-3 px-4 text-right">Amount</th>
                  <th className="py-3 px-4 text-center">Status</th>
                  <th className="py-3 px-4 text-right">Source</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-line">
                {data.items.map((tx) => (
                  <tr key={tx.transaction_id} className="hover:bg-sunken/40 transition-colors">
                    <td className="py-3 px-4 font-mono text-muted whitespace-nowrap">{tx.date}</td>
                    <td className="py-3 px-4 font-medium text-ink max-w-xs truncate" title={tx.description}>
                      {tx.description}
                      {tx.is_duplicate_candidate && (
                        <span className="ml-2 text-[10px] px-1.5 py-0.5 rounded bg-warn/20 text-warn font-semibold">
                          Dup Candidate
                        </span>
                      )}
                    </td>
                    <td className="py-3 px-4">
                      <button
                        onClick={() => { setOverrideModal(tx); setNewCategory(tx.category); }}
                        className="font-medium text-ink hover:text-accent hover:underline flex items-center gap-1.5 text-left"
                      >
                        <span>{tx.category}</span>
                        <span className="text-[10px] text-muted">({tx.category_source.replace("_", " ")})</span>
                      </button>
                    </td>
                    <td className="py-3 px-4">
                      <Badge variant={tx.transaction_type === "INCOME" ? "pass" : "default"} className="text-[10px]">
                        {tx.transaction_type}
                      </Badge>
                    </td>
                    <td className="py-3 px-4 font-mono text-muted text-[11px]">{tx.reference || "—"}</td>
                    <td className={`py-3 px-4 text-right font-semibold whitespace-nowrap ${
                      tx.direction === "CREDIT" ? "text-pass" : "text-ink"
                    }`}>
                      {tx.direction === "CREDIT" ? "+" : "-"}₹{Number(tx.amount).toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                    </td>
                    <td className="py-3 px-4 text-center">
                      <Badge variant={tx.review_state === "APPROVED" ? "pass" : "warn"} className="text-[10px]">
                        {tx.review_state}
                      </Badge>
                    </td>
                    <td className="py-3 px-4 text-right">
                      <button
                        onClick={() => setSelectedTx(tx)}
                        className="p-1 rounded text-muted hover:text-ink hover:bg-sunken"
                        title="View Provenance Lineage"
                      >
                        <Eye className="h-4 w-4" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination Bar */}
        {data && (
          <div className="flex items-center justify-between p-4 border-t border-line text-xs text-muted">
            <span>
              Showing {((page - 1) * data.page_size) + 1} - {Math.min(page * data.page_size, data.total)} of {data.total} rows
            </span>
            <div className="flex items-center gap-2">
              <Button
                variant="secondary"
                size="sm"
                disabled={page <= 1}
                onClick={() => setPage((p) => Math.max(1, p - 1))}
              >
                <ChevronLeft className="h-4 w-4" />
              </Button>
              <span className="font-semibold text-ink px-2">Page {page} of {data.total_pages}</span>
              <Button
                variant="secondary"
                size="sm"
                disabled={page >= data.total_pages}
                onClick={() => setPage((p) => Math.min(data.total_pages, p + 1))}
              >
                <ChevronRight className="h-4 w-4" />
              </Button>
            </div>
          </div>
        )}
      </Card>

      {/* Provenance Lineage Modal */}
      <Modal
        isOpen={!!selectedTx}
        onClose={() => setSelectedTx(null)}
        title="Transaction Provenance Lineage"
      >
        {selectedTx && (
          <div className="space-y-4 text-xs">
            <div className="p-3 rounded-lg bg-sunken space-y-1">
              <p className="font-semibold text-ink">{selectedTx.description}</p>
              <p className="text-muted">Transaction ID: {selectedTx.transaction_id}</p>
              <p className="text-muted">Amount: ₹{Number(selectedTx.amount).toFixed(2)} ({selectedTx.direction})</p>
            </div>

            <h4 className="font-semibold text-ink">Source Raw Document Lineage</h4>
            {selectedTx.sources && selectedTx.sources.length > 0 ? (
              selectedTx.sources.map((s, idx) => (
                <div key={idx} className="p-3 rounded-lg border border-line bg-canvas space-y-1 font-mono text-[11px]">
                  <p className="text-muted">Upload ID: {s.upload_id}</p>
                  <p className="text-muted">Row Number: {s.row_number || "N/A"} | Page: {s.page_number || "N/A"}</p>
                  <p className="text-ink bg-sunken p-2 rounded mt-2">{s.raw_text}</p>
                </div>
              ))
            ) : (
              <p className="text-muted">No raw lineage record linked.</p>
            )}
          </div>
        )}
      </Modal>

      {/* Category Override Modal */}
      <Modal
        isOpen={!!overrideModal}
        onClose={() => setOverrideModal(null)}
        title="Override Transaction Category"
      >
        {overrideModal && (
          <div className="space-y-4 text-xs">
            <p className="text-muted">
              Select a new category for: <span className="font-semibold text-ink">{overrideModal.description}</span>
            </p>
            <div>
              <label className="block font-semibold text-ink mb-1">New Category</label>
              <select
                value={newCategory}
                onChange={(e) => setNewCategory(e.target.value)}
                className="w-full px-3 py-2 rounded-lg border border-line bg-canvas text-ink focus:outline-none"
              >
                {CATEGORIES.filter((c) => c !== "ALL").map((c) => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>
            </div>
            <div className="flex items-center gap-2 pt-2">
              <input
                type="checkbox"
                id="merchantRule"
                checked={applyMerchant}
                onChange={(e) => setApplyMerchant(e.target.checked)}
                className="rounded border-line text-accent focus:ring-accent"
              />
              <label htmlFor="merchantRule" className="text-ink">
                Apply as recurring merchant rule to all matching future transactions
              </label>
            </div>
            <div className="flex justify-end gap-2 pt-4 border-t border-line">
              <Button variant="secondary" size="sm" onClick={() => setOverrideModal(null)}>Cancel</Button>
              <Button variant="primary" size="sm" loading={updating} onClick={handleApplyOverride}>
                Commit Override & Re-analyze
              </Button>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
}
