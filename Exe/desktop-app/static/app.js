// ─── State ─────────────────────────────────────────────────────────
const state = {
  token: null,
  refreshToken: null,
  user: null,
  worlds: [],
  currentWorld: null,
  backups: [],
  storage: null,
  page: "loading",
  params: {},
  _refreshInterval: null,
};

// ─── API Helpers ──────────────────────────────────────────────────
const API = {
  async request(method, path, body) {
    const opts = {
      method,
      headers: { "Accept": "application/json" },
    };
    if (state.token) {
      opts.headers["Authorization"] = `Bearer ${state.token}`;
    }
    if (body && !(body instanceof FormData)) {
      opts.headers["Content-Type"] = "application/json";
      opts.body = JSON.stringify(body);
    } else if (body instanceof FormData) {
      opts.body = body;
    }
    const res = await fetch(path, opts);
    if (res.status === 401 && state.refreshToken) {
      const refreshed = await API.refreshToken();
      if (refreshed) {
        opts.headers["Authorization"] = `Bearer ${state.token}`;
        const retry = await fetch(path, opts);
        return retry;
      } else {
        logout();
        throw new Error("Session expired");
      }
    }
    return res;
  },

  async get(path) { return this.request("GET", path); },
  async post(path, body) { return this.request("POST", path, body); },
  async patch(path, body) { return this.request("PATCH", path, body); },
  async put(path, body) { return this.request("PUT", path, body); },
  async del(path) { return this.request("DELETE", path); },

  async refreshToken() {
    try {
      const r = await fetch("/api/auth/refresh", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh_token: state.refreshToken }),
      });
      if (r.ok) {
        const data = await r.json();
        state.token = data.access_token;
        localStorage.setItem("token", state.token);
        return true;
      }
    } catch (e) { /* ignore */ }
    return false;
  },

  async json(method, path, body) {
    const res = await this.request(method, path, body);
    return res.json();
  },
};

// ─── Toast ─────────────────────────────────────────────────────────
function toast(message, type = "info") {
  const el = document.createElement("div");
  el.className = `toast toast-${type}`;
  el.textContent = message;
  el.setAttribute("role", "alert");
  el.setAttribute("aria-live", "polite");
  document.getElementById("toasts").appendChild(el);
  setTimeout(() => { el.style.opacity = "0"; el.style.transform = "translateX(20px)"; el.style.transition = "all 0.3s"; }, 3500);
  setTimeout(() => el.remove(), 3900);
  return el;
}

// ─── Confirm Dialog ───────────────────────────────────────────────
function confirmDialog(message, confirmText = "Confirm", danger = false) {
  return new Promise((resolve) => {
    const overlay = document.getElementById("confirm-overlay");
    const dialog = document.getElementById("confirm-dialog");
    dialog.innerHTML = `
      <p class="text-[#FAFBD3] text-xl mb-6 font-pixel">${message}</p>
      <div class="flex justify-end gap-3">
        <button class="pixel-btn bg-mc-darkwood " onclick="hideConfirm()">Cancel</button>
        <button class="pixel-btn ${danger ? 'pixel-btn-danger' : 'pixel-btn-primary'} " id="confirm-btn">${confirmText}</button>
      </div>
    `;
    overlay.classList.remove("hidden");
    overlay.classList.add("flex");
    document.getElementById("confirm-btn").onclick = () => { hideConfirm(); resolve(true); };
  });
}
function hideConfirm() {
  document.getElementById("confirm-overlay").classList.add("hidden");
  document.getElementById("confirm-overlay").classList.remove("flex");
}

// ─── Auth ──────────────────────────────────────────────────────────
function logout() {
  state.token = null;
  state.refreshToken = null;
  state.user = null;
  localStorage.removeItem("token");
  localStorage.removeItem("refreshToken");
  navigate("login");
}

// ─── Navigation ───────────────────────────────────────────────────
function navigate(page, params = {}) {
  if (state._refreshInterval) {
    clearInterval(state._refreshInterval);
    state._refreshInterval = null;
  }
  state.page = page;
  state.params = params;
  render();
}

// ─── Main Render ──────────────────────────────────────────────────
function render() {
  const app = document.getElementById("app");
  if (state.page === "login") {
    app.innerHTML = renderLogin();
  } else if (state.page === "loading") {
    app.innerHTML = `<div class="flex items-center justify-center min-h-screen minecraft-bg-grid"><div class="spinner" style="width:40px;height:40px;border-width:4px"></div></div>`;
  } else {
    app.innerHTML = renderMainLayout();
    renderPage();
    attachNavEvents();
  }
}

