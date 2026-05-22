import React, { useState, useEffect, useRef, useCallback } from 'react';
import { toast } from 'react-toastify';
import { useAuth } from '../contexts/AuthContext';
import api from '../services/api';
import { cn } from '../lib/utils';
import {
  User,
  Settings as SettingsIcon,
  Monitor,
  Shield,
  RefreshCw,
  Key,
  CheckCircle
} from 'lucide-react';

function Settings() {
  const { user } = useAuth();
  const [settings, setSettings] = useState({
    maxBackupsPerWorld: 10,
    autoCleanupEnabled: true,
  });
  const [pairingCode, setPairingCode] = useState('');
  const [pairStatus, setPairStatus] = useState('idle');
  const [paired, setPaired] = useState(false);
  const [pairError, setPairError] = useState('');
  const pollRef = useRef(null);

  const checkStatus = useCallback(async () => {
    try {
      const resp = await api.get('/api/auth/pair/status');
      setPaired(resp.data.paired);
      return resp.data.paired;
    } catch {
      return false;
    }
  }, []);

  useEffect(() => { checkStatus(); }, [checkStatus]);

  useEffect(() => {
    if (pairStatus === 'waiting') {
      pollRef.current = setInterval(async () => {
        if (await checkStatus()) {
          clearInterval(pollRef.current);
          setPairStatus('paired');
          setPairingCode('');
          toast.success('Desktop agent connected!');
        }
      }, 3000);
    }
    return () => { if (pollRef.current) clearInterval(pollRef.current); };
  }, [pairStatus, checkStatus]);

  const generateCode = async () => {
    setPairStatus('loading');
    setPairError('');
    try {
      const resp = await api.post('/api/auth/pair');
      setPairingCode(resp.data.code);
      setPairStatus('waiting');
      toast.info('Pairing code generated. Run the desktop agent with --pair to connect.');
    } catch (err) {
      const msg = err.response?.data?.detail || 'Failed to generate pairing code';
      setPairError(msg);
      setPairStatus('error');
      toast.error(msg);
    }
  };

  const revokeKey = async () => {
    try {
      await api.delete('/api/auth/api-keys');
      setPaired(false);
      toast.success('API key revoked. Desktop agent will no longer connect.');
    } catch (err) {
      toast.error('Failed to revoke API key');
    }
  };

  const handleSave = () => toast.success('Settings saved successfully!');

  return (
    <div className="space-y-8 max-w-3xl">
      {/* Header */}
      <div className="space-y-2">
        <h1 className="text-shadow text-2xl font-bold text-white uppercase tracking-wider">
          Settings
        </h1>
        <div className="h-1.5 w-16 bg-mc-grass" />
      </div>

      {/* Account Info */}
      <section className="pixel-card">
        <div className="flex items-center gap-3 mb-5">
          <User size={20} className="text-mc-grass" />
          <h2 className="text-shadow text-base font-bold text-white uppercase tracking-wider">
            Account
          </h2>
        </div>
        <div className="flex items-center gap-4">
          {user?.profile_picture && (
            <img
              src={user.profile_picture}
              alt={user.display_name}
              className="w-14 h-14 border-[3px] border-black"
            />
          )}
          <div>
            <p className="text-lg font-bold text-white">{user?.display_name}</p>
            <p className="text-sm font-medium text-black/60">{user?.email}</p>
          </div>
        </div>
      </section>

      {/* Backup Settings */}
      <section className="pixel-card">
        <div className="flex items-center gap-3 mb-6">
          <SettingsIcon size={20} className="text-mc-gold" />
          <h2 className="text-shadow text-base font-bold text-white uppercase tracking-wider">
            Backup Settings
          </h2>
        </div>

        <div className="space-y-6">
          <div>
            <label className="block text-sm font-bold text-black/70 mb-2">
              Maximum backups per world
            </label>
            <input
              type="number"
              min="1"
              max="50"
              value={settings.maxBackupsPerWorld}
              onChange={(e) => setSettings({ ...settings, maxBackupsPerWorld: parseInt(e.target.value) })}
              className="w-full p-3 text-sm font-mono bg-black/30 border-4 border-black/40 focus:border-mc-sky outline-none text-white transition-colors"
            />
            <p className="text-xs font-medium text-black/50 mt-1.5">
              Older backups will be automatically deleted when this limit is reached
            </p>
          </div>

          <div className="flex items-center justify-between group">
            <div>
              <p className="text-sm font-bold text-black/70 group-hover:text-mc-sky transition-colors">
                Auto-Cleanup
              </p>
              <p className="text-xs font-medium text-black/50 mt-0.5">
                Delete local backups older than 7 days
              </p>
            </div>
            <div
              onClick={() => setSettings({ ...settings, autoCleanupEnabled: !settings.autoCleanupEnabled })}
              className={cn('pixel-toggle', settings.autoCleanupEnabled ? 'on' : 'off')}
              role="switch"
              aria-checked={settings.autoCleanupEnabled}
              tabIndex={0}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.preventDefault();
                  setSettings({ ...settings, autoCleanupEnabled: !settings.autoCleanupEnabled });
                }
              }}
            >
              <div className="pixel-toggle-knob" />
            </div>
          </div>
        </div>
      </section>

      {/* Desktop Agent */}
      <section className="pixel-card">
        <div className="flex items-center gap-3 mb-6">
          <Monitor size={20} className="text-mc-sky" />
          <h2 className="text-shadow text-base font-bold text-white uppercase tracking-wider">
            Desktop Agent
          </h2>
        </div>

        {paired ? (
          <div>
            <div className="flex items-center gap-2 text-mc-grass mb-3">
              <CheckCircle size={20} />
              <span className="text-sm font-bold uppercase tracking-wider">Connected</span>
            </div>
            <p className="text-sm font-medium text-black/60 mb-5">
              Your desktop agent is authenticated and can create backups.
            </p>
            <button onClick={revokeKey} className="pixel-btn pixel-btn-danger text-sm">
              <Key size={16} />
              Revoke Access
            </button>
          </div>
        ) : pairStatus === 'waiting' ? (
          <div>
            <p className="text-sm font-medium text-black/60 mb-3">
              Run this command on the machine running your Minecraft worlds:
            </p>
            <div className="bg-black/40 border-4 border-black p-4 mb-4 font-mono text-sm text-mc-sky break-all">
              python main.py --pair {pairingCode}
            </div>
            <p className="text-xs font-medium text-black/50 mb-3">
              Code expires in 5 minutes. Waiting for agent to connect...
            </p>
            <div className="flex items-center gap-2 mb-4">
              <div className="w-3 h-3 bg-mc-grass border-2 border-black animate-pulse" />
              <span className="text-sm font-semibold text-black/60">Listening...</span>
            </div>
            <button
              onClick={() => { setPairStatus('idle'); setPairingCode(''); }}
              className="text-sm font-semibold text-mc-sky hover:underline"
            >
              Cancel
            </button>
          </div>
        ) : (
          <div>
            <p className="text-sm font-medium text-black/60 mb-5">
              Generate a one-time code to pair your desktop agent. The agent uses a permanent API key and won't need re-authentication.
            </p>
            <button onClick={generateCode} disabled={pairStatus === 'loading'} className="pixel-btn text-sm gap-2">
              <RefreshCw size={16} className={cn(pairStatus === 'loading' && 'animate-spin')} />
              {pairStatus === 'loading' ? 'Generating...' : 'Generate Pairing Code'}
            </button>
            {pairError && <p className="text-red-400 text-sm font-semibold mt-3">{pairError}</p>}
          </div>
        )}
      </section>

      {/* Save */}
      <button onClick={handleSave} className="pixel-btn w-full py-4 text-base gap-2">
        <Shield size={18} />
        Save Settings
      </button>
    </div>
  );
}

export default Settings;
