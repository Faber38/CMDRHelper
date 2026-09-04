from __future__ import annotations

import copy
import json
import platform
from datetime import datetime, timedelta
from pathlib import Path

from cmdrhelper.journal_files import journal_files
from cmdrhelper.mission_manager import build_summary, default_next_step, mission_kind
from cmdrhelper.models import (
    STATUS_ACCEPTED,
    STATUS_AT_DESTINATION,
    STATUS_CARGO_COLLECTED,
    STATUS_COMPLETED,
    STATUS_DATA_RECEIVED,
    STATUS_FAILED,
    STATUS_ABANDONED,
    STATUS_DELIVERING,
    STATUS_EN_ROUTE,
    STATUS_IN_TARGET_SYSTEM,
    STATUS_REDIRECTED,
)
from cmdrhelper.valuation import apply_values
from cmdrhelper.route_planner.models import GuardianFsdBooster, ShipLoadoutData
from cmdrhelper.ship_identity import is_definite_non_ship


class JournalReadError(OSError):
    """Die für den Livezustand maßgebliche Journaldatei war nicht lesbar."""

    def __init__(self, path: Path, cause: OSError):
        super().__init__(f"Journaldatei kann nicht gelesen werden: {path}: {cause}")
        self.path = path
        self.cause = cause


# Nur die aktive Sitzung wird gehalten. Der Byteoffset zeigt stets hinter die
# letzte newline-terminierte Zeile; ein unvollständiger Rest wird erneut gelesen.
_LIVE_LINE_CACHE: dict[str, tuple[int, int, list[str]]] = {}


def _live_complete_lines(path: Path) -> tuple[list[str], int]:
    key = str(path)
    stat = path.stat()
    size = stat.st_size
    modified_ns = int(stat.st_mtime_ns)
    old_offset, old_modified_ns, lines = _LIVE_LINE_CACHE.get(key, (0, 0, []))
    if size < old_offset or (size == old_offset and old_modified_ns != modified_ns):
        old_offset, lines = 0, []
    with path.open("rb") as handle:
        handle.seek(old_offset)
        added = handle.read()
    newline = added.rfind(b"\n")
    if newline < 0:
        return lines, old_offset
    complete = added[:newline + 1]
    new_lines = complete.decode("utf-8", errors="replace").splitlines()
    result = lines + new_lines
    offset = old_offset + newline + 1
    _LIVE_LINE_CACHE.clear()
    _LIVE_LINE_CACHE[key] = (offset, modified_ns, result)
    return result, offset


def read_journal_delta(path: Path, start_offset: int) -> tuple[list[dict], int]:
    """Reads only newline-terminated JSON events after a committed byte offset."""
    path = Path(path)
    start = max(0, int(start_offset or 0))
    size = path.stat().st_size
    if start > size:
        # A truncated/replaced journal cannot safely be treated as an append.
        start = 0
    with path.open("rb") as handle:
        handle.seek(start)
        raw = handle.read()
    newline = raw.rfind(b"\n")
    if newline < 0:
        return [], start
    safe_offset = start + newline + 1
    events = []
    for line in raw[:newline + 1].decode("utf-8", errors="replace").splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(event, dict):
            events.append(event)
    return events, safe_offset


def _optional_float(value):
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _optional_int(value):
    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _optional_bool(value):
    return value if isinstance(value, bool) else None


def sold_system_names(event: dict) -> set[str]:
    names = set()
    for field in ("Systems", "Discovered"):
        for item in event.get(field) or []:
            if isinstance(item, str):
                name = item
            elif isinstance(item, dict):
                name = item.get("SystemName") or item.get("Name") or ""
            else:
                name = ""
            if str(name).strip():
                names.add(str(name).strip().casefold())
    return names


def sold_bio_names(event: dict) -> set[str]:
    names = set()
    for item in event.get("BioData") or []:
        if not isinstance(item, dict):
            continue
        for field in ("Species_Localised", "Species", "Variant_Localised", "Variant"):
            if str(item.get(field) or "").strip():
                names.add(str(item[field]).strip().casefold())
    return names


def _matching_ship(loadout: ShipLoadoutData, event: dict) -> bool:
    event_id = _optional_int(event.get("ShipID"))
    return (
        event_id is None
        or loadout.ship_id is None
        or event_id == loadout.ship_id
    )


def _loadout_from_event(event: dict, previous: ShipLoadoutData) -> ShipLoadoutData:
    ship_id = _optional_int(event.get("ShipID"))
    same_ship = (
        ship_id is not None
        and previous.ship_id is not None
        and ship_id == previous.ship_id
    )
    fuel_capacity = event.get("FuelCapacity")
    main_capacity = None
    reserve_capacity = None
    if isinstance(fuel_capacity, dict):
        main_capacity = _optional_float(fuel_capacity.get("Main"))
        reserve_capacity = _optional_float(fuel_capacity.get("Reserve"))

    modules = event.get("Modules")
    modules = modules if isinstance(modules, list) else []
    fsd = None
    fallback_fsd = None
    boosters = []
    for module in modules:
        if not isinstance(module, dict):
            continue
        slot = str(module.get("Slot") or "").strip()
        item = str(module.get("Item") or "").strip()
        folded_item = item.casefold()
        if "guardianfsdbooster" in folded_item:
            boosters.append(
                GuardianFsdBooster(item=item, on=_optional_bool(module.get("On")))
            )
            continue
        if slot.casefold() == "frameshiftdrive":
            fsd = module
        elif fallback_fsd is None and "hyperdrive" in folded_item:
            fallback_fsd = module
    fsd = fsd or fallback_fsd

    engineering = fsd.get("Engineering") if isinstance(fsd, dict) else None
    engineering = engineering if isinstance(engineering, dict) else {}
    raw_modifiers = engineering.get("Modifiers")
    modifiers = tuple(
        dict(modifier)
        for modifier in (raw_modifiers if isinstance(raw_modifiers, list) else [])
        if isinstance(modifier, dict)
    )
    optimal_mass = None
    max_fuel = None
    for modifier in modifiers:
        label = str(modifier.get("Label") or "")
        if label == "FSDOptimalMass":
            optimal_mass = _optional_float(modifier.get("Value"))
        elif label == "MaxFuelPerJump":
            max_fuel = _optional_float(modifier.get("Value"))

    return ShipLoadoutData(
        ship_id=ship_id,
        ship_type=str(event.get("Ship") or "").strip() or None,
        ship_name=str(event.get("ShipName") or "").strip() or None,
        ship_ident=str(event.get("ShipIdent") or "").strip() or None,
        unladen_mass=_optional_float(event.get("UnladenMass")),
        cargo_capacity=_optional_int(event.get("CargoCapacity")),
        cargo=previous.cargo if same_ship else None,
        max_jump_range=_optional_float(event.get("MaxJumpRange")),
        main_tank_capacity=main_capacity,
        reserve_tank_capacity=reserve_capacity,
        main_fuel=previous.main_fuel if same_ship else None,
        reserve_fuel=previous.reserve_fuel if same_ship else None,
        fsd_item=(str(fsd.get("Item") or "").strip() or None) if fsd else None,
        fsd_on=_optional_bool(fsd.get("On")) if fsd else None,
        fsd_blueprint=str(engineering.get("BlueprintName") or "").strip() or None,
        fsd_engineering_level=_optional_int(engineering.get("Level")),
        fsd_engineering_quality=_optional_float(engineering.get("Quality")),
        fsd_experimental_effect=(
            str(engineering.get("ExperimentalEffect") or "").strip() or None
        ),
        fsd_engineering_modifiers=modifiers,
        fsd_optimal_mass=optimal_mass,
        fsd_max_fuel_per_jump=max_fuel,
        guardian_fsd_boosters=tuple(boosters),
        modules=tuple(dict(module) for module in modules if isinstance(module, dict)),
        loadout_timestamp=str(event.get("timestamp") or "").strip() or None,
        loadout_complete=True,
        loadout_stale=False,
    )

def _direct_parent_id(parents) -> int | None:
    """
    Ermittelt aus Elite-Dangerous-Parents den für CMDRHelper sinnvollsten
    direkten darstellbaren Elternkörper.

    Frontier liefert die Hierarchie vom nahen zum weiter entfernten Parent.
    Planet/Star sind für unsere Systemkarte darstellbar; Null (Barycentre)
    und Ring werden übersprungen.
    """
    if not isinstance(parents, list):
        return None

    for parent in parents:
        if not isinstance(parent, dict):
            continue

        for parent_type, value in parent.items():
            if parent_type not in ("Planet", "Star"):
                continue
            try:
                return int(value)
            except (TypeError, ValueError):
                continue

    return None


