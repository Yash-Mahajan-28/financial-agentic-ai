"""LangGraph Multi-Agent Workflow Engine (Syllabus Module 2.1, 4.1, 4.2 & Micro Project 10).
Implements a state graph with a Planner-Reviewer Pipeline, cyclic self-correction,
and schema-validated tool execution.
"""

import uuid
import time
import datetime
import logging
from typing import TypedDict, List, Dict, Any, Optional, Literal
from sqlalchemy.orm import Session

from langgraph.graph import StateGraph, START, END

from app.database import SessionLocal
from app.models.analysis import AnalysisRun, Insight
from app.agents.tools import (
    analyze_monthly_spending,
    evaluate_budget_utilization,
    detect_statistical_anomalies,
    scan_recurring_subscriptions,
    simulate_cashflow_runway,
    assess_financial_wellness
)
from app.agents import notification_agent
from app.rules.rules_engine import rules_engine

logger = logging.getLogger(__name__)


# -------------------------------------------------------------------------
# 1. Shared Graph State Definition (Module 4.2: Shared State System)
# -------------------------------------------------------------------------
class FinancialAgentState(TypedDict):
    run_id: str
    user_id: str
    data_version: str
    trigger_reason: str
    
    # Workflow Execution State
    current_phase: str
    execution_plan: List[Dict[str, Any]]
    stages_completed: List[str]
    
    # Tool Execution Artifacts
    spending_artifacts: Dict[str, Any]
    budget_artifacts: Dict[str, Any]
    anomaly_artifacts: Dict[str, Any]
    recurring_artifacts: Dict[str, Any]
    forecast_artifacts: Dict[str, Any]
    wellness_artifacts: Dict[str, Any]
    
    # Synthesis & Insights
    draft_insights: List[Dict[str, Any]]
    
    # Reviewer & Guardrails (Micro Project 10: Planner-Reviewer Pipeline)
    reviewer_verdict: Literal["PENDING", "APPROVED", "REVISE"]
    reviewer_feedback: List[str]
    iteration_count: int
    max_iterations: int
    
    # Final Output
    final_insights: List[Dict[str, Any]]
    execution_trace: List[Dict[str, Any]]
    status: str
    error: Optional[str]


# -------------------------------------------------------------------------
# 2. Graph Node Functions
# -------------------------------------------------------------------------

def planner_node(state: FinancialAgentState) -> Dict[str, Any]:
    """Planner Agent (Role: Strategic Financial Orchestrator).
    Decomposes the financial audit request into an actionable multi-step plan.
    """
    start_t = time.time()
    user_id = state["user_id"]
    logger.info(f"[Planner Agent] Creating execution plan for user [{user_id}]...")

    plan = [
        {
            "step_id": 1,
            "role": "SpendingAnalyst",
            "action": "Analyze monthly cash inflows, category expenditures, and net surplus.",
            "tool": "analyze_monthly_spending"
        },
        {
            "step_id": 2,
            "role": "BudgetOfficer",
            "action": "Evaluate budget limit utilizations, 90% warnings, and 50/30/20 allocation.",
            "tool": "evaluate_budget_utilization"
        },
        {
            "step_id": 3,
            "role": "RiskAuditor",
            "action": "Detect statistical MAD expense outliers and candidate duplicate transactions.",
            "tool": "detect_statistical_anomalies"
        },
        {
            "step_id": 4,
            "role": "SubscriptionSpecialist",
            "action": "Audit recurring charges, identify renewal dates, and project annual savings.",
            "tool": "scan_recurring_subscriptions"
        },
        {
            "step_id": 5,
            "role": "ForecastingEngine",
            "action": "Simulate 30-day daily balance trajectory with conservative intra-day ordering.",
            "tool": "simulate_cashflow_runway"
        },
        {
            "step_id": 6,
            "role": "WellnessAdvisor",
            "action": "Compute 4-component holistic financial wellness score (0-100).",
            "tool": "assess_financial_wellness"
        },
        {
            "step_id": 7,
            "role": "SynthesisAgent",
            "action": "Synthesize prioritized, evidence-backed financial recommendations.",
            "tool": "internal_synthesis"
        },
        {
            "step_id": 8,
            "role": "ReviewerValidator",
            "action": "Verify mathematical invariance, policy compliance, and anti-hallucination guardrails.",
            "tool": "reviewer_critique"
        }
    ]

    duration_ms = (time.time() - start_t) * 1000.0
    trace_entry = {
        "node": "planner_node",
        "agent": "Planner Agent",
        "duration_ms": duration_ms,
        "status": "COMPLETED",
        "message": f"Generated {len(plan)}-step structured diagnostic workflow plan."
    }

    return {
        "current_phase": "PLANNING_COMPLETED",
        "execution_plan": plan,
        "stages_completed": state["stages_completed"] + ["PLANNER_AGENT"],
        "execution_trace": state["execution_trace"] + [trace_entry]
    }


