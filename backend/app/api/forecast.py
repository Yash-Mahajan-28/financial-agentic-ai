from decimal import Decimal
from typing import Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.forecast import ForecastRead, ScenarioSimulationRequest, ScenarioSimulationResponse, DailyForecastItem
from app.agents import forecast_agent
from app.api.deps import get_current_user

router = APIRouter(prefix="/v1", tags=["Cash Flow Forecast & Scenarios"])

@router.get("/forecast", response_model=ForecastRead)
def get_forecast(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    res = forecast_agent.execute(db, current_user.user_id)
    timeline_items = [
        DailyForecastItem(
            date=t["date"],
            day_number=t["day_number"],
            opening_balance=t["opening_balance"],
            inflows=t["inflows"],
            outflows=t["outflows"],
            closing_balance=t["closing_balance"],
            events=t["events"]
        ) for t in res["timeline"]
    ]

    return ForecastRead(
        horizon_days=res["horizon_days"],
        balance_as_of=res["balance_as_of"],
        opening_liquid_balance=res["opening_liquid_balance"],
        projected_closing_balance=res["projected_closing_balance"],
        minimum_projected_balance=res["minimum_projected_balance"],
        minimum_balance_date=res["minimum_balance_date"],
        has_shortfall=res["has_shortfall"],
        first_shortfall_date=res["first_shortfall_date"],
        variable_daily_allowance=res["variable_daily_allowance"],
        currency=res["currency"],
        timeline=timeline_items
    )

@router.post("/scenarios", response_model=ScenarioSimulationResponse)
def simulate_scenario(
    req: ScenarioSimulationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 1. Baseline
    base_res = forecast_agent.execute(db, current_user.user_id)
    
    # 2. Scenario
    scenario_res = forecast_agent.execute(
        db,
        current_user.user_id,
        remove_salary=req.remove_salary,
        extra_one_time_expense=req.extra_one_time_expense or Decimal("0.00"),
        extra_expense_day=req.extra_expense_day or 15,
        variable_spend_multiplier=req.variable_spend_multiplier or Decimal("1.00")
    )

    base_timeline = [
        DailyForecastItem(
            date=t["date"],
            day_number=t["day_number"],
            opening_balance=t["opening_balance"],
            inflows=t["inflows"],
            outflows=t["outflows"],
            closing_balance=t["closing_balance"],
            events=t["events"]
        ) for t in base_res["timeline"]
    ]

    scen_timeline = [
        DailyForecastItem(
            date=t["date"],
            day_number=t["day_number"],
            opening_balance=t["opening_balance"],
            inflows=t["inflows"],
            outflows=t["outflows"],
            closing_balance=t["closing_balance"],
            events=t["events"]
        ) for t in scenario_res["timeline"]
    ]

    base_close = base_res["projected_closing_balance"]
    scen_close = scenario_res["projected_closing_balance"]

    return ScenarioSimulationResponse(
        scenario_name=req.scenario_name,
        baseline_closing_balance=base_close,
        scenario_closing_balance=scen_close,
        net_impact=scen_close - base_close,
        has_shortfall=scenario_res["has_shortfall"],
        first_shortfall_date=scenario_res["first_shortfall_date"],
        baseline_timeline=base_timeline,
        scenario_timeline=scen_timeline
    )
