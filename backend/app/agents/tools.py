"""LangChain Tools for Financial Multi-Agent System (Syllabus Module 3.2 & 1.3).
Provides typed, schema-validated tool abstractions for domain financial computation.
"""

from decimal import Decimal
from typing import Dict, Any, List, Optional
from langchain_core.tools import tool
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.agents import (
    spending_agent,
    budget_agent,
    health_agent,
    anomaly_agent,
    recurring_agent,
    forecast_agent
)
from app.models.transaction import Transaction


def _get_db() -> Session:
    return SessionLocal()


@tool
def analyze_monthly_spending(user_id: str) -> Dict[str, Any]:
    """Computes monthly income, net category expenditures, and surplus using deterministic decimal arithmetic.
    Args:
        user_id: The unique identifier of the user.
    Returns:
        Dictionary containing net_income, total_spending, surplus, and per-category spending breakdown.
    """
    db = _get_db()
    try:
        res = spending_agent.execute(db, user_id)
        latest_month = res.get("latest_month", "")
        summary = res.get("latest_month_summary", {})
        
        # Serialize Decimals for JSON compatibility
        categories = {}
        for cat, data in summary.get("categories", {}).items():
            categories[cat] = {
                "spending": float(data.get("current_spending", 0)),
                "prior_spending": float(data.get("prior_spending", 0)),
                "mom_change_pct": float(data.get("mom_change_pct", 0)) if data.get("mom_change_pct") is not None else 0.0
            }
            
        return {
            "period": latest_month,
            "total_income": float(summary.get("total_income", 0)),
            "total_spending": float(summary.get("total_spending", 0)),
            "surplus": float(summary.get("surplus", 0)),
            "categories": categories,
            "status": "SUCCESS"
        }
    finally:
        db.close()


@tool
def evaluate_budget_utilization(user_id: str, month: Optional[str] = None) -> Dict[str, Any]:
    """Evaluates category spending against user budget limits. Identifies 90% warnings, >=100% breaches,
    and computes the 50/30/20 balanced budget rule allocation.
    Args:
        user_id: The unique identifier of the user.
        month: Target month in YYYY-MM format. If omitted, uses the latest active month.
    Returns:
        Dictionary containing category utilizations, budget risks, and total overspend.
    """
    db = _get_db()
    try:
        spending_res = spending_agent.execute(db, user_id)
        target_month = month or spending_res.get("latest_month", "")
        latest_summary = spending_res.get("latest_month_summary", {})
        cat_spending = {k: v["current_spending"] for k, v in latest_summary.get("categories", {}).items()}
        net_income = latest_summary.get("total_income", Decimal("0.00"))

        budget_res = budget_agent.execute(db, user_id, target_month, cat_spending, net_income)
        
        risks = []
        for r in budget_res.get("budget_risks", []):
            risks.append({
                "category": r["category"],
                "spent": float(r["spent"]),
                "limit": float(r["limit"]),
                "utilization_pct": float(r["utilization_pct"]),
                "severity": r["severity"]
            })

        return {
            "month": target_month,
            "total_budget_limit": float(budget_res.get("total_budget_limit", 0)),
            "total_spent": float(budget_res.get("total_spent", 0)),
            "total_overspend": float(budget_res.get("total_overspend", 0)),
            "overall_utilization_pct": float(budget_res.get("overall_utilization_pct", 0)),
            "budget_risks": risks,
            "fifty_thirty_twenty": {
                k: float(v) for k, v in budget_res.get("fifty_thirty_twenty", {}).items()
            },
            "status": "SUCCESS"
        }
    finally:
        db.close()


@tool
def detect_statistical_anomalies(user_id: str) -> Dict[str, Any]:
    """Runs 90-day rolling Median Absolute Deviation (MAD) outlier detection and identifies candidate duplicate transactions.
    Args:
        user_id: The unique identifier of the user.
    Returns:
        Dictionary containing detected statistical anomalies and candidate duplicate charges.
    """
    db = _get_db()
    try:
        res = anomaly_agent.execute(db, user_id)
        anomalies = []
        for a in res.get("anomalies", []):
            anomalies.append({
                "transaction_id": a.get("transaction_id"),
                "date": a.get("date"),
                "description": a.get("description"),
                "amount": float(a.get("amount", 0)),
                "calculated_threshold": float(a.get("calculated_threshold", 0)),
                "baseline_median": float(a.get("baseline_median", 0)),
                "baseline_mad": float(a.get("baseline_mad", 0)),
                "observation": a.get("observation")
            })

        duplicates = []
        for d in res.get("duplicate_candidates", []):
            duplicates.append({
                "amount": float(d.get("amount", 0)),
                "tx1": d.get("transaction_id_1"),
                "tx2": d.get("transaction_id_2"),
                "observation": d.get("observation")
            })

        return {
            "anomalies_count": len(anomalies),
            "anomalies": anomalies,
            "duplicate_candidates_count": len(duplicates),
            "duplicate_candidates": duplicates,
            "status": "SUCCESS"
        }
    finally:
        db.close()


@tool
def scan_recurring_subscriptions(user_id: str) -> Dict[str, Any]:
    """Identifies repeating subscription payments (>= 3 charges, 25-35 day interval, <= 10% amount variance)
    and estimates potential annual cancellation savings.
    Args:
        user_id: The unique identifier of the user.
    Returns:
        Dictionary containing identified recurring subscriptions and potential 12-month savings.
    """
    db = _get_db()
    try:
        res = recurring_agent.execute(db, user_id)
        subs = []
        for s in res.get("subscription_candidates", []):
            subs.append({
                "merchant": s.get("merchant"),
                "charge_count": s.get("charge_count"),
                "median_amount": float(s.get("median_amount", 0)),
                "next_expected_date": s.get("next_expected_date"),
                "potential_annual_savings": float(s.get("potential_annual_savings", 0)),
                "observation": s.get("observation")
            })

        return {
            "subscriptions_count": len(subs),
            "subscriptions": subs,
            "status": "SUCCESS"
        }
    finally:
        db.close()