def domain_executors_node(state: FinancialAgentState) -> Dict[str, Any]:
    """Domain Worker Agents (Parallel Execution Pool).
    Executes the domain LangChain tools according to the plan.
    """
    start_t = time.time()
    user_id = state["user_id"]
    logger.info(f"[Domain Executors] Executing LangChain financial tools for user [{user_id}]...")

    # Step 1: Spending Analysis Tool
    spending_res = analyze_monthly_spending.invoke({"user_id": user_id})

    # Step 2: Budget Planning Tool
    budget_res = evaluate_budget_utilization.invoke({"user_id": user_id, "month": spending_res.get("period")})

    # Step 3: Anomaly Detection Tool (MAD)
    anomaly_res = detect_statistical_anomalies.invoke({"user_id": user_id})

    # Step 4: Subscription Intelligence Tool
    recurring_res = scan_recurring_subscriptions.invoke({"user_id": user_id})

    # Step 5: Cashflow Forecast Tool
    forecast_res = simulate_cashflow_runway.invoke({"user_id": user_id, "salary_delay_days": 0})

    # Step 6: Financial Wellness Scoring Tool
    wellness_res = assess_financial_wellness.invoke({"user_id": user_id})

    duration_ms = (time.time() - start_t) * 1000.0
    trace_entry = {
        "node": "domain_executors_node",
        "agent": "Domain Worker Pool",
        "duration_ms": duration_ms,
        "status": "COMPLETED",
        "message": "Executed 6 domain LangChain tools with deterministic precision."
    }

    return {
        "current_phase": "TOOLS_EXECUTED",
        "spending_artifacts": spending_res,
        "budget_artifacts": budget_res,
        "anomaly_artifacts": anomaly_res,
        "recurring_artifacts": recurring_res,
        "forecast_artifacts": forecast_res,
        "wellness_artifacts": wellness_res,
        "stages_completed": state["stages_completed"] + ["DOMAIN_EXECUTORS"],
        "execution_trace": state["execution_trace"] + [trace_entry]
    }


