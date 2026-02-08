"""
GitHub API 路由
- OAuth 授权流程
- 仓库、提交、Issue、PR 数据接口
- 统计信息
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import httpx

from app.core.config import get_settings
from app.db.database import get_db
from app.services.github_service import (
    get_github_service,
    get_github_oauth_service,
    GitHubAPIService
)
from app.utils.cache import get_cache

router = APIRouter()
settings = get_settings()


# ==================== OAuth 授权流程 ====================

@router.get("/auth/login")
async def github_login():
    """
    开始 GitHub OAuth 授权流程
    返回授权 URL，前端需要重定向到该 URL
    """
    oauth_service = get_github_oauth_service()
    
    if not settings.GITHUB_CLIENT_ID:
        raise HTTPException(
            status_code=500,
            detail="GitHub OAuth not configured. Please set GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET."
        )
    
    # 生成 state 参数防止 CSRF
    import secrets
    state = secrets.token_urlsafe(32)
    
    auth_url = oauth_service.get_authorization_url(state=state)
    
    return {
        "auth_url": auth_url,
        "state": state
    }


@router.get("/auth/callback")
async def github_callback(
    code: str,
    state: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    GitHub OAuth 回调处理
    交换授权码获取访问令牌
    """
    oauth_service = get_github_oauth_service()
    
    try:
        # 交换授权码获取令牌
        token_data = await oauth_service.exchange_code_for_token(code)
        
        if "access_token" not in token_data:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to get access token: {token_data.get('error_description', 'Unknown error')}"
            )
        
        access_token = token_data["access_token"]
        
        # 获取用户信息
        user_info = await oauth_service.get_user_info(access_token)
        
        # 加密并存储令牌（这里简化处理，实际应该与用户系统关联）
        encrypted_token = oauth_service.encrypt_token(access_token)
        
        return {
            "success": True,
            "user": {
                "id": user_info.get("id"),
                "login": user_info.get("login"),
                "name": user_info.get("name"),
                "email": user_info.get("email"),
                "avatar_url": user_info.get("avatar_url"),
                "bio": user_info.get("bio"),
            },
            "token_encrypted": encrypted_token[:20] + "...",  # 只显示部分
            "scope": token_data.get("scope", ""),
            "token_type": token_data.get("token_type", "bearer")
        }
        
    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to exchange code: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"OAuth callback error: {str(e)}"
        )


