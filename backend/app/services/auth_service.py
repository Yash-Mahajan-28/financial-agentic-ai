import os
import hashlib
import secrets
import base64
import json
import time
from typing import Optional, Dict
from sqlalchemy.orm import Session
from app.models.user import User
from app.config import settings

class AuthService:
    def hash_password(self, password: str, salt: Optional[bytes] = None) -> str:
        if salt is None:
            salt = secrets.token_bytes(16)
        # PBKDF2-HMAC-SHA256 with 100,000 iterations
        key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100000)
        return f"{base64.b64encode(salt).decode('ascii')}${base64.b64encode(key).decode('ascii')}"

    def verify_password(self, password: str, stored_hash: str) -> bool:
        try:
            parts = stored_hash.split("$")
            if len(parts) != 2:
                return False
            salt = base64.b64decode(parts[0].encode("ascii"))
            expected_key = base64.b64decode(parts[1].encode("ascii"))
            computed_key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100000)
            return secrets.compare_digest(expected_key, computed_key)
        except Exception:
            return False

    def create_session_token(self, user_id: str) -> str:
        payload = {
            "user_id": user_id,
            "created_at": int(time.time()),
            "nonce": secrets.token_hex(8)
        }
        raw_json = json.dumps(payload).encode("utf-8")
        token_data = base64.urlsafe_b64encode(raw_json).decode("ascii")
        signature = hashlib.sha256(f"{token_data}:{settings.SESSION_SECRET}".encode("utf-8")).hexdigest()
        return f"{token_data}.{signature}"

    def verify_session_token(self, token: str) -> Optional[str]:
        try:
            parts = token.split(".")
            if len(parts) != 2:
                return None
            token_data, signature = parts[0], parts[1]
            expected_signature = hashlib.sha256(f"{token_data}:{settings.SESSION_SECRET}".encode("utf-8")).hexdigest()
            if not secrets.compare_digest(signature, expected_signature):
                return None
            raw_json = base64.urlsafe_b64decode(token_data.encode("ascii")).decode("utf-8")
            payload = json.loads(raw_json)
            # Check expiry
            if time.time() - payload.get("created_at", 0) > settings.SESSION_MAX_AGE_SECONDS:
                return None
            return payload.get("user_id")
        except Exception:
            return None

auth_service = AuthService()
