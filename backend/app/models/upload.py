import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Text, JSON
from app.database import Base

class Upload(Base):
    __tablename__ = "uploads"
    
    upload_id = Column(String(64), primary_key=True, index=True)
    user_id = Column(String(64), ForeignKey("users.user_id"), nullable=False, index=True)
    account_id = Column(String(64), ForeignKey("accounts.account_id"), nullable=False, index=True)
    content_hash = Column(String(64), nullable=False, index=True) # SHA-256
    storage_key = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    parser_version = Column(String(32), default="v1.0", nullable=False)
    period = Column(String(32), nullable=True) # e.g. "2026-01 to 2026-03"
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

class Job(Base):
    __tablename__ = "jobs"
    
    job_id = Column(String(64), primary_key=True, index=True)
    upload_id = Column(String(64), ForeignKey("uploads.upload_id"), nullable=True, index=True)
    user_id = Column(String(64), ForeignKey("users.user_id"), nullable=False, index=True)
    job_type = Column(String(32), default="IMPORT_AND_ANALYZE", nullable=False)
    status = Column(String(32), default="QUEUED", nullable=False, index=True) # QUEUED, RUNNING, NEEDS_REVIEW, SUCCEEDED, FAILED
    stage = Column(String(64), default="INIT", nullable=False)
    total_rows = Column(Integer, default=0, nullable=False)
    processed_rows = Column(Integer, default=0, nullable=False)
    error_count = Column(Integer, default=0, nullable=False)
    review_errors = Column(JSON, default=list, nullable=False)
    error_code = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow, nullable=False)
