# Phone Access Troubleshooting

Use this checklist when Web Scraper Pro works on your PC (`http://127.0.0.1:8000`) but **not on your phone**.

---

## Fastest fix (works 99% of the time)

**Double-click `start-tunnel.bat`**

1. Add `NGROK_AUTHTOKEN=...` to `.env` (free at [ngrok dashboard](https://dashboard.ngrok.com/get-started/your-authtoken))
2. Run `start-tunnel.bat`
3. Open the **public HTTPS URL** it prints on your phone — works on mobile data, hotspot, any network

No Wi-Fi matching required.

---

## One-click local setup

**Double-click `phone-setup.bat`**

This script:

1. Adds the Windows Firewall rule (prompts for Admin if needed)
2. Starts the server on `0.0.0.0:8000`
3. Prints the exact URL to open on your phone (with optional QR code link)

---

## Diagnosis checklist

Run through these in order:

| # | Check | How | Expected |
|---|-------|-----|----------|
| 1 | Server running? | Open `http://127.0.0.1:8000/api/health` on PC | `{"status":"healthy",...}` |
| 2 | Bound to all interfaces? | `netstat -ano \| findstr :8000` | `0.0.0.0:8000 ... LISTENING` |
| 3 | LAN IP works on PC? | Open `http://<your-ip>:8000/api/health` on PC (use IP from startup) | Same health JSON |
| 4 | Firewall rule exists? | `netsh advfirewall firewall show rule name="Web Scraper Pro (port 8000)"` | `Enabled: Yes`, `Action: Allow` |
| 5 | Same network? | Phone Wi-Fi name = PC Wi-Fi name, OR PC connected to phone hotspot | Must match |
| 6 | Correct URL on phone? | Use `http://192.168.x.x:8000` — **not** `127.0.0.1` | LAN IP from startup |

---

## Common root causes

### 1. Phone on mobile data (SIM), PC on Wi-Fi

**Most common failure.** Mobile data and Wi-Fi are different networks. The phone cannot reach your PC's LAN IP.

**Fix:**

- Connect phone to the **same Wi-Fi** as the PC, OR
- Turn on phone **hotspot**, connect PC to it, then use the URL from startup, OR
- Use **`start-tunnel.bat`** (works from any network)

### 2. Hotspot client isolation (AP isolation)

Some Android phones block the hotspot host from reaching devices connected to the hotspot (and vice versa). Symptoms: PC has hotspot IP (e.g. `192.168.43.x`), firewall is open, but phone browser times out.

**Fix:** Use **`start-tunnel.bat`**. There is no reliable workaround for AP isolation on all phones.

### 3. Windows Firewall blocking inbound connections

Symptoms: `127.0.0.1` works, LAN IP fails even on the PC itself.

**Fix:**

```cmd
allow-phone-access.bat
```

Run **as Administrator**, or use `phone-setup.bat` which handles this automatically.

### 4. Wrong IP address

| IP | Meaning | Use on phone? |
|----|---------|---------------|
| `127.0.0.1` | This device only | **No** |
| `192.168.x.x` / `10.x.x.x` | LAN address of PC | **Yes** |
| Hotspot gateway (e.g. `192.168.43.1`) | The phone/router itself | Usually **no** — use the PC's IP |

Run `ipconfig` on Windows and look for **IPv4 Address** on your active Wi-Fi or hotspot adapter.

### 5. Server not actually running

Double-clicking `start.bat` opens a window that must **stay open**. Closing it stops the server.

### 6. Stale server on wrong host

If an old instance is bound to `127.0.0.1` only, restart with `start.bat` (it kills stale listeners on port 8000).

### 7. Antivirus / corporate network

Some antivirus or corporate Wi-Fi blocks device-to-device traffic. Try **`start-tunnel.bat`**.

---

## Tunnel options (different networks)

| Method | Setup | Command |
|--------|-------|---------|
| **start-tunnel.bat** | Add `NGROK_AUTHTOKEN` to `.env` | Double-click |
| ngrok CLI | Install from [ngrok.com](https://ngrok.com/download) | `ngrok http 8000` |
| cloudflared | Install from [Cloudflare](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/) | `cloudflared tunnel --url http://localhost:8000` |

`start-tunnel.bat` tries ngrok CLI → cloudflared → pyngrok automatically.

---

## Network setup scenarios

### Scenario A: Home Wi-Fi (recommended)

1. PC and phone on same Wi-Fi
2. Run `phone-setup.bat`
3. Open `http://<PC-LAN-IP>:8000` on phone

### Scenario B: Phone hotspot

1. Enable hotspot on phone
2. Connect **PC** to phone's hotspot Wi-Fi
3. Run `phone-setup.bat`
4. On phone, open the URL shown (e.g. `http://192.168.137.x:8000`)
5. If it fails → hotspot isolation → use `start-tunnel.bat`

### Scenario C: Phone on SIM, PC anywhere

**Will not work over LAN.** Use `start-tunnel.bat`.

---

## Still stuck?

1. On PC: `curl http://127.0.0.1:8000/api/health`
2. On PC: `curl http://<LAN-IP>:8000/api/health` (replace with your IP)
3. If #1 works but #2 fails → firewall or binding issue → run `phone-setup.bat`
4. If both work on PC but phone fails → network mismatch or hotspot isolation → `start-tunnel.bat`
5. Check [MOBILE.md](MOBILE.md) for PWA install and auth setup

---

## Version

This guide applies to **Web Scraper Pro v2.4.0**.
