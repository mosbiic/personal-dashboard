"""
GitHub API 集成测试
"""

import pytest
import pytest_asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
import json

from app.services.github_service import (
    GitHubAPIService,
    GitHubOAuthService,
    GitHubRateLimiter,
    get_github_service,
    get_github_oauth_service
)
from app.utils.encryption import TokenEncryption, get_encryption
from app.utils.cache import RedisCache, get_cache, cached


# ==================== 测试加密工具 ====================

class TestTokenEncryption:
    """测试 Token 加密"""
    
    def test_generate_key(self):
        """测试密钥生成"""
        key = TokenEncryption.generate_key()
        assert isinstance(key, str)
        assert len(key) > 0
    
    def test_encrypt_decrypt(self):
        """测试加密解密"""
        encryption = TokenEncryption()
        original = "test_token_12345"
        
        encrypted = encryption.encrypt(original)
        assert encrypted != original
        assert isinstance(encrypted, str)
        
        decrypted = encryption.decrypt(encrypted)
        assert decrypted == original
    
    def test_encrypt_dict(self):
        """测试字典加密"""
        encryption = TokenEncryption()
        data = {"access_token": "token123", "refresh_token": "refresh456"}
        
        encrypted = encryption.encrypt_dict(data)
        decrypted = encryption.decrypt_dict(encrypted)
        
        assert decrypted == data
    
    def test_empty_string(self):
        """测试空字符串处理"""
        encryption = TokenEncryption()
        assert encryption.encrypt("") == ""
        assert encryption.decrypt("") == ""
    
    def test_from_password(self):
        """测试从密码生成密钥"""
        password = "my_secure_password"
        enc1, salt = TokenEncryption.from_password(password)
        enc2, _ = TokenEncryption.from_password(password, salt)
        
        data = "test_data"
        encrypted = enc1.encrypt(data)
        decrypted = enc2.decrypt(encrypted)
        
        assert decrypted == data


# ==================== 测试速率限制管理器 ====================

class TestGitHubRateLimiter:
    """测试速率限制管理器"""
    
    def test_initial_state(self):
        """测试初始状态"""
        limiter = GitHubRateLimiter()
        assert limiter.remaining == 5000
        assert limiter.reset_at is None
        assert not limiter.is_rate_limited()
    
    def test_update_from_headers(self):
        """测试从响应头更新"""
        limiter = GitHubRateLimiter()
        reset_time = int(datetime.utcnow().timestamp()) + 3600
        
        headers = {
            'x-ratelimit-remaining': '100',
            'x-ratelimit-reset': str(reset_time)
        }
        
        limiter.update_from_headers(headers)
        
        assert limiter.remaining == 100
        assert limiter.reset_at is not None
    
    def test_is_rate_limited(self):
        """测试速率限制检测"""
        limiter = GitHubRateLimiter()
        limiter.remaining = 0
        assert limiter.is_rate_limited()
        
        limiter.remaining = 10
        assert not limiter.is_rate_limited()


# ==================== 测试 OAuth 服务 ====================

