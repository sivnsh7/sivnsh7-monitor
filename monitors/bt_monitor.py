"""monitors/bt_monitor.py

Scans for discoverable nearby Bluetooth devices. Prefers `hcitool scan`
(classic, widely available on Kali), falls back to a `bluetoothctl`
scan session. Handles a missing/disabled Bluetooth adapter gracefully.
"""

from __future__ import annotations

import subprocess
from typing import Any, Dict, List

from monitors.base_monitor import BaseMonitor
from utils.helpers import tool_available


class BluetoothMonitor(BaseMonitor):
    """Publishes a list of nearby Bluetooth devices: Name/MAC."""

    interval = 8.0

    def poll(self) -> None:
        if tool_available("hcitool"):
            devices = self._scan_hcitool()
            if devices is not None:
                self._set_data(status="ok", devices=devices, backend="hcitool")
                return

        if tool_available("bluetoothctl"):
            devices = self._scan_bluetoothctl()
            if devices is not None:
                self._set_data(status="ok", devices=devices, backend="bluetoothctl")
                return

        self._set_data(status="no_adapter", devices=[], backend=None)

    def _scan_hcitool(self) -> List[Dict[str, Any]] | None:
        try:
            result = subprocess.run(
                ["hcitool", "scan", "--flush"],
                capture_output=True,
                text=True,
                timeout=15.0,
            )
        except Exception:
            return None
        if result.returncode != 0:
            return None

        devices: List[Dict[str, Any]] = []
        for line in result.stdout.splitlines()[1:]:  # skip "Scanning ..." header
            line = line.strip()
            if not line:
                continue
            parts = line.split("\t")
            if len(parts) >= 2:
                devices.append({"mac": parts[0].strip(), "name": parts[1].strip() or "Unknown"})
        return devices

    def _scan_bluetoothctl(self) -> List[Dict[str, Any]] | None:
        try:
            # Run a short scan session, then list discovered devices.
            subprocess.run(
                ["bluetoothctl", "--timeout", "8", "scan", "on"],
                capture_output=True,
                text=True,
                timeout=12.0,
            )
            result = subprocess.run(
                ["bluetoothctl", "devices"],
                capture_output=True,
                text=True,
                timeout=6.0,
            )
        except Exception:
            return None
        if result.returncode != 0:
            return None

        devices: List[Dict[str, Any]] = []
        for line in result.stdout.splitlines():
            # Format: "Device AA:BB:CC:DD:EE:FF Some Name"
            if line.startswith("Device "):
                remainder = line[len("Device "):].strip()
                mac, _, name = remainder.partition(" ")
                devices.append({"mac": mac, "name": name or "Unknown"})
        return devices
