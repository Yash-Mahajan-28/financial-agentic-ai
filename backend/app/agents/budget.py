from decimal import Decimal
from typing import Dict, Any, List
from sqlalchemy.orm import Session

from app.agents.base import BaseAgent
from app.models.budget import Budget
from app.rules.rules_engine import rules_engine

class BudgetPlanningAgent(BaseAgent):
    def __init__(self):
        super().__init__("BudgetPlanningAgent")

    def run(self, db: Session, user_id: str, month: str, category_spending: Dict[str, Decimal], net_income: Decimal) -> Dict[str, Any]:
        # 1. Fetch budgets for user and month
        budget_records = db.query(Budget).filter(
            Budget.user_id == user_id,
            Budget.month == month
        ).all()
        
        limits = {b.category: Decimal(str(b.limit_amount)) for b in budget_records}

        warning_threshold = rules_engine.budget_warning_pct # e.g. 90.00
        exceeded_threshold = rules_engine.budget_exceeded_pct # e.g. 100.00

        utilization_items = []
        total_limit = Decimal("0.00")
        total_spent_under_budget = Decimal("0.00")
        total_overspend = Decimal("0.00")
        budget_risks = []

        # Check all budgeted categories and spent categories
        all_categories = set(limits.keys()).union(category_spending.keys())

        for cat in sorted(all_categories):
            spent = category_spending.get(cat, Decimal("0.00"))
            limit = limits.get(cat, Decimal("0.00"))
            total_limit += limit

            if limit > Decimal("0.00"):
                util_pct = (spent / limit) * Decimal("100.00")
                remaining = limit - spent
                if util_pct >= exceeded_threshold:
                    status = "EXCEEDED"
                    overspend = spent - limit
                    total_overspend += overspend
                    budget_risks.append({
                        "category": cat,
                        "spent": spent,
                        "limit": limit,
                        "utilization_pct": Decimal(f"{util_pct:.2f}"),
                        "severity": "HIGH",
                        "status": status,
                        "observation": f"{cat} budget is exceeded ({util_pct:.1f}%)"
                    })
                elif util_pct >= warning_threshold:
                    status = "WARNING"
                    budget_risks.append({
                        "category": cat,
                        "spent": spent,
                        "limit": limit,
                        "utilization_pct": Decimal(f"{util_pct:.2f}"),
                        "severity": "MEDIUM",
                        "status": status,
                        "observation": f"{cat} budget is {util_pct:.1f}% used"
                    })
                else:
                    status = "NORMAL"
            else:
                # Zero limit
                remaining = Decimal("0.00") - spent
                if spent > Decimal("0.00"):
                    util_pct = Decimal("100.00")
                    status = "ZERO_LIMIT_EXCEEDED"
                    total_overspend += spent
                else:
                    util_pct = Decimal("0.00")
                    status = "NORMAL"

            utilization_items.append({
                "category": cat,
                "spent": Decimal(f"{spent:.2f}"),
                "limit": Decimal(f"{limit:.2f}"),
                "remaining": Decimal(f"{remaining:.2f}"),
                "utilization_pct": Decimal(f"{util_pct:.2f}"),
                "status": status
            })

        overall_utilization = (sum(category_spending.values()) / total_limit * Decimal("100.00")) if total_limit > Decimal("0.00") else Decimal("0.00")

        # 50/30/20 Template suggestion
        needs_limit = net_income * Decimal("0.50")
        wants_limit = net_income * Decimal("0.30")
        savings_target = net_income * Decimal("0.20")

        fifty_thirty_twenty = {
            "total_income": Decimal(f"{net_income:.2f}"),
            "needs_limit": Decimal(f"{needs_limit:.2f}"),
            "wants_limit": Decimal(f"{wants_limit:.2f}"),
            "savings_target": Decimal(f"{savings_target:.2f}"),
            "breakdown": {
                "Housing & Rent (Needs)": Decimal(f"{needs_limit * Decimal('0.60'):.2f}"),
                "Groceries (Needs)": Decimal(f"{needs_limit * Decimal('0.25'):.2f}"),
                "Utilities (Needs)": Decimal(f"{needs_limit * Decimal('0.15'):.2f}"),
                "Food & Dining (Wants)": Decimal(f"{wants_limit * Decimal('0.50'):.2f}"),
                "Shopping (Wants)": Decimal(f"{wants_limit * Decimal('0.30'):.2f}"),
                "Entertainment (Wants)": Decimal(f"{wants_limit * Decimal('0.20'):.2f}"),
                "Emergency Reserve / SIP (Savings)": Decimal(f"{savings_target:.2f}")
            }
        }

        return {
            "month": month,
            "total_budget_limit": Decimal(f"{total_limit:.2f}"),
            "overall_utilization_pct": Decimal(f"{overall_utilization:.2f}"),
            "total_overspend": Decimal(f"{total_overspend:.2f}"),
            "items": utilization_items,
            "budget_risks": budget_risks,
            "fifty_thirty_twenty_template": fifty_thirty_twenty
        }

budget_agent = BudgetPlanningAgent()
