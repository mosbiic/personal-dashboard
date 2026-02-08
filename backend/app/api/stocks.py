"""
股票数据 API 路由
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from datetime import datetime

from app.services.stock_service import (
    get_stock_service,
    DEFAULT_HOLDINGS,
    MarketType
)
from app.utils.cache import get_cache

router = APIRouter()
stock_service = get_stock_service()


@router.get("/price/{symbol}")
async def get_stock_price(symbol: str):
    """
    获取单只股票实时价格
    
    支持格式:
    - A股: 002230, 600519 (自动识别)
    - 美股: AAPL, NVDA, MSFT
    - 港股: 00700, 0700.HK
    """
    data = await stock_service.get_current_price(symbol)
    
    if not data:
        raise HTTPException(
            status_code=404,
            detail=f"无法获取股票 {symbol} 的价格数据"
        )
    
    return {
        "success": True,
        "data": data
    }


@router.get("/prices")
async def get_multiple_prices(
    symbols: str = Query(..., description="逗号分隔的股票代码，如: AAPL,MSFT,NVDA")
):
    """批量获取股票价格"""
    symbol_list = [s.strip() for s in symbols.split(",")]
    
    if len(symbol_list) > 20:
        raise HTTPException(
            status_code=400,
            detail="一次最多查询20只股票"
        )
    
    prices = await stock_service.get_multiple_prices(symbol_list)
    
    return {
        "success": True,
        "count": len(prices),
        "data": prices
    }


@router.get("/history/{symbol}")
async def get_price_history(
    symbol: str,
    period: str = Query("1mo", description="时间周期: 1d, 5d, 1mo, 3mo, 6mo, 1y"),
    interval: str = Query("1d", description="时间间隔: 1m, 5m, 1h, 1d, 1wk")
):
    """获取股票历史价格数据"""
    history = await stock_service.get_price_history(symbol, period, interval)
    
    if not history:
        raise HTTPException(
            status_code=404,
            detail=f"无法获取股票 {symbol} 的历史数据"
        )
    
    return {
        "success": True,
        "symbol": symbol,
        "period": period,
        "interval": interval,
        "count": len(history),
        "data": history
    }


@router.get("/portfolio")
async def get_portfolio(
    use_default: bool = Query(True, description="使用默认持仓配置")
):
    """
    获取投资组合分析
    
    包含:
    - 各持仓盈亏计算
    - 总市值和成本
    - 总盈亏和收益率
    """
    holdings = DEFAULT_HOLDINGS if use_default else []
    
    if not holdings:
        return {
            "success": True,
            "data": {
                "holdings": [],
                "summary": {
                    "total_cost": 0,
                    "total_value": 0,
                    "total_pnl": 0,
                    "total_pnl_pct": 0,
                    "holdings_count": 0
                }
            }
        }
    
    portfolio = await stock_service.calculate_portfolio(holdings)
    
    return {
        "success": True,
        "data": portfolio
    }


@router.post("/portfolio/calculate")
async def calculate_custom_portfolio(holdings: List[dict]):
    """
    计算自定义持仓组合
    
    Request Body:
    [
        {"symbol": "AAPL", "shares": 100, "avg_cost": 150},
        {"symbol": "NVDA", "shares": 50, "avg_cost": 450}
    ]
    """
    if not holdings:
        raise HTTPException(
            status_code=400,
            detail="持仓数据不能为空"
        )
    
    if len(holdings) > 20:
        raise HTTPException(
            status_code=400,
            detail="一次最多计算20只持仓"
        )
    
    portfolio = await stock_service.calculate_portfolio(holdings)
    
    return {
        "success": True,
        "data": portfolio
    }


@router.get("/market/overview")
async def get_market_overview():
    """获取市场概览（主要指数）"""
    overview = await stock_service.get_market_overview()
    
    return {
        "success": True,
        "data": overview
    }


@router.get("/holdings")
async def get_default_holdings():
    """获取默认持仓配置"""
    # 获取当前价格
    prices = await stock_service.get_multiple_prices(
        [h['symbol'] for h in DEFAULT_HOLDINGS]
    )
    price_map = {p['symbol']: p for p in prices}
    
    holdings_with_info = []
    for holding in DEFAULT_HOLDINGS:
        symbol = holding['symbol']
        price_data = price_map.get(symbol, {})
        info = stock_service.get_stock_info(symbol)
        
        holdings_with_info.append({
            **holding,
            "name": price_data.get('name') or info['name'],
            "market": info['market'].value,
            "currency": info['currency'],
            "current_price": price_data.get('price')
        })
    
    return {
        "success": True,
        "data": holdings_with_info
    }


@router.get("/performance")
async def get_portfolio_performance(
    period: str = Query("1mo", description="分析周期: 1mo, 3mo, 6mo, 1y")
):
    """
    获取投资组合历史表现分析
    
    分析各持仓在指定周期内的表现
    """
    holdings = DEFAULT_HOLDINGS
    results = []
    
    for holding in holdings:
        symbol = holding['symbol']
        
        # 获取历史数据
        history = await stock_service.get_price_history(symbol, period)
        
        if history and len(history) > 0:
            start_price = history[0]['close']
            end_price = history[-1]['close']
            period_return = ((end_price - start_price) / start_price * 100)
            
            # 计算最大/最小值
            prices = [h['close'] for h in history]
            max_price = max(prices)
            min_price = min(prices)
            
            info = stock_service.get_stock_info(symbol)
            
            results.append({
                "symbol": symbol,
                "name": info['name'],
                "market": info['market'].value,
                "period": period,
                "start_price": round(start_price, 4),
                "end_price": round(end_price, 4),
                "period_return": round(period_return, 2),
                "max_price": round(max_price, 4),
                "min_price": round(min_price, 4),
                "volatility": round((max_price - min_price) / start_price * 100, 2),
                "data_points": len(history)
            })
    
    # 按收益率排序
    results.sort(key=lambda x: x['period_return'], reverse=True)
    
    return {
        "success": True,
        "period": period,
        "analysis_date": datetime.utcnow().isoformat(),
        "data": results
    }


@router.post("/cache/clear")
async def clear_stock_cache():
    """清除股票数据缓存（管理员用）"""
    cache = get_cache()
    deleted = await cache.delete_pattern("stock:*")
    
    return {
        "success": True,
        "message": f"已清除 {deleted} 个股票缓存条目"
    }
