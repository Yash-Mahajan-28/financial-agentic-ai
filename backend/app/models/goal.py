import datetime
from sqlalchemy import Column, String, Numeric, DateTime, ForeignKey, Boolean, JSON
from app.database import Base

class FinancialGoal(Base):
    __tablename__ = "financial_goals"
    
    goal_id = Column(String(64), primary_key=True, index=True)
    user_id = Column(String(64), ForeignKey("users.user_id"), nullable=False, index=True)
    title = Column(String(128), nullable=False)
    target_amount = Column(Numeric(18, 2), nullable=False)
    current_amount = Column(Numeric(18, 2), default=0.00, nullable=False)
    target_date = Column(String(10), nullable=False) # YYYY-MM-DD
    category = Column(String(64), default="Savings", nullable=False)
    is_achieved = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

class ScenarioComparison(Base):
    __tablename__ = "scenario_comparisons"
    
    scenario_id = Column(String(64), primary_key=True, index=True)
    user_id = Column(String(64), ForeignKey("users.user_id"), nullable=False, index=True)
    scenario_name = Column(String(128), nullable=False)
    parameters = Column(JSON, default=dict, nullable=False)
    results = Column(JSON, default=dict, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
