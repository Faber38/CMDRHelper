"""Static FSD and Guardian booster data used by the ship route planner.

The base values below are transcribed from EDSY's ``eddb.js`` module data
(``fsdoptmass``, ``maxfuel``, ``fuelpower``, ``fuelmul`` and ``jumpbst``).
Mass and fuel values are tonnes; Guardian booster values are light-years.
SCO drives and the Mk II special variant have their own explicit records.

Only internal Elite Journal item names observed in CMDRHelper's local journal
history are included.  Unknown items deliberately do not fall back to a
similar-looking drive: their specification remains unknown.
"""

from __future__ import annotations

from dataclasses import dataclass

from cmdrhelper.route_planner.models import ShipLoadoutData


@dataclass(frozen=True)
class FsdSpec:
    item: str
    optimal_mass: float
    max_fuel_per_jump: float
    fuel_power: float
    fuel_multiplier: float
    size: int
    rating: str
    variant: str = "classic"


@dataclass(frozen=True)
class ShipRouteTechnicalData:
    tank_size: float | None
    cargo: float | None
    base_mass: float | None
    internal_tank_size: float | None
    reserve_size: float | None
    optimal_mass: float | None
    max_fuel_per_jump: float | None
    fuel_power: float | None
    fuel_multiplier: float | None
    range_boost: float | None
    complete: bool
    stale: bool
    missing_fields: tuple[str, ...]
    unknown_fsd: bool


def _spec(
    item: str,
    optimal_mass: float,
    max_fuel_per_jump: float,
    fuel_power: float,
    fuel_multiplier: float,
    size: int,
    rating: str,
    variant: str = "classic",
) -> FsdSpec:
    return FsdSpec(
        item=item,
        optimal_mass=optimal_mass,
        max_fuel_per_jump=max_fuel_per_jump,
        fuel_power=fuel_power,
        fuel_multiplier=fuel_multiplier,
        size=size,
        rating=rating,
        variant=variant,
    )


# EDSY module data: https://github.com/taleden/EDSY/blob/master/eddb.js
_FSD_SPECS = (
    _spec("int_hyperdrive_size2_class1", 48.0, 0.60, 2.00, 0.011, 2, "E"),
    _spec("int_hyperdrive_size2_class2", 54.0, 0.60, 2.00, 0.010, 2, "D"),
    _spec("int_hyperdrive_size5_class5", 1050.0, 5.00, 2.45, 0.012, 5, "A"),
    _spec("int_hyperdrive_size6_class1", 960.0, 5.30, 2.60, 0.011, 6, "E"),
    _spec("int_hyperdrive_overcharge_size2_class3", 90.0, 0.90, 2.00, 0.012, 2, "C", "SCO"),
    _spec("int_hyperdrive_overcharge_size2_class5", 100.0, 1.00, 2.00, 0.013, 2, "A", "SCO"),
    _spec("int_hyperdrive_overcharge_size3_class5", 167.0, 1.90, 2.15, 0.013, 3, "A", "SCO"),
    _spec("int_hyperdrive_overcharge_size4_class3", 525.0, 3.00, 2.30, 0.012, 4, "C", "SCO"),
    _spec("int_hyperdrive_overcharge_size4_class5", 585.0, 3.20, 2.30, 0.013, 4, "A", "SCO"),
    _spec("int_hyperdrive_overcharge_size5_class1", 700.0, 3.30, 2.45, 0.008, 5, "E", "SCO"),
    _spec("int_hyperdrive_overcharge_size5_class3", 1050.0, 5.00, 2.45, 0.012, 5, "C", "SCO"),
    _spec("int_hyperdrive_overcharge_size5_class4", 1050.0, 5.00, 2.45, 0.012, 5, "B", "SCO"),
    _spec("int_hyperdrive_overcharge_size5_class5", 1175.0, 5.20, 2.45, 0.013, 5, "A", "SCO"),
    _spec("int_hyperdrive_overcharge_size6_class5", 2000.0, 8.30, 2.60, 0.013, 6, "A", "SCO"),
    _spec("int_hyperdrive_overcharge_size7_class1", 1800.0, 8.50, 2.75, 0.008, 7, "E", "SCO"),
    _spec("int_hyperdrive_overcharge_size7_class3", 2700.0, 12.80, 2.75, 0.012, 7, "C", "SCO"),
    _spec("int_hyperdrive_overcharge_size8_class1", 2800.0, 13.60, 2.90, 0.008, 8, "E", "SCO"),
    _spec(
        "int_hyperdrive_overcharge_size8_class5_overchargebooster_mkii",
        4670.0,
        6.80,
        2.5025,
        0.011,
        8,
        "A",
        "SCO Mk II",
    ),
)

