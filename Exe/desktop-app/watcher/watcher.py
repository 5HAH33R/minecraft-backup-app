import time
import threading
import logging
from pathlib import Path
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from app.watcher_status import set_status

logger = logging.getLogger("minecraft-backup.watcher")


class WorldWatcher(FileSystemEventHandler):
    def __init__(self, world_path, world_id, on_backup_callback, lock=None):
        self.world_path = Path(world_path)
        self.world_id = world_id
        self.on_backup = on_backup_callback
        self.last_modified = time.time()
        self.backup_pending = False
        self._backing_up = False
        self._lock = lock or threading.Lock()

    def on_modified(self, event):
        self._trigger(event)

    def on_created(self, event):
        self._trigger(event)

    def _trigger(self, event):
        if event.is_directory:
            return
        with self._lock:
            self.last_modified = time.time()
            if not self.backup_pending and not self._backing_up:
                self.backup_pending = True
                world_name = self.world_path.name
                logger.info(f"[{world_name}] Changes detected...")
                set_status(self.world_id, world_name, "detecting", "Changes detected — waiting to debounce...")


class BackupWatcher:
    """In-process file watcher for Minecraft worlds. Runs in a background thread."""

    def __init__(self, get_worlds_fn, backup_fn, debounce_seconds=10, sync_interval=300, resync_check_fn=None):
        self.get_worlds = get_worlds_fn
        self.backup_fn = backup_fn
        self.debounce = debounce_seconds
        self.sync_interval = sync_interval
        self.resync_check = resync_check_fn
        self.observers = []
        self.running = False
        self.last_sync = 0
        self._thread = None
        self._lock = threading.Lock()
        self._backup_running = set()

    def start(self):
        self.running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        logger.info("Backup watcher started")

    def stop(self):
        self.running = False
        for obs in self.observers:
            obs["observer"].stop()
        for obs in self.observers:
            obs["observer"].join()
        logger.info("Backup watcher stopped")

    def _sync_worlds(self):
        try:
            worlds = self.get_worlds()
            auto_sync = [w for w in worlds if w.get("auto_sync_enabled")]
            sync_ids = {w["id"] for w in auto_sync}

            with self._lock:
                remaining = []
                for obs in self.observers:
                    if obs["world"]["id"] not in sync_ids:
                        obs["observer"].stop()
                        threading.Thread(target=obs["observer"].join, daemon=True).start()
                    else:
                        remaining.append(obs)
                self.observers = remaining

                watched_ids = {obs["world"]["id"] for obs in self.observers}
                for world in auto_sync:
                    if world["id"] not in watched_ids:
                        self._start_watching(world)
        except Exception as e:
            logger.error(f"Watcher sync error: {e}")

    def _start_watching(self, world):
        path = Path(world.get("local_path") or "")
        if not path.exists():
            mc_path = Path.home() / ".minecraft" / "saves"
            path = mc_path / world["name"]
        if not path.exists():
            logger.warning(f"World folder not found: {path}")
            return

        watcher = WorldWatcher(path, world["id"], self.backup_fn, lock=self._lock)
        observer = Observer()
        observer.schedule(watcher, str(path), recursive=True)
        observer.start()
        self.observers.append({"observer": observer, "watcher": watcher, "world": world})
        logger.info(f"Watching: {world['name']}")

    def _run_backup(self, obs):
        """Wrapper that tracks running backups and cleans up when done."""
        world = obs["world"]
        watcher = obs["watcher"]
        world_id = world["id"]
        with self._lock:
            watcher._backing_up = True
        try:
            self.backup_fn(world, watcher.world_path, self._backup_done)
        except Exception as e:
            logger.error(f"Backup thread error for {world.get('name')}: {e}")
        finally:
            with self._lock:
                watcher._backing_up = False
                watcher.backup_pending = False
                self._backup_running.discard(world_id)

    def _backup_done(self, world_id):
        """Remove world from running set so new backups can fire."""
        with self._lock:
            self._backup_running.discard(world_id)

    def _run(self):
        self._sync_worlds()
        self.last_sync = time.time()

        while self.running:
            now = time.time()

            if (self.resync_check and self.resync_check()) or (now - self.last_sync > self.sync_interval):
                self._sync_worlds()
                self.last_sync = now

            with self._lock:
                for obs in self.observers:
                    w = obs["watcher"]
                    world = obs["world"]
                    if w.backup_pending and world["id"] not in self._backup_running and (now - w.last_modified) >= self.debounce:
                        w.backup_pending = False
                        self._backup_running.add(world["id"])
                        set_status(world["id"], world["name"], "backing_up", "Backing up...")
                        threading.Thread(
                            target=self._run_backup,
                            args=(obs,),
                            daemon=True,
                        ).start()

            time.sleep(1)
