import os
import hashlib
import uuid
from typing import Dict, Any, List
from sqlalchemy.orm import Session

from app.agents.base import BaseAgent
from app.models.upload import Upload, Job
from app.parsers.csv_parser import csv_parser
from app.parsers.pdf_parser import pdf_parser
from app.config import settings

class IngestionAgent(BaseAgent):
    def __init__(self):
        super().__init__("IngestionAgent")

    def run(self, db: Session, user_id: str, account_id: str, file_bytes: bytes, filename: str) -> Dict[str, Any]:
        # 1. Enforce file size limit (10 MB max as per spec Page 7)
        if len(file_bytes) > 10 * 1024 * 1024:
            raise ValueError("File exceeds maximum allowed size of 10 MB.")

        # 2. Compute SHA-256 digest
        hasher = hashlib.sha256()
        hasher.update(file_bytes)
        content_hash = hasher.hexdigest()

        # 3. Check for exact repeated file upload
        existing_upload = db.query(Upload).filter(
            Upload.user_id == user_id,
            Upload.account_id == account_id,
            Upload.content_hash == content_hash
        ).first()

        if existing_upload:
            return {
                "status": "DUPLICATE_FILE",
                "message": "This statement file has already been imported for this account.",
                "upload_id": existing_upload.upload_id,
                "rows": [],
                "errors": [{"error": "Exact repeat file detected for account.", "code": "REPEAT_FILE"}]
            }

        # 4. Generate private storage key
        upload_id = f"up_{uuid.uuid4().hex[:12]}"
        ext = os.path.splitext(filename)[1].lower()
        storage_filename = f"{upload_id}{ext}"
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        storage_path = os.path.join(settings.UPLOAD_DIR, storage_filename)
        with open(storage_path, "wb") as f:
            f.write(file_bytes)

        # 5. Parse content
        parsed_rows = []
        parse_errors = []
        if ext == ".csv":
            content_str = file_bytes.decode("utf-8", errors="replace")
            parsed_rows, parse_errors = csv_parser.parse(content_str)
        elif ext == ".pdf":
            parsed_rows, parse_errors = pdf_parser.parse(file_bytes)
        else:
            parse_errors.append({"error": f"Unsupported file extension: '{ext}'. Upload CSV or PDF.", "code": "UNSUPPORTED_FORMAT"})

        # 6. Create Upload entity
        upload_record = Upload(
            upload_id=upload_id,
            user_id=user_id,
            account_id=account_id,
            content_hash=content_hash,
            storage_key=storage_path,
            original_filename=filename,
            parser_version="v1.0"
        )
        db.add(upload_record)

        # 7. Create Job entity
        job_id = f"job_{uuid.uuid4().hex[:12]}"
        status = "NEEDS_REVIEW" if parse_errors or any(r.get("needs_review") for r in parsed_rows) else "SUCCEEDED"
        if not parsed_rows and parse_errors:
            status = "FAILED"

        job_record = Job(
            job_id=job_id,
            upload_id=upload_id,
            user_id=user_id,
            job_type="STATEMENT_INGESTION",
            status=status,
            stage="PARSING_COMPLETED",
            total_rows=len(parsed_rows) + len(parse_errors),
            processed_rows=len(parsed_rows),
            error_count=len(parse_errors),
            review_errors=parse_errors,
            error_code=parse_errors[0]["code"] if parse_errors else None
        )
        db.add(job_record)
        db.commit()
        db.refresh(upload_record)
        db.refresh(job_record)

        return {
            "upload_id": upload_id,
            "job_id": job_id,
            "status": status,
            "total_parsed": len(parsed_rows),
            "errors": parse_errors,
            "parsed_rows": parsed_rows
        }

ingestion_agent = IngestionAgent()
