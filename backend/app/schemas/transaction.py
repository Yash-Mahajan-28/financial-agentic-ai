from typing import Optional, List
from pydantic import BaseModel
from decimal import Decimal
from datetime import datetime

class SourceLineage(BaseModel):
    upload_id: Optional[str] = None
    row_number: Optional[int] = None
    page_number: Optional[int] = None
    raw_text: str

class TransactionRead(BaseModel):
    transaction_id: str
    user_id: str
    account_id: str
    date: str
    description: str
    amount: Decimal
    direction: str
    currency: str
    transaction_type: str
    category: str
    category_source: str
    classifier_score: Optional[Decimal] = None
    reference: Optional[str] = None
    review_state: str
    is_duplicate_candidate: bool
    transfer_linked_transaction_id: Optional[str] = None
    created_at: datetime
    sources: Optional[List[SourceLineage]] = []

    class Config:
        from_attributes = True

class TransactionUpdate(BaseModel):
    category: Optional[str] = None
    transaction_type: Optional[str] = None
    review_state: Optional[str] = None
    apply_to_merchant: Optional[bool] = False
    transfer_linked_transaction_id: Optional[str] = None

class PaginatedTransactions(BaseModel):
    items: List[TransactionRead]
    total: int
    page: int
    page_size: int
    total_pages: int
