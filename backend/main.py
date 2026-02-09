from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os

from app.core.config import get_settings
from app.core.auth import verify_auth, CF_ACCESS_ENABLED
from app.db.database import init_db
from app.api import trello, github, stocks, weather, timeline, dashboard

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    yield
    # Shutdown


app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
    lifespan=lifespan,
    docs_url=None if not settings.DEBUG else "/docs",  # 生产环境关闭 docs
    redoc_url=None if not settings.DEBUG else "/redoc"
)

# CORS - 允许本地开发和生产环境
allowed_origins = [
    "http://localhost:5173",
    "http://localhost:3000",
    "http://localhost:3001",
    "https://dashboard.mosbiic.com",  # Cloudflare Tunnel 域名
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Routes - 添加 Token 保护（跳过 DEBUG 模式）
# 在 Cloudflare Access 模式下也跳过本地 token 验证
auth_dependency = [Depends(verify_auth)] if not settings.DEBUG and not CF_ACCESS_ENABLED else []

app.include_router(trello.router, prefix="/api/trello", tags=["Trello"], dependencies=auth_dependency)
app.include_router(github.router, prefix="/api/github", tags=["GitHub"], dependencies=auth_dependency)
app.include_router(stocks.router, prefix="/api/stocks", tags=["Stocks"], dependencies=auth_dependency)
app.include_router(weather.router, prefix="/api/weather", tags=["Weather"], dependencies=auth_dependency)
app.include_router(timeline.router, prefix="/api/timeline", tags=["Timeline"], dependencies=auth_dependency)
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["Dashboard"], dependencies=auth_dependency)


@app.get("/health")
async def health_check():
    """健康检查 - 不需要 token"""
    return {"status": "ok", "app": settings.APP_NAME, "cf_access": CF_ACCESS_ENABLED}


@app.get("/")
async def root():
    """根路径 - 不需要 token"""
    return {
        "message": "Personal Dashboard API",
        "version": "0.1.0",
        "auth_required": not settings.DEBUG,
        "cf_access_enabled": CF_ACCESS_ENABLED,
        "docs": "/docs" if settings.DEBUG else None
    }
