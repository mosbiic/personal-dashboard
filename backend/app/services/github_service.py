"""
GitHub API 服务
- OAuth 授权流程
- REST API 和 GraphQL API 客户端
- 速率限制处理
- Redis 缓存
- Token 加密存储
"""

import httpx
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from github import Github
from github.GithubException import GithubException, RateLimitExceededException
import asyncio

from app.core.config import get_settings
from app.utils.encryption import get_encryption
from app.utils.cache import get_cache, cached

settings = get_settings()


class GitHubRateLimiter:
    """GitHub API 速率限制管理器"""
    
    # GitHub API 限制
    RATE_LIMIT = 5000  # 每小时请求数
    RATE_LIMIT_RESET_BUFFER = 60  # 重置前缓冲秒数
    
    def __init__(self):
        self.remaining = self.RATE_LIMIT
        self.reset_at: Optional[datetime] = None
        self.last_request_at: Optional[datetime] = None
    
    def update_from_headers(self, headers: Dict[str, str]):
        """从响应头更新速率限制信息"""
        try:
            self.remaining = int(headers.get('x-ratelimit-remaining', self.remaining))
            reset_timestamp = headers.get('x-ratelimit-reset')
            if reset_timestamp:
                self.reset_at = datetime.fromtimestamp(int(reset_timestamp))
            self.last_request_at = datetime.utcnow()
        except (ValueError, TypeError):
            pass
    
    def is_rate_limited(self) -> bool:
        """检查是否已触发速率限制"""
        if self.remaining <= 0:
            return True
        if self.reset_at and datetime.utcnow() < self.reset_at:
            return False
        return False
    
    def get_wait_time(self) -> int:
        """获取需要等待的秒数"""
        if not self.reset_at:
            return 0
        
        wait_time = (self.reset_at - datetime.utcnow()).total_seconds()
        return max(0, int(wait_time) + self.RATE_LIMIT_RESET_BUFFER)
    
    async def wait_if_needed(self):
        """如果需要，等待直到速率限制重置"""
        if self.is_rate_limited():
            wait_time = self.get_wait_time()
            if wait_time > 0:
                print(f"GitHub API rate limit hit. Waiting {wait_time} seconds...")
                await asyncio.sleep(wait_time)


class GitHubOAuthService:
    """GitHub OAuth 服务"""
    
    GITHUB_AUTH_URL = "https://github.com/login/oauth/authorize"
    GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
    GITHUB_API_URL = "https://api.github.com"
    
    def __init__(self):
        self.client_id = settings.GITHUB_CLIENT_ID
        self.client_secret = settings.GITHUB_CLIENT_SECRET
        self.redirect_uri = settings.GITHUB_REDIRECT_URI
        self.encryption = get_encryption()
        self.cache = get_cache()
    
    def get_authorization_url(self, state: Optional[str] = None) -> str:
        """生成 OAuth 授权 URL"""
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": "repo read:user read:org",
            "response_type": "code"
        }
        if state:
            params["state"] = state
        
        query = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{self.GITHUB_AUTH_URL}?{query}"
    
    async def exchange_code_for_token(self, code: str) -> Dict[str, Any]:
        """用授权码交换访问令牌"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.GITHUB_TOKEN_URL,
                headers={"Accept": "application/json"},
                data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "code": code,
                    "redirect_uri": self.redirect_uri
                }
            )
            response.raise_for_status()
            return response.json()
    
    async def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """刷新访问令牌（GitHub 不支持标准刷新令牌，需要重新授权）"""
        # GitHub OAuth 不返回刷新令牌，这里预留接口
        # 如果需要长期访问，建议使用 GitHub App 而不是 OAuth App
        raise NotImplementedError("GitHub OAuth does not support refresh tokens. Re-authorization required.")
    
    async def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """获取用户信息"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.GITHUB_API_URL}/user",
                headers={
                    "Authorization": f"token {access_token}",
                    "Accept": "application/vnd.github.v3+json"
                }
            )
            response.raise_for_status()
            return response.json()
    
    def encrypt_token(self, token: str) -> str:
        """加密令牌"""
        return self.encryption.encrypt(token)
    
    def decrypt_token(self, encrypted_token: str) -> str:
        """解密令牌"""
        return self.encryption.decrypt(encrypted_token)


