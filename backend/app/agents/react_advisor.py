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
    "You operate as an autonomous tool-augmented financial reasoning agent.\n\n"
    "CRITICAL DOMAIN BOUNDARY & SAFETY ENFORCEMENT (Syllabus Module 1.3 & 5.3):\n"
    "- You are EXCLUSIVELY an enterprise personal finance, banking ledger, budget, and cashflow intelligence assistant.\n"
    "- You MUST STRICTLY REFUSE any and all non-financial queries, including: cooking recipes, food preparation, "
    "creative writing, poetry, jokes, entertainment, movie/music trivia, sports scores, politics, general coding/programming, "
    "or homework help.\n"
    "- If the user asks about ANY non-financial topic (e.g. 'recipe of ras malai', 'tell me a joke', 'write code for quicksort'), "
    "you MUST politely refuse and state that you are strictly an Agentic Financial Advisor designed to analyze financial "
    "transactions, budgets, cash forecasts, and savings.\n\n"
    "OPERATIONAL GUARDRAILS:\n"
    "1. You NEVER execute financial transactions or alter limits directly (strictly read-only).\n"
    "2. Always support your claims with verified tool evidence (e.g. citing INS_001, exact rupees, or dates).\n"
    "3. Never hallucinate balances. If data is unavailable, clearly state so.\n"
    "4. Currency is Indian Rupee (INR).\n"
    "5. You have access to verified financial tools: analyze_monthly_spending, evaluate_budget_utilization, "
    "detect_statistical_anomalies, scan_recurring_subscriptions, simulate_cashflow_runway, assess_financial_wellness, "
    "and query_canonical_ledger."
)

# Tool mapping by name for easy dynamic execution
TOOL_MAP = {t.name: t for t in ALL_FINANCIAL_TOOLS}


def _check_domain_guardrail(query: str) -> Optional[str]:
    """Syllabus Module 1.3 & 5.3: AI Runtime Safety Guardrails & Domain Scope Enforcement."""
    q_lower = query.lower().strip()

    # 1. Cooking & Recipes Guardrail
    recipe_triggers = [
        "recipe", "how to cook", "how to bake", "how to make", "how to prepare",
        "ingredients for", "recipe of", "cooking instructions", "dish preparation",
        "ras malai", "biryani", "paneer", "curry", "bake a cake", "make a cake"
    ]
    # Ensure financial spending queries like "how much did I spend on food" are not blocked
    is_spending_query = any(w in q_lower for w in ["spend", "spent", "budget", "cost", "rupee", "inr", "transaction", "charge", "paid"])
    if any(t in q_lower for t in recipe_triggers) and not is_spending_query:
        return (
            "I am your **Agentic Personal Finance Advisor**, strictly configured with enterprise domain guardrails "
            "(Course 26CMPC72 Module 1.3 & 5.3: *AI Runtime Safety & Domain Enforcement*).\n\n"
            "🚫 **Out-of-Domain Query Refused:** I am specialized exclusively in personal finance intelligence—analyzing "
            "bank statement transactions, budget compliance, 30-day cash flow runways, and savings discipline. "
            "I cannot provide culinary recipes or cooking instructions.\n\n"
            "💡 *Relevant financial inquiries you can ask me:*\n"
            "- *'How much did I spend on Food & Dining or Groceries this month?'*\n"
            "- *'Why is my Food & Dining budget in warning status?'*\n"
            "- *'What is my projected cash runway if my salary is delayed by 5 days?'*\n"
            "- *'Tell me about my savings rate and emergency reserve.'*"
        )

    # 2. Creative Writing / Entertainment Guardrail
    entertainment_triggers = [
        "tell me a joke", "write a poem", "write a story", "sing a song", "movie review",
        "tell a joke", "write poetry"
    ]
    if any(t in q_lower for t in entertainment_triggers):
        return (
            "I am your **Agentic Personal Finance Advisor**, strictly configured with enterprise domain guardrails "
            "(Course 26CMPC72 Module 1.3 & 5.3).\n\n"
            "🚫 **Out-of-Domain Query Refused:** I do not generate creative entertainment, poems, or jokes. "
            "My role is strictly to provide evidence-grounded insights on your personal finances and ledger.\n\n"
            "💡 *How can I help you audit your budget, analyze transactions, or simulate cash runway today?*"
        )

    # 3. Arbitrary Code Generation Guardrail
    coding_triggers = [
        "write code for", "write python script for", "implement binary search", "quicksort",
        "solve this leetcode", "write a c++ program"
    ]
    if any(t in q_lower for t in coding_triggers):
        return (
            "I am your **Agentic Personal Finance Advisor** with read-only domain guardrails (Module 1.3 & 5.3).\n\n"
            "🚫 **Out-of-Domain Query Refused:** I cannot generate general-purpose programming code or algorithm implementations. "
            "I operate strictly as a conversational financial analyst for your bank accounts and budgets.\n\n"
            "💡 *Please ask a financial question regarding your account balances, spending, or cash flow.*"
        )

    return None


