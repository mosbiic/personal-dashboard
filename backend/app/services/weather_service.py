"""天气数据服务 - 使用 Open-Meteo API (免费，无需 API Key)"""
import httpx
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List

from app.db.database import AsyncSessionLocal
from app.db.database import WeatherData
from sqlalchemy import select


class WeatherService:
    """天气数据服务"""
    
    BASE_URL = "https://api.open-meteo.com/v1"
    GEO_URL = "https://geocoding-api.open-meteo.com/v1"
    
    # 默认城市：Jersey City, NJ (Garry 的位置)
    DEFAULT_LAT = 40.7282
    DEFAULT_LON = -74.0776
    DEFAULT_CITY = "Jersey City"
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=10.0)
    
    async def get_current_weather(
        self, 
        lat: float = None, 
        lon: float = None,
        city: str = None
    ) -> Dict[str, Any]:
        """
        获取当前天气
        
        Args:
            lat: 纬度
            lon: 经度  
            city: 城市名称 (用于缓存标识)
        """
        lat = lat or self.DEFAULT_LAT
        lon = lon or self.DEFAULT_LON
        city = city or self.DEFAULT_CITY
        
        # 检查缓存 (1小时内)
        cached = await self._get_cached_weather(city)
        if cached and (datetime.utcnow() - cached.fetched_at).seconds < 3600:
            return self._format_weather_response(cached)
        
        try:
            params = {
                "latitude": lat,
                "longitude": lon,
                "current": ["temperature_2m", "relative_humidity_2m", "apparent_temperature", 
                           "weather_code", "wind_speed_10m"],
                "daily": ["weather_code", "temperature_2m_max", "temperature_2m_min"],
                "timezone": "America/New_York"
            }
            
            response = await self.client.get(f"{self.BASE_URL}/forecast", params=params)
            response.raise_for_status()
            data = response.json()
            
            # 保存到数据库
            weather_data = await self._save_weather_data(city, data)
            
            return self._format_weather_response(weather_data)
            
        except httpx.HTTPError as e:
            # 如果有缓存，返回缓存数据
            if cached:
                return self._format_weather_response(cached)
            raise Exception(f"获取天气失败: {str(e)}")
    
    async def get_forecast(
        self,
        lat: float = None,
        lon: float = None,
        days: int = 7
    ) -> Dict[str, Any]:
        """获取天气预报"""
        lat = lat or self.DEFAULT_LAT
        lon = lon or self.DEFAULT_LON
        
        try:
            params = {
                "latitude": lat,
                "longitude": lon,
                "daily": ["weather_code", "temperature_2m_max", "temperature_2m_min", 
                         "precipitation_probability_max"],
                "timezone": "America/New_York",
                "forecast_days": days
            }
            
            response = await self.client.get(f"{self.BASE_URL}/forecast", params=params)
            response.raise_for_status()
            data = response.json()
            
            daily = data.get("daily", {})
            forecast = []
            
            for i in range(len(daily.get("time", []))):
                forecast.append({
                    "date": daily["time"][i],
                    "max_temp": daily["temperature_2m_max"][i],
                    "min_temp": daily["temperature_2m_min"][i],
                    "weather_code": daily["weather_code"][i],
                    "description": self._weather_code_to_desc(daily["weather_code"][i]),
                    "precipitation_prob": daily.get("precipitation_probability_max", [0]*7)[i]
                })
            
            return {
                "location": "Jersey City, NJ",
                "forecast": forecast
            }
            
        except httpx.HTTPError as e:
            raise Exception(f"获取预报失败: {str(e)}")
    
    async def search_city(self, query: str) -> List[Dict[str, Any]]:
        """搜索城市"""
        try:
            params = {"name": query, "count": 5}
            response = await self.client.get(f"{self.GEO_URL}/search", params=params)
            response.raise_for_status()
            data = response.json()
            
            results = []
            for result in data.get("results", []):
                results.append({
                    "name": result.get("name"),
                    "country": result.get("country"),
                    "admin1": result.get("admin1"),  # 州/省
                    "latitude": result.get("latitude"),
                    "longitude": result.get("longitude")
                })
            
            return results
            
        except httpx.HTTPError as e:
            raise Exception(f"搜索城市失败: {str(e)}")
    
    async def _get_cached_weather(self, city: str) -> Optional[WeatherData]:
        """获取缓存的天气数据"""
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(WeatherData).where(WeatherData.city == city)
                .order_by(WeatherData.fetched_at.desc())
                .limit(1)
            )
            return result.scalar()
    
    async def _save_weather_data(self, city: str, data: Dict) -> WeatherData:
        """保存天气数据到数据库"""
        current = data.get("current", {})
        daily = data.get("daily", {})
        
        # 构建预报数据
        forecast = []
        for i in range(min(7, len(daily.get("time", [])))):
            forecast.append({
                "date": daily["time"][i],
                "max_temp": daily["temperature_2m_max"][i] if i < len(daily["temperature_2m_max"]) else None,
                "min_temp": daily["temperature_2m_min"][i] if i < len(daily["temperature_2m_min"]) else None,
                "weather_code": daily["weather_code"][i] if i < len(daily["weather_code"]) else None,
                "description": self._weather_code_to_desc(daily["weather_code"][i]) if i < len(daily["weather_code"]) else "未知"
            })
        
        weather_code = current.get("weather_code", 0)
        
        weather_data = WeatherData(
            city=city,
            temperature=current.get("temperature_2m", 0),
            feels_like=current.get("apparent_temperature", 0),
            humidity=current.get("relative_humidity_2m", 0),
            description=self._weather_code_to_desc(weather_code),
            icon=self._weather_code_to_icon(weather_code),
            forecast=forecast
        )
        
        async with AsyncSessionLocal() as session:
            session.add(weather_data)
            await session.commit()
            await session.refresh(weather_data)
        
        return weather_data
    
    def _format_weather_response(self, data: WeatherData) -> Dict[str, Any]:
        """格式化天气响应"""
        return {
            "location": data.city,
            "current": {
                "temperature": data.temperature,
                "feels_like": data.feels_like,
                "humidity": data.humidity,
                "description": data.description,
                "icon": data.icon
            },
            "forecast": data.forecast,
            "fetched_at": data.fetched_at.isoformat()
        }
    
    def _weather_code_to_desc(self, code: int) -> str:
        """天气代码转描述"""
        codes = {
            0: "晴朗",
            1: "大部晴朗", 2: "多云", 3: "阴天",
            45: "雾", 48: "雾凇",
            51: "毛毛雨", 53: "中度毛毛雨", 55: "大毛毛雨",
            61: "小雨", 63: "中雨", 65: "大雨",
            71: "小雪", 73: "中雪", 75: "大雪",
            77: "雪粒",
            80: "小阵雨", 81: "中阵雨", 82: "大阵雨",
            85: "小阵雪", 86: "大阵雪",
            95: "雷雨", 96: "雷雨伴冰雹", 99: "大雷雨伴冰雹"
        }
        return codes.get(code, "未知")
    
    def _weather_code_to_icon(self, code: int) -> str:
        """天气代码转图标"""
        icons = {
            0: "☀️",
            1: "🌤️", 2: "⛅", 3: "☁️",
            45: "🌫️", 48: "🌫️",
            51: "🌦️", 53: "🌦️", 55: "🌧️",
            61: "🌧️", 63: "🌧️", 65: "🌧️",
            71: "🌨️", 73: "🌨️", 75: "🌨️",
            77: "🌨️",
            80: "🌦️", 81: "🌧️", 82: "🌧️",
            85: "🌨️", 86: "🌨️",
            95: "⛈️", 96: "⛈️", 99: "⛈️"
        }
        return icons.get(code, "❓")


# 全局实例
weather_service = WeatherService()
