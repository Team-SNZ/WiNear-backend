from __future__ import annotations

import uuid
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Query
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging
from ..schemas.chat import ChatResponse, ReplyRequest, ChatStartRequest, ChatEndRequest
from ..dependencies.db import get_db, get_redis
from ..repositories.chat_session_repository import get_session, create_session, update_session, delete_session

from ..services.chat_prompts import (
    next_question,
    make_draft_summary,
    make_final_summary,
)
from ..repositories.user_summary_repository import upsert_user_summary
from ..services.ai_client import request_recommendations


_logger = logging.getLogger("uvicorn.info")


router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/start", response_model=ChatResponse, summary="새 채팅 세션 등록")
async def start_chat(req: ChatStartRequest, redis = Depends(get_redis)) -> ChatResponse:
    session_id = str(uuid.uuid4())
    session_data: Dict[str, Any] = {
        "user_id": req.user_id,
        "messages": [],
        "count": 0,
        "draft_summary": None,
        "final_summary": None,
    }
    # Redis 세션 저장 후, 다음 질문 생성 시 메모리/Redis 동기화 유지
    await create_session(redis, session_id, session_data)
    assistant = await next_question(session_data) 
    await update_session(redis, session_id, session_data)  
    return ChatResponse(session_id=session_id, assistant=assistant, finished=False)


# TODO: 채팅 세션 종료 시, 세션 데이터 삭제 필요
# TODO: 5번 이내 채팅 종료 시, 채팅 세션 데이터 요약 후 다음 페이지로 이동 필요
@router.post("/reply", response_model=ChatResponse, summary="채팅 세션에 사용자 답변 등록")
async def user_reply(
    req: ReplyRequest,
    db: AsyncIOMotorDatabase = Depends(get_db),
    redis = Depends(get_redis),
    return_draft: bool = Query(default=False, description="true면 요약 초안을 응답합니다 (대화는 종료되지 않음)"),
) -> ChatResponse:
    session_id = req.session_id
    st = await get_session(redis, session_id)
    if st is None:
        raise HTTPException(status_code=404, detail="세션이 잘못되었거나 존재하지 않습니다.")
    st["messages"].append({"role": "user", "content": req.message})
    st["count"] += 1

    if return_draft and st.get("draft_summary") is None and st.get("final_summary") is None:
        st["draft_summary"] = await make_draft_summary(st)
        assistant_text = st["draft_summary"]
        await update_session(redis, session_id, st)
        return ChatResponse(
            session_id=session_id,
            assistant=assistant_text,
            finished=False,
            draft_summary=st["draft_summary"],
        )

    assistant = await next_question(st)
    await update_session(redis, session_id, st)
    return ChatResponse(assistant=assistant, finished=False)


@router.post("/end", response_model=ChatResponse, summary="채팅 종료 및 요약 확정")
async def end_chat(req: ChatEndRequest, db: AsyncIOMotorDatabase = Depends(get_db), redis = Depends(get_redis)) -> ChatResponse:
    session_id = req.session_id
    st = await get_session(redis, session_id)
    if st is None:
        raise HTTPException(status_code=404, detail="세션이 잘못되었거나 존재하지 않습니다.")
    if st.get("final_summary") is None:
    # 요약 저장이 완료되었으므로 외부 AI 백엔드에 추천 요청
    ai_payload = {
        "user_id": st["user_id"],
        "summary": st["final_summary"],
        # 필요한 추가 컨텍스트가 있다면 여기에 포함
    }
    ai_response = await request_recommendations(ai_payload)

    assistant = await _next_question(st)
    return ChatResponse(assistant=assistant, finished=False)


