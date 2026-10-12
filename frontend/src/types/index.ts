export interface UserProfile {
  user_id: string;
  email: string;
  full_name: string;
  currency: string;
  confirmed_net_income: number;
  confirmed_monthly_debt: number;
  liquid_emergency_reserve: number;
  target_savings_rate: number;
  debt_burden_ceiling: number;
  reserve_target_months: number;
}

export interface WellnessScore {
  score: number | null;
  status: "COMPLETE" | "INCOMPLETE";
  savings_discipline: number | null;
  budget_discipline: number | null;
  debt_burden: number | null;
  reserve_coverage: number | null;
  formula_version: string;
  explanation?: string;
}

export interface DashboardSummary {
  period: string;
  data_version: string;
  computed_at: string | null;
  currency: string;
  net_income: number;
  net_spending: number;
  monthly_surplus: number;
  total_budget_limit: number;
  overall_budget_utilization_pct: number;
  wellness_score: WellnessScore;
  active_alerts_count: number;
  data_coverage_months: number;
  latest_statement_date: string | null;
  is_recomputing: boolean;
}

export interface SourceLineage {
  upload_id?: string;
  row_number?: number;
  page_number?: number;
  raw_text: string;
}

export interface Transaction {
  transaction_id: string;
  user_id: string;
  account_id: string;
  date: string;
  description: string;
  amount: number;
  direction: "DEBIT" | "CREDIT";
  currency: string;
  transaction_type: string;
  category: string;
  category_source: string;
  classifier_score: number | null;
  reference: string | null;
  review_state: "APPROVED" | "NEEDS_REVIEW" | "EXCLUDED";
  is_duplicate_candidate: boolean;
  transfer_linked_transaction_id?: string | null;
  created_at: string;
  sources?: SourceLineage[];
}

export interface PaginatedTransactions {
  items: Transaction[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface BudgetUtilizationItem {
  category: string;
  spent: number;
  limit: number;
  remaining: number;
  utilization_pct: number;
  status: "NORMAL" | "WARNING" | "EXCEEDED" | "ZERO_LIMIT_EXCEEDED";
}

export interface FiftyThirtyTwentyTemplate {
  total_income: number;
  needs_limit: number;
  wants_limit: number;
  savings_target: number;
  breakdown: Record<string, number>;
}

export interface InsightItem {
  insight_id: string;
  run_id: string;
  insight_type: "BUDGET_RISK" | "UNUSUAL_EXPENSE" | "RECURRING_CANDIDATE" | "CASH_SHORTFALL" | "SAVINGS_OPPORTUNITY";
  severity: "HIGH" | "MEDIUM" | "LOW" | "INFO";
  observation: string;
  metric: Record<string, any>;
  evidence: Record<string, any>;
  action: string;
  assumptions: string[];
  created_at: string;
}

export interface AlertItem {
  alert_id: string;
  deduplication_key: string;
  insight_id?: string | null;
  title: string;
  message: string;
  severity: "HIGH" | "MEDIUM" | "LOW" | "INFO";
  status: "UNREAD" | "ACKNOWLEDGED" | "RESOLVED";
  resolution_notes?: string | null;
  created_at: string;
  updated_at: string;
}

export interface DailyForecastItem {
  date: string;
  day_number: number;
  opening_balance: number;
  inflows: number;
  outflows: number;
  closing_balance: number;
  events: string[];
}

export interface ForecastData {
  horizon_days: number;
  balance_as_of: string;
  opening_liquid_balance: number;
  projected_closing_balance: number;
  minimum_projected_balance: number;
  minimum_balance_date: string;
  has_shortfall: boolean;
  first_shortfall_date?: string | null;
  variable_daily_allowance: number;
  currency: string;
  timeline: DailyForecastItem[];
}

export interface ScenarioSimulationResult {
  scenario_name: string;
  baseline_closing_balance: number;
  scenario_closing_balance: number;
  net_impact: number;
  has_shortfall: boolean;
  first_shortfall_date?: string | null;
  baseline_timeline: DailyForecastItem[];
  scenario_timeline: DailyForecastItem[];
}

export interface ToolCallRecord {
  tool_name: string;
  arguments: Record<string, any>;
  result: any;
}

export interface ChatMessage {
  role: "user" | "assistant" | "system";
  content: string;
  tool_calls?: ToolCallRecord[];
  cited_insights?: string[];
  cited_transactions?: string[];
}

export interface AccountItem {
  account_id: string;
  account_name: string;
  account_type: "CHECKING" | "SAVINGS" | "CREDIT_CARD";
  account_number_masked: string;
  currency: string;
  balance: number;
  balance_as_of: string;
}

export interface ObligationItem {
  obligation_id: string;
  title: string;
  amount: number;
  direction: "CREDIT" | "DEBIT";
  day_of_month: number;
  category: string;
  obligation_type: "SALARY" | "BILL" | "EMI" | "SUBSCRIPTION";
  account_id: string;
  is_confirmed: boolean;
  is_active: boolean;
}

export interface ServiceHealthItem {
  name: string;
  status: "HEALTHY" | "DEGRADED" | "UNAVAILABLE" | "UNKNOWN";
  latency_ms?: number;
  details?: string;
}

export interface SystemStatus {
  environment: string;
  active_data_version: string;
  overall_health: string;
  services: Record<string, ServiceHealthItem>;
  worker_heartbeat_age_seconds?: number;
  scheduler_heartbeat_age_seconds?: number;
  llm_provider: string;
  timestamp: string;
}

export interface AgentRunRecord {
  run_id: string;
  data_version: string;
  status: string;
  stages_executed: string[];
  total_duration_ms: number;
  computed_at: string;
}
