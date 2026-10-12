from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.advisor import ChatRequest, ChatResponse
from app.agents import advisor_agent
from app.api.deps import get_current_user

router = APIRouter(prefix="/v1/advisor", tags=["Conversational Financial Advisor"])

@router.post("/chat", response_model=ChatResponse)
def chat_with_advisor(
    req: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    history_dicts = [{"role": m.role, "content": m.content} for m in req.conversation_history] if req.conversation_history else []
    
    res = advisor_agent.chat(
        db=db,
        user_id=current_user.user_id,
        query=req.message,
        history=history_dicts
    )

    return ChatResponse(
        answer=res["answer"],
        tool_calls=res["tool_calls"],
        cited_insights=res["cited_insights"],
        cited_transactions=res["cited_transactions"],
        suggested_follow_ups=res["suggested_follow_ups"]
    )
