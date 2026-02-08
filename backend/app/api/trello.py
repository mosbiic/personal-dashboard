from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import datetime, timedelta

from app.db.database import get_db
from app.services.trello_service import TrelloService

router = APIRouter()


@router.get("/boards")
async def get_boards(db: AsyncSession = Depends(get_db)):
    """获取 Trello 看板列表"""
    service = TrelloService()
    return await service.get_boards()


@router.get("/boards/{board_id}/lists")
async def get_lists(board_id: str, db: AsyncSession = Depends(get_db)):
    """获取看板列表"""
    service = TrelloService()
    return await service.get_lists(board_id)


@router.get("/boards/{board_id}/cards")
async def get_cards(
    board_id: str,
    since: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """获取看板卡片"""
    service = TrelloService()
    return await service.get_cards(board_id, since=since)


@router.post("/sync")
async def sync_trello_data(db: AsyncSession = Depends(get_db)):
    """同步 Trello 数据到数据库"""
    service = TrelloService(db)
    result = await service.sync_data()
    return result


@router.get("/stats")
async def get_stats(
    days: int = 7,
    db: AsyncSession = Depends(get_db)
):
    """获取 Trello 统计"""
    service = TrelloService(db)
    return await service.get_stats(days=days)


@router.get("/completed-today")
async def get_completed_today(db: AsyncSession = Depends(get_db)):
    """获取今日完成的任务"""
    service = TrelloService(db)
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    return await service.get_completed_since(today)
