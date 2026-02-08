from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, and_, or_
from typing import Optional, List
from datetime import datetime, timedelta

from app.db.database import get_db
from app.db.database import Activity, GitHubCommit, GitHubPullRequest, TrelloCard, StockPriceHistory

router = APIRouter()


@router.get("/")
async def get_timeline(
    start: Optional[str] = None,
    end: Optional[str] = None,
    sources: Optional[str] = None,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """
    获取统一时间轴
    
    参数:
    - start: 开始时间 (ISO 格式)
    - end: 结束时间 (ISO 格式)
    - sources: 数据源过滤 (逗号分隔: trello,github,stock,weather)
    - limit: 返回条数限制
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
    
    # 查询 Activity 表
    query = select(Activity).where(
        and_(
            Activity.occurred_at >= start_dt,
            Activity.occurred_at <= end_dt
        )
    ).order_by(desc(Activity.occurred_at)).limit(limit)
    
    if source_list:
        query = query.where(Activity.source_type.in_(source_list))
    
    result = await db.execute(query)
    activities = result.scalars().all()
    
    # 如果没有 Activity 数据，实时聚合各数据源
    if not activities:
        activities = await _aggregate_activities(start_dt, end_dt, source_list, db)
    
    return {
        "start": start_dt.isoformat(),
        "end": end_dt.isoformat(),
        "count": len(activities),
        "activities": [
            {
                "id": str(a.id),
                "source_type": a.source_type,
                "source_id": a.source_id,
                "activity_type": a.activity_type,
                "title": a.title,
                "description": a.description,
                "url": a.url,
                "metadata": a.metadata,
                "occurred_at": a.occurred_at.isoformat(),
                "icon": _get_activity_icon(a.source_type, a.activity_type)
            }
            for a in activities
        ]
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


async def _aggregate_activities(
    start_dt: datetime,
    end_dt: datetime,
    source_list: Optional[List[str]],
    db: AsyncSession
) -> List[Activity]:
    """实时聚合各数据源的活动"""
    activities = []
    
    sources_to_query = source_list or ["github", "trello", "stock"]
    
    # GitHub 活动
    if "github" in sources_to_query:
        # GitHub Commits
        commits_result = await db.execute(
            select(GitHubCommit).where(
                and_(
                    GitHubCommit.committed_at >= start_dt,
                    GitHubCommit.committed_at <= end_dt
                )
            ).order_by(desc(GitHubCommit.committed_at))
        )
        for commit in commits_result.scalars().all():
            activities.append(Activity(
                source_type="github",
                source_id=commit.sha,
                activity_type="commit",
                title=f"提交代码",
                description=commit.message[:100] if commit.message else "",
                url=commit.html_url,
                metadata={
                    "repository": commit.repository.full_name if commit.repository else None,
                    "sha": commit.sha[:7]
                },
                occurred_at=commit.committed_at or commit.created_at
            ))
        
        # GitHub PRs
        prs_result = await db.execute(
            select(GitHubPullRequest).where(
                and_(
                    GitHubPullRequest.updated_at >= start_dt,
                    GitHubPullRequest.updated_at <= end_dt
                )
            ).order_by(desc(GitHubPullRequest.updated_at))
        )
        for pr in prs_result.scalars().all():
            action = "合并" if pr.merged else ("关闭" if pr.state == "closed" else "打开")
            activities.append(Activity(
                source_type="github",
                source_id=str(pr.number),
                activity_type="pr_merge" if pr.merged else "pr",
                title=f"{action} PR: {pr.title}",
                description=f"#{pr.number} in {pr.repository.full_name if pr.repository else 'unknown'}",
                url=pr.html_url,
                metadata={
                    "repository": pr.repository.full_name if pr.repository else None,
                    "number": pr.number,
                    "state": "merged" if pr.merged else pr.state
                },
                occurred_at=pr.updated_at
            ))
    
    # Trello 活动
    if "trello" in sources_to_query:
        cards_result = await db.execute(
            select(TrelloCard).where(
                and_(
                    TrelloCard.completed_at >= start_dt,
                    TrelloCard.completed_at <= end_dt
                )
            ).order_by(desc(TrelloCard.completed_at))
        )
        for card in cards_result.scalars().all():
            activities.append(Activity(
                source_type="trello",
                source_id=card.trello_id,
                activity_type="task_complete",
                title="完成任务",
                description=card.name,
                url=f"https://trello.com/c/{card.trello_id}",
                metadata={
                    "board": card.board_name,
                    "list": card.list_name,
                    "labels": card.labels
                },
                occurred_at=card.completed_at
            ))
    
    # 按时间排序
    activities.sort(key=lambda x: x.occurred_at, reverse=True)
    
    return activities


def _get_activity_icon(source_type: str, activity_type: str) -> str:
    """获取活动图标"""
    icons = {
        "github": {
            "commit": "💻",
            "pr": "🔀",
            "pr_merge": "✅",
            "issue": "🐛",
            "issue_close": "🎯"
        },
        "trello": {
            "task_complete": "✅",
            "task_create": "📝",
            "task_move": "📋"
        },
        "stock": {
            "price_update": "📈",
            "alert": "🚨"
        },
        "weather": {
            "update": "🌤️"
        },
        "session": {
            "message": "💬"
        }
    }
    
    source_icons = icons.get(source_type, {})
    return source_icons.get(activity_type, "📝")


@router.post("/refresh")
async def refresh_timeline(db: AsyncSession = Depends(get_db)):
    """
    刷新时间轴 - 从各数据源同步最新活动到 Activity 表
    """
    from datetime import datetime, timedelta
    
    start_dt = datetime.utcnow() - timedelta(days=30)
    end_dt = datetime.utcnow()
    
    # 获取聚合的活动
    activities = await _aggregate_activities(start_dt, end_dt, None, db)
    
    # 保存到 Activity 表
    saved_count = 0
    for activity in activities:
        # 检查是否已存在
        existing = await db.execute(
            select(Activity).where(
                and_(
                    Activity.source_type == activity.source_type,
                    Activity.source_id == activity.source_id
                )
            )
        )
        if not existing.scalar_one_or_none():
            db.add(activity)
            saved_count += 1
    
    await db.commit()
    
    return {
        "success": True,
        "message": f"同步完成，新增 {saved_count} 条活动记录",
        "total_synced": len(activities)
    }
