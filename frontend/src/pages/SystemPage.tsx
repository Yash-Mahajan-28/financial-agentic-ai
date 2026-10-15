import React, { useState, useEffect } from "react";
import { Settings, ShieldCheck, Activity, Cpu, Database, RefreshCw, CheckCircle2, User, Calendar, Network, ArrowRight, RotateCw, CheckCircle } from "lucide-react";
import { Card, Badge, Button, LoadingState } from "../components/ui";
import { api } from "../services/api";
import { SystemStatus, AgentRunRecord, UserProfile, ObligationItem } from "../types";

export default function SystemPage() {
  const [status, setStatus] = useState<SystemStatus | null>(null);
  const [runs, setRuns] = useState<AgentRunRecord[]>([]);
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [obligations, setObligations] = useState<ObligationItem[]>([]);
  const [graphMeta, setGraphMeta] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  // Edit profile state
  const [income, setIncome] = useState("50000.00");
  const [debt, setDebt] = useState("7000.00");
  const [reserve, setReserve] = useState("75000.00");
  const [savingProfile, setSavingProfile] = useState(false);

  const loadData = async () => {
    setLoading(true);
    try {
      const [st, r, p, obs, gm] = await Promise.all([
        api.getSystemStatus(),
        api.getSystemRuns(),
        api.getMe(),
        api.getObligations(),
        api.getAgentGraphMetadata()
      ]);
      setStatus(st);
      setRuns(r || []);
      setProfile(p);
      setObligations(obs || []);
      setGraphMeta(gm);
      if (p) {
        if (p.confirmed_net_income !== undefined && p.confirmed_net_income !== null) setIncome(String(p.confirmed_net_income));
        if (p.confirmed_monthly_debt !== undefined && p.confirmed_monthly_debt !== null) setDebt(String(p.confirmed_monthly_debt));
        if (p.liquid_emergency_reserve !== undefined && p.liquid_emergency_reserve !== null) setReserve(String(p.liquid_emergency_reserve));
      }
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
        <h1 className="text-2xl font-bold text-ink tracking-tight flex items-center gap-2">
          System Health & Agentic Architecture
          <Badge variant="pass" className="text-xs">LangGraph Active</Badge>
        </h1>
        <p className="text-sm text-muted mt-1">
          Measured service readiness, LangGraph multi-agent orchestration traces, and syllabus alignment.
        </p>
      </div>

      {/* Services Health Status */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        {status?.services && Object.entries(status.services).map(([key, svc]) => (
          <Card key={key} className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold uppercase tracking-wider text-muted">{svc.name}</span>
              <Badge variant={svc.status === "HEALTHY" ? "pass" : "warn"} className="text-[10px]">
                {svc.status}
              </Badge>
            </div>
            <p className="text-xs text-ink font-medium">{svc.details || "Active"}</p>
            {typeof svc.latency_ms === "number" && (
              <span className="text-[10px] text-faint block">{svc.latency_ms.toFixed(1)}ms response</span>
            )}
          </Card>
        ))}
      </div>

      {/* LangGraph Multi-Agent Architecture (Syllabus Micro Project #10 & Module 2/4) */}
      <Card
        title="LangGraph Multi-Agent Orchestration Architecture"
        subtitle="Autonomous Planner-Reviewer StateGraph with cyclic self-correction & formal LangChain tools (VESIT Syllabus 26CMPC72)"
      >
        <div className="space-y-6 pt-2">
          {/* Architecture Badges Header */}
          <div className="flex flex-wrap items-center gap-2 pb-4 border-b border-line">
            <Badge variant="pass" className="text-xs px-2.5 py-1">
              Framework: {graphMeta?.framework || "LangGraph 1.2.15 + LangChain 1.4.5"}
            </Badge>
            <Badge variant="default" className="text-xs px-2.5 py-1">
              Pattern: Planner-Reviewer Pipeline (Micro Project #10)
            </Badge>
            <Badge variant="warn" className="text-xs px-2.5 py-1 flex items-center gap-1">
              <RotateCw className="h-3 w-3" />
              Workflow: Cyclic StateGraph with Self-Healing
            </Badge>
          </div>

          {/* Interactive Multi-Agent Node Visualizer */}
          <div className="grid grid-cols-1 md:grid-cols-5 gap-3">
            {/* Node 1: Planner Agent */}
            <div className="p-3.5 rounded-xl border border-accent/30 bg-accent/5 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-bold text-accent uppercase tracking-wide">Node 1</span>
                <Badge variant="default" className="text-[9px]">Planner</Badge>
              </div>
              <h4 className="text-xs font-bold text-ink">Planner Agent</h4>
              <p className="text-[11px] text-muted leading-relaxed">
                Decomposes financial audit request into structured 8-step execution plan across worker roles.
              </p>
              <div className="pt-1 text-[10px] text-accent font-semibold flex items-center gap-1">
                Output: Strategic Plan <ArrowRight className="h-3 w-3" />
              </div>
            </div>

            {/* Node 2: Domain Executors */}
            <div className="p-3.5 rounded-xl border border-line bg-canvas space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-bold text-muted uppercase tracking-wide">Node 2</span>
                <Badge variant="default" className="text-[9px]">6 Tools</Badge>
              </div>
              <h4 className="text-xs font-bold text-ink">Domain Workers</h4>
              <p className="text-[11px] text-muted leading-relaxed">
                Executes LangChain tools: Spending, 50/30/20 Budget, MAD Outliers, Subscriptions, Runway, Wellness.
              </p>
              <div className="pt-1 text-[10px] text-ink font-semibold flex items-center gap-1">
                Output: Raw Artifacts <ArrowRight className="h-3 w-3" />
              </div>
            </div>

            {/* Node 3: Synthesis Agent */}
            <div className="p-3.5 rounded-xl border border-line bg-canvas space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-bold text-muted uppercase tracking-wide">Node 3</span>
                <Badge variant="default" className="text-[9px]">Analyst</Badge>
              </div>
              <h4 className="text-xs font-bold text-ink">Synthesis Agent</h4>
              <p className="text-[11px] text-muted leading-relaxed">
                Synthesizes prioritized draft recommendations ranked by cash shortfall urgency & budget risks.
              </p>
              <div className="pt-1 text-[10px] text-ink font-semibold flex items-center gap-1">
                Output: Draft Insights <ArrowRight className="h-3 w-3" />
              </div>
            </div>

            {/* Node 4: Reviewer / Validator */}
            <div className="p-3.5 rounded-xl border border-warn/40 bg-warn/5 space-y-2 relative overflow-hidden">
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-bold text-warn uppercase tracking-wide">Node 4</span>
                <Badge variant="warn" className="text-[9px]">Critic</Badge>
              </div>
              <h4 className="text-xs font-bold text-ink">Reviewer Validator</h4>
              <p className="text-[11px] text-muted leading-relaxed">
                Audits against mathematical invariance, read-only safety guardrails, and verifiable evidence.
              </p>
              <div className="pt-1 text-[10px] text-warn font-semibold flex items-center gap-1">
                Loop: Self-Correction if invalid
              </div>
            </div>

            {/* Node 5: Publisher */}
            <div className="p-3.5 rounded-xl border border-pass/40 bg-pass/5 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-bold text-pass uppercase tracking-wide">Node 5</span>
                <Badge variant="pass" className="text-[9px]">Publisher</Badge>
              </div>
              <h4 className="text-xs font-bold text-ink">Publisher Node</h4>
              <p className="text-[11px] text-muted leading-relaxed">
                Atomically commits approved insights to SQLite/Postgres and dispatches in-app notifications.
              </p>
              <div className="pt-1 text-[10px] text-pass font-semibold flex items-center gap-1">
                <CheckCircle className="h-3 w-3" /> Published & Notified
              </div>
            </div>
          </div>

          {/* Syllabus Module Cross-Reference */}
          <div className="p-3 rounded-lg bg-sunken/40 border border-line text-xs space-y-2">
            <span className="font-semibold text-ink block">Curriculum Alignment Matrix (Course 26CMPC72):</span>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 text-[11px] text-muted">
              <div>• <strong>Module 1:</strong> Schema-constrained execution & guardrails</div>
              <div>• <strong>Module 2:</strong> StateGraph DAGs & cyclic feedback loops</div>
              <div>• <strong>Module 3:</strong> Formal @tool abstractions & pipelines</div>
              <div>• <strong>Module 4:</strong> Role-based multi-agent coordination</div>
              <div>• <strong>Module 5:</strong> AI observability & runtime safety</div>
              <div>• <strong>Micro Project 10:</strong> Full Planner-Reviewer Pipeline</div>
            </div>
          </div>
        </div>
      </Card>

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
                    {Array.isArray(r.stages_executed) ? `${r.stages_executed.slice(0, 4).join(" → ")}...` : "—"}
                  </td>
                  <td className="py-2.5 px-3 text-right font-mono text-ink">
                    {typeof r.total_duration_ms === "number" ? `${r.total_duration_ms.toFixed(1)}ms` : "—"}
                  </td>
                  <td className="py-2.5 px-3 text-right text-muted">
                    {r.computed_at ? new Date(r.computed_at).toLocaleTimeString() : "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}