def _parent_star_id(parents) -> int | None:
    if not isinstance(parents, list):
        return None
    for parent in parents:
        if isinstance(parent, dict) and "Star" in parent:
            try:
                return int(parent["Star"])
            except (TypeError, ValueError):
                continue
    return None


def _atmosphere_composition(value) -> str:
    if not isinstance(value, (list, dict)) or not value:
        return ""
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))



def default_journal_paths() -> list[Path]:
    home = Path.home()

    if platform.system().lower() == "windows":
        candidates = [
            home / "Saved Games" / "Frontier Developments" / "Elite Dangerous"
        ]
    else:
        candidates = [
            home / ".steam" / "steam" / "steamapps" / "compatdata" / "359320" /
            "pfx" / "drive_c" / "users" / "steamuser" / "Saved Games" /
            "Frontier Developments" / "Elite Dangerous",

            home / ".local" / "share" / "Steam" / "steamapps" / "compatdata" /
            "359320" / "pfx" / "drive_c" / "users" / "steamuser" / "Saved Games" /
            "Frontier Developments" / "Elite Dangerous",

            home / ".steam" / "debian-installation" / "steamapps" / "compatdata" /
            "359320" / "pfx" / "drive_c" / "users" / "steamuser" / "Saved Games" /
            "Frontier Developments" / "Elite Dangerous",
        ]

    return [p for p in candidates if p.exists() and p.is_dir()]


def classify_journal_file(journal: Path) -> dict:
    """Klassifiziert genau eine Datei, ohne Identität anderer Dateien zu erben."""
    journal = Path(journal)
    result = {
        "journal_file": str(journal),
        "commander_id": None,
        "fid_seen": None,
        "commander_name_seen": None,
        "first_event_at": None,
        "last_event_at": None,
        "file_size": None,
        "modified_ns": None,
        "attribution_status": "unknown",
        "fids_seen": [],
    }

    try:
        stat = journal.stat()
        result["file_size"] = int(stat.st_size)
        result["modified_ns"] = int(stat.st_mtime_ns)
    except OSError:
        pass

    identities: dict[str, str] = {}
    with journal.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue

            timestamp = str(event.get("timestamp") or "").strip()
            if timestamp:
                if result["first_event_at"] is None:
                    result["first_event_at"] = timestamp
                result["last_event_at"] = timestamp

            event_type = event.get("event")
            if event_type not in ("Commander", "LoadGame"):
                continue

            fid = str(event.get("FID") or "").strip()
            if not fid:
                continue

            name_field = "Name" if event_type == "Commander" else "Commander"
            name = str(event.get(name_field) or "").strip()
            if name or fid not in identities:
                identities[fid] = name

    result["fids_seen"] = sorted(identities)
    if len(identities) == 1:
        fid = next(iter(identities))
        result["attribution_status"] = "identified"
        result["fid_seen"] = fid
        result["commander_name_seen"] = identities[fid] or None
    elif len(identities) > 1:
        result["attribution_status"] = "ambiguous"

    return result



def _parse_frontier_message_params(message: str) -> dict:
    result = {}
    for part in str(message or "").split(":#")[1:]:
        if "=" not in part:
            continue
        key, value = part.split("=", 1)
        result[key.strip()] = value.strip().rstrip(";")
    return result


def _clean_frontier_token(value: str) -> str:
    raw = str(value or "").strip()
    if raw.startswith("$") and raw.endswith("_Name;"):
        raw = raw[1:-6]
    elif raw.startswith("$") and raw.endswith("_Name"):
        raw = raw[1:-5]
    return raw.replace("_", " ").strip()


def _receive_text_offer(event: dict) -> dict | None:
    if event.get("event") != "ReceiveText":
        return None

    message = str(event.get("Message") or "")
    if "$Mission_Collect_" not in message or "_MessengerChat" not in message:
        return None

    params = _parse_frontier_message_params(message)
    if not params:
        return None

    try:
        count = int(float(params.get("CommodityQuantity") or 0))
    except (TypeError, ValueError):
        count = 0

    try:
        reward = int(float(params.get("reward") or 0))
    except (TypeError, ValueError):
        reward = 0

    return {
        "mission_type": "collect",
        "timestamp": event.get("timestamp") or "",
        "sender": event.get("From_Localised") or event.get("From") or "",
        "message": event.get("Message_Localised") or "",
        "commodity": _clean_frontier_token(params.get("CommodityName") or ""),
        "count": count,
        "reward": reward,
        "destination_station": (
            params.get("destinationStationName")
            or params.get("altDestinationStationName")
            or ""
        ),
        "destination_system": (
            params.get("destinationStationSystemName")
            or params.get("altDestinationStationSystemName")
            or ""
        ),
        "contact": params.get("missionGiverFactionContact") or "",
        "matched": False,
    }


def _event_dt(timestamp: str):
    if not timestamp:
        return None
    try:
        return datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    except ValueError:
        return None


def _matching_pending_offer(
    pending_offers: list[dict],
    mission_item: dict,
    snapshot_timestamp: str,
) -> dict | None:
    internal_name = str(mission_item.get("Name") or "")
    if "Mission_Collect" not in internal_name:
        return None

    snapshot_dt = _event_dt(snapshot_timestamp)
    candidates = []

    for offer in pending_offers:
        if offer.get("matched"):
            continue
        if offer.get("mission_type") != "collect":
            continue

        offer_dt = _event_dt(offer.get("timestamp") or "")
        if snapshot_dt is not None and offer_dt is not None:
            age = snapshot_dt - offer_dt
            if age < timedelta(0) or age > timedelta(hours=24):
                continue

        candidates.append(offer)

    # Nur bei eindeutiger Zuordnung automatisch verknüpfen.
    if len(candidates) != 1:
        return None

    return candidates[0]


def _enrich_mission_from_offer(mission: dict, offer: dict):
    commodity = offer.get("commodity") or ""
    count = int(offer.get("count") or 0)

    if commodity:
        mission["commodity"] = commodity
    if count:
        mission["count"] = count
    if offer.get("destination_system"):
        mission["destination_system"] = offer["destination_system"]
    if offer.get("destination_station"):
        mission["destination_station"] = offer["destination_station"]
    if offer.get("reward"):
        mission["reward"] = int(offer["reward"])

    if commodity and count:
        mission["name"] = f"{count} Einheiten besorgen und liefern: {commodity}"
    elif commodity:
        mission["name"] = f"Beschaffungsmission: {commodity}"
    else:
        mission["name"] = "Beschaffungsmission"

    extra = dict(mission.get("extra") or {})
    extra.update({
        "source": "ReceiveText+Missions",
        "offer_sender": offer.get("sender") or "",
        "offer_message": offer.get("message") or "",
        "offer_contact": offer.get("contact") or "",
        "offer_reward": int(offer.get("reward") or 0),
        "offer_timestamp": offer.get("timestamp") or "",
    })
    mission["extra"] = extra
    mission["next_step"] = default_next_step(mission)
    mission["summary"] = build_summary(mission)


def _new_mission(e: dict) -> dict:
    name = (
        e.get("LocalisedName")
        or e.get("Name_Localised")
        or e.get("Name")
        or "Mission"
    )

    internal = e.get("Name") or ""

    destination_station = (
        e.get("DestinationStation")
        or e.get("DestinationSettlement")
        or ""
    )

    destination_body = (
        e.get("DestinationBody")
        or e.get("BodyName")
        or ""
    )

    raw = {
        "mission_id": e.get("MissionID"),
        "name": name,
        "internal_name": internal,
        "mission_type": mission_kind(internal + " " + str(name)),
        "faction": e.get("Faction") or "",
        "destination_system": (
            e.get("DestinationSystem")
            or e.get("TargetSystem")
            or ""
        ),
        "destination_station": destination_station,
        "destination_body": destination_body,
        "target": (
            e.get("Target_Localised")
            or e.get("Target")
            or ""
        ),
        "commodity": (
            e.get("Commodity_Localised")
            or e.get("Commodity")
            or ""
        ),
        "count": e.get("Count") or 0,
        "reward": e.get("Reward") or 0,
        "expiry": e.get("Expiry") or "",
        "status": STATUS_ACCEPTED,
        "next_step": "",
        "summary": "",
        "progress_text": "",
        "accepted_at": e.get("timestamp") or "",
        "last_update": e.get("timestamp") or "",
        "extra": {},
    }

    raw["next_step"] = default_next_step(raw)
    raw["summary"] = build_summary(raw)
    return raw


def _mission_name_matches_data(mission: dict) -> bool:
    text = (
        (mission.get("internal_name") or "")
        + " "
        + (mission.get("name") or "")
    )
    return mission_kind(text) == "data"


