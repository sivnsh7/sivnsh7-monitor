"""widgets/dashboard.py

Overview tab: eight compact summary cards pulling several headline
metrics from each monitor, so the user can glance at overall
system/network health without switching tabs.
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
from utils.helpers import human_bytes, human_rate, uptime_str

ACCENT = "#7AA2F7"


def _card(title: str, value: str, sub: str = "") -> str:
    lines = [f"[{ACCENT}]{title}[/{ACCENT}]", f"[bold]{value}[/bold]"]
    if sub:
        lines.append(f"[dim]{sub}[/dim]")
    return "\n".join(lines)


class Dashboard(Grid):
    """Grid of summary cards, one per monitor plus system overview, refreshed on an interval."""

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
        yield Static("", id="card_disk", classes="card")
        yield Static("", id="card_net", classes="card")
        yield Static("", id="card_wifi", classes="card")
        yield Static("", id="card_bt", classes="card")
        yield Static("", id="card_svc", classes="card")
        yield Static("", id="card_sys", classes="card")

    def on_mount(self) -> None:
        self.set_interval(1.0, self.refresh_data)

    def refresh_data(self) -> None:
        sys_data = self.sys_monitor.latest_data
        if sys_data.get("status") == "ok":
            self.query_one("#card_cpu", Static).update(
                _card(
                    "CPU",
                    f"{sys_data['cpu_avg']:.1f}%",
                    f"{sys_data.get('cpu_count_logical', '?')} cores",
                )
            )
            self.query_one("#card_mem", Static).update(
                _card(
                    "Memory",
                    f"{sys_data['mem_percent']:.1f}%",
                    f"{human_bytes(sys_data['mem_used'])} / {human_bytes(sys_data['mem_total'])}",
                )
            )
            self.query_one("#card_disk", Static).update(
                _card(
                    "Disk (/)",
                    f"{sys_data['disk_percent']:.1f}%",
                    f"{human_bytes(sys_data['disk_used'])} / {human_bytes(sys_data['disk_total'])}",
                )
            )
            self.query_one("#card_sys", Static).update(
                _card(
                    "System",
                    uptime_str(sys_data["boot_time"]),
                    f"load {sys_data['load1']:.2f}  \u2022  {sys_data['proc_count']} procs",
                )
            )

        net_data = self.net_monitor.latest_data
        if net_data.get("status") == "ok":
            total_rx = sum(s["rx_rate"] for s in net_data.get("interfaces", {}).values())
            total_tx = sum(s["tx_rate"] for s in net_data.get("interfaces", {}).values())
            iface_count = len(net_data.get("interfaces", {}))
            self.query_one("#card_net", Static).update(
                _card(
                    "Network",
                    f"\u2193{human_rate(total_rx)}  \u2191{human_rate(total_tx)}",
                    f"{iface_count} interfaces",
                )
            )

        wifi_data = self.wifi_monitor.latest_data
        if wifi_data.get("status") == "no_adapter":
            self.query_one("#card_wifi", Static).update(_card("WiFi", "\u2014", "no adapter"))
        else:
            aps = wifi_data.get("access_points", [])
            self.query_one("#card_wifi", Static).update(
                _card("WiFi", str(len(aps)), "networks in range")
            )

        bt_data = self.bt_monitor.latest_data
        if bt_data.get("status") == "no_adapter":
            self.query_one("#card_bt", Static).update(_card("Bluetooth", "\u2014", "no adapter"))
        else:
            devices = bt_data.get("devices", [])
            self.query_one("#card_bt", Static).update(
                _card("Bluetooth", str(len(devices)), "devices nearby")
            )

        svc_data = self.svc_monitor.latest_data
        if svc_data.get("status") == "ok":
            self.query_one("#card_svc", Static).update(
                _card(
                    "Services",
                    str(len(svc_data.get("listening", []))),
                    f"listening  \u2022  {svc_data.get('established_count', 0)} established",
                )
            )
