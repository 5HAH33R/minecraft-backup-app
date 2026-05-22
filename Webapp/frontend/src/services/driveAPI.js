import api from './api';

export const driveAPI = {
  // Get storage info
  getStorageInfo: async () => {
    return api.get('/api/drive/storage');
  },
  
  // Backup a world (upload ZIP)
  backupWorld: async (worldId, file, onProgress) => {
    const formData = new FormData();
    formData.append('file', file);
    
    return api.post(`/api/drive/worlds/${worldId}/backup`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        const percentCompleted = Math.round(
          (progressEvent.loaded * 100) / progressEvent.total
        );
        if (onProgress) {
          onProgress(percentCompleted);
        }
      },
    });
  },
  
  // List backups for a world
  listBackups: async (worldId) => {
    return api.get(`/api/drive/worlds/${worldId}/backups`);
  },
  
  // Get download link for a backup
  getDownloadLink: async (worldId, backupId) => {
    return api.get(`/api/drive/worlds/${worldId}/backups/${backupId}/download-link`);
  },
  
  // Delete a backup
  deleteBackup: async (worldId, backupId) => {
    return api.delete(`/api/drive/worlds/${worldId}/backups/${backupId}`);
  },
};

export const worldsAPI = {
  // List all worlds
  listWorlds: async () => {
    return api.get('/api/worlds');
  },
  
  // Get world details
  getWorld: async (worldId) => {
    return api.get(`/api/worlds/${worldId}`);
  },
  
  // Create new world
  createWorld: async (data) => {
    return api.post('/api/worlds', data);
  },
  
  // Update world
  updateWorld: async (worldId, data) => {
    return api.put(`/api/worlds/${worldId}`, data);
  },
  
  // Delete world
  deleteWorld: async (worldId) => {
    return api.delete(`/api/worlds/${worldId}`);
  },

};