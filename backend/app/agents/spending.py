from decimal import Decimal
from typing import Dict, Any, List
from collections import defaultdict
from sqlalchemy.orm import Session

from app.agents.base import BaseAgent
from app.models.transaction import Transaction

class SpendingAnalysisAgent(BaseAgent):
    def __init__(self):
        super().__init__("SpendingAnalysisAgent")

    def run(self, db: Session, user_id: str) -> Dict[str, Any]:
        # Fetch all approved transactions for user
        txs = db.query(Transaction).filter(
            Transaction.user_id == user_id,
            Transaction.review_state == "APPROVED"
        ).order_by(Transaction.date.asc()).all()

        # Monthly breakdown: month -> category -> net amount
        # month format: "YYYY-MM"
        monthly_category_spend: Dict[str, Dict[str, Decimal]] = defaultdict(lambda: defaultdict(lambda: Decimal("0.00")))
        monthly_income: Dict[str, Decimal] = defaultdict(lambda: Decimal("0.00"))
        monthly_total_spend: Dict[str, Decimal] = defaultdict(lambda: Decimal("0.00"))

        for t in txs:
            month = t.date[:7] # e.g. "2026-03"
            amt = Decimal(str(t.amount))

            if t.transaction_type == "EXPENSE":
                monthly_category_spend[month][t.category] += amt
                monthly_total_spend[month] += amt
            elif t.transaction_type == "REFUND":
                # Linked or unlinked refund offsets spending in category
                monthly_category_spend[month][t.category] -= amt
                monthly_total_spend[month] -= amt
            elif t.transaction_type == "INCOME":
                monthly_income[month] += amt

        # Ensure amounts are non-negative net spending
        sorted_months = sorted(monthly_category_spend.keys())
        trends: Dict[str, Dict[str, Any]] = {}

        # Compute month-over-month trend changes
        for i, m in enumerate(sorted_months):
            trends[m] = {
                "month": m,
                "total_spending": monthly_total_spend[m],
                "total_income": monthly_income[m],
                "surplus": monthly_income[m] - monthly_total_spend[m],
                "categories": {}
            }
            prev_m = sorted_months[i - 1] if i > 0 else None
            
            all_cats = set(monthly_category_spend[m].keys())
            if prev_m:
                all_cats.update(monthly_category_spend[prev_m].keys())

            for cat in all_cats:
                curr_val = monthly_category_spend[m].get(cat, Decimal("0.00"))
                prev_val = monthly_category_spend[prev_m].get(cat, Decimal("0.00")) if prev_m else None
                
                pct_change = None
                pct_unavailable = False
                amt_diff = None

                if prev_val is not None:
                    amt_diff = curr_val - prev_val
                    if prev_val > Decimal("0.00"):
                        pct_change = ((curr_val - prev_val) / prev_val) * Decimal("100.00")
                        pct_change = Decimal(f"{pct_change:.2f}")
                    else:
                        # Zero previous baseline: show amount difference and mark percentage unavailable
                        pct_unavailable = True

                trends[m]["categories"][cat] = {
                    "current_spending": curr_val,
                    "previous_spending": prev_val,
                    "amount_difference": amt_diff,
                    "pct_change": pct_change,
                    "pct_unavailable": pct_unavailable
                }

        latest_month = sorted_months[-1] if sorted_months else "2026-03"

        return {
            "sorted_months": sorted_months,
            "latest_month": latest_month,
            "monthly_trends": trends,
            "latest_month_summary": trends.get(latest_month, {
                "total_spending": Decimal("0.00"),
                "total_income": Decimal("0.00"),
                "surplus": Decimal("0.00"),
                "categories": {}
            })
        }

spending_agent = SpendingAnalysisAgent()
