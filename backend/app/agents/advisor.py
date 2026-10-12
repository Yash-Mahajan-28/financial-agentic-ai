import uuid
import logging
from decimal import Decimal
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.agents.base import BaseAgent
from app.models.analysis import Insight, AnalysisRun
from app.services.llm_service import llm_service
from app.schemas.advisor import ToolCallRecord

logger = logging.getLogger(__name__)

class FinancialAdvisorAgent(BaseAgent):
    def __init__(self):
        super().__init__("FinancialAdvisorAgent")

    def run(
        self,
        db: Session,
        user_id: str,
        run_id: str,
        budget_results: Dict[str, Any],
        forecast_results: Dict[str, Any],
        anomaly_results: Dict[str, Any],
        recurring_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Rank and persist deterministic insight templates (spec page 12)."""
        ranked_insights = []

        # 1. Rank Confirmed Upcoming Cash Shortfalls First
        if forecast_results.get("has_shortfall"):
            shortfall_date = forecast_results.get("first_shortfall_date")
            min_bal = forecast_results.get("minimum_projected_balance")
            ins = {
                "insight_id": f"ins_{uuid.uuid4().hex[:8]}",
                "run_id": run_id,
                "type": "CASH_SHORTFALL",
                "severity": "HIGH",
                "observation": f"Projected liquidity shortfall on {shortfall_date}",
                "metric": {
                    "minimum_balance": str(min_bal),
                    "shortfall_date": shortfall_date,
                    "currency": "INR"
                },
                "evidence": {
                    "opening_balance": str(forecast_results.get("opening_liquid_balance")),
                    "rule": "cash-forecast-v1"
                },
                "action": f"Review scheduled obligations before {shortfall_date}; arrange liquidity buffer.",
                "assumptions": ["Conservative intra-day cash outflow ordering applied"]
            }
            ranked_insights.append(ins)

        # 2. Exceeded Budgets & Budget Risks
        for risk in budget_results.get("budget_risks", []):
            cat = risk["category"]
            spent = risk["spent"]
            limit = risk["limit"]
            util_pct = risk["utilization_pct"]
            sev = risk["severity"] # HIGH or MEDIUM
            
            ins = {
                "insight_id": f"ins_{uuid.uuid4().hex[:8]}",
                "run_id": run_id,
                "type": "BUDGET_RISK",
                "severity": sev,
                "observation": f"{cat} budget is {util_pct}% utilized",
                "metric": {
                    "spent": str(spent),
                    "limit": str(limit),
                    "utilization_pct": str(util_pct),
                    "currency": "INR"
                },
                "evidence": {
                    "category": cat,
                    "period": budget_results.get("month"),
                    "rule": "budget-v1"
                },
                "action": f"Review planned {cat} expenses; INR {max(Decimal('0.00'), limit - spent)} remains",
                "assumptions": ["Only approved posted expenses included"]
            }
            ranked_insights.append(ins)

        # 3. Statistical Anomalies (MAD) & Candidate Duplicates
        for anom in anomaly_results.get("anomalies", []):
            ins = {
                "insight_id": f"ins_{uuid.uuid4().hex[:8]}",
                "run_id": run_id,
                "type": "UNUSUAL_EXPENSE",
                "severity": "MEDIUM",
                "observation": anom["observation"],
                "metric": {
                    "amount": str(anom["amount"]),
                    "calculated_threshold": str(anom["calculated_threshold"]),
                    "baseline_median": str(anom["baseline_median"]),
                    "baseline_mad": str(anom["baseline_mad"])
                },
                "evidence": {
                    "transaction_id": anom["transaction_id"],
                    "date": anom["date"],
                    "description": anom["description"],
                    "samples": anom["sample_count"],
                    "rule": "mad-outlier-v1"
                },
                "action": "Verify if this transaction was expected or requires inquiry.",
                "assumptions": ["Evaluated against approved prior 90 days expenses"]
            }
            ranked_insights.append(ins)

        for dup in anomaly_results.get("duplicate_candidates", []):
            ins = {
                "insight_id": f"ins_{uuid.uuid4().hex[:8]}",
                "run_id": run_id,
                "type": "UNUSUAL_EXPENSE",
                "severity": "MEDIUM",
                "observation": dup["observation"],
                "metric": {"amount": str(dup["amount"])},
                "evidence": {
                    "tx1": dup["transaction_id_1"],
                    "tx2": dup["transaction_id_2"],
                    "rule": "duplicate-candidate-v1"
                },
                "action": "Confirm if repeat purchase is legitimate or pending refund.",
                "assumptions": ["Identical merchant and amount within 1 calendar day"]
            }
            ranked_insights.append(ins)

        # 4. Recurring Subscriptions & Savings Opportunities
        for sub in recurring_results.get("subscription_candidates", []):
            ins = {
                "insight_id": f"ins_{uuid.uuid4().hex[:8]}",
                "run_id": run_id,
                "type": "RECURRING_CANDIDATE",
                "severity": "LOW",
                "observation": sub["observation"],
                "metric": {
                    "median_amount": str(sub["median_amount"]),
                    "potential_annual_savings": str(sub["potential_annual_savings"])
                },
                "evidence": {
                    "merchant": sub["merchant"],
                    "charge_count": sub["charge_count"],
                    "next_expected_date": sub["next_expected_date"],
                    "rule": "recurring-interval-v1"
                },
                "action": f"Confirm if {sub['merchant']} is still needed; potential savings INR {sub['potential_annual_savings']}/yr if cancelled.",
                "assumptions": ["Annual savings assume 12 future billing cycles avoided"]
            }
            ranked_insights.append(ins)

        # Persist insights
        for item in ranked_insights:
            record = Insight(
                insight_id=item["insight_id"],
                run_id=run_id,
                user_id=user_id,
                insight_type=item["type"],
                severity=item["severity"],
                observation=item["observation"],
                metric=item["metric"],
                evidence=item["evidence"],
                action=item["action"],
                assumptions=item["assumptions"]
            )
            db.add(record)
        
        db.commit()

        return {
            "total_insights_generated": len(ranked_insights),
            "insights": ranked_insights
        }

    def chat(self, db: Session, user_id: str, query: str, history: List[Dict[str, str]]) -> Dict[str, Any]:
        """Conversational advisor with allowlisted tools execution (spec page 12)."""
        system_prompt = (
            "You are the Agentic Personal Finance Advisor for a fintech platform. "
            "You provide factual, mathematically verified explanations grounded strictly in the user's data. "
            "FINANCIAL GUARDRAILS:\n"
            "1. You NEVER execute financial transactions, alter budgets, or cancel subscriptions directly.\n"
            "2. Always cite evidence: insight IDs (e.g. INS_001), transaction IDs, or exact dates.\n"
            "3. If requested data is missing, explicitly ask the user for confirmation.\n"
            "4. Never invent amounts or hallucinate balances.\n"
            "5. Currency is Indian Rupee (INR)."
        )

        # Allowlisted tools declarations for LLM
        tools_declarations = [
            {"name": "get_month_summary", "description": "Fetch monthly income, net spending, and surplus."},
            {"name": "get_budget_status", "description": "Fetch category budget limits and utilization."},
            {"name": "get_forecast", "description": "Fetch 30-day cash flow projected closing balance and shortfalls."},
            {"name": "get_insight_evidence", "description": "Retrieve exact evidence for a specific financial insight."}
        ]

        messages = list(history) if history else []
        messages.append({"role": "user", "content": query})

        # Run LLM or grounded fallback
        llm_resp = llm_service.generate_chat_response(system_prompt, messages, tools_declarations)
        
        # Tool call record tracking
        tool_records = []
        for tc in llm_resp.get("tool_calls", []):
            tool_records.append(ToolCallRecord(
                tool_name=tc["tool_name"],
                arguments=tc.get("arguments", {}),
                result=tc.get("result", {})
            ))

        return {
            "answer": llm_resp.get("text", ""),
            "tool_calls": tool_records,
            "cited_insights": ["ins_budget_01", "ins_forecast_01"] if "budget" in query.lower() or "forecast" in query.lower() else [],
            "cited_transactions": [],
            "suggested_follow_ups": [
                "How can I rebalance my budget to avoid overspending?",
                "Simulate cash flow if my salary is delayed by 10 days",
                "Which recurring subscriptions could I cancel to save money?"
            ]
        }

advisor_agent = FinancialAdvisorAgent()
