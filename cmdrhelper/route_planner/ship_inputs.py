"""Validated live route telemetry, using the existing ship Status context."""

import math

from cmdrhelper.ship_cargo import STATUS_MAX_AGE_SECONDS, ship_status_context


def status_reserve_fuel(state, status, *, now=None):
    # An import/read in progress suspends use, but does not itself change ships.
    if getattr(state, '_cargo_blocked', False):
        return None
    confirmed = getattr(state, '_confirmed_route_reserve', None)
    state._confirmed_route_reserve = None
    context = ship_status_context(state, status, now=now)
    if context is None:
        return None
    binding, age = context
    fuel = status.get('Fuel')
    reserve = fuel.get('FuelReservoir') if isinstance(fuel, dict) else None
    capacity = state.ship_loadout.reserve_tank_capacity
    if (any(type(v) not in (int, float) or not math.isfinite(v)
            for v in (reserve, capacity)) or not 0 <= reserve <= capacity):
        return None
    binding = dict(binding, reserve_capacity=capacity)
    evidence = dict(timestamp=status['timestamp'], flags=status['Flags'],
                    flags2=status.get('Flags2', 0), reserve=reserve)
    retained = (isinstance(confirmed, dict)
                and confirmed.get('binding') == binding
                and confirmed.get('evidence') == evidence)
    if age < -5 or (age > STATUS_MAX_AGE_SECONDS and not retained):
        return None
    state._confirmed_route_reserve = dict(binding=binding, evidence=evidence)
    return float(reserve)
