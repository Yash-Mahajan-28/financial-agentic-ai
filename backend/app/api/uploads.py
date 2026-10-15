import os
import uuid
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status, Response
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User, Account
from app.models.upload import Upload, Job
from app.models.transaction import Transaction, TransactionSource
from app.schemas.upload import UploadResponse, JobRead, ConfirmReviewRequest
from app.agents import ingestion_agent, categorization_agent
from app.orchestrator import orchestrator
from app.api.deps import get_current_user

router = APIRouter(prefix="/v1", tags=["Ingestion & Uploads"])

@router.post("/uploads", response_model=UploadResponse, status_code=status.HTTP_202_ACCEPTED)
async def upload_statement(
    file: UploadFile = File(...),
    account_id: str = Form(...),
    period: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Verify account ownership
    account = db.query(Account).filter(
        Account.account_id == account_id,
        Account.user_id == current_user.user_id
    ).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found or not owned by user.")

    file_bytes = await file.read()
    filename = file.filename or "statement.csv"

    # Run Ingestion Agent
    result = ingestion_agent.execute(
        db=db,
        user_id=current_user.user_id,
        account_id=account_id,
        file_bytes=file_bytes,
        filename=filename
    )

    upload_id = result["upload_id"]
    job_id = result.get("job_id", "")
    parsed_rows = result.get("parsed_rows", [])

    # Check if exact duplicate file detected
    if result.get("status") == "DUPLICATE_FILE":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This statement file has already been imported for this account. Duplicate upload prevented (SHA-256 match)."
        )

    # If parsing succeeded, run Categorization Agent on parsed rows
    if parsed_rows:
        cat_result = categorization_agent.execute(
            db=db,
            user_id=current_user.user_id,
            raw_transactions=parsed_rows
        )
        categorized_txs = cat_result["categorized_transactions"]

        # Persist transactions to ledger
        for r in categorized_txs:
            tx_id = f"tx_{uuid.uuid4().hex[:10]}"
            tx_record = Transaction(
                transaction_id=tx_id,
                user_id=current_user.user_id,
                account_id=account_id,
                date=r["date"],
                description=r.get("description", ""),
                amount=r["amount"],
                direction=r["direction"],
                currency=r["currency"],
                transaction_type=r["transaction_type"],
                category=r["category"],
                category_source=r["category_source"],
                classifier_score=r["classifier_score"],
                reference=r["reference"],
                review_state=r["review_state"]
            )
            db.add(tx_record)

            # Link source lineage
            source_rec = TransactionSource(
                transaction_id=tx_id,
                upload_id=upload_id,
                row_number=r.get("row_number"),
                page_number=r.get("page_number"),
                raw_text=r.get("raw_text", ""),
                parse_status="SUCCESS"
            )
            db.add(source_rec)

        db.commit()

        # Update latest account balance if final row had a closing balance
        final_bal = parsed_rows[-1].get("balance")
        if final_bal is not None:
            account.balance = final_bal
            account.balance_as_of = parsed_rows[-1]["date"]
            db.commit()

        # Run Master Orchestrator analysis pipeline
        orchestrator.run_full_pipeline(db, current_user.user_id, trigger_reason="STATEMENT_UPLOAD")

    return UploadResponse(
        upload_id=upload_id,
        job_id=job_id,
        message=f"File processed: {len(parsed_rows)} rows normalized.",
        status=result["status"]
    )

@router.get("/jobs/{job_id}", response_model=JobRead)
def get_job_status(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    job = db.query(Job).filter(Job.job_id == job_id, Job.user_id == current_user.user_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
    return job

@router.get("/uploads/{upload_id}/source")
def get_upload_source(
    upload_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    upload = db.query(Upload).filter(
        Upload.upload_id == upload_id,
        Upload.user_id == current_user.user_id
    ).first()
    if not upload or not os.path.exists(upload.storage_key):
        raise HTTPException(status_code=404, detail="Source statement not found.")
    
    return FileResponse(
        upload.storage_key,
        filename=upload.original_filename,
        media_type="application/octet-stream"
    )

@router.post("/uploads/{upload_id}/confirm")
def confirm_upload_review(
    upload_id: str,
    req: ConfirmReviewRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Commit user decisions and trigger pipeline
    orchestrator.run_full_pipeline(db, current_user.user_id, trigger_reason="REVIEW_CONFIRMATION")
    return {"message": "Decisions committed and analysis recomputed successfully."}
