import React from 'react';
import { useNavigate } from 'react-router-dom';
import { cn } from '../lib/utils';
import { Trash2, HardDrive, Package, Clock } from 'lucide-react';

function WorldCard({ world, onDelete }) {
  const navigate = useNavigate();

  const formatDate = (d) => d ? new Date(d).toLocaleString() : 'Never';

  const handleDelete = (e) => {
    e.stopPropagation();
    if (window.confirm(`Remove "${world.name}"? Backups on Google Drive won't be deleted.`)) {
      onDelete(world.id);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      navigate(`/worlds/${world.id}`);
    }
  };

  const status = world.auto_sync_enabled ? 'synced' : 'idle';
  const statusLabel = status === 'synced' ? 'Auto-sync active' : 'Auto-sync off';
  const statusColor = status === 'synced' ? 'bg-mc-grass' : 'bg-mc-gold';

  return (
    <div
      onClick={() => navigate(`/worlds/${world.id}`)}
      onKeyDown={handleKeyDown}
      tabIndex={0}
      role="button"
      aria-label={`${world.name} - ${world.total_backups || 0} backups, ${(world.total_size_mb || 0).toFixed(2)} MB total. Click to view details.`}
      className="pixel-card cursor-pointer hover:brightness-110 transition-all active:translate-y-0.5 group"
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="space-y-1 min-w-0 flex-1 mr-3">
          <h3 className="text-shadow text-lg font-bold text-white truncate">
            {world.name}
          </h3>
          {world.description && (
            <p className="text-sm font-medium text-black/60 line-clamp-1">{world.description}</p>
          )}
        </div>
        <div className="flex items-center gap-2 shrink-0">
          {world.auto_sync_enabled && (
            <span className="text-[11px] font-bold px-2 py-0.5 bg-mc-grass/40 border-2 border-black text-black uppercase">
              Auto
            </span>
          )}
          {/* Status indicator with text label for screen readers */}
          <div
            className={cn('w-3.5 h-3.5 border-2 border-black', statusColor)}
            role="img"
            aria-label={statusLabel}
            title={statusLabel}
          />
          <span className="sr-only">{statusLabel}</span>
        </div>
      </div>

      {/* Stats */}
      <div className="space-y-2 mb-4">
        {[
          { icon: Package, text: `${world.total_backups || 0} backup${(world.total_backups || 0) !== 1 ? 's' : ''}` },
          { icon: HardDrive, text: `${(world.total_size_mb || 0).toFixed(2)} MB` },
          { icon: Clock, text: `Last sync: ${world.last_sync ? formatDate(world.last_sync) : 'Never'}` },
        ].map(({ icon: Icon, text }) => (
          <div key={text} className="flex items-center gap-2">
            <Icon size={14} className="text-black/40 shrink-0" aria-hidden="true" />
            <span className="text-sm font-medium text-black/60 truncate">{text}</span>
          </div>
        ))}
      </div>

      {/* Actions */}
      <div className="grid grid-cols-2 gap-2" onClick={(e) => e.stopPropagation()}>
        <button
          onClick={(e) => { e.stopPropagation(); navigate(`/worlds/${world.id}`); }}
          className="pixel-btn text-sm !py-2.5"
          aria-label={`View details for ${world.name}`}
        >
          View Details
        </button>
        <button
          onClick={handleDelete}
          className="pixel-btn pixel-btn-danger text-sm !py-2.5 gap-1.5"
          aria-label={`Remove ${world.name}`}
        >
          <Trash2 size={14} aria-hidden="true" />
          Remove
        </button>
      </div>
    </div>
  );
}

export default WorldCard;
