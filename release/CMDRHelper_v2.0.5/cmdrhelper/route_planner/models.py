from __future__ import annotations

from dataclasses import dataclass
import math


@dataclass(frozen=True)
class CarrierRouteRequest:
    source: str
    destination: str
    tritium_in_tank: int
    tritium_in_storage: int
    max_jump_range: int


@dataclass(frozen=True)
class CarrierRouteJump:
    system: str
    distance: float | None
    distance_remaining: float | None
    tritium_used: int | None
    fuel_in_tank: int | None
    tritium_in_market: int | None
    has_icy_ring: bool | None
    is_system_pristine: bool | None
    must_restock: bool | None


@dataclass(frozen=True)
class CarrierRoute:
    jumps: tuple[CarrierRouteJump, ...]
    total_distance: float
    jump_count: int
    estimated_tritium: int


@dataclass(frozen=True)
class ShipRouteJump:
    system: str
    system_address: int | None = None
    distance: float | None = None
    distance_remaining: float | None = None
    fuel_in_tank: float | None = None
    fuel_used: float | None = None
    must_refuel: bool | None = None
    has_neutron: bool | None = None


@dataclass
class ShipRoute:
    jumps: tuple[ShipRouteJump, ...]
    reached_index: int | None = None
    next_index: int | None = None
    status: str = "active"


@dataclass(frozen=True)
class ShipRouteRequest:
    source: str
    destination: str
    is_supercharged: bool
    use_supercharge: bool
    use_injections: bool
    exclude_secondary: bool
    refuel_every_scoopable: bool
    algorithm: str
    tank_size: float
    cargo: float
    optimal_mass: float
    base_mass: float
    internal_tank_size: float
    max_fuel_per_jump: float
    range_boost: float
    fuel_power: float
    fuel_multiplier: float
    reserve_size: float
    supercharge_multiplier: float = 4.0
    injection_multiplier: float = 2.0
    max_time: int = 60

    def validation_error(self) -> str | None:
        if not self.source.strip():
            return "source_required"
        if not self.destination.strip():
            return "destination_required"
        values = (
            self.tank_size, self.cargo, self.optimal_mass, self.base_mass,
            self.internal_tank_size, self.max_fuel_per_jump, self.range_boost,
            self.fuel_power, self.fuel_multiplier, self.reserve_size,
            self.supercharge_multiplier, self.injection_multiplier,
        )
        if any(not math.isfinite(value) for value in values):
            return "technical_values"
        positive = (
            self.tank_size, self.optimal_mass, self.base_mass,
            self.max_fuel_per_jump, self.fuel_power, self.fuel_multiplier,
            self.supercharge_multiplier, self.injection_multiplier,
        )
        if any(value <= 0 for value in positive):
            return "positive_values"
        if any(value < 0 for value in (
            self.cargo, self.internal_tank_size, self.range_boost, self.reserve_size
        )) or self.max_time <= 0:
            return "technical_values"
        if self.reserve_size > self.internal_tank_size:
            return "reserve"
        return None


@dataclass(frozen=True)
class GuardianFsdBooster:
    item: str
    on: bool | None = None


@dataclass
class ShipLoadoutData:
    ship_id: int | None = None
    ship_type: str | None = None
    ship_name: str | None = None
    ship_ident: str | None = None
    unladen_mass: float | None = None
    cargo_capacity: int | None = None
    cargo: int | None = None
    max_jump_range: float | None = None
    main_tank_capacity: float | None = None
    reserve_tank_capacity: float | None = None
    main_fuel: float | None = None
    reserve_fuel: float | None = None
    fsd_item: str | None = None
    fsd_on: bool | None = None
    fsd_blueprint: str | None = None
    fsd_engineering_level: int | None = None
    fsd_engineering_quality: float | None = None
    fsd_experimental_effect: str | None = None
    fsd_engineering_modifiers: tuple[dict, ...] = ()
    fsd_optimal_mass: float | None = None
    fsd_max_fuel_per_jump: float | None = None
    guardian_fsd_boosters: tuple[GuardianFsdBooster, ...] = ()
    loadout_timestamp: str | None = None
    loadout_complete: bool = False
    loadout_stale: bool = True
