from __future__ import annotations

import json
import hashlib
import os
from datetime import datetime, timezone, timedelta
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from pathlib import Path
from urllib.request import Request, urlopen


EDSM_RANKS_URL = "https://www.edsm.net/api-commander-v1/get-ranks"
EDSM_BODIES_URL = "https://www.edsm.net/api-system-v1/bodies"
EDSM_CACHE_MAX_AGE = timedelta(hours=24)
INARA_API_URL = "https://inara.cz/inapi/v1/"


def _read_json_response(response) -> dict:
    raw = response.read().decode("utf-8", errors="replace")

    if not raw.strip():
        raise ValueError("Der Server hat keine Daten zurückgegeben.")

    data = json.loads(raw)

    if not isinstance(data, dict):
        raise ValueError("Der Server hat ein unerwartetes Datenformat geliefert.")

    return data


def test_edsm_connection(
    commander: str,
    api_key: str,
    timeout: int = 15,
) -> tuple[bool, str]:
    commander = (commander or "").strip()
    api_key = (api_key or "").strip()

    if not commander:
        return False, "Commander-Name fehlt."

    if not api_key:
        return False, "EDSM API-Schlüssel fehlt."

    query = urlencode(
        {
            "commanderName": commander,
            "apiKey": api_key,
        }
    )

    request = Request(
        f"{EDSM_RANKS_URL}?{query}",
        headers={
            "User-Agent": "CMDRHelper/0.1.8.7",
            "Accept": "application/json",
        },
        method="GET",
    )

    try:
        with urlopen(request, timeout=timeout) as response:
            data = _read_json_response(response)

    except HTTPError as exc:
        return False, f"EDSM HTTP-Fehler {exc.code}."

    except URLError as exc:
        reason = getattr(exc, "reason", exc)
        return False, f"EDSM nicht erreichbar: {reason}"

    except TimeoutError:
        return False, "Zeitüberschreitung bei der EDSM-Anfrage."

    except json.JSONDecodeError:
        return False, "EDSM hat keine gültige JSON-Antwort geliefert."

    except Exception as exc:
        return False, f"EDSM-Test fehlgeschlagen: {exc}"

    msgnum = data.get("msgnum")
    message = data.get("msg") or ""

    if msgnum == 100:
        return True, f"Verbindung erfolgreich – CMDR {commander}"

    if msgnum == 201:
        return False, "EDSM: Commander-Name fehlt oder ist ungültig."

    if msgnum == 203:
        return False, "EDSM: Commander-Name oder API-Schlüssel stimmt nicht."

    if msgnum == 207:
        # Dieser Code bedeutet laut EDSM lediglich, dass keine Ränge
        # gespeichert sind. Die Zugangsdaten können trotzdem gültig sein.
        return True, (
            f"EDSM-Zugang erkannt – für CMDR {commander} "
            "sind dort derzeit keine Ränge gespeichert."
        )

    if message:
        return False, f"EDSM: {message} (Code {msgnum})"

    return False, f"EDSM: unbekannte Antwort (Code {msgnum})."


