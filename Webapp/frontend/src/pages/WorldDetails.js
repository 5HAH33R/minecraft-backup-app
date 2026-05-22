import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { toast } from 'react-toastify';
import UploadProgress from '../components/UploadProgress';
import ConfirmDialog from '../components/ConfirmDialog';
import { worldsAPI, driveAPI } from '../services/driveAPI';
import { ArrowLeft, HardDrive, Package, Clock, Upload, Trash2, Download } from 'lucide-react';
import { cn } from '../lib/utils';

function WorldDetails() {
  const { worldId } = useParams();
  const navigate = useNavigate();

  const [world, setWorld] = useState(null);
  const [backups, setBackups] = useState([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadFileName, setUploadFileName] = useState('');
  const [deleteDialog, setDeleteDialog] = useState({ open: false, backupId: null, backupName: '' });

  useEffect(() => { loadWorldData(); }, [worldId]);

  const loadWorldData = async () => {
    try {
      const [worldRes, backupsRes] = await Promise.all([
        worldsAPI.getWorld(worldId),
        driveAPI.listBackups(worldId),
      ]);
      setWorld(worldRes.data);
      setBackups(backupsRes.data.backups || []);
    } catch (error) {
      toast.error('Failed to load world details');
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    if (!file.name.endsWith('.zip')) { toast.error('Please select a ZIP file'); return; }

    setUploading(true);
    setUploadFileName(file.name);
    setUploadProgress(0);
    try {
      await driveAPI.backupWorld(worldId, file, (p) => setUploadProgress(p));
      toast.success('Backup uploaded successfully!');
      await loadWorldData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Upload failed');
    } finally {
      setUploading(false);
      setUploadProgress(0);
      e.target.value = '';
    }
  };

  const handleDownload = async (backup) => {
    try {
      const response = await driveAPI.getDownloadLink(worldId, backup.id);
      window.open(response.data.download_link, '_blank');
    } catch {
      toast.error('Failed to get download link');
    }
  };

  const handleDeleteBackup = async () => {
    try {
      await driveAPI.deleteBackup(worldId, deleteDialog.backupId);
      toast.success('Backup deleted successfully');
      setDeleteDialog({ open: false, backupId: null, backupName: '' });
      await loadWorldData();
    } catch {
      toast.error('Failed to delete backup');
    }
  };

  const handleToggleAutoSync = async () => {
    if (!world.auto_sync_enabled && !world.local_path) {
      toast.error('Please set a local path first before enabling auto-sync');
      return;
    }
    try {
      await worldsAPI.updateWorld(worldId, {
        auto_sync_enabled: !world.auto_sync_enabled,
        local_path: world.local_path || null,
      });
      toast.success(`Auto-sync ${!world.auto_sync_enabled ? 'enabled' : 'disabled'}`);
      await loadWorldData();
    } catch {
      toast.error('Failed to update auto-sync');
    }
  };

  const formatDate = (d) => new Date(d).toLocaleString();

  if (loading) {
    return (
      <div className="flex items-center justify-center py-32">
        <div className="text-center">
          <div className="w-14 h-14 bg-mc-grass border-4 border-black mx-auto animate-pulse" />
          <p className="mt-5 text-base font-semibold text-white/60">Loading world details...</p>
        </div>
      </div>
    );
  }

  if (!world) {
    return (
      <div className="flex items-center justify-center py-32">
        <div className="text-center">
          <h2 className="text-xl font-bold text-white uppercase mb-5">World not found</h2>
          <button onClick={() => navigate('/dashboard')} className="pixel-btn text-sm">
            Back to Dashboard
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-6xl">
      {/* Back */}
      <button
        onClick={() => navigate('/dashboard')}
        className="inline-flex items-center gap-2 text-mc-sky hover:underline text-sm font-semibold"
      >
        <ArrowLeft size={16} />
        Back to Dashboard
      </button>

      {/* World Header */}
      <div className="pixel-card p-5 md:p-6">
        <div className="flex flex-col md:flex-row md:items-start justify-between gap-4 mb-4">
          <div className="space-y-1">
            <h1 className="text-shadow text-2xl md:text-3xl font-bold text-white uppercase">
              {world.name}
            </h1>
            {world.description && (
              <p className="text-sm font-medium text-black/60">{world.description}</p>
            )}
          </div>
          <div className="flex items-center gap-3 shrink-0">
            <span id="autosync-label" className="text-sm font-bold text-white/80">Auto-sync</span>
            <div
              onClick={handleToggleAutoSync}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.preventDefault();
                  handleToggleAutoSync();
                }
              }}
              className={cn('pixel-toggle', world.auto_sync_enabled ? 'on' : 'off')}
              role="switch"
              aria-checked={world.auto_sync_enabled}
              aria-labelledby="autosync-label"
              tabIndex={0}
            >
              <div className="pixel-toggle-knob" />
            </div>
          </div>
        </div>

        {/* Local Path */}
        <div className="bg-black/20 border-4 border-black/30 p-4">
          <div className="flex items-center justify-between mb-1">
            <span className="text-xs font-semibold text-white/60 uppercase tracking-wider">
              World Folder Path:
            </span>
            <button
              onClick={async () => {
                const p = prompt('Enter local path:', world.local_path || '');
                if (p !== null) {
                  try {
                    await worldsAPI.updateWorld(worldId, { local_path: p });
                    toast.success('Path updated!');
                    loadWorldData();
                  } catch { toast.error('Failed to update path'); }
                }
              }}
              className="text-xs font-semibold text-mc-sky hover:underline"
            >
              Edit
            </button>
          </div>
          <p className="text-sm font-mono text-white/80 break-all">
            {world.local_path || 'No path set'}
          </p>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {[
          { icon: Package, label: 'Total Backups', value: world.total_backups, color: 'text-mc-sky' },
          { icon: HardDrive, label: 'Total Size', value: `${(world.total_size_mb || 0).toFixed(2)} MB`, color: 'text-mc-grass' },
          { icon: Clock, label: 'Last Sync', value: world.last_sync ? formatDate(world.last_sync).split(',')[0] : 'Never', color: 'text-mc-gold' },
        ].map(({ icon: Icon, label, value, color }) => (
          <div key={label} className="pixel-card flex items-center gap-4">
            <Icon size={28} className={color} />
            <div>
              <p className="text-xs font-semibold text-black/50 uppercase tracking-wider">{label}</p>
              <p className="text-xl font-bold text-white">{value}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Upload */}
      <div className="pixel-card p-5 md:p-6">
        <h2 className="text-shadow text-lg font-bold text-white uppercase tracking-wider mb-5">
          Create New Backup
        </h2>
        <div className="border-4 border-dashed border-black/30 p-8 md:p-12 text-center">
          <Upload size={44} className="mx-auto text-black/30 mb-4" />
          <p className="text-base font-semibold text-black/60 mb-5">
            Upload your world as a ZIP file
          </p>
          <label className="inline-block">
            <input
              type="file"
              accept=".zip"
              onChange={handleFileUpload}
              className="hidden"
              disabled={uploading}
            />
            <span className="pixel-btn py-3 px-8 text-sm cursor-pointer inline-flex">
              <Upload size={16} />
              {uploading ? 'Uploading...' : 'Choose ZIP File'}
            </span>
          </label>
          <p className="text-xs font-medium text-black/40 mt-3">Maximum file size: 5 GB</p>
        </div>
      </div>

      {/* Backups List */}
      <div className="pixel-card p-5 md:p-6">
        <h2 className="text-shadow text-lg font-bold text-white uppercase tracking-wider mb-5">
          Backup History
        </h2>

        {backups.length === 0 ? (
          <div className="text-center py-12">
            <Package size={44} className="mx-auto text-black/30 mb-4" />
            <p className="text-sm font-semibold text-black/50">
              No backups yet. Upload your first backup above!
            </p>
          </div>
        ) : (
          <div className="space-y-2">
            {backups.map((backup) => (
              <div
                key={backup.id}
                className="flex items-center justify-between p-4 border-4 border-black/20 hover:bg-black/10 transition-colors gap-4"
              >
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-bold text-white truncate">{backup.filename}</p>
                  <div className="flex flex-wrap gap-x-4 text-xs font-medium text-white/50 mt-1">
                    <span>{(backup.size_mb || 0).toFixed(2)} MB</span>
                    <span>{formatDate(backup.created_at)}</span>
                    <span className="capitalize">{backup.backup_type}</span>
                  </div>
                </div>
                <div className="flex gap-2 shrink-0">
                  <button onClick={() => handleDownload(backup)} className="pixel-btn !py-2 !px-4 text-xs gap-1.5">
                    <Download size={14} />
                    Get
                  </button>
                  <button
                    onClick={() => setDeleteDialog({ open: true, backupId: backup.id, backupName: backup.filename })}
                    className="pixel-btn pixel-btn-danger !py-2 !px-4 text-xs gap-1.5"
                  >
                    <Trash2 size={14} />
                    Delete
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Modals */}
      {uploading && <UploadProgress progress={uploadProgress} fileName={uploadFileName} />}
      <ConfirmDialog
        isOpen={deleteDialog.open}
        title="Delete Backup"
        message={`Are you sure you want to delete "${deleteDialog.backupName}"? This action cannot be undone.`}
        onConfirm={handleDeleteBackup}
        onCancel={() => setDeleteDialog({ open: false, backupId: null, backupName: '' })}
        confirmText="Delete"
        cancelText="Cancel"
        danger
      />
    </div>
  );
}

export default WorldDetails;
