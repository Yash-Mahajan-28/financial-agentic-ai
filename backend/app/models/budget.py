import datetime
from sqlalchemy import Column, String, Numeric, DateTime, ForeignKey, Integer, Boolean
from app.database import Base

class Budget(Base):
    __tablename__ = "budgets"
    
    budget_id = Column(String(64), primary_key=True, index=True)
    user_id = Column(String(64), ForeignKey("users.user_id"), nullable=False, index=True)
    month = Column(String(7), nullable=False, index=True) # YYYY-MM
    category = Column(String(64), nullable=False, index=True)
    limit_amount = Column(Numeric(18, 2), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow, nullable=False)

class Obligation(Base):
    __tablename__ = "obligations"
    
    obligation_id = Column(String(64), primary_key=True, index=True)
    user_id = Column(String(64), ForeignKey("users.user_id"), nullable=False, index=True)
    title = Column(String(128), nullable=False)
    amount = Column(Numeric(18, 2), nullable=False)
    direction = Column(String(8), default="DEBIT", nullable=False) # CREDIT, DEBIT
    day_of_month = Column(Integer, nullable=False) # 1 - 31
    category = Column(String(64), nullable=False)
    obligation_type = Column(String(32), default="BILL", nullable=False) # SALARY, BILL, EMI, SUBSCRIPTION
    account_id = Column(String(64), nullable=False)
    is_confirmed = Column(Boolean, default=True, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
