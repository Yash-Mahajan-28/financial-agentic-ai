import uuid
from decimal import Decimal
from typing import Dict
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.budget import Budget
from app.schemas.budget import BudgetRead, BudgetUpdateRequest, FiftyThirtyTwentyTemplate
from app.agents import budget_agent, spending_agent
from app.orchestrator import orchestrator
from app.api.deps import get_current_user

router = APIRouter(prefix="/v1/budgets", tags=["Budgets & Planning"])

@router.get("/{month}")
def get_budget(
    month: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    budget_records = db.query(Budget).filter(
        Budget.user_id == current_user.user_id,
        Budget.month == month
    ).all()

    limits = {b.category: Decimal(str(b.limit_amount)) for b in budget_records}

    # Fetch spending to compute utilization
    spending_res = spending_agent.execute(db, current_user.user_id)
    monthly_trends = spending_res.get("monthly_trends", {}).get(month, {})
    cat_spending = {k: v["current_spending"] for k, v in monthly_trends.get("categories", {}).items()}
    net_income = monthly_trends.get("total_income", Decimal(str(current_user.confirmed_net_income)))

    budget_calc = budget_agent.execute(db, current_user.user_id, month, cat_spending, net_income)

    return {
        "month": month,
        "limits": limits,
        "utilization_summary": budget_calc
    }

@router.put("/{month}")
def update_budget(
    month: str,
    req: BudgetUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    for cat, limit in req.limits.items():
        if limit < Decimal("0.00"):
            raise HTTPException(status_code=400, detail=f"Budget limit cannot be negative for '{cat}'")

    # Replace existing budgets for month
    db.query(Budget).filter(
        Budget.user_id == current_user.user_id,
        Budget.month == month
    ).delete()

    for cat, limit in req.limits.items():
        b = Budget(
            budget_id=f"bg_{uuid.uuid4().hex[:8]}",
            user_id=current_user.user_id,
            month=month,
            category=cat,
            limit_amount=limit
        )
        db.add(b)

    db.commit()

    # Trigger re-analysis
    orchestrator.run_full_pipeline(db, current_user.user_id, trigger_reason="BUDGET_UPDATE")

    return {"message": "Budget updated successfully for month", "month": month, "limits": req.limits}

@router.get("/templates/50-30-20", response_model=FiftyThirtyTwentyTemplate)
def get_fifty_thirty_twenty_template(
    current_user: User = Depends(get_current_user)
):
    income = Decimal(str(current_user.confirmed_net_income))
    needs = income * Decimal("0.50")
    wants = income * Decimal("0.30")
    savings = income * Decimal("0.20")

    return FiftyThirtyTwentyTemplate(
        total_income=income,
        needs_limit=needs,
        wants_limit=wants,
        savings_target=savings,
        breakdown={
            "Housing & Rent (Needs)": needs * Decimal("0.60"),
            "Groceries (Needs)": needs * Decimal("0.25"),
            "Utilities (Needs)": needs * Decimal("0.15"),
            "Food & Dining (Wants)": wants * Decimal("0.50"),
            "Shopping (Wants)": wants * Decimal("0.30"),
            "Entertainment (Wants)": wants * Decimal("0.20"),
            "Emergency Savings / SIP": savings
        }
    )
