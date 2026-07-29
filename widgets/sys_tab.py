"""widgets/sys_tab.py

The deep-dive System tab: CPU (avg + per-core), memory, swap, disk for
every mounted partition, load/uptime/process-count, top processes by
CPU usage, and temperature sensors when available. Sourced from a
`SystemMonitor` instance.
"""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.widgets import DataTable, Label, ProgressBar, Static

from monitors.sys_monitor import SystemMonitor
from utils.helpers import human_bytes, uptime_str


class SystemTab(VerticalScroll):
    """Tab showing system resource utilization with live progress bars and tables."""

    def __init__(self, monitor: SystemMonitor) -> None:
        super().__init__()
        self.monitor = monitor

    def compose(self) -> ComposeResult:
        yield Label("CPU", classes="section-label")
        yield Static("", id="cpu_summary", classes="subtle")
        yield ProgressBar(id="cpu_avg_bar", total=100, show_eta=False)
        yield Static("", id="cpu_per_core", classes="subtle")

        yield Label("Memory", classes="section-label")
        yield ProgressBar(id="mem_bar", total=100, show_eta=False)
        yield Static("", id="mem_text", classes="subtle")

        yield Label("Swap", classes="section-label")
        yield ProgressBar(id="swap_bar", total=100, show_eta=False)
        yield Static("", id="swap_text", classes="subtle")

        yield Label("System", classes="section-label")
        yield Static("", id="sys_footer", classes="subtle")

        yield Label("Disk Partitions", classes="section-label")
        yield DataTable(id="disk_table")

        yield Label("Top Processes (by CPU)", classes="section-label")
        yield DataTable(id="proc_table")

        yield Label("Temperature Sensors", classes="section-label")
        yield Static("", id="temp_text", classes="subtle")

    def on_mount(self) -> None:
        disk_table = self.query_one("#disk_table", DataTable)
        disk_table.add_columns("Device", "Mountpoint", "FS", "Used / Total", "%")

        proc_table = self.query_one("#proc_table", DataTable)
        proc_table.add_columns("PID", "Name", "Status", "CPU %", "Mem %")

        self.set_interval(1.0, self.refresh_data)

    def refresh_data(self) -> None:
        data = self.monitor.latest_data
        if data.get("status") != "ok":
            return

        self.query_one("#cpu_summary", Static).update(
            f"{data.get('cpu_count_physical', '?')} physical / "
            f"{data.get('cpu_count_logical', '?')} logical cores"
        )
        self.query_one("#cpu_avg_bar", ProgressBar).update(progress=data["cpu_avg"])
        per_core = data.get("per_cpu", [])
        core_text = "   ".join(f"C{i}: {v:5.1f}%" for i, v in enumerate(per_core))
        self.query_one("#cpu_per_core", Static).update(core_text)

        self.query_one("#mem_bar", ProgressBar).update(progress=data["mem_percent"])
        self.query_one("#mem_text", Static).update(
            f"{human_bytes(data['mem_used'])} used / {human_bytes(data['mem_total'])} total   "
            f"({human_bytes(data.get('mem_available', 0))} available)  \u2014 {data['mem_percent']:.1f}%"
        )

        self.query_one("#swap_bar", ProgressBar).update(progress=data["swap_percent"])
        self.query_one("#swap_text", Static).update(
            f"{human_bytes(data['swap_used'])} / {human_bytes(data['swap_total'])} "
            f"({data['swap_percent']:.1f}%)"
        )

        uptime = uptime_str(data["boot_time"])
        self.query_one("#sys_footer", Static).update(
            f"Load avg: {data['load1']:.2f}  {data['load5']:.2f}  {data['load15']:.2f}   "
            f"Uptime: {uptime}   Processes: {data['proc_count']}"
        )

        disk_table = self.query_one("#disk_table", DataTable)
        disk_table.clear()
        for part in data.get("partitions", []):
            disk_table.add_row(
                part["device"],
                part["mountpoint"],
                part["fstype"],
                f"{human_bytes(part['used'])} / {human_bytes(part['total'])}",
                f"{part['percent']:.1f}%",
            )

        proc_table = self.query_one("#proc_table", DataTable)
        proc_table.clear()
        for proc in data.get("top_procs", []):
            proc_table.add_row(
                str(proc["pid"]),
                proc["name"],
                proc["status"],
                f"{proc['cpu']:.1f}",
                f"{proc['mem']:.1f}",
            )

        temps = data.get("temps", [])
        if temps:
            temp_text = "   ".join(f"{t['label']}: {t['current']:.0f}\u00b0C" for t in temps)
        else:
            temp_text = "No temperature sensors exposed on this system."
        self.query_one("#temp_text", Static).update(temp_text)
