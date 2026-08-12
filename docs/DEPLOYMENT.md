# Deployment Guide

Step-by-step instructions for running Web Scraper Pro in development and production.

---

## Health Check Endpoints

Use these for load balancers, Docker healthchecks, and uptime monitors:

| Endpoint | Purpose | Expected response |
|----------|---------|-------------------|
| `GET /api/health/live` | **Liveness probe** (K8s/Docker) | `200` — `{"status":"alive"}` |
| `GET /api/health/ready` | **Readiness probe** (DB connected) | `200` or `503` if DB down |
| `GET /api/health` | Lightweight health check | `200` — `{"status":"healthy","version":"2.3.0"}` |
| `GET /api/health/detail` | Full system dashboard data | `200` — uptime, active jobs, SSRF status |
| `GET /api/stats` | Performance benchmarks | `200` — success rate, avg job duration |
| `GET /` | Dashboard SPA (optional smoke test) | `200` — HTML |

**Docker / compose healthcheck** (included):

```bash
python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health')"
```

---

## Local Development (Windows)

```powershell
cd web-scraper
.\start.bat          # recommended — bypasses PowerShell execution policy
# or
.\start.ps1            # if execution policy allows scripts
```

Open **http://127.0.0.1:8000**

From the parent `v2` workspace:

```powershell
.\start-scraper.ps1
```

### Manual start (any OS)

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp .env.example .env               # Windows: Copy-Item .env.example .env
mkdir -p data
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

> **Common pitfall:** Run commands from `web-scraper/`, not the parent folder. `requirements.txt` and `app/` live here.

---

## Docker

### Quick start

```bash
cd web-scraper
docker compose up --build -d
curl http://localhost:8000/api/health
```

### Production single container

```bash
docker build -t web-scraper-pro .
docker run -d \
  --name scraper \
  -p 8000:8000 \
  -v scraper-data:/app/data \
  -e ENVIRONMENT=production \
  -e API_KEY=your-secret-key \
  -e CORS_ORIGINS=https://yourdomain.com \
  web-scraper-pro
```

### Environment variables (Docker)

Copy from `.env.example`. Minimum for production:

```env
ENVIRONMENT=production
API_KEY=<strong-random-key>
CORS_ORIGINS=https://yourdomain.com
DATABASE_URL=sqlite:///./data/scraper.db
CHECK_ROBOTS_TXT=true
ALLOW_PRIVATE_URLS=false
```

Data persists in the `scraper-data` volume (`/app/data`).

---

## Railway

1. Connect your GitHub repo `D1bakar/web-scraper`.
2. Railway auto-detects the **Procfile**:
   ```
   web: uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
   ```
3. Set environment variables in the Railway dashboard (see `.env.example`).
4. Add a **volume** mounted at `/app/data` for durable SQLite history.
5. Configure health check path: `/api/health/ready`

Or use the included `railway.toml` for automatic configuration.

---

## Render

Use the included `render.yaml` for one-click deploy, or:

1. Create a **Web Service** from the GitHub repo.
2. **Build command:** `pip install -r requirements.txt`
3. **Start command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Set env vars from `.env.example`.
5. Add a **disk** at `/app/data` (optional, for job history).
6. Health check path: `/api/health/ready`

---

## VPS (Ubuntu 22.04+)

### 1. Install dependencies

```bash
sudo apt update && sudo apt install -y python3-venv python3-pip nginx certbot python3-certbot-nginx
git clone https://github.com/D1bakar/web-scraper.git
cd web-scraper
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env — set ENVIRONMENT=production, API_KEY, CORS_ORIGINS
mkdir -p data
```

### 2. Systemd service

Create `/etc/systemd/system/web-scraper.service`:

```ini
[Unit]
Description=Web Scraper Pro
After=network.target

[Service]
User=www-data
WorkingDirectory=/opt/web-scraper
EnvironmentFile=/opt/web-scraper/.env
ExecStart=/opt/web-scraper/.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable --now web-scraper
```

### 3. Nginx reverse proxy + TLS

```nginx
server {
    listen 80;
    server_name scraper.yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
sudo certbot --nginx -d scraper.yourdomain.com
```

---

## Production Checklist

- [ ] `ENVIRONMENT=production`
- [ ] Strong `API_KEY` set; clients send `X-API-Key` header
- [ ] `CORS_ORIGINS` restricted to your domain(s)
- [ ] `ALLOW_PRIVATE_URLS=false`
- [ ] TLS terminated at reverse proxy
- [ ] Persistent volume for `/app/data` (SQLite)
- [ ] Health check monitoring on `/api/health/ready` (readiness) and `/api/health/live` (liveness)
- [ ] Log aggregation configured (`LOG_LEVEL=INFO` or `WARNING`)

---

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `uvicorn not recognized` | Not in venv / wrong folder | `cd web-scraper` then `python -m uvicorn ...` |
| `requirements.txt not found` | Running from parent `v2/` | `cd web-scraper` first |
| PowerShell `PSSecurityException` | Script execution disabled | Use `start.bat` or `powershell -ExecutionPolicy Bypass -File start.ps1` |
| Port 8000 in use | Another process bound | Change `PORT` in `.env` or stop conflicting service |
| Database error on start | Missing `data/` directory | `mkdir data` or let `start.ps1` create it |
