from decimal import Decimal
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from app.agents.base import BaseAgent
from app.models.user import User

def clamp(val: Decimal, low: Decimal = Decimal("0.00"), high: Decimal = Decimal("1.00")) -> Decimal:
    return max(low, min(val, high))

class HealthScoringAgent(BaseAgent):
    def __init__(self):
        super().__init__("HealthScoringAgent")

    def run(self, db: Session, user_id: str, net_monthly_surplus: Decimal, total_overspend: Decimal, total_budget_limit: Decimal, essential_monthly_spending: Decimal) -> Dict[str, Any]:
        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
            return {"status": "INCOMPLETE", "score": None, "explanation": "User profile not found."}

        confirmed_net_income = Decimal(str(user.confirmed_net_income))
        confirmed_debt = Decimal(str(user.confirmed_monthly_debt))
        liquid_reserve = Decimal(str(user.liquid_emergency_reserve))
        target_savings_rate = Decimal(str(user.target_savings_rate)) # 0.20
        debt_ceiling = Decimal(str(user.debt_burden_ceiling)) # 0.40
        reserve_target_months = Decimal(str(user.reserve_target_months)) # 3

        is_complete = True
        missing_inputs = []

        # 1. Savings discipline S (35%)
        S = None
        if confirmed_net_income > Decimal("0.00") and target_savings_rate > Decimal("0.00"):
            raw_s = (net_monthly_surplus / confirmed_net_income) / target_savings_rate
            S = clamp(raw_s, Decimal("0.00"), Decimal("1.00"))
        else:
            is_complete = False
            missing_inputs.append("confirmed_net_income")

        # 2. Budget discipline B (25%)
        B = None
        if total_budget_limit > Decimal("0.00"):
            raw_overspend_ratio = total_overspend / total_budget_limit
            B = Decimal("1.00") - clamp(raw_overspend_ratio, Decimal("0.00"), Decimal("1.00"))
        else:
            is_complete = False
            missing_inputs.append("total_budget_limit")

        # 3. Debt burden D (20%)
        D = None
        if confirmed_net_income > Decimal("0.00") and debt_ceiling > Decimal("0.00"):
            raw_debt_ratio = (confirmed_debt / confirmed_net_income) / debt_ceiling
            D = Decimal("1.00") - clamp(raw_debt_ratio, Decimal("0.00"), Decimal("1.00"))
        else:
            is_complete = False
            missing_inputs.append("debt_burden_parameters")

        # 4. Reserve coverage E (20%)
        E = None
        if essential_monthly_spending > Decimal("0.00") and reserve_target_months > Decimal("0.00"):
            raw_reserve_ratio = (liquid_reserve / essential_monthly_spending) / reserve_target_months
            E = clamp(raw_reserve_ratio, Decimal("0.00"), Decimal("1.00"))
        else:
            # If no essential spend measured yet, fallback or mark incomplete
            if essential_monthly_spending == Decimal("0.00"):
                is_complete = False
                missing_inputs.append("essential_monthly_spending")

        total_score = None
        if is_complete and S is not None and B is not None and D is not None and E is not None:
            weighted = (Decimal("0.35") * S) + (Decimal("0.25") * B) + (Decimal("0.20") * D) + (Decimal("0.20") * E)
            total_score = int(round(float(weighted * Decimal("100.00"))))
            status = "COMPLETE"
            explanation = "Calculated across all four financial disciplines."
        else:
            status = "INCOMPLETE"
            explanation = f"Incomplete input data: missing {', '.join(missing_inputs)}."

        return {
            "status": status,
            "score": total_score,
            "formula_version": "wellness-v1",
            "explanation": explanation,
            "savings_discipline": Decimal(f"{S:.4f}") if S is not None else None,
            "budget_discipline": Decimal(f"{B:.4f}") if B is not None else None,
            "debt_burden": Decimal(f"{D:.4f}") if D is not None else None,
            "reserve_coverage": Decimal(f"{E:.4f}") if E is not None else None,
            "inputs": {
                "net_monthly_surplus": net_monthly_surplus,
                "confirmed_net_income": confirmed_net_income,
                "confirmed_monthly_debt": confirmed_debt,
                "liquid_emergency_reserve": liquid_reserve,
                "essential_monthly_spending": essential_monthly_spending
            }
        }

health_agent = HealthScoringAgent()