function renderMainLayout() {
  const initial = (state.user?.display_name || '?')[0];
  const avatar = state.user?.profile_picture
    ? `<img src="${escHtml(state.user.profile_picture)}" class="w-9 h-9 border-3 border-black" alt="${escHtml(state.user.display_name || '')}">`
    : `<div class="w-9 h-9 bg-mc-grass border-3 border-black flex items-center justify-center text-sm font-bold text-[#FAFBD3]" aria-hidden="true">${escHtml(initial)}</div>`;
  return `
    <nav class="pixel-nav sticky top-0 z-30 px-4 h-16 flex items-center justify-between">
      <div class="flex items-center gap-4">
        <a href="#" class="flex items-center gap-3 font-press-start text-sm text-[#FAFBD3] text-shadow no-underline" onclick="navigate('dashboard');return false" aria-label="Dashboard">
          <div class="w-8 h-8 bg-mc-grass border-3 border-black shrink-0"></div>
          <span class="hidden sm:inline">BACKUP PRO</span>
        </a>
        <div class="hidden sm:flex items-center gap-1 ml-2">
          <button class="pixel-btn bg-[#995A24]  py-2 px-3 ${state.page === 'dashboard' ? '!bg-mc-grass' : ''}" onclick="navigate('dashboard')">Dashboard</button>
          <button class="pixel-btn bg-[#995A24]  py-2 px-3 ${state.page === 'settings' ? '!bg-mc-grass' : ''}" onclick="navigate('settings')">Settings</button>
        </div>
      </div>
      <div class="flex items-center gap-3">
        ${state.user ? `<span class="text-sm text-[#FAFBD3] hidden sm:block text-shadow">${escHtml(state.user.display_name || '')}</span>` : ''}
        ${avatar}
      </div>
    </nav>
    <main class="minecraft-bg-grid min-h-[calc(100vh-4rem)]">
      <div class="max-w-6xl mx-auto px-4 py-8 page-enter" id="page-content"></div>
    </main>
  `;
}

function renderPage() {
  const container = document.getElementById("page-content");
  if (!container) return;
  switch (state.page) {
    case "dashboard": container.innerHTML = renderDashboard(); loadDashboardData(); break;
    case "add-world": container.innerHTML = renderAddWorldForm(); break;
    case "world-details": container.innerHTML = renderWorldDetails(); loadWorldDetails(); break;
    case "settings": container.innerHTML = renderSettings(); loadSettingsData(); break;
    case "login": return; // handled by render()
    default: container.innerHTML = renderDashboard(); loadDashboardData();
  }
}

function attachNavEvents() {
  document.querySelectorAll("[onclick^=navigate]").forEach(el => {
    // Already handled via onclick
  });
}

// ─── Login Page ────────────────────────────────────────────────────
function renderLogin() {
  return `
    <div class="min-h-screen minecraft-bg-grid flex items-center justify-center px-4">
      <div class="pixel-card max-w-sm w-full text-center space-y-8">
        <div class="space-y-4">
          <div class="flex justify-center">
            <div class="w-16 h-16 bg-mc-grass border-4 border-black shadow-[4px_4px_0_0_rgba(0,0,0,0.3)] flex items-center justify-center">
              <svg class="w-8 h-8 text-[#FAFBD3]" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4"/></svg>
            </div>
          </div>
          <h1 class="text-shadow font-press-start text-xl text-[#FAFBD3] tracking-wider drop-shadow-[0_4px_0_rgba(0,0,0,0.5)] leading-relaxed">
            MINECRAFT<br/>BACKUP PRO
          </h1>
          <p class="font-bold text-sm text-[#995A24] uppercase tracking-tight font-pixel">
            Production Grade World Syncing
          </p>
        </div>
        <div class="space-y-4">
          <button class="pixel-btn pixel-btn-primary w-full justify-center py-4 text-sm" onclick="handleLogin()">
            Sign in with Google
          </button>
          <div class="flex justify-between text-[14px] font-bold text-[#995A24] uppercase font-pixel">
            <span>Ver 2.4.0</span>
            <span>BlockDev</span>
          </div>
        </div>
      </div>
    </div>
  `;
}

async function handleLogin() {
  try {
    const data = await API.json("GET", "/api/auth/login");
    if (data.auth_url) {
      window.location.href = data.auth_url;
    }
  } catch (e) {
    toast("Failed to start login: " + e.message, "error");
  }
}

// ─── Dashboard ─────────────────────────────────────────────────────
function renderDashboard() {
  return `
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
      <h1 class="font-press-start text-xl text-[#FAFBD3] text-shadow">WORLDS</h1>
      <button class="pixel-btn pixel-btn-primary " onclick="navigate('add-world')">
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/></svg>
        Add World
      </button>
    </div>
    <div class="mb-4">
      <input class="pixel-input" id="world-search" placeholder="SEARCH WORLDS..." oninput="filterWorlds()" aria-label="Search worlds">
    </div>
    <div id="storage-widget" class="mb-6"></div>
    <div id="worlds-container">
      <div class="flex justify-center py-12"><div class="spinner" style="width:32px;height:32px;border-width:4px"></div></div>
    </div>
  `;
}

