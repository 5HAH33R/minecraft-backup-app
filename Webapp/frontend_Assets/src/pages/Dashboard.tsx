/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import { useState } from 'react';
import { Link } from 'react-router-dom';
import { WorldCard } from '../components/WorldCard';
import { World } from '../types';
import { Search, Database, Cloud } from 'lucide-react';
import { motion } from 'motion/react';

const MOCK_WORLDS: World[] = [
  { id: '1', name: 'Survival Realm', status: 'synced', lastBackup: '2m ago', size: '156 MB' },
  { id: '2', name: 'Creative Build', status: 'syncing', lastBackup: '14h ago', size: '2.4 GB' },
  { id: '3', name: 'Hardcore S1', status: 'synced', lastBackup: '1m ago', size: '89 MB' },
  { id: '4', name: 'Redstone Lab', status: 'idle', lastBackup: '3d ago', size: '420 MB' },
  { id: '5', name: 'Ancient City', status: 'synced', lastBackup: '5h ago', size: '1.1 GB' },
];

export function Dashboard() {
  const [worlds] = useState<World[]>(MOCK_WORLDS);

  return (
    <div className="space-y-8 animate-in fade-in duration-700">
      {/* Hero Storage Section */}
      <section className="pixel-card bg-minecraft-stone p-6 border-b-8 border-minecraft-dirt-dark">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-2">
            <h2 className="text-shadow font-bold text-2xl text-white uppercase tracking-tight m-0">Drive Storage</h2>
            <p className="text-minecraft-dirt-dark font-bold text-xs uppercase opacity-80">Synchronizing with Google Drive</p>
          </div>
          <div className="flex-1 max-w-xl w-full">
            <div className="flex justify-between items-end mb-2">
              <div className="flex items-center gap-2 text-white font-bold text-[10px] uppercase">
                <Cloud size={14} className="text-minecraft-sky" />
                <span>Active Sync Status</span>
              </div>
              <span className="text-black font-bold text-[10px] uppercase">64% Full (9.6 GB / 15 GB)</span>
            </div>
            <div className="h-6 bg-black/40 border-4 border-black relative overflow-hidden">
               <motion.div 
                initial={{ width: 0 }}
                animate={{ width: '64%' }}
                className="h-full bg-minecraft-sky relative"
               >
                 <div className="absolute inset-0 bg-white/20 h-1/2"></div>
               </motion.div>
            </div>
          </div>
        </div>
      </section>

      <div className="flex justify-between items-center border-b-2 border-black/10 pb-4">
        <h2 className="text-shadow font-bold text-xl uppercase tracking-widest text-white m-0">
          YOUR WORLDS
        </h2>
        <div className="text-[12px] text-minecraft-stone uppercase tracking-tighter font-bold">
          Total: {worlds.length} Worlds Detected
        </div>
      </div>

      <div className="flex flex-col sm:flex-row gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-white/30" size={18} />
          <input 
            type="text" 
            placeholder="SEARCH FILE SYSTEM..." 
            className="pixel-input pl-12 h-12 uppercase tracking-tight font-bold text-xs"
          />
        </div>
        <Link to="/add-world" className="pixel-btn h-12 px-8 flex items-center justify-center">
          Add New World
        </Link>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
        {worlds.map((world, index) => (
          <motion.div
            key={world.id}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.05 }}
          >
            <WorldCard world={world} />
          </motion.div>
        ))}
        
        <Link 
          to="/add-world"
          className="pixel-card bg-minecraft-dirt border-4 border-black flex flex-col items-center justify-center min-h-[220px] gap-2 hover:brightness-110 active:translate-y-1 transition-all shadow-[8px_8px_0_0_rgba(0,0,0,0.3)]"
        >
          <div className="w-16 h-16 bg-white/20 border-4 border-black flex items-center justify-center">
            <span className="text-white text-5xl font-bold">+</span>
          </div>
          <span className="text-white font-bold text-[12px] uppercase tracking-wider text-shadow">Import Local World</span>
        </Link>
      </div>
    </div>
  );
}
