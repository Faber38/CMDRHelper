from __future__ import annotations

import math

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


def calculate_body_values(body: dict) -> dict:
    name_lower = (body.get("name") or "").lower()

    # Belt Cluster nicht als lohnenswerte Explorer-Ziele bewerten.
    if "belt cluster" in name_lower:
        return {
            "base_value": 0,
            "scan_value": 0,
            "mapped_value": 0,
            "current_value": 0,
            "high_value": False,
        }

    if body.get("body_type") == "Star" or body.get("star_type"):
        # Sterne können gescannt, aber nicht mit dem DSS kartographiert
        # werden. Daher gibt es keinen zusätzlichen Kartographiewert.
        base = _star_value(body)
        value = int(round(base))
        return {
            "base_value": value,
            "scan_value": value,
            "mapped_value": 0,
            "current_value": value,
            "high_value": False,
        }

    base = _planet_base_value(body)

    was_discovered = body.get("was_discovered")
    was_mapped = body.get("was_mapped")
    self_mapped = bool(body.get("self_mapped"))
    efficient_mapping = bool(body.get("efficient_mapping"))

    # Scanwert
    scan_value = base
    if was_discovered is False:
        scan_value *= FIRST_DISCOVERY_MULTIPLIER

    # Potenzieller Wert nach Kartographie.
    # Für die Anzeige nehmen wir effizientes Mapping als Zielwert an.
    if was_discovered is False and was_mapped is False:
        mapped_value = (
            base
            * FIRST_DISCOVERY_MULTIPLIER
            * FIRST_DISCOVERED_MAPPED_MULTIPLIER
            * EFFICIENCY_MULTIPLIER
        )
    elif was_discovered is True and was_mapped is False:
        mapped_value = (
            base
            * FIRST_MAPPED_MULTIPLIER
            * EFFICIENCY_MULTIPLIER
        )
    else:
        mapped_value = (
            base
            * NORMAL_MAPPING_MULTIPLIER
            * EFFICIENCY_MULTIPLIER
        )

    current_value = scan_value

    # Wenn wir den Körper selbst kartiert haben, den aktuell erreichten Wert
    # statt nur des möglichen Zielwertes anzeigen.
    if self_mapped:
        if was_discovered is False and was_mapped is False:
            current_value = (
                base
                * FIRST_DISCOVERY_MULTIPLIER
                * FIRST_DISCOVERED_MAPPED_MULTIPLIER
            )
        elif was_discovered is True and was_mapped is False:
            current_value = base * FIRST_MAPPED_MULTIPLIER
        else:
            current_value = base * NORMAL_MAPPING_MULTIPLIER

        if efficient_mapping:
            current_value *= EFFICIENCY_MULTIPLIER

    result = {
        "base_value": int(round(base)),
        "scan_value": int(round(scan_value)),
        "mapped_value": int(round(mapped_value)),
        "current_value": int(round(current_value)),
    }

    result["high_value"] = result["mapped_value"] > 200_000
    return result


def apply_values(body: dict) -> dict:
    body.update(calculate_body_values(body))
    return body


def system_totals(bodies: list[dict]) -> dict:
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
