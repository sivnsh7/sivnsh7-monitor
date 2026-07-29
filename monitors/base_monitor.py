"""monitors/base_monitor.py

Abstract base class for all background monitors. Each concrete monitor
runs its polling/scanning loop on a daemon thread and exposes its
latest snapshot through a lock-protected `data` dict, so the Textual UI
thread can read consistent state without racing the worker thread.
"""

from __future__ import annotations

import threading
from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseMonitor(ABC):
    """Base class for a background-threaded data source.

    Subclasses implement `poll()`, which should perform one unit of work
    (one scan, one sample) and call `self._set_data(...)` to publish
    results. `run_loop` is called on the worker thread and handles the
    sleep/interval and clean shutdown via a `threading.Event`.
    """

    #: Default interval, in seconds, between poll cycles.
    interval: float = 1.0

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._data: Dict[str, Any] = {"status": "starting", "error": None}
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        """Start the monitor's background thread (idempotent)."""
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Signal the background thread to stop and wait briefly for it."""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=2.0)

    @property
    def latest_data(self) -> Dict[str, Any]:
        """Thread-safe snapshot of the monitor's most recent published data."""
        with self._lock:
            return dict(self._data)

    def _set_data(self, **kwargs: Any) -> None:
        """Merge keyword values into the published data dict under the lock."""
        with self._lock:
            self._data.update(kwargs)
            self._data["error"] = None

    def _set_error(self, message: str) -> None:
        """Publish an error/status message without crashing the thread."""
        with self._lock:
            self._data["error"] = message
            self._data["status"] = "error"

    def _run_loop(self) -> None:
        """Worker-thread loop: poll repeatedly until stop() is called."""
        while not self._stop_event.is_set():
            try:
                self.poll()
            except Exception as exc:  # noqa: BLE001 - monitors must never crash the UI
                self._set_error(f"{type(exc).__name__}: {exc}")
            self._stop_event.wait(self.interval)

    @abstractmethod
    def poll(self) -> None:
        """Perform one unit of polling work. Must call `_set_data` to publish results."""
        raise NotImplementedError
