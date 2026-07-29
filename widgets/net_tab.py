"""widgets/net_tab.py

Renders per-interface bandwidth rates and a protocol-count table,
sourced from a `NetworkMonitor` instance.
"""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.widgets import DataTable, Label, Static

from monitors.net_monitor import NetworkMonitor
from utils.helpers import human_rate


class NetworkTab(VerticalScroll):
    """Tab showing live bandwidth per interface and protocol packet counts."""

    def __init__(self, monitor: NetworkMonitor) -> None:
        super().__init__()
        self.monitor = monitor

    def compose(self) -> ComposeResult:
        yield Label("Interfaces", classes="section-label")
        yield DataTable(id="iface_table")
        yield Label("Protocol Breakdown", classes="section-label")
        yield DataTable(id="proto_table")
        yield Static("", id="net_status")

    def on_mount(self) -> None:
        iface_table = self.query_one("#iface_table", DataTable)
        iface_table.add_columns("Interface", "RX Rate", "TX Rate", "Total RX", "Total TX")

        proto_table = self.query_one("#proto_table", DataTable)
        proto_table.add_columns("Protocol", "Packet Count")

        self.set_interval(1.0, self.refresh_data)

    def refresh_data(self) -> None:
        data = self.monitor.latest_data
        if data.get("status") != "ok":
            return

        iface_table = self.query_one("#iface_table", DataTable)
        iface_table.clear()
        for name, stats in data.get("interfaces", {}).items():
            iface_table.add_row(
                name,
                human_rate(stats["rx_rate"]),
                human_rate(stats["tx_rate"]),
                human_rate(stats["bytes_recv"]).replace("/s", ""),
                human_rate(stats["bytes_sent"]).replace("/s", ""),
            )

        proto_table = self.query_one("#proto_table", DataTable)
        proto_table.clear()
        for proto, count in data.get("protocols", {}).items():
            proto_table.add_row(proto, str(count))

        if not data.get("scapy_available", True):
            self.query_one("#net_status", Static).update(
                "[yellow]scapy not available — protocol counts disabled, bandwidth still live[/yellow]"
            )
        elif data.get("error"):
            self.query_one("#net_status", Static).update(f"[yellow]{data['error']}[/yellow]")
        else:
            self.query_one("#net_status", Static).update("")
