from typing import List, Optional, Dict, Any
from pydantic import BaseModel

class ToolCallRecord(BaseModel):
    tool_name: str
    arguments: Dict[str, Any]
    result: Any

class ChatMessage(BaseModel):
    role: str # user, assistant, system
    content: str
    tool_calls: Optional[List[ToolCallRecord]] = []
    cited_insights: Optional[List[str]] = []
    cited_transactions: Optional[List[str]] = []

class ChatRequest(BaseModel):
    message: str
    conversation_history: Optional[List[ChatMessage]] = []

class ChatResponse(BaseModel):
    answer: str
    tool_calls: List[ToolCallRecord] = []
    cited_insights: List[str] = []
    cited_transactions: List[str] = []
    suggested_follow_ups: List[str] = []