async function loadDashboardData() {
  try {
    const [worldsData, storageData] = await Promise.all([
      API.json("GET", "/api/worlds"),
      API.json("GET", "/api/drive/storage").catch(() => null),
    ]);
    state.worlds = Array.isArray(worldsData) ? worldsData : [];
    state.storage = storageData;
    renderWorldList();
    renderStorageWidget();
  } catch (e) {
    document.getElementById("worlds-container").innerHTML = `<div class="empty-state">Failed to load worlds: ${e.message}</div>`;
  }
}

function renderStorageWidget() {
  const el = document.getElementById("storage-widget");
  if (!el) return;
  if (!state.storage) { el.innerHTML = ""; return; }
  const s = state.storage;
  el.innerHTML = `
    <div class="pixel-card-dark flex items-center gap-3 text-lg">
      <svg class="w-5 h-5 text-mc-sky shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"/></svg>
      <span class="text-mc-wood font-pixel">Drive Storage:</span>
      <span class="font-bold text-mc-cream">${s.used_gb}GB</span>
      <span class="text-mc-wood">/ ${s.total_gb}GB</span>
      <span class="text-mc-wood">(${s.percent_used}%)</span>
      <div class="flex-1 max-w-xs ml-2"><div class="progress-bar"><div class="progress-bar-fill" style="width:${Math.min(s.percent_used, 100)}%"></div></div></div>
    </div>
  `;
}

function renderWorldList(filter) {
  const container = document.getElementById("worlds-container");
  if (!container) return;
  const search = (document.getElementById("world-search")?.value || "").toLowerCase();

  let worlds = state.worlds;
  if (search) {
    worlds = worlds.filter(w => w.name.toLowerCase().includes(search));
  }

  if (worlds.length === 0) {
    container.innerHTML = `
      <div class="empty-state">
        <svg class="w-12 h-12 mx-auto mb-3 text-mc-wood" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4"/></svg>
        <p class="text-xl font-bold text-mc-wood">${search ? 'NO WORLDS MATCH YOUR SEARCH' : 'NO WORLDS YET'}</p>
        <p class="text-sm mt-1 text-mc-wood">${search ? 'Try a different search term' : 'Add your first world to get started'}</p>
      </div>
    `;
    return;
  }

  container.innerHTML = `
    <div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 world-grid">
      ${worlds.map(w => `
        <div class="pixel-card cursor-pointer" onclick="navigate('world-details', {id: ${w.id}})" role="button" tabindex="0" onkeydown="if(event.key==='Enter'||event.key===' ') {event.preventDefault(); navigate('world-details', {id: ${w.id}})}" aria-label="View ${escHtml(w.name)} details">
          <div class="flex items-start justify-between mb-3">
            <h3 class="font-bold text-[#2a1f14] font-pixel text-xl truncate">${escHtml(w.name)}</h3>
            ${w.auto_sync_enabled ? '<span class="pixel-badge pixel-badge-green shrink-0 ml-2">Auto</span>' : ''}
          </div>
          ${w.description ? `<p class="text-base text-[#5a3a1e] mb-3 line-clamp-2 font-pixel">${escHtml(w.description)}</p>` : ''}
          <div class="flex items-center gap-4 text-lg text-[#5a3a1e] font-pixel">
            <span>${w.total_backups} backup${w.total_backups !== 1 ? 's' : ''}</span>
            <span>${w.total_size_mb ? w.total_size_mb.toFixed(1) + ' MB' : '—'}</span>
            <span>${w.last_sync ? timeAgo(w.last_sync) : 'Never'}</span>
          </div>
        </div>
      `).join('')}
    </div>
  `;
}

function filterWorlds() {
  renderWorldList();
}

// ─── Add World ────────────────────────────────────────────────────
function renderAddWorldForm() {
  return `
    <div class="max-w-lg mx-auto">
      <button class="pixel-btn bg-mc-darkwood  mb-4" onclick="navigate('dashboard')">
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/></svg>
        Back
      </button>
      <h1 class="font-press-start text-xl text-[#FAFBD3] text-shadow mb-6">ADD WORLD</h1>
      <div class="pixel-card space-y-4">
        <div>
          <label class="block text-base font-bold text-[#2a1f14] uppercase mb-1 font-pixel" for="world-name">World Name *</label>
          <input class="pixel-input" id="world-name" placeholder="e.g. My Survival World">
        </div>
        <div>
          <label class="block text-base font-bold text-[#2a1f14] uppercase mb-1 font-pixel" for="world-desc">Description</label>
          <textarea class="pixel-input" id="world-desc" rows="2" placeholder="Optional description"></textarea>
        </div>
        <div>
          <label class="block text-base font-bold text-[#2a1f14] uppercase mb-1 font-pixel" for="world-path">Local Save Path</label>
          <div class="flex gap-2">
            <input class="pixel-input" id="world-path" placeholder="e.g. C:\\Users\\You\\AppData\\Roaming\\.minecraft\\saves\\My World">
            <button class="pixel-btn bg-mc-darkwood  shrink-0" onclick="detectPath()" title="Auto-detect Minecraft saves folder" aria-label="Detect saves path">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/></svg>
            </button>
          </div>
          <p class="text-sm text-[#5a3a1e] mt-1 font-pixel">Optional: set this to enable auto-backup watching</p>
        </div>
        <button class="pixel-btn pixel-btn-primary w-full justify-center py-3 " onclick="handleCreateWorld()">Create World</button>
      </div>
    </div>
  `;
}

