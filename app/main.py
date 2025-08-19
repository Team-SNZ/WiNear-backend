from contextlib import asynccontextmanager
from datetime import datetime, timezone
import logging
from urllib.parse import urlparse, urlunparse

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.server_api import ServerApi
import redis.asyncio as aioredis

from .core.config import get_settings
from .routers.user_features import router as user_features_router
from .routers.chat import router as chat_router
from .routers.user_summary import router as user_summary_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    client_kwargs: dict[str, object] = {}
    if settings.mongodb_server_api:
        client_kwargs["server_api"] = ServerApi(settings.mongodb_server_api)
    client = AsyncIOMotorClient(settings.mongodb_uri, **client_kwargs)
    # 연결 핑 및 URI 로깅
    logger = logging.getLogger("uvicorn.error")

    def _mask_mongo_uri(uri: str) -> str:
        parsed = urlparse(uri)
        netloc = parsed.netloc
        if "@" in netloc:
            host_part = netloc.split("@", 1)[1]
            netloc = f"***:***@{host_part}"
        masked = urlunparse((parsed.scheme, netloc, parsed.path, parsed.params, parsed.query, parsed.fragment))
        return masked

    try:
        await client.admin.command("ping")
        logger.info(f"Connected to MongoDB: {_mask_mongo_uri(settings.mongodb_uri)} / db={settings.mongodb_db}")
    except Exception as exc:
        logger.error(f"[------------[MongoDB connection failed]----------------\n{exc}")
        raise
    app.state.mongo_client = client
    app.state.mongo_db = client[settings.mongodb_db]

    # Redis 연결 생성 (실패해도 앱은 기동되도록 처리)
    redis_client = aioredis.from_url(settings.redis_url, encoding="utf-8", decode_responses=True)
    try:
        await redis_client.ping()
        app.state.redis = redis_client
        logger.info("Connected to Redis")
    except Exception as exc:
        logger.warning(f"Redis connection failed; continuing without Redis. error={exc}")
        app.state.redis = None
    yield
    client.close()
    try:
        if getattr(app.state, "redis", None) is not None:
            await app.state.redis.aclose()
    except Exception:
        pass


settings = get_settings()
app = FastAPI(
    title="WiNear API - Web Backend",
    version="0.1.0",
    lifespan=lifespan,
    root_path="",
    docs_url="/docs",
    openapi_url="/openapi.json",
    openapi_version="3.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["system"], summary="헬스 체크")  # liveness probe
def health() -> dict[str, str]:
    return {"status": "ok", "time": datetime.now(timezone.utc).isoformat()}


app.include_router(user_features_router)
app.include_router(chat_router)
app.include_router(user_summary_router)