import csv
import io
import re
from decimal import Decimal, InvalidOperation
from datetime import datetime
from typing import List, Dict, Tuple, Any

class CSVStatementParser:
    REQUIRED_COLUMNS = ["date", "description", "amount", "direction", "currency", "reference"]

    def parse(self, file_content: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        valid_rows = []
        errors = []
        
        reader = csv.DictReader(io.StringIO(file_content.strip()))
        headers = [h.strip().lower() for h in (reader.fieldnames or [])]
        
        # Check required columns
        for req in self.REQUIRED_COLUMNS:
            if req not in headers:
                return [], [{
                    "row": 0,
                    "error": f"Missing required column header: '{req}'",
                    "code": "MISSING_HEADER"
                }]

        prev_balance = None
        for row_idx, row in enumerate(reader, start=2): # Line 2 is first data row
            raw_text = ", ".join([f"{k}:{v}" for k, v in row.items()])
            date_str = (row.get("date") or "").strip()
            desc = (row.get("description") or "").strip()
            amt_str = (row.get("amount") or "").strip()
            direction = (row.get("direction") or "").strip().upper()
            curr = (row.get("currency") or "").strip().upper()
            ref = (row.get("reference") or "").strip()
            bal_str = (row.get("balance") or "").strip()

            # 1. Validate date
            if not date_str:
                errors.append({"row": row_idx, "error": "Empty transaction date", "code": "EMPTY_DATE", "raw": raw_text})
                continue
            
            # Require ISO 8601 YYYY-MM-DD
            if not re.match(r"^\d{4}-\d{2}-\d{2}$", date_str):
                errors.append({
                    "row": row_idx,
                    "error": f"Ambiguous or invalid date '{date_str}'. Strict ISO YYYY-MM-DD format required.",
                    "code": "INVALID_DATE_FORMAT",
                    "raw": raw_text
                })
                continue

            try:
                datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                errors.append({"row": row_idx, "error": f"Invalid calendar date '{date_str}'", "code": "INVALID_DATE", "raw": raw_text})
                continue

            # 2. Validate description
            if not desc:
                errors.append({"row": row_idx, "error": "Empty description", "code": "EMPTY_DESCRIPTION", "raw": raw_text})
                continue

            # 3. Validate direction
            if direction not in ["DEBIT", "CREDIT"]:
                errors.append({
                    "row": row_idx,
                    "error": f"Invalid direction '{direction}'. Must be DEBIT or CREDIT.",
                    "code": "INVALID_DIRECTION",
                    "raw": raw_text
                })
                continue

            # 4. Validate currency
            if curr != "INR":
                errors.append({
                    "row": row_idx,
                    "error": f"Unsupported currency '{curr}'. System operates in INR baseline.",
                    "code": "UNSUPPORTED_CURRENCY",
                    "raw": raw_text
                })
                continue

            # 5. Validate amount
            try:
                amt = Decimal(amt_str)
                if amt <= 0 or amt.is_nan() or amt.is_infinite():
                    errors.append({
                        "row": row_idx,
                        "error": f"Amount must be a strictly positive number, got '{amt_str}'",
                        "code": "NON_POSITIVE_AMOUNT",
                        "raw": raw_text
                    })
                    continue
            except (InvalidOperation, TypeError):
                errors.append({
                    "row": row_idx,
                    "error": f"Invalid numeric amount '{amt_str}'",
                    "code": "INVALID_AMOUNT",
                    "raw": raw_text
                })
                continue

            # 6. Balance reconciliation check
            balance_val = None
            if bal_str:
                try:
                    balance_val = Decimal(bal_str)
                    if prev_balance is not None:
                        expected_bal = prev_balance + amt if direction == "CREDIT" else prev_balance - amt
                        if abs(expected_bal - balance_val) > Decimal("0.01"):
                            errors.append({
                                "row": row_idx,
                                "error": f"Balance mismatch: Expected {expected_bal}, statement declares {balance_val}",
                                "code": "BALANCE_RECONCILIATION_WARNING",
                                "raw": raw_text
                            })
                    prev_balance = balance_val
                except (InvalidOperation, TypeError):
                    pass

            valid_rows.append({
                "row_number": row_idx,
                "date": date_str,
                "description": desc,
                "amount": amt,
                "direction": direction,
                "currency": curr,
                "reference": ref,
                "balance": balance_val,
                "raw_text": raw_text
            })

        return valid_rows, errors

csv_parser = CSVStatementParser()
