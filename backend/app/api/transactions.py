import math
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.transaction import TransactionRead, TransactionUpdate, PaginatedTransactions, SourceLineage
from app.services.ledger_service import ledger_service
from app.orchestrator import orchestrator
from app.api.deps import get_current_user

router = APIRouter(prefix="/v1", tags=["Ledger & Transactions"])

@router.get("/transactions", response_model=PaginatedTransactions)
def list_transactions(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    month: Optional[str] = Query(None), # YYYY-MM
    account_id: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    review_state: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    items, total = ledger_service.get_transactions(
        db=db,
        user_id=current_user.user_id,
        page=page,
        page_size=page_size,
        month=month,
        account_id=account_id,
        category=category,
        review_state=review_state,
        search=search
    )

    serialized_items = []
    for it in items:
        sources_list = [
            SourceLineage(
                upload_id=s.upload_id,
                row_number=s.row_number,
                page_number=s.page_number,
                raw_text=s.raw_text
            ) for s in it.sources
        ]
        serialized_items.append(
            TransactionRead(
                transaction_id=it.transaction_id,
                user_id=it.user_id,
                account_id=it.account_id,
                date=it.date,
                description=it.description,
                amount=it.amount,
                direction=it.direction,
                currency=it.currency,
                transaction_type=it.transaction_type,
                category=it.category,
                category_source=it.category_source,
                classifier_score=it.classifier_score,
                reference=it.reference,
                review_state=it.review_state,
                is_duplicate_candidate=it.is_duplicate_candidate,
                transfer_linked_transaction_id=it.transfer_linked_transaction_id,
                created_at=it.created_at,
                sources=sources_list
            )
        )

    total_pages = math.ceil(total / page_size) if total > 0 else 1

    return PaginatedTransactions(
        items=serialized_items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )

@router.patch("/transactions/{transaction_id}", response_model=TransactionRead)
def update_transaction(
    transaction_id: str,
    update: TransactionUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    updated_tx = None
    if update.category:
        updated_tx = ledger_service.update_category(
            db=db,
            user_id=current_user.user_id,
            transaction_id=transaction_id,
            new_category=update.category,
            apply_to_merchant=update.apply_to_merchant or False
        )

    if not updated_tx:
        raise HTTPException(status_code=404, detail="Transaction not found or not owned by user.")

    # Re-run pipeline to update dependent insights and budgets
    orchestrator.run_full_pipeline(db, current_user.user_id, trigger_reason="TRANSACTION_CATEGORY_UPDATE")

    sources_list = [
        SourceLineage(
            upload_id=s.upload_id,
            row_number=s.row_number,
            page_number=s.page_number,
            raw_text=s.raw_text
        ) for s in updated_tx.sources
    ]

    return TransactionRead(
        transaction_id=updated_tx.transaction_id,
        user_id=updated_tx.user_id,
        account_id=updated_tx.account_id,
        date=updated_tx.date,
        description=updated_tx.description,
        amount=updated_tx.amount,
        direction=updated_tx.direction,
        currency=updated_tx.currency,
        transaction_type=updated_tx.transaction_type,
        category=updated_tx.category,
        category_source=updated_tx.category_source,
        classifier_score=updated_tx.classifier_score,
        reference=updated_tx.reference,
        review_state=updated_tx.review_state,
        is_duplicate_candidate=updated_tx.is_duplicate_candidate,
        transfer_linked_transaction_id=updated_tx.transfer_linked_transaction_id,
        created_at=updated_tx.created_at,
        sources=sources_list
    )

@router.get("/exports/transactions.csv")
def export_transactions(
    month: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    csv_data = ledger_service.export_csv(db=db, user_id=current_user.user_id, month=month)
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=transactions_{month or 'all'}.csv"}
    )