async function detectPath() {
  toast("Enter the full path to your Minecraft saves folder. Common locations:\nWindows: %APPDATA%\\.minecraft\\saves\nMac: ~/Library/Application Support/minecraft/saves\nLinux: ~/.minecraft/saves", "info");
}

async function handleCreateWorld() {
  const name = document.getElementById("world-name").value.trim();
  if (!name) { toast("World name is required", "error"); return; }
  const description = document.getElementById("world-desc").value.trim() || null;
  const local_path = document.getElementById("world-path").value.trim() || null;

  try {
    const res = await API.post("/api/worlds", { name, description, local_path });
    if (res.ok) {
      toast("World created!", "success");
      navigate("dashboard");
    } else {
      const err = await res.json();
      toast(err.detail || "Failed to create world", "error");
    }
  } catch (e) {
    toast("Error: " + e.message, "error");
  }
}

// ─── World Details ────────────────────────────────────────────────
function renderWorldDetails() {
  return `
    <button class="pixel-btn bg-mc-darkwood  mb-4" onclick="navigate('dashboard')">
      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/></svg>
      Back to Dashboard
    </button>
    <div id="world-details-content">
      <div class="flex justify-center py-12"><div class="spinner" style="width:32px;height:32px;border-width:4px"></div></div>
    </div>
  `;
}

async function loadWorldDetails() {
  const container = document.getElementById("world-details-content");
  if (!container) return;
  const worldId = state.params.id;
  if (!worldId) { container.innerHTML = '<div class="empty-state">World not found</div>'; return; }

  if (state._refreshInterval) {
    clearInterval(state._refreshInterval);
    state._refreshInterval = null;
  }

  try {
    const [world, backupsData] = await Promise.all([
      API.json("GET", `/api/worlds/${worldId}`),
      API.json("GET", `/api/drive/worlds/${worldId}/backups`),
    ]);
    state.currentWorld = world;
    state.backups = backupsData?.backups || [];

    // Auto-refresh when auto-sync is on — only updates backup list, not the whole page
    let refreshing = false;
    if (world.auto_sync_enabled) {
      state._refreshInterval = setInterval(() => {
        if (refreshing) return;
        refreshing = true;
        _refreshBackupsOnly(worldId).finally(() => { refreshing = false; });
      }, 5000);
    }

    const w = world;
    container.innerHTML = `
      <!-- World Info -->
      <div id="world-info-card" class="pixel-card mb-6">
        <div class="flex flex-col sm:flex-row sm:items-start justify-between gap-4 mb-4">
          <div>
            <h1 class="font-press-start text-xl text-[#2a1f14] text-shadow">${escHtml(w.name)}</h1>
            ${w.description ? `<p class="text-[#5a3a1e] mt-1 font-pixel text-xl">${escHtml(w.description)}</p>` : ''}
          </div>
          <div class="flex gap-2 flex-wrap">
            <button class="pixel-btn bg-mc-darkwood " onclick="toggleSync(${w.id})">
              ${w.auto_sync_enabled ? 'Disable Auto-Sync' : 'Enable Auto-Sync'}
            </button>
            <button class="pixel-btn pixel-btn-danger " onclick="handleDeleteWorld(${w.id})">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/></svg>
            </button>
          </div>
        </div>
        <div class="grid grid-cols-2 sm:grid-cols-4 gap-4 text-[#2a1f14] font-pixel text-xl">
          <div><span class="text-[#5a3a1e] text-base uppercase font-bold">Backups</span><p class="font-bold">${w.total_backups}</p></div>
          <div><span class="text-[#5a3a1e] text-base uppercase font-bold">Total Size</span><p class="font-bold">${w.total_size_mb ? w.total_size_mb.toFixed(1) + ' MB' : '—'}</p></div>
          <div><span class="text-[#5a3a1e] text-base uppercase font-bold">Last Backup</span><p class="font-bold">${w.last_sync ? timeAgo(w.last_sync) : 'Never'}</p></div>
          <div><span class="text-[#5a3a1e] text-base uppercase font-bold">Auto-Sync</span><p class="font-bold ${w.auto_sync_enabled ? 'text-mc-grass' : 'text-[#4D3018]'}">${w.auto_sync_enabled ? 'On' : 'Off'}</p></div>
        </div>
        ${w.local_path ? `<p class="text-lg text-[#5a3a1e] mt-3 font-pixel">Local path: ${escHtml(w.local_path)}</p>` : ''}
      </div>

      <!-- Watcher Status Bar -->
      <div id="watcher-status-bar" class="mb-6 ${w.auto_sync_enabled ? '' : 'hidden'}"></div>

      <!-- Upload Backup -->
      <div class="pixel-card mb-6">
        <h2 class="font-press-start text-[14px] text-[#2a1f14] mb-4">Upload Backup</h2>
        <div class="flex items-center gap-3 flex-wrap">
          <input type="file" id="backup-file" class="pixel-file-input flex-1" aria-label="Select backup file">
          <button class="pixel-btn pixel-btn-primary " onclick="handleUploadBackup(${w.id})">Upload</button>
        </div>
        <div id="upload-progress" class="mt-3 hidden">
          <div class="progress-bar"><div class="progress-bar-fill" id="upload-progress-fill" style="width:0%"></div></div>
          <p class="text-sm text-mc-cream mt-1 text-center font-pixel" id="upload-progress-text">0%</p>
        </div>
      </div>

      <!-- Backup History -->
      <div id="backup-history-section" class="pixel-card">
        ${renderBackupTable(w.id)}
      </div>
    `;

    // Initial status load
    if (world.auto_sync_enabled) {
      _updateWatcherStatusBar(worldId);
    }
  } catch (e) {
    container.innerHTML = `<div class="empty-state">Failed to load world: ${e.message}</div>`;
  }
}

