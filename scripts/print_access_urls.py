#!/usr/bin/env python3
"""Print dashboard URLs for local PC and phone (LAN) access."""

from __future__ import annotations

import socket
import subprocess
import sys
import urllib.parse

DEFAULT_PORT = 8000


def _lan_ipv4_addresses() -> list[tuple[str, str]]:
    """Return (ip, hint) pairs for non-loopback IPv4 addresses."""
    seen: set[str] = set()
    results: list[tuple[str, str]] = []

    def add(ip: str, hint: str) -> None:
        if ip.startswith("127.") or ip.startswith("169.254."):
            return
        if ip in seen:
            return
        seen.add(ip)
        results.append((ip, hint))

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect(("8.8.8.8", 80))
            add(sock.getsockname()[0], "default route (try this first)")
    except OSError:
        pass

    try:
        for info in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
            add(info[4][0], "hostname")
    except OSError:
        pass

    if sys.platform == "win32":
        try:
            proc = subprocess.run(
                ["ipconfig"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=False,
            )
            current_adapter = ""
            for line in proc.stdout.splitlines():
                stripped = line.strip()
                if stripped.endswith(":") and "adapter" in stripped.lower():
                    current_adapter = stripped.rstrip(":")
                if "IPv4" in stripped and ":" in stripped:
                    ip = stripped.rsplit(":", 1)[-1].strip()
                    hint = current_adapter or "adapter"
                    add(ip, hint)
        except OSError:
            pass

    return results


def _guess_scenario(ips: list[tuple[str, str]]) -> str:
    if not ips:
        return "unknown"
    primary = ips[0][0]
    if primary.startswith("192.168.43.") or primary.startswith("192.168.137."):
        return "hotspot"
    if primary.startswith("192.168.") or primary.startswith("10."):
        return "wifi"
    return "other"


def _qr_link(url: str) -> str:
    encoded = urllib.parse.quote(url, safe="")
    return f"https://api.qrserver.com/v1/create-qr-code/?size=240x240&data={encoded}"


def _print_banner(title: str) -> None:
    line = "=" * max(len(title) + 4, 52)
    print()
    print(f"  {line}")
    print(f"  {title}")
    print(f"  {line}")


def main() -> int:
    # Robust port parsing: first non-flag positional arg (avoids PowerShell splat quirks)
    port = DEFAULT_PORT
    for arg in sys.argv[1:]:
        if arg.startswith("-"):
            continue
        try:
            port = int(arg)
            break
        except ValueError:
            continue
    show_qr = "--qr" in sys.argv

    print(f"  Dashboard (this PC):  http://127.0.0.1:{port}", flush=True)
    print(f"  API docs (this PC):   http://127.0.0.1:{port}/api/docs", flush=True)
    print(f"  Health (this PC):     http://127.0.0.1:{port}/api/health", flush=True)

    lan_ips = _lan_ipv4_addresses()
    scenario = _guess_scenario(lan_ips)

    print()
    if lan_ips:
        primary_ip, primary_hint = lan_ips[0]
        phone_url = f"http://{primary_ip}:{port}"

        _print_banner("OPEN THIS URL ON YOUR PHONE")
        print()
        print(f"    {phone_url}")
        print()
        print(f"  ({primary_hint})")
        print()

        if len(lan_ips) > 1:
            print("  Other IPs to try if the above fails:")
            for ip, hint in lan_ips[1:]:
                print(f"    http://{ip}:{port}  ({hint})")
            print()

        if scenario == "hotspot":
            print("  Hotspot detected: PC is connected to a phone hotspot.")
            print("  On the PHONE that created the hotspot, open the URL above.")
            print()
            print("  If the phone still cannot connect, your hotspot may block")
            print("  phone-to-PC traffic (AP/client isolation). Use start-tunnel.bat")
            print("  instead - it gives a public HTTPS link that always works.")
        else:
            print("  Phone must be on the SAME network as this PC.")
            print("  Do NOT use mobile data (SIM) on the phone - that is a different network.")
            print()
            print("  Options:")
            print("    1. Connect phone to the same Wi-Fi as this PC")
            print("    2. Turn on phone hotspot, connect PC to it, then use URL above")
            print("    3. Run start-tunnel.bat for a public URL (works on any network)")

        if show_qr:
            print()
            print("  QR code (open on phone camera or browser):")
            print(f"    {_qr_link(phone_url)}")
    else:
        print("  Dashboard (phone):  (no LAN IPv4 found — run ipconfig)")
        print()
        print("  Cannot detect a LAN IP. Run start-tunnel.bat for a public URL.")

    print()
    print("  Firewall: run allow-phone-access.bat as Administrator if phone cannot connect.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