class TestGitHubOAuthService:
    """测试 GitHub OAuth 服务"""
    
    @pytest.mark.asyncio
    async def test_get_authorization_url(self):
        """测试生成授权 URL"""
        service = get_github_oauth_service()
        
        # 如果没有配置 client_id，应该返回基本 URL
        url = service.get_authorization_url(state="test_state")
        
        assert "github.com/login/oauth/authorize" in url
        assert "client_id=" in url
        assert "redirect_uri=" in url
        assert "scope=" in url
        assert "response_type=" in url
    
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient.post')
    async def test_exchange_code_for_token(self, mock_post):
        """测试交换授权码"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "access_token": "test_token",
            "token_type": "bearer",
            "scope": "repo"
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        service = get_github_oauth_service()
        result = await service.exchange_code_for_token("test_code")
        
        assert result["access_token"] == "test_token"
        assert result["token_type"] == "bearer"
    
    def test_encrypt_decrypt_token(self):
        """测试令牌加密解密"""
        service = get_github_oauth_service()
        token = "gho_testtoken123"
        
        encrypted = service.encrypt_token(token)
        decrypted = service.decrypt_token(encrypted)
        
        assert encrypted != token
        assert decrypted == token


# ==================== 测试 GitHub API 服务 ====================

class TestGitHubAPIService:
    """测试 GitHub API 服务"""
    
    @patch('app.services.github_service.Github')
    def test_init_with_token(self, mock_github):
        """测试使用令牌初始化"""
        mock_instance = Mock()
        mock_instance.get_user.return_value.login = "testuser"
        mock_github.return_value = mock_instance
        
        service = GitHubAPIService("test_token")
        
        assert service.token == "test_token"
        mock_github.assert_called_once_with("test_token", per_page=100)
    
    @patch('app.services.github_service.Github')
    def test_init_without_token_raises(self, mock_github):
        """测试无令牌时抛出异常"""
        with patch('app.services.github_service.settings') as mock_settings:
            mock_settings.GITHUB_TOKEN = ""
            with pytest.raises(ValueError, match="GitHub token is required"):
                GitHubAPIService()
    
    @patch('app.services.github_service.Github')
    def test_username_property(self, mock_github):
        """测试用户名属性"""
        mock_instance = Mock()
        mock_user = Mock()
        mock_user.login = "testuser"
        mock_instance.get_user.return_value = mock_user
        mock_github.return_value = mock_instance
        
        service = GitHubAPIService("test_token")
        assert service.username == "testuser"
    
    @pytest.mark.asyncio
    @patch('app.services.github_service.Github')
    async def test_get_user_repositories(self, mock_github):
        """测试获取用户仓库"""
        # Mock 设置
        mock_instance = Mock()
        mock_user = Mock()
        
        # 创建模拟仓库
        mock_repo = Mock()
        mock_repo.id = 123
        mock_repo.name = "test-repo"
        mock_repo.full_name = "user/test-repo"
        mock_repo.owner.login = "user"
        mock_repo.description = "Test repository"
        mock_repo.private = False
        mock_repo.fork = False
        mock_repo.html_url = "https://github.com/user/test-repo"
        mock_repo.created_at = datetime.utcnow()
        mock_repo.updated_at = datetime.utcnow()
        mock_repo.pushed_at = datetime.utcnow()
        mock_repo.homepage = ""
        mock_repo.size = 100
        mock_repo.stargazers_count = 10
        mock_repo.watchers_count = 10
        mock_repo.language = "Python"
        mock_repo.forks_count = 5
        mock_repo.open_issues_count = 2
        mock_repo.default_branch = "main"
        mock_repo.topics = ["python", "test"]
        mock_repo.archived = False
        mock_repo.disabled = False
        
        mock_user.get_repos.return_value = [mock_repo]
        mock_instance.get_user.return_value = mock_user
        mock_github.return_value = mock_instance
        
        service = GitHubAPIService("test_token")
        repos = await service.get_user_repositories(per_page=10)
        
        assert len(repos) == 1
        assert repos[0]["name"] == "test-repo"
        assert repos[0]["language"] == "Python"
    
    @pytest.mark.asyncio
    @patch('app.services.github_service.Github')
    async def test_get_repository_commits(self, mock_github):
        """测试获取仓库提交"""
        mock_instance = Mock()
        mock_repo = Mock()
        
        # 创建模拟提交
        mock_commit = Mock()
        mock_commit.sha = "abc123def456"
        mock_commit.commit.message = "Test commit message"
        mock_commit.commit.author.name = "Test Author"
        mock_commit.commit.author.email = "test@example.com"
        mock_commit.commit.author.date = datetime.utcnow()
        mock_commit.commit.committer.name = "Test Committer"
        mock_commit.commit.committer.email = "committer@example.com"
        mock_commit.commit.committer.date = datetime.utcnow()
        mock_commit.author = Mock(login="testuser")
        mock_commit.committer = Mock(login="testuser")
        mock_commit.html_url = "https://github.com/user/repo/commit/abc123"
        
        mock_repo.get_commits.return_value = [mock_commit]
        mock_instance.get_repo.return_value = mock_repo
        mock_github.return_value = mock_instance
        
        service = GitHubAPIService("test_token")
        since = datetime.utcnow() - timedelta(days=7)
        commits = await service.get_repository_commits("user/repo", since=since)
        
        assert len(commits) == 1
        assert commits[0]["sha"] == "abc123def456"
        assert commits[0]["message"] == "Test commit message"
    
    @pytest.mark.asyncio
    @patch('app.services.github_service.Github')
    async def test_get_repository_issues(self, mock_github):
        """测试获取仓库 Issues"""
        mock_instance = Mock()
        mock_repo = Mock()
        
        # 创建模拟 Issue
        mock_issue = Mock()
        mock_issue.id = 123
        mock_issue.number = 1
        mock_issue.title = "Test Issue"
        mock_issue.body = "Issue description"
        mock_issue.state = "open"
        mock_issue.state_reason = None
        mock_issue.user = Mock(login="testuser", id=1, avatar_url="")
        mock_issue.labels = []
        mock_issue.assignees = []
        mock_issue.milestone = None
        mock_issue.comments = 0
        mock_issue.created_at = datetime.utcnow()
        mock_issue.updated_at = datetime.utcnow()
        mock_issue.closed_at = None
        mock_issue.html_url = "https://github.com/user/repo/issues/1"
        mock_issue.pull_request = None  # 确保不是 PR
        
        mock_repo.get_issues.return_value = [mock_issue]
        mock_instance.get_repo.return_value = mock_repo
        mock_github.return_value = mock_instance
        
        service = GitHubAPIService("test_token")
        issues = await service.get_repository_issues("user/repo")
        
        assert len(issues) == 1
        assert issues[0]["title"] == "Test Issue"
        assert issues[0]["state"] == "open"
    
    @pytest.mark.asyncio
    @patch('app.services.github_service.Github')
    async def test_get_repository_pull_requests(self, mock_github):
        """测试获取仓库 PR"""
        mock_instance = Mock()
        mock_repo = Mock()
        
        # 创建模拟 PR
        mock_pr = Mock()
        mock_pr.id = 456
        mock_pr.number = 2
        mock_pr.title = "Test PR"
        mock_pr.body = "PR description"
        mock_pr.state = "open"
        mock_pr.user = Mock(login="testuser", id=1, avatar_url="")
        mock_pr.head = Mock(ref="feature", sha="abc123", repo=Mock(full_name="user/repo"))
        mock_pr.base = Mock(ref="main", sha="def456", repo=Mock(full_name="user/repo"))
        mock_pr.is_merged.return_value = False
        mock_pr.mergeable = True
        mock_pr.merged_by = None
        mock_pr.merged_at = None
        mock_pr.draft = False
        mock_pr.labels = []
        mock_pr.additions = 10
        mock_pr.deletions = 5
        mock_pr.changed_files = 2
        mock_pr.comments = 0
        mock_pr.review_comments = 0
        mock_pr.created_at = datetime.utcnow()
        mock_pr.updated_at = datetime.utcnow()
        mock_pr.closed_at = None
        mock_pr.html_url = "https://github.com/user/repo/pull/2"
        
        mock_repo.get_pulls.return_value = [mock_pr]
        mock_instance.get_repo.return_value = mock_repo
        mock_github.return_value = mock_instance
        
        service = GitHubAPIService("test_token")
        prs = await service.get_repository_pull_requests("user/repo")
        
        assert len(prs) == 1
        assert prs[0]["title"] == "Test PR"
        assert prs[0]["state"] == "open"


# ==================== 测试缓存 ====================

class TestCache:
    """测试缓存功能"""
    
    @pytest.mark.asyncio
    async def test_cache_key_generation(self):
        """测试缓存 key 生成"""
        cache = RedisCache()
        
        key1 = cache.cache_key("repos", "updated", per_page=30)
        key2 = cache.cache_key("repos", "updated", per_page=30)
        key3 = cache.cache_key("repos", "created", per_page=30)
        
        assert key1 == key2
        assert key1 != key3
        assert len(key1) == 32  # MD5 哈希长度
    
    @pytest.mark.asyncio
    async def test_make_key_with_prefix(self):
        """测试带前缀的 key 生成"""
        cache = RedisCache()
        
        key = cache._make_key("repos:list", "github")
        assert key == "github:repos:list"


# ==================== 测试装饰器 ====================

class TestDecorators:
    """测试装饰器"""
    
    @pytest.mark.asyncio
    @patch('app.utils.cache.get_cache')
    async def test_cached_decorator(self, mock_get_cache):
        """测试缓存装饰器"""
        # 创建 AsyncMock 用于异步方法
        mock_cache = Mock()
        mock_cache.cache_key = Mock(return_value="test_key")
        mock_cache.get = AsyncMock(return_value=None)  # 模拟缓存未命中
        mock_cache.set = AsyncMock(return_value=True)
        mock_get_cache.return_value = mock_cache
        
        call_count = 0
        
        @cached(ttl=300, prefix="test")
        async def test_function(x, y):
            nonlocal call_count
            call_count += 1
            return x + y
        
        result = await test_function(1, 2)
        
        assert result == 3
        assert call_count == 1
        mock_cache.set.assert_called_once()


# ==================== 集成测试 ====================

@pytest.mark.integration
class TestGitHubIntegration:
    """GitHub API 集成测试（需要真实 token）"""
    
    @pytest.fixture
    def github_service(self):
        """创建 GitHub 服务实例"""
        import os
        token = os.getenv("GITHUB_TEST_TOKEN")
        if not token:
            pytest.skip("GITHUB_TEST_TOKEN not set")
        return GitHubAPIService(token)
    
    @pytest.mark.asyncio
    async def test_get_rate_limit(self, github_service):
        """测试获取速率限制"""
        rate_limit = await github_service.get_rate_limit_status()
        
        assert "core" in rate_limit
        assert "limit" in rate_limit["core"]
        assert "remaining" in rate_limit["core"]
    
    @pytest.mark.asyncio
    async def test_get_user_repositories_real(self, github_service):
        """真实测试获取用户仓库"""
        repos = await github_service.get_user_repositories(per_page=5)
        
        assert isinstance(repos, list)
        if repos:
            assert "id" in repos[0]
            assert "name" in repos[0]
            assert "full_name" in repos[0]


# ==================== 运行测试 ====================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
