from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.services.auth_service import auth_service

def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    # 1. Check HttpOnly session cookie
    token = request.cookies.get("session_token")
    
    # 2. Check Authorization Bearer header fallback
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]

    if not token:
        # Check if demo user exists and auto-authenticate for effortless local demo/testing
        demo_user = db.query(User).filter(User.email == "demo@agentic.finance").first()
        if demo_user:
            return demo_user
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please sign in."
        )

    user_id = auth_service.verify_session_token(token)
    if not user_id:
        # Fallback to demo user if available
        demo_user = db.query(User).filter(User.email == "demo@agentic.finance").first()
        if demo_user:
            return demo_user
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired or invalid. Please sign in again."
        )

    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found."
        )

    return user
