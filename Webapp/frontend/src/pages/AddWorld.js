import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'react-toastify';
import { worldsAPI } from '../services/driveAPI';
import { ArrowLeft, Info } from 'lucide-react';

function AddWorld() {
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    local_path: '',
  });
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState({});
  const navigate = useNavigate();

  const validate = () => {
    const newErrors = {};
    if (!formData.name.trim()) {
      newErrors.name = 'World name is required';
    }
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    // Clear error when user starts typing
    if (errors[name]) {
      setErrors((prev) => ({ ...prev, [name]: '' }));
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validate()) {
      const firstError = Object.values(errors).find(Boolean) || 'Please fix the errors above';
      toast.error(firstError);
      return;
    }
    setLoading(true);
    try {
      await worldsAPI.createWorld(formData);
      toast.success('World added successfully!');
      navigate('/dashboard');
    } catch (error) {
      const msg = error.response?.data?.detail || 'Failed to add world';
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  };

  const inputClass = (field) =>
    `pixel-input ${errors[field] ? '!border-red-400 !shadow-[0_0_0_2px_rgba(248,113,113,0.3)]' : ''}`;

  return (
    <div className="space-y-8 max-w-2xl">
      {/* Back */}
      <button
        onClick={() => navigate('/dashboard')}
        className="inline-flex items-center gap-2 text-mc-sky hover:underline text-sm font-semibold"
      >
        <ArrowLeft size={16} aria-hidden="true" />
        Back to Dashboard
      </button>

      {/* Header */}
      <div className="space-y-1">
        <h1 className="text-shadow text-2xl md:text-3xl font-bold text-white uppercase" id="add-world-heading">
          Add New World
        </h1>
        <p className="text-sm font-medium text-white/50">
          Add a Minecraft world to start backing up
        </p>
      </div>

      {/* Form */}
      <form
        onSubmit={handleSubmit}
        className="pixel-card p-6 md:p-8 space-y-6"
        aria-labelledby="add-world-heading"
        noValidate
      >
        {/* Local Path */}
        <div className="space-y-2">
          <label className="block text-sm font-bold text-black/70" htmlFor="local_path">
            Local World Path <span className="text-xs font-normal text-black/40">(for auto-sync)</span>
          </label>
          <input
            type="text"
            id="local_path"
            name="local_path"
            value={formData.local_path}
            onChange={handleChange}
            placeholder="e.g., C:/Users/.../.minecraft/saves/MyWorld"
            className={inputClass('local_path')}
            aria-describedby="local_path_help"
          />
          <p id="local_path_help" className="text-xs font-medium text-black/50">
            Required for desktop agent auto-sync
          </p>
        </div>

        {/* World Name */}
        <div className="space-y-2">
          <label className="block text-sm font-bold text-black/70" htmlFor="name">
            World Name <span className="text-red-400" aria-hidden="true">*</span>
            <span className="sr-only">(required)</span>
          </label>
          <input
            type="text"
            id="name"
            name="name"
            value={formData.name}
            onChange={handleChange}
            placeholder="e.g., Survival World, Creative Build"
            className={inputClass('name')}
            required
            aria-required="true"
            aria-describedby={errors.name ? 'name_error' : 'name_help'}
            aria-invalid={!!errors.name}
          />
          {errors.name ? (
            <p id="name_error" className="text-xs font-bold text-red-300" role="alert">
              {errors.name}
            </p>
          ) : (
            <p id="name_help" className="text-xs font-medium text-black/50">
              Choose a memorable name for your world
            </p>
          )}
        </div>

        {/* Description */}
        <div className="space-y-2">
          <label className="block text-sm font-bold text-black/70" htmlFor="description">
            Description <span className="text-xs font-normal text-black/40">(optional)</span>
          </label>
          <textarea
            id="description"
            name="description"
            value={formData.description}
            onChange={handleChange}
            placeholder="Add a description for this world..."
            rows={4}
            className="pixel-input resize-none"
            aria-describedby="desc_help"
          />
          <p id="desc_help" className="text-xs font-medium text-black/50">
            Briefly describe what this world is about
          </p>
        </div>

        {/* Next Steps - info box */}
        <div className="bg-mc-sky/10 border-2 border-mc-sky/30 p-5 space-y-3" role="note" aria-label="Next steps after adding a world">
          <div className="flex items-center gap-2 text-mc-sky font-bold text-sm">
            <Info size={18} aria-hidden="true" />
            Next Steps:
          </div>
          <ol className="space-y-1.5 text-sm font-medium text-white/80 list-decimal list-inside">
            <li>Create your world entry here</li>
            <li>Upload your world's ZIP file from the world details page</li>
            <li>Enable auto-backup if desired</li>
          </ol>
        </div>

        {/* Buttons */}
        <div className="flex flex-col sm:flex-row gap-3 pt-2">
          <button
            type="button"
            onClick={() => navigate('/dashboard')}
            className="pixel-btn pixel-btn-secondary flex-1 py-3 text-sm"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={loading}
            className="pixel-btn flex-1 py-3 text-sm"
            aria-busy={loading}
          >
            {loading ? 'Adding...' : 'Add World'}
          </button>
        </div>
      </form>
    </div>
  );
}

export default AddWorld;
