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
    price_compare: {
      description:
        'Compare product prices across multiple websites. Paste one product page URL per line, set a CSS selector for the price, and get a sorted comparison table.',
      recommended: true,
      priceCompare: true,
      exampleUrls: [
        'https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html',
        'https://books.toscrape.com/catalogue/tipping-the-velvet_999/index.html',
        'https://books.toscrape.com/catalogue/soumission_998/index.html',
        'https://books.toscrape.com/catalogue/sharp-objects_997/index.html',
        'https://books.toscrape.com/catalogue/sapiens-our-evolution-from-robots-to-gods_314/index.html',
      ].join('\n'),
      examplePriceSelector: '.price_color',
      exampleProductLabel: 'Demo book prices',
      summary: (n) => `Compared prices across ${n} website${n !== 1 ? 's' : ''} — sorted lowest first when numeric`,
      columns: {
        site_name: 'Website',
        price_text: 'Price',
        price_numeric: 'Numeric',
        status: 'Status',
        url: 'Link',
        error: 'Error',
      },
      emptyHint: 'No results returned. Check your URLs and CSS selector, then try again.',
      submitLabel: 'Compare Prices',
    },
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
    sitemap: {
      description:
        'Crawls sitemap.xml (and sitemap indexes) to extract all page URLs. Great for site audits and bulk discovery.',
      example: 'https://quotes.toscrape.com',
      placeholder: 'https://example.com',
      sitemapMode: true,
      summary: (n) => `Found ${n} URL${n !== 1 ? 's' : ''} in sitemap`,
      columns: { url: 'URL', source_sitemap: 'Source Sitemap' },
      emptyHint: 'No URLs found. Ensure the site has /sitemap.xml or provide a direct sitemap URL.',
      submitLabel: 'Crawl Sitemap',
    },
    email_extract: {
      description:
        'Extracts email addresses from page text and mailto: links. Useful for outreach research and contact discovery.',
      example: 'https://quotes.toscrape.com',
      placeholder: 'https://example.com/contact',
      summary: (n) => `Found ${n} email address${n !== 1 ? 'es' : ''}`,
      columns: { email: 'Email', source: 'Source', context: 'Context' },
      emptyHint: 'No emails found on this page.',
      submitLabel: 'Extract Emails',
    },
    json_ld: {
      description:
        'Extracts JSON-LD structured data (schema.org) — products, prices, ratings, and reviews.',
      example: 'https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html',
      placeholder: 'https://example.com/product',
      summary: (n) => `Found ${n} JSON-LD schema block${n !== 1 ? 's' : ''}`,
      columns: { type: 'Type', name: 'Name', price: 'Price', price_currency: 'Currency', rating_value: 'Rating' },
      emptyHint: 'No JSON-LD structured data found on this page.',
      submitLabel: 'Extract JSON-LD',
    },
    social_meta: {
      description:
        'Extracts Open Graph and Twitter Card metadata — og:title, og:image, twitter:card, and more.',
      example: 'https://quotes.toscrape.com',
      placeholder: 'https://example.com',
      cardMode: true,
      summary: () => 'Showing social sharing metadata (Open Graph + Twitter)',
      emptyHint: 'No social metadata found.',
      submitLabel: 'Extract Social Meta',
    },
    readability: {
      description:
        'Extracts clean main article text using readability heuristics — strips nav, ads, and boilerplate.',
      example: 'https://quotes.toscrape.com',
      placeholder: 'https://example.com/article',
      articleMode: true,
      summary: (n) => `Extracted article with ${n} word${n !== 1 ? 's' : ''}`,
      emptyHint: 'Could not extract readable content from this page.',
      submitLabel: 'Extract Article',
    },
  };

  const MAX_COMPARE_URLS = 50;

  const SETTINGS_KEY = 'scraper_settings';

  function loadSettings() {
    const defaults = {
      delay: 1.0,
      timeout: 15,
      retries: 3,
      user_agent: '',
      check_robots: true,
      api_key: '',
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

  function apiHeaders() {
    const headers = { 'Content-Type': 'application/json' };
    const apiKey = loadSettings().api_key;
    if (apiKey) headers['X-API-Key'] = apiKey;
    return headers;
  }

  function formatJobError(error) {
    if (!error) return 'Job failed';
    const map = {
      ROBOTS_BLOCKED: 'Blocked by robots.txt. Try Quotes demo or turn off "Check robots.txt" in Settings.',
      ACCESS_DENIED: 'Site blocked access (403). Try Quotes demo or https://quotes.toscrape.com',
      RATE_LIMITED: 'Rate limited by target site (429). Increase delay and retry later.',
      TIMEOUT: 'Request timed out. Increase timeout in Settings.',
      NOT_FOUND: 'Page not found (404). Check the URL.',
      SSRF_BLOCKED: 'URL blocked for security (private/reserved IP).',
    };
    for (const [key, msg] of Object.entries(map)) {
      if (error.includes(key)) return msg;
    }
    if (error.toLowerCase().includes('robots.txt')) {
      return map.ROBOTS_BLOCKED;
    }
    return error.replace(/^(ROBOTS_BLOCKED|ACCESS_DENIED|RATE_LIMITED|TIMEOUT|NOT_FOUND|SSRF_BLOCKED):\s*/, '');
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
    requestAnimationFrame(() => {
      setTimeout(() => {
        el.style.opacity = '0';
        el.style.transform = 'translateX(110%)';
        setTimeout(() => el.remove(), 300);
      }, 4000);
    });
  }

  function calcProgress(job) {
    if (job.status === 'completed') return 100;
    if (job.mode === 'price_compare') return Math.min(Math.max(job.progress, 5), 99);
    if (job.progress > 0 && job.progress <= 100) return job.progress;
    if (job.status === 'running') return Math.min(Math.max(job.progress * 8, 15), 85);
    return 10;
  }

  // --- Error boundary ---
  window.addEventListener('error', (e) => {
    console.error('UI error:', e.error || e.message);
    toast('Something went wrong in the UI. Try refreshing the page.', 'error');
  });

  window.addEventListener('unhandledrejection', (e) => {
    console.error('Unhandled promise:', e.reason);
    toast('An unexpected error occurred. Please try again.', 'error');
  });

  // --- Navigation with transitions ---
  $$('.nav-item').forEach((btn) => {
    btn.addEventListener('click', () => {
      $$('.nav-item').forEach((b) => b.classList.remove('active'));
      btn.classList.add('active');
      const view = btn.dataset.view;
      $$('.view').forEach((v) => {
        v.classList.remove('active');
        v.classList.add('view-exit');
      });
      const target = $(`#view-${view}`);
      target.classList.remove('view-exit');
      target.classList.add('active', 'view-enter');
      setTimeout(() => target.classList.remove('view-enter'), 300);
      if (view === 'history') loadHistory();
      if (view === 'health') loadHealthDashboard();
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
    const priceComparePanel = $('#price-compare-panel');
    const batchMetaGroup = $('#batch-meta-group');
    const maxUrlsGroup = $('#max-urls-group');
    const tryExampleBtn = $('#try-example-btn');
    const modeDesc = $('#mode-description');
    const submitText = $('.btn-text');
    const pageSubtitle = $('#page-subtitle');

    const isPriceCompare = mode === 'price_compare';
    const isBatchMeta = mode === 'meta';
    priceComparePanel.classList.toggle('hidden', !isPriceCompare);
    batchMetaGroup.classList.toggle('hidden', !isBatchMeta);
    maxUrlsGroup.classList.toggle('hidden', mode !== 'sitemap');
    urlGroup.classList.toggle('hidden', mode === 'quotes' || isPriceCompare);
    selectorsGroup.classList.toggle('hidden', mode !== 'selectors');
    pagesGroup.classList.toggle('hidden', mode !== 'quotes');
    domainGroup.classList.toggle('hidden', mode !== 'links');

    if (pageSubtitle) {
      pageSubtitle.textContent = isPriceCompare
        ? 'Paste product URLs, pick a price selector, and compare — up to 50 sites per run'
        : 'Configure and launch a data extraction job';
    }

    if (mode === 'quotes' || isPriceCompare) {
      $('#url').removeAttribute('required');
    } else {
      $('#url').setAttribute('required', '');
      $('#url').placeholder = cfg.placeholder || 'https://example.com';
    }

    if (cfg.example && !isPriceCompare) {
      tryExampleBtn.classList.remove('hidden');
    } else {
      tryExampleBtn.classList.add('hidden');
    }

    let descHtml = cfg.description;
    if (cfg.recommended && mode !== 'price_compare') {
      descHtml += ' <span class="mode-badge">Recommended for first-time users</span>';
    }
    if (isPriceCompare) {
      descHtml += ' <span class="mode-badge">Easiest way to compare prices</span>';
    }
    modeDesc.innerHTML = descHtml;

    submitText.textContent = cfg.submitLabel || 'Start Scraping';
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

  $('#load-example-urls-btn').addEventListener('click', () => {
    const cfg = MODE_CONFIG.price_compare;
    $('#compare-urls').value = cfg.exampleUrls;
    $('#price-selector').value = cfg.examplePriceSelector;
    $('#product-label').value = cfg.exampleProductLabel;
    toast('Example URLs loaded — click Compare Prices to try it', 'info');
  });

  function parseCsvText(text) {
    return text
      .split(/\r?\n/)
      .flatMap((line) => line.split(','))
      .map((s) => s.trim().replace(/^["']|["']$/g, ''))
      .filter((s) => s && s.toLowerCase() !== 'url' && s.startsWith('http'));
  }

  function handleCsvFile(file, targetTextarea) {
    const reader = new FileReader();
    reader.onload = (e) => {
      const urls = parseCsvText(e.target.result);
      if (!urls.length) {
        toast('No valid URLs found in CSV', 'error');
        return;
      }
      if (urls.length > MAX_COMPARE_URLS) {
        toast(`CSV has ${urls.length} URLs — using first ${MAX_COMPARE_URLS}`, 'info');
      }
      $(targetTextarea).value = urls.slice(0, MAX_COMPARE_URLS).join('\n');
      toast(`Imported ${Math.min(urls.length, MAX_COMPARE_URLS)} URLs from CSV`, 'success');
    };
    reader.readAsText(file);
  }

  $('#csv-import')?.addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (file) handleCsvFile(file, '#compare-urls');
    e.target.value = '';
  });

  $('#meta-csv-import')?.addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (file) handleCsvFile(file, '#batch-meta-urls');
    e.target.value = '';
  });

  $('#suggest-selectors-btn')?.addEventListener('click', async () => {
    const urls = $('#compare-urls').value.split('\n').map((s) => s.trim()).filter(Boolean);
    const singleUrl = $('#url').value.trim();
    const targetUrl = urls[0] || singleUrl;
    if (!targetUrl) {
      toast('Enter a URL first to get selector hints', 'error');
      return;
    }
    const hintsEl = $('#selector-hints');
    hintsEl.classList.remove('hidden');
    hintsEl.innerHTML = '<div class="skeleton skeleton-line"></div>';
    try {
      const res = await fetch(`${API}/selector-hints?url=${encodeURIComponent(targetUrl)}`, {
        headers: apiHeaders(),
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Failed to get hints');
      }
      const data = await res.json();
      const priceHints = (data.price_selectors || []).slice(0, 5);
      if (!priceHints.length) {
        hintsEl.innerHTML = '<p class="form-hint">No price selectors detected on this page.</p>';
        return;
      }
      hintsEl.innerHTML = `
        <p class="form-hint"><strong>Smart selector hints</strong> (click to apply):</p>
        <div class="hint-chips">
          ${priceHints.map((h) => `
            <button type="button" class="hint-chip" data-selector="${escapeHtml(h.selector)}">
              ${escapeHtml(h.selector)} <span class="hint-conf">${Math.round(h.confidence * 100)}%</span>
            </button>
          `).join('')}
        </div>
      `;
      hintsEl.querySelectorAll('.hint-chip').forEach((chip) => {
        chip.addEventListener('click', () => {
          $('#price-selector').value = chip.dataset.selector;
          toast(`Applied selector: ${chip.dataset.selector}`, 'success');
        });
      });
      if (data.recommended_price) {
        $('#price-selector').value = data.recommended_price;
      }
    } catch (err) {
      hintsEl.innerHTML = `<p class="form-hint" style="color:var(--error)">${escapeHtml(err.message)}</p>`;
    }
  });

  document.addEventListener('keydown', (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      const form = $('#scrape-form');
      if (form && !$('#submit-btn').disabled) {
        e.preventDefault();
        form.requestSubmit();
      }
    }
  });

  // --- Health check ---
  async function checkHealth() {
    const badge = $('#health-badge');
    try {
      const res = await fetch(`${API}/health`);
      const data = await res.json();
      if (data.status === 'healthy') {
        badge.innerHTML = '<span class="badge-dot"></span> Online';
        badge.className = 'badge badge-healthy';
      } else {
        badge.innerHTML = '<span class="badge-dot"></span> Degraded';
        badge.className = 'badge badge-pending';
      }
    } catch {
      badge.innerHTML = '<span class="badge-dot"></span> Offline';
      badge.className = 'badge badge-error';
    }
  }

  async function loadHealthDashboard() {
    const container = $('#health-dashboard');
    container.innerHTML = '<div class="health-card glass-panel loading-card"><div class="health-spinner"></div><p>Loading system status...</p></div>';

    try {
      const res = await fetch(`${API}/health/detail`, { headers: apiHeaders() });
      const data = await res.json();

      const cards = [
        { label: 'Status', value: data.status.toUpperCase(), status: data.status === 'healthy' ? 'ok' : 'warn' },
        { label: 'Version', value: data.version, status: 'ok' },
        { label: 'Database', value: data.database, status: data.database === 'connected' ? 'ok' : 'err' },
        { label: 'Uptime', value: formatUptime(data.uptime_seconds), status: 'ok' },
        { label: 'Active Jobs', value: `${data.active_jobs} / ${data.max_concurrent_jobs}`, status: data.active_jobs < data.max_concurrent_jobs ? 'ok' : 'warn' },
        { label: 'Environment', value: data.environment, status: 'ok' },
        { label: 'SSRF Protection', value: data.ssrf_protection ? 'Enabled' : 'Disabled', status: data.ssrf_protection ? 'ok' : 'warn' },
        { label: 'API Key Auth', value: data.api_key_required ? 'Required' : 'Optional', status: data.api_key_required ? 'ok' : 'warn' },
        { label: 'Rate Limit', value: `${data.rate_limit_per_minute}/min`, status: 'ok' },
      ];

      container.innerHTML = cards.map((c, i) => `
        <div class="health-card glass-panel slide-up" style="animation-delay:${i * 0.05}s">
          <div class="health-card-label">${c.label}</div>
          <div class="health-card-value">${escapeHtml(String(c.value))}</div>
          <div class="health-card-status ${c.status}">${c.status === 'ok' ? '● Normal' : c.status === 'warn' ? '● Warning' : '● Error'}</div>
        </div>
      `).join('');

      await loadStatsDashboard();
    } catch {
      container.innerHTML = '<div class="health-card glass-panel"><p style="color:var(--error)">Failed to load health data. Is the server running?</p></div>';
    }
  }

  async function loadStatsDashboard() {
    const statsEl = $('#stats-dashboard');
    if (!statsEl) return;
    statsEl.classList.remove('hidden');
    statsEl.innerHTML = '<div class="health-card glass-panel skeleton-card"><div class="skeleton skeleton-line"></div></div>';

    try {
      const res = await fetch(`${API}/stats`, { headers: apiHeaders() });
      const stats = await res.json();
      const statCards = [
        { label: 'Total Jobs', value: stats.total_jobs, status: 'ok' },
        { label: 'Success Rate', value: `${stats.success_rate}%`, status: stats.success_rate >= 80 ? 'ok' : 'warn' },
        { label: 'Avg Job Time', value: stats.avg_job_duration_seconds != null ? `${stats.avg_job_duration_seconds}s` : 'N/A', status: 'ok' },
        { label: 'Completed', value: stats.completed_jobs, status: 'ok' },
        { label: 'Failed', value: stats.failed_jobs, status: stats.failed_jobs > 0 ? 'warn' : 'ok' },
      ];
      statsEl.innerHTML = `
        <h3 class="stats-heading">Performance Stats</h3>
        ${statCards.map((c, i) => `
          <div class="health-card glass-panel slide-up" style="animation-delay:${i * 0.05}s">
            <div class="health-card-label">${c.label}</div>
            <div class="health-card-value">${escapeHtml(String(c.value))}</div>
            <div class="health-card-status ${c.status}">● Benchmark</div>
          </div>
        `).join('')}
      `;
    } catch {
      statsEl.innerHTML = '';
    }
  }

  function formatUptime(seconds) {
    if (seconds < 60) return `${Math.round(seconds)}s`;
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ${Math.round(seconds % 60)}s`;
    return `${Math.floor(seconds / 3600)}h ${Math.floor((seconds % 3600) / 60)}m`;
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
    if (mode === 'price_compare') {
      const urls = $('#compare-urls').value
        .split('\n')
        .map((s) => s.trim())
        .filter(Boolean);
      if (!urls.length) {
        toast('Paste at least one product page URL', 'error');
        btn.disabled = false;
        $('.btn-text').classList.remove('hidden');
        $('.btn-loader').classList.add('hidden');
        return;
      }
      if (urls.length > MAX_COMPARE_URLS) {
        toast(`Maximum ${MAX_COMPARE_URLS} URLs per run. Run multiple batches for more sites.`, 'error');
        btn.disabled = false;
        $('.btn-text').classList.remove('hidden');
        $('.btn-loader').classList.add('hidden');
        return;
      }
      body.urls = urls;
      const selector = $('#price-selector').value.trim();
      if (selector) body.price_selector = selector;
      const label = $('#product-label').value.trim();
      if (label) body.product_label = label;
      delete body.url;
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
    if (mode === 'meta') {
      const batchUrls = $('#batch-meta-urls')?.value
        .split('\n')
        .map((s) => s.trim())
        .filter(Boolean);
      if (batchUrls?.length) {
        body.urls = batchUrls;
        delete body.url;
      }
    }
    if (mode === 'sitemap') {
      const maxUrls = $('#max-urls')?.value;
      if (maxUrls) body.max_urls = parseInt(maxUrls, 10);
    }

    try {
      const res = await fetch(`${API}/jobs`, {
        method: 'POST',
        headers: apiHeaders(),
        body: JSON.stringify(body),
      });
      if (!res.ok) {
        const err = await res.json();
        const detail = err.detail;
        throw new Error(Array.isArray(detail) ? detail.map((d) => d.msg || d).join(', ') : detail || 'Failed to create job');
      }
      const data = await res.json();
      currentJobId = data.job_id;
      currentJobMode = mode;
      toast('Job queued successfully', 'success');
      $('#results-section').classList.add('hidden');
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
      const res = await fetch(`${API}/jobs/${jobId}`, { headers: apiHeaders() });
      if (!res.ok) return;
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

    const progress = calcProgress(job);

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
          <span class="status-value ${statusClass} status-indicator">${job.status.toUpperCase()}</span>
        </div>
        <div class="status-row">
          <span class="status-label">Items</span>
          <span class="status-value">${job.total_items}</span>
        </div>
        ${job.error ? `<div class="status-row"><span class="status-label">Error</span><span class="status-value status-failed">${escapeHtml(formatJobError(job.error))}</span></div>` : ''}
        ${job.error && job.error.includes('ROBOTS_BLOCKED') ? `<div class="robots-help">Tip: Open <strong>Settings</strong> and uncheck "Check robots.txt", or use <strong>Quotes Demo</strong> mode.</div>` : ''}
        ${job.status === 'failed' ? `<button class="btn btn-retry btn-sm" style="margin-top:0.75rem;width:100%" onclick="window.__retryJob('${job.id}')">↻ Retry Job</button>` : ''}
        <div class="progress-bar"><div class="progress-fill" style="width:${progress}%"></div></div>
      </div>
    `;
  }

  // --- Retry ---
  window.__retryJob = async (jobId) => {
    try {
      const res = await fetch(`${API}/jobs/${jobId}/retry`, {
        method: 'POST',
        headers: apiHeaders(),
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Retry failed');
      }
      const data = await res.json();
      currentJobId = data.job_id;
      toast('Retry job queued', 'success');
      $$('.nav-item').forEach((b) => b.classList.remove('active'));
      $$('.nav-item')[0].classList.add('active');
      $$('.view').forEach((v) => v.classList.remove('active'));
      $('#view-scrape').classList.add('active');
      startPolling(data.job_id);
    } catch (err) {
      toast(err.message, 'error');
    }
  };

  // --- Results ---
  async function loadResults(jobId) {
    const res = await fetch(`${API}/jobs/${jobId}/results`, { headers: apiHeaders() });
    if (!res.ok) {
      toast('Failed to load results', 'error');
      return;
    }
    const data = await res.json();
    resultsData = normalizeResults(data.data, currentJobMode);
    renderResults(resultsData, currentJobMode);
    const section = $('#results-section');
    section.classList.remove('hidden');
    section.classList.remove('reveal');
    void section.offsetWidth;
    section.classList.add('reveal');
    currentJobId = jobId;
  }

  function normalizeResults(data, mode) {
    if ((mode === 'meta' || mode === 'social_meta' || mode === 'readability') && typeof data === 'object' && data !== null && !Array.isArray(data)) {
      return [data];
    }
    if (Array.isArray(data)) {
      const rows = flattenForDisplay(mode, data);
      if (mode === 'price_compare') {
        return sortPriceCompareResults(rows);
      }
      return rows;
    }
    if (typeof data === 'object' && data !== null) return [data];
    return [{ value: data }];
  }

  function sortPriceCompareResults(rows) {
    return [...rows].sort((a, b) => {
      const aNum = a.price_numeric;
      const bNum = b.price_numeric;
      if (aNum != null && bNum != null) return aNum - bNum;
      if (aNum != null) return -1;
      if (bNum != null) return 1;
      if (a.status === 'ok' && b.status !== 'ok') return -1;
      if (b.status === 'ok' && a.status !== 'ok') return 1;
      return (a.site_name || '').localeCompare(b.site_name || '');
    });
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

  function renderSocialMetaCard(data) {
    const metaEl = $('#results-meta');
    const tableWrap = $('#results-table-wrap');
    const emptyEl = $('#results-empty');

    emptyEl.classList.add('hidden');
    tableWrap.classList.add('hidden');
    metaEl.classList.remove('hidden');

    const og = data.open_graph || {};
    const tw = data.twitter || {};
    const ogItems = Object.entries(og).map(([k, v]) => `<li><strong>og:${escapeHtml(k)}</strong> — ${escapeHtml(v)}</li>`).join('');
    const twItems = Object.entries(tw).map(([k, v]) => `<li><strong>twitter:${escapeHtml(k)}</strong> — ${escapeHtml(v)}</li>`).join('');

    metaEl.innerHTML = `
      <div class="meta-card-item">
        <div class="meta-card-label">Title</div>
        <div class="meta-card-value">${escapeHtml(data.title || '—')}</div>
      </div>
      ${data.og_image ? `<div class="meta-card-item"><div class="meta-card-label">OG Image</div><div class="meta-card-value"><a href="${escapeHtml(data.og_image)}" target="_blank" rel="noopener">${escapeHtml(data.og_image)}</a></div></div>` : ''}
      <div class="meta-card-item">
        <div class="meta-card-label">Open Graph</div>
        <ul class="meta-headings-list">${ogItems || '<li>No OG tags found</li>'}</ul>
      </div>
      <div class="meta-card-item">
        <div class="meta-card-label">Twitter Cards</div>
        <ul class="meta-headings-list">${twItems || '<li>No Twitter tags found</li>'}</ul>
      </div>
    `;
    $('#results-count').textContent = `${Object.keys(og).length + Object.keys(tw).length} tags`;
  }

  function renderReadabilityCard(data) {
    const metaEl = $('#results-meta');
    const tableWrap = $('#results-table-wrap');
    const emptyEl = $('#results-empty');

    emptyEl.classList.add('hidden');
    tableWrap.classList.add('hidden');
    metaEl.classList.remove('hidden');

    metaEl.innerHTML = `
      <div class="meta-card-item">
        <div class="meta-card-label">Title</div>
        <div class="meta-card-value">${escapeHtml(data.title || '—')}</div>
      </div>
      <div class="meta-card-item">
        <div class="meta-card-label">Word Count</div>
        <div class="meta-card-value">${data.word_count || 0} words</div>
      </div>
      <div class="meta-card-item">
        <div class="meta-card-label">Excerpt</div>
        <div class="meta-card-value">${escapeHtml(data.excerpt || '')}</div>
      </div>
      <div class="meta-card-item">
        <div class="meta-card-label">Full Text</div>
        <div class="meta-card-value article-text">${escapeHtml((data.text || '').slice(0, 5000))}</div>
      </div>
    `;
    $('#results-count').textContent = `${data.word_count || 0} words`;
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

    if (mode === 'social_meta') {
      renderSocialMetaCard(rows[0]);
      return;
    }

    if (mode === 'readability') {
      renderReadabilityCard(rows[0]);
      return;
    }

    $('#results-meta').classList.add('hidden');
    $('#results-table-wrap').classList.remove('hidden');
    renderResultsTable(rows, mode);
  }

  function renderResultsTable(rows, mode) {
    const thead = $('#results-table thead');
    const tbody = $('#results-table tbody');
    const cfg = MODE_CONFIG[mode] || {};

    let keys = [];
    if (cfg.columns) {
      keys = Object.keys(cfg.columns);
      rows.forEach((row) => {
        Object.keys(row).forEach((k) => {
          if (!keys.includes(k) && k !== 'product_label') keys.push(k);
        });
      });
      if (mode === 'price_compare') {
        keys = keys.filter((k) => k !== 'product_label' && k !== 'price_numeric');
      }
    } else {
      rows.forEach((row) => {
        Object.keys(row).forEach((k) => {
          if (!keys.includes(k)) keys.push(k);
        });
      });
    }

    thead.innerHTML = `<tr>${keys.map((k) => `<th>${escapeHtml(getColumnLabel(mode, k))}</th>`).join('')}</tr>`;
    tbody.innerHTML = rows
      .map(
        (row) =>
          `<tr>${keys
            .map((k) => {
              const val = flatten(row[k]);
              if (mode === 'price_compare' && k === 'url' && val) {
                return `<td class="link-url"><a href="${escapeHtml(val)}" target="_blank" rel="noopener">Open</a></td>`;
              }
              if (mode === 'price_compare' && k === 'status') {
                const cls = val === 'ok' ? 'status-ok' : 'status-error';
                return `<td class="${cls}">${escapeHtml(val === 'ok' ? 'OK' : 'Error')}</td>`;
              }
              if (mode === 'price_compare' && k === 'price_text' && val) {
                return `<td class="price-cell">${escapeHtml(String(val))}</td>`;
              }
              if (mode === 'links' && k === 'url' && val) {
                return `<td class="link-url" title="${escapeHtml(val)}"><a href="${escapeHtml(val)}" target="_blank" rel="noopener">${escapeHtml(val)}</a></td>`;
              }
              return `<td title="${escapeHtml(String(val))}">${escapeHtml(String(val))}</td>`;
            })
            .join('')}</tr>`
      )
      .join('');

    const countLabel = mode === 'price_compare'
      ? `${rows.length} site${rows.length !== 1 ? 's' : ''}`
      : `${rows.length} item${rows.length !== 1 ? 's' : ''}`;
    $('#results-count').textContent = countLabel;
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
    const tbody = $('#history-table tbody');
    tbody.innerHTML = '<tr><td colspan="7"><div class="skeleton skeleton-line"></div></td></tr>';
    try {
      const res = await fetch(`${API}/jobs?limit=50`, { headers: apiHeaders() });
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
            <div class="history-actions">
              ${job.status === 'completed' ? `<button class="btn btn-ghost btn-sm" onclick="window.__viewJob('${job.id}')">View</button>` : ''}
              ${job.status === 'failed' ? `<button class="btn btn-ghost btn-sm" onclick="window.__viewJob('${job.id}')" title="${escapeHtml(formatJobError(job.error || ''))}">Details</button>` : ''}
              ${job.status === 'failed' ? `<button class="btn btn-retry btn-sm" onclick="window.__retryJob('${job.id}')">↻ Retry</button>` : ''}
            </div>
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
    const res = await fetch(`${API}/jobs/${jobId}`, { headers: apiHeaders() });
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
    try {
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
    } catch (err) {
      console.error('Init failed:', err);
      toast('Failed to initialize dashboard', 'error');
    }
  }

  init();
})();
