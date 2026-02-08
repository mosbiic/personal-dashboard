from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import get_settings
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
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Routes
app.include_router(trello.router, prefix="/api/trello", tags=["Trello"])
app.include_router(github.router, prefix="/api/github", tags=["GitHub"])
app.include_router(stocks.router, prefix="/api/stocks", tags=["Stocks"])
app.include_router(weather.router, prefix="/api/weather", tags=["Weather"])
app.include_router(timeline.router, prefix="/api/timeline", tags=["Timeline"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["Dashboard"])


@app.get("/health")
async def health_check():
    return {"status": "ok", "app": settings.APP_NAME}


@app.get("/")
async def root():
    return {
        "message": "Personal Dashboard API",
        "docs": "/docs",
        "version": "0.1.0"
    }
