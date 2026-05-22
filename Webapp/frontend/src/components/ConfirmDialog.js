import React, { useEffect, useRef } from 'react';
import { AlertTriangle } from 'lucide-react';

function ConfirmDialog({ isOpen, title, message, onConfirm, onCancel, confirmText = 'Confirm', cancelText = 'Cancel', danger = false }) {
  const cancelRef = useRef(null);

  // Focus the cancel button on open (safest default)
  useEffect(() => {
    if (isOpen && cancelRef.current) {
      cancelRef.current.focus();
    }
  }, [isOpen]);

  // Close on Escape
  useEffect(() => {
    if (!isOpen) return;
    const handleEsc = (e) => {
      if (e.key === 'Escape') onCancel();
    };
    document.addEventListener('keydown', handleEsc);
    return () => document.removeEventListener('keydown', handleEsc);
  }, [isOpen, onCancel]);

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="confirm-title"
      aria-describedby="confirm-message"
    >
      <div className="pixel-card max-w-md w-full p-6">
        <div className="flex items-center gap-3 mb-4">
          {danger && <AlertTriangle size={22} className="text-red-400" aria-hidden="true" />}
          <h3 id="confirm-title" className="text-shadow text-lg font-bold text-white uppercase">{title}</h3>
        </div>

        <p id="confirm-message" className="text-sm font-medium text-black/60 mb-6 leading-relaxed">{message}</p>

        <div className="flex gap-3 justify-end">
          <button
            ref={cancelRef}
            onClick={onCancel}
            className="pixel-btn pixel-btn-secondary !py-2.5 !px-5 text-sm"
          >
            {cancelText}
          </button>
          <button
            onClick={onConfirm}
            className={`pixel-btn !py-2.5 !px-5 text-sm ${danger ? '!bg-red-500' : ''}`}
          >
            {confirmText}
          </button>
        </div>
      </div>
    </div>
  );
}

export default ConfirmDialog;
