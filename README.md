# 个人数据全景仪表盘 (Personal Data Dashboard)

整合多数据源的个人数据仪表盘，提供统一时间轴视图和数据关联分析。

## 功能特性

- 📋 **Trello** - 任务追踪与完成统计
- 🐙 **GitHub** - 代码提交、PR、Issues 监控
- 📈 **虚拟股票** - A股+美股盈亏追踪
- 🌤️ **天气** - 当前天气与预报
- 💬 **Session Browser** - 对话统计分析

## 技术栈

- **后端**: FastAPI + Python 3.11+
- **前端**: Vue 3 + Tailwind CSS
- **数据库**: PostgreSQL
- **部署**: Cloudflare Tunnel

## 项目结构

```
personal-dashboard/
├── backend/          # FastAPI 后端
├── frontend/         # Vue 3 前端
├── docs/             # 文档
├── scripts/          # 部署和维护脚本
└── README.md
```

## 快速开始

### 后端

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

### 前端

```bash
cd frontend
npm install
npm run dev
```

## 环境变量

复制 `.env.example` 到 `.env` 并填写配置：

```bash
# 数据库
DATABASE_URL=postgresql://user:pass@localhost/dashboard

# API Keys
TRELLO_API_KEY=xxx
TRELLO_TOKEN=xxx
GITHUB_TOKEN=xxx
OPENWEATHER_API_KEY=xxx
```

## 许可证

MIT
