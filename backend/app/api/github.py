from fastapi import APIRouter

router = APIRouter()

@router.get("/events")
async def get_github_events():
    return {"message": "GitHub API - 待实现"}

@router.post("/sync")
async def sync_github():
    return {"message": "GitHub sync - 待实现"}
