#!/usr/bin/env bash
# Convenience wrapper: ensures root and launches KaliWatch.
set -e
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec sudo python3 "$DIR/kalwatch.py"
