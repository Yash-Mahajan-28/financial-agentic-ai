import io
import re
from decimal import Decimal, InvalidOperation
from typing import List, Dict, Tuple, Any

class PDFStatementParser:
    def parse(self, pdf_bytes: bytes) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        valid_rows = []
        errors = []
        
        extracted_text = ""
        page_texts = []
        
        try:
            import pypdf
            reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
            for p_num, page in enumerate(reader.pages, start=1):
                t = page.extract_text() or ""
                page_texts.append((p_num, t))
                extracted_text += t
        except Exception:
            # Fallback pure-python basic stream extraction
            raw = pdf_bytes.decode("latin-1", errors="ignore")
            # Look for stream chunks
            text_chunks = re.findall(r"\((.*?)\)\s*'", raw)
            extracted_text = "\n".join(text_chunks)
            page_texts.append((1, extracted_text))

        if not extracted_text.strip():
            return [], [{
                "row": 0,
                "error": "Scanned or non-extractable PDF document. OCR processing required.",
                "code": "OCR_REQUIRED"
            }]

        # Regex for transaction line:
        # e.g. 2026-03-05  MONTHLY SALARY CREDIT TECHCORP LTD  50000.00  CREDIT  SAL1036  60500.00
        line_pattern = re.compile(
            r"^(\d{4}-\d{2}-\d{2})\s+(.+?)\s+([\d,]+\.\d{2})\s+(DEBIT|CREDIT)\s+(\S+)(?:\s+([\d,]+\.\d{2}))?$",
            re.MULTILINE
        )

        for page_num, p_text in page_texts:
            for row_idx, line in enumerate(p_text.splitlines(), start=1):
                clean_line = line.strip()
                if not clean_line or clean_line.startswith("---") or clean_line.startswith("Date "):
                    continue

                match = line_pattern.match(clean_line)
                if match:
                    d_str, desc, amt_str, direction, ref, bal_str = match.groups()
                    try:
                        amt = Decimal(amt_str.replace(",", ""))
                        bal = Decimal(bal_str.replace(",", "")) if bal_str else None
                        valid_rows.append({
                            "row_number": row_idx,
                            "page_number": page_num,
                            "date": d_str,
                            "description": desc.strip(),
                            "amount": amt,
                            "direction": direction,
                            "currency": "INR",
                            "reference": ref,
                            "balance": bal,
                            "raw_text": clean_line
                        })
                    except (InvalidOperation, TypeError) as e:
                        errors.append({
                            "row": row_idx,
                            "page": page_num,
                            "error": f"Invalid amount in PDF row: {e}",
                            "code": "INVALID_AMOUNT",
                            "raw": clean_line
                        })

        if not valid_rows and not errors:
            errors.append({
                "row": 0,
                "error": "Unsupported PDF statement layout. No recognized transaction lines detected.",
                "code": "UNSUPPORTED_LAYOUT"
            })

        return valid_rows, errors

pdf_parser = PDFStatementParser()