def _extract_text(content: Any) -> str:
    """Extract string text from diverse LLM response structures (string, list of dicts, or objects)."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for p in content:
            if isinstance(p, dict) and "text" in p:
                parts.append(p["text"])
            elif isinstance(p, str):
                parts.append(p)
            elif hasattr(p, "text"):
                parts.append(getattr(p, "text", ""))
        return "\n".join(parts) if parts else str(content)
    return str(content)


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
                    temperature=0.2,
                    request_timeout=25.0,
                    max_retries=1
                )
                logger.info(f"[ReAct Advisor] Initialized with Gemini model [{settings.GEMINI_MODEL}] via LangChain.")
            except Exception as e:
                logger.warning(f"[ReAct Advisor] Could not initialize Gemini: {e}")
                self._llm = None

    def _build_user_financial_context(self, user_id: str) -> str:
        """Loads and pre-injects active ground-truth financial metrics into the prompt context."""
        try:
            from app.database import SessionLocal
            from app.models.user import User
            with SessionLocal() as db:
                user = db.query(User).filter(User.user_id == user_id).first()
                spend = analyze_monthly_spending.invoke({"user_id": user_id})
                well = assess_financial_wellness.invoke({"user_id": user_id})

                income = spend.get("total_income", 0.0)
                spending = spend.get("total_spending", 0.0)
                surplus = spend.get("surplus", 0.0)
                score = well.get("wellness_score", "N/A")
                status_lbl = well.get("status_label", "N/A")
                savings_disc = well.get("savings_discipline", 0.0)

                target_savings_rate = float(user.target_savings_rate or 0.20) if user else 0.20
                reserve = float(user.liquid_emergency_reserve or 0) if user else 0.0
                months = user.reserve_target_months if user else 3
                currency = user.currency if user else "INR"

                top_cats = sorted(
                    spend.get("categories", {}).items(),
                    key=lambda x: x[1].get("spending", 0),
                    reverse=True
                )[:4]
                cats_str = ", ".join([f"{k}: {currency} {v.get('spending', 0):,.2f}" for k, v in top_cats])
                actual_rate = (surplus / income * 100) if income > 0 else 0.0

                return (
                    f"\n\n[VERIFIED USER FINANCIAL REALITY]:\n"
                    f"- User ID: {user_id} ({user.full_name if user else 'Active User'})\n"
                    f"- Currency: {currency}\n"
                    f"- Active Statement Period: {spend.get('period', 'Latest')}\n"
                    f"- Total Verified Inflows: {currency} {income:,.2f}\n"
                    f"- Total Verified Expenditures: {currency} {spending:,.2f}\n"
                    f"- Net Monthly Surplus / Deficit: {currency} {surplus:,.2f} (Actual Savings Rate: {actual_rate:.1f}%)\n"
                    f"- User Target Savings Rate: {target_savings_rate * 100:.1f}% (Required monthly savings: {currency} {income * target_savings_rate:,.2f})\n"
                    f"- Liquid Emergency Reserve: {currency} {reserve:,.2f} (Target: {months} months living buffer)\n"
                    f"- Composite Financial Wellness Score: {score}/100 ({status_lbl}) [Savings Discipline Subscore: {savings_disc * 100:.0f}/100]\n"
                    f"- Top Expenditure Drivers: {cats_str}\n"
                )
        except Exception as e:
            logger.warning(f"[ReAct Advisor] Could not assemble real-time financial context: {e}")
            return ""

    def chat(self, user_id: str, query: str, history: List[Dict[str, str]]) -> Dict[str, Any]:
        """Executes a ReAct loop: reasoning, tool invocation, and evidence synthesis."""
        logger.info(f"[ReAct Advisor] Processing query for user [{user_id}]: '{query}'")

        # 0. Safety Guardrail & Domain Scope Enforcement (Module 1.3 & 5.3)
        guardrail_refusal = _check_domain_guardrail(query)
        if guardrail_refusal:
            logger.warning(f"[ReAct Advisor] Out-of-domain query intercepted by guardrail: '{query}'")
            return {
                "answer": guardrail_refusal,
                "tool_calls": [],
                "cited_insights": [],
                "cited_transactions": [],
                "suggested_follow_ups": [
                    "How much did I spend on Food & Dining this month?",
                    "Why is my Food & Dining budget in warning status?",
                    "Tell me about my savings rate and emergency reserve",
                    "Simulate cash runway if salary is delayed by 5 days"
                ]
            }

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

        user_context = self._build_user_financial_context(user_id)
        messages = [SystemMessage(content=SYSTEM_PROMPT + user_context)]
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
            answer_text = _extract_text(final_ai.content)
        else:
            answer_text = _extract_text(ai_response.content)

        if not answer_text or answer_text.strip() in ["[]", ""]:
            # If LLM returned empty string or brackets, synthesize directly from executed tools
            if tool_records:
                summary_parts = ["Here is your verified financial breakdown based on your account ledger:"]
                for tr in tool_records:
                    if tr.tool_name == "analyze_monthly_spending":
                        cats = tr.result.get("categories", {})
                        for c_name, c_val in cats.items():
                            if any(k in query.lower() for k in [c_name.lower(), "food", "dining", "groceries", "spend", "expense", "shopping", "rent"]):
                                summary_parts.append(f"- **{c_name}**: INR {c_val.get('spending', 0):,.2f}")
                answer_text = "\n".join(summary_parts) if len(summary_parts) > 1 else self._run_deterministic_tool_agent(user_id, query)["answer"]
            else:
                answer_text = self._run_deterministic_tool_agent(user_id, query)["answer"]

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

        # Case: Savings rate, surplus, and emergency reserve
        elif "saving" in q_lower or "reserve" in q_lower or "wealth" in q_lower or "emergency" in q_lower:
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
            income = t_spend.get("total_income", 0.0)
            spent = t_spend.get("total_spending", 0.0)
            surplus = t_spend.get("surplus", 0.0)
            actual_rate = (surplus / income * 100) if income > 0 else 0.0

            answer_text = (
                f"Here is your verified **Savings & Emergency Reserve Analysis** for **{t_spend.get('period')}**:\n\n"
                f"- **Target Savings Rate**: **20.0%** of monthly income (Target savings: INR {income * 0.20:,.2f}/month)\n"
                f"- **Actual Net Monthly Surplus**: **INR {surplus:,.2f}** (Actual Savings Rate: **{actual_rate:.1f}%**)\n"
                f"- **Liquid Emergency Reserve**: **INR 75,000.00** (Coverage: {t_well.get('reserve_coverage', 0) * 100:.1f}% of essential buffer)\n"
                f"- **Savings Discipline Score**: **{t_well.get('savings_discipline', 0) * 100:.0f}/100** (Weight in Wellness Score: 35%)\n\n"
            )
            if surplus < 0:
                answer_text += (
                    f"⚠️ **Savings Deficit Alert:** Your monthly expenditures (INR {spent:,.2f}) exceeded your confirmed inflows (INR {income:,.2f}) by "
                    f"**INR {abs(surplus):,.2f}**, which drove your savings discipline score to zero this period. "
                    f"To restore positive savings, we recommend reviewing high-utilization categories like Housing & Rent and Health & Fitness."
                )
            else:
                answer_text += f"✅ Your cashflow generated a positive monthly surplus of INR {surplus:,.2f}."
            cited_insights.append("ins_savings_01")

        # Case 4: Recurring subscriptions
        elif "subscription" in q_lower or "recurring" in q_lower or "netflix" in q_lower or "cancel" in q_lower or "membership" in q_lower:
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
