from __future__ import annotations

import argparse
from pathlib import Path

from cmdrhelper.edsm_uploader import (
    fetch_discarded_events,
    prepare_recent_batch,
)


def main():
    parser = argparse.ArgumentParser(
        description="Zeigt einen kleinen EDSM-Testbatch an. Es wird NICHT gesendet."
    )
    parser.add_argument("journal", type=Path)
    parser.add_argument("--limit", type=int, default=10)
    args = parser.parse_args()

    ok, discarded, error = fetch_discarded_events()
    if not ok:
        print("Discard-Liste konnte nicht geladen werden:")
        print(error)
        return

    batch = prepare_recent_batch(
        args.journal,
        discarded_events=discarded,
        limit=args.limit,
    )

    print("Journal:", batch.journal.name)
    print("Game-Version:", batch.game_version)
    print("Game-Build:", batch.game_build)
    print("EDSM-Discard-Events:", len(discarded))
    print("Test-Batch:", len(batch.events))
    print()

    for index, event in enumerate(batch.events, 1):
        print(
            f"{index:2d}. "
            f"{event.get('timestamp', '')}  "
            f"{event.get('event', '')}"
        )

    print()
    print("Es wurde NICHTS an EDSM gesendet.")


if __name__ == "__main__":
    main()
