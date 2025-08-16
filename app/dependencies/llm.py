from langchain_openai import ChatOpenAI
from ..core.config import get_settings


def get_llm() -> ChatOpenAI:
    settings = get_settings()
    return ChatOpenAI(model=settings.openai_model, temperature=0.3, api_key=settings.openai_api_key)
