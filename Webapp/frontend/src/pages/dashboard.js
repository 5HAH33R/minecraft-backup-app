import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'react-toastify';
import WorldCard from '../components/WorldCard';
import StorageWidget from '../components/StorageWidget';
import { worldsAPI } from '../services/driveAPI';
import { Plus, Search, Box } from 'lucide-react';

function Dashboard() {
  const [worlds, setWorlds] = useState([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    loadWorlds();
  }, []);

  const loadWorlds = async () => {
    try {
      const response = await worldsAPI.listWorlds();
      setWorlds(response.data);
    } catch (error) {
      console.error('Failed to load worlds', error);
      toast.error('Failed to load worlds');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteWorld = async (worldId) => {
    try {
      await worldsAPI.deleteWorld(worldId);
      setWorlds((prev) => prev.filter((w) => w.id !== worldId));
      toast.success('World removed successfully');
    } catch (error) {
      const msg = error.response?.data?.detail || 'Failed to remove world';
      toast.error(msg);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-32">
        <div className="text-center">
          <div className="w-14 h-14 bg-mc-grass border-4 border-black mx-auto animate-pulse" aria-hidden="true" />
          <p className="mt-5 text-base font-semibold text-white/60">Loading your worlds...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Storage Widget */}
      <StorageWidget />

      {/* Section header */}
      <div className="flex items-center justify-between border-b-2 border-white/10 pb-4">
        <h2 className="text-shadow text-xl md:text-2xl font-bold text-white uppercase tracking-wider">
          Your Worlds
        </h2>
        <span className="text-sm font-semibold text-white/40 uppercase tracking-wider">
          {worlds.length} total
        </span>
      </div>

      {/* Search & Add */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-white/30" size={18} aria-hidden="true" />
          <label htmlFor="world-search" className="sr-only">Search worlds</label>
          <input
            id="world-search"
            type="text"
            placeholder="Search worlds..."
            className="pixel-input pl-11 h-[48px] text-sm"
          />
        </div>
        <button
          onClick={() => navigate('/add-world')}
          className="pixel-btn h-[48px] px-8 text-sm shrink-0 gap-2"
        >
          <Plus size={18} />
          Add World
        </button>
      </div>

      {/* Empty state / Grid */}
      {worlds.length === 0 ? (
        <div className="pixel-card py-16 text-center">
          <Box size={56} className="mx-auto text-black/30 mb-4" />
          <h3 className="text-shadow text-lg font-bold text-white uppercase mb-2">No worlds yet</h3>
          <p className="text-sm font-semibold text-black/60 mb-6">
            Add your first Minecraft world to start backing up!
          </p>
          <button
            onClick={() => navigate('/add-world')}
            className="pixel-btn text-sm gap-2"
          >
            <Plus size={16} />
            Add Your First World
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-5">
          {worlds.map((world) => (
            <WorldCard key={world.id} world={world} onDelete={handleDeleteWorld} />
          ))}
        </div>
      )}
    </div>
  );
}

export default Dashboard;
