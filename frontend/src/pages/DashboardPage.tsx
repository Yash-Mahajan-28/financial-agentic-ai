import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  TrendingUp,
  TrendingDown,
  Wallet,
  PieChart,
  ShieldAlert,
  ArrowRight,
  Calendar,
  Sparkles,
  CheckCircle2
} from "lucide-react";
import { Card, Badge, Button, LoadingState } from "../components/ui";
import { api } from "../services/api";
import { DashboardSummary, AlertItem } from "../types";

export default function DashboardPage() {
  const [data, setData] = useState<DashboardSummary | null>(null);
  const [alerts, setAlerts] = useState<AlertItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const [dash, alt] = await Promise.all([
          api.getDashboard(),
          api.getAlerts("UNREAD")
        ]);
        setData(dash);
        setAlerts(alt);
      } catch (err) {
        console.error("Failed to load dashboard data", err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  if (loading || !data) {
    return <LoadingState message="Calculating deterministic financial insights..." />;
  }

  const wellness = data.wellness_score;

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8">
      {/* Top Header & Coverage Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-ink tracking-tight">Financial Overview</h1>
          <p className="text-sm text-muted mt-1">
            Deterministic multi-agent analysis for period <span className="font-semibold text-ink">{data.period}</span>
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Badge variant="accent" className="px-3 py-1 text-xs">
            <Calendar className="h-3.5 w-3.5" />
            Simulated As Of: {data.latest_statement_date || "2026-04-01"}
          </Badge>
          <Badge variant="pass" className="px-3 py-1 text-xs">
            <CheckCircle2 className="h-3.5 w-3.5" />
            {data.data_coverage_months} Months Covered
          </Badge>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        <Card className="hover:border-accent/40 transition-colors">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-muted">Monthly Net Income</span>
            <div className="p-2 rounded-lg bg-pass-soft text-pass">
              <TrendingUp className="h-4 w-4" />
            </div>
          </div>
          <div className="mt-3">
            <span className="text-2xl font-bold text-ink">₹{Number(data.net_income).toLocaleString("en-IN", { minimumFractionDigits: 2 })}</span>
            <p className="text-[11px] text-muted mt-1">Confirmed payroll deposits</p>
          </div>
        </Card>

        <Card className="hover:border-accent/40 transition-colors">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-muted">Net Monthly Spending</span>
            <div className="p-2 rounded-lg bg-fail-soft text-fail">
              <TrendingDown className="h-4 w-4" />
            </div>
          </div>
          <div className="mt-3">
            <span className="text-2xl font-bold text-ink">₹{Number(data.net_spending).toLocaleString("en-IN", { minimumFractionDigits: 2 })}</span>
            <p className="text-[11px] text-muted mt-1">Approved expenses minus refunds</p>
          </div>
        </Card>

        <Card className="hover:border-accent/40 transition-colors">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-muted">Monthly Net Surplus</span>
            <div className="p-2 rounded-lg bg-accent-soft text-accent">
              <Wallet className="h-4 w-4" />
            </div>
          </div>
          <div className="mt-3">
            <span className="text-2xl font-bold text-ink">₹{Number(data.monthly_surplus).toLocaleString("en-IN", { minimumFractionDigits: 2 })}</span>
            <p className="text-[11px] text-muted mt-1">Available for savings & buffer</p>
          </div>
        </Card>

        <Card className="hover:border-accent/40 transition-colors">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-muted">Budget Utilization</span>
            <div className="p-2 rounded-lg bg-warn-soft text-warn">
              <PieChart className="h-4 w-4" />
            </div>
          </div>
          <div className="mt-3">
            <span className="text-2xl font-bold text-ink">{Number(data.overall_budget_utilization_pct).toFixed(1)}%</span>
            <p className="text-[11px] text-muted mt-1">Limit: ₹{Number(data.total_budget_limit).toLocaleString("en-IN")}</p>
          </div>
        </Card>
      </div>

      {/* Wellness Score & Components Section */}
      <Card
        title={
          <div className="flex items-center gap-2">
            <span>Financial Wellness Score</span>
            <Badge variant={wellness.status === "COMPLETE" ? "pass" : "warn"}>
              {wellness.status}
            </Badge>
          </div>
        }
        subtitle="Transparent heuristic calculated across four verified disciplines (Spec Page 9)"
      >
        <div className="grid grid-cols-1 lg:grid-cols-5 gap-6 items-center pt-2">
          {/* Main Dial */}
          <div className="flex flex-col items-center justify-center p-6 rounded-xl bg-sunken border border-line lg:col-span-1">
            <span className="text-4xl font-extrabold text-accent">
              {wellness.score !== null ? wellness.score : "—"}
            </span>
            <span className="text-xs font-semibold text-muted mt-1">out of 100</span>
            <p className="text-[10px] text-faint text-center mt-2">Transparent Metric</p>
          </div>

          {/* 4 Components */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 lg:col-span-4">
            <div className="p-4 rounded-xl border border-line bg-canvas">
              <div className="flex justify-between items-center text-xs mb-1">
                <span className="font-semibold text-ink">Savings Discipline</span>
                <span className="font-bold text-accent">35%</span>
              </div>
              <p className="text-xs text-muted mb-2">Target rate: 20% of net income</p>
              <div className="w-full bg-line rounded-full h-2">
                <div
                  className="bg-accent h-2 rounded-full transition-all"
                  style={{ width: `${Math.min(100, (Number(wellness.savings_discipline || 0)) * 100)}%` }}
                />
              </div>
              <span className="text-[11px] text-faint mt-1.5 block">
                Factor: {wellness.savings_discipline ? Number(wellness.savings_discipline).toFixed(2) : "Incomplete"}
              </span>
            </div>

            <div className="p-4 rounded-xl border border-line bg-canvas">
              <div className="flex justify-between items-center text-xs mb-1">
                <span className="font-semibold text-ink">Budget Discipline</span>
                <span className="font-bold text-accent">25%</span>
              </div>
              <p className="text-xs text-muted mb-2">Category overspend ratio</p>
              <div className="w-full bg-line rounded-full h-2">
                <div
                  className="bg-pass h-2 rounded-full transition-all"
                  style={{ width: `${Math.min(100, (Number(wellness.budget_discipline || 0)) * 100)}%` }}
                />
              </div>
              <span className="text-[11px] text-faint mt-1.5 block">
                Factor: {wellness.budget_discipline ? Number(wellness.budget_discipline).toFixed(2) : "Incomplete"}
              </span>
            </div>

            <div className="p-4 rounded-xl border border-line bg-canvas">
              <div className="flex justify-between items-center text-xs mb-1">
                <span className="font-semibold text-ink">Debt Burden</span>
                <span className="font-bold text-accent">20%</span>
              </div>
              <p className="text-xs text-muted mb-2">Ceiling: 40% debt-to-income</p>
              <div className="w-full bg-line rounded-full h-2">
                <div
                  className="bg-warn h-2 rounded-full transition-all"
                  style={{ width: `${Math.min(100, (Number(wellness.debt_burden || 0)) * 100)}%` }}
                />
              </div>
              <span className="text-[11px] text-faint mt-1.5 block">
                Factor: {wellness.debt_burden ? Number(wellness.debt_burden).toFixed(2) : "Incomplete"}
              </span>
            </div>

            <div className="p-4 rounded-xl border border-line bg-canvas">
              <div className="flex justify-between items-center text-xs mb-1">
                <span className="font-semibold text-ink">Reserve Coverage</span>
                <span className="font-bold text-accent">20%</span>
              </div>
              <p className="text-xs text-muted mb-2">Target: 3 months essential spend</p>
              <div className="w-full bg-line rounded-full h-2">
                <div
                  className="bg-accent h-2 rounded-full transition-all"
                  style={{ width: `${Math.min(100, (Number(wellness.reserve_coverage || 0)) * 100)}%` }}
                />
              </div>
              <span className="text-[11px] text-faint mt-1.5 block">
                Factor: {wellness.reserve_coverage ? Number(wellness.reserve_coverage).toFixed(2) : "Incomplete"}
              </span>
            </div>
          </div>
        </div>
      </Card>

      {/* Unread Alerts & Quick Actions */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-semibold text-ink flex items-center gap-2">
              <ShieldAlert className="h-4 w-4 text-warn" />
              Active System Alerts ({alerts.length})
            </h2>
            <Link to="/insights" className="text-xs font-semibold text-accent hover:underline flex items-center gap-1">
              View all insights <ArrowRight className="h-3 w-3" />
            </Link>
          </div>

          {alerts.length === 0 ? (
            <Card>
              <div className="text-center py-6">
                <CheckCircle2 className="h-8 w-8 text-pass mx-auto mb-2" />
                <p className="text-sm font-medium text-ink">No unresolved alerts</p>
                <p className="text-xs text-muted">All active risk thresholds and anomalies have been acknowledged.</p>
              </div>
            </Card>
          ) : (
            alerts.slice(0, 3).map((alt) => (
              <Card key={alt.alert_id} className="border-l-4 border-l-warn">
                <div className="flex items-start justify-between">
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-semibold text-sm text-ink">{alt.title}</span>
                      <Badge variant={alt.severity === "HIGH" ? "fail" : alt.severity === "MEDIUM" ? "warn" : "accent"}>
                        {alt.severity}
                      </Badge>
                    </div>
                    <p className="text-xs text-muted">{alt.message}</p>
                  </div>
                  <Link to="/insights">
                    <Button size="sm" variant="secondary">Review</Button>
                  </Link>
                </div>
              </Card>
            ))
          )}
        </div>

        {/* AI Advisor Shortcut Widget */}
        <div className="space-y-4">
          <h2 className="text-base font-semibold text-ink flex items-center gap-2">
            <Sparkles className="h-4 w-4 text-accent" />
            Personal Finance Agent
          </h2>
          <Card className="bg-gradient-to-br from-surface to-accent/5">
            <p className="text-xs text-ink leading-relaxed">
              Your conversational advisor has verified your spending, budgets, and upcoming cash flow projections.
            </p>
            <div className="mt-4 space-y-2">
              <Link to="/advisor">
                <Button variant="primary" size="sm" className="w-full">
                  Chat with Advisor
                </Button>
              </Link>
              <Link to="/forecast">
                <Button variant="secondary" size="sm" className="w-full">
                  Simulate 30-Day Cash Runway
                </Button>
              </Link>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}
