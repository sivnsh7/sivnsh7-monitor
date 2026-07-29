"""monitors/sys_monitor.py

Polls system-wide resource metrics using psutil: CPU (avg + per-core),
RAM, swap, disk (root + all mounted partitions), load, uptime, process
count, top processes by CPU usage, and hardware temperature sensors
where available. Runs on a 1-second interval by default.
"""

from __future__ import annotations

import os
import time
from typing import Any, Dict, List

import psutil

from monitors.base_monitor import BaseMonitor


class SystemMonitor(BaseMonitor):
    """Publishes a deep snapshot of system resource usage."""

    interval = 1.0
    #: How many top-CPU processes to publish.
    top_n = 8

    def __init__(self) -> None:
        super().__init__()
        self._boot_time = psutil.boot_time()
        # Persistent Process handles so cpu_percent() deltas are meaningful
        # across poll cycles instead of resetting to 0 every time.
        self._proc_cache: Dict[int, psutil.Process] = {}

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
        partitions = self._poll_partitions()
        top_procs = self._poll_top_processes()
        temps = self._poll_temperatures()

        snapshot: Dict[str, Any] = {
            "status": "ok",
            "per_cpu": per_cpu,
            "cpu_avg": cpu_avg,
            "cpu_count_logical": psutil.cpu_count(logical=True),
            "cpu_count_physical": psutil.cpu_count(logical=False),
            "mem_percent": vmem.percent,
            "mem_used": vmem.used,
            "mem_total": vmem.total,
            "mem_available": vmem.available,
            "swap_percent": swap.percent,
            "swap_used": swap.used,
            "swap_total": swap.total,
            "disk_percent": disk.percent,
            "disk_used": disk.used,
            "disk_total": disk.total,
            "partitions": partitions,
            "top_procs": top_procs,
            "temps": temps,
            "load1": load1,
            "load5": load5,
            "load15": load15,
            "boot_time": self._boot_time,
            "proc_count": proc_count,
            "timestamp": time.time(),
        }
        self._set_data(**snapshot)

    def _poll_partitions(self) -> List[Dict[str, Any]]:
        """Usage for every mounted, non-virtual partition."""
        partitions: List[Dict[str, Any]] = []
        try:
            for part in psutil.disk_partitions(all=False):
                try:
                    usage = psutil.disk_usage(part.mountpoint)
                except (PermissionError, OSError):
                    continue
                partitions.append(
                    {
                        "device": part.device,
                        "mountpoint": part.mountpoint,
                        "fstype": part.fstype,
                        "percent": usage.percent,
                        "used": usage.used,
                        "total": usage.total,
                    }
                )
        except Exception:  # noqa: BLE001
            pass
        return partitions

    def _poll_top_processes(self) -> List[Dict[str, Any]]:
        """Top processes by CPU usage, using cached Process handles so
        cpu_percent() reflects real deltas between polls rather than 0.0
        on every call (a common pitfall with psutil.process_iter)."""
        current_pids = set(psutil.pids())

        for pid in list(self._proc_cache.keys()):
            if pid not in current_pids:
                del self._proc_cache[pid]

        rows: List[Dict[str, Any]] = []
        for pid in current_pids:
            proc = self._proc_cache.get(pid)
            if proc is None:
                try:
                    proc = psutil.Process(pid)
                    proc.cpu_percent(None)  # prime the internal delta tracker
                    self._proc_cache[pid] = proc
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
                continue  # skip this cycle; first sample is unreliable

            try:
                cpu = proc.cpu_percent(None)
                mem = proc.memory_percent()
                name = proc.name()
                status = proc.status()
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
            rows.append({"pid": pid, "name": name, "cpu": cpu, "mem": mem, "status": status})

        rows.sort(key=lambda r: r["cpu"], reverse=True)
        return rows[: self.top_n]

    def _poll_temperatures(self) -> List[Dict[str, Any]]:
        """Hardware temperature sensor readings, if the kernel/lm-sensors expose any."""
        readings: List[Dict[str, Any]] = []
        try:
            sensors = psutil.sensors_temperatures()
        except (AttributeError, OSError, NotImplementedError):
            return readings
        for chip, entries in sensors.items():
            for entry in entries:
                readings.append(
                    {
                        "label": entry.label or chip,
                        "current": entry.current,
                        "high": entry.high,
                    }
                )
        return readings
