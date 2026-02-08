# GitHub API 集成文档

## 概述

已实现完整的 GitHub API 集成，支持 OAuth 授权、数据获取、缓存和速率限制保护。

## 实现功能

### 1. OAuth 授权流程

- `GET /api/github/auth/login` - 获取授权 URL
- `GET /api/github/auth/callback` - OAuth 回调处理
- Token 加密存储（Fernet 加密算法）

### 2. API 端点

#### 仓库接口
- `GET /api/github/repos` - 获取用户所有仓库
  - 支持排序：created, updated, pushed, full_name
  - 支持分页（per_page: 1-100）
  - 缓存 5 分钟

#### 提交记录接口
- `GET /api/github/repos/{owner}/{repo}/commits` - 仓库提交记录
  - 支持时间范围过滤
  - 支持作者过滤
  - 缓存 3 分钟

- `GET /api/github/commits/recent` - 最近 N 天提交（跨仓库）
  - 默认最近 30 天
  - 自动聚合所有仓库

#### Issue 和 PR 接口
- `GET /api/github/repos/{owner}/{repo}/issues` - 仓库 Issues
  - 状态过滤：open, closed, all
  - 缓存 2 分钟

- `GET /api/github/repos/{owner}/{repo}/pulls` - 仓库 PRs
  - 包含合并信息
  - 缓存 2 分钟

- `GET /api/github/pulls/my` - 用户的所有 PR（跨仓库）

#### 统计接口
- `GET /api/github/stats` - 用户统计信息
  - 提交数量
  - PR 统计
  - 活跃仓库
  - 编程语言分布
  - 小时分布

#### 其他接口
- `GET /api/github/rate-limit` - API 速率限制状态
- `GET /api/github/events` - 用户活动事件流
- `POST /api/github/sync` - 触发数据同步
- `POST /api/github/cache/clear` - 清除缓存

### 3. 技术特性

#### 速率限制保护
- 每小时 5000 请求限制
- 自动检测和等待重置
- 响应头信息跟踪

#### Redis 缓存
- 默认 TTL: 5 分钟
- 支持强制刷新
- 模式匹配删除

#### 加密存储
- Fernet 对称加密
- 支持从密码生成密钥
- Token 安全存储

## 配置

复制 `.env.example` 到 `.env` 并配置：

```env
# GitHub OAuth App
GITHUB_CLIENT_ID=your_github_client_id
GITHUB_CLIENT_SECRET=your_github_client_secret
GITHUB_REDIRECT_URI=http://localhost:5173/auth/github/callback

# 备用 Token
GITHUB_TOKEN=your_github_personal_access_token
GITHUB_USERNAME=your_github_username

# 加密密钥（可选，自动生成）
ENCRYPTION_KEY=
```

## 测试

```bash
# 运行所有测试
cd backend
python3 -m pytest tests/test_github.py -v

# 运行非集成测试
python3 -m pytest tests/test_github.py -v -k "not integration"
```

测试结果：21 个测试全部通过

## 数据库模型

新增表：
- `github_tokens` - OAuth Token 存储
- `github_repositories` - 仓库缓存
- `github_commits` - 提交记录缓存
- `github_pull_requests` - PR 缓存
- `github_issues` - Issue 缓存
- `github_contribution_stats` - 贡献统计

## 依赖

新增依赖：
- PyGithub==2.2.0 - GitHub API SDK
- cryptography==42.0.0 - 加密
- redis==5.0.1 - 缓存
- gql==3.5.0 - GraphQL（预留）

## 注意事项

1. GitHub OAuth App 需要设置回调 URL
2. 生产环境必须设置 ENCRYPTION_KEY
3. Redis 需要单独部署或使用云服务
4. Token 过期需要重新授权（GitHub 不支持刷新令牌）
