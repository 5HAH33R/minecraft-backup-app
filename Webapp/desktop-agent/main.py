import os
import time
import json
import zipfile
import requests
import threading
import argparse
import sys
import signal
import logging
import base64
from pathlib import Path
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# ------------------------------------------------------------
# CLI Arguments
# ------------------------------------------------------------
parser = argparse.ArgumentParser(description='Minecraft Backup Agent')
parser.add_argument('--config', type=str, default=None, help='Path to config file')
parser.add_argument('--api-url', type=str, default=None, help='API URL override')
parser.add_argument('--debug', action='store_true', help='Enable debug logging')
parser.add_argument('--pair', type=str, default=None, help='Pairing code from the web app Settings page')
ARGS = parser.parse_args()

# ------------------------------------------------------------
# Logging Setup
# ------------------------------------------------------------
log_level = logging.DEBUG if ARGS.debug else logging.INFO
logging.basicConfig(
    filename='agent.log',
    level=log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('BackupAgent')
console = logging.StreamHandler()
console.setLevel(log_level)
console.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logging.getLogger('').addHandler(console)

# ------------------------------------------------------------
# Signal Handling
# ------------------------------------------------------------
_agent_instance = None
_shutdown = threading.Event()


def signal_handler(sig, frame):
    """Graceful shutdown on SIGINT/SIGTERM."""
    print("\nShutting down gracefully...")
    if _agent_instance is not None and _agent_instance.running:
        _agent_instance.stop()
    _shutdown.set()
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


def _is_token_expired(token):
    """Check if a JWT token is expired by decoding its payload (no signature verify)."""
    if not token:
        return True
    try:
        parts = token.split('.')
        if len(parts) != 3:
            return True
        payload = parts[1]
        padding = 4 - len(payload) % 4
        if padding != 4:
            payload += '=' * padding
        decoded = json.loads(base64.urlsafe_b64decode(payload))
        return time.time() > decoded.get('exp', 0)
    except Exception:
        return True


# ------------------------------------------------------------
# Config
# ------------------------------------------------------------
class Config:
    def __init__(self, args=None):
        if args and args.config:
            self.config_file = Path(args.config)
        else:
            self.config_file = Path(__file__).parent / 'config.json'
        self.config_file.parent.mkdir(exist_ok=True)
        self.load()
        if args and args.api_url:
            self.data['api_url'] = args.api_url

    def load(self):
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    self.data = json.load(f)
                self.data.setdefault('refresh_token', '')
                self.data.setdefault('api_key', '')
                self.data.setdefault('debug', False)
            except Exception:
                self.reset_default()
        else:
            self.reset_default()

    def reset_default(self):
        self.data = {
            "api_url": "http://localhost:8000",
            "auth_token": "",
            "refresh_token": "",
            "api_key": "",
            "debug": False,
            "minecraft_saves_path": self.detect_minecraft_path(),
            "watched_worlds": [],
            "sync_interval_minutes": 5,
            "debounce_seconds": 10
        }
        self.save()

    def save(self):
        with open(self.config_file, 'w') as f:
            json.dump(self.data, f, indent=2)

    @staticmethod
    def detect_minecraft_path():
        import platform
        system = platform.system()
        if system == "Windows":
            appdata = os.getenv("APPDATA")
            return str(Path(appdata) / ".minecraft" / "saves")
        elif system == "Darwin":
            return str(Path.home() / "Library/Application Support/minecraft/saves")
        elif system == "Linux":
            return str(Path.home() / ".minecraft" / "saves")
        return ""


# ------------------------------------------------------------
# Minecraft World Watcher
# ------------------------------------------------------------
class MinecraftWorldWatcher(FileSystemEventHandler):
    def __init__(self, world_path, world_id, backup_agent):
        self.world_path = Path(world_path)
        self.world_id = world_id
        self.backup_agent = backup_agent
        self.last_modified = time.time()
        self.backup_pending = False

    def on_modified(self, event):
        self._trigger_backup(event)

    def on_created(self, event):
        self._trigger_backup(event)

    def on_deleted(self, event):
        self._trigger_backup(event)

    def _trigger_backup(self, event):
        if event.is_directory:
            return
        self.last_modified = time.time()
        if not self.backup_pending:
            self.backup_pending = True
            print(f"[{self.world_path.name}] Changes detected...")


# ------------------------------------------------------------
# Backup Agent
# ------------------------------------------------------------
class BackupAgent:
    def __init__(self):
        self.config = Config(ARGS)
        self.observers = []
        self.running = False
        self.active_backups = set()
        self.last_sync_time = 0

    def start(self):
        self.running = True
        self.sync_with_api()
        threading.Thread(target=self.main_loop, daemon=True).start()
        print("Backup agent started!")
        logger.info("Backup agent started")

    def _make_authenticated_request(self, method, url, **kwargs):
        """Send an authenticated request, preferring API key over JWT."""
        api_key = self.config.data.get("api_key", "")
        headers = kwargs.pop('headers', {})
        kwargs.setdefault('timeout', 10)

        if api_key:
            # API key auth — no refresh logic needed (keys don't expire)
            headers['X-API-Key'] = api_key
            kwargs['headers'] = headers
            return requests.request(method, url, **kwargs)

        # Legacy JWT auth with auto-refresh
        token = self.config.data.get("auth_token", "")
        headers['Authorization'] = f'Bearer {token}'
        kwargs['headers'] = headers

        response = requests.request(method, url, **kwargs)

        if response.status_code == 401:
            logger.info("Received 401, attempting token refresh...")
            if self._refresh_access_token():
                new_token = self.config.data.get("auth_token", "")
                headers['Authorization'] = f'Bearer {new_token}'
                kwargs['headers'] = headers
                # Rewind file streams for retry
                if 'files' in kwargs:
                    for key, val in kwargs['files'].items():
                        if isinstance(val, tuple) and len(val) >= 2:
                            f = val[1]
                        else:
                            f = val
                        if hasattr(f, 'seek'):
                            f.seek(0)
                response = requests.request(method, url, **kwargs)
                logger.info(f"Retry after refresh: {response.status_code}")
            else:
                logger.warning("Token refresh failed, cannot authenticate")

        return response

    def _refresh_access_token(self):
        """Refresh the auth token via POST /api/auth/refresh."""
        refresh_token = self.config.data.get("refresh_token", "")
        if not refresh_token:
            logger.warning("No refresh token available")
            return False
        try:
            response = requests.post(
                f'{self.config.data["api_url"]}/api/auth/refresh',
                json={"refresh_token": refresh_token},
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                if "access_token" in data:
                    self.config.data["auth_token"] = data["access_token"]
                elif "token" in data:
                    self.config.data["auth_token"] = data["token"]
                if "refresh_token" in data:
                    self.config.data["refresh_token"] = data["refresh_token"]
                self.config.save()
                logger.info("Auth token refreshed successfully")
                return True
            else:
                logger.warning(f"Token refresh failed: HTTP {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Token refresh error: {e}")
            return False

    def sync_with_api(self):
        """Fetch worlds from API and update observers to match."""
        try:
            print("Syncing world list with API...")
            logger.info("Syncing world list with API...")
            response = self._make_authenticated_request(
                'GET', f'{self.config.data["api_url"]}/api/worlds', timeout=10
            )
            if response.status_code == 200:
                api_worlds = response.json()
                auto_sync_worlds = [w for w in api_worlds if w.get('auto_sync_enabled', False)]
                self.config.data['watched_worlds'] = auto_sync_worlds
                self.config.save()
                api_world_ids = {w['id'] for w in auto_sync_worlds}

                # Remove watchers for worlds no longer in API
                remaining_observers = []
                for obs in self.observers:
                    if obs['world']['id'] not in api_world_ids:
                        print(f"Stopping watcher for: {obs['world']['name']} (deleted or disabled)")
                        logger.info(f"Stopping watcher for: {obs['world']['name']}")
                        obs['observer'].stop()
                        threading.Thread(target=obs['observer'].join).start()
                    else:
                        remaining_observers.append(obs)
                self.observers = remaining_observers

                # Add watchers for new worlds
                current_watched_ids = {obs['world']['id'] for obs in self.observers}
                for world in auto_sync_worlds:
                    if world['id'] not in current_watched_ids:
                        self.start_single_watcher(world)

                self.last_sync_time = time.time()
                logger.info(f"Sync completed: {len(auto_sync_worlds)} auto-sync worlds")
            else:
                print(f"API Sync failed (Status {response.status_code})")
                logger.warning(f"API Sync failed (Status {response.status_code})")
        except Exception as e:
            print(f"Error syncing with API: {e}")
            logger.error(f"Error syncing with API: {e}")

    def start_single_watcher(self, world):
        api_local_path = world.get('local_path')
        if api_local_path and Path(api_local_path).exists():
            world_path = Path(api_local_path)
        else:
            minecraft_path = Path(self.config.data['minecraft_saves_path'])
            world_path = minecraft_path / world['name']
        if not world_path.exists():
            print(f"World folder not found: {world_path}")
            logger.warning(f"World folder not found: {world_path}")
            return
        watcher = MinecraftWorldWatcher(world_path, world['id'], self)
        observer = Observer()
        observer.schedule(watcher, str(world_path), recursive=True)
        observer.start()
        self.observers.append({'observer': observer, 'watcher': watcher, 'world': world})
        print(f"Now watching: {world['name']}")
        logger.info(f"Now watching: {world['name']}")

    def main_loop(self):
        """Background loop for debounced backups and periodic API sync."""
        while self.running:
            current_time = time.time()
            sync_interval = self.config.data.get("sync_interval_minutes", 5) * 60
            if current_time - self.last_sync_time > sync_interval:
                self.sync_with_api()
            debounce = self.config.data.get("debounce_seconds", 10)
            for obs in self.observers:
                watcher = obs['watcher']
                world = obs['world']
                if watcher.backup_pending and world['id'] not in self.active_backups:
                    time_since_change = current_time - watcher.last_modified
                    if time_since_change >= debounce:
                        watcher.backup_pending = False
                        threading.Thread(
                            target=self.backup_world,
                            args=(world, watcher.world_path, watcher),
                            daemon=True
                        ).start()
            time.sleep(1)

    def backup_world(self, world, world_path, watcher=None):
        """Compress a world folder and upload to the API."""
        if world['id'] in self.active_backups:
            return
        self.active_backups.add(world['id'])
        try:
            print(f"Starting backup: {world['name']}")
            logger.info(f"Starting backup: {world['name']}")
            temp_base = Path.home() / '.minecraft_backup' / 'temp'
            temp_base.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
            zip_filename = f"{world['name']}_{timestamp}.zip"
            zip_path = temp_base / zip_filename

            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file_path in world_path.rglob('*'):
                    if file_path.is_file():
                        try:
                            arcname = str(file_path.relative_to(world_path.parent))
                            zipf.write(file_path, arcname)
                        except (PermissionError, OSError) as e:
                            print(f"Skipping locked or inaccessible file: {file_path.name}")
                            logger.warning(f"Skipping locked file: {file_path.name}")

            with open(zip_path, 'rb') as f:
                files = {'file': (zip_filename, f, 'application/zip')}
                logger.info(f"Uploading backup for {world['name']} ({zip_path.stat().st_size} bytes)")
                response = self._make_authenticated_request(
                    'POST',
                    f'{self.config.data["api_url"]}/api/drive/worlds/{world["id"]}/backup',
                    files=files,
                    timeout=(30, 900)
                )

            if response.status_code == 200:
                print(f"Backup successful: {world['name']}")
                logger.info(f"Backup successful: {world['name']}")
            else:
                print(f"Backup failed for {world['name']}: {response.text}")
                logger.error(f"Backup failed for {world['name']}: HTTP {response.status_code}")

            if zip_path.exists():
                try:
                    zip_path.unlink()
                except Exception as e:
                    print(f"Could not delete temp file {zip_path.name}: {e}")
                    logger.warning(f"Could not delete temp file {zip_path.name}: {e}")
        except Exception as e:
            print(f"Error during backup of {world['name']}: {e}")
            logger.error(f"Error during backup of {world['name']}: {e}")
        finally:
            self.active_backups.remove(world['id'])
            if watcher:
                watcher.backup_pending = False

    def stop(self):
        self.running = False
        for obs in self.observers:
            obs['observer'].stop()
            obs['observer'].join()
        print("Backup agent stopped")
        logger.info("Backup agent stopped")


# ------------------------------------------------------------
# Main
# ------------------------------------------------------------
def main():
    global _agent_instance

    # --- Pairing flow ---
    if ARGS.pair:
        api_url = ARGS.api_url or "http://localhost:8000"
        code = ARGS.pair.strip().upper()
        print(f"Pairing with code: {code}")
        try:
            resp = requests.post(
                f"{api_url}/api/auth/pair/exchange",
                json={"code": code},
                timeout=10,
            )
            if resp.status_code == 200:
                api_key = resp.json()["api_key"]
                config = Config(ARGS)
                config.data["api_key"] = api_key
                config.save()
                print("Desktop agent paired successfully! API key saved to config.")
                logger.info("Desktop agent paired successfully")
                return
            else:
                print(f"Pairing failed: {resp.json().get('detail', 'Unknown error')}")
                logger.error(f"Pairing failed: {resp.status_code} {resp.text}")
                return
        except Exception as e:
            print(f"Pairing error: {e}")
            logger.error(f"Pairing error: {e}")
            return

    agent = BackupAgent()
    _agent_instance = agent

    api_key = agent.config.data.get("api_key", "")
    token = agent.config.data.get("auth_token", "")
    refresh_token = agent.config.data.get("refresh_token", "")

    if api_key:
        print("Using API key authentication.")
        logger.info("Using API key authentication")
    elif token:
        # Proactively refresh an expired token when a refresh_token is available
        if _is_token_expired(token) and refresh_token:
            print("Auth token expired, attempting refresh...")
            logger.info("Auth token expired, attempting refresh...")
            if agent._refresh_access_token():
                print("Token refreshed successfully")
                logger.info("Token refreshed successfully")
            else:
                print("Could not refresh expired token. Please login again via the app.")
                logger.warning("Could not refresh expired token")
    else:
        print("No auth token or API key found! Please login via the app first.")
        logger.warning("No authentication configured")
        return

    agent.start()

    # Block main thread until signal handler signals shutdown
    try:
        _shutdown.wait()
    except KeyboardInterrupt:
        agent.stop()


if __name__ == "__main__":
    main()
