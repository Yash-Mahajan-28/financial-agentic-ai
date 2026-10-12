import io
import csv
import uuid
import datetime
from decimal import Decimal
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models.transaction import Transaction, TransactionSource, CategoryOverride
from app.models.analysis import AuditEvent

class LedgerService:
    def get_transactions(
        self,
        db: Session,
        user_id: str,
        page: int = 1,
        page_size: int = 50,
        month: Optional[str] = None,
        account_id: Optional[str] = None,
        category: Optional[str] = None,
        search: Optional[str] = None,
        review_state: Optional[str] = None
    ) -> Tuple[List[Transaction], int]:
        query = db.query(Transaction).filter(Transaction.user_id == user_id)

        if month:
            query = query.filter(Transaction.date.startswith(month))
        if account_id:
            query = query.filter(Transaction.account_id == account_id)
        if category and category != "ALL":
            query = query.filter(Transaction.category == category)
        if review_state and review_state != "ALL":
            query = query.filter(Transaction.review_state == review_state)
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    Transaction.description.ilike(search_term),
                    Transaction.reference.ilike(search_term),
                    Transaction.category.ilike(search_term)
                )
            )

        total = query.count()
        items = query.order_by(Transaction.date.desc(), Transaction.transaction_id.desc())\
                     .offset((page - 1) * page_size)\
                     .limit(page_size)\
                     .all()

        return items, total

    def update_category(
        self,
        db: Session,
        user_id: str,
        transaction_id: str,
        new_category: str,
        apply_to_merchant: bool = False
    ) -> Optional[Transaction]:
        tx = db.query(Transaction).filter(
            Transaction.transaction_id == transaction_id,
            Transaction.user_id == user_id
        ).first()

        if not tx:
            return None

        old_category = tx.category
        tx.category = new_category
        tx.category_source = "user_override"
        tx.review_state = "APPROVED"

        # Record override
        override_type = "MERCHANT" if apply_to_merchant else "TRANSACTION"
        pattern = tx.description.split()[0].upper() if apply_to_merchant else (tx.reference or tx.transaction_id)
        
        override = CategoryOverride(
            override_id=f"ovr_{uuid.uuid4().hex[:8]}",
            user_id=user_id,
            pattern_or_tx_id=pattern,
            override_type=override_type,
            category=new_category
        )
        db.add(override)

        # Audit event
        audit = AuditEvent(
            event_id=f"aud_{uuid.uuid4().hex[:8]}",
            user_id=user_id,
            actor="user",
            action="CATEGORY_OVERRIDE",
            entity_type="Transaction",
            entity_id=transaction_id,
            details={"old_category": old_category, "new_category": new_category, "apply_to_merchant": apply_to_merchant}
        )
        db.add(audit)
        db.commit()
        db.refresh(tx)
        return tx

    def export_csv(self, db: Session, user_id: str, month: Optional[str] = None) -> str:
        """Export ledger with CSV formula injection protection (spec page 14, 23)."""
        query = db.query(Transaction).filter(
            Transaction.user_id == user_id,
            Transaction.review_state == "APPROVED"
        )
        if month:
            query = query.filter(Transaction.date.startswith(month))
        
        txs = query.order_by(Transaction.date.asc()).all()

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Date", "Description", "Amount", "Direction", "Currency", "Category", "Type", "Reference"])

        for t in txs:
            # Escape formula injection: prefix with single quote if starts with =, +, -, @
            desc_safe = t.description
            if desc_safe and desc_safe[0] in ["=", "+", "-", "@", "\t", "\r"]:
                desc_safe = f"'{desc_safe}"
            ref_safe = t.reference or ""
            if ref_safe and ref_safe[0] in ["=", "+", "-", "@", "\t", "\r"]:
                ref_safe = f"'{ref_safe}"

            writer.writerow([
                t.date,
                desc_safe,
                f"{t.amount:.2f}",
                t.direction,
                t.currency,
                t.category,
                t.transaction_type,
                ref_safe
            ])

        return output.getvalue()

ledger_service = LedgerService()
