"""widgets/dashboard.py

Overview tab: compact summary cards pulling one headline metric from
each monitor, so the user can glance at overall system/network health
without switching tabs.
"""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Grid
from textual.widgets import Static

from monitors.bt_monitor import BluetoothMonitor
from monitors.net_monitor import NetworkMonitor
from monitors.svc_monitor import ServiceMonitor
from monitors.sys_monitor import SystemMonitor
from monitors.wifi_monitor import WifiMonitor
from utils.helpers import human_rate


class Dashboard(Grid):
    """Grid of summary cards, one per monitor, refreshed on an interval."""

    def __init__(
        self,
        sys_monitor: SystemMonitor,
        net_monitor: NetworkMonitor,
        wifi_monitor: WifiMonitor,
        bt_monitor: BluetoothMonitor,
        svc_monitor: ServiceMonitor,
    ) -> None:
        super().__init__(id="dashboard_grid")
        self.sys_monitor = sys_monitor
        self.net_monitor = net_monitor
        self.wifi_monitor = wifi_monitor
        self.bt_monitor = bt_monitor
        self.svc_monitor = svc_monitor

    def compose(self) -> ComposeResult:
        yield Static("", id="card_cpu", classes="card")
        yield Static("", id="card_mem", classes="card")
        yield Static("", id="card_net", classes="card")
        yield Static("", id="card_wifi", classes="card")
        yield Static("", id="card_bt", classes="card")
        yield Static("", id="card_svc", classes="card")

    def on_mount(self) -> None:
        self.set_interval(1.0, self.refresh_data)

    def refresh_data(self) -> None:
        sys_data = self.sys_monitor.latest_data
        if sys_data.get("status") == "ok":
            self.query_one("#card_cpu", Static).update(
                f"[bold green]CPU[/bold green]\n{sys_data['cpu_avg']:.1f}% avg"
            )
            self.query_one("#card_mem", Static).update(
                f"[bold green]Memory[/bold green]\n{sys_data['mem_percent']:.1f}% used"
            )

        net_data = self.net_monitor.latest_data
        if net_data.get("status") == "ok":
            total_rx = sum(s["rx_rate"] for s in net_data.get("interfaces", {}).values())
            total_tx = sum(s["tx_rate"] for s in net_data.get("interfaces", {}).values())
            self.query_one("#card_net", Static).update(
                f"[bold green]Network[/bold green]\n"
                f"RX {human_rate(total_rx)}  TX {human_rate(total_tx)}"
            )

        wifi_data = self.wifi_monitor.latest_data
        if wifi_data.get("status") == "no_adapter":
            wifi_text = "no adapter"
        else:
            wifi_text = f"{len(wifi_data.get('access_points', []))} networks"
        self.query_one("#card_wifi", Static).update(f"[bold green]WiFi[/bold green]\n{wifi_text}")

        bt_data = self.bt_monitor.latest_data
        if bt_data.get("status") == "no_adapter":
            bt_text = "no adapter"
        else:
            bt_text = f"{len(bt_data.get('devices', []))} devices"
        self.query_one("#card_bt", Static).update(f"[bold green]Bluetooth[/bold green]\n{bt_text}")

        svc_data = self.svc_monitor.latest_data
        if svc_data.get("status") == "ok":
            self.query_one("#card_svc", Static).update(
                f"[bold green]Services[/bold green]\n"
                f"{len(svc_data.get('listening', []))} listening / "
                f"{svc_data.get('established_count', 0)} established"
            )