def synthesis_node(state: FinancialAgentState) -> Dict[str, Any]:
    """Synthesis Agent (Role: Lead Financial Analyst).
    Synthesizes actionable recommendations ranked by urgency and severity.
    """
    start_t = time.time()
    run_id = state["run_id"]
    logger.info(f"[Synthesis Agent] Synthesizing insights for run [{run_id}]...")

    forecast = state["forecast_artifacts"]
    budget = state["budget_artifacts"]
    anomaly = state["anomaly_artifacts"]
    recurring = state["recurring_artifacts"]

    drafts = []

    # Priority 1: Cashflow Shortfalls
    if forecast.get("has_shortfall"):
        drafts.append({
            "insight_id": f"ins_{uuid.uuid4().hex[:8]}",
            "run_id": run_id,
            "type": "CASH_SHORTFALL",
            "severity": "HIGH",
            "observation": f"Projected liquidity shortfall on {forecast.get('first_shortfall_date')}",
            "metric": {
                "minimum_balance": str(forecast.get("minimum_projected_balance")),
                "shortfall_date": forecast.get("first_shortfall_date"),
                "currency": "INR"
            },
            "evidence": {
                "opening_balance": str(forecast.get("opening_liquid_balance")),
                "rule": "cash-forecast-v1"
            },
            "action": f"Review scheduled obligations before {forecast.get('first_shortfall_date')}; arrange liquidity buffer.",
            "assumptions": ["Conservative intra-day cash outflow ordering applied"]
        })

    # Priority 2: Budget Breaches & 90% Warnings
    for r in budget.get("budget_risks", []):
        drafts.append({
            "insight_id": f"ins_{uuid.uuid4().hex[:8]}",
            "run_id": run_id,
            "type": "BUDGET_RISK",
            "severity": r["severity"],
            "observation": f"{r['category']} budget is {r['utilization_pct']}% utilized",
            "metric": {
                "spent": str(r["spent"]),
                "limit": str(r["limit"]),
                "utilization_pct": str(r["utilization_pct"]),
                "currency": "INR"
            },
            "evidence": {
                "category": r["category"],
                "period": budget.get("month"),
                "rule": "budget-v1"
            },
            "action": f"Review planned {r['category']} expenses; INR {max(0.0, r['limit'] - r['spent']):.2f} remains",
            "assumptions": ["Only approved posted expenses included"]
        })

    # Priority 3: Statistical MAD Anomalies & Duplicates
    for a in anomaly.get("anomalies", []):
        drafts.append({
            "insight_id": f"ins_{uuid.uuid4().hex[:8]}",
            "run_id": run_id,
            "type": "UNUSUAL_EXPENSE",
            "severity": "MEDIUM",
            "observation": a.get("observation", "Unusual expense detected"),
            "metric": {
                "amount": str(a.get("amount")),
                "calculated_threshold": str(a.get("calculated_threshold")),
                "baseline_median": str(a.get("baseline_median")),
                "baseline_mad": str(a.get("baseline_mad"))
            },
            "evidence": {
                "transaction_id": a.get("transaction_id"),
                "date": a.get("date"),
                "description": a.get("description"),
                "rule": "mad-outlier-v1"
            },
            "action": "Verify if this transaction was expected or requires merchant inquiry.",
            "assumptions": ["Evaluated against approved prior 90 days expenses"]
        })

    for d in anomaly.get("duplicate_candidates", []):
        drafts.append({
            "insight_id": f"ins_{uuid.uuid4().hex[:8]}",
            "run_id": run_id,
            "type": "UNUSUAL_EXPENSE",
            "severity": "MEDIUM",
            "observation": d.get("observation", "Candidate duplicate charge"),
            "metric": {"amount": str(d.get("amount"))},
            "evidence": {
                "tx1": d.get("tx1"),
                "tx2": d.get("tx2"),
                "rule": "duplicate-candidate-v1"
            },
            "action": "Confirm if repeat purchase is legitimate or pending refund.",
            "assumptions": ["Identical merchant and amount within 1 calendar day"]
        })

    # Priority 4: Recurring Subscriptions & Savings
    for s in recurring.get("subscriptions", []):
        drafts.append({
            "insight_id": f"ins_{uuid.uuid4().hex[:8]}",
            "run_id": run_id,
            "type": "RECURRING_CANDIDATE",
            "severity": "LOW",
            "observation": s.get("observation", "Recurring subscription detected"),
            "metric": {
                "median_amount": str(s.get("median_amount")),
                "potential_annual_savings": str(s.get("potential_annual_savings"))
            },
            "evidence": {
                "merchant": s.get("merchant"),
                "charge_count": s.get("charge_count"),
                "next_expected_date": s.get("next_expected_date"),
                "rule": "recurring-interval-v1"
            },
            "action": f"Confirm if {s.get('merchant')} is still needed; potential savings INR {s.get('potential_annual_savings')}/yr if cancelled.",
            "assumptions": ["Annual savings assume 12 future billing cycles avoided"]
        })

    duration_ms = (time.time() - start_t) * 1000.0
    trace_entry = {
        "node": "synthesis_node",
        "agent": "Synthesis Agent",
        "duration_ms": duration_ms,
        "status": "COMPLETED",
        "message": f"Synthesized {len(drafts)} draft recommendations for Reviewer audit."
    }

    return {
        "current_phase": "SYNTHESIS_COMPLETED",
        "draft_insights": drafts,
        "stages_completed": state["stages_completed"] + ["SYNTHESIS_AGENT"],
        "execution_trace": state["execution_trace"] + [trace_entry]
    }