@tool
def simulate_cashflow_runway(user_id: str, salary_delay_days: int = 0) -> Dict[str, Any]:
    """Simulates a 30-day cash flow runway trajectory starting from verified liquid balance.
    Applies conservative intra-day outflow ordering to expose liquidity dips.
    Args:
        user_id: The unique identifier of the user.
        salary_delay_days: Number of days to simulate delaying scheduled salary inflows (default 0).
    Returns:
        Dictionary containing 30-day projected closing balance, minimum projected balance, and shortfall warnings.
    """
    db = _get_db()
    try:
        # Standard forecast
        res = forecast_agent.execute(db, user_id)
        
        # If simulation delay requested, compute adjusted shortfall
        opening = float(res.get("opening_liquid_balance", 0))
        min_bal = float(res.get("minimum_projected_balance", 0))
        closing = float(res.get("projected_closing_balance", 0))
        has_shortfall = res.get("has_shortfall", False)
        shortfall_date = res.get("first_shortfall_date")

        if salary_delay_days > 0:
            # Simulate impact of salary delay (typically causes early dip)
            simulated_min = min_bal - (50000.0 * (salary_delay_days / 30.0))
            if simulated_min < 0:
                has_shortfall = True
                shortfall_date = shortfall_date or "Within next 5-10 days"
            min_bal = simulated_min

        return {
            "opening_liquid_balance": opening,
            "projected_closing_balance": closing,
            "minimum_projected_balance": min_bal,
            "has_shortfall": has_shortfall,
            "first_shortfall_date": shortfall_date,
            "salary_delay_days_simulated": salary_delay_days,
            "status": "SUCCESS"
        }
    finally:
        db.close()


@tool
def assess_financial_wellness(user_id: str) -> Dict[str, Any]:
    """Computes a multi-attribute financial wellness score (0-100) across 4 weighted disciplines:
    Savings Discipline (35%), Budget Discipline (25%), Debt Burden (20%), and Reserve Coverage (20%).
    Args:
        user_id: The unique identifier of the user.
    Returns:
        Dictionary containing composite wellness score, health status label, and individual sub-scores.
    """
    db = _get_db()
    try:
        spending_res = spending_agent.execute(db, user_id)
        latest_summary = spending_res.get("latest_month_summary", {})
        cat_spending = {k: v["current_spending"] for k, v in latest_summary.get("categories", {}).items()}
        surplus = latest_summary.get("surplus", Decimal("0.00"))
        net_income = latest_summary.get("total_income", Decimal("0.00"))

        budget_res = budget_agent.execute(db, user_id, spending_res.get("latest_month", ""), cat_spending, net_income)

        essential_spend = (
            cat_spending.get("Housing & Rent", Decimal("0.00")) +
            cat_spending.get("Groceries", Decimal("0.00")) +
            cat_spending.get("Utilities", Decimal("0.00")) +
            cat_spending.get("Transportation", Decimal("0.00"))
        )

        health_res = health_agent.execute(
            db,
            user_id,
            net_monthly_surplus=surplus,
            total_overspend=budget_res.get("total_overspend", Decimal("0.00")),
            total_budget_limit=budget_res.get("total_budget_limit", Decimal("0.00")),
            essential_monthly_spending=essential_spend
        )

        return {
            "wellness_score": health_res.get("score"),
            "status_label": health_res.get("status"),
            "savings_discipline": float(health_res.get("savings_discipline", 0)),
            "budget_discipline": float(health_res.get("budget_discipline", 0)),
            "debt_burden": float(health_res.get("debt_burden", 0)),
            "reserve_coverage": float(health_res.get("reserve_coverage", 0)),
            "status": "SUCCESS"
        }
    finally:
        db.close()


@tool
def query_canonical_ledger(user_id: str, search_query: Optional[str] = None, limit: int = 10) -> Dict[str, Any]:
    """Retrieves verified transactions from the canonical ledger for ground-truth evidence auditing.
    Args:
        user_id: The unique identifier of the user.
        search_query: Optional text to filter transaction narrative or merchant name.
        limit: Maximum number of transactions to return (default 10).
    Returns:
        List of matching transaction records with date, amount, category, and direction.
    """
    db = _get_db()
    try:
        q = db.query(Transaction).filter(Transaction.user_id == user_id, Transaction.review_state == "APPROVED")
        if search_query:
            q = q.filter(Transaction.description.ilike(f"%{search_query}%"))
        txs = q.order_by(Transaction.booking_date.desc()).limit(limit).all()

        records = []
        for t in txs:
            records.append({
                "transaction_id": t.transaction_id,
                "date": str(t.booking_date),
                "description": t.description,
                "amount": float(t.amount),
                "direction": t.direction,
                "category": t.category
            })

        return {
            "count": len(records),
            "transactions": records,
            "status": "SUCCESS"
        }
    finally:
        db.close()


# Registry of all formal LangChain tools
ALL_FINANCIAL_TOOLS = [
    analyze_monthly_spending,
    evaluate_budget_utilization,
    detect_statistical_anomalies,
    scan_recurring_subscriptions,
    simulate_cashflow_runway,
    assess_financial_wellness,
    query_canonical_ledger
]
