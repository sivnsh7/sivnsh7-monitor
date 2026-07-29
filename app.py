"""app.py

The KaliWatch Textual application: builds the tabbed layout, owns the
five monitor instances, and manages their thread lifecycle alongside
the app's own mount/unmount events.
"""

from __future__ import annotations

from datetime import datetime

from textual.app import App, ComposeResult
from textual.containers import Horizontal
from textual.widgets import Footer, Header, Static, TabbedContent, TabPane

from monitors.bt_monitor import BluetoothMonitor
from monitors.net_monitor import NetworkMonitor
from monitors.svc_monitor import ServiceMonitor
from monitors.sys_monitor import SystemMonitor
from monitors.wifi_monitor import WifiMonitor
from utils.helpers import list_interfaces
from widgets.bt_tab import BluetoothTab
from widgets.dashboard import Dashboard
from widgets.net_tab import NetworkTab
from widgets.svc_tab import ServicesTab
from widgets.sys_tab import SystemTab
from widgets.wifi_tab import WifiTab

KALIWATCH_CSS = """
Screen {
    background: #0D0D0D;
    color: #00FF00;
}

Header {
    background: #0D0D0D;
    color: #00FF00;
}

Footer {
    background: #0D0D0D;
    color: #00FF00;
}

.section-label {
    color: #00FF00;
    text-style: bold;
    margin-top: 1;
}

DataTable {
    background: #0D0D0D;
    color: #00FF00;
    height: auto;
    max-height: 16;
}

ProgressBar {
    width: 100%;
}

ProgressBar > .bar--bar {
    color: #00FF00;
}

#dashboard_grid {
    grid-size: 3 2;
    grid-gutter: 1 2;
    padding: 1 2;
}

.card {
    background: #111111;
    border: round #00FF00;
    padding: 1 2;
    height: 100%;
}

#status_bar {
    dock: bottom;
    height: 1;
    background: #0D0D0D;
    color: #00FF00;
}
"""


class KaliWatchApp(App):
    """Root Textual application: header, tabbed content, status footer."""

    CSS = KALIWATCH_CSS
    TITLE = "KaliWatch"
    SUB_TITLE = "Kali Linux Monitoring Dashboard"
    BINDINGS = [("q", "quit", "Quit")]

    def __init__(self) -> None:
        super().__init__()
        self.sys_monitor = SystemMonitor()
        self.net_monitor = NetworkMonitor()
        self.wifi_monitor = WifiMonitor()
        self.bt_monitor = BluetoothMonitor()
        self.svc_monitor = ServiceMonitor()

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with TabbedContent(initial="dashboard"):
            with TabPane("Dashboard", id="dashboard"):
                yield Dashboard(
                    self.sys_monitor,
                    self.net_monitor,
                    self.wifi_monitor,
                    self.bt_monitor,
                    self.svc_monitor,
                )
            with TabPane("Network", id="network"):
                yield NetworkTab(self.net_monitor)
            with TabPane("System", id="system"):
                yield SystemTab(self.sys_monitor)
            with TabPane("WiFi", id="wifi"):
                yield WifiTab(self.wifi_monitor)
            with TabPane("Bluetooth", id="bluetooth"):
                yield BluetoothTab(self.bt_monitor)
            with TabPane("Services", id="services"):
                yield ServicesTab(self.svc_monitor)
        with Horizontal(id="status_bar"):
            yield Static("", id="status_text")
        yield Footer()

    def on_mount(self) -> None:
        for monitor in (
            self.sys_monitor,
            self.net_monitor,
            self.wifi_monitor,
            self.bt_monitor,
            self.svc_monitor,
        ):
            monitor.start()
        self.set_interval(1.0, self._refresh_status_bar)

    def _refresh_status_bar(self) -> None:
        now = datetime.now().strftime("%H:%M:%S")
        ifaces = ", ".join(list_interfaces()) or "none detected"
        self.query_one("#status_text", Static).update(
            f"[bold]{now}[/bold]   root: yes   interfaces: {ifaces}"
        )

    def on_unmount(self) -> None:
        for monitor in (
            self.sys_monitor,
            self.net_monitor,
            self.wifi_monitor,
            self.bt_monitor,
            self.svc_monitor,
        ):
            monitor.stop()