def test_inara_connection(
    commander: str,
    api_key: str,
    timeout: int = 15,
) -> tuple[bool, str]:
    commander = (commander or "").strip()
    api_key = (api_key or "").strip()

    if not commander:
        return False, "Commander-Name fehlt."

    if not api_key:
        return False, "Inara API-Schlüssel fehlt."

    timestamp = (
        datetime.now(timezone.utc)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z")
    )

    payload = {
        "header": {
            "appName": "CMDRHelper",
            "appVersion": "0.1.8.7",
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

    body = json.dumps(payload).encode("utf-8")

    request = Request(
        INARA_API_URL,
        data=body,
        headers={
            "User-Agent": "CMDRHelper/0.1.8.7",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )

    try:
        with urlopen(request, timeout=timeout) as response:
            data = _read_json_response(response)

    except HTTPError as exc:
        if exc.code == 403:
            return False, (
                "Inara hat die Anfrage mit HTTP 403 abgewiesen. "
                "Das kann an der App-Freigabe/Whitelisting liegen."
            )
        return False, f"Inara HTTP-Fehler {exc.code}."

    except URLError as exc:
        reason = getattr(exc, "reason", exc)
        return False, f"Inara nicht erreichbar: {reason}"

    except TimeoutError:
        return False, "Zeitüberschreitung bei der Inara-Anfrage."

    except json.JSONDecodeError:
        return False, "Inara hat keine gültige JSON-Antwort geliefert."

    except Exception as exc:
        return False, f"Inara-Test fehlgeschlagen: {exc}"

    header = data.get("header") or {}
    header_status = header.get("eventStatus")

    if header_status is not None and int(header_status) != 200:
        text = (
            header.get("eventStatusText")
            or "Anfrage wurde von Inara abgelehnt."
        )
        return False, f"Inara: {text} (Code {header_status})"

    events = data.get("events") or []

    if not events:
        return False, "Inara hat keine Event-Antwort zurückgegeben."

    event = events[0] or {}
    status = event.get("eventStatus")
    status_text = event.get("eventStatusText") or ""

    if status == 200:
        event_data = event.get("eventData") or {}
        returned_name = (
            event_data.get("commanderName")
            or commander
        )
        return True, f"Verbindung erfolgreich – CMDR {returned_name}"

    if status_text:
        return False, f"Inara: {status_text} (Code {status})"

    return False, f"Inara-Test fehlgeschlagen (Code {status})."


def _cache_root() -> Path:
    if os.name == "nt":
        base = Path(
            os.environ.get(
                "LOCALAPPDATA",
                str(Path.home() / "AppData" / "Local")
            )
        )
    else:
        base = Path(
            os.environ.get(
                "XDG_CACHE_HOME",
                str(Path.home() / ".cache")
            )
        )

    path = base / "CMDRHelper" / "edsm"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _edsm_cache_file(system_name: str) -> Path:
    digest = hashlib.sha256(
        system_name.encode("utf-8")
    ).hexdigest()[:24]

    return _cache_root() / f"{digest}.json"


def _parse_edsm_timestamp(value: str):
    if not value:
        return None

    try:
        return datetime.fromisoformat(
            value.replace("Z", "+00:00")
        )
    except ValueError:
        return None


def load_cached_edsm_bodies(
    system_name: str,
    max_age: timedelta = EDSM_CACHE_MAX_AGE,
) -> dict | None:
    system_name = (system_name or "").strip()

    if not system_name:
        return None

    path = _edsm_cache_file(system_name)

    if not path.exists():
        return None

    try:
        payload = json.loads(
            path.read_text(encoding="utf-8")
        )
    except Exception:
        return None

    if (
        not isinstance(payload, dict)
        or payload.get("system") != system_name
    ):
        return None

    fetched_at = _parse_edsm_timestamp(
        payload.get("fetched_at") or ""
    )

    if fetched_at is None:
        return None

    now = datetime.now(timezone.utc)

    if now - fetched_at > max_age:
        return None

    data = payload.get("data")

    if not isinstance(data, dict):
        return None

    return data


def _save_edsm_bodies_cache(
    system_name: str,
    data: dict,
):
    payload = {
        "system": system_name,
        "fetched_at": (
            datetime.now(timezone.utc)
            .isoformat(timespec="seconds")
            .replace("+00:00", "Z")
        ),
        "data": data,
    }

    path = _edsm_cache_file(system_name)
    temp = path.with_suffix(".tmp")

    temp.write_text(
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    temp.replace(path)


def _edsm_parent_id(body: dict):
    parents = body.get("parents") or []

    if not parents:
        return None

    try:
        last = parents[-1]

        if isinstance(last, dict) and last:
            return int(
                next(iter(last.values()))
            )
    except Exception:
        pass

    return None


def _normalize_materials(value) -> dict:
    result = {}

    if isinstance(value, dict):
        for name, amount in value.items():
            try:
                result[str(name)] = float(amount)
            except Exception:
                continue

        return result

    if isinstance(value, list):
        for item in value:
            if not isinstance(item, dict):
                continue

            name = (
                item.get("name")
                or item.get("Name")
                or item.get("material")
                or item.get("Material")
            )

            amount = (
                item.get("share")
                if item.get("share") is not None
                else item.get("percent")
                if item.get("percent") is not None
                else item.get("percentage")
                if item.get("percentage") is not None
                else item.get("amount")
                if item.get("amount") is not None
                else item.get("value")
            )

            if not name or amount is None:
                continue

            try:
                result[str(name)] = float(amount)
            except Exception:
                continue

    return result


def _normalize_edsm_body(
    body: dict,
    system_name: str,
) -> dict:
    body_name = body.get("name") or ""
    short_name = body_name

    if (
        system_name
        and body_name.startswith(system_name)
    ):
        short_name = (
            body_name[len(system_name):].strip()
            or body_name
        )

    body_type = body.get("type") or ""
    subtype = body.get("subType") or ""

    terraform_state = (
        body.get("terraformingState")
        or ""
    )
    terraformable = (
        bool(terraform_state)
        and "terraform" in terraform_state.lower()
        and "not terraform" not in terraform_state.lower()
    )

    body_id = body.get("bodyId")

    try:
        if body_id is not None:
            body_id = int(body_id)
    except Exception:
        body_id = None

    return {
        "body_id": body_id,
        "name": body_name,
        "short_name": short_name,
        "body_type": body_type,
        "star_type": (
            subtype
            if body_type == "Star"
            else ""
        ),
        "planet_class": (
            subtype
            if body_type == "Planet"
            else ""
        ),
        "mass_em": body.get("earthMasses"),
        "stellar_mass": body.get("solarMasses"),
        "parent_id": _edsm_parent_id(body),
        "gravity_g": body.get("gravity"),
        "distance_ls": body.get("distanceToArrival"),
        "landable": bool(
            body.get("isLandable", False)
        ),
        "terraformable": terraformable,
        # Sobald EDSM den Körper kennt, ist eine Erstentdeckung
        # für CMDRHelper nicht mehr als "möglich" zu markieren.
        "was_discovered": True,
        # Falls EDSM einen Mapping-Status liefert, behalten wir ihn.
        "was_mapped": (
            bool(body.get("isMapped"))
            if body.get("isMapped") is not None
            else (
                bool(body.get("wasMapped"))
                if body.get("wasMapped") is not None
                else None
            )
        ),
        "atmosphere": (
            body.get("atmosphereType")
            or ""
        ),
        "volcanism": (
            body.get("volcanismType")
            or ""
        ),
        "materials": _normalize_materials(
            body.get("materials")
            or body.get("Materials")
            or {}
        ),
        "biological_signals": 0,
        "self_mapped": False,
        "efficient_mapping": False,
        "journal_scanned": False,
        "edsm_known": True,
        "source": "EDSM",
    }


def fetch_edsm_bodies(
    system_name: str,
    timeout: int = 12,
) -> tuple[bool, dict | None, str]:
    system_name = (system_name or "").strip()

    if not system_name:
        return False, None, "Kein Systemname vorhanden."

    cached = load_cached_edsm_bodies(
        system_name
    )

    if cached is not None:
        return True, cached, "cache"

    query = urlencode(
        {
            "systemName": system_name,
        }
    )

    request = Request(
        f"{EDSM_BODIES_URL}?{query}",
        headers={
            "User-Agent": "CMDRHelper/0.1.8.10",
            "Accept": "application/json",
        },
        method="GET",
    )

    try:
        with urlopen(
            request,
            timeout=timeout
        ) as response:
            raw = _read_json_response(response)

    except HTTPError as exc:
        return (
            False,
            None,
            f"EDSM HTTP-Fehler {exc.code}.",
        )

    except URLError as exc:
        reason = getattr(
            exc,
            "reason",
            exc
        )
        return (
            False,
            None,
            f"EDSM nicht erreichbar: {reason}",
        )

    except TimeoutError:
        return (
            False,
            None,
            "Zeitüberschreitung bei der EDSM-Anfrage.",
        )

    except json.JSONDecodeError:
        return (
            False,
            None,
            "EDSM hat keine gültige JSON-Antwort geliefert.",
        )

    except Exception as exc:
        return (
            False,
            None,
            f"EDSM-Abfrage fehlgeschlagen: {exc}",
        )

    bodies_raw = raw.get("bodies") or []

    if not isinstance(bodies_raw, list):
        bodies_raw = []

    normalized = [
        _normalize_edsm_body(
            body,
            system_name,
        )
        for body in bodies_raw
        if isinstance(body, dict)
    ]

    body_count = raw.get("bodyCount")

    try:
        body_count = int(body_count or 0)
    except Exception:
        body_count = 0

    data = {
        "system": raw.get("name") or system_name,
        "body_count": body_count,
        "bodies": normalized,
    }

    try:
        _save_edsm_bodies_cache(
            system_name,
            data,
        )
    except Exception:
        # Ein Cache-Fehler darf die EDSM-Daten nicht unbrauchbar machen.
        pass

    return True, data, "network"
