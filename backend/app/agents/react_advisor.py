"""ReAct Conversational Financial Advisor (Syllabus Module 4.1: ReAct Loop, Tool-Using Agents).
Equips the conversational advisor with formal LangChain tools, dynamic function calling,
and evidence-grounded synthesis.
"""

import json
import logging
from typing import Dict, Any, List, Optional
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage
from sqlalchemy.orm import Session

from app.config import settings
from app.agents.tools import (
    analyze_monthly_spending,
    evaluate_budget_utilization,
    detect_statistical_anomalies,
    scan_recurring_subscriptions,
    simulate_cashflow_runway,
    assess_financial_wellness,
    query_canonical_ledger,
    ALL_FINANCIAL_TOOLS
)
from app.schemas.advisor import ToolCallRecord

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are the Agentic Personal Finance Advisor for FinAgentic AI. "
    "You operate as an autonomous tool-augmented financial reasoning agent. "
    "You have access to verified financial tools: analyze_monthly_spending, evaluate_budget_utilization, "
    "detect_statistical_anomalies, scan_recurring_subscriptions, simulate_cashflow_runway, assess_financial_wellness, "
    "and query_canonical_ledger.\n\n"
    "SAFETY GUARDRAILS (Module 1.3 & 5.3):\n"
    "1. You NEVER execute financial transactions or alter limits directly (strictly read-only).\n"
    "2. Always support your claims with verified tool evidence (e.g. citing INS_001, exact rupees, or dates).\n"
    "3. Never hallucinate balances. If data is unavailable, clearly state so.\n"
    "4. Currency is Indian Rupee (INR)."
)

# Tool mapping by name for easy dynamic execution
TOOL_MAP = {t.name: t for t in ALL_FINANCIAL_TOOLS}


