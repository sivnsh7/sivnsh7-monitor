"""monitors/net_monitor.py

Tracks live network activity two ways:
  1. Per-interface bandwidth (RX/TX rate) via psutil counter deltas —
     robust, works even without scapy/root packet-capture support.
  2. Protocol breakdown (TCP/UDP/ICMP/Other) via a scapy sniff() thread
     with store=0 (per PROJECT_RULES, to avoid memory bloat).

If scapy sniffing is unavailable (no libpcap, permissions issue, no
interface), the monitor degrades gracefully: bandwidth stats keep
flowing and protocol counts simply stay at zero with a status note.
"""

from __future__ import annotations

import threading
import time
from typing import Any, Dict

import psutil

from monitors.base_monitor import BaseMonitor
from utils.helpers import list_interfaces

try:
    from scapy.all import sniff, IP, TCP, UDP, ICMP  # type: ignore

    SCAPY_AVAILABLE = True
except Exception:  # noqa: BLE001 - scapy import can fail for many env reasons
    SCAPY_AVAILABLE = False


class NetworkMonitor(BaseMonitor):
    """Publishes per-interface bandwidth rates and protocol packet counts."""

    interval = 1.0

    def __init__(self) -> None:
        super().__init__()
        self._prev_counters = psutil.net_io_counters(pernic=True)
        self._prev_time = time.time()
        self._proto_counts = {"TCP": 0, "UDP": 0, "ICMP": 0, "Other": 0}
        self._proto_lock = threading.Lock()
        self._sniff_thread: threading.Thread | None = None
        self._sniff_started = False

    def start(self) -> None:
        super().start()
        if SCAPY_AVAILABLE and not self._sniff_started:
            self._sniff_started = True
            self._sniff_thread = threading.Thread(target=self._sniff_loop, daemon=True)
            self._sniff_thread.start()

    def _sniff_loop(self) -> None:
        """Runs scapy sniff() with a callback that tallies protocol counts.

        store=0 keeps memory flat; stop_filter checks the shared stop
        event so the sniffer exits cleanly when the app shuts down.
        """
        try:
            sniff(
                prn=self._on_packet,
                store=0,
                stop_filter=lambda _pkt: self._stop_event.is_set(),
                timeout=None,
            )
        except Exception as exc:  # noqa: BLE001
            self._set_error(f"packet capture unavailable: {exc}")

    def _on_packet(self, pkt: Any) -> None:
        try:
            if pkt.haslayer(TCP):
                key = "TCP"
            elif pkt.haslayer(UDP):
                key = "UDP"
            elif pkt.haslayer(ICMP):
                key = "ICMP"
            elif pkt.haslayer(IP):
                key = "Other"
            else:
                key = "Other"
            with self._proto_lock:
                self._proto_counts[key] += 1
        except Exception:  # noqa: BLE001 - never let a malformed packet kill the sniffer
            pass

    def poll(self) -> None:
        now = time.time()
        elapsed = max(now - self._prev_time, 1e-6)
        counters = psutil.net_io_counters(pernic=True)

        interfaces: Dict[str, Dict[str, float]] = {}
        for name in list_interfaces():
            cur = counters.get(name)
            prev = self._prev_counters.get(name)
            if cur is None:
                continue
            if prev is None:
                rx_rate = tx_rate = 0.0
            else:
                rx_rate = max(cur.bytes_recv - prev.bytes_recv, 0) / elapsed
                tx_rate = max(cur.bytes_sent - prev.bytes_sent, 0) / elapsed
            interfaces[name] = {
                "rx_rate": rx_rate,
                "tx_rate": tx_rate,
                "bytes_recv": cur.bytes_recv,
                "bytes_sent": cur.bytes_sent,
            }

        self._prev_counters = counters
        self._prev_time = now

        with self._proto_lock:
            proto_snapshot = dict(self._proto_counts)

        data: Dict[str, Any] = {
            "status": "ok",
            "interfaces": interfaces,
            "protocols": proto_snapshot,
            "scapy_available": SCAPY_AVAILABLE,
        }
        self._set_data(**data)