def _mission_name_matches_delivery(mission: dict) -> bool:
    text = (
        (mission.get("internal_name") or "")
        + " "
        + (mission.get("name") or "")
    )
    return mission_kind(text) == "delivery"


def _update_location_status(
    missions: dict[int, dict],
    current_system: str,
    current_station: str,
    current_body: str,
    timestamp: str,
):
    for mission in missions.values():
        dest_system = mission.get("destination_system") or ""
        dest_station = mission.get("destination_station") or ""
        dest_body = mission.get("destination_body") or ""

        if not dest_system or dest_system != current_system:
            continue

        at_specific_place = False

        if dest_station and current_station and dest_station == current_station:
            at_specific_place = True

        if dest_body and current_body and dest_body == current_body:
            at_specific_place = True

        if at_specific_place:
            mission["status"] = STATUS_AT_DESTINATION
            if _mission_name_matches_delivery(mission):
                mission["next_step"] = "Missionsterminal öffnen / Lieferung abgeben"
            elif _mission_name_matches_data(mission):
                mission["next_step"] = "Missionsziel ausführen / Daten beschaffen"
            else:
                mission["next_step"] = "Missionsziel ausführen"
        else:
            if mission.get("status") in (STATUS_ACCEPTED, STATUS_EN_ROUTE):
                mission["status"] = STATUS_IN_TARGET_SYSTEM
                mission["next_step"] = (
                    f"Zum Zielort {dest_station} weiterfliegen"
                    if dest_station
                    else "Missionsziel aufsuchen"
                )

        mission["last_update"] = timestamp or mission.get("last_update", "")


def _update_mission_event(mission: dict, e: dict):
    et = e.get("event")
    ts = e.get("timestamp") or mission.get("last_update", "")

    if et == "MissionRedirected":
        redirected_name = (
            e.get("LocalisedName")
            or e.get("Name_Localised")
            or ""
        )
        if redirected_name:
            mission["name"] = redirected_name

        if e.get("NewDestinationSystem"):
            mission["destination_system"] = e["NewDestinationSystem"]
        if e.get("NewDestinationStation"):
            mission["destination_station"] = e["NewDestinationStation"]

        extra = dict(mission.get("extra") or {})
        extra["source"] = extra.get("source") or "Missions+MissionRedirected"
        if e.get("OldDestinationSystem"):
            extra["old_destination_system"] = e["OldDestinationSystem"]
        mission["extra"] = extra

        mission["status"] = STATUS_REDIRECTED
        mission["next_step"] = default_next_step(mission)
        mission["summary"] = build_summary(mission)

    elif et == "CargoDepot":
        update_type = (e.get("UpdateType") or "").lower()
        collected = e.get("ItemsCollected")
        delivered = e.get("ItemsDelivered")
        total = e.get("TotalItemsToDeliver")

        cargo_name = (
            e.get("CargoType_Localised")
            or e.get("CargoType")
            or ""
        )
        if cargo_name and not mission.get("commodity"):
            mission["commodity"] = cargo_name

        if total is not None and not mission.get("count"):
            try:
                mission["count"] = int(total)
            except (TypeError, ValueError):
                pass

        if (
            mission.get("commodity")
            and mission.get("count")
            and str(mission.get("name") or "").startswith("Mission_")
        ):
            mission["name"] = (
                f"{mission['count']} Einheiten besorgen "
                f"und liefern: {mission['commodity']}"
            )
            mission["summary"] = build_summary(mission)

        if update_type == "collect":
            mission["status"] = STATUS_CARGO_COLLECTED
            if collected is not None and total is not None:
                mission["progress_text"] = f"{collected}/{total} aufgenommen"
            mission["next_step"] = default_next_step(mission)

        elif update_type == "deliver":
            mission["status"] = STATUS_DELIVERING
            if delivered is not None and total is not None:
                mission["progress_text"] = f"{delivered}/{total} geliefert"

            if (
                delivered is not None
                and total is not None
                and delivered >= total
            ):
                mission["status"] = STATUS_COMPLETED
                mission["next_step"] = "Zurück zum Missionsterminal"
            else:
                mission["next_step"] = "Weitere Missionsware abgeben"

    mission["last_update"] = ts


