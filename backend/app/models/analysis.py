import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, JSON
from app.database import Base

class AnalysisRun(Base):
    __tablename__ = "analysis_runs"
    
    run_id = Column(String(64), primary_key=True, index=True)
    user_id = Column(String(64), ForeignKey("users.user_id"), nullable=False, index=True)
    data_version = Column(String(32), nullable=False)
    config_version = Column(String(32), default="finance-v1", nullable=False)
    cutoff_date = Column(String(10), nullable=False) # e.g. "2026-04-01"
    status = Column(String(32), default="COMPLETED", nullable=False)
    summary_metrics = Column(JSON, default=dict, nullable=False)
    wellness_score = Column(JSON, default=dict, nullable=False)
    computed_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

class Insight(Base):
    __tablename__ = "insights"
    
    insight_id = Column(String(64), primary_key=True, index=True)
    run_id = Column(String(64), ForeignKey("analysis_runs.run_id"), nullable=False, index=True)
    user_id = Column(String(64), ForeignKey("users.user_id"), nullable=False, index=True)
    insight_type = Column(String(32), nullable=False, index=True) # BUDGET_RISK, UNUSUAL_EXPENSE, RECURRING_CANDIDATE, CASH_SHORTFALL, SAVINGS_OPPORTUNITY
    severity = Column(String(16), default="MEDIUM", nullable=False) # HIGH, MEDIUM, LOW, INFO
    observation = Column(String(255), nullable=False)
    metric = Column(JSON, default=dict, nullable=False)
    evidence = Column(JSON, default=dict, nullable=False)
    action = Column(String(255), nullable=False)
    assumptions = Column(JSON, default=list, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

class Alert(Base):
    __tablename__ = "alerts"
    
    alert_id = Column(String(64), primary_key=True, index=True)
    user_id = Column(String(64), ForeignKey("users.user_id"), nullable=False, index=True)
    deduplication_key = Column(String(128), nullable=False, index=True)
    insight_id = Column(String(64), nullable=True)
    title = Column(String(128), nullable=False)
    message = Column(Text, nullable=False)
    severity = Column(String(16), default="MEDIUM", nullable=False)
    status = Column(String(16), default="UNREAD", nullable=False, index=True) # UNREAD, ACKNOWLEDGED, RESOLVED
    resolution_notes = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow, nullable=False)

class AuditEvent(Base):
    __tablename__ = "audit_events"
    
    event_id = Column(String(64), primary_key=True, index=True)
    user_id = Column(String(64), ForeignKey("users.user_id"), nullable=False, index=True)
    actor = Column(String(64), default="user", nullable=False)
    action = Column(String(64), nullable=False)
    entity_type = Column(String(64), nullable=False)
    entity_id = Column(String(64), nullable=False)
    details = Column(JSON, default=dict, nullable=False)
    correlation_id = Column(String(64), nullable=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