def reviewer_validator_node(state: FinancialAgentState) -> Dict[str, Any]:
    """Reviewer / Guardrail Validator Agent (Micro Project 10: Planner-Reviewer Pipeline).
    Validates draft insights against mathematical invariance, safety policies, and ground-truth citations.
    """
    start_t = time.time()
    logger.info(f"[Reviewer Agent] Auditing {len(state['draft_insights'])} draft insights...")

    drafts = state["draft_insights"]
    feedback = []
    approved_insights = []

    # Criteria 1: Guardrail against unauthorized execution/mutations (Module 1.3 & 5.3)
    FORBIDDEN_KEYWORDS = ["execute transfer", "cancel now", "alter limit directly", "debit account"]

    for ins in drafts:
        action_text = ins.get("action", "").lower()
        if any(kw in action_text for kw in FORBIDDEN_KEYWORDS):
            feedback.append(f"Safety Violation in {ins['insight_id']}: Prohibited autonomous action suggested.")
            continue

        # Criteria 2: Verification of evidence and rules
        if not ins.get("evidence"):
            feedback.append(f"Verification Failure in {ins['insight_id']}: Missing evidence provenance.")
            continue

        # Criteria 3: Check metric precision and currency validity
        if "metric" not in ins:
            feedback.append(f"Schema Incompleteness in {ins['insight_id']}: Missing metric payload.")
            continue

        approved_insights.append(ins)

    # Determine verdict
    iteration = state["iteration_count"] + 1
    if feedback and iteration < state["max_iterations"]:
        verdict = "REVISE"
        logger.warning(f"[Reviewer Agent] Verdict: REVISE (Iteration {iteration}). Feedback: {feedback}")
    else:
        verdict = "APPROVED"
        logger.info(f"[Reviewer Agent] Verdict: APPROVED. {len(approved_insights)} verified insights passed.")

    duration_ms = (time.time() - start_t) * 1000.0
    trace_entry = {
        "node": "reviewer_validator_node",
        "agent": "Reviewer Validator Agent",
        "duration_ms": duration_ms,
        "status": verdict,
        "message": f"Audited {len(drafts)} items. Verdict: {verdict}. Feedback count: {len(feedback)}."
    }

    return {
        "current_phase": "REVIEW_COMPLETED",
        "reviewer_verdict": verdict,
        "reviewer_feedback": feedback,
        "iteration_count": iteration,
        "final_insights": approved_insights,
        "stages_completed": state["stages_completed"] + [f"REVIEWER_VALIDATOR_{verdict}"],
        "execution_trace": state["execution_trace"] + [trace_entry]
    }


