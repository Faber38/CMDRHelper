from __future__ import annotations

import json
import logging
import math
from email.utils import parsedate_to_datetime
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from cmdrhelper.version import __version__


logger = logging.getLogger(__name__)
INARA_API_URL = "https://inara.cz/inapi/v1/"
BATCH_SIZE = 25
TIMEOUT_SECONDS = 30
SUCCESS_STATUSES = {200, 202}


def header_presentation(status):
    return {
        "uploading": ("topbar.inara_uploading", "statusOk"),
        "ok": ("topbar.inara_ok", "statusOk"),
        "error": ("topbar.inara_error", "statusWarn"),
        "waiting": ("topbar.inara_waiting", "muted"),
    }.get(status, ("topbar.inara_off", "muted"))


def header_tooltip(status):
    return {
        "waiting": "topbar.inara_waiting_tooltip",
        "uploading": "topbar.inara_uploading_tooltip",
        "ok": "topbar.inara_ok_tooltip",
        "error": "topbar.inara_error_tooltip",
    }.get(status, "topbar.inara_off_tooltip")


def account_guidance(configured):
    if configured:
        return "settings.inara_key_hint", "settings.inara_configured_short"
    return "settings.inara_not_configured", "settings.inara_not_configured_short"


def _optional(data: dict, target: str, source: str, transform=None) -> None:
    value = data.get(source)
    if value is None or value == "":
        return
    try:
        data[target] = transform(value) if transform else value
    except (TypeError, ValueError):
        return
    if target != source:
        data.pop(source, None)


def map_journal_event(event: dict, context: dict) -> tuple[str, dict] | None:
    """Map only journal events whose Inara representation is unambiguous."""
    event_type = str(event.get("event") or "")
    system = str(event.get("StarSystem") or context.get("system") or "")
    station = str(event.get("StationName") or context.get("station") or "")
    ship_type = event.get("ShipType") or context.get("ship_type")
    ship_id = event.get("ShipID") or context.get("ship_id")

    def travel(include_station=False, include_body=False) -> dict:
        data = {"starsystemName": system}
        if isinstance(event.get("StarPos"), list) and len(event["StarPos"]) == 3:
            data["starsystemCoords"] = event["StarPos"]
        if include_station and station:
            data["stationName"] = station
        if event.get("MarketID") is not None:
            data["marketID"] = event["MarketID"]
        body = event.get("Body") or event.get("BodyName")
        if include_body and body:
            data["starsystemBodyName"] = body
        if include_body and event.get("Latitude") is not None and event.get("Longitude") is not None:
            data["starsystemBodyCoords"] = [event["Latitude"], event["Longitude"]]
        if ship_type:
            data["shipType"] = ship_type
        if ship_id is not None:
            data["shipGameID"] = ship_id
        return data

    mapped = None
    if event_type == "FSDJump" and system:
        data = travel()
        if event.get("JumpDist") is not None:
            data["jumpDistance"] = event["JumpDist"]
        mapped = ("addCommanderTravelFSDJump", data)
    elif event_type == "Docked" and system and station:
        mapped = ("addCommanderTravelDock", travel(include_station=True, include_body=True))
    elif event_type == "Touchdown" and system:
        mapped = ("addCommanderTravelLand", travel(include_body=True))
    elif event_type == "CarrierJump" and system:
        mapped = ("addCommanderTravelCarrierJump", travel(include_station=True))
    elif event_type == "Location" and system:
        mapped = ("setCommanderTravelLocation", travel(include_station=True, include_body=True))
    elif event_type == "MissionAccepted" and event.get("MissionID") is not None and event.get("Name"):
        data = {"missionName": event["Name"], "missionGameID": event["MissionID"]}
        fields = {
            "Expiry": "missionExpiry", "Influence": "influenceGain",
            "Reputation": "reputationGain", "Faction": "minorfactionNameOrigin",
            "DestinationSystem": "starsystemNameTarget",
            "DestinationStation": "stationNameTarget",
            "TargetFaction": "minorfactionNameTarget", "TargetType": "targetType",
            "KillCount": "killCount", "Commodity": "commodityName",
            "Count": "commodityCount", "PassengerType": "passengerType",
            "PassengerCount": "passengerCount", "PassengerVIPs": "passengerIsVIP",
        }
        if context.get("system"):
            data["starsystemNameOrigin"] = context["system"]
        if context.get("station"):
            data["stationNameOrigin"] = context["station"]
        for source, target in fields.items():
            if event.get(source) is not None:
                data[target] = event[source]
        mapped = ("addCommanderMission", data)
    elif event_type in {"MissionCompleted", "MissionFailed", "MissionAbandoned"} and event.get("MissionID") is not None:
        suffix = {"MissionCompleted": "Completed", "MissionFailed": "Failed", "MissionAbandoned": "Abandoned"}[event_type]
        data = {"missionGameID": event["MissionID"]}
        if event_type == "MissionCompleted":
            if event.get("Donation") is not None:
                data["donationCredits"] = event["Donation"]
            if event.get("Reward") is not None:
                data["rewardCredits"] = event["Reward"]
        mapped = (f"setCommanderMission{suffix}", data)
    elif event_type == "ShipyardNew" and event.get("ShipType") and event.get("ShipID") is not None:
        mapped = ("addCommanderShip", {"shipType": event["ShipType"], "shipGameID": event["ShipID"]})
    elif event_type == "ShipyardSell" and event.get("ShipType") and event.get("SellShipID") is not None:
        mapped = ("delCommanderShip", {"shipType": event["ShipType"], "shipGameID": event["SellShipID"]})

    if event_type in {"Location", "FSDJump", "CarrierJump"}:
        context["system"] = system
        context["station"] = station if event_type == "Location" else ""
    elif event_type == "Docked":
        context.update(system=system, station=station)
    elif event_type == "Undocked":
        context["station"] = ""
    if event.get("ShipType"):
        context["ship_type"] = event["ShipType"]
    if event.get("ShipID") is not None:
        context["ship_id"] = event["ShipID"]
    return mapped


