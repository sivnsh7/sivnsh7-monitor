"""widgets/wifi_tab.py

Renders nearby access points (SSID/BSSID/Channel/Signal/Encryption)
sourced from a `WifiMonitor` instance. Shows clear scanning / no
adapter states instead of an empty table.
"""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.widgets import DataTable, Static

from monitors.wifi_monitor import WifiMonitor


class WifiTab(VerticalScroll):
    """Tab showing a live-refreshing table of nearby WiFi access points."""

    def __init__(self, monitor: WifiMonitor) -> None:
        super().__init__()
        self.monitor = monitor

    def compose(self) -> ComposeResult:
        yield Static("Scanning...", id="wifi_status")
        yield DataTable(id="wifi_table")

    def on_mount(self) -> None:
        table = self.query_one("#wifi_table", DataTable)
        table.add_columns("SSID", "BSSID", "Channel", "Signal", "Encryption")
        self.set_interval(2.0, self.refresh_data)

    def refresh_data(self) -> None:
        data = self.monitor.latest_data
        status_widget = self.query_one("#wifi_status", Static)
        table = self.query_one("#wifi_table", DataTable)

        if data.get("status") == "no_adapter":
            status_widget.update("[red]No wireless adapter found.[/red]")
            table.clear()
            return

        if data.get("error"):
            status_widget.update(f"[yellow]{data['error']}[/yellow]")
            return

        aps = data.get("access_points", [])
        iface = data.get("interface", "?")
        status_widget.update(f"Interface: {iface}   Found: {len(aps)} networks")

        table.clear()
        for ap in aps:
            table.add_row(
                str(ap.get("ssid", "?")),
                str(ap.get("bssid", "?")),
                str(ap.get("channel", "?")),
                str(ap.get("signal", "?")),
                str(ap.get("encryption", "?")),
            )
