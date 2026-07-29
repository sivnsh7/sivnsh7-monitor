"""widgets/sys_tab.py

Renders live CPU/RAM/Swap/Disk progress bars plus load average, uptime,
and process count, sourced from a `SystemMonitor` instance.
"""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical, VerticalScroll
from textual.widgets import Static, ProgressBar, Label

from monitors.sys_monitor import SystemMonitor
from utils.helpers import human_bytes, uptime_str


class SystemTab(VerticalScroll):
    """Tab showing system resource utilization with live progress bars."""

    def __init__(self, monitor: SystemMonitor) -> None:
        super().__init__()
        self.monitor = monitor
        self._cpu_bars: list[ProgressBar] = []

    def compose(self) -> ComposeResult:
        yield Label("CPU (average)", classes="section-label")
        yield ProgressBar(id="cpu_avg_bar", total=100, show_eta=False)
        yield Static("", id="cpu_per_core")
        yield Label("Memory", classes="section-label")
        yield ProgressBar(id="mem_bar", total=100, show_eta=False)
        yield Static("", id="mem_text")
        yield Label("Swap", classes="section-label")
        yield ProgressBar(id="swap_bar", total=100, show_eta=False)
        yield Static("", id="swap_text")
        yield Label("Disk (/)", classes="section-label")
        yield ProgressBar(id="disk_bar", total=100, show_eta=False)
        yield Static("", id="disk_text")
        yield Static("", id="sys_footer")

    def on_mount(self) -> None:
        self.set_interval(1.0, self.refresh_data)

    def refresh_data(self) -> None:
        data = self.monitor.latest_data
        if data.get("status") != "ok":
            return

        self.query_one("#cpu_avg_bar", ProgressBar).update(progress=data["cpu_avg"])
        per_core = data.get("per_cpu", [])
        core_text = "  ".join(f"C{i}: {v:5.1f}%" for i, v in enumerate(per_core))
        self.query_one("#cpu_per_core", Static).update(core_text)

        self.query_one("#mem_bar", ProgressBar).update(progress=data["mem_percent"])
        self.query_one("#mem_text", Static).update(
            f"{human_bytes(data['mem_used'])} / {human_bytes(data['mem_total'])} "
            f"({data['mem_percent']:.1f}%)"
        )

        self.query_one("#swap_bar", ProgressBar).update(progress=data["swap_percent"])
        self.query_one("#swap_text", Static).update(
            f"{human_bytes(data['swap_used'])} / {human_bytes(data['swap_total'])} "
            f"({data['swap_percent']:.1f}%)"
        )

        self.query_one("#disk_bar", ProgressBar).update(progress=data["disk_percent"])
        self.query_one("#disk_text", Static).update(
            f"{human_bytes(data['disk_used'])} / {human_bytes(data['disk_total'])} "
            f"({data['disk_percent']:.1f}%)"
        )

        uptime = uptime_str(data["boot_time"])
        self.query_one("#sys_footer", Static).update(
            f"Load avg: {data['load1']:.2f} {data['load5']:.2f} {data['load15']:.2f}   "
            f"Uptime: {uptime}   Processes: {data['proc_count']}"
        )