FSD_SPECS: dict[str, FsdSpec] = {
    spec.item.casefold(): spec for spec in _FSD_SPECS
}

GUARDIAN_FSD_BOOSTS: dict[str, float] = {
    "int_guardianfsdbooster_size1": 4.00,
    "int_guardianfsdbooster_size2": 6.00,
    "int_guardianfsdbooster_size3": 7.75,
    "int_guardianfsdbooster_size4": 9.25,
    "int_guardianfsdbooster_size5": 10.50,
}


def lookup_fsd_spec(item: str | None) -> FsdSpec | None:
    """Return the exact spec for a Journal item, never a guessed substitute."""

    if not item:
        return None
    return FSD_SPECS.get(item.strip().casefold())


def lookup_guardian_fsd_boost(item: str | None) -> float | None:
    """Return an exact Guardian booster bonus in ly, or ``None``."""

    if not item:
        return None
    return GUARDIAN_FSD_BOOSTS.get(item.strip().casefold())


def _active_guardian_boost(loadout: ShipLoadoutData) -> float | None:
    active = [booster for booster in loadout.guardian_fsd_boosters if booster.on is True]
    if not active:
        return 0.0

    bonuses = [lookup_guardian_fsd_boost(booster.item) for booster in active]
    # Elite normally limits this module to one installation.  Multiple active
    # entries or an unknown active item are ambiguous, so do not sum or guess.
    if len(bonuses) != 1 or bonuses[0] is None:
        return None
    return bonuses[0]


def derive_ship_route_technical_data(
    loadout: ShipLoadoutData,
) -> ShipRouteTechnicalData:
    """Derive only technically supported Spansh inputs from a loadout snapshot."""

    spec = lookup_fsd_spec(loadout.fsd_item)
    base_mass = (
        loadout.unladen_mass + loadout.reserve_tank_capacity
        if loadout.unladen_mass is not None
        and loadout.reserve_tank_capacity is not None
        else None
    )
    optimal_mass = (
        loadout.fsd_optimal_mass
        if loadout.fsd_optimal_mass is not None
        else spec.optimal_mass if spec is not None else None
    )
    max_fuel = (
        loadout.fsd_max_fuel_per_jump
        if loadout.fsd_max_fuel_per_jump is not None
        else spec.max_fuel_per_jump if spec is not None else None
    )

    values = {
        "tank_size": loadout.main_tank_capacity,
        "cargo": float(loadout.cargo) if loadout.cargo is not None else None,
        "base_mass": base_mass,
        "internal_tank_size": loadout.reserve_tank_capacity,
        "reserve_size": loadout.reserve_fuel,
        "optimal_mass": optimal_mass,
        "max_fuel_per_jump": max_fuel,
        "fuel_power": spec.fuel_power if spec is not None else None,
        "fuel_multiplier": spec.fuel_multiplier if spec is not None else None,
        "range_boost": _active_guardian_boost(loadout),
    }
    missing_fields = tuple(name for name, value in values.items() if value is None)
    stale = loadout.loadout_stale
    complete = loadout.loadout_complete and not stale and not missing_fields

    return ShipRouteTechnicalData(
        **values,
        complete=complete,
        stale=stale,
        missing_fields=missing_fields,
        unknown_fsd=spec is None,
    )
