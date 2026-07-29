"""monitors/svc_monitor.py

Enumerates listening ports and established connections via
psutil.net_connections(), resolving PIDs to process names where
permissions allow. Also reports a simple established-connection count.
"""

from __future__ import annotations

from typing import Any, Dict, List

import psutil

from monitors.base_monitor import BaseMonitor


class ServiceMonitor(BaseMonitor):
    """Publishes listening ports (with owning process) and connection counts."""

    interval = 2.0

    def poll(self) -> None:
        try:
            conns = psutil.net_connections(kind="inet")
        except (psutil.AccessDenied, PermissionError) as exc:
            self._set_error(f"insufficient permissions for connection table: {exc}")
            return

        listening: List[Dict[str, Any]] = []
        established = 0

        for conn in conns:
            status = conn.status
            if status == psutil.CONN_LISTEN:
                proto = "TCP" if conn.type == 1 else "UDP"
                pname = "?"
                if conn.pid:
                    try:
                        pname = psutil.Process(conn.pid).name()
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pname = "?"
                laddr = conn.laddr
                port = laddr.port if laddr else "?"
                listening.append(
                    {
                        "pid": conn.pid or "-",
                        "process": pname,
                        "port": port,
                        "protocol": proto,
                    }
                )
            elif status == "ESTABLISHED":
                established += 1

        listening.sort(key=lambda row: (row["port"] if isinstance(row["port"], int) else 0))

        self._set_data(
            status="ok",
            listening=listening,
            established_count=established,
            total_connections=len(conns),
        )
