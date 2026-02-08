from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import datetime, timedelta

from app.db.database import get_db

router = APIRouter()

@router.get("/")
async def get_timeline(
    start: Optional[str] = None,
    end: Optional[str] = None,
    sources: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    获取统一时间轴
    
    参数:
    - start: 开始时间 (ISO 格式)
    - end: 结束时间 (ISO 格式)
    - sources: 数据源过滤 (逗号分隔: trello,github,stock,weather)
    """
    # 默认最近7天
    if not end:
        end_dt = datetime.utcnow()
    else:
        end_dt = datetime.fromisoformat(end)
    
    if not start:
        start_dt = end_dt - timedelta(days=7)
    else:
        start_dt = datetime.fromisoformat(start)
    
    source_list = sources.split(",") if sources else None
    
    return {
        "start": start_dt.isoformat(),
        "end": end_dt.isoformat(),
        "activities": [],  # 待实现：查询 Activity 表
        "message": "Timeline API - 待实现"
    }

@router.get("/today")
async def get_today_timeline(db: AsyncSession = Depends(get_db)):
    """获取今日活动"""
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    return await get_timeline(start=today.isoformat(), db=db)

@router.get("/week")
async def get_week_timeline(db: AsyncSession = Depends(get_db)):
    """获取本周活动"""
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today - timedelta(days=today.weekday())
    return await get_timeline(start=week_start.isoformat(), db=db)

@router.get("/month")
async def get_month_timeline(db: AsyncSession = Depends(get_db)):
    """获取本月活动"""
    today = datetime.utcnow()
    month_start = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    return await get_timeline(start=month_start.isoformat(), db=db)
