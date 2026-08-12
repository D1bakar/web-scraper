#!/usr/bin/env python3
"""Expose the local dashboard via ngrok (works from any network)."""

from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

DEFAULT_PORT = 8000
ROOT = Path(__file__).resolve().parent.parent


def _load_dotenv() -> None:
    env_path = ROOT / ".env"
    if not env_path.is_file():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


def _ensure_pyngrok() -> None:
    try:
        import pyngrok  # noqa: F401
    except ImportError:
        print("  Installing pyngrok...")
    subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "-q", "-r", str(ROOT / "requirements-tunnel.txt")],
            cwd=ROOT,
        )


def main() -> int:
    _load_dotenv()
    port = DEFAULT_PORT
    for arg in sys.argv[1:]:
        if arg.isdigit():
            port = int(arg)

    token = os.environ.get("NGROK_AUTHTOKEN", "").strip()
    if not token:
        print()
        print("  ERROR: NGROK_AUTHTOKEN is not set.")
        print()
        print("  1. Sign up free at https://dashboard.ngrok.com/signup")
        print("  2. Copy your authtoken from https://dashboard.ngrok.com/get-started/your-authtoken")
        print("  3. Add to .env:")
        print("       NGROK_AUTHTOKEN=your_token_here")
        print()
        print("  Alternative: install ngrok CLI and run:  ngrok http 8000")
        print("  Alternative: install cloudflared and run:  cloudflared tunnel --url http://localhost:8000")
        return 1

    _ensure_pyngrok()
    from pyngrok import conf, ngrok

    conf.get_default().auth_token = token
    print()
    print("  Starting ngrok tunnel...")
    tunnel = ngrok.connect(port, bind_tls=True)
    public_url = tunnel.public_url.rstrip("/")

    print()
    print("  ============================================================")
    print("  OPEN THIS URL ON YOUR PHONE (any network, even mobile data)")
    print("  ============================================================")
    print()
    print(f"    {public_url}")
    print()
    print("  Health check:")
    print(f"    {public_url}/api/health")
    print()
    print("  Keep this window open. Press Ctrl+C to stop the tunnel.")
    print()

    try:
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        print()
        print("  Stopping tunnel...")
        ngrok.disconnect(public_url)
        ngrok.kill()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
