import React, { useState, useEffect } from "react";
import { PieChart, Plus, AlertTriangle, CheckCircle2, Sliders, RefreshCw } from "lucide-react";
import { Card, Badge, Button, Modal, LoadingState } from "../components/ui";
import { api } from "../services/api";
import { BudgetUtilizationItem, FiftyThirtyTwentyTemplate } from "../types";

export default function BudgetsPage() {
  const [month, setMonth] = useState("2026-03");
  const [items, setItems] = useState<BudgetUtilizationItem[]>([]);
  const [template, setTemplate] = useState<FiftyThirtyTwentyTemplate | null>(null);
  const [loading, setLoading] = useState(true);
  const [editModal, setEditModal] = useState(false);
  const [editableLimits, setEditableLimits] = useState<Record<string, number>>({});
  const [saving, setSaving] = useState(false);

  const loadData = async () => {
    setLoading(true);
    try {
      const [bData, tData] = await Promise.all([
        api.getBudget(month),
        api.get503020Template()
      ]);
      setItems(bData.utilization_summary.items || []);
      setEditableLimits(bData.limits || {});
      setTemplate(tData);
    } catch (err) {
      console.error("Failed to load budgets", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [month]);

  const handleSaveBudget = async () => {
    setSaving(true);
    try {
      await api.updateBudget(month, editableLimits);
      setEditModal(false);
      loadData();
    } catch (err) {
      console.error("Failed to update budget", err);
    } finally {
      setSaving(false);
    }
  };

  const handleApplyTemplate = () => {
    if (!template) return;
    const newLimits: Record<string, number> = {
      "Housing & Rent": template.breakdown["Housing & Rent (Needs)"],
      "Groceries": template.breakdown["Groceries (Needs)"],
      "Utilities": template.breakdown["Utilities (Needs)"],
      "Food & Dining": template.breakdown["Food & Dining (Wants)"],
      "Shopping": template.breakdown["Shopping (Wants)"],
      "Entertainment": template.breakdown["Entertainment (Wants)"]
    };
    setEditableLimits(newLimits);
  };

  if (loading) {
    return <LoadingState message="Computing monthly budget utilizations..." />;
  }

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-ink tracking-tight">Budgets & Planning</h1>
          <p className="text-sm text-muted mt-1">
            Category spending utilization and 50/30/20 balanced budget allocations.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <select
            value={month}
            onChange={(e) => setMonth(e.target.value)}
            className="px-3 py-1.5 text-xs rounded-lg border border-line bg-canvas text-ink focus:outline-none"
          >
            <option value="2026-03">March 2026</option>
            <option value="2026-02">February 2026</option>
            <option value="2026-01">January 2026</option>
          </select>
          <Button variant="primary" size="sm" onClick={() => setEditModal(true)} className="gap-2">
            <Sliders className="h-4 w-4" />
            Adjust Limits
          </Button>
        </div>
      </div>

      {/* Category Progress Meters */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {items.map((it) => {
          const util = Number(it.utilization_pct);
          const isExceeded = it.status === "EXCEEDED" || it.status === "ZERO_LIMIT_EXCEEDED";
          const isWarning = it.status === "WARNING";

          return (
            <Card key={it.category} className="space-y-3">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-semibold text-sm text-ink">{it.category}</h3>
                  <span className="text-xs text-muted">
                    Limit: ₹{Number(it.limit).toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                  </span>
                </div>
                <Badge
                  variant={isExceeded ? "fail" : isWarning ? "warn" : "pass"}
                  className="text-xs font-semibold"
                >
                  {isExceeded ? "Exceeded" : isWarning ? "Warning (90%)" : "On Track"} ({util.toFixed(1)}%)
                </Badge>
              </div>

              {/* Progress Bar */}
              <div className="w-full bg-line rounded-full h-2.5 overflow-hidden">
                <div
                  className={`h-2.5 rounded-full transition-all ${
                    isExceeded ? "bg-fail" : isWarning ? "bg-warn" : "bg-pass"
                  }`}
                  style={{ width: `${Math.min(100, util)}%` }}
                />
              </div>

              <div className="flex justify-between items-center text-xs">
                <span className="text-muted">
                  Spent: <span className="font-semibold text-ink">₹{Number(it.spent).toLocaleString("en-IN", { minimumFractionDigits: 2 })}</span>
                </span>
                <span className={isExceeded ? "text-fail font-semibold" : "text-muted"}>
                  {isExceeded ? `Over by ₹${Math.abs(Number(it.remaining)).toFixed(2)}` : `Remaining: ₹${Number(it.remaining).toFixed(2)}`}
                </span>
              </div>
            </Card>
          );
        })}
      </div>

      {/* 50/30/20 Suggestion Card */}
      {template && (
        <Card
          title="Configurable 50 / 30 / 20 Framework Suggestion"
          subtitle={`Based on verified net monthly income of ₹${Number(template.total_income).toLocaleString("en-IN")}`}
        >
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-3">
            <div className="p-4 rounded-xl bg-accent-soft/40 border border-accent/20">
              <span className="text-xs font-semibold text-accent">50% Needs</span>
              <p className="text-xl font-bold text-ink mt-1">₹{Number(template.needs_limit).toLocaleString("en-IN")}</p>
              <p className="text-[11px] text-muted mt-1">Rent, Groceries, Electricity, Utilities</p>
            </div>

            <div className="p-4 rounded-xl bg-warn-soft/40 border border-warn/20">
              <span className="text-xs font-semibold text-warn">30% Wants</span>
              <p className="text-xl font-bold text-ink mt-1">₹{Number(template.wants_limit).toLocaleString("en-IN")}</p>
              <p className="text-[11px] text-muted mt-1">Dining out, Entertainment, Shopping</p>
            </div>

            <div className="p-4 rounded-xl bg-pass-soft/40 border border-pass/20">
              <span className="text-xs font-semibold text-pass">20% Savings Target</span>
              <p className="text-xl font-bold text-ink mt-1">₹{Number(template.savings_target).toLocaleString("en-IN")}</p>
              <p className="text-[11px] text-muted mt-1">Liquid Reserve, Emergency Fund, SIP</p>
            </div>
          </div>
        </Card>
      )}

      {/* Adjust Budget Modal */}
      <Modal
        isOpen={editModal}
        onClose={() => setEditModal(false)}
        title={`Adjust Budget Limits for ${month}`}
      >
        <div className="space-y-4 text-xs">
          <div className="flex justify-between items-center pb-2 border-b border-line">
            <span className="text-muted">Enter monthly spending caps in INR</span>
            <Button variant="ghost" size="sm" onClick={handleApplyTemplate} className="text-accent gap-1 text-[11px]">
              <RefreshCw className="h-3 w-3" />
              Apply 50/30/20 Template
            </Button>
          </div>

          <div className="max-h-72 overflow-y-auto space-y-3 pr-1">
            {Object.keys(editableLimits).map((cat) => (
              <div key={cat} className="flex items-center justify-between gap-4">
                <span className="font-medium text-ink w-1/2">{cat}</span>
                <input
                  type="number"
                  step="500"
                  value={editableLimits[cat] || 0}
                  onChange={(e) =>
                    setEditableLimits({
                      ...editableLimits,
                      [cat]: parseFloat(e.target.value) || 0
                    })
                  }
                  className="w-1/2 px-3 py-1.5 rounded-lg border border-line bg-canvas text-ink text-right focus:outline-none focus:ring-1 focus:ring-accent"
                />
              </div>
            ))}
          </div>

          <div className="flex justify-end gap-2 pt-4 border-t border-line">
            <Button variant="secondary" size="sm" onClick={() => setEditModal(false)}>Cancel</Button>
            <Button variant="primary" size="sm" loading={saving} onClick={handleSaveBudget}>
              Save and Re-run Analysis
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
