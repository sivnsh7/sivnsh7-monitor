#!/usr/bin/env python3
"""kalwatch.py

Entry point for KaliWatch. Verifies root privileges before importing
any monitor modules (packet capture / scanning require root), then
launches the Textual application.

Usage:
    sudo python3 kalwatch.py
"""

from __future__ import annotations

import os
import sys

# Ensure the project root is importable regardless of the caller's cwd.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.helpers import require_root  # noqa: E402


def main() -> None:
    """Enforce root, then build and run the KaliWatch Textual app."""
    require_root()

    from app import KaliWatchApp  # deferred import: only after root check passes

    app = KaliWatchApp()
    app.run()


if __name__ == "__main__":
    main()
