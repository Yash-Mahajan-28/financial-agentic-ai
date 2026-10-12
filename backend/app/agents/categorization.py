from decimal import Decimal
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.agents.base import BaseAgent
from app.models.transaction import CategoryOverride
from app.rules.rules_engine import rules_engine
from app.ml.classifier import classifier

class CategorizationAgent(BaseAgent):
    def __init__(self):
        super().__init__("CategorizationAgent")

    def run(self, db: Session, user_id: str, raw_transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
        # 1. Fetch user custom category overrides
        user_overrides = db.query(CategoryOverride).filter(CategoryOverride.user_id == user_id).all()
        tx_overrides = {o.pattern_or_tx_id: o.category for o in user_overrides if o.override_type == "TRANSACTION"}
        merchant_overrides = {o.pattern_or_tx_id.upper(): o.category for o in user_overrides if o.override_type == "MERCHANT"}

        categorized_results = []
        needs_review_count = 0

        for tx in raw_transactions:
            desc = tx.get("description", "").strip()
            desc_upper = desc.upper()
            ref = tx.get("reference", "")
            direction = tx.get("direction", "DEBIT")
            amount = tx.get("amount", Decimal("0.00"))

            chosen_category = None
            category_source = "unclassified"
            classifier_score = None
            review_state = "APPROVED"

            # 1. User Transaction Correction
            if ref and ref in tx_overrides:
                chosen_category = tx_overrides[ref]
                category_source = "user_override"
            # 2. User Merchant Mapping
            elif any(m in desc_upper for m in merchant_overrides):
                matching_m = next(m for m in merchant_overrides if m in desc_upper)
                chosen_category = merchant_overrides[matching_m]
                category_source = "user_approved_merchant"
            # 3. Configured Merchant Rule
            else:
                rule_match = rules_engine.match_merchant_rule(desc)
                if rule_match:
                    chosen_category = rule_match
                    category_source = "merchant_rule"
                # 4. Local Trained Classifier
                else:
                    pred_cat, score = classifier.predict(desc)
                    chosen_category = pred_cat
                    category_source = "ml_classifier"
                    classifier_score = Decimal(f"{score:.4f}")
                    # Proposed 0.75 cutoff routes to review
                    if score < 0.75:
                        review_state = "NEEDS_REVIEW"
                        needs_review_count += 1

            # 5. Fallback Unclassified
            if not chosen_category:
                chosen_category = "Unclassified"
                category_source = "unclassified"
                review_state = "NEEDS_REVIEW"
                needs_review_count += 1

            # Determine transaction type
            tx_type = "EXPENSE"
            if direction == "CREDIT":
                if "SALARY" in desc_upper or chosen_category == "Income":
                    tx_type = "INCOME"
                elif "REFUND" in desc_upper:
                    tx_type = "REFUND"
                elif "REVERSAL" in desc_upper:
                    tx_type = "REFUND"
                else:
                    tx_type = "INCOME"
            else: # DEBIT
                if "REPAYMENT" in desc_upper or "CREDIT CARD" in desc_upper:
                    tx_type = "CREDIT_CARD_REPAYMENT"
                elif "TRANSFER" in desc_upper and ("SELF" in desc_upper or "SAVINGS" in desc_upper):
                    tx_type = "TRANSFER"
                elif chosen_category == "Debt Settlement" or "LOAN EMI" in desc_upper:
                    tx_type = "EXPENSE" # Counted in debt burden
                else:
                    tx_type = "EXPENSE"

            tx_copy = dict(tx)
            tx_copy.update({
                "category": chosen_category,
                "category_source": category_source,
                "classifier_score": classifier_score,
                "review_state": review_state,
                "transaction_type": tx_type
            })
            categorized_results.append(tx_copy)

        return {
            "total_processed": len(categorized_results),
            "needs_review_count": needs_review_count,
            "categorized_transactions": categorized_results
        }

categorization_agent = CategorizationAgent()
