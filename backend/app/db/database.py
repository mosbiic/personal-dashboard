from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float, Text, JSON, ForeignKey, create_engine, BigInteger, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from datetime import datetime

from app.core.config import get_settings

settings = get_settings()

# 使用 asyncpg 驱动
DATABASE_URL = settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

engine = create_async_engine(DATABASE_URL, echo=settings.DEBUG)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True)
    email = Column(String(100), unique=True, index=True)
    github_id = Column(String(50), unique=True, nullable=True)
    avatar_url = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    data_sources = relationship("DataSource", back_populates="user")
    activities = relationship("Activity", back_populates="user")
    github_token = relationship("GitHubToken", back_populates="user", uselist=False)


class DataSource(Base):
    __tablename__ = "data_sources"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    name = Column(String(50))  # trello, github, stocks, weather
    config = Column(JSON)  # API keys, board IDs, etc.
    enabled = Column(Boolean, default=True)
    last_sync = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="data_sources")


class Activity(Base):
    """统一活动记录表 - 所有数据源的活动都归一化到这里"""
    __tablename__ = "activities"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    
    # 活动来源
    source_type = Column(String(20))  # trello, github, session, stock, weather
    source_id = Column(String(100))  # 原始 ID
    
    # 活动内容
    activity_type = Column(String(50))  # task_complete, commit, pr_merge, message, price_update
    title = Column(String(255))
    description = Column(Text, nullable=True)
    url = Column(String(500), nullable=True)
    metadata = Column(JSON, nullable=True)  # 额外数据
    
    # 时间
    occurred_at = Column(DateTime, index=True)  # 实际发生时间
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="activities")


class TrelloCard(Base):
    """Trello 卡片缓存"""
    __tablename__ = "trello_cards"
    
    id = Column(Integer, primary_key=True, index=True)
    trello_id = Column(String(50), unique=True, index=True)
    name = Column(String(255))
    description = Column(Text, nullable=True)
    list_name = Column(String(100))
    board_name = Column(String(100))
    labels = Column(JSON)
    due_date = Column(DateTime, nullable=True)
    completed = Column(Boolean, default=False)
    completed_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow)


# 导入 GitHub 模型
from app.models.github import (
    GitHubToken,
    GitHubRepository,
    GitHubCommit,
    GitHubPullRequest,
    GitHubIssue,
    GitHubContributionStats
)


class StockHolding(Base):
    """股票持仓"""
    __tablename__ = "stock_holdings"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), index=True)  # AAPL, 00700.HK
    name = Column(String(100))
    market = Column(String(10))  # US, HK, CN
    shares = Column(Float)
    avg_cost = Column(Float)
    current_price = Column(Float)
    is_virtual = Column(Boolean, default=True)  # 虚拟持仓 vs 真实持仓
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class StockPriceHistory(Base):
    """股票价格历史记录"""
    __tablename__ = "stock_price_history"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), index=True)
    name = Column(String(100))
    market = Column(String(10))  # US, HK, CN
    currency = Column(String(10))

    # 价格数据
    price = Column(Float)
    previous_close = Column(Float, nullable=True)
    change = Column(Float, nullable=True)
    change_pct = Column(Float, nullable=True)

    # 当日数据
    day_high = Column(Float, nullable=True)
    day_low = Column(Float, nullable=True)
    volume = Column(BigInteger, nullable=True)

    # 52周数据
    fifty_two_week_high = Column(Float, nullable=True)
    fifty_two_week_low = Column(Float, nullable=True)

    # 其他数据
    market_cap = Column(BigInteger, nullable=True)

    # 记录时间
    recorded_at = Column(DateTime, default=datetime.utcnow, index=True)

    class Config:
        # 复合索引用于快速查询
        __table_args__ = (
            Index('idx_symbol_recorded', 'symbol', 'recorded_at'),
        )


class WeatherData(Base):
    """天气数据缓存"""
    __tablename__ = "weather_data"
    
    id = Column(Integer, primary_key=True, index=True)
    city = Column(String(50))
    temperature = Column(Float)
    feels_like = Column(Float)
    humidity = Column(Integer)
    description = Column(String(100))
    icon = Column(String(20))
    forecast = Column(JSON)  # 未来几天预报
    fetched_at = Column(DateTime, default=datetime.utcnow)


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
