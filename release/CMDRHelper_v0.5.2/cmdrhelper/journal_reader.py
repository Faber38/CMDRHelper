from __future__ import annotations

import json
import platform
from datetime import datetime
from pathlib import Path

from cmdrhelper.mission_manager import build_summary, default_next_step, mission_kind
from cmdrhelper.valuation import apply_values


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


def journal_files(folder: Path) -> list[Path]:
    if not folder or not folder.exists():
        return []
    return sorted(folder.glob("Journal.*.log"))


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
        "status": "Angenommen",
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
            mission["status"] = "Am Missionsziel"
            if _mission_name_matches_delivery(mission):
                mission["next_step"] = "Missionsterminal öffnen / Lieferung abgeben"
            elif _mission_name_matches_data(mission):
                mission["next_step"] = "Missionsziel ausführen / Daten beschaffen"
            else:
                mission["next_step"] = "Missionsziel ausführen"
        else:
            if mission.get("status") in ("Angenommen", "Unterwegs"):
                mission["status"] = "Im Zielsystem"
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
        if e.get("NewDestinationSystem"):
            mission["destination_system"] = e["NewDestinationSystem"]
        if e.get("NewDestinationStation"):
            mission["destination_station"] = e["NewDestinationStation"]

        mission["status"] = "Ziel geändert"
        mission["next_step"] = default_next_step(mission)
        mission["summary"] = build_summary(mission)

    elif et == "CargoDepot":
        update_type = (e.get("UpdateType") or "").lower()
        collected = e.get("ItemsCollected")
        delivered = e.get("ItemsDelivered")
        total = e.get("TotalItemsToDeliver")

        if update_type == "collect":
            mission["status"] = "Ware aufgenommen"
            if collected is not None and total is not None:
                mission["progress_text"] = f"{collected}/{total} aufgenommen"
            mission["next_step"] = default_next_step(mission)

        elif update_type == "deliver":
            mission["status"] = "Lieferung läuft"
            if delivered is not None and total is not None:
                mission["progress_text"] = f"{delivered}/{total} geliefert"

            if (
                delivered is not None
                and total is not None
                and delivered >= total
            ):
                mission["status"] = "Aufgabe erledigt"
                mission["next_step"] = "Zurück zum Missionsterminal"
            else:
                mission["next_step"] = "Weitere Missionsware abgeben"

    mission["last_update"] = ts