class InaraUploadError(RuntimeError):
    """Only fixed technical codes cross the transport boundary, never payloads."""
    def __init__(self, code, *, http_status=None, retry_seconds=0):
        super().__init__("Inara: " + code)
        self.code = code
        self.http_status = http_status
        self.retry_seconds = retry_seconds


def retry_after_seconds(value, now=None):
    if not isinstance(value, str):
        return 0
    value = value.strip()
    now = now or datetime.now(timezone.utc)
    try:
        if value.isascii() and value.isdigit():
            seconds = int(value)
        else:
            target = parsedate_to_datetime(value)
            if target.tzinfo is None:
                return 0
            seconds = max(0, math.ceil((target - now).total_seconds()))
        # Validate representability rather than silently shortening a long wait.
        from datetime import timedelta
        now + timedelta(seconds=seconds)
        return seconds
    except (ValueError, TypeError, OverflowError):
        return 0


def _valid_status(record):
    return (isinstance(record, dict) and type(record.get("eventStatus")) is int
            and 100 <= record["eventStatus"] <= 599
            and ("eventStatusText" not in record or isinstance(record["eventStatusText"], str)))


def upload_batch(api_key: str, commander_name: str, commander_fid: str,
                 rows: list[dict], timeout: int = TIMEOUT_SECONDS,
                 opener=urlopen) -> tuple[list[int], dict[int, str]]:
    if not isinstance(commander_fid, str) or not commander_fid.strip():
        raise InaraUploadError("invalid_identity")
    ids = [row.get("id") for row in rows]
    if (not ids or any(type(value) is not int or value <= 0 for value in ids)
            or len(set(ids)) != len(ids)):
        raise InaraUploadError("invalid_batch")
    events = [{"eventName": row["event_name"],
               "eventTimestamp": row["event_timestamp"],
               "eventCustomID": row["id"],
               "eventData": row["event_data"]} for row in rows]
    payload = {"header": {"appName": "CMDRHelper", "appVersion": __version__,
                           "isBeingDeveloped": False, "APIkey": api_key,
                           "commanderName": commander_name,
                           "commanderFrontierID": commander_fid},
               "events": events}
    request = Request(INARA_API_URL,
                      data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                      headers={"User-Agent": f"CMDRHelper/{__version__}",
                               "Content-Type": "application/json", "Accept": "application/json"},
                      method="POST")
    try:
        with opener(request, timeout=timeout) as response:
            reply = json.loads(response.read().decode("utf-8", errors="replace"))
    except HTTPError as exc:
        wait = retry_after_seconds(exc.headers.get("Retry-After") if exc.headers else None) if exc.code == 429 else 0
        raise InaraUploadError("http_error", http_status=exc.code, retry_seconds=wait) from None
    except (URLError, TimeoutError, OSError):
        raise InaraUploadError("transport_error") from None
    except (ValueError, UnicodeError, RecursionError):
        raise InaraUploadError("invalid_json") from None
    if not isinstance(reply, dict) or not _valid_status(reply.get("header")):
        raise InaraUploadError("invalid_response")
    if reply["header"]["eventStatus"] not in SUCCESS_STATUSES:
        raise InaraUploadError("api_rejected")
    returned = reply.get("events")
    if not isinstance(returned, list) or len(returned) != len(rows):
        raise InaraUploadError("incomplete_response")
    # Validate the entire response before accepting even one acknowledgement.
    by_id = {}
    for result in returned:
        if not _valid_status(result):
            raise InaraUploadError("invalid_response")
        identity = result.get("eventCustomID")
        if type(identity) is not int or identity not in ids or identity in by_id:
            raise InaraUploadError("invalid_event_id")
        by_id[identity] = result
    sent, failed = [], {}
    for identity in ids:
        status = by_id[identity]["eventStatus"]
        if status in SUCCESS_STATUSES:
            sent.append(identity)
        else:
            failed[identity] = f"Inara: event_rejected ({status})"
    return sent, failed
