"""
股票数据服务
- A股/港股/美股行情数据获取
- 持仓盈亏计算
- 历史价格缓存
- 使用 yfinance 作为数据源
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from decimal import Decimal, ROUND_HALF_UP
from dataclasses import dataclass
from enum import Enum

from app.core.config import get_settings
from app.utils.cache import get_cache, cached

settings = get_settings()


class MarketType(str, Enum):
    """市场类型"""
    US = "US"      # 美股
    CN = "CN"      # A股
    HK = "HK"      # 港股


@dataclass
class StockHolding:
    """持仓数据模型"""
    symbol: str
    name: str
    market: MarketType
    shares: float
    avg_cost: float
    currency: str = "USD"
    
    @property
    def market_value(self, current_price: float = 0) -> float:
        """市值"""
        return self.shares * current_price
    
    def calculate_pnl(self, current_price: float) -> Dict[str, float]:
        """计算盈亏"""
        cost_basis = self.shares * self.avg_cost
        market_value = self.shares * current_price
        pnl = market_value - cost_basis
        pnl_pct = (pnl / cost_basis * 100) if cost_basis > 0 else 0
        
        return {
            "cost_basis": round(cost_basis, 2),
            "market_value": round(market_value, 2),
            "pnl": round(pnl, 2),
            "pnl_pct": round(pnl_pct, 2)
        }


class StockDataService:
    """股票数据服务"""
    
    # 股票代码映射
    SYMBOL_MAP = {
        # A股 - 需要添加后缀
        "002230": "002230.SZ",      # 科大讯飞 - 深交所
        "600519": "600519.SS",      # 贵州茅台 - 上交所
        "000001": "000001.SZ",      # 平安银行
        
        # 美股 - 直接使用
        "AAPL": "AAPL",
        "MSFT": "MSFT",
        "NVDA": "NVDA",
        "TSLA": "TSLA",
        "GOOGL": "GOOGL",
        "AMZN": "AMZN",
        "META": "META",
        
        # 港股 - 需要转换格式
        "00700": "0700.HK",         # 腾讯控股
        "01810": "1810.HK",         # 小米集团
        "09988": "9988.HK",         # 阿里巴巴
    }
    
    # 股票信息映射
    STOCK_INFO = {
        "002230.SZ": {"name": "科大讯飞", "market": MarketType.CN, "currency": "CNY"},
        "600519.SS": {"name": "贵州茅台", "market": MarketType.CN, "currency": "CNY"},
        "000001.SZ": {"name": "平安银行", "market": MarketType.CN, "currency": "CNY"},
        "AAPL": {"name": "Apple Inc.", "market": MarketType.US, "currency": "USD"},
        "MSFT": {"name": "Microsoft Corp.", "market": MarketType.US, "currency": "USD"},
        "NVDA": {"name": "NVIDIA Corp.", "market": MarketType.US, "currency": "USD"},
        "TSLA": {"name": "Tesla Inc.", "market": MarketType.US, "currency": "USD"},
        "GOOGL": {"name": "Alphabet Inc.", "market": MarketType.US, "currency": "USD"},
        "AMZN": {"name": "Amazon.com Inc.", "market": MarketType.US, "currency": "USD"},
        "META": {"name": "Meta Platforms", "market": MarketType.US, "currency": "USD"},
        "0700.HK": {"name": "腾讯控股", "market": MarketType.HK, "currency": "HKD"},
        "1810.HK": {"name": "小米集团", "market": MarketType.HK, "currency": "HKD"},
        "9988.HK": {"name": "阿里巴巴", "market": MarketType.HK, "currency": "HKD"},
    }
    
    def __init__(self):
        self.cache = get_cache()
    
    def normalize_symbol(self, symbol: str) -> str:
        """标准化股票代码"""
        symbol = symbol.upper().strip()
        
        # 如果已经在映射中，直接返回
        if symbol in self.SYMBOL_MAP.values():
            return symbol
        
        # 从映射中查找
        if symbol in self.SYMBOL_MAP:
            return self.SYMBOL_MAP[symbol]
        
        # 智能识别
        # 纯数字6位 -> A股
        if symbol.isdigit() and len(symbol) == 6:
            if symbol.startswith(('600', '601', '603', '605', '688')):
                return f"{symbol}.SS"  # 上交所
            else:
                return f"{symbol}.SZ"  # 深交所
        
        # 纯数字5位 -> 港股
        if symbol.isdigit() and len(symbol) == 5:
            return f"0{symbol}.HK"
        
        # 纯数字4位 -> 港股（补零）
        if symbol.isdigit() and len(symbol) == 4:
            return f"0{symbol}.HK"
        
        # 默认当作美股处理
        return symbol
    
    def get_stock_info(self, symbol: str) -> Dict[str, Any]:
        """获取股票信息"""
        normalized = self.normalize_symbol(symbol)
        return self.STOCK_INFO.get(normalized, {
            "name": symbol,
            "market": MarketType.US,
            "currency": "USD"
        })
    
    @cached(ttl=300, prefix="stock:price")  # 5分钟缓存
    async def get_current_price(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        获取当前股价
        
        Args:
            symbol: 股票代码（支持多种格式）
        
        Returns:
            包含价格信息的字典
        """
        try:
            ticker_symbol = self.normalize_symbol(symbol)
            ticker = yf.Ticker(ticker_symbol)
            
            # 获取实时数据
            info = ticker.info
            
            if not info:
                return None
            
            # 提取关键价格信息
            current_price = info.get('currentPrice') or info.get('regularMarketPrice') or info.get('previousClose')
            previous_close = info.get('previousClose') or info.get('regularMarketPreviousClose')
            
            if current_price is None:
                # 尝试获取历史数据作为备选
                hist = ticker.history(period="1d")
                if not hist.empty:
                    current_price = hist['Close'].iloc[-1]
                    previous_close = hist['Close'].iloc[-1]
            
            if current_price is None:
                return None
            
            # 计算涨跌幅
            change = current_price - previous_close if previous_close else 0
            change_pct = (change / previous_close * 100) if previous_close else 0
            
            stock_info = self.get_stock_info(symbol)
            
            return {
                "symbol": symbol,
                "ticker": ticker_symbol,
                "name": info.get('shortName') or info.get('longName') or stock_info['name'],
                "market": stock_info['market'].value,
                "currency": info.get('currency') or stock_info['currency'],
                "price": round(current_price, 4),
                "previous_close": round(previous_close, 4) if previous_close else None,
                "change": round(change, 4),
                "change_pct": round(change_pct, 2),
                "volume": info.get('volume') or info.get('regularMarketVolume'),
                "day_high": info.get('dayHigh') or info.get('regularMarketDayHigh'),
                "day_low": info.get('dayLow') or info.get('regularMarketDayLow'),
                "fifty_two_week_high": info.get('fiftyTwoWeekHigh'),
                "fifty_two_week_low": info.get('fiftyTwoWeekLow'),
                "market_cap": info.get('marketCap'),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            print(f"Error fetching price for {symbol}: {e}")
            return None
    
    @cached(ttl=600, prefix="stock:history")  # 10分钟缓存
    async def get_price_history(
        self,
        symbol: str,
        period: str = "1mo",
        interval: str = "1d"
    ) -> Optional[List[Dict[str, Any]]]:
        """
        获取历史价格数据
        
        Args:
            symbol: 股票代码
            period: 周期 (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
            interval: 间隔 (1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo)
        """
        try:
            ticker_symbol = self.normalize_symbol(symbol)
            ticker = yf.Ticker(ticker_symbol)
            
            hist = ticker.history(period=period, interval=interval)
            
            if hist.empty:
                return None
            
            result = []
            for date, row in hist.iterrows():
                result.append({
                    "date": date.isoformat(),
                    "open": round(row['Open'], 4),
                    "high": round(row['High'], 4),
                    "low": round(row['Low'], 4),
                    "close": round(row['Close'], 4),
                    "volume": int(row['Volume'])
                })
            
            return result
            
        except Exception as e:
            print(f"Error fetching history for {symbol}: {e}")
            return None
    
    async def get_multiple_prices(self, symbols: List[str]) -> List[Dict[str, Any]]:
        """批量获取多个股票价格"""
        import asyncio
        
        tasks = [self.get_current_price(symbol) for symbol in symbols]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        return [
            r for r in results 
            if isinstance(r, dict) and r is not None
        ]
    
    async def calculate_portfolio(
        self,
        holdings: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        计算投资组合
        
        Args:
            holdings: 持仓列表 [{"symbol": "AAPL", "shares": 100, "avg_cost": 150}]
        
        Returns:
            组合分析结果
        """
        portfolio = []
        total_cost = 0
        total_value = 0
        
        symbols = [h['symbol'] for h in holdings]
        prices = await self.get_multiple_prices(symbols)
        price_map = {p['symbol']: p for p in prices}
        
        for holding in holdings:
            symbol = holding['symbol']
            shares = holding.get('shares', 0)
            avg_cost = holding.get('avg_cost', 0)
            
            price_data = price_map.get(symbol)
            if not price_data:
                continue
            
            current_price = price_data['price']
            cost_basis = shares * avg_cost
            market_value = shares * current_price
            pnl = market_value - cost_basis
            pnl_pct = (pnl / cost_basis * 100) if cost_basis > 0 else 0
            
            stock_info = self.get_stock_info(symbol)
            
            portfolio.append({
                "symbol": symbol,
                "name": price_data.get('name') or stock_info['name'],
                "market": price_data.get('market') or stock_info['market'].value,
                "currency": price_data.get('currency') or stock_info['currency'],
                "shares": shares,
                "avg_cost": round(avg_cost, 4),
                "current_price": current_price,
                "price_change_pct": price_data.get('change_pct', 0),
                "cost_basis": round(cost_basis, 2),
                "market_value": round(market_value, 2),
                "pnl": round(pnl, 2),
                "pnl_pct": round(pnl_pct, 2)
            })
            
            total_cost += cost_basis
            total_value += market_value
        
        total_pnl = total_value - total_cost
        total_pnl_pct = (total_pnl / total_cost * 100) if total_cost > 0 else 0
        
        # 按盈亏排序
        portfolio.sort(key=lambda x: x['pnl'], reverse=True)
        
        return {
            "holdings": portfolio,
            "summary": {
                "total_cost": round(total_cost, 2),
                "total_value": round(total_value, 2),
                "total_pnl": round(total_pnl, 2),
                "total_pnl_pct": round(total_pnl_pct, 2),
                "holdings_count": len(portfolio),
                "updated_at": datetime.utcnow().isoformat()
            }
        }
    
    async def get_market_overview(self) -> Dict[str, Any]:
        """获取市场概览"""
        # 主要指数
        indices = {
            "^GSPC": {"name": "标普500", "market": "US"},
            "^DJI": {"name": "道琼斯", "market": "US"},
            "^IXIC": {"name": "纳斯达克", "market": "US"},
            "^HSI": {"name": "恒生指数", "market": "HK"},
            "000001.SS": {"name": "上证指数", "market": "CN"},
            "399001.SZ": {"name": "深证成指", "market": "CN"},
        }
        
        results = []
        for symbol, info in indices.items():
            try:
                data = await self.get_current_price(symbol)
                if data:
                    data['name'] = info['name']
                    data['market'] = info['market']
                    results.append(data)
            except Exception as e:
                print(f"Error fetching index {symbol}: {e}")
        
        return {
            "indices": results,
            "updated_at": datetime.utcnow().isoformat()
        }


# 工厂函数
def get_stock_service() -> StockDataService:
    """获取股票数据服务实例"""
    return StockDataService()


# 默认持仓配置（可以改为从数据库读取）
DEFAULT_HOLDINGS = [
    # A股
    {"symbol": "002230", "shares": 500, "avg_cost": 45.50},    # 科大讯飞
    
    # 美股
    {"symbol": "NVDA", "shares": 50, "avg_cost": 450.00},      # NVIDIA
    {"symbol": "MSFT", "shares": 30, "avg_cost": 380.00},      # Microsoft
    {"symbol": "AAPL", "shares": 100, "avg_cost": 175.00},     # Apple
]
