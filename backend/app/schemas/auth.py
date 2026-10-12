from typing import Optional, List
from pydantic import BaseModel
from decimal import Decimal

class LoginRequest(BaseModel):
    email: str
    password: str

class UserProfile(BaseModel):
    user_id: str
    email: str
    full_name: str
    currency: str
    confirmed_net_income: Decimal
    confirmed_monthly_debt: Decimal
    liquid_emergency_reserve: Decimal
    target_savings_rate: Decimal
    debt_burden_ceiling: Decimal
    reserve_target_months: int

class LoginResponse(BaseModel):
    message: str
    user: UserProfile

class ProfileUpdateRequest(BaseModel):
    full_name: Optional[str] = None
    confirmed_net_income: Optional[Decimal] = None
    confirmed_monthly_debt: Optional[Decimal] = None
    liquid_emergency_reserve: Optional[Decimal] = None
    target_savings_rate: Optional[Decimal] = None
    debt_burden_ceiling: Optional[Decimal] = None
    reserve_target_months: Optional[int] = None