def read_latest_state(
    folder: Path,
    mission_reset_at: str = "",
    indexed_sessions: list[dict] | None = None,
    force_full_history: bool = False,
) -> dict:
    """
    Liest Journale chronologisch ein.

    System-/Body-Daten werden über SystemAddress + BodyID zusammengeführt.
    Dadurch sind Scan und SAASignalsFound nicht mehr von der Event-Reihenfolge
    oder vom gerade gesetzten current_system abhängig.
    """
    ship_loadout = ShipLoadoutData()

    def merge_materials(previous, current):
        """Merge body-wide Scan.Materials without losing older entries."""
        if not current:
            return previous or {}
        if not previous:
            return current
        if isinstance(previous, dict) and isinstance(current, dict):
            return {**previous, **current}
        if isinstance(previous, list) and isinstance(current, list):
            merged = {}
            order = []
            for item in previous + current:
                if not isinstance(item, dict):
                    continue
                name = item.get("Name") or item.get("Name_Localised") or item.get("name")
                key = str(name or "").strip().casefold()
                if not key:
                    continue
                if key not in merged:
                    order.append(key)
                merged[key] = item
            return [merged[key] for key in order]
        return current

    result = {
        "commander": "",
        "commander_fid": "",
        "commander_identity_name": "",
        "commander_identity_timestamp": "",
        "latest_journal_session": None,
        "system": "",
        "system_address": None,
        "last_system_event": None,
        "last_event": None,
        "star_pos": None,
        "body": "",
        "station": "",
        "ship": "",
        "ship_loadout": ship_loadout,
        "fleet_ships": [],
        "last_timestamp": "",
        "missions": [],
        "mission_terminal_updates": [],
        "missions_snapshot_seen": False,
        "last_position": None,
        "owned_carrier": None,
        "wealth": None,
        "journal_files": 0,
        "system_bodies": [],
        "system_body_count": 0,
        "system_signals_count": 0,
        "system_all_bodies_found": False,
        "fss_discovery_scan_seen": False,
        "all_bodies_found_at": None,
        "unsold_cartography_value": 0,
        "unsold_cartography_count": 0,
        "unsold_biology": [],
        "unsold_cartography": [],
    }
    reset_dt = None
    if mission_reset_at:
        try:
            reset_dt = datetime.fromisoformat(
                mission_reset_at.replace("Z", "+00:00")
            )
        except ValueError:
            reset_dt = None

    def _after_mission_reset(timestamp: str) -> bool:
        if reset_dt is None:
            return True

        if not timestamp:
            return False

        try:
            event_dt = datetime.fromisoformat(
                timestamp.replace("Z", "+00:00")
            )
        except ValueError:
            return False

        return event_dt >= reset_dt

    files = (
        [Path(item["journal_file"]) for item in indexed_sessions]
        if indexed_sessions is not None else journal_files(folder)
    )
    result["journal_files"] = len(files)

    if not files:
        return result

    # Jede Datei beginnt ohne geerbte Identität. Persönliche Runtime-Daten
    # dürfen später ausschließlich aus eindeutig dem aktiven FID zugeordneten
    # Sitzungen aufgebaut werden.
    classified_sessions = {}
    if indexed_sessions is not None:
        classified_sessions = {
            str(item["journal_file"]): item for item in indexed_sessions
        }
    else:
        for journal in files:
            try:
                session = classify_journal_file(journal)
            except OSError as exc:
                if journal == files[-1]:
                    raise JournalReadError(journal, exc) from exc
                continue
            classified_sessions[str(journal)] = session

    latest_session = classified_sessions.get(str(files[-1]))
    result["latest_journal_session"] = latest_session

    active_identity = None
    for journal in reversed(files):
        session = classified_sessions.get(str(journal))
        if session is None:
            continue
        if session["attribution_status"] == "identified":
            active_identity = session
            break

    if active_identity is not None:
        result["commander_fid"] = active_identity["fid_seen"] or ""
        result["commander_identity_name"] = (
            active_identity["commander_name_seen"] or ""
        )
        result["commander_identity_timestamp"] = (
            active_identity["last_event_at"] or ""
        )

    missions: dict[int, dict] = {}
    known_missions: dict[int, dict] = {}
    mission_terminal_updates: dict[int, dict] = {}
    missions_snapshot_seen = False
    pending_mission_offers: list[dict] = []
    owned_carrier = None
    fleet_ships: dict[int, dict] = {}
    away_from_own_ship = False

    def _remember_ship(timestamp="", location=None):
        ship_id = getattr(ship_loadout, "ship_id", None)
        if ship_id is None:
            return
        ship_id = int(ship_id)
        previous = fleet_ships.get(ship_id) or {}
        fleet_ships[ship_id] = {
            "loadout": copy.deepcopy(ship_loadout),
            "first_seen": previous.get("first_seen") or str(timestamp or ""),
            "last_seen": str(timestamp or previous.get("last_seen") or ""),
            "location": copy.deepcopy(location) if location else previous.get("location"),
            "is_current": True,
        }
        for other_id, item in fleet_ships.items():
            if other_id != ship_id:
                item["is_current"] = False

    current_system = ""
    current_system_address = None
    current_station = ""
    current_body = ""

    def _known_ship_location(timestamp):
        if not current_system and current_system_address is None:
            return None
        return {
            "system_name": current_system,
            "system_address": current_system_address,
            "station_name": current_station,
            "body_name": current_body,
            "event_timestamp": str(timestamp or ""),
            "event_type": "ShipState",
        }

    def _set_last_position(event, event_type, station_name="", body_name=""):
        result["last_position"] = {
            "system_name": str(event.get("StarSystem") or current_system or ""),
            "system_address": (
                event.get("SystemAddress")
                if isinstance(event.get("SystemAddress"), int)
                else current_system_address
            ),
            "station_name": str(station_name or ""),
            "body_name": str(body_name or ""),
            "event_timestamp": str(event.get("timestamp") or ""),
            "event_type": str(event_type or ""),
        }

    # SystemAddress -> {BodyID -> body}
    scans_by_address: dict[int, dict[int, dict]] = {}

    # Körper, auf denen wir tatsächlich ausgestiegen sind. Zusammen mit
    # WasFootfalled == False aus dem vorherigen Scan lässt sich damit eine
    # eigene Erstbetretung sicher erkennen.
    first_footfall_disembarks: set[tuple[int, int]] = set()

    # SystemAddress -> {BodyID -> bio_count}
    pending_bio_by_address: dict[int, dict[int, int]] = {}

    # Vom DSS/FSS bereits gemeldete BIO-Gattungen (Genuses).
    # Diese stehen oft schon fest, bevor eine Probe mit ScanOrganic
    # genommen wurde.
    pending_bio_genuses_by_address: dict[int, dict[int, list[str]]] = {}

    # SystemAddress -> BodyID -> eindeutige biologische Funde
    biology_by_address: dict[int, dict[int, dict[tuple, dict]]] = {}

    # SystemAddress -> {BodyName -> bio_count}
    # Fallback nur innerhalb desselben Systems.
    pending_bio_name_by_address: dict[int, dict[str, int]] = {}

    # GEO analog zu BIO
    pending_geo_by_address: dict[int, dict[int, int]] = {}
    pending_geo_name_by_address: dict[int, dict[str, int]] = {}
    pending_planetary_mining_by_address: dict[int, dict[int, int]] = {}

    # SystemAddress -> BodyCount
    body_count_by_address: dict[int, int] = {}

    # SystemAddressen, bei denen FSSAllBodiesFound auftrat
    all_found_addresses: set[int] = set()
    all_found_at_by_address: dict[int, str] = {}
    fss_scanned_addresses: set[int] = set()

    # Signale deduplizieren statt blind mitzuzählen:
    # SystemAddress -> set(signature)
    signal_signatures: dict[int, set[tuple]] = {}

    # Noch nicht verkaufte Explorer-Daten seit dem letzten jeweiligen Verkauf.
    unsold_cartography: dict[tuple[int, int], dict] = {}
    unsold_biology: dict[tuple[int, int, str, str, str], dict] = {}

    def _system_address(event: dict):
        value = event.get("SystemAddress")
        if isinstance(value, int):
            return value
        return current_system_address

    def _sold_system_names(event: dict) -> set[str]:
        return sold_system_names(event)

    def _sold_bio_names(event: dict) -> set[str]:
        return sold_bio_names(event)

    def _bio_count_from_event(event: dict) -> int:
        bio_count = 0

        for signal in (event.get("Signals") or []):
            signal_type = str(signal.get("Type") or "").lower()
            signal_type_localised = str(signal.get("Type_Localised") or "").lower()
            signal_text = f"{signal_type} {signal_type_localised}"

            # Primär Frontiers internen Token auswerten; lokalisierter Text
            # bleibt nur als Fallback. So funktioniert die Erkennung unabhängig
            # von der in Elite Dangerous eingestellten Sprache.
            if (
                "saa_signaltype_biological" in signal_text
                or "biological" in signal_text
                or "biologisch" in signal_text
                or "biology" in signal_text
            ):
                try:
                    bio_count += int(signal.get("Count") or 0)
                except Exception:
                    pass

        # Falls Signals aus irgendeinem Grund keine brauchbare Lokalisierung
        # haben, sind vorhandene Genuses ebenfalls ein sicherer Bio-Hinweis.
        if bio_count == 0:
            genuses = event.get("Genuses") or []
            if genuses:
                bio_count = len(genuses)

        return bio_count

    def _bio_genuses_from_event(event: dict) -> list[str]:
        result = []

        for genus in event.get("Genuses") or []:
            if not isinstance(genus, dict):
                continue

            name = (
                genus.get("Genus_Localised")
                or genus.get("Genus")
                or genus.get("Name_Localised")
                or genus.get("Name")
                or ""
            )

            name = str(name or "").strip()
            if name and name not in result:
                result.append(name)

        return result

    def _geo_count_from_event(event: dict) -> int:
        geo_count = 0

        for signal in (event.get("Signals") or []):
            signal_type = str(signal.get("Type") or "").lower()
            signal_type_localised = str(signal.get("Type_Localised") or "").lower()
            signal_text = f"{signal_type} {signal_type_localised}"

            if (
                "saa_signaltype_geological" in signal_text
                or "geological" in signal_text
                or "geologisch" in signal_text
                or "geology" in signal_text
            ):
                try:
                    geo_count += int(signal.get("Count") or 0)
                except Exception:
                    pass

        return geo_count

    def _planetary_mining_count_from_event(event: dict) -> int | None:
        for signal in event.get("Signals") or []:
            if not isinstance(signal, dict):
                continue
            if str(signal.get("Type") or "").casefold() != (
                "$PlanetaryMiningLocation_Name;".casefold()
            ):
                continue
            try:
                return int(signal["Count"])
            except (KeyError, TypeError, ValueError):
                return None
        return None

    def _apply_pending_geo(address: int | None, body: dict):
        if address is None:
            return

        body_name = body.get("name") or ""

        if "belt cluster" in body_name.lower():
            body["geological_signals"] = 0
            return

        geo_count = int(body.get("geological_signals") or 0)

        body_id = body.get("body_id")
        if body_id is not None:
            geo_count = max(
                geo_count,
                int(
                    pending_geo_by_address
                    .get(address, {})
                    .get(body_id, 0)
                )
            )

        if body_name:
            geo_count = max(
                geo_count,
                int(
                    pending_geo_name_by_address
                    .get(address, {})
                    .get(body_name, 0)
                )
            )

        body["geological_signals"] = geo_count

    def _apply_pending_bio(address: int | None, body: dict):
        # Ohne eindeutige SystemAddress keine BIO-Zuordnung.
        if address is None:
            return

        # Belt Cluster können keine Exobiologie tragen.
        body_name = body.get("name") or ""
        if "belt cluster" in body_name.lower():
            body["biological_signals"] = 0
            return

        bio_count = int(body.get("biological_signals") or 0)

        body_id = body.get("body_id")
        if body_id is not None:
            bio_count = max(
                bio_count,
                int(
                    pending_bio_by_address
                    .get(address, {})
                    .get(body_id, 0)
                )
            )

        if body_name:
            bio_count = max(
                bio_count,
                int(
                    pending_bio_name_by_address
                    .get(address, {})
                    .get(body_name, 0)
                )
            )

        body["biological_signals"] = bio_count

        body_id = body.get("body_id")
        if body_id is not None:
            body["bio_genuses"] = list(
                pending_bio_genuses_by_address
                .get(address, {})
                .get(int(body_id), [])
            )


    current_journal = files[-1]

    runtime_files = (
        files if indexed_sessions is None or force_full_history else files[-1:]
    )
    for journal in runtime_files:
        session = classified_sessions.get(str(journal))
        input_lines = None
        if indexed_sessions is not None and session is not None:
            try:
                input_lines, safe_offset = _live_complete_lines(journal)
            except OSError as exc:
                raise JournalReadError(journal, exc) from exc
            session["last_complete_line_offset"] = safe_offset
            identities = {}
            for raw_line in input_lines:
                try:
                    identity_event = json.loads(raw_line)
                except json.JSONDecodeError:
                    continue
                event_type = identity_event.get("event")
                if event_type not in ("Commander", "LoadGame"):
                    continue
                fid = str(identity_event.get("FID") or "").strip()
                if not fid:
                    continue
                field = "Name" if event_type == "Commander" else "Commander"
                identities[fid] = str(identity_event.get(field) or "").strip()
            if len(identities) == 1:
                fid = next(iter(identities))
                session.update(attribution_status="identified", fid_seen=fid,
                               commander_name_seen=identities[fid] or None)
                active_identity = session
                result["commander_fid"] = fid
                result["commander_identity_name"] = identities[fid]
            elif len(identities) > 1:
                session.update(attribution_status="ambiguous", fid_seen=None,
                               commander_name_seen=None)
        if (
            active_identity is None
            or session is None
            or session.get("attribution_status") != "identified"
            or session.get("fid_seen") != active_identity.get("fid_seen")
        ):
            # Unknown/ambiguous und Sitzungen anderer Commander liefern keine
            # persönlichen Runtime-Daten. Globale Archivdaten bleiben Aufgabe
            # des separaten Datenbankimports und werden hier nicht benötigt.
            continue

        try:
            if indexed_sessions is not None:
                handle = input_lines
            else:
                handle = journal.open(
                    "r", encoding="utf-8", errors="replace"
                )
        except OSError as exc:
            if journal == current_journal:
                raise JournalReadError(journal, exc) from exc
            continue

        from contextlib import nullcontext
        with (nullcontext(handle) if isinstance(handle, list) else handle):
            for line in handle:
                try:
                    e = json.loads(line)
                except json.JSONDecodeError:
                    continue

                ts = e.get("timestamp") or ""
                if ts:
                    result["last_timestamp"] = ts

                et = e.get("event")
                result["last_event"] = str(et or "")

                # ---------------------------------------------------------
                # Basisstatus
                # ---------------------------------------------------------
                if et == "Commander":
                    result["commander"] = (
                        e.get("Name")
                        or result["commander"]
                    )

                elif et == "LoadGame":
                    result["commander"] = (
                        e.get("Commander")
                        or result["commander"]
                    )
                    if isinstance(e.get("Credits"), int) and e.get("Credits") >= 0:
                        result["wealth"] = {
                            "credits": int(e["Credits"]),
                            "event_timestamp": ts,
                            "source_event": "LoadGame",
                        }

                    if is_definite_non_ship(e.get("Ship"), e.get("Ship_Localised")):
                        away_from_own_ship = True
                    else:
                        away_from_own_ship = False
                        result["ship"] = (
                            e.get("ShipName") or e.get("Ship_Localised")
                            or e.get("Ship") or result["ship"]
                        )
                        event_ship_id = _optional_int(e.get("ShipID"))
                        if (
                            ship_loadout.ship_id is not None
                            and event_ship_id is not None
                            and ship_loadout.ship_id != event_ship_id
                        ):
                            ship_loadout = ShipLoadoutData(
                                ship_id=event_ship_id, loadout_stale=True,
                            )
                        ship_loadout.ship_id = event_ship_id or ship_loadout.ship_id
                        ship_loadout.ship_type = str(e.get("Ship") or "").strip() or ship_loadout.ship_type
                        ship_loadout.ship_name = str(e.get("ShipName") or "").strip() or ship_loadout.ship_name
                        ship_loadout.ship_ident = str(e.get("ShipIdent") or "").strip() or ship_loadout.ship_ident
                        fuel_capacity = e.get("FuelCapacity")
                        if isinstance(fuel_capacity, dict):
                            fuel_capacity = fuel_capacity.get("Main")
                        parsed_capacity = _optional_float(fuel_capacity)
                        if parsed_capacity is not None:
                            ship_loadout.main_tank_capacity = parsed_capacity
                        parsed_fuel = _optional_float(e.get("FuelLevel"))
                        if parsed_fuel is not None:
                            ship_loadout.main_fuel = parsed_fuel
                        _remember_ship(ts, _known_ship_location(ts))

                elif et == "Loadout":
                    result["ship"] = (
                        e.get("ShipName")
                        or e.get("Ship")
                        or result["ship"]
                    )
                    ship_loadout = _loadout_from_event(e, ship_loadout)
                    away_from_own_ship = False
                    _remember_ship(ts, _known_ship_location(ts))

                elif et in ("ShipyardSwap", "ShipyardBuy"):
                    ship_loadout = ShipLoadoutData(
                        ship_id=_optional_int(e.get("ShipID")),
                        ship_type=(
                            str(e.get("ShipType") or "").strip() or None
                        ),
                        loadout_complete=False,
                        loadout_stale=True,
                    )
                    away_from_own_ship = False
                    result["ship"] = (
                        str(e.get("ShipType_Localised") or e.get("ShipType") or "").strip()
                        or result["ship"]
                    )
                    _remember_ship(ts, _known_ship_location(ts))

                elif et in (
                    "ModuleBuy",
                    "ModuleSell",
                    "ModuleSwap",
                    "ModuleStore",
                    "ModuleRetrieve",
                    "MassModuleStore",
                    "MassModuleRetrieve",
                    "EngineerCraft",
                ):
                    if _matching_ship(ship_loadout, e):
                        ship_loadout.loadout_stale = True
                        _remember_ship(ts)

                elif et == "Cargo":
                    if str(e.get("Vessel") or "").strip().casefold() == "ship":
                        cargo = _optional_int(e.get("Count"))
                        if cargo is not None:
                            ship_loadout.cargo = cargo

                elif et == "FuelScoop":
                    fuel = _optional_float(e.get("Total"))
                    if fuel is not None:
                        ship_loadout.main_fuel = fuel

                elif et == "ReservoirReplenished":
                    main_fuel = _optional_float(e.get("FuelMain"))
                    reserve_fuel = _optional_float(e.get("FuelReservoir"))
                    if main_fuel is not None:
                        ship_loadout.main_fuel = main_fuel
                    if reserve_fuel is not None:
                        ship_loadout.reserve_fuel = reserve_fuel

                # ---------------------------------------------------------
                # System / Location
                # ---------------------------------------------------------
                elif et in ("Location", "FSDJump", "CarrierJump"):
                    result["last_system_event"] = et
                    current_system = (
                        e.get("StarSystem")
                        or current_system
                    )

                    address = e.get("SystemAddress")
                    if isinstance(address, int):
                        current_system_address = address

                    current_body = (
                        e.get("Body")
                        or e.get("BodyName")
                        or current_body
                    )

                    if et == "Location":
                        current_station = (
                            e.get("StationName")
                            or current_station
                        )
                    else:
                        current_station = ""

                    result["system"] = current_system
                    result["system_address"] = current_system_address

                    star_pos = e.get("StarPos")
                    if isinstance(star_pos, (list, tuple)) and len(star_pos) >= 3:
                        result["star_pos"] = [
                            float(star_pos[0]), float(star_pos[1]), float(star_pos[2])
                        ]

                    result["body"] = current_body
                    result["station"] = current_station

                    _set_last_position(
                        e,
                        et,
                        current_station if et == "Location" else "",
                        (e.get("Body") or e.get("BodyName") or ""),
                    )
                    if not away_from_own_ship:
                        _remember_ship(ts, result["last_position"])

                    if et == "CarrierJump" and owned_carrier is not None:
                        event_carrier_id = _optional_int(
                            e.get("CarrierID") if e.get("CarrierID") is not None
                            else e.get("MarketID")
                        )
                        if event_carrier_id == owned_carrier["carrier_id"]:
                            owned_carrier["system_name"] = str(
                                e.get("StarSystem") or owned_carrier["system_name"]
                            )
                            if isinstance(e.get("SystemAddress"), int):
                                owned_carrier["system_address"] = e["SystemAddress"]
                            owned_carrier["last_updated"] = ts

                    if et == "FSDJump":
                        fuel = _optional_float(e.get("FuelLevel"))
                        if fuel is not None:
                            ship_loadout.main_fuel = fuel

                    _update_location_status(
                        missions,
                        current_system,
                        current_station,
                        current_body,
                        ts,
                    )

                elif et == "Docked":
                    current_station = e.get("StationName") or ""
                    current_system = (
                        e.get("StarSystem")
                        or current_system
                    )

                    address = e.get("SystemAddress")
                    if isinstance(address, int):
                        current_system_address = address

                    result["station"] = current_station
                    result["system"] = current_system
                    result["system_address"] = current_system_address

                    _set_last_position(e, et, current_station, "")
                    if not away_from_own_ship:
                        _remember_ship(ts, result["last_position"])

                    _update_location_status(
                        missions,
                        current_system,
                        current_station,
                        current_body,
                        ts,
                    )

                elif et == "Undocked":
                    current_station = ""
                    result["station"] = ""

                elif et in ("ApproachBody", "Touchdown"):
                    current_body = (
                        e.get("Body")
                        or e.get("BodyName")
                        or current_body
                    )

                    result["body"] = current_body

                    _update_location_status(
                        missions,
                        current_system,
                        current_station,
                        current_body,
                        ts,
                    )

                elif et == "Disembark":
                    away_from_own_ship = True
                    current_body = (
                        e.get("Body")
                        or e.get("BodyName")
                        or current_body
                    )
                    result["body"] = current_body

                    address = _system_address(e)
                    body_id = e.get("BodyID")

                    if (
                        bool(e.get("OnPlanet"))
                        and address is not None
                        and body_id is not None
                    ):
                        try:
                            body_id_int = int(body_id)
                        except (TypeError, ValueError):
                            body_id_int = None

                        if body_id_int is not None:
                            first_footfall_disembarks.add((int(address), body_id_int))

                            body = scans_by_address.setdefault(
                                int(address),
                                {},
                            ).get(body_id_int)

                            # Entscheidend ist Frontiers Zustand VOR unserer
                            # Landung: WasFootfalled=False + eigenes Aussteigen
                            # auf diesem Körper = eigene Erstbetretung.
                            if body and body.get("was_footfalled") is False:
                                body["first_footfall"] = True
                                body["first_footfall_at"] = ts

                    _update_location_status(
                        missions,
                        current_system,
                        current_station,
                        current_body,
                        ts,
                    )

                elif et == "Embark":
                    away_from_own_ship = bool(
                        e.get("SRV") or e.get("Taxi") or e.get("Multicrew")
                    )

                elif et == "LaunchSRV":
                    if e.get("PlayerControlled") is not False:
                        away_from_own_ship = True

                elif et == "DockSRV":
                    away_from_own_ship = False

                elif et == "LaunchFighter":
                    if bool(e.get("PlayerControlled")):
                        away_from_own_ship = True

                elif et == "DockFighter":
                    away_from_own_ship = False

                elif et == "ApproachSettlement":
                    current_station = (
                        e.get("Name")
                        or current_station
                    )

                    current_body = (
                        e.get("BodyName")
                        or current_body
                    )

                    result["station"] = current_station
                    result["body"] = current_body

                    _update_location_status(
                        missions,
                        current_system,
                        current_station,
                        current_body,
                        ts,
                    )

                # ---------------------------------------------------------
                # FSS Systemdaten
                # ---------------------------------------------------------
                elif et == "FSSDiscoveryScan":
                    address = _system_address(e)

                    if address is not None:
                        fss_scanned_addresses.add(address)
                        if isinstance(e.get("BodyCount"), int):
                            body_count_by_address[address] = e["BodyCount"]

                elif et == "FSSAllBodiesFound":
                    address = _system_address(e)

                    if address is not None:
                        all_found_addresses.add(address)
                        all_found_at_by_address[address] = ts

                        if isinstance(e.get("Count"), int):
                            body_count_by_address[address] = e["Count"]

                elif et == "FSSSignalDiscovered":
                    address = _system_address(e)

                    if address is not None:
                        signature = (
                            e.get("SignalName"),
                            e.get("SignalName_Localised"),
                            e.get("SignalType"),
                            e.get("IsStation"),
                        )

                        signal_signatures.setdefault(
                            address,
                            set()
                        ).add(signature)

                # ---------------------------------------------------------
                # Body Scan
                # ---------------------------------------------------------
                elif et == "Scan":
                    address = _system_address(e)
                    body_id = e.get("BodyID")

                    if (
                        address is not None
                        and body_id is not None
                    ):
                        try:
                            body_id_int = int(body_id)
                        except Exception:
                            continue

                        parents = e.get("Parents") or []
                        parent_id = _direct_parent_id(parents)
                        parent_star_id = _parent_star_id(parents)

                        raw_gravity = e.get("SurfaceGravity")
                        gravity_g = None

                        if isinstance(raw_gravity, (int, float)):
                            gravity_g = float(raw_gravity) / 9.80665

                        body_name = e.get("BodyName") or ""
                        short_name = body_name

                        if (
                            current_system
                            and body_name.startswith(current_system)
                        ):
                            short_name = (
                                body_name[len(current_system):].strip()
                                or body_name
                            )

                        body = {
                            "body_id": body_id_int,
                            "name": body_name,
                            "short_name": short_name,
                            "body_type": (
                                "Star"
                                if e.get("StarType")
                                else "Planet"
                            ),
                            "star_type": e.get("StarType") or "",
                            "planet_class": e.get("PlanetClass") or "",
                            "mass_em": e.get("MassEM"),
                            "stellar_mass": e.get("StellarMass"),
                            # Frontier-Journal liefert Radius in Metern.
                            "radius_m": e.get("Radius"),
                            "parent_id": parent_id,
                            "parent_star_id": parent_star_id,
                            "surface_temperature": e.get("SurfaceTemperature"),
                            "surface_pressure": e.get("SurfacePressure"),
                            "atmosphere_composition": _atmosphere_composition(
                                e.get("AtmosphereComposition")
                            ),
                            "gravity_g": gravity_g,
                            "distance_ls": e.get("DistanceFromArrivalLS"),
                            "landable": bool(e.get("Landable", False)),
                            "terraformable": (
                                e.get("TerraformState")
                                == "Terraformable"
                            ),
                            "was_discovered": e.get("WasDiscovered"),
                            "was_mapped": e.get("WasMapped"),
                            "was_footfalled": e.get("WasFootfalled"),
                            "first_footfall": bool(
                                (int(address), body_id_int) in first_footfall_disembarks
                                and e.get("WasFootfalled") is False
                            ),
                            "first_footfall_at": (
                                ts
                                if (int(address), body_id_int) in first_footfall_disembarks
                                and e.get("WasFootfalled") is False
                                else None
                            ),
                            "atmosphere": (
                                e.get("Atmosphere_Localised")
                                or e.get("Atmosphere")
                                or ""
                            ),
                            "volcanism": (
                                e.get("Volcanism_Localised")
                                or e.get("Volcanism")
                                or ""
                            ),
                            "materials": (
                                e.get("Materials")
                                or {}
                            ),
                            "biological_signals": 0,
                            "geological_signals": 0,
                            "planetary_mining_signals": (
                                pending_planetary_mining_by_address
                                .get(address, {})
                                .get(body_id_int)
                            ),
                            "biology": [],
                            "bio_genuses": [],
                            "self_mapped": False,
                            "efficient_mapping": False,
                        }

                        # Frühere Scan-Version desselben Körpers nicht blind
                        # überschreiben, wenn dort Mappingstatus gesetzt war.
                        previous = scans_by_address.setdefault(
                            address,
                            {}
                        ).get(body_id_int)

                        if previous:
                            for field in (
                                "parent_id", "parent_star_id", "radius_m",
                                "surface_temperature", "surface_pressure",
                                "atmosphere_composition",
                            ):
                                if body.get(field) in (None, ""):
                                    body[field] = previous.get(field)
                            body["self_mapped"] = bool(
                                previous.get("self_mapped")
                            )
                            body["efficient_mapping"] = bool(
                                previous.get("efficient_mapping")
                            )
                            body["first_footfall"] = bool(
                                body.get("first_footfall")
                                or previous.get("first_footfall")
                            )
                            body["first_footfall_at"] = (
                                body.get("first_footfall_at")
                                or previous.get("first_footfall_at")
                            )
                            if body.get("was_footfalled") is None:
                                body["was_footfalled"] = previous.get("was_footfalled")
                            body["biological_signals"] = int(
                                previous.get("biological_signals") or 0
                            )
                            body["geological_signals"] = int(
                                previous.get("geological_signals") or 0
                            )
                            if body.get("planetary_mining_signals") is None:
                                body["planetary_mining_signals"] = previous.get(
                                    "planetary_mining_signals"
                                )
                            # Scan-Folgeevents koennen Materials auslassen oder nur
                            # einen Teil liefern. Bereits bekannte bodyweite Werte
                            # duerfen dadurch im Live-Zustand nicht verschwinden.
                            body["materials"] = merge_materials(
                                previous.get("materials"), body.get("materials")
                            )
                            body["bio_genuses"] = list(
                                previous.get("bio_genuses") or []
                            )

                        _apply_pending_bio(address, body)
                        _apply_pending_geo(address, body)
                        apply_values(body)

                        scans_by_address[address][body_id_int] = body

                        # NavBeaconDetail gibt bekannte Körperdaten nach einem
                        # Nav-Beacon-Scan erneut aus. Das ist kein Beleg für neu
                        # entstandene, bei Universal Cartographics verkaufbare
                        # Daten.
                        if not (
                            body.get("star_type")
                            or "belt cluster" in body_name.lower()
                            or str(e.get("ScanType") or "") == "NavBeaconDetail"
                        ):
                            unsold_cartography[(address, body_id_int)] = {
                                "system_address": int(address), "body_id": body_id_int,
                                "system_name": current_system,
                                "body_name": body_name, "scanned_at": ts,
                                "mapped_at": "", "self_mapped": False,
                                "planet_class": body.get("planet_class") or "",
                                "terraformable": bool(body.get("terraformable")),
                                "estimated_value": int(body.get("current_value") or 0),
                            }

                # ---------------------------------------------------------
                # DSS Mapping
                # ---------------------------------------------------------
                elif et == "SAAScanComplete":
                    address = _system_address(e)
                    body_id = e.get("BodyID")

                    if (
                        address is not None
                        and body_id is not None
                    ):
                        try:
                            body_id_int = int(body_id)
                        except Exception:
                            continue

                        body = scans_by_address.setdefault(
                            address,
                            {}
                        ).get(body_id_int)

                        if body:
                            body["self_mapped"] = True
                            body["mapped_at"] = ts

                            probes_used = e.get("ProbesUsed")
                            efficiency_target = e.get("EfficiencyTarget")

                            if (
                                isinstance(probes_used, int)
                                and isinstance(efficiency_target, int)
                            ):
                                body["efficient_mapping"] = (
                                    probes_used <= efficiency_target
                                )
                                body["probes_used"] = probes_used
                                body["efficiency_target"] = efficiency_target

                            apply_values(body)

                            ledger_key = (address, body_id_int)
                            mapped_value = int(body.get("current_value") or 0)
                            if ledger_key in unsold_cartography:
                                unsold_cartography[ledger_key].update({
                                    "estimated_value": mapped_value,
                                    "mapped_at": ts, "self_mapped": True,
                                })
                            else:
                                # Scan bereits verkauft, DSS erst danach: nur Mehrwert offen.
                                scan_value = int(body.get("scan_value") or 0)
                                unsold_cartography[ledger_key] = {
                                    "system_address": int(address), "body_id": body_id_int,
                                    "system_name": current_system,
                                    "body_name": body.get("name") or "", "scanned_at": "",
                                    "mapped_at": ts, "self_mapped": True,
                                    "planet_class": body.get("planet_class") or "",
                                    "terraformable": bool(body.get("terraformable")),
                                    "estimated_value": max(0, mapped_value - scan_value),
                                }

                # ---------------------------------------------------------
                # BIO / GEO Signals
                # ---------------------------------------------------------
                elif et in ("SAASignalsFound", "FSSBodySignals"):
                    address = _system_address(e)
                    body_id = e.get("BodyID")

                    if (
                        address is not None
                        and body_id is not None
                    ):
                        try:
                            body_id_int = int(body_id)
                        except Exception:
                            continue

                        bio_count = _bio_count_from_event(e)
                        geo_count = _geo_count_from_event(e)
                        mining_count = _planetary_mining_count_from_event(e)
                        bio_genuses = _bio_genuses_from_event(e)

                        if bio_genuses:
                            pending_bio_genuses_by_address.setdefault(
                                address,
                                {}
                            )[body_id_int] = list(bio_genuses)

                        pending_bio_by_address.setdefault(
                            address,
                            {}
                        )[body_id_int] = bio_count

                        pending_geo_by_address.setdefault(
                            address,
                            {}
                        )[body_id_int] = geo_count
                        if mining_count is not None:
                            pending_planetary_mining_by_address.setdefault(
                                address, {}
                            )[body_id_int] = mining_count

                        saa_body_name = (
                            e.get("BodyName")
                            or e.get("Body")
                            or ""
                        )

                        if saa_body_name:
                            pending_bio_name_by_address.setdefault(
                                address,
                                {}
                            )[saa_body_name] = max(
                                bio_count,
                                pending_bio_name_by_address
                                .get(address, {})
                                .get(saa_body_name, 0)
                            )

                            pending_geo_name_by_address.setdefault(
                                address,
                                {}
                            )[saa_body_name] = max(
                                geo_count,
                                pending_geo_name_by_address
                                .get(address, {})
                                .get(saa_body_name, 0)
                            )

                        body = scans_by_address.setdefault(
                            address,
                            {}
                        ).get(body_id_int)

                        if body is None and mining_count is not None:
                            body = {
                                "body_id": body_id_int,
                                "name": saa_body_name,
                                "short_name": saa_body_name,
                                "body_type": "",
                                "star_type": "",
                                "planet_class": "",
                                "biological_signals": bio_count,
                                "geological_signals": geo_count,
                                "planetary_mining_signals": mining_count,
                                "biology": [],
                                "bio_genuses": list(bio_genuses),
                                "self_mapped": False,
                                "efficient_mapping": False,
                                "_placeholder": True,
                            }
                            scans_by_address[address][body_id_int] = body

                        if body:
                            body["biological_signals"] = bio_count
                            body["geological_signals"] = geo_count
                            if mining_count is not None:
                                body["planetary_mining_signals"] = mining_count
                            if bio_genuses:
                                body["bio_genuses"] = list(bio_genuses)
                            apply_values(body)

                elif et == "ScanOrganic":
                    address = _system_address(e)
                    body_id = e.get("BodyID")
                    if body_id is None and isinstance(e.get("Body"), int):
                        body_id = e.get("Body")

                    if address is not None and body_id is not None:
                        try:
                            body_id_int = int(body_id)
                        except Exception:
                            body_id_int = None

                        if body_id_int is not None:
                            pending_bio_by_address.setdefault(address, {})[
                                body_id_int
                            ] = max(
                                1,
                                pending_bio_by_address.get(address, {}).get(
                                    body_id_int, 0
                                ),
                            )

                            genus = e.get("Genus_Localised") or e.get("Genus") or ""
                            species = e.get("Species_Localised") or e.get("Species") or ""
                            variant = e.get("Variant_Localised") or e.get("Variant") or ""

                            key = (str(genus), str(species), str(variant))
                            bio_entry = {
                                "system_address": int(address),
                                "body_id": body_id_int,
                                "system_name": current_system,
                                "body_name": (
                                    scans_by_address.get(address, {}).get(body_id_int, {}).get("name")
                                    or e.get("BodyName") or ""
                                ),
                                "genus": genus,
                                "species": species,
                                "variant": variant,
                                "scan_type": e.get("ScanType") or "",
                                "timestamp": ts,
                            }
                            biology_by_address.setdefault(address, {}).setdefault(
                                body_id_int, {}
                            )[key] = bio_entry

                            # Erst der dritte Genetic-Sampler-Scan (Analyse) ist verkaufsfertig.
                            if str(e.get("ScanType") or "").strip().casefold() in ("analyse", "analyze"):
                                unsold_biology[(
                                    int(address), body_id_int, str(genus),
                                    str(species), str(variant)
                                )] = dict(bio_entry)

                            body = scans_by_address.setdefault(address, {}).get(
                                body_id_int
                            )
                            if body and "belt cluster" not in (
                                body.get("name") or ""
                            ).lower():
                                body["biological_signals"] = max(
                                    1, int(body.get("biological_signals") or 0)
                                )
                                body["biology"] = list(
                                    biology_by_address[address][body_id_int].values()
                                )

                # ---------------------------------------------------------
                # Verkauf setzt nur den jeweils passenden offenen Topf zurück.
                # ---------------------------------------------------------
                elif et in ("SellExplorationData", "MultiSellExplorationData"):
                    # Systems/Discovered sind keine vollständige Aufzählung
                    # der verkauften Daten. Das Verkaufsereignis ist deshalb
                    # die autoritative Watermark für den gesamten bis hierhin
                    # rekonstruierten offenen UC-Bestand.
                    unsold_cartography.clear()

                elif et == "SellOrganicData":
                    sold_names = _sold_bio_names(e)
                    if sold_names:
                        for key, entry in list(unsold_biology.items()):
                            candidates = {
                                str(entry.get("species") or "").strip().casefold(),
                                str(entry.get("variant") or "").strip().casefold(),
                            }
                            if candidates & sold_names:
                                unsold_biology.pop(key, None)
                    else:
                        unsold_biology.clear()

                # ---------------------------------------------------------
                # Missionsangebote per NPC-Nachricht
                # ---------------------------------------------------------
                elif et == "ReceiveText":
                    if not _after_mission_reset(ts):
                        continue

                    offer = _receive_text_offer(e)
                    if offer is not None:
                        pending_mission_offers.append(offer)

                # ---------------------------------------------------------
                # Mission Snapshot
                # ---------------------------------------------------------
                elif et == "Missions":
                    if not _after_mission_reset(ts):
                        continue
                    missions_snapshot_seen = True
                    active_ids = {
                        item.get("MissionID")
                        for item in (e.get("Active") or [])
                        if item.get("MissionID") is not None
                    }

                    for old_id in list(missions):
                        if old_id not in active_ids:
                            missions.pop(old_id, None)

                    for item in (e.get("Active") or []):
                        mid = item.get("MissionID")

                        if mid is None or mid in missions:
                            continue

                        raw = {
                            "MissionID": mid,
                            "Name": item.get("Name") or "Mission",
                            "LocalisedName": (
                                item.get("LocalisedName")
                                or item.get("Name_Localised")
                            ),
                            "Expiry": item.get("Expiry") or "",
                            "timestamp": ts,
                        }

                        mission = _new_mission(raw)

                        offer = _matching_pending_offer(
                            pending_mission_offers,
                            item,
                            ts,
                        )
                        if offer is not None:
                            _enrich_mission_from_offer(
                                mission,
                                offer,
                            )
                            offer["matched"] = True

                        missions[mid] = mission
                        known_missions[int(mid)] = mission

                elif et == "MissionAccepted":
                    if not _after_mission_reset(ts):
                        continue
                    mid = e.get("MissionID")

                    if mid is not None:
                        missions[mid] = _new_mission(e)
                        known_missions[int(mid)] = missions[mid]

                elif et == "MissionRedirected":
                    if not _after_mission_reset(ts):
                        continue
                    mid = e.get("MissionID")

                    # Manche im Flug/über NPC-Nachrichten entstehenden Missionen
                    # besitzen keinen MissionAccepted-Eintrag. Falls der aktuelle
                    # Missions-Snapshot noch nicht gelesen wurde (z. B. Logsegment),
                    # legen wir spätestens hier einen vorläufigen Datensatz an.
                    if mid is not None and mid not in missions:
                        missions[mid] = _new_mission({
                            "MissionID": mid,
                            "Name": e.get("Name") or "Mission",
                            "LocalisedName": (
                                e.get("LocalisedName")
                                or e.get("Name_Localised")
                            ),
                            "timestamp": ts,
                        })
                        known_missions[int(mid)] = missions[mid]

                    if mid in missions:
                        _update_mission_event(
                            missions[mid],
                            e
                        )

                elif et == "CargoDepot":
                    if not _after_mission_reset(ts):
                        continue
                    mid = e.get("MissionID")

                    if mid in missions:
                        _update_mission_event(
                            missions[mid],
                            e
                        )

                elif et in ("DataScanned", "DatalinkScan"):
                    if not _after_mission_reset(ts):
                        continue
                    for mission in missions.values():
                        if (
                            _mission_name_matches_data(mission)
                            and mission.get("destination_system")
                            == current_system
                        ):
                            mission["status"] = STATUS_DATA_RECEIVED
                            mission["next_step"] = (
                                "Zurück zum Missionsterminal"
                            )
                            mission["last_update"] = ts

                elif et in (
                    "MissionCompleted",
                    "MissionFailed",
                    "MissionAbandoned",
                ):
                    if not _after_mission_reset(ts):
                        continue
                    mid = e.get("MissionID")
                    if mid is not None:
                        mission = (
                            missions.pop(mid, None)
                            or known_missions.get(int(mid))
                            or _new_mission(e)
                        )
                        terminal_state = {
                            "MissionCompleted": "completed",
                            "MissionFailed": "failed",
                            "MissionAbandoned": "abandoned",
                        }[et]
                        mission["terminal_state"] = terminal_state
                        mission["status"] = {
                            "MissionCompleted": STATUS_COMPLETED,
                            "MissionFailed": STATUS_FAILED,
                            "MissionAbandoned": STATUS_ABANDONED,
                        }[et]
                        mission["last_update"] = ts
                        if e.get("Reward") is not None:
                            mission["reward"] = e.get("Reward") or 0
                        mission_terminal_updates[int(mid)] = mission

                # CarrierStats ist der Eigentumsbeleg. Alle Folgeevents
                # werden nur bei derselben Carrier-/MarketID übernommen.
                elif et == "CarrierStats":
                    carrier_id = _optional_int(e.get("CarrierID"))
                    if carrier_id is not None:
                        owned_carrier = {
                            "carrier_id": carrier_id,
                            "callsign": str(e.get("Callsign") or ""),
                            "carrier_name": str(e.get("Name") or ""),
                            "system_name": str(e.get("StarSystem") or ""),
                            "system_address": (
                                e.get("SystemAddress")
                                if isinstance(e.get("SystemAddress"), int) else None
                            ),
                            "last_updated": ts,
                        }

                elif et in ("CarrierNameChange", "CarrierLocation"):
                    if owned_carrier is None:
                        continue
                    event_carrier_id = _optional_int(
                        e.get("CarrierID") if e.get("CarrierID") is not None
                        else e.get("MarketID")
                    )
                    if event_carrier_id != owned_carrier["carrier_id"]:
                        continue
                    if et == "CarrierNameChange":
                        owned_carrier["callsign"] = str(
                            e.get("Callsign") or owned_carrier["callsign"]
                        )
                        owned_carrier["carrier_name"] = str(
                            e.get("Name") or owned_carrier["carrier_name"]
                        )
                    else:
                        owned_carrier["system_name"] = str(
                            e.get("StarSystem") or owned_carrier["system_name"]
                        )
                        if isinstance(e.get("SystemAddress"), int):
                            owned_carrier["system_address"] = e["SystemAddress"]
                    owned_carrier["last_updated"] = ts

    if active_identity is not None and active_identity.get("commander_name_seen"):
        # Ein Namensevent ohne FID aus einer späteren unknown-Datei darf die
        # eindeutig belegte aktive Identität nicht optisch überschreiben.
        result["commander"] = active_identity["commander_name_seen"]

    result["missions"] = list(missions.values())
    result["mission_terminal_updates"] = list(mission_terminal_updates.values())
    result["missions_snapshot_seen"] = missions_snapshot_seen
    result["owned_carrier"] = owned_carrier
    result["ship_loadout"] = ship_loadout
    result["fleet_ships"] = list(fleet_ships.values())

    # -------------------------------------------------------------
    # Nur Daten des AKTUELLEN SystemAddress anzeigen
    # -------------------------------------------------------------
    address = result.get("system_address")

    if address is not None:
        bodies = list(
            scans_by_address.get(address, {}).values()
        )

        for body in bodies:
            _apply_pending_bio(address, body)
            _apply_pending_geo(address, body)
            body_id = body.get("body_id")
            if body_id is not None:
                mining_count = pending_planetary_mining_by_address.get(
                    address, {}
                ).get(int(body_id))
                if mining_count is not None:
                    body["planetary_mining_signals"] = mining_count

            body_id = body.get("body_id")
            if body_id is not None:
                body["bio_genuses"] = list(
                    pending_bio_genuses_by_address
                    .get(address, {})
                    .get(int(body_id), body.get("bio_genuses") or [])
                )

            body_id = body.get("body_id")
            if body_id is not None:
                body["biology"] = list(
                    biology_by_address.get(address, {})
                    .get(int(body_id), {})
                    .values()
                )

            if "belt cluster" in (
                body.get("name") or ""
            ).lower():
                body["biological_signals"] = 0
                body["geological_signals"] = 0

            apply_values(body)

        bodies.sort(
            key=lambda b: b.get("body_id", 999999)
        )

        result["system_bodies"] = bodies

        result["system_body_count"] = (
            body_count_by_address.get(
                address,
                len(bodies)
            )
        )

        result["system_signals_count"] = len(
            signal_signatures.get(
                address,
                set()
            )
        )

        result["system_all_bodies_found"] = (
            address in all_found_addresses
        )
        result["fss_discovery_scan_seen"] = address in fss_scanned_addresses
        result["all_bodies_found_at"] = all_found_at_by_address.get(address)

    result["unsold_cartography_value"] = int(
        sum(max(0, int(value.get("estimated_value") or 0))
            for value in unsold_cartography.values())
    )
    result["unsold_cartography_count"] = int(
        sum(1 for value in unsold_cartography.values()
            if int(value.get("estimated_value") or 0) > 0)
    )
    result["unsold_biology"] = list(unsold_biology.values())
    result["unsold_cartography"] = list(unsold_cartography.values())

    return result