function renderBackupTable(worldId) {
  const b = state.backups;
  return `
    <h2 class="font-press-start text-[14px] text-[#2a1f14] mb-4">Backup History (${b.length})</h2>
    ${b.length === 0
      ? '<div class="empty-state py-8"><p class="text-[#4D3018]">NO BACKUPS YET</p></div>'
      : `
    <div class="overflow-x-auto">
      <table class="pixel-table">
        <thead>
          <tr>
            <th>Filename</th>
            <th>Size</th>
            <th>Type</th>
            <th>Date</th>
            <th class="text-right">Actions</th>
          </tr>
        </thead>
        <tbody>
          ${b.map(bu => `
            <tr>
              <td class="truncate max-w-[200px]" title="${escHtml(bu.filename)}">${escHtml(bu.filename)}</td>
              <td>${bu.size_mb.toFixed(1)} MB</td>
              <td><span class="pixel-badge ${bu.backup_type === 'auto' ? 'pixel-badge-green' : 'pixel-badge-gray'}">${bu.backup_type}</span></td>
              <td class="text-[#5a3a1e]">${formatDate(bu.created_at)}</td>
              <td class="text-right">
                <button class="pixel-btn bg-mc-darkwood  py-1 px-2 inline-flex" onclick="handleDownloadBackup(${worldId}, ${bu.id})" title="Download" aria-label="Download backup">
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>
                </button>
                <button class="pixel-btn pixel-btn-danger  py-1 px-2 inline-flex" onclick="handleDeleteBackup(${worldId}, ${bu.id})" title="Delete" aria-label="Delete backup">
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/></svg>
                </button>
              </td>
            </tr>
          `).join('')}
        </tbody>
      </table>
    </div>
    `}
  `;
}

async function _updateWatcherStatusBar(worldId) {
  try {
    const status = await API.json("GET", `/api/watcher/status/${worldId}`);
    const bar = document.getElementById("watcher-status-bar");
    if (!bar) return;

    const states = {
      idle: { bg: "status-bar-idle", icon: "check", text: "Watching for changes" },
      detecting: { bg: "status-bar-detecting", icon: "clock", text: "Changes detected — backing up soon..." },
      backing_up: { bg: "status-bar-backing_up", icon: "spinner", text: status.message || "Backing up..." },
      completed: { bg: "status-bar-completed", icon: "check_circle", text: status.message || "Backup complete!" },
      error: { bg: "status-bar-error", icon: "alert", text: status.message || "Backup failed" },
    };
    const s = states[status.status] || states.idle;

    let iconHtml;
    if (s.icon === "spinner") {
      iconHtml = '<div class="spinner" style="width:16px;height:16px;border-width:3px"></div>';
    } else if (s.icon === "check_circle") {
      iconHtml = '<svg class="w-5 h-5 text-mc-grass" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>';
    } else if (s.icon === "check") {
      iconHtml = '<svg class="w-5 h-5 text-mc-grass" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg>';
    } else if (s.icon === "clock") {
      iconHtml = '<svg class="w-5 h-5 text-mc-sky" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>';
    } else {
      iconHtml = '<svg class="w-5 h-5 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>';
    }

    bar.innerHTML = `
      <div class="pixel-card-dark flex items-center gap-3 px-4 py-3 text-lg ${s.bg}">
        ${iconHtml}
        <span class="text-mc-cream font-pixel">${s.text}</span>
      </div>
    `;
  } catch (e) {
    // silent
  }
}