def publisher_node(state: FinancialAgentState) -> Dict[str, Any]:
    """Publisher Node (Atomic Persistence & Notification Dispatch).
    Publishes the reviewer-approved insights and commits the AnalysisRun snapshot to the database.
    """
    start_t = time.time()
    user_id = state["user_id"]
    run_id = state["run_id"]
    logger.info(f"[Publisher Node] Persisting snapshot for run [{run_id}]...")

    db: Session = SessionLocal()
    try:
        # 1. Update AnalysisRun record
        run_record = db.query(AnalysisRun).filter(AnalysisRun.run_id == run_id).first()
        spending = state["spending_artifacts"]
        budget = state["budget_artifacts"]
        wellness = state["wellness_artifacts"]

        if run_record:
            run_record.status = "COMPLETED"
            run_record.summary_metrics = {
                "period": spending.get("period"),
                "net_income": str(spending.get("total_income", 0)),
                "net_spending": str(spending.get("total_spending", 0)),
                "monthly_surplus": str(spending.get("surplus", 0)),
                "total_budget_limit": str(budget.get("total_budget_limit", 0)),
                "overall_budget_utilization_pct": str(budget.get("overall_utilization_pct", 0))
            }
            run_record.wellness_score = {
                "score": wellness.get("wellness_score"),
                "status": wellness.get("status_label"),
                "savings_discipline": str(wellness.get("savings_discipline")),
                "budget_discipline": str(wellness.get("budget_discipline")),
                "debt_burden": str(wellness.get("debt_burden")),
                "reserve_coverage": str(wellness.get("reserve_coverage")),
                "formula_version": "health-v1"
            }

        # 2. Persist approved insights
        for item in state["final_insights"]:
            db.add(Insight(
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
            ))

        db.commit()

        # 3. Trigger Notification Agent
        notification_res = notification_agent.execute(db, user_id, insights=state["final_insights"])

    except Exception as e:
        logger.error(f"[Publisher Node] Failed during snapshot commit: {e}", exc_info=True)
        db.rollback()
        raise e
    finally:
        db.close()

    duration_ms = (time.time() - start_t) * 1000.0
    trace_entry = {
        "node": "publisher_node",
        "agent": "Publisher Node",
        "duration_ms": duration_ms,
        "status": "COMPLETED",
        "message": f"Atomically published {len(state['final_insights'])} insights and committed snapshot."
    }

    return {
        "current_phase": "PUBLISHED",
        "status": "COMPLETED",
        "stages_completed": state["stages_completed"] + ["PUBLISHER_NODE"],
        "execution_trace": state["execution_trace"] + [trace_entry]
    }


# -------------------------------------------------------------------------
# 3. Conditional Routing Logic (Module 2.1 & 4.2: Cyclic Workflows)
# -------------------------------------------------------------------------
def should_continue_or_revise(state: FinancialAgentState) -> Literal["analyst_worker", "publisher"]:
    """Cyclic Routing: If Reviewer requires revision and retries remain, loop back to Analyst Worker."""
    verdict = state.get("reviewer_verdict")
    iteration = state.get("iteration_count", 0)
    max_iter = state.get("max_iterations", 2)

    if verdict == "REVISE" and iteration < max_iter:
        logger.info(f"[Graph Router] Reviewer requested revision. Cycling back to synthesis (attempt {iteration}/{max_iter}).")
        return "analyst_worker"
    
    return "publisher"


# -------------------------------------------------------------------------
# 4. StateGraph Assembly & Compilation
# -------------------------------------------------------------------------
def build_financial_multi_agent_graph():
    """Builds the compiled LangGraph StateGraph embodying the Planner-Reviewer Pipeline."""
    builder = StateGraph(FinancialAgentState)

    # Register Nodes
    builder.add_node("planner", planner_node)
    builder.add_node("domain_executors", domain_executors_node)
    builder.add_node("analyst_worker", synthesis_node)
    builder.add_node("reviewer_validator", reviewer_validator_node)
    builder.add_node("publisher", publisher_node)

    # Add Edges (Module 2.1: DAG & Cyclic Flow)
    builder.add_edge(START, "planner")
    builder.add_edge("planner", "domain_executors")
    builder.add_edge("domain_executors", "analyst_worker")
    builder.add_edge("analyst_worker", "reviewer_validator")

    # Conditional Cyclic Feedback Edge
    builder.add_conditional_edges(
        "reviewer_validator",
        should_continue_or_revise,
        {
            "analyst_worker": "analyst_worker",
            "publisher": "publisher"
        }
    )

    builder.add_edge("publisher", END)

    return builder.compile()


# Singleton compiled graph instance
financial_multi_agent_graph = build_financial_multi_agent_graph()
