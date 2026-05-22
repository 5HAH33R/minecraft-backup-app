import React, { useState, useEffect } from 'react';
import { driveAPI } from '../services/driveAPI';
import { Cloud } from 'lucide-react';

function StorageWidget() {
  const [storage, setStorage] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => { loadStorage(); }, []);

  const loadStorage = async () => {
    try {
      const res = await driveAPI.getStorageInfo();
      setStorage(res.data);
    } catch (err) {
      console.error('Failed to load storage info', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="pixel-card animate-pulse">
        <div className="h-5 bg-black/20 w-3/4 mb-4" />
        <div className="h-8 bg-black/20 border-[3px] border-black mb-2" />
        <div className="h-4 bg-black/20 w-1/2" />
      </div>
    );
  }

  if (!storage) return null;

  const pct = Math.min(storage.percent_used || (storage.used_gb / storage.total_gb * 100), 100);

  return (
    <div className="pixel-card-dark border-4 border-mc-dirt-dark p-5 md:p-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="space-y-1">
          <h3 className="text-shadow text-xl font-bold text-white uppercase tracking-tight">
            Drive Storage
          </h3>
          <p className="text-sm font-medium text-white/50">
            Synchronized with Google Drive
          </p>
        </div>

        <div className="flex-1 max-w-xl w-full">
          <div className="flex items-center justify-between mb-1.5">
            <div className="flex items-center gap-2">
              <Cloud size={16} className="text-mc-sky" />
              <span className="text-sm font-semibold text-white/70">Sync Active</span>
            </div>
            <span className="text-sm font-bold text-white">
              {storage.used_gb} GB / {storage.total_gb} GB
            </span>
          </div>
          <div className="h-6 bg-black/40 border-[3px] border-black relative overflow-hidden">
            <div
              className="h-full bg-mc-sky transition-all duration-700 relative"
              style={{ width: `${pct}%` }}
            >
              <div className="absolute inset-0 bg-white/10 h-1/2" />
            </div>
          </div>
          <div className="flex justify-between mt-1.5">
            <span className="text-xs font-medium text-white/40">
              {storage.available_gb || (storage.total_gb - storage.used_gb).toFixed(1)} GB available
            </span>
            {pct > 90 && (
              <span className="text-xs font-bold text-red-300">Storage almost full!</span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default StorageWidget;