async function _refreshBackupsOnly(worldId) {
  try {
    const [worldData, backupsData] = await Promise.all([
      API.json("GET", `/api/worlds/${worldId}`),
      API.json("GET", `/api/drive/worlds/${worldId}/backups`),
    ]);
    state.currentWorld = worldData;
    state.backups = backupsData?.backups || [];
    const section = document.getElementById("backup-history-section");
    if (section) {
      section.innerHTML = renderBackupTable(worldId);
    }
    const card = document.getElementById("world-info-card");
    if (card) {
      const w = worldData;
      card.innerHTML = `
        <div class="flex flex-col sm:flex-row sm:items-start justify-between gap-4 mb-4">
          <div>
            <h1 class="font-press-start text-xl text-[#2a1f14] text-shadow">${escHtml(w.name)}</h1>
            ${w.description ? `<p class="text-[#5a3a1e] mt-1 font-pixel text-xl">${escHtml(w.description)}</p>` : ''}
          </div>
          <div class="flex gap-2 flex-wrap">
            <button class="pixel-btn bg-mc-darkwood " onclick="toggleSync(${w.id})">
              ${w.auto_sync_enabled ? 'Disable Auto-Sync' : 'Enable Auto-Sync'}
            </button>
            <button class="pixel-btn pixel-btn-danger " onclick="handleDeleteWorld(${w.id})">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/></svg>
            </button>
          </div>
        </div>
        <div class="grid grid-cols-2 sm:grid-cols-4 gap-4 text-[#2a1f14] font-pixel text-xl">
          <div><span class="text-[#5a3a1e] text-base uppercase font-bold">Backups</span><p class="font-bold">${w.total_backups}</p></div>
          <div><span class="text-[#5a3a1e] text-base uppercase font-bold">Total Size</span><p class="font-bold">${w.total_size_mb ? w.total_size_mb.toFixed(1) + ' MB' : '—'}</p></div>
          <div><span class="text-[#5a3a1e] text-base uppercase font-bold">Last Backup</span><p class="font-bold">${w.last_sync ? timeAgo(w.last_sync) : 'Never'}</p></div>
          <div><span class="text-[#5a3a1e] text-base uppercase font-bold">Auto-Sync</span><p class="font-bold ${w.auto_sync_enabled ? 'text-mc-grass' : 'text-[#4D3018]'}">${w.auto_sync_enabled ? 'On' : 'Off'}</p></div>
        </div>
        ${w.local_path ? `<p class="text-lg text-[#5a3a1e] mt-3 font-pixel">Local path: ${escHtml(w.local_path)}</p>` : ''}
      `;
    }
    _updateWatcherStatusBar(worldId);
  } catch (e) {
    // silent — don't disrupt the user
  }
}

async function toggleSync(worldId) {
  const w = state.currentWorld;
  if (!w) return;
  try {
    const res = await API.put(`/api/worlds/${worldId}`, { auto_sync_enabled: !w.auto_sync_enabled });
    if (res.ok) {
      w.auto_sync_enabled = !w.auto_sync_enabled;
      loadWorldDetails();
      toast(w.auto_sync_enabled ? "Auto-sync enabled" : "Auto-sync disabled", "success");
      // Tell the watcher to pick up this world immediately
      if (w.auto_sync_enabled) {
        API.post("/api/watcher/resync").catch(() => {});
      }
    }
  } catch (e) {
    toast("Failed to update sync setting", "error");
  }
}

async function handleDeleteWorld(worldId) {
  const confirmed = await confirmDialog("Delete this world? Backups in Google Drive will NOT be deleted.", "Delete", true);
  if (!confirmed) return;
  try {
    const res = await API.del(`/api/worlds/${worldId}`);
    if (res.ok) {
      toast("World deleted", "success");
      navigate("dashboard");
    } else {
      toast("Failed to delete world", "error");
    }
  } catch (e) {
    toast("Error: " + e.message, "error");
  }
}

