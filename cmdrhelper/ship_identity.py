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


def is_definite_non_ship(ship_type, localized_name="") -> bool:
    """Konservative Erkennung eindeutig nicht persistenter Raumfahrzeuge."""
    internal = str(ship_type or "").strip().casefold()
    localized = str(localized_name or "").strip().casefold()
    if not internal:
        return False
    if _SUIT_TYPE.fullmatch(internal):
        return True
    if internal in _CONFIRMED_SRV_TYPES:
        return True
    if "suit_class" in localized:
        return True
    if localized.startswith("srv ") or "(srv)" in localized:
        return True
    return False
