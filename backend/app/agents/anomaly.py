import statistics
from decimal import Decimal
from datetime import datetime, timedelta
from typing import Dict, Any, List
from collections import defaultdict
from sqlalchemy.orm import Session

from app.agents.base import BaseAgent
from app.models.transaction import Transaction
from app.rules.rules_engine import rules_engine

class AnomalyDetectionAgent(BaseAgent):
    def __init__(self):
        super().__init__("AnomalyDetectionAgent")

    def run(self, db: Session, user_id: str) -> Dict[str, Any]:
        history_days = rules_engine.anomaly_history_days # 90
        min_samples = rules_engine.anomaly_min_samples # 10
        min_floor = rules_engine.anomaly_min_amount # 2000.00

        # Fetch all approved expenses
        txs = db.query(Transaction).filter(
            Transaction.user_id == user_id,
            Transaction.review_state == "APPROVED",
            Transaction.transaction_type == "EXPENSE"
        ).order_by(Transaction.date.asc()).all()

        anomalies = []
        duplicate_candidates = []

        # 1. Detect Possible Duplicate Charges within 1 calendar day
        # Group by (normalized merchant, amount)
        by_merchant_amt = defaultdict(list)
        for t in txs:
            norm_merchant = t.category_source if t.category_source != "unclassified" else t.description[:12]
            key = (norm_merchant, t.amount)
            by_merchant_amt[key].append(t)

        for (merchant_name, amt), group in by_merchant_amt.items():
            if len(group) >= 2:
                for i in range(len(group)):
                    for j in range(i + 1, len(group)):
                        t1, t2 = group[i], group[j]
                        d1 = datetime.strptime(t1.date, "%Y-%m-%d")
                        d2 = datetime.strptime(t2.date, "%Y-%m-%d")
                        if abs((d2 - d1).days) <= 1 and t1.reference != t2.reference:
                            duplicate_candidates.append({
                                "transaction_id_1": t1.transaction_id,
                                "transaction_id_2": t2.transaction_id,
                                "amount": amt,
                                "date_1": t1.date,
                                "date_2": t2.date,
                                "description": t1.description,
                                "observation": f"Two identical charges of INR {amt} on {t1.date} and {t2.date} with different references."
                            })

        # 2. Statistical Outlier Detection using Median and MAD
        # For each transaction, compare with prior transactions in same category within history_days
        cat_history = defaultdict(list)
        for t in txs:
            t_date = datetime.strptime(t.date, "%Y-%m-%d")
            cat = t.category
            amt = float(t.amount)

            # Look up past transactions in same category within 90 days
            past_samples = [
                past_amt for (past_d, past_amt) in cat_history[cat]
                if (t_date - past_d).days > 0 and (t_date - past_d).days <= history_days
            ]

            if len(past_samples) >= min_samples:
                median = statistics.median(past_samples)
                deviations = [abs(x - median) for x in past_samples]
                mad = statistics.median(deviations) if deviations else 0.0

                # Threshold: max(3m, m + 6MAD, 2000.00)
                t1 = 3.0 * median
                t2 = median + (6.0 * mad)
                threshold = max(t1, t2, float(min_floor))

                if amt > threshold:
                    anomalies.append({
                        "transaction_id": t.transaction_id,
                        "date": t.date,
                        "description": t.description,
                        "category": cat,
                        "amount": Decimal(f"{amt:.2f}"),
                        "baseline_median": Decimal(f"{median:.2f}"),
                        "baseline_mad": Decimal(f"{mad:.2f}"),
                        "sample_count": len(past_samples),
                        "calculated_threshold": Decimal(f"{threshold:.2f}"),
                        "observation": f"Unusual {cat} expense of INR {amt:.2f} (Threshold: INR {threshold:.2f})"
                    })

            # Record in history
            cat_history[cat].append((t_date, amt))

        return {
            "anomalies_detected": len(anomalies),
            "duplicates_detected": len(duplicate_candidates),
            "anomalies": anomalies,
            "duplicate_candidates": duplicate_candidates
        }

anomaly_agent = AnomalyDetectionAgent()
