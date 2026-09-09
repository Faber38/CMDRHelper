#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
# The helper uses only Python's standard library; no application startup needed.
if ! command -v python3 >/dev/null 2>&1; then
    echo '[FEHLER] Python 3.10 oder neuer wird für die Veröffentlichung benötigt.' >&2
    exit 1
fi
exec python3 -B tools/publish_release.py
