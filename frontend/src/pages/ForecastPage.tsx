import React, { useState, useEffect } from "react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine
} from "recharts";
import { TrendingUp, AlertOctagon, Sliders, CheckCircle2, ArrowRight } from "lucide-react";
import { Card, Badge, Button, LoadingState } from "../components/ui";
import { api } from "../services/api";
import { ForecastData, ScenarioSimulationResult } from "../types";

export default function ForecastPage() {
  const [data, setData] = useState<ForecastData | null>(null);
  const [loading, setLoading] = useState(true);

  // Scenario Simulator controls
  const [removeSalary, setRemoveSalary] = useState(false);
  const [extraExpense, setExtraExpense] = useState(0);
  const [spendMultiplier, setSpendMultiplier] = useState(1.0);
  const [simResult, setSimResult] = useState<ScenarioSimulationResult | null>(null);
  const [simulating, setSimulating] = useState(false);

  const loadForecast = async () => {
    setLoading(true);
    try {
      const res = await api.getForecast();
      setData(res);
    } catch (err) {
      console.error("Failed to load forecast", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadForecast();
  }, []);

  const handleSimulate = async () => {
    setSimulating(true);
    try {
      const res = await api.simulateScenario({
        scenario_name: "Interactive Simulation",
        remove_salary: removeSalary,
        extra_one_time_expense: extraExpense,
        variable_spend_multiplier: spendMultiplier
      });
      setSimResult(res);
    } catch (err) {
      console.error("Failed to simulate scenario", err);
    } finally {
      setSimulating(false);
    }
  };

  if (loading || !data) {
    return <LoadingState message="Projecting 30-day cash curve with intra-day outflow ordering..." />;
  }

  // Prepare chart data
  const chartData = (simResult ? simResult.scenario_timeline : data.timeline).map((t, idx) => ({
    date: t.date.slice(5), // MM-DD
    baseline: Number(data.timeline[idx]?.closing_balance || 0),
    scenario: Number(t.closing_balance),
    inflows: Number(t.inflows),
    outflows: Number(t.outflows),
    events: t.events
  }));

  const activeShortfall = simResult ? simResult.has_shortfall : data.has_shortfall;
  const activeShortfallDate = simResult ? simResult.first_shortfall_date : data.first_shortfall_date;

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-ink tracking-tight">30-Day Cash Flow Forecast</h1>
        <p className="text-sm text-muted mt-1">
          Conservative projection deducting intra-day outflows before inflows to expose temporary liquidity dips (Spec Page 11).
        </p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
        <Card>
          <span className="text-xs text-muted font-medium">Opening Liquid Balance</span>
          <p className="text-xl font-bold text-ink mt-1">₹{Number(data.opening_liquid_balance).toLocaleString("en-IN")}</p>
          <span className="text-[11px] text-faint">As of {data.balance_as_of}</span>
        </Card>

        <Card>
          <span className="text-xs text-muted font-medium">Projected Closing (Day 30)</span>
          <p className={`text-xl font-bold mt-1 ${
            (simResult ? Number(simResult.scenario_closing_balance) : Number(data.projected_closing_balance)) < 0
              ? "text-fail"
              : "text-pass"
          }`}>
            ₹{Number(simResult ? simResult.scenario_closing_balance : data.projected_closing_balance).toLocaleString("en-IN")}
          </p>
          <span className="text-[11px] text-faint">
            {simResult ? `Diff: ₹${Number(simResult.net_impact).toFixed(2)}` : "Baseline projection"}
          </span>
        </Card>

        <Card>
          <span className="text-xs text-muted font-medium">Minimum Intra-Day Balance</span>
          <p className={`text-xl font-bold mt-1 ${
            Number(data.minimum_projected_balance) < 0 ? "text-fail" : "text-ink"
          }`}>
            ₹{Number(data.minimum_projected_balance).toLocaleString("en-IN")}
          </p>
          <span className="text-[11px] text-faint">On {data.minimum_balance_date}</span>
        </Card>

        <Card>
          <span className="text-xs text-muted font-medium">Daily Variable Allowance</span>
          <p className="text-xl font-bold text-ink mt-1">₹{Number(data.variable_daily_allowance).toFixed(2)}/day</p>
          <span className="text-[11px] text-faint">₹{Number(data.variable_daily_allowance * 30).toLocaleString("en-IN")} total horizon</span>
        </Card>
      </div>

      {/* Shortfall Alert Banner */}
      {activeShortfall && (
        <div className="p-4 rounded-xl bg-fail-soft border border-fail/20 flex items-start gap-3 text-fail">
          <AlertOctagon className="h-5 w-5 shrink-0 mt-0.5" />
          <div className="text-xs">
            <p className="font-semibold text-sm">Critical Liquidity Shortfall Warning</p>
            <p className="mt-0.5 text-fail/90">
              The projected cash curve enters negative liquidity on <span className="font-bold underline">{activeShortfallDate}</span>.
              Review confirmed bill dates or arrange emergency liquid reserves to avoid default.
            </p>
          </div>
        </div>
      )}

      {/* Forecast Chart */}
      <Card title="30-Day Liquidity Timeline">
        <div className="h-80 w-full pt-4">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={chartData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
              <defs>
                <linearGradient id="curveColor" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="rgb(var(--accent))" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="rgb(var(--accent))" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="scenarioColor" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="rgb(var(--fail))" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="rgb(var(--fail))" stopOpacity={0} />
                </linearGradient>
              </defs>
              <XAxis dataKey="date" stroke="rgb(var(--faint))" fontSize={11} tickLine={false} />
              <YAxis stroke="rgb(var(--faint))" fontSize={11} tickLine={false} tickFormatter={(v) => `₹${v / 1000}k`} />
              <Tooltip
                content={({ active, payload }: any) => {
                  if (active && payload && payload.length) {
                    const d = payload[0].payload;
                    return (
                      <div className="rounded-lg border border-line bg-surface p-3 shadow-lg text-xs space-y-1">
                        <p className="font-bold text-ink">{d.date}</p>
                        <p className="text-accent font-semibold">Balance: ₹{d.scenario.toLocaleString("en-IN")}</p>
                        <p className="text-pass">Inflows: +₹{d.inflows.toLocaleString("en-IN")}</p>
                        <p className="text-fail">Outflows: -₹{d.outflows.toLocaleString("en-IN")}</p>
                        {d.events.length > 0 && (
                          <div className="pt-1 border-t border-line text-[11px] text-muted">
                            {d.events.map((e: string, i: number) => <div key={i}>• {e}</div>)}
                          </div>
                        )}
                      </div>
                    );
                  }
                  return null;
                }}
              />
              <ReferenceLine y={0} stroke="rgb(var(--fail))" strokeDasharray="3 3" />
              <Area
                type="monotone"
                dataKey="scenario"
                stroke={simResult ? "rgb(var(--fail))" : "rgb(var(--accent))"}
                strokeWidth={2}
                fillOpacity={1}
                fill={simResult ? "url(#scenarioColor)" : "url(#curveColor)"}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </Card>

      {/* Interactive Scenario Sandbox */}
      <Card
        title={
          <div className="flex items-center gap-2">
            <Sliders className="h-4 w-4 text-accent" />
            <span>Interactive Scenario Simulator</span>
          </div>
        }
        subtitle="Stress-test cash flow resilience against simulated salary disruption or unexpected expenses (Spec Page 11)"
      >
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 pt-2">
          {/* Salary Delay Toggle */}
          <div className="p-4 rounded-xl border border-line bg-canvas space-y-2">
            <label className="text-xs font-semibold text-ink block">Simulate Salary Omission</label>
            <p className="text-[11px] text-muted">Excludes April 5 paycheck (+₹50,000) from projection</p>
            <div className="pt-2">
              <label className="flex items-center gap-2 cursor-pointer text-xs font-medium text-ink">
                <input
                  type="checkbox"
                  checked={removeSalary}
                  onChange={(e) => setRemoveSalary(e.target.checked)}
                  className="rounded border-line text-fail focus:ring-fail"
                />
                <span>Remove April Salary Inflow</span>
              </label>
            </div>
          </div>

          {/* Extra Expense Input */}
          <div className="p-4 rounded-xl border border-line bg-canvas space-y-2">
            <label className="text-xs font-semibold text-ink block">One-Time Emergency Expense</label>
            <p className="text-[11px] text-muted">Add simulated medical or urgent debit on Day 15</p>
            <input
              type="number"
              step="1000"
              value={extraExpense}
              onChange={(e) => setExtraExpense(parseFloat(e.target.value) || 0)}
              placeholder="e.g. 15000"
              className="w-full px-3 py-1.5 text-xs rounded-lg border border-line bg-surface text-ink focus:outline-none"
            />
          </div>

          {/* Variable Spend Multiplier */}
          <div className="p-4 rounded-xl border border-line bg-canvas space-y-2">
            <label className="text-xs font-semibold text-ink block">
              Variable Spending Rate: {(spendMultiplier * 100).toFixed(0)}%
            </label>
            <p className="text-[11px] text-muted">Adjust daily cash spending allowance multiplier</p>
            <input
              type="range"
              min="0.5"
              max="2.0"
              step="0.1"
              value={spendMultiplier}
              onChange={(e) => setSpendMultiplier(parseFloat(e.target.value))}
              className="w-full"
            />
          </div>
        </div>

        <div className="flex justify-end gap-3 mt-4 pt-4 border-t border-line">
          {simResult && (
            <Button
              variant="secondary"
              size="sm"
              onClick={() => {
                setSimResult(null);
                setRemoveSalary(false);
                setExtraExpense(0);
                setSpendMultiplier(1.0);
              }}
            >
              Reset to Baseline
            </Button>
          )}
          <Button variant="primary" size="sm" loading={simulating} onClick={handleSimulate}>
            Run Scenario Stress-Test
          </Button>
        </div>
      </Card>
    </div>
  );
}
