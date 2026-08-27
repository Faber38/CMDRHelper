from __future__ import annotations

import argparse
import json
from pathlib import Path

from PySide6.QtCore import QSettings

from cmdrhelper.edsm_uploader import (
    fetch_discarded_events,
    upload_events,
)


TARGET_TIMESTAMP = "2026-08-26T21:35:02Z"
TARGET_EVENT = "FSDJump"


def find_event(journal: Path):
    game_version = ""
    game_build = ""
    found = None

    with journal.open(
        "r",
        encoding="utf-8",
        errors="replace",
    ) as handle:
        for line in handle:
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue

            if event.get("event") == "Fileheader":
                game_version = str(
                    event.get("gameversion") or game_version
                )
                game_build = str(
                    event.get("build") or game_build
                )

            if (
                event.get("event") == TARGET_EVENT
                and event.get("timestamp") == TARGET_TIMESTAMP
            ):
                found = event

    return game_version, game_build, found


def main():
    parser = argparse.ArgumentParser(
        description="Sendet genau einen bekannten FSDJump als EDSM-Test."
    )
    parser.add_argument("journal", type=Path)
    args = parser.parse_args()

    settings = QSettings(
        "CMDRHelper",
        "CMDRHelper",
    )

    commander = str(
        settings.value("edsm/commander", "")
        or ""
    ).strip()
    api_key = str(
        settings.value("edsm/api_key", "")
        or ""
    ).strip()

    if not commander or not api_key:
        print("EDSM-Zugangsdaten fehlen in CMDRHelper.")
        print("Bitte zuerst in den CMDRHelper-Einstellungen EDSM einrichten.")
        return

    ok, discarded, error = fetch_discarded_events()

    if not ok:
        print("Discard-Liste konnte nicht geladen werden:")
        print(error)
        return

    if TARGET_EVENT in discarded:
        print(
            f"{TARGET_EVENT} steht aktuell auf der EDSM-Discard-Liste. "
            "Der Test wird nicht gesendet."
        )
        return

    game_version, game_build, event = find_event(
        args.journal
    )

    if event is None:
        print(
            "Gesuchter Testevent wurde nicht gefunden:"
        )
        print(TARGET_TIMESTAMP, TARGET_EVENT)
        return

    print("Commander:", commander)
    print("Journal:", args.journal.name)
    print("Game-Version:", game_version)
    print("Game-Build:", game_build)
    print(
        "Sende genau:",
        event.get("timestamp"),
        event.get("event"),
        event.get("StarSystem", ""),
    )
    print()

    ok, reply, error = upload_events(
        commander=commander,
        api_key=api_key,
        game_version=game_version,
        game_build=game_build,
        events=[event],
    )

    print("EDSM-Antwort:")
    print(
        json.dumps(
            reply,
            ensure_ascii=False,
            indent=2,
        )
        if reply is not None
        else "(keine JSON-Antwort)"
    )

    if ok:
        print()
        print("TEST ERFOLGREICH: EDSM hat den Event akzeptiert.")
    else:
        print()
        print("TEST FEHLGESCHLAGEN:")
        print(error)


if __name__ == "__main__":
    main()
