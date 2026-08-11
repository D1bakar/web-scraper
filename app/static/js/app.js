(() => {
  'use strict';

  const API = '/api';
  let currentJobId = null;
  let currentJobMode = 'quotes';
  let pollTimer = null;
  let resultsData = [];

  const $ = (sel) => document.querySelector(sel);
  const $$ = (sel) => document.querySelectorAll(sel);

  const MODE_CONFIG = {
    quotes: {
      description:
        'Extracts quote text, author names, and tags from quotes.toscrape.com. No URL needed — great first demo.',
      example: null,
      placeholder: '',
      recommended: true,
      summary: (n) => `Showing ${n} quote${n !== 1 ? 's' : ''} with text, author, and tags`,
      columns: { text: 'Quote', author: 'Author', tags: 'Tags', source_url: 'Source Page' },
      emptyHint: 'No quotes found. The demo site may be unreachable — check your connection.',
    },
    meta: {
      description:
        'Extracts page title, meta description, and H1–H3 headings from a single URL. One summary card, not a list of links.',
      example: 'https://quotes.toscrape.com',
      placeholder: 'https://quotes.toscrape.com',
      summary: () => 'Showing page metadata — title, description, and headings',
      emptyHint: 'No metadata could be extracted. Check the URL and try again.',
    },
    links: {
      description:
        'Extracts hyperlinks (URLs + link text) found on a page. Results are a list of links — not article text, prices, or full page content.',
      example: 'https://quotes.toscrape.com',
      placeholder: 'https://quotes.toscrape.com',
      summary: (n) =>
        `Showing ${n} link${n !== 1 ? 's' : ''} extracted from the page (URL + link text only)`,
      columns: { url: 'Link URL', text: 'Link Text' },
      emptyHint:
        'No links found. Try unchecking "Same domain only" or use a page with more navigation links.',
      linksMode: true,
    },
    tables: {
      description:
        'Extracts structured data from HTML tables — rows and columns as spreadsheet-style records.',
      example: 'https://en.wikipedia.org/wiki/List_of_countries_by_population_(United_Nations)',
      placeholder: 'https://example.com/page-with-tables',
      summary: (n) => `Showing ${n} table row${n !== 1 ? 's' : ''} extracted from HTML tables`,
      columns: { table: 'Table #' },
      emptyHint: 'No HTML tables found on this page. Try a URL that contains <table> elements.',
    },
    selectors: {
      description:
        'Extracts content matching your CSS selectors — text and HTML snippets for each match.',
      example: 'https://quotes.toscrape.com',
      placeholder: 'https://quotes.toscrape.com',
      exampleSelectors: 'div.quote span.text\nsmall.author',
      summary: (n) => `Showing ${n} element${n !== 1 ? 's' : ''} matched by your CSS selectors`,
      columns: { selector: 'Selector', match: 'Match #', text: 'Text', html: 'HTML snippet' },
      emptyHint: 'No elements matched your selectors. Check spelling and try simpler selectors like h1 or .class.',
    },
  };

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

  function formatJobError(error) {
    if (!error) return 'Job failed';
    if (error.includes('ROBOTS_BLOCKED') || error.toLowerCase().includes('robots.txt')) {
      return 'Blocked by robots.txt. Try Quotes demo or turn off "Check robots.txt" in Settings.';
    }
    if (error.includes('ACCESS_DENIED') || error.includes('403')) {
      return 'Site blocked access (403). Try Quotes demo or https://quotes.toscrape.com';
    }
    return error.replace(/^(ROBOTS_BLOCKED|ACCESS_DENIED):\s*/, '');
  }

  function showRobotsHint() {
    const hint = $('#robots-hint');
    if (hint) hint.classList.remove('hidden');
  }

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
    const cfg = MODE_CONFIG[mode];
    const urlGroup = $('#url-group');
    const selectorsGroup = $('#selectors-group');
    const pagesGroup = $('#pages-group');
    const domainGroup = $('#domain-group');
    const tryExampleBtn = $('#try-example-btn');
    const modeDesc = $('#mode-description');

    urlGroup.classList.toggle('hidden', mode === 'quotes');
    selectorsGroup.classList.toggle('hidden', mode !== 'selectors');
    pagesGroup.classList.toggle('hidden', mode !== 'quotes');
    domainGroup.classList.toggle('hidden', mode !== 'links');

    if (mode === 'quotes') {
      $('#url').removeAttribute('required');
    } else {
      $('#url').setAttribute('required', '');
      $('#url').placeholder = cfg.placeholder || 'https://example.com';
    }

    if (cfg.example) {
      tryExampleBtn.classList.remove('hidden');
    } else {
      tryExampleBtn.classList.add('hidden');
    }

    let descHtml = cfg.description;
    if (cfg.recommended) {
      descHtml += ' <span class="mode-badge">Recommended for first-time users</span>';
    }
    modeDesc.innerHTML = descHtml;
  }

  $('#mode').addEventListener('change', updateModeUI);
  updateModeUI();

  $('#try-example-btn').addEventListener('click', () => {
    const mode = $('#mode').value;
    const cfg = MODE_CONFIG[mode];
    if (cfg.example) {
      $('#url').value = cfg.example;
      toast('Example URL filled in', 'info');
    }
    if (cfg.exampleSelectors) {
      $('#selectors').value = cfg.exampleSelectors;
    }
  });

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
      currentJobMode = mode;
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
        currentJobMode = job.mode;
        await loadResults(jobId);
        toast(`Scrape complete — ${job.total_items} items`, 'success');
      } else if (job.status === 'failed') {
        clearInterval(pollTimer);
        pollTimer = null;
        const msg = formatJobError(job.error);
        toast(msg, 'error');
        if (job.error && job.error.includes('ROBOTS_BLOCKED')) showRobotsHint();
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
        ${job.error ? `<div class="status-row"><span class="status-label">Error</span><span class="status-value status-failed">${escapeHtml(formatJobError(job.error))}</span></div>` : ''}
        ${job.error && job.error.includes('ROBOTS_BLOCKED') ? `<div class="robots-help">Tip: Open <strong>Settings</strong> and uncheck "Check robots.txt", or use <strong>Quotes Demo</strong> mode.</div>` : ''}
        <div class="progress-bar"><div class="progress-fill" style="width:${progress}%"></div></div>
      </div>
    `;
  }

  // --- Results ---
  async function loadResults(jobId) {
    const res = await fetch(`${API}/jobs/${jobId}/results`);
    const data = await res.json();
    resultsData = normalizeResults(data.data, currentJobMode);
    renderResults(resultsData, currentJobMode);
    $('#results-section').classList.remove('hidden');
    currentJobId = jobId;
  }

  function normalizeResults(data, mode) {
    if (mode === 'meta' && typeof data === 'object' && data !== null && !Array.isArray(data)) {
      return [data];
    }
    if (Array.isArray(data)) {
      return flattenForDisplay(mode, data);
    }
    if (typeof data === 'object' && data !== null) return [data];
    return [{ value: data }];
  }

  function flattenForDisplay(mode, data) {
    if (mode === 'tables') {
      const flat = [];
      data.forEach((t) => {
        (t.rows || []).forEach((row) => {
          flat.push({ table: (t.table_index ?? 0) + 1, ...row });
        });
      });
      return flat;
    }
    if (mode === 'selectors') {
      const flat = [];
      data.forEach((group) => {
        (group.items || []).forEach((item, i) => {
          flat.push({
            selector: group.selector,
            match: i + 1,
            text: item.text,
            html: item.html,
          });
        });
      });
      return flat;
    }
    return data;
  }

  function getColumnLabel(mode, key) {
    const cfg = MODE_CONFIG[mode];
    if (cfg && cfg.columns && cfg.columns[key]) return cfg.columns[key];
    return key.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
  }

  function renderResultsSummary(mode, count) {
    const el = $('#results-summary');
    const cfg = MODE_CONFIG[mode] || {};
    el.textContent = cfg.summary ? cfg.summary(count) : `Showing ${count} result${count !== 1 ? 's' : ''}`;
    el.classList.remove('hidden');
    el.classList.toggle('links-mode', !!cfg.linksMode);
  }

  function renderEmptyState(mode) {
    const cfg = MODE_CONFIG[mode] || {};
    const emptyEl = $('#results-empty');
    const tableWrap = $('#results-table-wrap');
    const metaEl = $('#results-meta');

    emptyEl.classList.remove('hidden');
    tableWrap.classList.add('hidden');
    metaEl.classList.add('hidden');
    emptyEl.innerHTML = `
      <div class="results-empty-icon">📭</div>
      <p><strong>No results</strong></p>
      <p>${escapeHtml(cfg.emptyHint || 'Try a different URL or scrape mode.')}</p>
    `;
    $('#results-count').textContent = '0 items';
    $('#results-table thead').innerHTML = '';
    $('#results-table tbody').innerHTML = '';
  }

  function renderMetaCard(meta) {
    const metaEl = $('#results-meta');
    const tableWrap = $('#results-table-wrap');
    const emptyEl = $('#results-empty');

    emptyEl.classList.add('hidden');
    tableWrap.classList.add('hidden');
    metaEl.classList.remove('hidden');

    const headings = Array.isArray(meta.headings) ? meta.headings : [];
    const headingsHtml = headings.length
      ? `<ul class="meta-headings-list">${headings.map((h) => `<li>${escapeHtml(h)}</li>`).join('')}</ul>`
      : '<span class="meta-card-value">No headings found</span>';

    metaEl.innerHTML = `
      <div class="meta-card-item">
        <div class="meta-card-label">Title</div>
        <div class="meta-card-value">${escapeHtml(meta.title || '—')}</div>
      </div>
      <div class="meta-card-item">
        <div class="meta-card-label">Page URL</div>
        <div class="meta-card-value"><a href="${escapeHtml(meta.url || '')}" target="_blank" rel="noopener">${escapeHtml(meta.url || '—')}</a></div>
      </div>
      <div class="meta-card-item">
        <div class="meta-card-label">Description</div>
        <div class="meta-card-value">${escapeHtml(meta.description || 'No meta description found')}</div>
      </div>
      <div class="meta-card-item">
        <div class="meta-card-label">Headings (H1–H3)</div>
        ${headingsHtml}
      </div>
    `;

    $('#results-count').textContent = `${headings.length} heading${headings.length !== 1 ? 's' : ''}`;
  }

  function renderResults(rows, mode) {
    renderResultsSummary(mode, rows.length);

    if (!rows.length) {
      renderEmptyState(mode);
      return;
    }

    $('#results-empty').classList.add('hidden');

    if (mode === 'meta') {
      renderMetaCard(rows[0]);
      return;
    }

    $('#results-meta').classList.add('hidden');
    $('#results-table-wrap').classList.remove('hidden');
    renderResultsTable(rows, mode);
  }

  function renderResultsTable(rows, mode) {
    const thead = $('#results-table thead');
    const tbody = $('#results-table tbody');

    const keys = [];
    rows.forEach((row) => {
      Object.keys(row).forEach((k) => {
        if (!keys.includes(k)) keys.push(k);
      });
    });

    thead.innerHTML = `<tr>${keys.map((k) => `<th>${escapeHtml(getColumnLabel(mode, k))}</th>`).join('')}</tr>`;
    tbody.innerHTML = rows
      .map(
        (row) =>
          `<tr>${keys
            .map((k) => {
              const val = flatten(row[k]);
              if (mode === 'links' && k === 'url' && val) {
                return `<td class="link-url" title="${escapeHtml(val)}"><a href="${escapeHtml(val)}" target="_blank" rel="noopener">${escapeHtml(val)}</a></td>`;
              }
              return `<td title="${escapeHtml(String(val))}">${escapeHtml(String(val))}</td>`;
            })
            .join('')}</tr>`
      )
      .join('');

    $('#results-count').textContent = `${rows.length} item${rows.length !== 1 ? 's' : ''}`;
  }

  function flatten(val) {
    if (Array.isArray(val)) return val.join(', ');
    if (typeof val === 'object' && val !== null) return JSON.stringify(val);
    return val ?? '';
  }

  function escapeHtml(str) {
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  $('#results-search').addEventListener('input', (e) => {
    const q = e.target.value.toLowerCase();
    if (!q) {
      renderResults(resultsData, currentJobMode);
      return;
    }
    const filtered = resultsData.filter((row) => JSON.stringify(row).toLowerCase().includes(q));
    if (currentJobMode === 'meta') {
      renderResults(filtered.length ? filtered : resultsData, currentJobMode);
      return;
    }
    renderResultsSummary(currentJobMode, filtered.length);
    $('#results-empty').classList.add('hidden');
    $('#results-meta').classList.add('hidden');
    $('#results-table-wrap').classList.remove('hidden');
    renderResultsTable(filtered, currentJobMode);
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
        tbody.innerHTML =
          '<tr><td colspan="7" style="text-align:center;color:var(--text-muted)">No jobs yet</td></tr>';
        return;
      }

      tbody.innerHTML = data.jobs
        .map(
          (job) => `
        <tr>
          <td class="job-id">${job.id.slice(0, 8)}...</td>
          <td>${job.mode}</td>
          <td title="${escapeHtml(job.url || '—')}">${truncate(job.url || '—', 40)}</td>
          <td><span class="badge badge-${job.status === 'completed' ? 'healthy' : job.status === 'failed' ? 'error' : 'pending'}">${job.status}</span></td>
          <td>${job.total_items}</td>
          <td>${formatDate(job.created_at)}</td>
          <td>
            ${job.status === 'completed' ? `<button class="btn btn-ghost btn-sm" onclick="window.__viewJob('${job.id}')">View</button>` : job.status === 'failed' ? `<button class="btn btn-ghost btn-sm" onclick="window.__viewJob('${job.id}')" title="${escapeHtml(formatJobError(job.error || ''))}">Details</button>` : '—'}
          </td>
        </tr>
      `
        )
        .join('');
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
    currentJobMode = job.mode;
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
    } catch {
      /* ignore */
    }
  }

  init();
})();
