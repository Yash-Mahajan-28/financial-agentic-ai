import React, { useState, useEffect } from "react";
import { Settings, ShieldCheck, Activity, Cpu, Database, RefreshCw, CheckCircle2, User, Calendar } from "lucide-react";
import { Card, Badge, Button, LoadingState } from "../components/ui";
import { api } from "../services/api";
import { SystemStatus, AgentRunRecord, UserProfile, ObligationItem } from "../types";

export default function SystemPage() {
  const [status, setStatus] = useState<SystemStatus | null>(null);
  const [runs, setRuns] = useState<AgentRunRecord[]>([]);
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [obligations, setObligations] = useState<ObligationItem[]>([]);
  const [loading, setLoading] = useState(true);

  // Edit profile state
  const [income, setIncome] = useState("50000.00");
  const [debt, setDebt] = useState("7000.00");
  const [reserve, setReserve] = useState("75000.00");
  const [savingProfile, setSavingProfile] = useState(false);

  const loadData = async () => {
    setLoading(true);
    try {
      const [st, r, p, obs] = await Promise.all([
        api.getSystemStatus(),
        api.getSystemRuns(),
        api.getMe(),
        api.getObligations()
      ]);
      setStatus(st);
      setRuns(r);
      setProfile(p);
      setObligations(obs);
      setIncome(String(p.confirmed_net_income));
      setDebt(String(p.confirmed_monthly_debt));
      setReserve(String(p.liquid_emergency_reserve));
    } catch (err) {
      console.error("Failed to load system data", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleUpdateProfile = async () => {
    setSavingProfile(true);
    try {
      await api.updateProfile({
        confirmed_net_income: parseFloat(income),
        confirmed_monthly_debt: parseFloat(debt),
        liquid_emergency_reserve: parseFloat(reserve)
      });
      loadData();
    } catch (err) {
      console.error("Failed to update profile", err);
    } finally {
      setSavingProfile(false);
    }
  };

  if (loading || !status) {
    return <LoadingState message="Polling system readiness and agent execution telemetry..." />;
  }

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-ink tracking-tight">System Health & Settings</h1>
        <p className="text-sm text-muted mt-1">
          Measured service readiness, agent orchestration execution logs, and user profile inputs.
        </p>
      </div>

      {/* Services Health Status */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        {Object.entries(status.services).map(([key, svc]) => (
          <Card key={key} className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold uppercase tracking-wider text-muted">{svc.name}</span>
              <Badge variant={svc.status === "HEALTHY" ? "pass" : "warn"} className="text-[10px]">
                {svc.status}
              </Badge>
            </div>
            <p className="text-xs text-ink font-medium">{svc.details || "Active"}</p>
            {svc.latency_ms !== undefined && (
              <span className="text-[10px] text-faint block">{svc.latency_ms.toFixed(1)}ms response</span>
            )}
          </Card>
        ))}
      </div>

      {/* Financial Profile Settings Card */}
      <Card
        title="Financial Profile & Wellness Inputs"
        subtitle="Transparent user inputs required for deterministic wellness scoring and 30-day forecast allowance"
      >
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-5 pt-3">
          <div>
            <label className="text-xs font-semibold text-ink block mb-1">Confirmed Monthly Net Income (₹)</label>
            <input
              type="number"
              value={income}
              onChange={(e) => setIncome(e.target.value)}
              className="w-full px-3 py-2 text-xs rounded-lg border border-line bg-canvas text-ink focus:outline-none focus:ring-1 focus:ring-accent"
            />
            <p className="text-[10px] text-muted mt-1">Used for savings discipline & debt burden ceiling</p>
          </div>

          <div>
            <label className="text-xs font-semibold text-ink block mb-1">Confirmed Monthly Debt Payments (₹)</label>
            <input
              type="number"
              value={debt}
              onChange={(e) => setDebt(e.target.value)}
              className="w-full px-3 py-2 text-xs rounded-lg border border-line bg-canvas text-ink focus:outline-none focus:ring-1 focus:ring-accent"
            />
            <p className="text-[10px] text-muted mt-1">EMIs and personal loan repayments</p>
          </div>

          <div>
            <label className="text-xs font-semibold text-ink block mb-1">Liquid Emergency Reserves (₹)</label>
            <input
              type="number"
              value={reserve}
              onChange={(e) => setReserve(e.target.value)}
              className="w-full px-3 py-2 text-xs rounded-lg border border-line bg-canvas text-ink focus:outline-none focus:ring-1 focus:ring-accent"
            />
            <p className="text-[10px] text-muted mt-1">Liquid savings dedicated for 3-month reserve coverage</p>
          </div>
        </div>

        <div className="flex justify-end pt-4 mt-4 border-t border-line">
          <Button variant="primary" size="sm" loading={savingProfile} onClick={handleUpdateProfile}>
            Save Profile & Re-run Orchestrator
          </Button>
        </div>
      </Card>

      {/* Scheduled Obligations Table */}
      <Card title="Confirmed Scheduled Obligations">
        <div className="overflow-x-auto pt-2">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="border-b border-line bg-sunken/40 text-muted font-semibold">
                <th className="py-2.5 px-3">Title</th>
                <th className="py-2.5 px-3">Type</th>
                <th className="py-2.5 px-3">Day of Month</th>
                <th className="py-2.5 px-3 text-right">Amount</th>
                <th className="py-2.5 px-3 text-center">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-line">
              {obligations.map((ob) => (
                <tr key={ob.obligation_id} className="hover:bg-sunken/30">
                  <td className="py-2.5 px-3 font-medium text-ink">{ob.title}</td>
                  <td className="py-2.5 px-3"><Badge variant="default" className="text-[10px]">{ob.obligation_type}</Badge></td>
                  <td className="py-2.5 px-3 font-mono text-muted">{ob.day_of_month}th of month</td>
                  <td className={`py-2.5 px-3 text-right font-semibold ${
                    ob.direction === "CREDIT" ? "text-pass" : "text-ink"
                  }`}>
                    {ob.direction === "CREDIT" ? "+" : "-"}₹{Number(ob.amount).toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                  </td>
                  <td className="py-2.5 px-3 text-center">
                    <Badge variant="pass" className="text-[10px]">Confirmed</Badge>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      {/* Orchestration Runs Telemetry Table */}
      <Card title="Agent Orchestration Run Logs (Spec Page 6, 12)">
        <div className="overflow-x-auto pt-2">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="border-b border-line bg-sunken/40 text-muted font-semibold">
                <th className="py-2.5 px-3">Run ID</th>
                <th className="py-2.5 px-3">Data Version</th>
                <th className="py-2.5 px-3">Executed Stages</th>
                <th className="py-2.5 px-3 text-right">Duration</th>
                <th className="py-2.5 px-3 text-right">Timestamp</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-line">
              {runs.map((r) => (
                <tr key={r.run_id} className="hover:bg-sunken/30">
                  <td className="py-2.5 px-3 font-mono font-medium text-accent">{r.run_id}</td>
                  <td className="py-2.5 px-3 font-mono text-muted">{r.data_version}</td>
                  <td className="py-2.5 px-3 text-muted text-[11px]">
                    {r.stages_executed.slice(0, 4).join(" → ")}...
                  </td>
                  <td className="py-2.5 px-3 text-right font-mono text-ink">{r.total_duration_ms.toFixed(1)}ms</td>
                  <td className="py-2.5 px-3 text-right text-muted">{new Date(r.computed_at).toLocaleTimeString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}
