import React, { useState, useEffect } from "react";
import { AlertTriangle, TrendingDown, Clock, ShieldCheck, CheckCircle2, ChevronRight, Info } from "lucide-react";
import { Card, Badge, Button, Modal, LoadingState } from "../components/ui";
import { api } from "../services/api";
import { InsightItem, AlertItem } from "../types";

export default function InsightsPage() {
  const [insights, setInsights] = useState<InsightItem[]>([]);
  const [alerts, setAlerts] = useState<AlertItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedInsight, setSelectedInsight] = useState<InsightItem | null>(null);
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  const loadData = async () => {
    setLoading(true);
    try {
      const [ins, alt] = await Promise.all([
        api.getInsights(),
        api.getAlerts()
      ]);
      setInsights(ins);
      setAlerts(alt);
    } catch (err) {
      console.error("Failed to load insights", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleAlertAction = async (alertId: string, status: "ACKNOWLEDGED" | "RESOLVED") => {
    setActionLoading(alertId);
    try {
      await api.updateAlertStatus(alertId, status, "Reviewed by user in intelligence center");
      loadData();
    } catch (err) {
      console.error("Failed to update alert", err);
    } finally {
      setActionLoading(null);
    }
  };

  if (loading) {
    return <LoadingState message="Fetching ranked insights and alerts..." />;
  }

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-ink tracking-tight">Intelligence & Insights Center</h1>
        <p className="text-sm text-muted mt-1">
          Ranked recommendations, statistical MAD anomalies, and subscription intelligence (Spec Page 10 & 12).
        </p>
      </div>

      {/* In-App Alerts Management */}
      <div className="space-y-4">
        <h2 className="text-base font-semibold text-ink flex items-center gap-2">
          <AlertTriangle className="h-4 w-4 text-warn" />
          Active Notification Queue ({alerts.filter((a) => a.status === "UNREAD").length} Unread)
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {alerts.map((alt) => (
            <Card
              key={alt.alert_id}
              className={`border-l-4 ${
                alt.status === "RESOLVED"
                  ? "border-l-pass opacity-70"
                  : alt.severity === "HIGH"
                  ? "border-l-fail"
                  : "border-l-warn"
              }`}
            >
              <div className="flex items-start justify-between">
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <span className="font-semibold text-sm text-ink">{alt.title}</span>
                    <Badge variant={alt.status === "RESOLVED" ? "pass" : alt.severity === "HIGH" ? "fail" : "warn"}>
                      {alt.status}
                    </Badge>
                  </div>
                  <p className="text-xs text-muted leading-relaxed">{alt.message}</p>
                </div>
              </div>

              {alt.status !== "RESOLVED" && (
                <div className="flex justify-end gap-2 pt-3 mt-3 border-t border-line">
                  {alt.status === "UNREAD" && (
                    <Button
                      variant="secondary"
                      size="sm"
                      loading={actionLoading === alt.alert_id}
                      onClick={() => handleAlertAction(alt.alert_id, "ACKNOWLEDGED")}
                    >
                      Acknowledge Review
                    </Button>
                  )}
                  <Button
                    variant="primary"
                    size="sm"
                    loading={actionLoading === alt.alert_id}
                    onClick={() => handleAlertAction(alt.alert_id, "RESOLVED")}
                  >
                    Mark Resolved
                  </Button>
                </div>
              )}
            </Card>
          ))}
        </div>
      </div>

      {/* Ranked Insights List */}
      <div className="space-y-4 pt-4">
        <h2 className="text-base font-semibold text-ink flex items-center gap-2">
          <Info className="h-4 w-4 text-accent" />
          Deterministic Ranked Insights
        </h2>

        <div className="space-y-3">
          {insights.map((ins) => (
            <Card key={ins.insight_id} className="hover:border-accent/40 transition-colors">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-sm text-ink">{ins.observation}</span>
                    <Badge variant={ins.severity === "HIGH" ? "fail" : ins.severity === "MEDIUM" ? "warn" : "accent"}>
                      {ins.severity}
                    </Badge>
                    <span className="text-[11px] text-faint font-mono">[{ins.insight_type}]</span>
                  </div>
                  <p className="text-xs text-accent font-medium">Proposed Action: {ins.action}</p>
                </div>

                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => setSelectedInsight(ins)}
                  className="gap-1 text-xs shrink-0"
                >
                  Inspect Evidence <ChevronRight className="h-3.5 w-3.5" />
                </Button>
              </div>
            </Card>
          ))}
        </div>
      </div>

      {/* Insight Evidence Modal */}
      <Modal
        isOpen={!!selectedInsight}
        onClose={() => setSelectedInsight(null)}
        title="Mathematical Evidence & Provenance"
      >
        {selectedInsight && (
          <div className="space-y-4 text-xs">
            <div className="p-3 rounded-lg bg-sunken space-y-1">
              <p className="font-semibold text-ink">{selectedInsight.observation}</p>
              <p className="text-muted">Insight Reference: {selectedInsight.insight_id}</p>
            </div>

            <div className="space-y-1">
              <h4 className="font-semibold text-ink">Recorded Metrics:</h4>
              <pre className="p-3 rounded-lg bg-canvas border border-line font-mono text-[11px] text-ink overflow-x-auto">
                {JSON.stringify(selectedInsight.metric, null, 2)}
              </pre>
            </div>

            <div className="space-y-1">
              <h4 className="font-semibold text-ink">Evidence Data:</h4>
              <pre className="p-3 rounded-lg bg-canvas border border-line font-mono text-[11px] text-ink overflow-x-auto">
                {JSON.stringify(selectedInsight.evidence, null, 2)}
              </pre>
            </div>

            <div className="space-y-1">
              <h4 className="font-semibold text-ink">Underlying Assumptions:</h4>
              <ul className="list-disc list-inside text-muted space-y-1">
                {selectedInsight.assumptions.map((a, i) => (
                  <li key={i}>{a}</li>
                ))}
              </ul>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
}
