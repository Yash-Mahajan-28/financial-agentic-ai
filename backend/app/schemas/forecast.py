from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from decimal import Decimal

class DailyForecastItem(BaseModel):
    date: str
    day_number: int
    opening_balance: Decimal
    inflows: Decimal
    outflows: Decimal
    closing_balance: Decimal
    events: List[str]

class ForecastRead(BaseModel):
    horizon_days: int = 30
    balance_as_of: str
    opening_liquid_balance: Decimal
    projected_closing_balance: Decimal
    minimum_projected_balance: Decimal
    minimum_balance_date: str
    has_shortfall: bool
    first_shortfall_date: Optional[str] = None
    variable_daily_allowance: Decimal
    currency: str = "INR"
    timeline: List[DailyForecastItem]

class ScenarioSimulationRequest(BaseModel):
    scenario_name: str = "Custom Scenario"
    remove_salary: bool = False
    extra_one_time_expense: Optional[Decimal] = Decimal("0.00")
    extra_expense_day: Optional[int] = 15
    variable_spend_multiplier: Optional[Decimal] = Decimal("1.00")

class ScenarioSimulationResponse(BaseModel):
    scenario_name: str
    baseline_closing_balance: Decimal
    scenario_closing_balance: Decimal
    net_impact: Decimal
    has_shortfall: bool
    first_shortfall_date: Optional[str] = None
    baseline_timeline: List[DailyForecastItem]
    scenario_timeline: List[DailyForecastItem]
