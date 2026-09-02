from __future__ import annotations


VEHICLE_TYPES = {
    "testbuggy": "scarab",
    "combat_multicrew_srv_01": "scorpion",
    "lander01": "nomad",
}


def analyze_ship_modules(modules) -> dict:
    """Leitet nur direkt aus Loadout-Slots und -Items belegbare Ausrüstung ab."""
    result = {
        "vehicle_hangar": False,
        "vehicle_hangar_item": "",
        "vehicles": {"scarab": 0, "scorpion": 0, "nomad": 0},
        "fighter_hangar": False,
        "fighters": 0,
        "shield_generator": "",
        "shield_engineering": {},
        "shield_boosters": 0,
        "guardian_shield_reinforcements": 0,
        "weapons": 0,
        "hull_reinforcements": 0,
        "module_reinforcements": 0,
        "fighter_hangar_item": "",
        "passenger_cabins": 0,
    }
    for module in modules or ():
        if not isinstance(module, dict):
            continue
        slot = str(module.get("Slot") or "").strip().casefold()
        item_raw = str(module.get("Item") or "").strip()
        item = item_raw.casefold()
        if not item:
            continue

        is_vehicle_hangar = item.startswith(
            ("int_buggybay_", "int_mkiilargebuggybay_")
        )
        if is_vehicle_hangar:
            result["vehicle_hangar"] = True
            result["vehicle_hangar_item"] = item_raw
        vehicle_type = VEHICLE_TYPES.get(item)
        if vehicle_type and "planetaryvehiclehangar" in slot:
            result["vehicle_hangar"] = True
            result["vehicles"][vehicle_type] += 1

        if item.startswith(("int_fighterbay_", "int_fighterbaymk2_")):
            result["fighter_hangar"] = True
            result["fighter_hangar_item"] = item_raw
        elif slot.startswith("fighterbay") and not is_vehicle_hangar:
            result["fighter_hangar"] = True
            result["fighters"] += 1

        if slot == "shieldgenerator" or item.startswith("int_shieldgenerator_"):
            result["shield_generator"] = item_raw
            engineering = module.get("Engineering")
            result["shield_engineering"] = (
                dict(engineering) if isinstance(engineering, dict) else {}
            )
        if item.startswith("hpt_shieldbooster_"):
            result["shield_boosters"] += 1
        if item.startswith("int_guardianshieldreinforcement_"):
            result["guardian_shield_reinforcements"] += 1
        if "hardpoint" in slot and not slot.startswith("tinyhardpoint"):
            result["weapons"] += 1
        if item.startswith("int_hullreinforcement_"):
            result["hull_reinforcements"] += 1
        if item.startswith("int_modulereinforcement_"):
            result["module_reinforcements"] += 1
        if item.startswith("int_passengercabin_"):
            result["passenger_cabins"] += 1

    result["srv_count"] = sum(result["vehicles"].values())
    return result
