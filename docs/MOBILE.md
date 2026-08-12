# Using Web Scraper Pro on Your Phone

Web Scraper Pro v2.4 is a **mobile-first progressive web app**. Same URL, same backend — optimized for touch and small screens.

---

## Quick Start on Mobile

### Easiest: one-click phone setup (Windows)

Double-click **`phone-setup.bat`** — adds firewall rule, starts server, prints the URL for your phone.

If that still fails (hotspot isolation or phone on mobile data), double-click **`start-tunnel.bat`** and open the public HTTPS URL on your phone. See [TROUBLESHOOTING.md](TROUBLESHOOTING.md).

### 1. Start the server (on your PC)

```powershell
cd web-scraper
.\start.bat
```

The server binds to `0.0.0.0:8000` so other devices on your network can connect. On startup you'll see:

```
Dashboard (this PC):  http://127.0.0.1:8000
Dashboard (phone):    http://192.168.x.x:8000
```

Use the **phone / LAN** URL on your mobile browser.

### 2. Allow Windows Firewall (first time on Windows)

If your phone cannot connect, run **as Administrator**:

```cmd
allow-phone-access.bat
```

This adds an inbound rule for TCP port 8000. Without it, Windows may block phone connections even when the server is running.

### 3. Find your network URL

On Windows PowerShell:

```powershell
ipconfig
```

Look for **IPv4 Address** on your active adapter (Wi-Fi or hotspot, e.g. `192.168.43.100`).

On your phone (same network), open:

```
http://192.168.1.42:8000
```

Replace with the IP shown at startup or from `ipconfig`.

### 4. Sign in (optional)

If the server has `ADMIN_USER` and `ADMIN_PASSWORD` set in `.env`, you'll see a login page. Enter credentials to access the dashboard.

---

## Phone Hotspot Setup

Use this when your PC has no Wi-Fi router, or you want the phone and PC on a network you control.

### Steps

1. **On your phone:** turn on **Mobile Hotspot** (Settings → Hotspot / Tethering).
2. **On your PC:** connect to that hotspot Wi-Fi network (not your home Wi-Fi).
3. **On your PC:** run `.\start.bat` in the `web-scraper` folder.
4. **Note the LAN IP** printed at startup (e.g. `http://192.168.137.1:8000`), or run `ipconfig` and find IPv4 on the hotspot/Wi-Fi adapter.
5. **On your phone:** open that URL in Chrome or Safari (same device that hosts the hotspot is fine).

### Important limitations

| Scenario | Works? |
|----------|--------|
| PC on phone hotspot, phone opens LAN IP | Yes |
| PC on home Wi-Fi, phone on mobile data (SIM) | **No** — different networks |
| PC on Wi-Fi, phone on same Wi-Fi | Yes |
| PC on Ethernet, phone on Wi-Fi (same router) | Yes |

**PC and phone must share a network.** If the PC is on office Wi-Fi and the phone uses cellular data, they cannot talk to each other directly.

### First-time Windows checklist

1. Run `allow-phone-access.bat` as Administrator (opens port 8000 in Windows Firewall).
2. Run `start.bat` — confirm it shows a **phone / LAN** URL, not only `127.0.0.1`.
3. On the phone, use `http://<LAN-IP>:8000` (not `127.0.0.1` — that always means "this device only").

---

## Alternative: ngrok / tunnel (different networks / hotspot isolation)

When PC and phone are on **different networks**, or your phone hotspot blocks phone→PC traffic:

```cmd
start-tunnel.bat
```

Add `NGROK_AUTHTOKEN=...` to `.env` (free at [ngrok dashboard](https://dashboard.ngrok.com/get-started/your-authtoken)).

Or manually with ngrok CLI:

```powershell
# Install ngrok, then with the server running on port 8000:
ngrok http 8000
```

Open the `https://….ngrok-free.app` URL on your phone. Useful for demos; not recommended for production or sensitive data.

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
| Can't reach server from phone | Run **`phone-setup.bat`**. Same network? Use LAN IP, not `127.0.0.1`. See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) |
| Phone on mobile data, PC on Wi-Fi | Won't work over LAN — use **`start-tunnel.bat`** |
| Hotspot won't connect phone to PC | AP isolation — use **`start-tunnel.bat`** |
| Only `127.0.0.1` works | Server was bound to localhost — update to latest and use `start.bat` (binds `0.0.0.0`) |
| Login loop | Clear cookies; check ADMIN_USER/PASSWORD |
| Install banner missing | iOS requires manual Add to Home Screen |
| Old version cached | Hard refresh or clear site data |
| Horizontal scroll | Update to v2.4+ |

---

## Version

This guide applies to **Web Scraper Pro v2.4.0** (Mobile-First Release).

See also: [MOBILE_AUDIT.md](MOBILE_AUDIT.md) for technical audit details.
