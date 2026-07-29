"""monitors/sys_monitor.py

Polls system-wide resource metrics (CPU, RAM, swap, disk, load, uptime,
process count) using psutil. Runs on a 1-second interval by default.
"""

from __future__ import annotations

import os
import time
from typing import Any, Dict, List

import psutil

from monitors.base_monitor import BaseMonitor


class SystemMonitor(BaseMonitor):
    """Publishes a snapshot of CPU/RAM/disk/swap/load/uptime/process-count."""

    interval = 1.0

    def __init__(self) -> None:
        super().__init__()
        self._boot_time = psutil.boot_time()

    def poll(self) -> None:
        per_cpu: List[float] = psutil.cpu_percent(percpu=True)
        cpu_avg: float = sum(per_cpu) / len(per_cpu) if per_cpu else 0.0

        vmem = psutil.virtual_memory()
        swap = psutil.swap_memory()
        disk = psutil.disk_usage("/")

        try:
            load1, load5, load15 = os.getloadavg()
        except (OSError, AttributeError):
            load1 = load5 = load15 = 0.0

        proc_count = len(psutil.pids())

        snapshot: Dict[str, Any] = {
            "status": "ok",
            "per_cpu": per_cpu,
            "cpu_avg": cpu_avg,
            "mem_percent": vmem.percent,
            "mem_used": vmem.used,
            "mem_total": vmem.total,
            "swap_percent": swap.percent,
            "swap_used": swap.used,
            "swap_total": swap.total,
            "disk_percent": disk.percent,
            "disk_used": disk.used,
            "disk_total": disk.total,
            "load1": load1,
            "load5": load5,
            "load15": load15,
            "boot_time": self._boot_time,
            "proc_count": proc_count,
            "timestamp": time.time(),
        }
        self._set_data(**snapshot)
