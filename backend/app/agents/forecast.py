from decimal import Decimal
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.agents.base import BaseAgent
from app.models.user import User, Account
from app.models.budget import Obligation
from app.rules.rules_engine import rules_engine

class CashFlowForecastAgent(BaseAgent):
    def __init__(self):
        super().__init__("CashFlowForecastAgent")

    def run(
        self,
        db: Session,
        user_id: str,
        remove_salary: bool = False,
        extra_one_time_expense: Decimal = Decimal("0.00"),
        extra_expense_day: int = 15,
        variable_spend_multiplier: Decimal = Decimal("1.00"),
        daily_allowance_override: Optional[Decimal] = None
    ) -> Dict[str, Any]:
        horizon_days = rules_engine.forecast_horizon_days # 30

        # 1. Fetch liquid accounts (CHECKING / SAVINGS)
        accounts = db.query(Account).filter(
            Account.user_id == user_id,
            Account.account_type.in_(["CHECKING", "SAVINGS"])
        ).all()

        opening_balance = sum([Decimal(str(a.balance)) for a in accounts]) if accounts else Decimal("32000.00")
        balance_as_of = accounts[0].balance_as_of if accounts else "2026-04-01"
        start_date = datetime.strptime(balance_as_of, "%Y-%m-%d")

        # 2. Fetch confirmed active obligations
        obligations = db.query(Obligation).filter(
            Obligation.user_id == user_id,
            Obligation.is_active == True,
            Obligation.is_confirmed == True
        ).all()

        # 3. Estimate or use variable cash spending allowance
        # Spec Page 11 uses INR 600.00 per day baseline allowance
        base_allowance = daily_allowance_override or Decimal("600.00")
        daily_variable_spend = base_allowance * variable_spend_multiplier

        timeline = []
        current_balance = opening_balance
        min_balance = opening_balance
        min_balance_date = balance_as_of
        has_shortfall = False
        first_shortfall_date = None

        for day_idx in range(1, horizon_days + 1):
            day_date = start_date + timedelta(days=day_idx)
            day_str = day_date.strftime("%Y-%m-%d")
            day_of_month = day_date.day

            day_inflows = Decimal("0.00")
            day_outflows = daily_variable_spend # Variable daily allowance
            events = [f"Daily variable cash allowance: -INR {daily_variable_spend:.2f}"]

            # Check extra one-time expense scenario
            if extra_one_time_expense > Decimal("0.00") and day_idx == extra_expense_day:
                day_outflows += extra_one_time_expense
                events.append(f"Scenario extra expense: -INR {extra_one_time_expense:.2f}")

            # Check scheduled obligations matching day_of_month
            for ob in obligations:
                if ob.day_of_month == day_of_month:
                    amt = Decimal(str(ob.amount))
                    if ob.direction == "CREDIT":
                        if ob.obligation_type == "SALARY" and remove_salary:
                            events.append(f"Simulated omission: {ob.title} skipped in scenario")
                        else:
                            day_inflows += amt
                            events.append(f"Inflow: {ob.title} +INR {amt:.2f}")
                    else:
                        day_outflows += amt
                        events.append(f"Outflow: {ob.title} -INR {amt:.2f}")

            # CONSERVATIVE ORDERING: Within-day outflows deducted BEFORE inflows
            intraday_dip = current_balance - day_outflows
            if intraday_dip < min_balance:
                min_balance = intraday_dip
                min_balance_date = day_str
            if intraday_dip < Decimal("0.00") and not has_shortfall:
                has_shortfall = True
                first_shortfall_date = day_str

            # End of day balance after inflows
            day_closing = intraday_dip + day_inflows
            if day_closing < min_balance:
                min_balance = day_closing
                min_balance_date = day_str
            if day_closing < Decimal("0.00") and not has_shortfall:
                has_shortfall = True
                first_shortfall_date = day_str

            timeline.append({
                "date": day_str,
                "day_number": day_idx,
                "opening_balance": Decimal(f"{current_balance:.2f}"),
                "inflows": Decimal(f"{day_inflows:.2f}"),
                "outflows": Decimal(f"{day_outflows:.2f}"),
                "closing_balance": Decimal(f"{day_closing:.2f}"),
                "events": events
            })

            current_balance = day_closing

        projected_closing = current_balance

        return {
            "horizon_days": horizon_days,
            "balance_as_of": balance_as_of,
            "opening_liquid_balance": Decimal(f"{opening_balance:.2f}"),
            "projected_closing_balance": Decimal(f"{projected_closing:.2f}"),
            "minimum_projected_balance": Decimal(f"{min_balance:.2f}"),
            "minimum_balance_date": min_balance_date,
            "has_shortfall": has_shortfall,
            "first_shortfall_date": first_shortfall_date,
            "variable_daily_allowance": Decimal(f"{daily_variable_spend:.2f}"),
            "currency": "INR",
            "timeline": timeline
        }

forecast_agent = CashFlowForecastAgent()
