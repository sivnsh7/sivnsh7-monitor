"""utils/helpers.py

Shared, side-effect-light helper functions used across KaliWatch:
root privilege enforcement, network interface discovery, and
human-readable formatting utilities.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from typing import List

import psutil
from rich.console import Console
from rich.panel import Panel


def require_root() -> None:
    """Verify the process is running as root (EUID 0).

    Packet capture, WiFi/Bluetooth scanning, and full process/connection
    visibility all require elevated privileges on Linux. If the check
    fails, prints a styled error panel and exits with status 1.
    """
    if os.geteuid() != 0:
        console = Console()
        console.print(
            Panel(
                "[bold red]KaliWatch requires root privileges.[/bold red]\n\n"
                "Packet capture, WiFi/Bluetooth scanning, and full connection "
                "visibility all need elevated access.\n\n"
                "Run it again with:\n"
                "  [bold green]sudo python3 kalwatch.py[/bold green]",
                title="[bold]Permission Denied[/bold]",
                border_style="red",
            )
        )
        sys.exit(1)


def list_interfaces() -> List[str]:
    """Return a list of non-loopback network interface names present on the host."""
    try:
        names = [name for name in psutil.net_if_addrs().keys() if name != "lo"]
        return sorted(names)
    except Exception:
        return []


def list_wireless_interfaces() -> List[str]:
    """Best-effort discovery of wireless interfaces via /sys/class/net/*/wireless."""
    wireless = []
    for iface in list_interfaces():
        if os.path.isdir(f"/sys/class/net/{iface}/wireless"):
            wireless.append(iface)
    return wireless


def tool_available(name: str) -> bool:
    """Check whether a CLI tool exists on PATH (e.g. 'iw', 'hcitool', 'nmcli')."""
    return shutil.which(name) is not None


def run_cmd(args: List[str], timeout: float = 10.0) -> str:
    """Run a subprocess command and return its stdout as text.

    Raises on non-zero exit or timeout; callers are expected to wrap this
    in try/except per PROJECT_RULES (no unhandled subprocess failures).
    """
    result = subprocess.run(
        args,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=True,
    )
    return result.stdout


def human_bytes(num: float) -> str:
    """Format a byte count as a human-readable string (e.g. '12.3 MB')."""
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if abs(num) < 1024.0:
            return f"{num:3.1f} {unit}"
        num /= 1024.0
    return f"{num:.1f} PB"


def human_rate(bytes_per_sec: float) -> str:
    """Format a byte-rate as a human-readable per-second string."""
    return f"{human_bytes(bytes_per_sec)}/s"


def uptime_str(boot_time_epoch: float) -> str:
    """Format seconds since a given boot-time epoch as 'Xd Xh Xm'."""
    import time

    total = int(time.time() - boot_time_epoch)
    days, rem = divmod(total, 86400)
    hours, rem = divmod(rem, 3600)
    minutes, _ = divmod(rem, 60)
    parts = []
    if days:
        parts.append(f"{days}d")
    if hours or days:
        parts.append(f"{hours}h")
    parts.append(f"{minutes}m")
    return " ".join(parts)
