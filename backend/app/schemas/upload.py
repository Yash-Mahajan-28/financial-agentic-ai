from typing import Optional, List, Any
from pydantic import BaseModel
from datetime import datetime

class UploadResponse(BaseModel):
    upload_id: str
    job_id: str
    message: str
    status: str

class ReviewItem(BaseModel):
    row_or_tx_id: str
    date: str
    description: str
    amount: str
    direction: str
    proposed_category: str
    confidence_score: Optional[float] = None
    reason: str # e.g. "LOW_CONFIDENCE_SCORE", "POSSIBLE_DUPLICATE", "AMBIGUOUS_MERCHANT"

class JobRead(BaseModel):
    job_id: str
    upload_id: Optional[str] = None
    job_type: str
    status: str # QUEUED, RUNNING, NEEDS_REVIEW, SUCCEEDED, FAILED
    stage: str
    total_rows: int
    processed_rows: int
    error_count: int
    review_errors: List[Any]
    error_code: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ConfirmReviewRequest(BaseModel):
    approved_transactions: List[dict] # list of items with review decisions
