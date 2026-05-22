/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { ArrowLeft, Info } from 'lucide-react';
import { motion } from 'motion/react';

export function AddWorldPage() {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    path: '',
    name: '',
    description: ''
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    // In a real app, this would call an API
    console.log('Adding world:', formData);
    navigate('/');
  };

  return (
    <div className="max-w-3xl mx-auto space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
      <Link to="/" className="inline-flex items-center gap-2 text-minecraft-sky hover:underline font-bold text-sm uppercase tracking-tighter">
        <ArrowLeft size={16} />
        Back to Dashboard
      </Link>

      <div className="space-y-1">
        <h1 className="text-shadow font-bold text-3xl text-white uppercase tracking-tight m-0">
          Add New World
        </h1>
        <p className="text-minecraft-stone font-bold text-xs uppercase">
          Add a Minecraft world to start backing up
        </p>
      </div>

      <div className="pixel-card bg-white p-8 space-y-8">
        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="space-y-2">
            <label className="block text-[11px] font-bold text-minecraft-dirt-dark uppercase tracking-wide">
              Local World Path (for auto-sync)
            </label>
            <input
              type="text"
              placeholder="e.g., C:/Users/YourName/AppData/Roaming/.minecraft/saves/MyWorld"
              className="w-full p-4 border-2 border-gray-200 font-mono text-sm focus:border-minecraft-sky outline-none transition-colors text-black"
              value={formData.path}
              onChange={(e) => setFormData({ ...formData, path: e.target.value })}
            />
            <p className="text-[9px] font-bold text-gray-400 uppercase">Required for desktop agent auto-sync</p>
          </div>

          <div className="space-y-2">
            <label className="block text-[11px] font-bold text-minecraft-dirt-dark uppercase tracking-wide">
              World Name *
            </label>
            <input
              type="text"
              required
              placeholder="e.g., Survival World, Creative Build"
              className="w-full p-4 border-2 border-gray-200 font-mono text-sm focus:border-minecraft-sky outline-none transition-colors text-black"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            />
          </div>

          <div className="space-y-2">
            <label className="block text-[11px] font-bold text-minecraft-dirt-dark uppercase tracking-wide">
              Description (optional)
            </label>
            <textarea
              placeholder="Add a description for this world..."
              rows={4}
              className="w-full p-4 border-2 border-gray-200 font-mono text-sm focus:border-minecraft-sky outline-none transition-colors text-black resize-none"
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
            />
          </div>

          <div className="bg-blue-50 border-2 border-blue-100 p-6 space-y-3">
            <div className="flex items-center gap-2 text-blue-800 font-bold text-sm tracking-tight">
              <Info size={18} />
              Next Steps:
            </div>
            <ul className="space-y-2 text-[11px] font-bold text-blue-700/80 uppercase list-decimal list-inside">
              <li>Create your world entry here</li>
              <li>Upload your world's ZIP file from the world details page</li>
              <li>Enable auto-backup if desired</li>
            </ul>
          </div>

          <div className="flex flex-col sm:flex-row gap-4 pt-4">
            <button
              type="button"
              onClick={() => navigate('/')}
              className="flex-1 pixel-btn !bg-gray-200 !text-gray-600 !border-gray-300 font-bold"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="flex-1 pixel-btn !bg-blue-500 !border-blue-700 font-bold"
            >
              Add World
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
