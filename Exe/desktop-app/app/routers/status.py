from fastapi import APIRouter, Depends
from app.dependencies import get_current_user
from app.models import User
from app.watcher_status import get_status

router = APIRouter(tags=["watcher"])


@router.get("/watcher/status")
async def list_watcher_status(current_user: User = Depends(get_current_user)):
    return get_status()


@router.get("/watcher/status/{world_id}")
async def get_world_watcher_status(world_id: int, current_user: User = Depends(get_current_user)):
    return get_status(world_id)
