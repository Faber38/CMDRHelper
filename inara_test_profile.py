from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from PySide6.QtCore import QSettings

from cmdrhelper.version import __version__


INARA_API_URL = "https://inara.cz/inapi/v1/"


def main():
    settings = QSettings(
        "CMDRHelper",
        "CMDRHelper",
    )

    commander = str(
        settings.value("inara/commander", "")
        or ""
    ).strip()

    api_key = str(
        settings.value("inara/api_key", "")
        or ""
    ).strip()

    if not commander:
        print("INARA Commander-Name fehlt in den CMDRHelper-Einstellungen.")
        sys.exit(1)

    if not api_key:
        print("INARA API-Schlüssel fehlt in den CMDRHelper-Einstellungen.")
        sys.exit(1)

    timestamp = (
        datetime.now(timezone.utc)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z")
    )

    payload = {
        "header": {
            "appName": "CMDRHelper",
            "appVersion": __version__,
            "isBeingDeveloped": True,
            "APIkey": api_key,
            "commanderName": commander,
        },
        "events": [
            {
                "eventName": "getCommanderProfile",
                "eventTimestamp": timestamp,
                "eventData": {
                    "searchName": commander,
                },
            }
        ],
    }

    request = Request(
        INARA_API_URL,
        data=json.dumps(
            payload,
            ensure_ascii=False,
        ).encode("utf-8"),
        headers={
            "User-Agent": f"CMDRHelper/{__version__}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )

    print("Commander:", commander)
    print("CMDRHelper-Version:", __version__)
    print("Sende Testevent: getCommanderProfile")
    print()

    try:
        with urlopen(request, timeout=20) as response:
            raw = response.read().decode(
                "utf-8",
                errors="replace",
            )

    except HTTPError as exc:
        print(f"HTTP-Fehler: {exc.code}")

        try:
            body = exc.read().decode(
                "utf-8",
                errors="replace",
            )
            if body:
                print(body)
        except Exception:
            pass

        sys.exit(1)

    except URLError as exc:
        reason = getattr(
            exc,
            "reason",
            exc,
        )
        print("INARA nicht erreichbar:", reason)
        sys.exit(1)

    except TimeoutError:
        print("Zeitüberschreitung bei der INARA-Anfrage.")
        sys.exit(1)

    except Exception as exc:
        print("INARA-Test fehlgeschlagen:", exc)
        sys.exit(1)

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        print("INARA hat keine gültige JSON-Antwort geliefert.")
        print(raw)
        sys.exit(1)

    print("INARA-Antwort:")
    print(
        json.dumps(
            data,
            ensure_ascii=False,
            indent=2,
        )
    )

    header = data.get("header") or {}
    header_status = header.get("eventStatus")

    if header_status is not None:
        try:
            header_ok = int(header_status) == 200
        except (TypeError, ValueError):
            header_ok = False

        if not header_ok:
            print()
            print(
                "TEST FEHLGESCHLAGEN:",
                header.get("eventStatusText")
                or f"Header-Status {header_status}",
            )
            sys.exit(1)

    events = data.get("events") or []

    if not events:
        print()
        print("TEST FEHLGESCHLAGEN: Keine Event-Antwort erhalten.")
        sys.exit(1)

    event = events[0] or {}
    status = event.get("eventStatus")
    status_text = (
        event.get("eventStatusText")
        or ""
    )

    if status == 200:
        profile = event.get("eventData") or {}

        print()
        print("TEST ERFOLGREICH.")
        print(
            "Commander:",
            profile.get("commanderName")
            or commander,
        )

        # Nur anzeigen, falls INARA diese Felder tatsächlich liefert.
        for key, label in (
            ("commanderFrontierID", "Frontier-ID"),
            ("commanderInaraID", "INARA-ID"),
            ("commanderSquadronName", "Squadron"),
        ):
            value = profile.get(key)
            if value not in (None, ""):
                print(f"{label}: {value}")

        return

    print()
    print(
        "TEST FEHLGESCHLAGEN:",
        status_text
        or f"Event-Status {status}",
    )
    sys.exit(1)


if __name__ == "__main__":
    main()
