/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import { useState } from 'react';
import { Sun, Moon, Cpu, Globe, Shield, RefreshCw } from 'lucide-react';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function SettingsPage() {
  const [theme, setTheme] = useState<'day' | 'night'>('night');
  const [autoSync, setAutoSync] = useState(true);
  const [cleanup, setCleanup] = useState(false);

  return (
    <div className="max-w-4xl mx-auto space-y-10 animate-in fade-in slide-in-from-bottom-4 duration-700">
      <div className="space-y-2">
        <h1 className="font-press-start text-xl text-white">Options</h1>
        <div className="h-1 w-20 bg-minecraft-grass"></div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 space-y-8">
          {/* Pairing Section */}
          <section className="pixel-card bg-minecraft-obsidian/40 space-y-6">
            <div className="flex items-center gap-3">
              <Globe className="text-minecraft-sky" size={20} />
              <h2 className="font-press-start text-xs text-white uppercase">Device Pairing</h2>
            </div>
            <p className="text-[10px] text-minecraft-stone font-press-start leading-relaxed uppercase">
              Enter this code on your Minecraft Launcher to link this account.
            </p>
            <div className="bg-black/60 p-8 border-4 border-minecraft-stone flex items-center justify-center relative overflow-hidden group">
              <div className="absolute inset-0 bg-blue-500/5 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none"></div>
              <span className="font-press-start text-2xl md:text-4xl text-minecraft-sky tracking-[0.2em] drop-shadow-[0_4px_0_rgba(0,0,0,0.8)]">
                ABC-123
              </span>
            </div>
            <div className="flex justify-center">
              <button className="text-[8px] font-press-start text-minecraft-sky hover:underline flex items-center gap-2 uppercase">
                <RefreshCw size={12} />
                Generate New Code
              </button>
            </div>
          </section>

          {/* Preferences */}
          <section className="pixel-card bg-minecraft-obsidian/40 space-y-8">
            <div className="flex items-center gap-3">
              <Cpu className="text-minecraft-gold" size={20} />
              <h2 className="font-press-start text-xs text-white uppercase">System Settings</h2>
            </div>

            <div className="space-y-6">
              <div className="flex items-center justify-between group">
                <div className="space-y-2">
                  <div className="font-press-start text-[10px] text-white uppercase group-hover:text-minecraft-sky transition-colors">Auto-Sync Worlds</div>
                  <div className="text-[8px] text-minecraft-stone font-press-start uppercase">Sync worlds every 30 minutes</div>
                </div>
                <button 
                  onClick={() => setAutoSync(!autoSync)}
                  className={cn(
                    "w-16 h-8 border-4 border-black transition-all flex items-center px-1",
                    autoSync ? "bg-minecraft-grass" : "bg-red-500"
                  )}
                >
                  <div className={cn(
                    "w-6 h-4 bg-white border-2 border-black transition-transform",
                    autoSync ? "translate-x-7" : "translate-x-0"
                  )}></div>
                </button>
              </div>

              <div className="border-t-4 border-black/20 pt-6 flex items-center justify-between group">
                <div className="space-y-2">
                  <div className="font-press-start text-[10px] text-white uppercase group-hover:text-minecraft-sky transition-colors">Auto-Cleanup</div>
                  <div className="text-[8px] text-minecraft-stone font-press-start uppercase">Delete local backups older than 7 days</div>
                </div>
                <button 
                  onClick={() => setCleanup(!cleanup)}
                  className={cn(
                    "w-16 h-8 border-4 border-black transition-all flex items-center px-1",
                    cleanup ? "bg-minecraft-grass" : "bg-red-500"
                  )}
                >
                  <div className={cn(
                    "w-6 h-4 bg-white border-2 border-black transition-transform",
                    cleanup ? "translate-x-7" : "translate-x-0"
                  )}></div>
                </button>
              </div>
            </div>
          </section>
        </div>

        <div className="space-y-8">
          {/* Day/Night Toggle */}
          <section className="pixel-card bg-minecraft-obsidian/40 space-y-6">
            <h2 className="font-press-start text-xs text-white uppercase">Atmosphere</h2>
            <div className="flex gap-4">
              <button 
                onClick={() => setTheme('day')}
                className={cn(
                  "flex-1 p-4 border-4 transition-all flex flex-col items-center gap-3",
                  theme === 'day' ? "border-minecraft-gold bg-minecraft-gold/20" : "border-black bg-black/20 opacity-50"
                )}
              >
                <Sun className={theme === 'day' ? "text-minecraft-gold" : "text-white"} size={24} />
                <span className="font-press-start text-[8px] uppercase">Day</span>
              </button>
              <button 
                onClick={() => setTheme('night')}
                className={cn(
                  "flex-1 p-4 border-4 transition-all flex flex-col items-center gap-3",
                  theme === 'night' ? "border-minecraft-sky bg-minecraft-sky/20" : "border-black bg-black/20 opacity-50"
                )}
              >
                <Moon className={theme === 'night' ? "text-minecraft-sky" : "text-white"} size={24} />
                <span className="font-press-start text-[8px] uppercase">Night</span>
              </button>
            </div>
          </section>

          {/* Security */}
          <section className="pixel-card bg-minecraft-obsidian/40 space-y-6">
            <div className="flex items-center gap-3">
              <Shield className="text-minecraft-grass" size={20} />
              <h2 className="font-press-start text-xs text-white uppercase">Security</h2>
            </div>
            <div className="space-y-4">
              <button className="pixel-btn w-full !bg-red-500 text-[8px]">
                Purge All Backups
              </button>
              <button className="pixel-btn w-full !bg-minecraft-obsidian border-minecraft-stone text-[8px]">
                Export Logs
              </button>
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}
