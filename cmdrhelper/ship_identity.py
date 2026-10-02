from __future__ import annotations

import re


_SUIT_TYPE = re.compile(r"^(exploration|utility|tactical)suit_class\d+$", re.I)

# Diese internen Typen sind durch die realen Journale eindeutig als SRVType
# in LaunchSRV/DockSRV und zugleich als irreführendes LoadGame.Ship belegt.
_CONFIRMED_SRV_TYPES = {
    "testbuggy",                 # Scarab
    "combat_multicrew_srv_01",  # Scorpion
    "lander01",                 # Nomad
    "mev_rhino",                # Rhino
}


def is_suit(ship_type, localized_name="") -> bool:
    internal = str(ship_type or "").strip().casefold()
    localized = str(localized_name or "").strip().casefold()
    return bool(_SUIT_TYPE.fullmatch(internal) or "suit_class" in localized)


def is_definite_non_ship(ship_type, localized_name="") -> bool:
    """Konservative Erkennung eindeutig nicht persistenter Raumfahrzeuge."""
    internal = str(ship_type or "").strip().casefold()
    localized = str(localized_name or "").strip().casefold()
    if not internal:
        return False
    if is_suit(ship_type, localized_name):
        return True
    if internal in _CONFIRMED_SRV_TYPES:
        return True
    if localized.startswith("srv ") or "(srv)" in localized:
        return True
    return False
