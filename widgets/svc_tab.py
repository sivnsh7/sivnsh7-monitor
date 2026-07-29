"""widgets/svc_tab.py

Renders listening ports (PID/process/port/protocol) and an established
connection counter, sourced from a `ServiceMonitor` instance.
"""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.widgets import DataTable, Static

from monitors.svc_monitor import ServiceMonitor


class ServicesTab(VerticalScroll):
    """Tab showing listening ports and connection counts."""

    def __init__(self, monitor: ServiceMonitor) -> None:
        super().__init__()
        self.monitor = monitor

    def compose(self) -> ComposeResult:
        yield Static("", id="svc_status")
        yield DataTable(id="svc_table")

    def on_mount(self) -> None:
        table = self.query_one("#svc_table", DataTable)
        table.add_columns("PID", "Process", "Port", "Protocol")
        self.set_interval(2.0, self.refresh_data)

    def refresh_data(self) -> None:
        data = self.monitor.latest_data
        status_widget = self.query_one("#svc_status", Static)

        if data.get("error"):
            status_widget.update(f"[yellow]{data['error']}[/yellow]")
            return

        if data.get("status") != "ok":
            return

        listening = data.get("listening", [])
        status_widget.update(
            f"Listening ports: {len(listening)}   "
            f"Established connections: {data.get('established_count', 0)}   "
            f"Total tracked: {data.get('total_connections', 0)}"
        )

        table = self.query_one("#svc_table", DataTable)
        table.clear()
        for row in listening:
            table.add_row(str(row["pid"]), row["process"], str(row["port"]), row["protocol"])
