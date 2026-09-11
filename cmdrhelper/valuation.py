from __future__ import annotations

import math
import json
from functools import lru_cache
from pathlib import Path

from cmdrhelper.exploration_status import exploration_status, journal_flag

# Geschätzte Elite-Dangerous-Explorationswerte.
# Die Werte bleiben absichtlich als Schätzung gekennzeichnet.
#
# Grundlage ist die bekannte Exploration-Payout-Formel mit
# Körperklassen-spezifischen k-Werten und Terraforming-Boni.

Q = 0.56591828

FIRST_DISCOVERY_MULTIPLIER = 2.6
FIRST_DISCOVERED_MAPPED_MULTIPLIER = 3.699622554
FIRST_MAPPED_MULTIPLIER = 8.0956
EFFICIENCY_MULTIPLIER = 1.25

# Für bereits entdeckte und bereits kartographierte Körper verwenden wir
# als normale DSS-Schätzung einen Mapping-Multiplikator.
NORMAL_MAPPING_MULTIPLIER = 3.3333333333

# (k, Terraforming-Bonus)
BODY_VALUES = {
    "Ammonia world": (96932, 93328),
    "Earthlike body": (64831, 116295),
    "Water world": (64831, 116295),
    "High metal content body": (9654, 100677),
    "Metal rich body": (21790, 65631),
    "Icy body": (300, 93328),
    "Rocky body": (300, 93328),
    "Rocky ice body": (300, 93328),

    "Sudarsky class I gas giant": (1656, 93328),
    "Sudarsky class II gas giant": (9654, 100677),
    "Sudarsky class III gas giant": (300, 93328),
    "Sudarsky class IV gas giant": (300, 93328),
    "Sudarsky class V gas giant": (300, 93328),

    "Gas giant with ammonia based life": (300, 93328),
    "Gas giant with water based life": (300, 93328),
    "Helium rich gas giant": (300, 93328),
    "Helium gas giant": (300, 93328),
    "Water giant": (300, 93328),
    "Water giant with life": (300, 93328),
}


def is_live_valuation(body: dict) -> bool:
    """Unknown context gets no Live bonus; explicit 4.x or Odyssey enables it."""
    return (str(body.get("game_version") or "").startswith("4.")
            or body.get("odyssey") is True)


@lru_cache(maxsize=256)
def _journal_context(path: str, modified_ns: int) -> dict:
    context = {}
    with Path(path).open(encoding="utf-8", errors="replace") as handle:
        for line in handle:
            try:
                event = json.loads(line)
            except ValueError:
                continue
            if event.get("event") == "Fileheader":
                context["game_version"] = event.get("gameversion") or ""
                if "Odyssey" in event:
                    context["odyssey"] = event["Odyssey"]
            elif event.get("event") == "LoadGame":
                if "Odyssey" in event:
                    context["odyssey"] = event["Odyssey"]
                break
            elif event.get("event") in ("Location", "FSDJump", "Scan"):
                break
    return context


def journal_valuation_context(path) -> dict:
    """Read existing journal metadata without adding persistent schema fields."""
    try:
        return dict(_journal_context(str(path), Path(path).stat().st_mtime_ns))
    except OSError:
        return {}


@lru_cache(maxsize=256)
def _journal_last_timestamp(path: str, modified_ns: int) -> str:
    # The active file may have grown beyond journal_sessions.last_event_at.
    with Path(path).open("rb") as handle:
        handle.seek(0, 2)
        handle.seek(max(0, handle.tell() - 65536))
        lines = handle.read().splitlines()
    for line in reversed(lines):
        try:
            event = json.loads(line)
        except (ValueError, UnicodeDecodeError):
            continue
        if event.get("timestamp"):
            return str(event["timestamp"])
    return ""


def journal_reaches_timestamp(path, timestamp: str) -> bool:
    try:
        return _journal_last_timestamp(str(path), Path(path).stat().st_mtime_ns) >= timestamp
    except OSError:
        return False


def valuation_signature(body: dict) -> tuple:
    return tuple(body.get(key) for key in (
        "name", "body_type", "star_type", "planet_class", "mass_em", "stellar_mass",
        "terraformable", "was_discovered", "was_mapped", "was_discovered_at_scan",
        "was_mapped_at_scan", "self_mapped", "mapped_at", "efficient_mapping",
        "journal_scanned", "source", "game_version", "odyssey"))


def has_valuation_data(body: dict) -> bool:
    """Do not turn incomplete archive placeholders into estimated scan values."""
    if body.get("_placeholder"):
        return False
    if "belt cluster" in str(body.get("name") or "").lower():
        return True
    star = body.get("body_type") == "Star" or bool(body.get("star_type"))
    mass = body.get("stellar_mass" if star else "mass_em")
    return bool(
        body.get("star_type" if star else "planet_class")
        and type(mass) in (int, float) and math.isfinite(mass) and mass > 0
    )


def _planet_base_value(body: dict) -> float:
    planet_class = body.get("planet_class") or ""
    k, terra_bonus = BODY_VALUES.get(planet_class, (300, 93328))

    if body.get("terraformable"):
        k += terra_bonus

    mass = body.get("mass_em")
    if not isinstance(mass, (int, float)) or mass <= 0:
        mass = 1.0

    value = k + (k * math.pow(mass, 0.2) * Q)
    return max(value, 500.0)


