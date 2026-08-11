(() => {
  'use strict';

  const API = '/api';
  let currentJobId = null;
  let pollTimer = null;
  let resultsData = [];

  const $ = (sel) => document.querySelector(sel);
  const $$ = (sel) => document.querySelectorAll(sel);

  // --- Settings (localStorage) ---
  const SETTINGS_KEY = 'scraper_settings';

  function loadSettings() {
    const defaults = {
      delay: 1.0,
      timeout: 15,
      retries: 3,
      user_agent: '',
      check_robots: true,
    };
    try {
      return { ...defaults, ...JSON.parse(localStorage.getItem(SETTINGS_KEY) || '{}') };
    } catch {
      return defaults;
    }
  }

  function saveSettings(settings) {
    localStorage.setItem(SETTINGS_KEY, JSON.stringify(settings));
  }

  function applySettingsToForm() {
    const s = loadSettings();
    $('#setting-delay').value = s.delay;
    $('#setting-timeout').value = s.timeout;
    $('#setting-retries').value = s.retries;
    $('#setting-user-agent').value = s.user_agent;
    $('#setting-robots').checked = s.check_robots;
  }

  // --- Toast ---
  function toast(message, type = 'info') {
    const el = document.createElement('div');
    el.className = `toast toast-${type}`;
    el.textContent = message;
    $('#toast-container').appendChild(el);
    setTimeout(() => el.remove(), 4000);
  }

  // --- Navigation ---
  $$('.nav-item').forEach((btn) => {
    btn.addEventListener('click', () => {
      $$('.nav-item').forEach((b) => b.classList.remove('active'));
      btn.classList.add('active');
      const view = btn.dataset.view;
      $$('.view').forEach((v) => v.classList.remove('active'));
      $(`#view-${view}`).classList.add('active');
      if (view === 'history') loadHistory();
    });
  });

  // --- Mode toggles ---
  function updateModeUI() {
    const mode = $('#mode').value;
    const urlGroup = $('#url-group');
    const selectorsGroup = $('#selectors-group');
    const pagesGroup = $('#pages-group');
    const domainGroup = $('#domain-group');

    urlGroup.classList.toggle('hidden', mode === 'quotes');
    selectorsGroup.classList.toggle('hidden', mode !== 'selectors');
    pagesGroup.classList.toggle('hidden', mode !== 'quotes');
    domainGroup.classList.toggle('hidden', mode !== 'links');

    if (mode === 'quotes') {
      $('#url').removeAttribute('required');
    } else {
      $('#url').setAttribute('required', '');
    }
  }

  $('#mode').addEventListener('change', updateModeUI);
  updateModeUI();

  // --- Health check ---
  async function checkHealth() {
    const badge = $('#health-badge');
    try {
      const res = await fetch(`${API}/health`);
      const data = await res.json();
      if (data.status === 'healthy') {
        badge.textContent = 'Online';
        badge.className = 'badge badge-healthy';
      } else {
        badge.textContent = 'Degraded';
        badge.className = 'badge badge-pending';
      }
    } catch {
      badge.textContent = 'Offline';
      badge.className = 'badge badge-error';
    }
  }

  // --- Scrape form ---
  $('#scrape-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const btn = $('#submit-btn');
    btn.disabled = true;
    $('.btn-text').classList.add('hidden');
    $('.btn-loader').classList.remove('hidden');

    const settings = loadSettings();
    const mode = $('#mode').value;
    const body = {
      mode,
      delay: parseFloat(settings.delay),
      timeout: parseInt(settings.timeout, 10),
      retries: parseInt(settings.retries, 10),
      check_robots: settings.check_robots,
    };

    if (settings.user_agent) body.user_agent = settings.user_agent;

    if (mode !== 'quotes') {
      body.url = $('#url').value;
    }
    if (mode === 'quotes') {
      const pages = $('#max-pages').value;
      if (pages) body.max_pages = parseInt(pages, 10);
    }
    if (mode === 'links') {
      body.same_domain = $('#same-domain').checked;
    }
    if (mode === 'selectors') {
      body.selectors = $('#selectors').value.split('\n').map((s) => s.trim()).filter(Boolean);
    }

    try {
      const res = await fetch(`${API}/jobs`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Failed to create job');
      }
      const data = await res.json();
      currentJobId = data.job_id;
      toast('Job queued successfully', 'success');
      startPolling(currentJobId);
    } catch (err) {
      toast(err.message, 'error');
    } finally {
      btn.disabled = false;
      $('.btn-text').classList.remove('hidden');
      $('.btn-loader').classList.add('hidden');
    }
  });

  // --- Job polling ---
  function startPolling(jobId) {
    if (pollTimer) clearInterval(pollTimer);
    pollLiveStatus(jobId);
    pollTimer = setInterval(() => pollLiveStatus(jobId), 1500);
  }

  async function pollLiveStatus(jobId) {
    try {
      const res = await fetch(`${API}/jobs/${jobId}`);
      const job = await res.json();
      renderLiveStatus(job);

      if (job.status === 'completed') {
        clearInterval(pollTimer);
        pollTimer = null;
        await loadResults(jobId);
        toast(`Scrape complete — ${job.total_items} items`, 'success');
      } else if (job.status === 'failed') {
        clearInterval(pollTimer);
        pollTimer = null;
        toast(job.error || 'Job failed', 'error');
      }
    } catch (err) {
      console.error('Poll error:', err);
    }
  }

  function renderLiveStatus(job) {
    const el = $('#live-status');
    el.classList.remove('empty');

    const statusClass = {
      pending: 'status-running',
      running: 'status-running',
      completed: 'status-completed',
      failed: 'status-failed',
    }[job.status] || '';

    const progress = job.status === 'completed' ? 100 : Math.min(job.progress * 10, 90);

    el.innerHTML = `
      <div class="status-active">
        <div class="status-row">
          <span class="status-label">Job ID</span>
          <span class="status-value job-id">${job.id.slice(0, 8)}...</span>
        </div>
        <div class="status-row">
          <span class="status-label">Mode</span>
          <span class="status-value">${job.mode}</span>
        </div>
        <div class="status-row">
          <span class="status-label">Status</span>
          <span class="status-value ${statusClass}">${job.status.toUpperCase()}</span>
        </div>
        <div class="status-row">
          <span class="status-label">Items</span>
          <span class="status-value">${job.total_items}</span>
        </div>
        ${job.error ? `<div class="status-row"><span class="status-label">Error</span><span class="status-value status-failed">${job.error}</span></div>` : ''}
        <div class="progress-bar"><div class="progress-fill" style="width:${progress}%"></div></div>
      </div>
    `;
  }

  // --- Results ---
  async function loadResults(jobId) {
    const res = await fetch(`${API}/jobs/${jobId}/results`);
    const data = await res.json();
    resultsData = normalizeResults(data.data);
    renderResultsTable(resultsData);
    $('#results-section').classList.remove('hidden');
    currentJobId = jobId;
  }

  function normalizeResults(data) {
    if (Array.isArray(data)) return data;
    if (typeof data === 'object' && data !== null) return [data];
    return [{ value: data }];
  }

  function renderResultsTable(rows) {
    const thead = $('#results-table thead');
    const tbody = $('#results-table tbody');

    if (!rows.length) {
      thead.innerHTML = '';
      tbody.innerHTML = '<tr><td>No results</td></tr>';
      $('#results-count').textContent = '0 items';
      return;
    }

    const keys = [];
    rows.forEach((row) => {
      Object.keys(row).forEach((k) => {
        if (!keys.includes(k)) keys.push(k);
      });
    });

    thead.innerHTML = `<tr>${keys.map((k) => `<th>${k}</th>`).join('')}</tr>`;
    tbody.innerHTML = rows.map((row) =>
      `<tr>${keys.map((k) => `<td title="${escapeHtml(String(flatten(row[k])))}">${escapeHtml(String(flatten(row[k])))}</td>`).join('')}</tr>`
    ).join('');

    $('#results-count').textContent = `${rows.length} item${rows.length !== 1 ? 's' : ''}`;
  }

  function flatten(val) {
    if (Array.isArray(val)) return val.join(', ');
    if (typeof val === 'object' && val !== null) return JSON.stringify(val);
    return val ?? '';
  }

  function escapeHtml(str) {
    return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }

  $('#results-search').addEventListener('input', (e) => {
    const q = e.target.value.toLowerCase();
    if (!q) {
      renderResultsTable(resultsData);
      return;
    }
    const filtered = resultsData.filter((row) =>
      JSON.stringify(row).toLowerCase().includes(q)
    );
    renderResultsTable(filtered);
  });

  $$('[data-export]').forEach((btn) => {
    btn.addEventListener('click', () => {
      if (!currentJobId) return toast('No results to export', 'error');
      window.open(`${API}/jobs/${currentJobId}/export?format=${btn.dataset.export}`, '_blank');
    });
  });

  // --- History ---
  async function loadHistory() {
    try {
      const res = await fetch(`${API}/jobs?limit=50`);
      const data = await res.json();
      const tbody = $('#history-table tbody');

      if (!data.jobs.length) {
        tbody.innerHTML = '<tr><td colspan="7" style="text-align:center;color:var(--text-muted)">No jobs yet</td></tr>';
        return;
      }

      tbody.innerHTML = data.jobs.map((job) => `
        <tr>
          <td class="job-id">${job.id.slice(0, 8)}...</td>
          <td>${job.mode}</td>
          <td title="${escapeHtml(job.url || '—')}">${truncate(job.url || '—', 40)}</td>
          <td><span class="badge badge-${job.status === 'completed' ? 'healthy' : job.status === 'failed' ? 'error' : 'pending'}">${job.status}</span></td>
          <td>${job.total_items}</td>
          <td>${formatDate(job.created_at)}</td>
          <td>
            ${job.status === 'completed' ? `<button class="btn btn-ghost btn-sm" onclick="window.__viewJob('${job.id}')">View</button>` : '—'}
          </td>
        </tr>
      `).join('');
    } catch {
      toast('Failed to load history', 'error');
    }
  }

  function truncate(str, len) {
    return str.length > len ? str.slice(0, len) + '…' : str;
  }

  function formatDate(iso) {
    return new Date(iso).toLocaleString();
  }

  window.__viewJob = async (jobId) => {
    $$('.nav-item').forEach((b) => b.classList.remove('active'));
    $$('.nav-item')[0].classList.add('active');
    $$('.view').forEach((v) => v.classList.remove('active'));
    $('#view-scrape').classList.add('active');
    currentJobId = jobId;
    const res = await fetch(`${API}/jobs/${jobId}`);
    const job = await res.json();
    renderLiveStatus(job);
    if (job.status === 'completed') await loadResults(jobId);
  };

  // --- Settings form ---
  $('#settings-form').addEventListener('submit', (e) => {
    e.preventDefault();
    saveSettings({
      delay: parseFloat($('#setting-delay').value),
      timeout: parseInt($('#setting-timeout').value, 10),
      retries: parseInt($('#setting-retries').value, 10),
      user_agent: $('#setting-user-agent').value,
      check_robots: $('#setting-robots').checked,
    });
    toast('Settings saved', 'success');
  });

  // --- Init ---
  async function init() {
    applySettingsToForm();
    checkHealth();
    setInterval(checkHealth, 30000);

    try {
      const res = await fetch(`${API}/settings`);
      const serverSettings = await res.json();
      if (!$('#setting-user-agent').value) {
        $('#setting-user-agent').value = serverSettings.default_user_agent;
      }
    } catch { /* ignore */ }
  }

  init();
})();
