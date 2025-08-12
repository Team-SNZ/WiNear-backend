from __future__ import annotations

import uuid
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, Request
from langchain_openai import ChatOpenAI
from motor.motor_asyncio import AsyncIOMotorDatabase

from ..core.config import get_settings
from ..schemas.chat import ChatResponse, ReplyRequest, StartRequest


router = APIRouter(prefix="/chat", tags=["chat"])


# 세션 저장소 (실 서비스라면 Redis/DB 권장)
sessions: Dict[str, Dict[str, Any]] = {}


QUESTION_THEMES: List[str] = [
    "여행 중 최악의 경험과 그 이유",
    "이번 여행에서 이것만큼은 꼭 있으면 하는 것",
    "같이 여행을 가고 싶은 사람의 특징",
    "이번 여행에서 가장 기대하는 것",
    "당신에게 이번 여행이 가져다줄 삶의 의미",
]


def get_db(request: Request) -> AsyncIOMotorDatabase:
    db = getattr(request.app.state, "mongo_db", None)
    if db is None:
        raise HTTPException(status_code=500, detail="Database not initialized")
    return db


def build_prompt(context: str, themes: List[str]) -> str:
    themes_text = "\n".join([f"- {theme}" for theme in themes])
    return (
        "당신은 사용자의 구체적인 여행 성향을 파악하는 전문 상담가입니다.\n\n"
        "<목표>\n"
        "아래 5가지 주제에 대해 사용자의 답변을 모두 얻어야 합니다:\n"
        f"{themes_text}\n\n"
        "<현재 대화 상황>\n"
        f"{context}\n\n"
        "<지침>\n"
        "1. 위 대화를 분석해서 어떤 주제들이 이미 다뤄졌는지 파악하세요.\n"
        "2. 대화가 없다면, \"더 구체적인 당신의 여행 성향을 파악하기 위해 몇 가지 질문을 준비했습니다. 생각나는대로 편하게 답변해주세요!\" 와 함께 임의로 한 가지 주제를 정해서 질문을 시작하세요.\n"
        "3. 아직 다루지 않은 주제 중에서 가장 자연스럽게 이어갈 수 있는 하나를 선택하세요.\n"
        "4. 사용자의 이전 답변에 공감하며 자연스럽게 다음 질문으로 넘어가세요.\n\n"
        "상담가의 답변: "
    )


def _build_transcript(messages: List[Dict[str, str]]) -> str:
    if not messages:
        return ""
    return "\n".join([f"{m['role']}: {m['content']}" for m in messages])


def _get_llm() -> ChatOpenAI:
    settings = get_settings()
    return ChatOpenAI(model=settings.openai_model, temperature=0.3, api_key=settings.openai_api_key)


async def _next_question(state: Dict[str, Any]) -> str:
    transcript = _build_transcript(state["messages"])  # type: ignore[index]
    prompt = build_prompt(transcript, QUESTION_THEMES)
    llm = _get_llm()
    ai_message = await llm.ainvoke(prompt)
    assistant = ai_message.content.strip()
    state["messages"].append({"role": "assistant", "content": assistant})
    return assistant


async def _make_draft_summary(state: Dict[str, Any]) -> str:
    transcript = _build_transcript(state["messages"])  # type: ignore[index]
    sys_prompt = (
        "다음 대화는 사용자의 여행 성향을 파악하기 위한 Q&A입니다.\n"
        "먼저 사용자의 마지막 답변에 공감하세요.\n"
        "그 후 지금까지의 사용자의 답변을 한 단락으로 누락 없이 정리한 후, 사용자에게 추가하고 싶은 내용이 있는지 피드백을 요청하세요."
    )
    llm = _get_llm()
    ai_message = await llm.ainvoke(f"{sys_prompt}\n\n대화:\n{transcript}")
    return ai_message.content.strip()


async def _make_final_summary(state: Dict[str, Any], db: AsyncIOMotorDatabase) -> str:
    transcript = _build_transcript(state["messages"])  # type: ignore[index]
    sys_prompt = (
        "다음 대화는 사용자의 여행 성향을 파악하기 위한 Q&A입니다.\n"
        "사용자의 답변을 한 단락으로 누락 없이 정리하세요."
    )
    llm = _get_llm()
    ai_message = await llm.ainvoke(f"{sys_prompt}\n\n대화:\n{transcript}")
    final_text = ai_message.content.strip()
    await db["user_summary"].update_one(
        {"ID": state["user_id"]},  # type: ignore[index]
        {"$set": {"Summary": final_text}},
        upsert=True,
    )
    return final_text


@router.post("/start", response_model=ChatResponse)
async def start_chat(req: StartRequest) -> ChatResponse:
    session_id = str(uuid.uuid4())
    sessions[session_id] = {
        "user_id": req.user_id,
        "messages": [],
        "count": 0,
        "draft_summary": None,
        "final_summary": None,
    }
    assistant = await _next_question(sessions[session_id])
    return ChatResponse(session_id=session_id, assistant=assistant, finished=False)


@router.post("/reply", response_model=ChatResponse)
async def user_reply(req: ReplyRequest, db: AsyncIOMotorDatabase = Depends(get_db)) -> ChatResponse:
    session_id = req.session_id
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="There is no session.")

    st = sessions[session_id]
    st["messages"].append({"role": "user", "content": req.message})
    st["count"] += 1

    if st["count"] >= 5 and st["draft_summary"] is None and st["final_summary"] is None:
        st["draft_summary"] = await _make_draft_summary(st)
        assistant_text = st["draft_summary"]
        return ChatResponse(
            session_id=session_id,
            assistant=assistant_text,
            finished=False,
            draft_summary=st["draft_summary"],
        )

    if st["count"] >= 5 and st["draft_summary"] is not None and st["final_summary"] is None:
        st["final_summary"] = await _make_final_summary(st, db)
        assistant_text = (
            "당신의 적극적인 답변 덕분에 여행 성향을 보다 깊이 이해할 수 있게 되었어요!\n"
            "이를 바탕으로 당신의 여행 메이트와 추천 여행지를 탐색해볼게요!"
        )
        return ChatResponse(
            session_id=session_id,
            assistant=assistant_text,
            finished=True,
            final_summary=st["final_summary"],
        )

    assistant = await _next_question(st)
    return ChatResponse(assistant=assistant, finished=False)


