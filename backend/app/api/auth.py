from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, LoginResponse, UserProfile, ProfileUpdateRequest
from app.services.auth_service import auth_service
from app.api.deps import get_current_user

router = APIRouter(prefix="/v1/auth", tags=["Authentication"])

@router.post("/login", response_model=LoginResponse)
def login(creds: LoginRequest, response: Response, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == creds.email).first()
    if not user or not auth_service.verify_password(creds.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials. Use demo@agentic.finance / Demo@1234."
        )

    token = auth_service.create_session_token(user.user_id)
    # Set HttpOnly session cookie
    response.set_cookie(
        key="session_token",
        value=token,
        httponly=True,
        samesite="lax",
        max_age=86400 * 7,
        path="/"
    )

    profile = UserProfile(
        user_id=user.user_id,
        email=user.email,
        full_name=user.full_name,
        currency=user.currency,
        confirmed_net_income=user.confirmed_net_income,
        confirmed_monthly_debt=user.confirmed_monthly_debt,
        liquid_emergency_reserve=user.liquid_emergency_reserve,
        target_savings_rate=user.target_savings_rate,
        debt_burden_ceiling=user.debt_burden_ceiling,
        reserve_target_months=user.reserve_target_months
    )

    return LoginResponse(message="Authentication successful", user=profile)

@router.get("/me", response_model=UserProfile)
def get_me(current_user: User = Depends(get_current_user)):
    return UserProfile(
        user_id=current_user.user_id,
        email=current_user.email,
        full_name=current_user.full_name,
        currency=current_user.currency,
        confirmed_net_income=current_user.confirmed_net_income,
        confirmed_monthly_debt=current_user.confirmed_monthly_debt,
        liquid_emergency_reserve=current_user.liquid_emergency_reserve,
        target_savings_rate=current_user.target_savings_rate,
        debt_burden_ceiling=current_user.debt_burden_ceiling,
        reserve_target_months=current_user.reserve_target_months
    )

@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(key="session_token", path="/")
    return {"message": "Logged out successfully"}

@router.patch("/profile", response_model=UserProfile)
def update_profile(
    updates: ProfileUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if updates.full_name is not None:
        current_user.full_name = updates.full_name
    if updates.confirmed_net_income is not None:
        current_user.confirmed_net_income = updates.confirmed_net_income
    if updates.confirmed_monthly_debt is not None:
        current_user.confirmed_monthly_debt = updates.confirmed_monthly_debt
    if updates.liquid_emergency_reserve is not None:
        current_user.liquid_emergency_reserve = updates.liquid_emergency_reserve
    if updates.target_savings_rate is not None:
        current_user.target_savings_rate = updates.target_savings_rate
    if updates.debt_burden_ceiling is not None:
        current_user.debt_burden_ceiling = updates.debt_burden_ceiling
    if updates.reserve_target_months is not None:
        current_user.reserve_target_months = updates.reserve_target_months

    db.commit()
    db.refresh(current_user)

    # Trigger re-analysis with new profile inputs
    from app.orchestrator import orchestrator
    orchestrator.run_full_pipeline(db, current_user.user_id, trigger_reason="PROFILE_UPDATE")

    return get_me(current_user)