async function handleUploadBackup(worldId) {
  const input = document.getElementById("backup-file");
  const file = input?.files?.[0];
  if (!file) { toast("Please select a file", "error"); return; }

  const progressDiv = document.getElementById("upload-progress");
  const progressFill = document.getElementById("upload-progress-fill");
  const progressText = document.getElementById("upload-progress-text");
  progressDiv.classList.remove("hidden");

  const formData = new FormData();
  formData.append("file", file);

  try {
    await new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();
      xhr.upload.onprogress = (e) => {
        if (e.lengthComputable) {
          const pct = Math.round((e.loaded / e.total) * 100);
          progressFill.style.width = pct + "%";
          progressText.textContent = pct + "%";
        }
      };
      xhr.onload = () => {
        if (xhr.status === 200) resolve();
        else reject(new Error(xhr.responseText || "Upload failed"));
      };
      xhr.onerror = () => reject(new Error("Network error"));
      xhr.open("POST", `/api/drive/worlds/${worldId}/backup`);
      xhr.setRequestHeader("Authorization", `Bearer ${state.token}`);
      xhr.send(formData);
    });

    progressFill.style.width = "100%";
    progressText.textContent = "Complete!";
    toast("Backup uploaded successfully", "success");
    input.value = "";
    setTimeout(() => progressDiv.classList.add("hidden"), 2000);
    loadWorldDetails();

  } catch (e) {
    progressDiv.classList.add("hidden");
    toast("Upload failed: " + e.message, "error");
  }
}

async function handleDownloadBackup(worldId, backupId) {
  try {
    const data = await API.json("GET", `/api/drive/worlds/${worldId}/backups/${backupId}/download-link`);
    if (data.download_link) {
      window.open(data.download_link, "_blank");
    } else {
      toast("No download link available", "error");
    }
  } catch (e) {
    toast("Failed to get download link", "error");
  }
}

async function handleDeleteBackup(worldId, backupId) {
  const confirmed = await confirmDialog("Delete this backup from Google Drive?", "Delete", true);
  if (!confirmed) return;
  try {
    const res = await API.del(`/api/drive/worlds/${worldId}/backups/${backupId}`);
    if (res.ok) {
      toast("Backup deleted", "success");
      loadWorldDetails();
    } else {
      toast("Failed to delete backup", "error");
    }
  } catch (e) {
    toast("Error: " + e.message, "error");
  }
}

// ─── Settings ─────────────────────────────────────────────────────
function renderSettings() {
  return `
    <h1 class="font-press-start text-xl text-[#FAFBD3] text-shadow mb-6">SETTINGS</h1>
    <div class="space-y-6">
      <!-- Account -->
      <div class="pixel-card" id="settings-account">
        <div class="flex items-center gap-4 mb-2">
          <div id="settings-avatar">...</div>
          <div id="settings-user-info">...</div>
        </div>
      </div>
      <!-- Preferences -->
      <div class="pixel-card" id="settings-preferences">
        <h2 class="font-press-start text-[14px] text-[#2a1f14] mb-4">Preferences</h2>
        <p class="text-[#4D3018] font-pixel">Loading...</p>
      </div>
      <!-- Logout -->
      <div class="pixel-card border-red-900/50">
        <button class="pixel-btn pixel-btn-danger " onclick="handleLogout()">Sign Out</button>
      </div>
      <!-- Shut Down -->
      <div class="pixel-card border-red-900/50">
        <button class="pixel-btn pixel-btn-danger " id="shutdown-btn">Shut Down App</button>
        <p class="text-sm text-[#5a3a1e] mt-2 font-pixel">Close the desktop app completely</p>
      </div>
    </div>
  `;
}

async function loadSettingsData() {
  // Load all settings data
  const u = state.user;
  if (u) {
    const initial = escHtml((u.display_name || '?')[0]);
    const avatar = u.profile_picture
      ? `<img src="${escHtml(u.profile_picture)}" class="w-12 h-12 border-3 border-black" alt="${escHtml(u.display_name || '')}">`
      : `<div class="w-12 h-12 bg-mc-grass border-3 border-black flex items-center justify-center text-xl font-bold text-[#FAFBD3]" aria-hidden="true">${initial}</div>`;
    document.getElementById("settings-avatar").innerHTML = avatar;
    document.getElementById("settings-user-info").innerHTML = `
      <p class="font-bold text-[#2a1f14] font-pixel text-xl">${escHtml(u.display_name || '')}</p>
      <p class="text-[#5a3a1e] font-pixel">${u.email || ''}</p>
    `;
  }

  try {
    const userData = await API.json("GET", "/api/auth/me");
    state.user = userData;
    // Update avatar/info with server data if available
  } catch (e) { /* noop */ }

  // Preferences
  try {
    const u = state.user || {};
    const checked = u.auto_cleanup_enabled !== false ? "checked" : "";
    const maxVal = u.max_backups_per_world || 10;
    document.getElementById("settings-preferences").innerHTML = `
      <h2 class="font-press-start text-[14px] text-[#2a1f14] mb-4">Preferences</h2>
      <div class="space-y-4">
        <div class="flex items-center justify-between">
          <div>
            <p class="font-bold text-[#2a1f14] font-pixel text-lg">Auto-cleanup old backups</p>
            <p class="text-[#5a3a1e] text-lg font-pixel">Keep only the N most recent backups per world</p>
          </div>
          <label class="pixel-toggle" aria-label="Toggle auto-cleanup">
            <input type="checkbox" id="pref-cleanup" ${checked} onchange="updatePreferences()">
            <div class="pixel-toggle-slider"></div>
          </label>
        </div>
        <div>
          <label class="block font-bold text-[#2a1f14] text-lg font-pixel mb-1" for="pref-max-backups">Max backups per world</label>
          <input class="pixel-input" id="pref-max-backups" type="number" value="${maxVal}" min="1" max="50" style="max-width:120px" onchange="updatePreferences()">
        </div>
      </div>
    `;
  } catch (e) { /* noop */ }

  // Wire up shutdown button
  const btn = document.getElementById("shutdown-btn");
  if (btn) btn.onclick = handleShutdown;
}

