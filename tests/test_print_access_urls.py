"""Startup URL helper tests."""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "print_access_urls.py"


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def test_default_port_in_output():
    result = _run()
    assert "127.0.0.1:8000" in result.stdout


def test_explicit_port_and_qr_flag():
    result = _run("8000", "--qr")
    assert "127.0.0.1:8000" in result.stdout
    assert "qrserver.com" in result.stdout
