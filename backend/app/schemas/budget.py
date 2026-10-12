from typing import Dict, List, Optional
from pydantic import BaseModel
from decimal import Decimal

class BudgetRead(BaseModel):
    month: str # YYYY-MM
    limits: Dict[str, Decimal]

class BudgetUpdateRequest(BaseModel):
    month: str
    limits: Dict[str, Decimal]

class BudgetUtilizationItem(BaseModel):
    category: str
    spent: Decimal
    limit: Decimal
    remaining: Decimal
    utilization_pct: Decimal
    status: str # NORMAL, WARNING, EXCEEDED

class FiftyThirtyTwentyTemplate(BaseModel):
    total_income: Decimal
    needs_limit: Decimal     # 50%
    wants_limit: Decimal     # 30%
    savings_target: Decimal  # 20%
    breakdown: Dict[str, Decimal]
