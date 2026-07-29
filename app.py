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

# --------------------------------------------------------------------------
# Minimal, modern dark theme. Neutral slate surfaces, a single restrained
# accent color for structure/emphasis, and desaturated status colors used
# sparingly (only where they mean something) rather than everything green.
# --------------------------------------------------------------------------
BG = "#0E1015"
SURFACE = "#161922"
SURFACE_ALT = "#1C2029"
BORDER = "#2A2F3A"
TEXT = "#E6E8EC"
TEXT_DIM = "#8B93A3"
ACCENT = "#7AA2F7"
OK = "#4ADE80"
WARN = "#F5C453"
DANGER = "#F26D6D"

KALIWATCH_CSS = f"""
Screen {{
    background: {BG};
    color: {TEXT};
}}

Header {{
    background: {SURFACE};
    color: {TEXT};
}}

Footer {{
    background: {SURFACE};
    color: {TEXT_DIM};
}}

Tabs {{
    background: {SURFACE};
}}

Tab {{
    color: {TEXT_DIM};
}}

Tab.-active {{
    color: {ACCENT};
    text-style: bold;
}}

TabbedContent ContentSwitcher {{
    background: {BG};
}}

.section-label {{
    color: {ACCENT};
    text-style: bold;
    margin-top: 1;
    padding: 0 1;
}}

.subtle {{
    color: {TEXT_DIM};
    padding: 0 1;
}}

DataTable {{
    background: {SURFACE};
    color: {TEXT};
    height: auto;
    max-height: 14;
    margin: 0 1 1 1;
    border: round {BORDER};
}}

DataTable > .datatable--header {{
    background: {SURFACE_ALT};
    color: {ACCENT};
    text-style: bold;
}}

DataTable > .datatable--cursor {{
    background: {SURFACE_ALT};
}}

ProgressBar {{
    width: 100%;
    margin: 0 1;
}}

ProgressBar > .bar--bar {{
    color: {ACCENT};
}}

ProgressBar > .bar--complete {{
    color: {ACCENT};
}}

#dashboard_grid {{
    grid-size: 4 2;
    grid-gutter: 1 2;
    padding: 1 2;
}}

.card {{
    background: {SURFACE};
    border: round {BORDER};
    padding: 1 2;
    height: 100%;
}}

.card-title {{
    color: {TEXT_DIM};
    text-style: bold;
}}

.card-value {{
    color: {TEXT};
    text-style: bold;
}}

.card-sub {{
    color: {TEXT_DIM};
}}

#status_bar {{
    dock: bottom;
    height: 1;
    background: {SURFACE};
    color: {TEXT_DIM};
    padding: 0 1;
}}
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
            f"{now}  \u2022  root: yes  \u2022  interfaces: {ifaces}"
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
