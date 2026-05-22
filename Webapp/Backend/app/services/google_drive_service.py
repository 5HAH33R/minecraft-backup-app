from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from google.auth.transport.requests import Request
from tenacity import retry, stop_after_attempt, wait_exponential
import os
import io
import zipfile
from pathlib import Path
from datetime import datetime
import pickle
import tempfile

class GoogleDriveService:
    
    SCOPES = ['https://www.googleapis.com/auth/drive.file']
    
    def __init__(self, credentials_dict=None):
        """
        Initialize with user credentials
        credentials_dict: User's OAuth tokens from database
        """
        self.credentials = None
        
        if credentials_dict:
            self.credentials = Credentials.from_authorized_user_info(
                credentials_dict, 
                self.SCOPES
            )
        
        # Refresh token if expired
        if self.credentials and self.credentials.expired and self.credentials.refresh_token:
            try:
                self.credentials.refresh(Request())
            except Exception as e:
                print(f"Warning: Failed to refresh Google credentials: {e}")
                # If refresh fails, we keep the expired credentials.
                # The API calls will fail later, which is handled by the router.
        
        # Build Drive API service
        if self.credentials:
            self.service = build('drive', 'v3', credentials=self.credentials)
        else:
            self.service = None
    
    @staticmethod
    def get_auth_url(redirect_uri, client_config):
        """Generate OAuth authorization URL"""
        flow = Flow.from_client_config(
            client_config,
            scopes=GoogleDriveService.SCOPES,
            redirect_uri=redirect_uri
        )
        
        auth_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'  # Force to get refresh token
        )
        
        return auth_url, state
    
    @staticmethod
    def exchange_code_for_token(code, redirect_uri, client_config):
        """Exchange authorization code for access token"""
        flow = Flow.from_client_config(
            client_config,
            scopes=GoogleDriveService.SCOPES,
            redirect_uri=redirect_uri
        )
        
        flow.fetch_token(code=code)
        credentials = flow.credentials
        
        return {
            'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes
        }
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    def create_app_folder(self):
        """Create main app folder in user's Drive"""
        # Check if folder exists
        query = "name='MinecraftBackups' and mimeType='application/vnd.google-apps.folder' and trashed=false"
        results = self.service.files().list(q=query, fields="files(id, name)").execute()
        folders = results.get('files', [])
        
        if folders:
            return folders[0]['id']
        
        # Create folder
        folder_metadata = {
            'name': 'MinecraftBackups',
            'mimeType': 'application/vnd.google-apps.folder'
        }
        
        folder = self.service.files().create(
            body=folder_metadata,
            fields='id'
        ).execute()
        
        return folder['id']
    
    def create_world_folder(self, world_name, parent_folder_id):
        """Create folder for specific world"""
        folder_metadata = {
            'name': world_name,
            'mimeType': 'application/vnd.google-apps.folder',
            'parents': [parent_folder_id]
        }
        
        folder = self.service.files().create(
            body=folder_metadata,
            fields='id'
        ).execute()
        
        return folder['id']
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    def upload_world_backup(self, world_path, world_name, folder_id):
        """
        Upload world to Google Drive. 
        If world_path is a folder, it zips it first.
        If world_path is already a ZIP, it uploads it directly.
        """
        source_path = Path(world_path).resolve()
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        
        # Determine if we need to create a new zip or use the existing one
        is_already_zipped = source_path.suffix.lower() == '.zip'
        
        if is_already_zipped:
            print(f"File is already zipped. Preparing to upload: {source_path.name}")
            zip_path = source_path
        else:
            # Create a temporary zip file path for the folder
            zip_filename = f"{world_name}_{timestamp}.zip"
            zip_path = Path(tempfile.gettempdir()) / zip_filename
            
            print(f"Compressing folder {world_name} into {zip_path}...")
            
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # We use rglob('*') to find all files inside the folder
                for file_path in source_path.rglob('*'):
                    if file_path.is_file():
                        # relative_to(source_path) makes the ZIP structure clean
                        arcname = file_path.relative_to(source_path)
                        zipf.write(file_path, arcname)
            
            print(f"Compression complete. Size: {os.path.getsize(zip_path) / (1024*1024):.2f} MB")

        # Final check: Is the file we're about to upload actually there?
        if not zip_path.exists() or os.path.getsize(zip_path) <= 22:
            raise Exception(f"Failed to create a valid backup. File is empty or missing at {zip_path}")

        # Prepare metadata for Google Drive
        # Use consistent format: {world_name}_{YYYY-MM-dd_HH-MM-SS}.zip
        drive_filename = f"{world_name}_{timestamp}.zip"
        
        file_metadata = {
            'name': drive_filename,
            'parents': [folder_id],
            'description': f'Minecraft world backup - {world_name}'
        }

        try:
            media = MediaFileUpload(
                str(zip_path), # Convert Path object to string for Google API
                mimetype='application/zip',
                resumable=True
            )

            print(f"Uploading to Google Drive...")
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, name, size, createdTime, webViewLink'
            ).execute()

            # IMPORTANT: Explicitly delete the media handle so Windows releases the file lock
            del media 
            print(f"Upload complete! File ID: {file['id']}")

            return {
                'file_id': file['id'],
                'name': file['name'],
                'size_bytes': int(file['size']),
                'size_mb': round(int(file['size']) / (1024*1024), 2),
                'created_time': file['createdTime'],
                'web_link': file.get('webViewLink'),
                'timestamp': timestamp
            }

        finally:
            # Only delete the file if we were the ones who created the temporary ZIP
            # We don't want to delete the user's original upload file if Case A applies!
            if not is_already_zipped and zip_path.exists():
                try:
                    os.remove(zip_path)
                except PermissionError:
                    print(f"Warning: Could not delete temporary file {zip_path}. Windows still has it locked.")
    
    def list_backups(self, folder_id):
        """List all backups in a folder"""
        query = f"'{folder_id}' in parents and trashed=false"
        
        results = self.service.files().list(
            q=query,
            fields="files(id, name, size, createdTime, webViewLink)",
            orderBy="createdTime desc"
        ).execute()
        
        files = results.get('files', [])
        
        return [{
            'file_id': f['id'],
            'name': f['name'],
            'size_mb': round(int(f['size']) / (1024*1024), 2),
            'created_time': f['createdTime'],
            'web_link': f.get('webViewLink')
        } for f in files]
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    def download_backup(self, file_id, destination_path):
        """
        Download and extract backup from Google Drive
        
        Args:
            file_id: Google Drive file ID
            destination_path: Where to extract the world
        
        Returns:
            Path to extracted world
        """
        destination_path = Path(destination_path)
        
        # Download file
        request = self.service.files().get_media(fileId=file_id)
        
        zip_path = os.path.join(tempfile.gettempdir(), f"minecraft_restore_{file_id}.zip")
        
        with io.FileIO(zip_path, 'wb') as fh:
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            
            print("Downloading backup...")
            while not done:
                status, done = downloader.next_chunk()
                if status:
                    print(f"Download {int(status.progress() * 100)}%")
        
        # Extract zip
        print("Extracting files...")
        with zipfile.ZipFile(zip_path, 'r') as zipf:
            zipf.extractall(destination_path.parent)
        
        # Clean up
        os.remove(zip_path)
        
        return destination_path
    
    def delete_backup(self, file_id):
        """Delete a backup file"""
        self.service.files().delete(fileId=file_id).execute()
        return True
    
    def get_storage_quota(self):
        """Get user's Drive storage information"""
        about = self.service.about().get(fields="storageQuota").execute()
        quota = about.get('storageQuota', {})
        
        total = int(quota.get('limit', 0))
        used = int(quota.get('usage', 0))
        
        return {
            'total_gb': round(total / (1024**3), 2),
            'used_gb': round(used / (1024**3), 2),
            'available_gb': round((total - used) / (1024**3), 2),
            'percent_used': round((used / total) * 100, 2) if total > 0 else 0
        }
    
    def cleanup_old_backups(self, folder_id, keep_count=10):
        """
        Delete old backups, keeping only the most recent ones
        
        Args:
            folder_id: Folder containing backups
            keep_count: Number of recent backups to keep
        """
        backups = self.list_backups(folder_id)
        
        # Sort by creation time (already sorted from list_backups)
        if len(backups) > keep_count:
            to_delete = backups[keep_count:]
            
            for backup in to_delete:
                print(f"Deleting old backup: {backup['name']}")
                self.delete_backup(backup['file_id'])
            
            return len(to_delete)
        
        return 0