class ReActFinancialAdvisor:
    """Agentic ReAct Advisor with dynamic tool selection and execution."""

    def __init__(self):
        self._llm = None
        self._setup_llm()

    def _setup_llm(self):
        if settings.GEMINI_API_KEY:
            try:
                from langchain_google_genai import ChatGoogleGenerativeAI
                self._llm = ChatGoogleGenerativeAI(
                    model=settings.GEMINI_MODEL,
                    google_api_key=settings.GEMINI_API_KEY,
                    temperature=0.2
                )
                logger.info("[ReAct Advisor] Initialized with Gemini via LangChain.")
            except Exception as e:
                logger.warning(f"[ReAct Advisor] Could not initialize Gemini: {e}")
                self._llm = None

    def chat(self, user_id: str, query: str, history: List[Dict[str, str]]) -> Dict[str, Any]:
        """Executes a ReAct loop: reasoning, tool invocation, and evidence synthesis."""
        logger.info(f"[ReAct Advisor] Processing query for user [{user_id}]: '{query}'")

        # 1. If LLM is configured, execute LangChain ReAct loop
        if self._llm:
            try:
                return self._run_llm_react_loop(user_id, query, history)
            except Exception as e:
                logger.error(f"[ReAct Advisor] LangChain LLM execution failed: {e}. Falling back to deterministic tool routing.", exc_info=True)

        # 2. Deterministic Tool Routing (offline / zero-key mode)
        return self._run_deterministic_tool_agent(user_id, query)

    def _run_llm_react_loop(self, user_id: str, query: str, history: List[Dict[str, str]]) -> Dict[str, Any]:
        """LangChain ReAct tool-calling loop (Module 4.1)."""
        llm_with_tools = self._llm.bind_tools(ALL_FINANCIAL_TOOLS)

        messages = [SystemMessage(content=SYSTEM_PROMPT)]
        for h in (history or []):
            if h.get("role") == "user":
                messages.append(HumanMessage(content=h.get("content", "")))
            elif h.get("role") == "assistant":
                messages.append(AIMessage(content=h.get("content", "")))

        # Append user query with injected user_id context
        augmented_query = f"{query}\n[SYSTEM CONTEXT: The active authenticated user_id is '{user_id}']"
        messages.append(HumanMessage(content=augmented_query))

        # ReAct Turn 1: Model decides to call tools
        ai_response = llm_with_tools.invoke(messages)
        tool_records: List[ToolCallRecord] = []
        cited_insights = []
        cited_transactions = []

        if hasattr(ai_response, "tool_calls") and ai_response.tool_calls:
            messages.append(ai_response)
            
            # Execute invoked tools
            for tc in ai_response.tool_calls:
                t_name = tc.get("name")
                t_args = tc.get("args", {})
                t_args["user_id"] = user_id # Ensure user_id scoping

                if t_name in TOOL_MAP:
                    t_instance = TOOL_MAP[t_name]
                    tool_output = t_instance.invoke(t_args)

                    tool_records.append(ToolCallRecord(
                        tool_name=t_name,
                        arguments=t_args,
                        result=tool_output
                    ))

                    # Append Tool Observation message
                    messages.append(ToolMessage(
                        tool_call_id=tc.get("id", "call_1"),
                        content=json.dumps(tool_output)
                    ))

            # ReAct Turn 2: Synthesize final answer from observations
            final_ai = self._llm.invoke(messages)
            answer_text = final_ai.content
        else:
            answer_text = ai_response.content

        return {
            "answer": answer_text,
            "tool_calls": tool_records,
            "cited_insights": cited_insights,
            "cited_transactions": cited_transactions,
            "suggested_follow_ups": self._generate_follow_ups(query)
        }

    def _run_deterministic_tool_agent(self, user_id: str, query: str) -> Dict[str, Any]:
        """Autonomous tool agent for offline/reliable demonstration.
        Selects and executes actual LangChain tools on the live database.
        """
        q_lower = query.lower()
        tool_records: List[ToolCallRecord] = []
        cited_insights = []
        cited_transactions = []
        answer_text = ""

        # Case 1: Budget utilization questions
        if "budget" in q_lower or "limit" in q_lower or "overspend" in q_lower:
            t_res = evaluate_budget_utilization.invoke({"user_id": user_id})
            tool_records.append(ToolCallRecord(
                tool_name="evaluate_budget_utilization",
                arguments={"user_id": user_id},
                result=t_res
            ))
            risks = t_res.get("budget_risks", [])
            if risks:
                highest_risk = max(risks, key=lambda x: x["utilization_pct"])
                answer_text = (
                    f"Based on your verified {t_res.get('month')} ledger, your overall budget utilization is "
                    f"**{t_res.get('overall_utilization_pct')}%** (Spent INR {t_res.get('total_spent'):,.2f} of INR {t_res.get('total_budget_limit'):,.2f}).\n\n"
                    f"⚠️ **Key Risk:** Category **{highest_risk['category']}** is at **{highest_risk['utilization_pct']}%** utilization "
                    f"(INR {highest_risk['spent']:,.2f} / INR {highest_risk['limit']:,.2f}). "
                    f"Under our 50/30/20 balanced rule, Needs should stay at INR {t_res.get('fifty_thirty_twenty', {}).get('needs_50', 0):,.2f}."
                )
                cited_insights.append("ins_budget_01")
            else:
                answer_text = (
                    f"All category budgets for {t_res.get('month')} are currently healthy with no exceeded thresholds. "
                    f"Total spending is INR {t_res.get('total_spent'):,.2f} against a limit of INR {t_res.get('total_budget_limit'):,.2f}."
                )

        # Case 2: Cashflow forecast & salary delays
        elif "forecast" in q_lower or "shortfall" in q_lower or "salary" in q_lower or "runway" in q_lower or "cash" in q_lower:
            delay = 5 if "delay" in q_lower else 0
            t_res = simulate_cashflow_runway.invoke({"user_id": user_id, "salary_delay_days": delay})
            tool_records.append(ToolCallRecord(
                tool_name="simulate_cashflow_runway",
                arguments={"user_id": user_id, "salary_delay_days": delay},
                result=t_res
            ))
            if t_res.get("has_shortfall"):
                answer_text = (
                    f"Simulating a {delay}-day salary delay identifies a **critical liquidity shortfall** on **{t_res.get('first_shortfall_date')}**.\n\n"
                    f"Starting from an opening balance of INR {t_res.get('opening_liquid_balance'):,.2f}, your projected minimum balance dips to "
                    f"**INR {t_res.get('minimum_projected_balance'):,.2f}** due to scheduled rent and utility obligations. "
                    f"We recommend preserving INR {abs(t_res.get('minimum_projected_balance', 0)):,.2f} in liquid buffer."
                )
                cited_insights.append("ins_forecast_01")
            else:
                answer_text = (
                    f"Your 30-day cash runway is stable. Opening balance: INR {t_res.get('opening_liquid_balance'):,.2f}, "
                    f"projected closing balance: INR {t_res.get('projected_closing_balance'):,.2f}. No liquidity dips below zero detected."
                )

        # Case 3: Statistical anomalies & duplicate transactions
        elif "unusual" in q_lower or "anomaly" in q_lower or "duplicate" in q_lower or "outlier" in q_lower:
            t_res = detect_statistical_anomalies.invoke({"user_id": user_id})
            tool_records.append(ToolCallRecord(
                tool_name="detect_statistical_anomalies",
                arguments={"user_id": user_id},
                result=t_res
            ))
            anomalies = t_res.get("anomalies", [])
            dups = t_res.get("duplicate_candidates", [])
            if anomalies or dups:
                answer_text = f"The Statistical Auditor detected **{len(anomalies)} statistical outliers** and **{len(dups)} candidate duplicate charges**:\n\n"
                for a in anomalies[:2]:
                    answer_text += f"- **{a['description']}** on {a['date']}: INR {a['amount']:,.2f} (Category median: INR {a['baseline_median']:,.2f}, MAD threshold: INR {a['calculated_threshold']:,.2f})\n"
                for d in dups[:1]:
                    answer_text += f"- **Potential Duplicate**: Charge of INR {d['amount']:,.2f} repeated within 24 hours.\n"
                cited_insights.append("ins_anomaly_01")
            else:
                answer_text = "No statistical MAD outliers or duplicate transactions detected across the 90-day baseline."

        # Case 4: Recurring subscriptions
        elif "subscription" in q_lower or "recurring" in q_lower or "save" in q_lower or "netflix" in q_lower:
            t_res = scan_recurring_subscriptions.invoke({"user_id": user_id})
            tool_records.append(ToolCallRecord(
                tool_name="scan_recurring_subscriptions",
                arguments={"user_id": user_id},
                result=t_res
            ))
            subs = t_res.get("subscriptions", [])
            total_savings = sum(s.get("potential_annual_savings", 0) for s in subs)
            answer_text = (
                f"Subscription Intelligence identified **{len(subs)} recurring services**.\n\n"
                f"Cancelling inactive memberships could yield **INR {total_savings:,.2f} in annual savings**:\n"
            )
            for s in subs:
                answer_text += f"- **{s['merchant']}**: INR {s['median_amount']:,.2f}/month (Next billing: {s['next_expected_date']})\n"
            cited_insights.append("ins_sub_01")

        # Case 5: General spending overview or wellness score
        else:
            t_spend = analyze_monthly_spending.invoke({"user_id": user_id})
            t_well = assess_financial_wellness.invoke({"user_id": user_id})
            tool_records.append(ToolCallRecord(
                tool_name="analyze_monthly_spending",
                arguments={"user_id": user_id},
                result=t_spend
            ))
            tool_records.append(ToolCallRecord(
                tool_name="assess_financial_wellness",
                arguments={"user_id": user_id},
                result=t_well
            ))
            answer_text = (
                f"Welcome! Here is your latest verified financial summary for **{t_spend.get('period')}**:\n\n"
                f"- **Total Income**: INR {t_spend.get('total_income'):,.2f}\n"
                f"- **Total Expenditures**: INR {t_spend.get('total_spending'):,.2f}\n"
                f"- **Monthly Surplus**: INR {t_spend.get('surplus'):,.2f}\n"
                f"- **Financial Wellness Score**: **{t_well.get('wellness_score')}/100** ({t_well.get('status_label')})\n\n"
                f"You can ask me to simulate cash runway delays, inspect budget warnings, or audit recurring subscriptions."
            )

        return {
            "answer": answer_text,
            "tool_calls": tool_records,
            "cited_insights": cited_insights,
            "cited_transactions": cited_transactions,
            "suggested_follow_ups": self._generate_follow_ups(query)
        }

    def _generate_follow_ups(self, query: str) -> List[str]:
        return [
            "Why is my Food & Dining budget in warning status?",
            "Simulate cash runway if salary is delayed by 5 days",
            "Which subscriptions can I cancel to maximize savings?",
            "Audit unusual expenses and duplicate charges"
        ]


react_advisor = ReActFinancialAdvisor()
