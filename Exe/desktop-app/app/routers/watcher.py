from fastapi import APIRouter, Depends
from app.dependencies import get_current_user
from app.models import User
from app.watcher_events import trigger_resync

router = APIRouter(tags=["watcher"])


@router.post("/watcher/resync")
async def resync_watcher(current_user: User = Depends(get_current_user)):
    trigger_resync()
    return {"message": "Watcher resync triggered"}
