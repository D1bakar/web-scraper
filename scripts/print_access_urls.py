#!/usr/bin/env python3
"""Print dashboard URLs for local PC and phone (LAN) access."""

from __future__ import annotations

import socket
import sys

DEFAULT_PORT = 8000


def _lan_ipv4_addresses() -> list[str]:
    """Collect non-loopback, non-link-local IPv4 addresses."""
    seen: set[str] = set()

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect(("8.8.8.8", 80))
            seen.add(sock.getsockname()[0])
    except OSError:
        pass

    try:
        for info in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
            ip = info[4][0]
            if not ip.startswith("127.") and not ip.startswith("169.254."):
                seen.add(ip)
    except OSError:
        pass

    return sorted(seen)


def main() -> int:
    port = int(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_PORT
    print(f"  Dashboard (this PC):  http://127.0.0.1:{port}")
    print(f"  API docs (this PC):   http://127.0.0.1:{port}/api/docs")
    print(f"  Health (this PC):     http://127.0.0.1:{port}/api/health")
    print()
    lan_ips = _lan_ipv4_addresses()
    if lan_ips:
        print("  Dashboard (phone / LAN):")
        for ip in lan_ips:
            print(f"    http://{ip}:{port}")
        print()
        print("  Tip: phone and PC must be on the same network (Wi-Fi or hotspot).")
        print("  If the phone cannot connect, run allow-phone-access.bat as Administrator.")
    else:
        print("  Dashboard (phone):  (no LAN IPv4 found — run ipconfig)")
        print()
        print("  If the phone cannot connect, run allow-phone-access.bat as Administrator.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