def _star_value(body: dict) -> float:
    # Für die erste Version genügt eine solide Schätzung.
    mass = body.get("stellar_mass")
    if not isinstance(mass, (int, float)) or mass <= 0:
        mass = 1.0

    k = 1200.0
    return k + (mass * k / 66.25)


def calculate_body_values(body: dict, correction_factor: float = 1.0) -> dict:
    name_lower = (body.get("name") or "").lower()

    # Belt Cluster nicht als lohnenswerte Explorer-Ziele bewerten.
    if "belt cluster" in name_lower:
        return {
            "base_value": 0,
            "scan_value": 0,
            "mapped_value": 0,
            "first_discovered_mapped_value": 0,
            "first_discovered_mapped_efficiency_value": 0,
            "possible_value": 0,
            "possible_value_without_efficiency": 0,
            "current_value": 0,
            "mapping_state": "not_applicable",
            "first_mapping_possible": False,
            "already_mapped": False,
            "high_value": False,
        }

    if body.get("body_type") == "Star" or body.get("star_type"):
        # Sterne können gescannt, aber nicht mit dem DSS kartographiert
        # werden. Daher gibt es keinen zusätzlichen Kartographiewert.
        base = _star_value(body)
        value = int(base)
        return {
            "base_value": value,
            "scan_value": value,
            "mapped_value": 0,
            "first_discovered_mapped_value": 0,
            "first_discovered_mapped_efficiency_value": 0,
            "current_value": value,
            "mapping_state": "not_applicable",
            "first_mapping_possible": False,
            "already_mapped": False,
            "high_value": False,
        }

    base = _planet_base_value(body)

    # Kept as a compatible argument; sales calibration never scales this formula.
    was_discovered = journal_flag(body, "was_discovered")
    was_mapped = journal_flag(body, "was_mapped")
    self_mapped = exploration_status(body)["self_mapped"] is True
    efficient_mapping = bool(body.get("efficient_mapping"))

    def mapping_value(multiplier, first_discovery=False, efficient=False):
        value = base * multiplier
        if is_live_valuation(body):
            value += max(value * 0.30, 555)
        if first_discovery:
            value *= FIRST_DISCOVERY_MULTIPLIER
        if efficient:
            value *= EFFICIENCY_MULTIPLIER
        return value

    # A previously mapped body cannot gain FD from a contradictory flag.
    first_discovery = was_discovered is False and was_mapped is not True
    scan_value = base * (FIRST_DISCOVERY_MULTIPLIER if first_discovery else 1)
    combined = was_discovered is False and was_mapped is False
    multiplier = (FIRST_DISCOVERED_MAPPED_MULTIPLIER if combined else
                  FIRST_MAPPED_MULTIPLIER if was_mapped is False else
                  NORMAL_MAPPING_MULTIPLIER)
    mapped_value = mapping_value(multiplier, combined, True)
    first_discovered_mapped_value = mapping_value(FIRST_DISCOVERED_MAPPED_MULTIPLIER, True)
    first_discovered_mapped_efficiency_value = mapping_value(
        FIRST_DISCOVERED_MAPPED_MULTIPLIER, True, True)
    possible_value_without_efficiency = mapping_value(multiplier, combined)
    possible_value = mapped_value
    current_value = scan_value
    if self_mapped:
        # Match EDDiscovery's current-value selection when WasMapped is unknown.
        if was_discovered is False and was_mapped is None:
            current_value = scan_value
            possible_value_without_efficiency = scan_value
        else:
            current_value = mapping_value(multiplier, combined, efficient_mapping)
        possible_value = current_value

    if self_mapped:
        mapping_state = "self_mapped"
    elif was_mapped is True:
        mapping_state = "already_mapped"
    elif was_mapped is False:
        mapping_state = "first_mapping_possible"
    else:
        mapping_state = "unknown"

    result = {
        "base_value": int(base),
        "scan_value": int(scan_value),
        "mapped_value": int(mapped_value),
        "first_discovered_mapped_value": int(first_discovered_mapped_value),
        "first_discovered_mapped_efficiency_value": int(first_discovered_mapped_efficiency_value),
        "possible_value": int(possible_value),
        "possible_value_without_efficiency": int(possible_value_without_efficiency),
        "current_value": int(current_value),
        "mapping_state": mapping_state,
        "first_mapping_possible": mapping_state == "first_mapping_possible",
        "already_mapped": mapping_state == "already_mapped",
    }

    result["high_value"] = result["possible_value"] > 200_000
    return result


def apply_values(body: dict, correction_factor: float = 1.0) -> dict:
    body.update(
        calculate_body_values(
            body,
            correction_factor=correction_factor,
        )
    )
    body["_valuation_signature"] = valuation_signature(body)
    return body


def system_totals(
    bodies: list[dict],
    correction_factor_func=None,
) -> dict:
    scan_total = 0
    mapped_total = 0
    current_total = 0
    high_value_count = 0

    for body in bodies:
        values = calculate_body_values(body)

        scan_total += values["scan_value"]
        mapped_total += values["mapped_value"]
        current_total += values["current_value"]

        if values["high_value"]:
            high_value_count += 1

    return {
        "scan_total": int(scan_total),
        "mapped_total": int(mapped_total),
        "current_total": int(current_total),
        "high_value_count": high_value_count,
    }
