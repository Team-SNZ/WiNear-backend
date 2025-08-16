from typing import Optional

from pydantic import BaseModel


class ChatStartRequest(BaseModel):
    user_id: str


class ReplyRequest(BaseModel):
    message: str
    session_id: str


class ChatResponse(BaseModel):
    session_id: Optional[str] = None
    assistant: str
    finished: bool
    draft_summary: Optional[str] = None
    final_summary: Optional[str] = None


class ChatEndRequest(BaseModel):
    session_id: str