class GitHubAPIService:
    """GitHub API 服务"""
    
    def __init__(self, access_token: Optional[str] = None):
        """
        初始化 GitHub API 服务
        
        Args:
            access_token: GitHub 访问令牌，如果为 None 则使用环境变量中的令牌
        """
        self.token = access_token or settings.GITHUB_TOKEN
        if not self.token:
            raise ValueError("GitHub token is required. Please provide access_token or set GITHUB_TOKEN env var.")
        
        # 初始化 PyGithub 客户端
        self.github = Github(self.token, per_page=100)
        
        # 初始化速率限制管理器
        self.rate_limiter = GitHubRateLimiter()
        
        # 初始化缓存
        self.cache = get_cache()
        
        # 用户名（延迟加载）
        self._username: Optional[str] = None
    
    @property
    def username(self) -> str:
        """获取当前用户名"""
        if self._username is None:
            try:
                self._username = self.github.get_user().login
            except Exception:
                self._username = settings.GITHUB_USERNAME
        return self._username
    
    def _handle_rate_limit(self, func):
        """处理速率限制的包装器"""
        async def wrapper(*args, **kwargs):
            await self.rate_limiter.wait_if_needed()
            try:
                result = func(*args, **kwargs)
                # 更新速率限制信息（如果有响应头）
                return result
            except RateLimitExceededException:
                # 等待并重试
                reset_time = self.github.get_rate_limit().core.reset
                wait_time = (reset_time - datetime.utcnow()).total_seconds()
                if wait_time > 0:
                    await asyncio.sleep(wait_time + 5)
                    return func(*args, **kwargs)
                raise
        return wrapper
    
    # ==================== 仓库相关接口 ====================
    
    @cached(ttl=300, prefix="github:repos")
    async def get_user_repositories(
        self,
        sort: str = "updated",
        direction: str = "desc",
        per_page: int = 100
    ) -> List[Dict[str, Any]]:
        """
        获取用户的所有仓库
        
        Args:
            sort: 排序方式 (created, updated, pushed, full_name)
            direction: 排序方向 (asc, desc)
            per_page: 每页数量
        """
        try:
            user = self.github.get_user()
            repos = user.get_repos(
                sort=sort,
                direction=direction,
                affiliation='owner,collaborator,organization_member'
            )
            
            result = []
            for repo in repos[:per_page]:
                try:
                    repo_data = {
                        "id": repo.id,
                        "name": repo.name,
                        "full_name": repo.full_name,
                        "owner": repo.owner.login,
                        "description": repo.description,
                        "private": repo.private,
                        "fork": repo.fork,
                        "url": repo.html_url,
                        "created_at": repo.created_at.isoformat() if repo.created_at else None,
                        "updated_at": repo.updated_at.isoformat() if repo.updated_at else None,
                        "pushed_at": repo.pushed_at.isoformat() if repo.pushed_at else None,
                        "homepage": repo.homepage,
                        "size": repo.size,
                        "stargazers_count": repo.stargazers_count,
                        "watchers_count": repo.watchers_count,
                        "language": repo.language,
                        "forks_count": repo.forks_count,
                        "open_issues_count": repo.open_issues_count,
                        "default_branch": repo.default_branch,
                        "topics": repo.topics,
                        "archived": repo.archived,
                        "disabled": repo.disabled,
                    }
                    result.append(repo_data)
                except Exception as e:
                    print(f"Error processing repo {repo.name}: {e}")
                    continue
            
            return result
            
        except GithubException as e:
            raise Exception(f"GitHub API error: {e.data.get('message', str(e))}")
    
    async def get_repository_languages(self, repo_full_name: str) -> Dict[str, int]:
        """获取仓库的语言统计"""
        try:
            repo = self.github.get_repo(repo_full_name)
            return repo.get_languages()
        except GithubException as e:
            print(f"Error fetching languages for {repo_full_name}: {e}")
            return {}
    
    # ==================== 提交记录接口 ====================
    
    async def get_repository_commits(
        self,
        repo_full_name: str,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        author: Optional[str] = None,
        per_page: int = 100
    ) -> List[Dict[str, Any]]:
        """
        获取仓库的提交记录
        
        Args:
            repo_full_name: 仓库全名 (owner/repo)
            since: 开始时间
            until: 结束时间
            author: 作者过滤
            per_page: 每页数量
        """
        cache_key = f"commits:{repo_full_name}:{since}:{until}:{author}"
        
        async def fetch_commits():
            try:
                repo = self.github.get_repo(repo_full_name)
                
                # 构建查询参数
                kwargs = {}
                if since:
                    kwargs['since'] = since
                if until:
                    kwargs['until'] = until
                if author:
                    kwargs['author'] = author
                
                commits = repo.get_commits(**kwargs)
                
                result = []
                for commit in commits[:per_page]:
                    try:
                        commit_data = {
                            "sha": commit.sha,
                            "message": commit.commit.message,
                            "author": {
                                "name": commit.commit.author.name,
                                "email": commit.commit.author.email,
                                "date": commit.commit.author.date.isoformat() if commit.commit.author.date else None,
                                "login": commit.author.login if commit.author else None
                            },
                            "committer": {
                                "name": commit.commit.committer.name,
                                "email": commit.commit.committer.email,
                                "date": commit.commit.committer.date.isoformat() if commit.commit.committer.date else None,
                                "login": commit.committer.login if commit.committer else None
                            },
                            "html_url": commit.html_url,
                            "stats": {
                                "additions": commit.stats.additions if hasattr(commit, 'stats') else None,
                                "deletions": commit.stats.deletions if hasattr(commit, 'stats') else None,
                                "total": commit.stats.total if hasattr(commit, 'stats') else None
                            } if hasattr(commit, 'stats') else None
                        }
                        result.append(commit_data)
                    except Exception as e:
                        print(f"Error processing commit {commit.sha[:7]}: {e}")
                        continue
                
                return result
                
            except GithubException as e:
                raise Exception(f"GitHub API error: {e.data.get('message', str(e))}")
        
        return await self.cache.get_or_set(cache_key, fetch_commits, ttl=180, prefix="github")
    
    async def get_recent_commits(
        self,
        days: int = 30,
        per_repo: int = 30
    ) -> List[Dict[str, Any]]:
        """
        获取最近 N 天的所有提交记录
        
        Args:
            days: 最近多少天
            per_repo: 每个仓库获取多少条
        """
        since = datetime.utcnow() - timedelta(days=days)
        
        # 获取用户仓库列表
        repos = await self.get_user_repositories(per_page=50)
        
        all_commits = []
        for repo in repos:
            try:
                commits = await self.get_repository_commits(
                    repo['full_name'],
                    since=since,
                    per_page=per_repo
                )
                
                for commit in commits:
                    commit['repository'] = {
                        'name': repo['name'],
                        'full_name': repo['full_name']
                    }
                
                all_commits.extend(commits)
            except Exception as e:
                print(f"Error fetching commits from {repo['full_name']}: {e}")
                continue
        
        # 按时间排序
        all_commits.sort(
            key=lambda x: x['committer']['date'] if x['committer']['date'] else '',
            reverse=True
        )
        
        return all_commits
    
    # ==================== Issue 和 PR 接口 ====================
    
    async def get_repository_issues(
        self,
        repo_full_name: str,
        state: str = "open",
        sort: str = "created",
        direction: str = "desc",
        per_page: int = 30
    ) -> List[Dict[str, Any]]:
        """
        获取仓库的 Issues
        
        Args:
            repo_full_name: 仓库全名
            state: 状态 (open, closed, all)
            sort: 排序方式
            direction: 排序方向
            per_page: 每页数量
        """
        cache_key = f"issues:{repo_full_name}:{state}:{sort}"
        
        async def fetch_issues():
            try:
                repo = self.github.get_repo(repo_full_name)
                issues = repo.get_issues(
                    state=state,
                    sort=sort,
                    direction=direction
                )
                
                result = []
                for issue in issues[:per_page]:
                    # 跳过 PR（GitHub 把 PR 也当作 Issue）
                    if issue.pull_request:
                        continue
                    
                    issue_data = {
                        "id": issue.id,
                        "number": issue.number,
                        "title": issue.title,
                        "body": issue.body,
                        "state": issue.state,
                        "state_reason": issue.state_reason,
                        "user": {
                            "login": issue.user.login,
                            "id": issue.user.id,
                            "avatar_url": issue.user.avatar_url
                        },
                        "labels": [
                            {"name": label.name, "color": label.color}
                            for label in issue.labels
                        ],
                        "assignees": [
                            {"login": assignee.login, "id": assignee.id}
                            for assignee in issue.assignees
                        ],
                        "milestone": issue.milestone.title if issue.milestone else None,
                        "comments": issue.comments,
                        "created_at": issue.created_at.isoformat() if issue.created_at else None,
                        "updated_at": issue.updated_at.isoformat() if issue.updated_at else None,
                        "closed_at": issue.closed_at.isoformat() if issue.closed_at else None,
                        "html_url": issue.html_url
                    }
                    result.append(issue_data)
                
                return result
                
            except GithubException as e:
                raise Exception(f"GitHub API error: {e.data.get('message', str(e))}")
        
        return await self.cache.get_or_set(cache_key, fetch_issues, ttl=120, prefix="github")
    
    async def get_repository_pull_requests(
        self,
        repo_full_name: str,
        state: str = "open",
        sort: str = "created",
        direction: str = "desc",
        per_page: int = 30
    ) -> List[Dict[str, Any]]:
        """
        获取仓库的 Pull Requests
        
        Args:
            repo_full_name: 仓库全名
            state: 状态 (open, closed, all)
            sort: 排序方式 (created, updated, popularity, long-running)
            direction: 排序方向
            per_page: 每页数量
        """
        cache_key = f"prs:{repo_full_name}:{state}:{sort}"
        
        async def fetch_prs():
            try:
                repo = self.github.get_repo(repo_full_name)
                pulls = repo.get_pulls(
                    state=state,
                    sort=sort,
                    direction=direction
                )
                
                result = []
                for pr in pulls[:per_page]:
                    pr_data = {
                        "id": pr.id,
                        "number": pr.number,
                        "title": pr.title,
                        "body": pr.body,
                        "state": pr.state,
                        "user": {
                            "login": pr.user.login,
                            "id": pr.user.id,
                            "avatar_url": pr.user.avatar_url
                        },
                        "head": {
                            "ref": pr.head.ref,
                            "sha": pr.head.sha,
                            "repo": pr.head.repo.full_name if pr.head.repo else None
                        },
                        "base": {
                            "ref": pr.base.ref,
                            "sha": pr.base.sha,
                            "repo": pr.base.repo.full_name
                        },
                        "merged": pr.is_merged(),
                        "mergeable": pr.mergeable,
                        "merged_by": pr.merged_by.login if pr.merged_by else None,
                        "merged_at": pr.merged_at.isoformat() if pr.merged_at else None,
                        "draft": pr.draft,
                        "labels": [
                            {"name": label.name, "color": label.color}
                            for label in pr.labels
                        ],
                        "additions": pr.additions,
                        "deletions": pr.deletions,
                        "changed_files": pr.changed_files,
                        "comments": pr.comments,
                        "review_comments": pr.review_comments,
                        "created_at": pr.created_at.isoformat() if pr.created_at else None,
                        "updated_at": pr.updated_at.isoformat() if pr.updated_at else None,
                        "closed_at": pr.closed_at.isoformat() if pr.closed_at else None,
                        "html_url": pr.html_url
                    }
                    result.append(pr_data)
                
                return result
                
            except GithubException as e:
                raise Exception(f"GitHub API error: {e.data.get('message', str(e))}")
        
        return await self.cache.get_or_set(cache_key, fetch_prs, ttl=120, prefix="github")
    
    async def get_user_pull_requests(
        self,
        state: str = "open",
        per_page: int = 50
    ) -> List[Dict[str, Any]]:
        """获取用户的所有 PR（跨仓库）"""
        repos = await self.get_user_repositories(per_page=30)
        
        all_prs = []
        for repo in repos:
            try:
                prs = await self.get_repository_pull_requests(
                    repo['full_name'],
                    state=state,
                    per_page=20
                )
                
                # 过滤出用户创建的 PR
                user_prs = [
                    pr for pr in prs
                    if pr['user']['login'].lower() == self.username.lower()
                ]
                
                all_prs.extend(user_prs)
            except Exception as e:
                print(f"Error fetching PRs from {repo['full_name']}: {e}")
                continue
        
        # 按更新时间排序
        all_prs.sort(key=lambda x: x['updated_at'] or '', reverse=True)
        
        return all_prs[:per_page]
    
    # ==================== 统计接口 ====================
    
    async def get_user_stats(self, days: int = 30) -> Dict[str, Any]:
        """
        获取用户统计信息
        
        Args:
            days: 统计天数
        """
        since = datetime.utcnow() - timedelta(days=days)
        
        # 获取最近的提交
        commits = await self.get_recent_commits(days=days, per_repo=50)
        
        # 统计
        stats = {
            "period_days": days,
            "commits_count": len(commits),
            "repos_contributed": list(set(
                c['repository']['full_name'] for c in commits
            )),
            "daily_commits": {},
            "languages_used": {},
            "hour_distribution": {str(h): 0 for h in range(24)}
        }
        
        # 每日提交统计
        for commit in commits:
            commit_date = commit['committer']['date'][:10] if commit['committer']['date'] else None
            if commit_date:
                stats['daily_commits'][commit_date] = stats['daily_commits'].get(commit_date, 0) + 1
            
            # 小时分布
            if commit['committer']['date']:
                hour = datetime.fromisoformat(commit['committer']['date'].replace('Z', '+00:00')).hour
                stats['hour_distribution'][str(hour)] += 1
        
        # 获取语言统计
        repos = await self.get_user_repositories(per_page=30)
        for repo in repos[:10]:  # 限制前 10 个仓库
            if repo['language']:
                stats['languages_used'][repo['language']] = stats['languages_used'].get(repo['language'], 0) + 1
        
        # 添加 PR 和 Issue 统计
        try:
            user_prs = await self.get_user_pull_requests(state="all", per_page=100)
            recent_prs = [
                pr for pr in user_prs
                if pr['created_at'] and datetime.fromisoformat(pr['created_at'].replace('Z', '+00:00')) >= since
            ]
            
            stats['prs_opened'] = len([pr for pr in recent_prs if not pr['merged'] and pr['state'] == 'open'])
            stats['prs_merged'] = len([pr for pr in recent_prs if pr['merged']])
            stats['prs_closed'] = len([pr for pr in recent_prs if not pr['merged'] and pr['state'] == 'closed'])
        except Exception as e:
            print(f"Error fetching PR stats: {e}")
            stats['prs_opened'] = 0
            stats['prs_merged'] = 0
            stats['prs_closed'] = 0
        
        return stats
    
    async def get_rate_limit_status(self) -> Dict[str, Any]:
        """获取当前速率限制状态"""
        try:
            rate_limit = self.github.get_rate_limit()
            return {
                "core": {
                    "limit": rate_limit.core.limit,
                    "remaining": rate_limit.core.remaining,
                    "reset": rate_limit.core.reset.isoformat(),
                    "used": rate_limit.core.limit - rate_limit.core.remaining
                },
                "search": {
                    "limit": rate_limit.search.limit,
                    "remaining": rate_limit.search.remaining,
                    "reset": rate_limit.search.reset.isoformat()
                },
                "graphql": {
                    "limit": rate_limit.graphql.limit if hasattr(rate_limit, 'graphql') else None,
                    "remaining": rate_limit.graphql.remaining if hasattr(rate_limit, 'graphql') else None,
                    "reset": rate_limit.graphql.reset.isoformat() if hasattr(rate_limit, 'graphql') else None
                }
            }
        except Exception as e:
            return {"error": str(e)}
    
    # ==================== 事件流接口 ====================
    
    async def get_user_events(self, per_page: int = 30) -> List[Dict[str, Any]]:
        """获取用户活动事件流"""
        try:
            user = self.github.get_user(self.username)
            events = user.get_events()
            
            result = []
            for event in events[:per_page]:
                event_data = {
                    "id": event.id,
                    "type": event.type,
                    "actor": event.actor.login if event.actor else None,
                    "repo": event.repo.name if event.repo else None,
                    "created_at": event.created_at.isoformat() if event.created_at else None,
                    "payload": event.payload
                }
                result.append(event_data)
            
            return result
            
        except GithubException as e:
            raise Exception(f"GitHub API error: {e.data.get('message', str(e))}")


# 工厂函数
def get_github_service(access_token: Optional[str] = None) -> GitHubAPIService:
    """获取 GitHub API 服务实例"""
    return GitHubAPIService(access_token)


def get_github_oauth_service() -> GitHubOAuthService:
    """获取 GitHub OAuth 服务实例"""
    return GitHubOAuthService()
