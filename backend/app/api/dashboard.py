from fastapi import APIRouter, HTTPException
from typing import Optional
from datetime import datetime, timedelta
import asyncio

from app.services.trello_service import TrelloService
from app.services.github_service import get_github_service
from app.services.stock_service import get_stock_service, DEFAULT_HOLDINGS
from app.services.weather_service import weather_service
from app.db.database import AsyncSessionLocal
from sqlalchemy import select, func
from app.db.database import TrelloCard, Activity

router = APIRouter()


@router.get("/summary")
async def get_dashboard_summary():
    """仪表盘总览 - 获取真实数据"""
    result = {
        "date": datetime.utcnow().isoformat(),
        "trello": {"completed_today": 0, "pending": 0},
        "github": {"commits_today": 0, "prs": 0},
        "stocks": {"total_pnl": 0, "daily_change": 0},
        "weather": {"temp": 0, "condition": "加载中..."},
    }
    
    # 1. 获取 Trello 数据
    try:
        async with AsyncSessionLocal() as db:
            # 获取今日完成的任务
            today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            completed_result = await db.execute(
                select(TrelloCard).where(
                    TrelloCard.completed == True,
                    TrelloCard.updated_at >= today
                )
            )
            completed_count = len(completed_result.scalars().all())
            
            # 获取待办任务数（未完成的卡片）
            pending_result = await db.execute(
                select(TrelloCard).where(TrelloCard.completed == False)
            )
            pending_count = len(pending_result.scalars().all())
            
            result["trello"] = {
                "completed_today": completed_count,
                "pending": pending_count
            }
    except Exception as e:
        print(f"Error fetching Trello data: {e}")
        result["trello"] = {"completed_today": 0, "pending": 0, "error": str(e)}
    
    # 2. 获取 GitHub 数据
    try:
        github = get_github_service()
        # 获取今日提交数
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        commits = await github.get_recent_commits(days=1, per_repo=20)
        
        # 统计今日提交
        today_commits = 0
        for commit in commits:
            commit_date = commit.get('committer', {}).get('date')
            if commit_date:
                commit_dt = datetime.fromisoformat(commit_date.replace('Z', '+00:00')).replace(tzinfo=None)
                if commit_dt >= today:
                    today_commits += 1
        
        # 获取开放的 PR 数
        prs = await github.get_user_pull_requests(state="open", per_page=50)
        
        result["github"] = {
            "commits_today": today_commits,
            "prs": len(prs)
        }
    except Exception as e:
        print(f"Error fetching GitHub data: {e}")
        result["github"] = {"commits_today": 0, "prs": 0, "error": str(e)}
    
    # 3. 获取股票数据
    try:
        stock_service = get_stock_service()
        portfolio = await stock_service.calculate_portfolio(DEFAULT_HOLDINGS)
        
        summary = portfolio.get("summary", {})
        result["stocks"] = {
            "total_pnl": summary.get("total_pnl", 0),
            "daily_change": summary.get("total_pnl_pct", 0),
            "total_value": summary.get("total_value", 0)
        }
    except Exception as e:
        print(f"Error fetching stock data: {e}")
        result["stocks"] = {"total_pnl": 0, "daily_change": 0, "error": str(e)}
    
    # 4. 获取天气数据
    try:
        weather = await weather_service.get_current_weather()
        current = weather.get("current", {})
        result["weather"] = {
            "temp": current.get("temperature", 0),
            "condition": current.get("description", "未知"),
            "icon": current.get("icon", "🌡️"),
            "feels_like": current.get("feels_like", 0),
            "humidity": current.get("humidity", 0)
        }
    except Exception as e:
        print(f"Error fetching weather data: {e}")
        result["weather"] = {"temp": 0, "condition": "获取失败", "error": str(e)}
    
    return result


@router.get("/correlations")
async def get_correlations(days: int = 7):
    """
    数据关联分析
    
    - 代码提交 vs Trello 完成率
    - 对话活跃度 vs 任务进度
    """
    return {
        "period_days": days,
        "code_vs_tasks": {"correlation": 0, "description": "待计算"},
        "chat_vs_progress": {"correlation": 0, "description": "待计算"},
        "message": "Correlations API - 待实现"
    }
