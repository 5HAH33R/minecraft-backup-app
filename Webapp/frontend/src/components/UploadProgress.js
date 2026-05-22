import React from 'react';
import { Upload, CheckCircle } from 'lucide-react';

function UploadProgress({ progress, fileName }) {
  const isComplete = progress === 100;

  return (
    <div
      className="fixed bottom-6 right-6 pixel-card-dark border-4 border-black p-5 w-80 z-50 shadow-2xl"
      role="status"
      aria-live="polite"
      aria-label={`Upload ${isComplete ? 'complete' : 'in progress'}: ${progress}%`}
    >
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Upload size={18} className="text-mc-sky" aria-hidden="true" />
          <h4 className="text-sm font-bold text-white uppercase">
            {isComplete ? 'Complete' : 'Uploading'}
          </h4>
        </div>
        <span className="text-sm font-bold text-white" aria-hidden="true">{progress}%</span>
      </div>

      <p className="text-xs font-medium text-white/60 mb-3 truncate">{fileName}</p>

      {/* Progress bar */}
      <div className="h-5 bg-black/40 border-[3px] border-black overflow-hidden" role="progressbar" aria-valuenow={progress} aria-valuemin={0} aria-valuemax={100} aria-label={`Upload progress: ${progress}%`}>
        <div
          className="h-full bg-mc-sky transition-all duration-300 flex items-center justify-end"
          style={{ width: `${Math.max(progress, 8)}%` }}
        >
          {progress > 20 && (
            <span className="text-[10px] font-bold text-white mr-1.5" aria-hidden="true">{progress}%</span>
          )}
        </div>
      </div>

      {isComplete && (
        <div className="flex items-center gap-2 mt-3">
          <CheckCircle size={16} className="text-mc-grass" aria-hidden="true" />
          <p className="text-xs font-bold text-mc-grass uppercase">Upload complete! Processing...</p>
        </div>
      )}
    </div>
  );
}

export default UploadProgress;
