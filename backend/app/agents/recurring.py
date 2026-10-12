import statistics
from decimal import Decimal
from datetime import datetime, timedelta
from typing import Dict, Any, List
from collections import defaultdict
from sqlalchemy.orm import Session

from app.agents.base import BaseAgent
from app.models.transaction import Transaction
from app.rules.rules_engine import rules_engine

class SubscriptionIntelligenceAgent(BaseAgent):
    def __init__(self):
        super().__init__("SubscriptionIntelligenceAgent")

    def run(self, db: Session, user_id: str) -> Dict[str, Any]:
        min_charges = rules_engine.recurring_min_charges # 3
        gap_min = rules_engine.recurring_gap_min_days # 25
        gap_max = rules_engine.recurring_gap_max_days # 35
        amt_tolerance = float(rules_engine.recurring_amount_tolerance) # 0.10

        txs = db.query(Transaction).filter(
            Transaction.user_id == user_id,
            Transaction.review_state == "APPROVED",
            Transaction.transaction_type == "EXPENSE"
        ).order_by(Transaction.date.asc()).all()

        # Group by normalized merchant keywords
        by_merchant = defaultdict(list)
        for t in txs:
            # Extract dominant merchant keyword
            desc_words = t.description.upper().split()
            merchant_key = desc_words[0] if desc_words else "UNKNOWN"
            if len(desc_words) > 1 and desc_words[0] in ["THE", "MONTHLY"]:
                merchant_key = f"{desc_words[0]} {desc_words[1]}"
            by_merchant[merchant_key].append(t)

        candidates = []

        for merchant_key, group in by_merchant.items():
            if len(group) < min_charges:
                continue

            # Sort by date
            group_sorted = sorted(group, key=lambda x: x.date)
            dates = [datetime.strptime(x.date, "%Y-%m-%d") for x in group_sorted]
            amounts = [float(x.amount) for x in group_sorted]

            # Calculate successive date gaps
            gaps = [(dates[i] - dates[i-1]).days for i in range(1, len(dates))]
            
            # Check if all or most successive gaps fall within 25 and 35 days
            valid_gaps = [g for g in gaps if gap_min <= g <= gap_max]
            if len(valid_gaps) < (min_charges - 1):
                continue

            median_amt = statistics.median(amounts)
            # Check if amounts are within 10% tolerance of median
            amount_matches = all(abs(a - median_amt) <= (median_amt * amt_tolerance) for a in amounts)
            if not amount_matches:
                continue

            median_gap = int(statistics.median(gaps))
            last_date = dates[-1]
            next_expected = last_date + timedelta(days=median_gap)
            annual_avoidable_savings = Decimal(f"{median_amt * 12:.2f}")

            candidates.append({
                "merchant": merchant_key,
                "category": group_sorted[-1].category,
                "median_amount": Decimal(f"{median_amt:.2f}"),
                "charge_count": len(group_sorted),
                "last_charged_date": last_date.strftime("%Y-%m-%d"),
                "next_expected_date": next_expected.strftime("%Y-%m-%d"),
                "observed_interval_days": median_gap,
                "potential_annual_savings": annual_avoidable_savings,
                "transaction_ids": [x.transaction_id for x in group_sorted],
                "observation": f"Recurring charge pattern detected for {merchant_key}: {len(group_sorted)} charges, avg INR {median_amt:.2f}."
            })

        return {
            "total_recurring_found": len(candidates),
            "subscription_candidates": candidates
        }

recurring_agent = SubscriptionIntelligenceAgent()