def read_latest_state(folder: Path, mission_reset_at: str = "") -> dict:
    """
    Liest Journale chronologisch ein.

    System-/Body-Daten werden über SystemAddress + BodyID zusammengeführt.
    Dadurch sind Scan und SAASignalsFound nicht mehr von der Event-Reihenfolge
    oder vom gerade gesetzten current_system abhängig.
    """
    result = {
        "commander": "",
        "system": "",
        "system_address": None,
        "star_pos": None,
        "body": "",
        "station": "",
        "ship": "",
        "last_timestamp": "",
        "missions": [],
        "journal_files": 0,
        "system_bodies": [],
        "system_body_count": 0,
        "system_signals_count": 0,
        "system_all_bodies_found": False,
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

    files = journal_files(folder)
    result["journal_files"] = len(files)

    if not files:
        return result

    missions: dict[int, dict] = {}

    current_system = ""
    current_system_address = None
    current_station = ""
    current_body = ""

    # SystemAddress -> {BodyID -> body}
    scans_by_address: dict[int, dict[int, dict]] = {}

    # SystemAddress -> {BodyID -> bio_count}
    pending_bio_by_address: dict[int, dict[int, int]] = {}

    # SystemAddress -> BodyID -> eindeutige biologische Funde
    biology_by_address: dict[int, dict[int, dict[tuple, dict]]] = {}

    # SystemAddress -> {BodyName -> bio_count}
    # Fallback nur innerhalb desselben Systems.
    pending_bio_name_by_address: dict[int, dict[str, int]] = {}

    # GEO analog zu BIO
    pending_geo_by_address: dict[int, dict[int, int]] = {}
    pending_geo_name_by_address: dict[int, dict[str, int]] = {}

    # SystemAddress -> BodyCount
    body_count_by_address: dict[int, int] = {}

    # SystemAddressen, bei denen FSSAllBodiesFound auftrat
    all_found_addresses: set[int] = set()

    # Signale deduplizieren statt blind mitzuzählen:
    # SystemAddress -> set(signature)
    signal_signatures: dict[int, set[tuple]] = {}

    def _system_address(event: dict):
        value = event.get("SystemAddress")
        if isinstance(value, int):
            return value
        return current_system_address

    def _bio_count_from_event(event: dict) -> int:
        bio_count = 0

        for signal in (event.get("Signals") or []):
            signal_type = (
                signal.get("Type_Localised")
                or signal.get("Type")
                or ""
            ).lower()

            # Frontier intern:
            # $SAA_SignalType_Biological;
            if (
                "biological" in signal_type
                or "biologisch" in signal_type
                or "biology" in signal_type
                or "saa_signaltype_biological" in signal_type
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

    def _geo_count_from_event(event: dict) -> int:
        geo_count = 0

        for signal in (event.get("Signals") or []):
            signal_type = (
                signal.get("Type_Localised")
                or signal.get("Type")
                or ""
            ).lower()

            if (
                "geological" in signal_type
                or "geologisch" in signal_type
                or "geology" in signal_type
                or "saa_signaltype_geological" in signal_type
            ):
                try:
                    geo_count += int(signal.get("Count") or 0)
                except Exception:
                    pass

        return geo_count

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


    for journal in files:
        try:
            handle = journal.open(
                "r",
                encoding="utf-8",
                errors="replace"
            )
        except OSError:
            continue

        with handle:
            for line in handle:
                try:
                    e = json.loads(line)
                except json.JSONDecodeError:
                    continue

                ts = e.get("timestamp") or ""
                if ts:
                    result["last_timestamp"] = ts

                et = e.get("event")

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
                    result["ship"] = (
                        e.get("ShipName")
                        or e.get("Ship_Localised")
                        or e.get("Ship")
                        or result["ship"]
                    )

                elif et == "Loadout":
                    result["ship"] = (
                        e.get("ShipName")
                        or e.get("Ship")
                        or result["ship"]
                    )

                # ---------------------------------------------------------
                # System / Location
                # ---------------------------------------------------------
                elif et in ("Location", "FSDJump", "CarrierJump"):
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
                        if isinstance(e.get("BodyCount"), int):
                            body_count_by_address[address] = e["BodyCount"]

                elif et == "FSSAllBodiesFound":
                    address = _system_address(e)

                    if address is not None:
                        all_found_addresses.add(address)

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
                        parent_id = None

                        if parents:
                            try:
                                parent_id = int(
                                    next(
                                        iter(
                                            parents[-1].values()
                                        )
                                    )
                                )
                            except Exception:
                                parent_id = None

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
                            "gravity_g": gravity_g,
                            "distance_ls": e.get("DistanceFromArrivalLS"),
                            "landable": bool(e.get("Landable", False)),
                            "terraformable": (
                                e.get("TerraformState")
                                == "Terraformable"
                            ),
                            "was_discovered": e.get("WasDiscovered"),
                            "was_mapped": e.get("WasMapped"),
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
                            "biology": [],
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
                            body["self_mapped"] = bool(
                                previous.get("self_mapped")
                            )
                            body["efficient_mapping"] = bool(
                                previous.get("efficient_mapping")
                            )
                            body["biological_signals"] = int(
                                previous.get("biological_signals") or 0
                            )
                            body["geological_signals"] = int(
                                previous.get("geological_signals") or 0
                            )

                        _apply_pending_bio(address, body)
                        _apply_pending_geo(address, body)
                        apply_values(body)

                        scans_by_address[address][body_id_int] = body

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

                            probes_used = e.get("ProbesUsed")
                            efficiency_target = e.get("EfficiencyTarget")

                            if (
                                isinstance(probes_used, int)
                                and isinstance(efficiency_target, int)
                            ):
                                body["efficient_mapping"] = (
                                    probes_used <= efficiency_target
                                )

                            apply_values(body)

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

                        pending_bio_by_address.setdefault(
                            address,
                            {}
                        )[body_id_int] = bio_count

                        pending_geo_by_address.setdefault(
                            address,
                            {}
                        )[body_id_int] = geo_count

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

                        if body:
                            body["biological_signals"] = bio_count
                            body["geological_signals"] = geo_count
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
                            biology_by_address.setdefault(address, {}).setdefault(
                                body_id_int, {}
                            )[key] = {
                                "genus": genus,
                                "species": species,
                                "variant": variant,
                                "scan_type": e.get("ScanType") or "",
                                "timestamp": ts,
                            }

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
                # Mission Snapshot
                # ---------------------------------------------------------
                elif et == "Missions":
                    if not _after_mission_reset(ts):
                        continue
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

                        missions[mid] = _new_mission(raw)

                elif et == "MissionAccepted":
                    if not _after_mission_reset(ts):
                        continue
                    mid = e.get("MissionID")

                    if mid is not None:
                        missions[mid] = _new_mission(e)

                elif et == "MissionRedirected":
                    if not _after_mission_reset(ts):
                        continue
                    mid = e.get("MissionID")

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
                            mission["status"] = "Daten erhalten"
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
                    missions.pop(mid, None)

    result["missions"] = list(missions.values())

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

    return result
