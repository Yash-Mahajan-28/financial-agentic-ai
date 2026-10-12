import datetime
from sqlalchemy import Column, String, Numeric, DateTime, ForeignKey, Text, Boolean, Integer
from sqlalchemy.orm import relationship
from app.database import Base

class User(Base):
    __tablename__ = "users"
    
    user_id = Column(String(64), primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    currency = Column(String(3), default="INR", nullable=False)
    
    # Financial profile inputs for health score & planning
    confirmed_net_income = Column(Numeric(18, 2), default=50000.00, nullable=False)
    confirmed_monthly_debt = Column(Numeric(18, 2), default=7000.00, nullable=False)
    liquid_emergency_reserve = Column(Numeric(18, 2), default=75000.00, nullable=False)
    target_savings_rate = Column(Numeric(5, 4), default=0.20, nullable=False)
    debt_burden_ceiling = Column(Numeric(5, 4), default=0.40, nullable=False)
    reserve_target_months = Column(Integer, default=3, nullable=False)
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    accounts = relationship("Account", back_populates="user", cascade="all, delete-orphan")

class Account(Base):
    __tablename__ = "accounts"
    
    account_id = Column(String(64), primary_key=True, index=True)
    user_id = Column(String(64), ForeignKey("users.user_id"), nullable=False, index=True)
    account_name = Column(String(128), nullable=False)
    account_type = Column(String(32), default="CHECKING", nullable=False) # CHECKING, SAVINGS, CREDIT_CARD
    account_number_masked = Column(String(32), default="•••• 0000", nullable=False)
    currency = Column(String(3), default="INR", nullable=False)
    balance = Column(Numeric(18, 2), default=0.00, nullable=False)
    balance_as_of = Column(String(10), default="2026-04-01", nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="accounts")
