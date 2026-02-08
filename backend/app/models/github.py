from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, JSON, ForeignKey, BigInteger
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.database import Base


class GitHubToken(Base):
    """GitHub OAuth Token 存储"""
    __tablename__ = "github_tokens"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    
    # OAuth Tokens (encrypted)
    access_token_encrypted = Column(Text, nullable=False)
    refresh_token_encrypted = Column(Text, nullable=True)
    
    # Token 元数据
    token_type = Column(String(20), default="bearer")
    scope = Column(String(255), nullable=True)
    
    # 过期时间
    expires_at = Column(DateTime, nullable=True)
    
    # 速率限制信息
    rate_limit_remaining = Column(Integer, default=5000)
    rate_limit_reset_at = Column(DateTime, nullable=True)
    
    # 状态
    is_active = Column(Boolean, default=True)
    last_used_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    user = relationship("User", back_populates="github_token")


class GitHubRepository(Base):
    """GitHub 仓库缓存"""
    __tablename__ = "github_repositories"
    
    id = Column(Integer, primary_key=True, index=True)
    repo_id = Column(BigInteger, unique=True, index=True)  # GitHub's repo ID
    
    # 仓库信息
    name = Column(String(100), nullable=False)
    full_name = Column(String(200), nullable=False, index=True)
    owner = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    
    # 统计
    stars = Column(Integer, default=0)
    forks = Column(Integer, default=0)
    open_issues = Column(Integer, default=0)
    watchers = Column(Integer, default=0)
    
    # 语言和其他信息
    language = Column(String(50), nullable=True)
    languages = Column(JSON, nullable=True)  # 所有语言占比
    topics = Column(JSON, nullable=True)
    
    # 可见性
    private = Column(Boolean, default=False)
    is_fork = Column(Boolean, default=False)
    
    # 时间戳
    github_created_at = Column(DateTime, nullable=True)
    github_updated_at = Column(DateTime, nullable=True)
    last_pushed_at = Column(DateTime, nullable=True)
    
    # 缓存元数据
    fetched_at = Column(DateTime, default=datetime.utcnow)
    

class GitHubCommit(Base):
    """GitHub 提交记录缓存"""
    __tablename__ = "github_commits"
    
    id = Column(Integer, primary_key=True, index=True)
    sha = Column(String(40), unique=True, index=True)
    
    # 仓库信息
    repo_full_name = Column(String(200), nullable=False, index=True)
    
    # 提交信息
    message = Column(Text, nullable=False)
    author_name = Column(String(100))
    author_email = Column(String(100))
    author_github_id = Column(BigInteger, nullable=True)
    
    # 时间
    committed_at = Column(DateTime, nullable=False, index=True)
    
    # URL
    html_url = Column(String(500))
    
    # 统计
    additions = Column(Integer, nullable=True)
    deletions = Column(Integer, nullable=True)
    changed_files = Column(Integer, nullable=True)
    
    # 缓存元数据
    fetched_at = Column(DateTime, default=datetime.utcnow)
    
    
class GitHubPullRequest(Base):
    """GitHub PR 缓存"""
    __tablename__ = "github_pull_requests"
    
    id = Column(Integer, primary_key=True, index=True)
    pr_id = Column(BigInteger, unique=True, index=True)
    number = Column(Integer, nullable=False)
    
    # 仓库信息
    repo_full_name = Column(String(200), nullable=False, index=True)
    
    # PR 信息
    title = Column(String(500), nullable=False)
    body = Column(Text, nullable=True)
    state = Column(String(20), nullable=False)  # open, closed
    
    # 作者
    author = Column(String(100), nullable=False)
    author_id = Column(BigInteger)
    
    # 分支
    head_branch = Column(String(255))
    base_branch = Column(String(255))
    
    # 合并信息
    is_merged = Column(Boolean, default=False)
    merged_at = Column(DateTime, nullable=True)
    merged_by = Column(String(100), nullable=True)
    
    # 时间
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
    closed_at = Column(DateTime, nullable=True)
    
    # 统计
    additions = Column(Integer, default=0)
    deletions = Column(Integer, default=0)
    changed_files = Column(Integer, default=0)
    comments_count = Column(Integer, default=0)
    
    # URL
    html_url = Column(String(500))
    
    # 缓存元数据
    fetched_at = Column(DateTime, default=datetime.utcnow)


class GitHubIssue(Base):
    """GitHub Issue 缓存"""
    __tablename__ = "github_issues"
    
    id = Column(Integer, primary_key=True, index=True)
    issue_id = Column(BigInteger, unique=True, index=True)
    number = Column(Integer, nullable=False)
    
    # 仓库信息
    repo_full_name = Column(String(200), nullable=False, index=True)
    
    # Issue 信息
    title = Column(String(500), nullable=False)
    body = Column(Text, nullable=True)
    state = Column(String(20), nullable=False)  # open, closed
    state_reason = Column(String(20), nullable=True)  # completed, not_planned, reopened
    
    # 作者
    author = Column(String(100), nullable=False)
    author_id = Column(BigInteger)
    
    # 标签
    labels = Column(JSON, nullable=True)
    
    # 指派
    assignees = Column(JSON, nullable=True)
    
    # 时间
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
    closed_at = Column(DateTime, nullable=True)
    
    # 统计
    comments_count = Column(Integer, default=0)
    
    # URL
    html_url = Column(String(500))
    
    # 缓存元数据
    fetched_at = Column(DateTime, default=datetime.utcnow)


class GitHubContributionStats(Base):
    """GitHub 贡献统计"""
    __tablename__ = "github_contribution_stats"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    
    # 统计周期
    date = Column(DateTime, nullable=False, index=True)
    
    # 提交统计
    commits_count = Column(Integer, default=0)
    lines_added = Column(Integer, default=0)
    lines_deleted = Column(Integer, default=0)
    
    # PR 统计
    prs_opened = Column(Integer, default=0)
    prs_merged = Column(Integer, default=0)
    prs_closed = Column(Integer, default=0)
    
    # Issue 统计
    issues_opened = Column(Integer, default=0)
    issues_closed = Column(Integer, default=0)
    
    # 活跃的仓库
    active_repos = Column(JSON, nullable=True)
    
    # 缓存元数据
    fetched_at = Column(DateTime, default=datetime.utcnow)
