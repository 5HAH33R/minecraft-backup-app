/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import { World } from '../types';
import { motion } from 'motion/react';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

interface WorldCardProps {
  world: World;
}

export function WorldCard({ world }: WorldCardProps) {
  return (
    <motion.div 
      whileHover={{ y: -4 }}
      className="pixel-card group"
    >
      <div className="flex items-start justify-between">
        <div className="space-y-1">
          <h3 className="font-bold text-black text-sm uppercase tracking-tight">
            {world.name}
          </h3>
          <div className="text-[10px] text-minecraft-dirt-dark/80 font-bold">
            Last Backup: {world.lastBackup}
          </div>
        </div>
        <div className={cn(
          "w-3 h-3 border-2 border-black",
          world.status === 'synced' ? "bg-minecraft-grass" :
          world.status === 'idle' ? "bg-minecraft-gold" :
          world.status === 'syncing' ? "bg-minecraft-sky animate-pulse" : "bg-red-500"
        )}></div>
      </div>

      <div className="bg-black/90 h-32 my-4 border-2 border-black flex items-center justify-center relative group-hover:bg-black/80 transition-colors">
        <div className="text-white/10 font-bold select-none text-xs">PREVIEW_IMG</div>
        {world.status === 'syncing' && (
          <div className="absolute inset-0 flex items-center justify-center bg-minecraft-sky/10">
             <div className="w-12 h-1 bg-black overflow-hidden">
                <div className="h-full bg-minecraft-sky animate-[move_2s_infinite]" style={{ width: '40%' }}></div>
             </div>
          </div>
        )}
      </div>

      <div className="grid grid-cols-2 gap-2">
        <button className="pixel-btn text-[9px] py-1.5 h-auto">Sync</button>
        <button className="pixel-btn-secondary text-[9px] py-1.5 h-auto">Config</button>
      </div>
    </motion.div>
  );
}
