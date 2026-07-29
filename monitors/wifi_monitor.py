"""monitors/wifi_monitor.py

Scans for nearby WiFi access points. Prefers `iw dev <iface> scan`
(standard on Kali), falling back to `nmcli -f ... dev wifi list` if
`iw` is unavailable or fails. Degrades gracefully with a clear status
message when no wireless interface is present.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List

from monitors.base_monitor import BaseMonitor
from utils.helpers import list_wireless_interfaces, run_cmd, tool_available


class WifiMonitor(BaseMonitor):
    """Publishes a list of nearby access points: SSID/BSSID/Channel/Signal/Enc."""

    interval = 5.0

    def poll(self) -> None:
        interfaces = list_wireless_interfaces()
        if not interfaces:
            self._set_data(status="no_adapter", access_points=[], interface=None)
            return

        iface = interfaces[0]

        if tool_available("iw"):
            aps = self._scan_iw(iface)
            if aps is not None:
                self._set_data(status="ok", access_points=aps, interface=iface)
                return

        if tool_available("nmcli"):
            aps = self._scan_nmcli()
            if aps is not None:
                self._set_data(status="ok", access_points=aps, interface=iface)
                return

        self._set_error("no working WiFi scan backend (iw/nmcli) found")

    def _scan_iw(self, iface: str) -> List[Dict[str, Any]] | None:
        try:
            output = run_cmd(["iw", "dev", iface, "scan"], timeout=15.0)
        except Exception:
            return None

        aps: List[Dict[str, Any]] = []
        current: Dict[str, Any] = {}
        for line in output.splitlines():
            line = line.strip()
            bss_match = re.match(r"BSS (\S+)", line)
            if bss_match:
                if current:
                    aps.append(current)
                current = {
                    "bssid": bss_match.group(1).split("(")[0],
                    "ssid": "<hidden>",
                    "channel": "?",
                    "signal": "?",
                    "encryption": "Open",
                }
                continue
            if line.startswith("SSID:"):
                current["ssid"] = line.split("SSID:", 1)[1].strip() or "<hidden>"
            elif line.startswith("signal:"):
                current["signal"] = line.split("signal:", 1)[1].strip()
            elif "DS Parameter set: channel" in line:
                current["channel"] = line.split("channel")[-1].strip()
            elif "RSN:" in line or "WPA:" in line:
                current["encryption"] = "WPA/WPA2"
            elif "Privacy" in line and current.get("encryption") == "Open":
                current["encryption"] = "WEP/Unknown"
        if current:
            aps.append(current)
        return aps

    def _scan_nmcli(self) -> List[Dict[str, Any]] | None:
        try:
            output = run_cmd(
                ["nmcli", "-t", "-f", "SSID,BSSID,CHAN,SIGNAL,SECURITY", "dev", "wifi", "list"],
                timeout=15.0,
            )
        except Exception:
            return None

        aps: List[Dict[str, Any]] = []
        for line in output.splitlines():
            parts = line.split(":")
            if len(parts) < 5:
                continue
            ssid, bssid, chan, signal, security = parts[:5]
            aps.append(
                {
                    "ssid": ssid or "<hidden>",
                    "bssid": bssid,
                    "channel": chan,
                    "signal": f"{signal} %",
                    "encryption": security or "Open",
                }
            )
        return aps
