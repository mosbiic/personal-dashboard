from fastapi import APIRouter

router = APIRouter()

@router.get("/current")
async def get_current_weather():
    return {"message": "Weather API - 待实现"}

@router.get("/forecast")
async def get_weather_forecast():
    return {"message": "Weather forecast - 待实现"}
