from fastapi import APIRouter

router = APIRouter()

@router.get("/holdings")
async def get_holdings():
    return {"message": "Stocks API - 待实现"}

@router.get("/performance")
async def get_performance():
    return {"message": "Stocks performance - 待实现"}
