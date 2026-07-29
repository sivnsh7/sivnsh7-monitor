"""widgets/bt_tab.py

Renders discoverable nearby Bluetooth devices (Name/MAC) sourced from
a `BluetoothMonitor` instance.
"""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.widgets import DataTable, Static

from monitors.bt_monitor import BluetoothMonitor


class BluetoothTab(VerticalScroll):
    """Tab showing a live-refreshing table of nearby Bluetooth devices."""

    def __init__(self, monitor: BluetoothMonitor) -> None:
        super().__init__()
        self.monitor = monitor

    def compose(self) -> ComposeResult:
        yield Static("Scanning...", id="bt_status")
        yield DataTable(id="bt_table")

    def on_mount(self) -> None:
        table = self.query_one("#bt_table", DataTable)
        table.add_columns("Name", "MAC Address")
        self.set_interval(3.0, self.refresh_data)

    def refresh_data(self) -> None:
        data = self.monitor.latest_data
        status_widget = self.query_one("#bt_status", Static)
        table = self.query_one("#bt_table", DataTable)

        if data.get("status") == "no_adapter":
            status_widget.update("[#F26D6D]No Bluetooth adapter / scan tool found.[/#F26D6D]")
            table.clear()
            return

        if data.get("error"):
            status_widget.update(f"[#F5C453]{data['error']}[/#F5C453]")
            return

        devices = data.get("devices", [])
        backend = data.get("backend", "?")
        status_widget.update(f"Backend: {backend}   Found: {len(devices)} devices")

        table.clear()
        for dev in devices:
            table.add_row(str(dev.get("name", "Unknown")), str(dev.get("mac", "?")))
