import datetime
from sqlalchemy import Column, String, Numeric, DateTime, ForeignKey, Integer, Text, Boolean
from sqlalchemy.orm import relationship
from app.database import Base

class Transaction(Base):
    __tablename__ = "transactions"
    
    transaction_id = Column(String(64), primary_key=True, index=True)
    user_id = Column(String(64), ForeignKey("users.user_id"), nullable=False, index=True)
    account_id = Column(String(64), ForeignKey("accounts.account_id"), nullable=False, index=True)
    date = Column(String(10), nullable=False, index=True) # YYYY-MM-DD
    description = Column(String(255), default="", nullable=False)
    amount = Column(Numeric(18, 2), nullable=False)
    direction = Column(String(8), nullable=False) # DEBIT, CREDIT
    currency = Column(String(3), default="INR", nullable=False)
    transaction_type = Column(String(32), default="EXPENSE", nullable=False) # INCOME, EXPENSE, TRANSFER, CREDIT_CARD_REPAYMENT, REFUND
    category = Column(String(64), default="Unclassified", nullable=False, index=True)
    category_source = Column(String(32), default="unclassified", nullable=False) # user_override, merchant_rule, ml_classifier, unclassified
    classifier_score = Column(Numeric(5, 4), nullable=True)
    reference = Column(String(128), nullable=True, index=True)
    review_state = Column(String(32), default="APPROVED", nullable=False, index=True) # APPROVED, NEEDS_REVIEW, EXCLUDED
    is_duplicate_candidate = Column(Boolean, default=False, nullable=False)
    transfer_linked_transaction_id = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    sources = relationship("TransactionSource", back_populates="transaction", cascade="all, delete-orphan")

class TransactionSource(Base):
    __tablename__ = "transaction_sources"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    transaction_id = Column(String(64), ForeignKey("transactions.transaction_id"), nullable=False, index=True)
    upload_id = Column(String(64), ForeignKey("uploads.upload_id"), nullable=True, index=True)
    row_number = Column(Integer, nullable=True)
    page_number = Column(Integer, nullable=True)
    raw_text = Column(Text, nullable=False)
    parse_status = Column(String(32), default="SUCCESS", nullable=False)

    transaction = relationship("Transaction", back_populates="sources")

class CategoryOverride(Base):
    __tablename__ = "category_overrides"
    
    override_id = Column(String(64), primary_key=True, index=True)
    user_id = Column(String(64), ForeignKey("users.user_id"), nullable=False, index=True)
    pattern_or_tx_id = Column(String(128), nullable=False, index=True)
    override_type = Column(String(32), default="MERCHANT", nullable=False) # TRANSACTION, MERCHANT
    category = Column(String(64), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