async function updatePreferences() {
  const cleanup = document.getElementById("pref-cleanup")?.checked;
  const maxBackups = parseInt(document.getElementById("pref-max-backups")?.value || "10");
  try {
    const res = await API.patch("/api/auth/preferences", {
      auto_cleanup_enabled: cleanup,
      max_backups_per_world: maxBackups,
    });
    if (res.ok) toast("Preferences saved", "success");
  } catch (e) {
    toast("Failed to save preferences", "error");
  }
}

async function handleLogout() {
  try { await API.post("/api/auth/logout"); } catch (e) { /* ignore */ }
  logout();
}

async function handleShutdown() {
  const confirmed = await confirmDialog("Shut down the desktop app? You'll need to restart it manually.", "Shut Down", true);
  if (!confirmed) return;
  // Fire request without waiting for response (server may exit before responding)
  fetch("/api/shutdown-now", { method: "POST", keepalive: true }).catch(() => {});
  // Show shut down confirmation immediately
  document.getElementById("app").innerHTML = `
    <div class="min-h-screen minecraft-bg-grid flex items-center justify-center px-4">
      <div class="pixel-card max-w-sm w-full text-center p-8">
        <h1 class="text-shadow font-press-start text-lg text-[#FAFBD3] mb-4">APP SHUT DOWN</h1>
        <p class="font-pixel text-[#5a3a1e] text-xl">The desktop app has shut down. You may close this tab.</p>
      </div>
    </div>
  `;
}

// ─── Utility ──────────────────────────────────────────────────────
function escHtml(str) {
  if (!str) return "";
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

function timeAgo(dateStr) {
  const now = new Date();
  const d = new Date(dateStr);
  const diff = Math.floor((now - d) / 1000);
  if (diff < 60) return "just now";
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  return `${Math.floor(diff / 86400)}d ago`;
}

function formatDate(dateStr) {
  const d = new Date(dateStr);
  return d.toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric", hour: "2-digit", minute: "2-digit" });
}

// ─── Init ─────────────────────────────────────────────────────────
async function init() {
  // ─── App lifecycle (register before auth check) ─────────
  // Heartbeat: lets the server know the tab is still open.
  // Also cancels any pending shutdown (e.g. OAuth redirect return).
  // Immediate heartbeat on page load to cancel any pending shutdown from refresh.
  try { await fetch("/api/heartbeat", { method: "POST" }); }
  catch (_) { /* server may be gone */ }
  setInterval(async () => {
    try { await fetch("/api/heartbeat", { method: "POST" }); }
    catch (_) { /* server may be gone */ }
  }, 3000);

  // Tab close → signal shutdown with 120s cancellable timer.
  // OAuth redirect also fires this, but the new page load's heartbeat
  // cancels the countdown before it expires.
  window.addEventListener("beforeunload", () => {
    navigator.sendBeacon("/api/shutdown", "{}");
  });

  // Check URL params for token
  const params = new URLSearchParams(window.location.search);
  const urlToken = params.get("token");
  const urlRefresh = params.get("refresh_token");

  if (urlToken) {
    state.token = urlToken;
    state.refreshToken = urlRefresh || localStorage.getItem("refreshToken");
    localStorage.setItem("token", urlToken);
    if (state.refreshToken) localStorage.setItem("refreshToken", state.refreshToken);
    // Clean URL
    window.history.replaceState({}, "", "/");
  } else {
    state.token = localStorage.getItem("token");
    state.refreshToken = localStorage.getItem("refreshToken");
  }

  if (!state.token) {
    navigate("login");
    return;
  }

  // Verify token by fetching user info
  try {
    const user = await API.json("GET", "/api/auth/me");
    state.user = user;
    navigate("dashboard");
  } catch (e) {
    // Token invalid or expired
    localStorage.removeItem("token");
    navigate("login");
  }
}

document.addEventListener("DOMContentLoaded", init);
