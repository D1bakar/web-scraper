# Using Web Scraper Pro on Your Phone

Web Scraper Pro v2.4 is a **mobile-first progressive web app**. Same URL, same backend — optimized for touch and small screens.

---

## Quick Start on Mobile

### 1. Start the server (on your PC)

```powershell
cd web-scraper
.\start.bat
```

The server binds to `0.0.0.0:8000` by default.

### 2. Find your network URL

On Windows PowerShell:

```powershell
ipconfig
```

Look for **IPv4 Address** on your Wi-Fi adapter (e.g. `192.168.1.42`).

On your phone (same Wi-Fi), open:

```
http://192.168.1.42:8000
```

Replace with your actual IP.

### 3. Sign in (optional)

If the server has `ADMIN_USER` and `ADMIN_PASSWORD` set in `.env`, you'll see a login page. Enter credentials to access the dashboard.

---

## Install as PWA (Add to Home Screen)

### Android (Chrome)

1. Open the app URL in Chrome
2. Tap the **Install** banner, or Menu → **Install app** / **Add to Home screen**
3. Confirm — the app opens fullscreen without browser chrome

### iPhone (Safari)

1. Open the URL in Safari
2. Tap **Share** → **Add to Home Screen**
3. Name it "Scraper Pro" and tap **Add**

The app uses `display: standalone` and purple theme color `#7c6ff7`.

---

## Mobile Navigation

Bottom bar (<768px):

| Tab | Purpose |
|-----|---------|
| **New Scrape** | Start a job, live status, results |
| **Jobs** | Active + recent jobs as cards |
| **History** | Past jobs with view/retry |
| **Settings** | Scraping defaults, schedules, webhooks, API keys |
| **More** | Health, API docs, install, sign out |

---

## Mobile Tips

- **Touch targets** are 44px+ for buttons and nav items
- **Form drafts** auto-save to sessionStorage — survive page refresh
- **Results** show as cards on phone; tables on desktop
- **Copy** individual result fields with the 📋 button
- **Export** JSON/CSV/Excel via the export buttons (opens download)
- **Offline** — you'll see a toast; drafts are preserved locally
- **Reconnect** — polling resumes automatically when back online

---

## Optional Auth Setup

Add to `.env`:

```env
ADMIN_USER=admin
ADMIN_PASSWORD=your-secure-password
SESSION_SECRET=random-32-char-string
```

Restart the server. Mobile users sign in at `/login`.

---

## API Keys on Mobile

1. Go to **Settings** → **API Keys**
2. Tap **Generate Key**
3. Copy the key immediately — it is shown **once**
4. Use in API calls: `X-API-Key: wsp_...`

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Can't reach server from phone | Same Wi-Fi? Firewall allows port 8000? |
| Login loop | Clear cookies; check ADMIN_USER/PASSWORD |
| Install banner missing | iOS requires manual Add to Home Screen |
| Old version cached | Hard refresh or clear site data |
| Horizontal scroll | Update to v2.4+ |

---

## Version

This guide applies to **Web Scraper Pro v2.4.0** (Mobile-First Release).

See also: [MOBILE_AUDIT.md](MOBILE_AUDIT.md) for technical audit details.
