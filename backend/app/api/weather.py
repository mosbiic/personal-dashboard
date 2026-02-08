from fastapi import APIRouter, HTTPException
from typing import Optional

from app.services.weather_service import weather_service

router = APIRouter()


@router.get("/current")
async def get_current_weather(
    city: Optional[str] = None,
    lat: Optional[float] = None,
    lon: Optional[float] = None
):
    """
    获取当前天气
    
    参数:
    - city: 城市名称 (可选，默认 Jersey City)
    - lat: 纬度 (可选)
    - lon: 经度 (可选)
    """
    try:
        weather = await weather_service.get_current_weather(
            city=city, lat=lat, lon=lon
        )
        return {
            "success": True,
            "data": weather
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/forecast")
async def get_weather_forecast(
    days: int = 7,
    lat: Optional[float] = None,
    lon: Optional[float] = None
):
    """
    获取天气预报
    
    参数:
    - days: 预报天数 (默认7天)
    - lat: 纬度 (可选)
    - lon: 经度 (可选)
    """
    try:
        forecast = await weather_service.get_forecast(
            lat=lat, lon=lon, days=days
        )
        return {
            "success": True,
            "data": forecast
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search")
async def search_city(query: str):
    """
    搜索城市
    
    参数:
    - query: 城市名称
    """
    try:
        results = await weather_service.search_city(query)
        return {
            "success": True,
            "data": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
