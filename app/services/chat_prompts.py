from __future__ import annotations

from typing import Dict, List, Any
from ..dependencies.llm import get_llm


QUESTION_THEMES: List[str] = [
    "여행 중 최악의 경험과 그 이유",
    "이번 여행에서 이것만큼은 꼭 있으면 하는 것",
    "같이 여행을 가고 싶은 사람의 특징",
    "이번 여행에서 가장 기대하는 것",
    "당신에게 이번 여행이 가져다줄 삶의 의미",
]

async def next_question(state: Dict[str, Any]) -> str:
    prompt = build_next_question_prompt(state["messages"])  # type: ignore[index]
    llm = get_llm()
    ai_message = await llm.ainvoke(prompt)
    assistant = ai_message.content.strip()
    state["messages"].append({"role": "assistant", "content": assistant})
    return assistant


async def make_draft_summary(state: Dict[str, Any]) -> str:
    llm = get_llm()
    ai_message = await llm.ainvoke(build_draft_summary_prompt(state["messages"]))  # type: ignore[index]
    return ai_message.content.strip()


async def make_final_summary(state: Dict[str, Any]) -> str:
    llm = get_llm()
    ai_message = await llm.ainvoke(build_final_summary_prompt(state["messages"]))  # type: ignore[index]
    final_text = ai_message.content.strip()
    return final_text

def build_transcript(messages: List[Dict[str, str]]) -> str:
    if not messages:
        return ""
    return "\n".join([f"{m['role']}: {m['content']}" for m in messages])


def build_next_question_prompt(messages: List[Dict[str, str]]) -> str:
    context = build_transcript(messages)
    themes_text = "\n".join([f"- {theme}" for theme in QUESTION_THEMES])
    return (
        "당신은 사용자의 구체적인 여행 성향을 파악하는 전문 상담가입니다.\n\n"
        "<목표>\n"
        "아래 5가지 주제에 대해 사용자의 답변을 모두 얻어야 합니다:\n"
        f"{themes_text}\n\n"
        "<현재 대화 상황>\n"
        f"{context}\n\n"
        "<지침>\n"
        "1. 위 대화를 분석해서 어떤 주제들이 이미 다뤄졌는지 파악하세요.\n"
        "2. 대화가 없다면, \"더 구체적인 당신의 여행 성향을 파악하기 위해 몇 가지 질문을 준비했습니다. 생각나는대로 편하게 답변해주세요!\" 와 비슷한 분위기로, 임의로 한 가지 주제를 정해서 질문을 시작하세요.\n"
        "3. 아직 다루지 않은 주제 중에서 가장 자연스럽게 이어갈 수 있는 하나를 선택하세요.\n"
        "4. 사용자의 이전 답변에 공감하며 자연스럽게 다음 질문으로 넘어가세요.\n\n"
        "상담가의 답변: "
    )


def build_draft_summary_prompt(messages: List[Dict[str, str]]) -> str:
    transcript = build_transcript(messages)
    sys_prompt = (
        "다음 대화는 사용자의 여행 성향을 파악하기 위한 Q&A입니다.\n"
        "먼저 사용자의 마지막 답변에 공감하세요.\n"
        "그 후 지금까지의 사용자의 답변을 한 단락으로 누락 없이 정리한 후, 사용자에게 추가하고 싶은 내용이 있는지 피드백을 요청하세요."
    )
    return f"{sys_prompt}\n\n대화:\n{transcript}"


def build_final_summary_prompt(messages: List[Dict[str, str]]) -> str:
    transcript = build_transcript(messages)
    sys_prompt = (
        "다음 대화는 사용자의 여행 성향을 파악하기 위한 Q&A입니다.\n"
        "사용자의 답변을 한 단락으로 누락 없이 정리하세요."
    )
    return f"{sys_prompt}\n\n대화:\n{transcript}"


