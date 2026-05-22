import threading
from datetime import datetime, UTC

_status = {}
_lock = threading.Lock()


def set_status(world_id: int, world_name: str, status: str, message: str):
    with _lock:
        _status[world_id] = {
            "world_id": world_id,
            "world_name": world_name,
            "status": status,
            "message": message,
            "updated_at": datetime.now(UTC).isoformat(),
        }


def get_status(world_id: int = None):
    with _lock:
        if world_id is not None:
            entry = _status.get(world_id)
            if entry:
                return entry
            return {"world_id": world_id, "status": "idle", "message": "Idle", "updated_at": None}
        return list(_status.values())
