import httpx
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.core.config import get_settings
from app.db.database import TrelloCard, Activity

settings = get_settings()

TRELLO_BASE_URL = "https://api.trello.com/1"


class TrelloService:
    def __init__(self, db: Optional[AsyncSession] = None):
        self.api_key = settings.TRELLO_API_KEY
        self.token = settings.TRELLO_TOKEN
        self.db = db
        self.client = httpx.AsyncClient(base_url=TRELLO_BASE_URL)
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, *args):
        await self.client.aclose()
    
    def _get_auth_params(self) -> Dict[str, str]:
        return {"key": self.api_key, "token": self.token}
    
    async def get_boards(self) -> List[Dict]:
        """获取用户所有看板"""
        params = {**self._get_auth_params(), "fields": "name,url,dateLastActivity"}
        response = await self.client.get("/members/me/boards", params=params)
        response.raise_for_status()
        return response.json()
    
    async def get_lists(self, board_id: str) -> List[Dict]:
        """获取看板的列表"""
        params = self._get_auth_params()
        response = await self.client.get(f"/boards/{board_id}/lists", params=params)
        response.raise_for_status()
        return response.json()
    
    async def get_cards(
        self,
        board_id: str,
        since: Optional[str] = None
    ) -> List[Dict]:
        """获取看板卡片"""
        params = {
            **self._get_auth_params(),
            "fields": "name,desc,due,dueComplete,dateLastActivity,labels,url",
            "checklists": "all"
        }
        if since:
            params["since"] = since
        
        response = await self.client.get(f"/boards/{board_id}/cards", params=params)
        response.raise_for_status()
        return response.json()
    
    async def get_actions(self, board_id: str, since: Optional[str] = None) -> List[Dict]:
        """获取看板活动"""
        params = {
            **self._get_auth_params(),
            "filter": "updateCard:idList,updateCard:closed,createCard",
            "limit": 1000
        }
        if since:
            params["since"] = since
        
        response = await self.client.get(f"/boards/{board_id}/actions", params=params)
        response.raise_for_status()
        return response.json()
    
    async def sync_data(self) -> Dict[str, Any]:
        """同步 Trello 数据到数据库"""
        if not self.db:
            return {"error": "Database session required"}
        
        if not settings.TRELLO_BOARD_ID:
            boards = await self.get_boards()
            if not boards:
                return {"error": "No boards found"}
            board_id = boards[0]["id"]
        else:
            board_id = settings.TRELLO_BOARD_ID
        
        # 获取卡片
        cards = await self.get_cards(board_id)
        
        # 获取列表名称映射
        lists = await self.get_lists(board_id)
        list_names = {l["id"]: l["name"] for l in lists}
        
        boards_data = await self.get_boards()
        board_name = next((b["name"] for b in boards_data if b["id"] == board_id), "Unknown")
        
        synced_count = 0
        for card_data in cards:
            # 检查是否已存在
            existing = await self.db.execute(
                select(TrelloCard).where(TrelloCard.trello_id == card_data["id"])
            )
            existing_card = existing.scalar_one_or_none()
            
            list_name = list_names.get(card_data.get("idList"), "Unknown")
            due_date = None
            if card_data.get("due"):
                due_date = datetime.fromisoformat(card_data["due"].replace("Z", "+00:00"))
            
            if existing_card:
                # 更新
                existing_card.name = card_data["name"]
                existing_card.description = card_data.get("desc", "")
                existing_card.list_name = list_name
                existing_card.labels = [l["name"] for l in card_data.get("labels", [])]
                existing_card.due_date = due_date
                existing_card.completed = card_data.get("dueComplete", False)
                existing_card.updated_at = datetime.utcnow()
            else:
                # 新建
                new_card = TrelloCard(
                    trello_id=card_data["id"],
                    name=card_data["name"],
                    description=card_data.get("desc", ""),
                    list_name=list_name,
                    board_name=board_name,
                    labels=[l["name"] for l in card_data.get("labels", [])],
                    due_date=due_date,
                    completed=card_data.get("dueComplete", False)
                )
                self.db.add(new_card)
                synced_count += 1
        
        await self.db.commit()
        
        return {
            "board_id": board_id,
            "board_name": board_name,
            "cards_synced": synced_count,
            "total_cards": len(cards)
        }
    
    async def get_stats(self, days: int = 7) -> Dict[str, Any]:
        """获取 Trello 统计"""
        if not self.db:
            return {"error": "Database session required"}
        
        since = datetime.utcnow() - __import__('datetime').timedelta(days=days)
        
        # 完成的任务数
        completed_result = await self.db.execute(
            select(TrelloCard).where(
                and_(
                    TrelloCard.completed == True,
                    TrelloCard.completed_at >= since
                )
            )
        )
        completed = completed_result.scalars().all()
        
        # 按列表分组
        all_cards_result = await self.db.execute(select(TrelloCard))
        all_cards = all_cards_result.scalars().all()
        
        by_list = {}
        for card in all_cards:
            by_list[card.list_name] = by_list.get(card.list_name, 0) + 1
        
        return {
            "period_days": days,
            "completed_count": len(completed),
            "total_cards": len(all_cards),
            "by_list": by_list
        }
    
    async def get_completed_since(self, since: datetime) -> List[Dict]:
        """获取自指定时间以来完成的任务"""
        if not self.db:
            return []
        
        result = await self.db.execute(
            select(TrelloCard).where(
                and_(
                    TrelloCard.completed == True,
                    TrelloCard.completed_at >= since
                )
            )
        )
        cards = result.scalars().all()
        
        return [
            {
                "id": c.trello_id,
                "name": c.name,
                "list": c.list_name,
                "completed_at": c.completed_at.isoformat() if c.completed_at else None,
                "labels": c.labels
            }
            for c in cards
        ]
