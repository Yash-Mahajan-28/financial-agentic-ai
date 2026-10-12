import uuid
from decimal import Decimal
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.models.user import User, Account
from app.models.budget import Obligation
from app.models.goal import FinancialGoal
from app.orchestrator import orchestrator
from app.api.deps import get_current_user

router = APIRouter(prefix="/v1", tags=["Accounts, Obligations & Goals"])

class BalanceUpdateRequest(BaseModel):
    balance: Decimal
    balance_as_of: str # YYYY-MM-DD

class ObligationCreate(BaseModel):
    title: str
    amount: Decimal
    direction: str = "DEBIT" # CREDIT, DEBIT
    day_of_month: int
    category: str
    obligation_type: str = "BILL" # SALARY, BILL, EMI, SUBSCRIPTION
    account_id: str
    is_confirmed: bool = True

class GoalCreate(BaseModel):
    title: str
    target_amount: Decimal
    current_amount: Decimal = Decimal("0.00")
    target_date: str # YYYY-MM-DD
    category: str = "Savings"

@router.get("/accounts")
def list_accounts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    accs = db.query(Account).filter(Account.user_id == current_user.user_id).all()
    return [
        {
            "account_id": a.account_id,
            "account_name": a.account_name,
            "account_type": a.account_type,
            "account_number_masked": a.account_number_masked,
            "currency": a.currency,
            "balance": a.balance,
            "balance_as_of": a.balance_as_of
        } for a in accs
    ]

@router.put("/accounts/{account_id}/balance")
def update_account_balance(
    account_id: str,
    req: BalanceUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    acc = db.query(Account).filter(
        Account.account_id == account_id,
        Account.user_id == current_user.user_id
    ).first()
    if not acc:
        raise HTTPException(status_code=404, detail="Account not found.")

    acc.balance = req.balance
    acc.balance_as_of = req.balance_as_of
    db.commit()

    # Re-run pipeline to update cash forecast
    orchestrator.run_full_pipeline(db, current_user.user_id, trigger_reason="ACCOUNT_BALANCE_UPDATE")
    return {"message": "Account balance updated successfully.", "account_id": account_id, "balance": req.balance}

@router.get("/obligations")
def list_obligations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    obs = db.query(Obligation).filter(Obligation.user_id == current_user.user_id).all()
    return [
        {
            "obligation_id": o.obligation_id,
            "title": o.title,
            "amount": o.amount,
            "direction": o.direction,
            "day_of_month": o.day_of_month,
            "category": o.category,
            "obligation_type": o.obligation_type,
            "account_id": o.account_id,
            "is_confirmed": o.is_confirmed,
            "is_active": o.is_active
        } for o in obs
    ]

@router.post("/obligations")
def create_obligation(
    req: ObligationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    new_ob = Obligation(
        obligation_id=f"ob_{uuid.uuid4().hex[:8]}",
        user_id=current_user.user_id,
        title=req.title,
        amount=req.amount,
        direction=req.direction,
        day_of_month=req.day_of_month,
        category=req.category,
        obligation_type=req.obligation_type,
        account_id=req.account_id,
        is_confirmed=req.is_confirmed,
        is_active=True
    )
    db.add(new_ob)
    db.commit()

    orchestrator.run_full_pipeline(db, current_user.user_id, trigger_reason="OBLIGATION_CREATED")
    return {"message": "Obligation scheduled.", "obligation_id": new_ob.obligation_id}

@router.get("/goals")
def list_goals(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    goals = db.query(FinancialGoal).filter(FinancialGoal.user_id == current_user.user_id).all()
    return [
        {
            "goal_id": g.goal_id,
            "title": g.title,
            "target_amount": g.target_amount,
            "current_amount": g.current_amount,
            "target_date": g.target_date,
            "category": g.category,
            "is_achieved": g.is_achieved
        } for g in goals
    ]

@router.post("/goals")
def create_goal(
    req: GoalCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    goal = FinancialGoal(
        goal_id=f"gl_{uuid.uuid4().hex[:8]}",
        user_id=current_user.user_id,
        title=req.title,
        target_amount=req.target_amount,
        current_amount=req.current_amount,
        target_date=req.target_date,
        category=req.category,
        is_achieved=False
    )
    db.add(goal)
    db.commit()
    return {"message": "Financial goal created.", "goal_id": goal.goal_id}
