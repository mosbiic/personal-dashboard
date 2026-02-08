# Database Schema Design

## 核心表结构

### 1. users - 用户表
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 2. data_sources - 数据源配置
```sql
CREATE TABLE data_sources (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    name VARCHAR(50) NOT NULL, -- trello, github, stocks, weather
    config JSONB, -- API keys, settings
    enabled BOOLEAN DEFAULT TRUE,
    last_sync TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 3. activities - 统一活动记录表 ⭐核心
```sql
CREATE TABLE activities (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    
    -- 活动来源
    source_type VARCHAR(20) NOT NULL, -- trello, github, session, stock, weather
    source_id VARCHAR(100) NOT NULL, -- 原始ID
    
    -- 活动内容
    activity_type VARCHAR(50) NOT NULL, -- task_complete, commit, pr_merge, message, price_update
    title VARCHAR(255) NOT NULL,
    description TEXT,
    url VARCHAR(500),
    metadata JSONB, -- 灵活存储额外数据
    
    -- 时间索引
    occurred_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_user_source (user_id, source_type),
    INDEX idx_occurred_at (occurred_at)
);
```

### 4. trello_cards - Trello 卡片缓存
```sql
CREATE TABLE trello_cards (
    id SERIAL PRIMARY KEY,
    trello_id VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    list_name VARCHAR(100),
    board_name VARCHAR(100),
    labels JSONB,
    due_date TIMESTAMP,
    completed BOOLEAN DEFAULT FALSE,
    completed_at TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 5. github_events - GitHub 事件缓存
```sql
CREATE TABLE github_events (
    id SERIAL PRIMARY KEY,
    event_id VARCHAR(50) UNIQUE NOT NULL,
    event_type VARCHAR(50) NOT NULL, -- PushEvent, PullRequestEvent, IssuesEvent
    repo_name VARCHAR(100),
    actor VARCHAR(50),
    payload JSONB,
    created_at TIMESTAMP NOT NULL
);
```

### 6. stock_holdings - 股票持仓
```sql
CREATE TABLE stock_holdings (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL, -- AAPL, 00700.HK
    name VARCHAR(100),
    market VARCHAR(10) NOT NULL, -- US, HK, CN
    shares DECIMAL(12,4),
    avg_cost DECIMAL(12,4),
    current_price DECIMAL(12,4),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 7. weather_data - 天气数据缓存
```sql
CREATE TABLE weather_data (
    id SERIAL PRIMARY KEY,
    city VARCHAR(50) NOT NULL,
    temperature DECIMAL(4,1),
    feels_like DECIMAL(4,1),
    humidity INTEGER,
    description VARCHAR(100),
    icon VARCHAR(20),
    forecast JSONB,
    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 数据流设计

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Trello    │────▶│  Trello     │────▶│  activities │
│    API      │     │  Service    │     │    table    │
└─────────────┘     └─────────────┘     └─────────────┘
                                               │
┌─────────────┐     ┌─────────────┐            │
│   GitHub    │────▶│  GitHub     │───────────┤
│    API      │     │  Service    │           │
└─────────────┘     └─────────────┘           │
                                              ▼
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Stocks    │────▶│   Stock     │────▶│   Timeline  │
│    API      │     │  Service    │     │     API     │
└─────────────┘     └─────────────┘     └─────────────┘

┌─────────────┐     ┌─────────────┐           │
│   Weather   │────▶│  Weather    │───────────┤
│    API      │     │  Service    │           │
└─────────────┘     └─────────────┘           ▼
                                        ┌─────────────┐
                                        │   Frontend  │
                                        │  Dashboard  │
                                        └─────────────┘
```

## 关联分析查询示例

### 代码提交 vs Trello 完成率
```sql
SELECT 
    DATE_TRUNC('day', occurred_at) as day,
    COUNT(*) FILTER (WHERE source_type = 'github' AND activity_type = 'commit') as commits,
    COUNT(*) FILTER (WHERE source_type = 'trello' AND activity_type = 'task_complete') as tasks_completed
FROM activities
WHERE occurred_at >= NOW() - INTERVAL '7 days'
GROUP BY day
ORDER BY day;
```
