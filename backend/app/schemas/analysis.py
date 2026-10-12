from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from decimal import Decimal
from datetime import datetime

class WellnessScoreRead(BaseModel):
    score: Optional[int] = None
    status: str # COMPLETE, INCOMPLETE
    savings_discipline: Optional[Decimal] = None
    budget_discipline: Optional[Decimal] = None
    debt_burden: Optional[Decimal] = None
    reserve_coverage: Optional[Decimal] = None
    formula_version: str = "wellness-v1"
    explanation: Optional[str] = None

class DashboardSummaryRead(BaseModel):
    period: str
    data_version: str
    computed_at: Optional[datetime] = None
    currency: str = "INR"
    net_income: Decimal
    net_spending: Decimal
    monthly_surplus: Decimal
    total_budget_limit: Decimal
    overall_budget_utilization_pct: Decimal
    wellness_score: WellnessScoreRead
    active_alerts_count: int
    data_coverage_months: int
    latest_statement_date: Optional[str] = None
    is_recomputing: bool = False

class InsightRead(BaseModel):
    insight_id: str
    run_id: str
    insight_type: str
    severity: str
    observation: str
    metric: Dict[str, Any]
    evidence: Dict[str, Any]
    action: str
    assumptions: List[str]
    created_at: datetime

    class Config:
        from_attributes = True

class AlertRead(BaseModel):
    alert_id: str
    deduplication_key: str
    insight_id: Optional[str] = None
    title: str
    message: str
    severity: str
    status: str
    resolution_notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class AlertUpdateRequest(BaseModel):
    status: str # ACKNOWLEDGED, RESOLVED
    resolution_notes: Optional[str] = None

class AuditEventRead(BaseModel):
    event_id: str
    actor: str
    action: str
    entity_type: str
    entity_id: str
    details: Dict[str, Any]
    timestamp: datetime

    class Config:
        from_attributes = True
