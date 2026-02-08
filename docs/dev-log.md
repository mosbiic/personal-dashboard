# 个人数据仪表盘 - 开发日志

## 2025-02-08

### 项目初始化
- [x] 创建 GitHub 仓库 (mosbiic/personal-dashboard)
- [x] 初始化项目结构
- [x] 设计数据库 schema
- [x] 创建 Trello 卡片追踪进度

### 数据库 Schema 设计
- `users` - 用户表
- `data_sources` - 数据源配置
- `activities` - 统一活动记录表
- `trello_cards` - Trello 卡片缓存
- `github_events` - GitHub 事件缓存
- `stock_holdings` - 股票持仓
- `weather_data` - 天气数据缓存

### 下一步计划
1. 配置 FastAPI 后端框架
2. 实现 Trello API 集成
3. 创建前端基础组件
4. 实现时间轴视图
