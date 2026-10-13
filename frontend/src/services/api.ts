import {
  DashboardSummary,
  PaginatedTransactions,
  Transaction,
  BudgetUtilizationItem,
  FiftyThirtyTwentyTemplate,
  InsightItem,
  AlertItem,
  ForecastData,
  ScenarioSimulationResult,
  ChatMessage,
  AccountItem,
  ObligationItem,
  SystemStatus,
  AgentRunRecord,
  UserProfile
} from "../types";

const BASE_URL = "/api/v1";

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${BASE_URL}${endpoint}`;
  const headers = {
    "Content-Type": "application/json",
    ...(options.headers || {})
  };

  const res = await fetch(url, {
    ...options,
    headers: options.body instanceof FormData ? undefined : headers,
    credentials: "include"
  });

  if (!res.ok) {
    let errMessage = `HTTP error ${res.status}`;
    try {
      const errJson = await res.json();
      errMessage = errJson.detail || errJson.message || errMessage;
    } catch {}
    throw new Error(errMessage);
  }

  return res.json() as Promise<T>;
}

export const api = {
  // Auth
  getMe: () => request<UserProfile>("/auth/me"),
  updateProfile: (data: Partial<UserProfile>) =>
    request<UserProfile>("/auth/profile", { method: "PATCH", body: JSON.stringify(data) }),

  // Dashboard
  getDashboard: () => request<DashboardSummary>("/dashboard"),

  // Ledger & Transactions
  getTransactions: (params: {
    page?: number;
    page_size?: number;
    month?: string;
    account_id?: string;
    category?: string;
    review_state?: string;
    search?: string;
  }) => {
    const query = new URLSearchParams();
    if (params.page) query.set("page", params.page.toString());
    if (params.page_size) query.set("page_size", params.page_size.toString());
    if (params.month) query.set("month", params.month);
    if (params.account_id) query.set("account_id", params.account_id);
    if (params.category && params.category !== "ALL") query.set("category", params.category);
    if (params.review_state && params.review_state !== "ALL") query.set("review_state", params.review_state);
    if (params.search) query.set("search", params.search);
    return request<PaginatedTransactions>(`/transactions?${query.toString()}`);
  },

  updateTransactionCategory: (txId: string, category: string, applyToMerchant = false) =>
    request<Transaction>(`/transactions/${txId}`, {
      method: "PATCH",
      body: JSON.stringify({ category, apply_to_merchant: applyToMerchant })
    }),

  getExportCsvUrl: (month?: string) => `/api/v1/exports/transactions.csv${month ? `?month=${month}` : ""}`,

  // Ingestion & Uploads
  uploadStatement: (file: File, accountId: string, period?: string) => {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("account_id", accountId);
    if (period) formData.append("period", period);
    return request<{ upload_id: string; job_id: string; message: string; status: string }>("/uploads", {
      method: "POST",
      body: formData
    });
  },

  getJobStatus: (jobId: string) => request<any>(`/jobs/${jobId}`),

  // Budgets
  getBudget: (month: string) => request<{ month: string; limits: Record<string, number>; utilization_summary: any }>(`/budgets/${month}`),

  updateBudget: (month: string, limits: Record<string, number>) =>
    request<{ message: string }>(`/budgets/${month}`, {
      method: "PUT",
      body: JSON.stringify({ month, limits })
    }),

  get503020Template: () => request<FiftyThirtyTwentyTemplate>("/budgets/templates/50-30-20"),

  // Insights & Alerts
  getInsights: (type?: string, severity?: string) => {
    const query = new URLSearchParams();
    if (type) query.set("insight_type", type);
    if (severity) query.set("severity", severity);
    return request<InsightItem[]>(`/insights?${query.toString()}`);
  },

  getAlerts: (status?: string) => {
    const query = new URLSearchParams();
    if (status) query.set("status_filter", status);
    return request<AlertItem[]>(`/alerts?${query.toString()}`);
  },

  updateAlertStatus: (alertId: string, status: "ACKNOWLEDGED" | "RESOLVED", notes?: string) =>
    request<AlertItem>(`/alerts/${alertId}`, {
      method: "PATCH",
      body: JSON.stringify({ status, resolution_notes: notes })
    }),

  // Forecast & Scenarios
  getForecast: () => request<ForecastData>("/forecast"),

  simulateScenario: (scenario: {
    scenario_name: string;
    remove_salary: boolean;
    extra_one_time_expense?: number;
    extra_expense_day?: number;
    variable_spend_multiplier?: number;
  }) =>
    request<ScenarioSimulationResult>("/scenarios", {
      method: "POST",
      body: JSON.stringify(scenario)
    }),

  // Conversational Advisor
  sendAdvisorChat: (message: string, history: ChatMessage[]) =>
    request<{
      answer: string;
      tool_calls: any[];
      cited_insights: string[];
      cited_transactions: string[];
      suggested_follow_ups: string[];
    }>("/advisor/chat", {
      method: "POST",
      body: JSON.stringify({ message, conversation_history: history })
    }),

  // Accounts & Obligations
  getAccounts: () => request<AccountItem[]>("/accounts"),

  updateAccountBalance: (accountId: string, balance: number, balanceAsOf: string) =>
    request<{ message: string }>(`/accounts/${accountId}/balance`, {
      method: "PUT",
      body: JSON.stringify({ balance, balance_as_of: balanceAsOf })
    }),

  getObligations: () => request<ObligationItem[]>("/obligations"),

  createObligation: (data: Omit<ObligationItem, "obligation_id">) =>
    request<{ message: string; obligation_id: string }>("/obligations", {
      method: "POST",
      body: JSON.stringify(data)
    }),

  // System
  getSystemStatus: () => request<SystemStatus>("/system/status"),
  getSystemRuns: () => request<AgentRunRecord[]>("/system/runs"),
  getAgentGraphMetadata: () =>
    request<{
      framework: string;
      pattern: string;
      syllabus_mapping: Record<string, string>;
      nodes: Array<{ id: string; label: string; role: string; description: string }>;
      edges: Array<{ source: string; target: string; type: string; condition?: string }>;
    }>("/system/agent-graph")
};
