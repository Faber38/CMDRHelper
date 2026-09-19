"""Standalone EDSM batch diagnostic; not part of normal application startup.

Run: python tools/edsm_test_batch.py JOURNAL [--limit 10]
Only fetches the public discard list and previews local events; no upload.
This tool needs no credentials. CMDRHelper stores service credentials in local
settings; no credentials are embedded in this repository.
"""
from __future__ import annotations

import argparse
from collections import deque
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from cmdrhelper.edsm_uploader import fetch_discarded_events


def preview_batch(journal: Path, discarded_events: set[str], limit: int):
    """Read the last eligible events without uploader state or network writes."""
    events = deque(maxlen=limit)
    game_version = game_build = ""
    with journal.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(event, dict):
                continue
            name = event.get("event")
            if name == "Fileheader":
                game_version = str(event.get("gameversion") or "")
                game_build = str(event.get("build") or "")
            if name and name not in discarded_events:
                events.append(event)
    return game_version, game_build, list(events)


def main():
    parser = argparse.ArgumentParser(
        description="Zeigt einen kleinen EDSM-Testbatch an. Es wird NICHT gesendet."
    )
    parser.add_argument("journal", type=Path)
    parser.add_argument("--limit", type=int, default=10)
    args = parser.parse_args()
    if args.limit < 1:
        parser.error("--limit muss mindestens 1 sein.")
    if not args.journal.is_file():
        parser.error("Journaldatei wurde nicht gefunden.")

    ok, discarded, error = fetch_discarded_events()
    if not ok:
        print("Discard-Liste konnte nicht geladen werden:")
        print(error)
        return

    game_version, game_build, events = preview_batch(
        args.journal,
        discarded_events=discarded,
        limit=args.limit,
    )

    print("Journal:", args.journal.name)
    print("Game-Version:", game_version)
    print("Game-Build:", game_build)
    print("EDSM-Discard-Events:", len(discarded))
    print("Test-Batch:", len(events))
    print()

    for index, event in enumerate(events, 1):
        print(
            f"{index:2d}. "
            f"{event.get('timestamp', '')}  "
            f"{event.get('event', '')}"
        )

    print()
    print("Es wurde NICHTS an EDSM gesendet.")


if __name__ == "__main__":
    main()
