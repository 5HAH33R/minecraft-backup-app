from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from google.auth.transport.requests import Request
from tenacity import retry, stop_after_attempt, wait_exponential
import logging
import os
import io
import zipfile
from pathlib import Path
from datetime import datetime, UTC
import tempfile

logger = logging.getLogger("minecraft-backup.drive")


class GoogleDriveService:

    SCOPES = ["https://www.googleapis.com/auth/drive.file"]

    def __init__(self, credentials_dict=None):
        self.credentials = None

        if credentials_dict:
            self.credentials = Credentials.from_authorized_user_info(
                credentials_dict, self.SCOPES
            )

        if self.credentials and self.credentials.expired and self.credentials.refresh_token:
            try:
                self.credentials.refresh(Request())
            except Exception as e:
                logger.warning(f"Warning: Failed to refresh Google credentials: {e}")

        if self.credentials:
            self.service = build("drive", "v3", credentials=self.credentials)
        else:
            self.service = None

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    def create_app_folder(self):
        query = (
            "name='MinecraftBackups' and "
            "mimeType='application/vnd.google-apps.folder' and "
            "trashed=false"
        )
        results = self.service.files().list(q=query, fields="files(id, name)").execute()
        folders = results.get("files", [])
        if folders:
            return folders[0]["id"]

        folder = (
            self.service.files()
            .create(
                body={
                    "name": "MinecraftBackups",
                    "mimeType": "application/vnd.google-apps.folder",
                },
                fields="id",
            )
            .execute()
        )
        return folder["id"]

    def create_world_folder(self, world_name, parent_folder_id):
        folder = (
            self.service.files()
            .create(
                body={
                    "name": world_name,
                    "mimeType": "application/vnd.google-apps.folder",
                    "parents": [parent_folder_id],
                },
                fields="id",
            )
            .execute()
        )
        return folder["id"]

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    def upload_world_backup(self, world_path, world_name, folder_id):
        source_path = Path(world_path).resolve()
        timestamp = datetime.now(UTC).strftime("%Y-%m-%d_%H-%M-%S")
        is_already_zipped = source_path.suffix.lower() == ".zip"

        if is_already_zipped:
            zip_path = source_path
        else:
            zip_filename = f"{world_name}_{timestamp}.zip"
            zip_path = Path(tempfile.gettempdir()) / zip_filename

            logger.info(f"Compressing {world_name}...")
            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
                for fp in source_path.rglob("*"):
                    if fp.is_file():
                        arcname = fp.relative_to(source_path)
                        compress = zipfile.ZIP_STORED if fp.suffix.lower() == ".mca" else zipfile.ZIP_DEFLATED
                        try:
                            zipf.write(fp, arcname, compress_type=compress)
                        except (PermissionError, OSError):
                            pass

        final_size = os.path.getsize(zip_path)
        if not zip_path.exists() or final_size <= 22:
            raise Exception(f"Backup file is empty or missing at {zip_path}")

        drive_filename = f"{world_name}_{timestamp}.zip"
        file_metadata = {
            "name": drive_filename,
            "parents": [folder_id],
            "description": f"Minecraft world backup - {world_name}",
        }

        try:
            media = MediaFileUpload(
                str(zip_path), mimetype="application/zip", resumable=True
            )

            logger.info(f"Uploading to Google Drive...")
            uploaded = (
                self.service.files()
                .create(
                    body=file_metadata,
                    media_body=media,
                    fields="id, name, size, createdTime, webViewLink",
                )
                .execute()
            )

            del media

            return {
                "file_id": uploaded["id"],
                "name": uploaded["name"],
                "size_bytes": int(uploaded["size"]),
                "size_mb": round(int(uploaded["size"]) / (1024 * 1024), 2),
                "created_time": uploaded["createdTime"],
                "web_link": uploaded.get("webViewLink"),
                "timestamp": timestamp,
            }
        finally:
            if not is_already_zipped and zip_path.exists():
                try:
                    os.remove(zip_path)
                except PermissionError:
                    pass

    def list_backups(self, folder_id):
        query = f"'{folder_id}' in parents and trashed=false"
        results = (
            self.service.files()
            .list(
                q=query,
                fields="files(id, name, size, createdTime, webViewLink)",
                orderBy="createdTime desc",
            )
            .execute()
        )
        return [
            {
                "file_id": f["id"],
                "name": f["name"],
                "size_mb": round(int(f["size"]) / (1024 * 1024), 2),
                "created_time": f["createdTime"],
                "web_link": f.get("webViewLink"),
            }
            for f in results.get("files", [])
        ]

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    def download_backup(self, file_id, destination_path):
        dest = Path(destination_path)
        request = self.service.files().get_media(fileId=file_id)
        zip_path = os.path.join(
            tempfile.gettempdir(), f"minecraft_restore_{file_id}.zip"
        )

        with io.FileIO(zip_path, "wb") as fh:
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while not done:
                status, done = downloader.next_chunk()

        with zipfile.ZipFile(zip_path, "r") as zipf:
            zipf.extractall(dest.parent)

        os.remove(zip_path)
        return dest

    def delete_backup(self, file_id):
        self.service.files().delete(fileId=file_id).execute()
        return True

    def get_storage_quota(self):
        about = self.service.about().get(fields="storageQuota").execute()
        quota = about.get("storageQuota", {})
        total = int(quota.get("limit", 0))
        used = int(quota.get("usage", 0))
        return {
            "total_gb": round(total / (1024**3), 2),
            "used_gb": round(used / (1024**3), 2),
            "available_gb": round((total - used) / (1024**3), 2),
            "percent_used": round((used / total) * 100, 2) if total > 0 else 0,
        }

    def cleanup_old_backups(self, folder_id, keep_count=10):
        backups = self.list_backups(folder_id)
        if len(backups) > keep_count:
            deleted = 0
            for backup in backups[keep_count:]:
                self.delete_backup(backup["file_id"])
                deleted += 1
            return deleted
        return 0
