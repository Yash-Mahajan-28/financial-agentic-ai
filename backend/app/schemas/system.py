from typing import List, Dict, Optional, Any
from pydantic import BaseModel
from datetime import datetime

class ServiceHealthItem(BaseModel):
    name: str
    status: str # HEALTHY, DEGRADED, UNAVAILABLE, UNKNOWN
    latency_ms: Optional[float] = None
    details: Optional[str] = None

class SystemStatusRead(BaseModel):
    environment: str
    active_data_version: str
    overall_health: str # HEALTHY, DEGRADED, UNHEALTHY
    services: Dict[str, ServiceHealthItem]
    worker_heartbeat_age_seconds: Optional[int] = None
    scheduler_heartbeat_age_seconds: Optional[int] = None
    llm_provider: str
    timestamp: datetime

class AgentRunRecord(BaseModel):
    run_id: str
    data_version: str
    status: str
    stages_executed: List[str]
    total_duration_ms: float
    computed_at: datetime