@router.post("/auth/token")
async def store_token(
    token: str,
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    存储用户的 GitHub Token（加密存储）
    """
    from app.models.github import GitHubToken
    from sqlalchemy import select
    
    oauth_service = get_github_oauth_service()
    encrypted_token = oauth_service.encrypt_token(token)
    
    # 检查是否已存在
    result = await db.execute(
        select(GitHubToken).where(GitHubToken.user_id == user_id)
    )
    existing = result.scalar_one_or_none()
    
    if existing:
        existing.access_token_encrypted = encrypted_token
        existing.updated_at = datetime.utcnow()
    else:
        new_token = GitHubToken(
            user_id=user_id,
            access_token_encrypted=encrypted_token,
            is_active=True
        )
        db.add(new_token)
    
    await db.commit()
    
    return {"message": "Token stored successfully"}


# ==================== 仓库接口 ====================

@router.get("/repos", response_model=Dict[str, Any])
async def get_repositories(
    sort: str = Query("updated", description="排序方式: created, updated, pushed, full_name"),
    direction: str = Query("desc", description="排序方向: asc, desc"),
    per_page: int = Query(30, ge=1, le=100),
    force_refresh: bool = Query(False, description="强制刷新缓存"),
    token: Optional[str] = None
):
    """
    获取用户所有仓库列表
    
    - 支持分页和排序
    - 包含仓库基本信息和统计
    - 缓存 5 分钟
    """
    try:
        # 如果强制刷新，清除缓存
        if force_refresh:
            cache = get_cache()
            await cache.delete_pattern("repos:*", prefix="github")
        
        github = get_github_service(token)
        repos = await github.get_user_repositories(
            sort=sort,
            direction=direction,
            per_page=per_page
        )
        
        return {
            "success": True,
            "count": len(repos),
            "username": github.username,
            "repositories": repos
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/repos/{owner}/{repo}")
async def get_repository_detail(
    owner: str,
    repo: str,
    token: Optional[str] = None
):
    """获取单个仓库的详细信息"""
    try:
        github = get_github_service(token)
        
        # 获取基本信息已在 get_user_repositories 中，这里获取额外信息
        repo_full_name = f"{owner}/{repo}"
        languages = await github.get_repository_languages(repo_full_name)
        
        return {
            "success": True,
            "repository": repo_full_name,
            "languages": languages
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 提交记录接口 ====================

@router.get("/repos/{owner}/{repo}/commits")
async def get_repository_commits(
    owner: str,
    repo: str,
    since: Optional[datetime] = None,
    until: Optional[datetime] = None,
    author: Optional[str] = None,
    per_page: int = Query(30, ge=1, le=100),
    token: Optional[str] = None
):
    """
    获取指定仓库的提交记录
    
    - 支持时间范围过滤
    - 支持作者过滤
    - 缓存 3 分钟
    """
    try:
        github = get_github_service(token)
        repo_full_name = f"{owner}/{repo}"
        
        commits = await github.get_repository_commits(
            repo_full_name=repo_full_name,
            since=since,
            until=until,
            author=author,
            per_page=per_page
        )
        
        return {
            "success": True,
            "repository": repo_full_name,
            "count": len(commits),
            "commits": commits
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/commits/recent")
async def get_recent_commits(
    days: int = Query(30, ge=1, le=90, description="最近多少天"),
    per_repo: int = Query(30, ge=1, le=100),
    token: Optional[str] = None
):
    """
    获取最近 N 天的所有提交记录（跨仓库）
    
    - 自动获取用户所有仓库的提交
    - 按时间排序
    - 默认最近 30 天
    """
    try:
        github = get_github_service(token)
        commits = await github.get_recent_commits(
            days=days,
            per_repo=per_repo
        )
        
        return {
            "success": True,
            "days": days,
            "total_commits": len(commits),
            "username": github.username,
            "commits": commits[:100]  # 限制返回数量
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Issue 和 PR 接口 ====================

@router.get("/repos/{owner}/{repo}/issues")
async def get_repository_issues(
    owner: str,
    repo: str,
    state: str = Query("open", description="状态: open, closed, all"),
    sort: str = Query("created", description="排序: created, updated, comments"),
    direction: str = Query("desc", description="方向: asc, desc"),
    per_page: int = Query(30, ge=1, le=100),
    token: Optional[str] = None
):
    """
    获取仓库的 Issues
    
    - 支持状态过滤
    - 不包含 PR
    - 缓存 2 分钟
    """
    try:
        github = get_github_service(token)
        repo_full_name = f"{owner}/{repo}"
        
        issues = await github.get_repository_issues(
            repo_full_name=repo_full_name,
            state=state,
            sort=sort,
            direction=direction,
            per_page=per_page
        )
        
        return {
            "success": True,
            "repository": repo_full_name,
            "state": state,
            "count": len(issues),
            "issues": issues
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/repos/{owner}/{repo}/pulls")
async def get_repository_pulls(
    owner: str,
    repo: str,
    state: str = Query("open", description="状态: open, closed, all"),
    sort: str = Query("created", description="排序: created, updated, popularity, long-running"),
    direction: str = Query("desc", description="方向: asc, desc"),
    per_page: int = Query(30, ge=1, le=100),
    token: Optional[str] = None
):
    """
    获取仓库的 Pull Requests
    
    - 支持状态过滤
    - 包含合并信息
    - 缓存 2 分钟
    """
    try:
        github = get_github_service(token)
        repo_full_name = f"{owner}/{repo}"
        
        pulls = await github.get_repository_pull_requests(
            repo_full_name=repo_full_name,
            state=state,
            sort=sort,
            direction=direction,
            per_page=per_page
        )
        
        return {
            "success": True,
            "repository": repo_full_name,
            "state": state,
            "count": len(pulls),
            "pull_requests": pulls
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pulls/my")
async def get_my_pull_requests(
    state: str = Query("open", description="状态: open, closed, all"),
    per_page: int = Query(50, ge=1, le=100),
    token: Optional[str] = None
):
    """获取当前用户的所有 PR（跨仓库）"""
    try:
        github = get_github_service(token)
        pulls = await github.get_user_pull_requests(
            state=state,
            per_page=per_page
        )
        
        return {
            "success": True,
            "username": github.username,
            "state": state,
            "count": len(pulls),
            "pull_requests": pulls
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 统计接口 ====================

@router.get("/stats")
async def get_user_stats(
    days: int = Query(30, ge=1, le=365, description="统计天数"),
    token: Optional[str] = None
):
    """
    获取用户 GitHub 统计信息
    
    - 提交数量
    - PR 统计
    - Issue 统计
    - 活跃仓库
    - 编程语言分布
    """
    try:
        github = get_github_service(token)
        stats = await github.get_user_stats(days=days)
        
        return {
            "success": True,
            "username": github.username,
            "period_days": days,
            "stats": stats
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rate-limit")
async def get_rate_limit(token: Optional[str] = None):
    """获取当前 GitHub API 速率限制状态"""
    try:
        github = get_github_service(token)
        rate_limit = await github.get_rate_limit_status()
        
        return {
            "success": True,
            "rate_limit": rate_limit
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 事件流接口 ====================

@router.get("/events")
async def get_user_events(
    per_page: int = Query(30, ge=1, le=100),
    token: Optional[str] = None
):
    """获取用户活动事件流"""
    try:
        github = get_github_service(token)
        events = await github.get_user_events(per_page=per_page)
        
        return {
            "success": True,
            "username": github.username,
            "count": len(events),
            "events": events
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 同步和缓存接口 ====================

@router.post("/sync")
async def sync_github_data(
    full_sync: bool = Query(False, description="是否全量同步"),
    token: Optional[str] = None
):
    """
    触发 GitHub 数据同步
    
    - 仓库列表
    - 最近提交
    - PR 和 Issue
    """
    try:
        github = get_github_service(token)
        cache = get_cache()
        
        results = {
            "repositories": 0,
            "commits": 0,
            "pull_requests": 0
        }
        
        # 1. 同步仓库
        repos = await github.get_user_repositories(per_page=100)
        results["repositories"] = len(repos)
        
        # 2. 同步最近提交（如果全量同步）
        if full_sync:
            commits = await github.get_recent_commits(days=30, per_repo=50)
            results["commits"] = len(commits)
            
            # 3. 同步 PR
            prs = await github.get_user_pull_requests(state="all", per_page=100)
            results["pull_requests"] = len(prs)
        
        # 清除相关缓存
        await cache.delete_pattern("*", prefix="github")
        
        return {
            "success": True,
            "full_sync": full_sync,
            "synced_at": datetime.utcnow().isoformat(),
            "results": results
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cache/clear")
async def clear_cache():
    """清除 GitHub 数据缓存"""
    try:
        cache = get_cache()
        deleted = await cache.delete_pattern("*", prefix="github")
        
        return {
            "success": True,
            "deleted_keys": deleted
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 兼容旧接口 ====================

@router.get("/contributions")
async def get_contributions_compat(token: Optional[str] = None):
    """兼容旧接口：获取用户贡献信息"""
    try:
        github = get_github_service(token)
        
        # 获取用户信息
        user = github.github.get_user()
        
        return {
            "username": user.login,
            "public_repos": user.public_repos,
            "followers": user.followers,
            "following": user.following,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "bio": user.bio,
            "location": user.location,
            "blog": user.blog,
            "avatar_url": user.avatar_url,
            "html_url": user.html_url
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
