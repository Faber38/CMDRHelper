"""Per-ship manual supplements. Automatic data always wins; no new FSD model."""
import hashlib
import json
import math
import re
import time

from PySide6.QtCore import QSettings

from cmdrhelper.ship_cargo import ship_context_valid
from .fsd_specs import derive_ship_route_technical_data

FIELDS = {
    'tank_size': ('ship_tank_size', 't', 100000, True),
    'cargo': ('ship_cargo', 't', 100000, False),
    'base_mass': ('ship_base_mass', 't', 100000, True),
    'internal_tank_size': ('ship_internal_tank', 't', 10000, False),
    'reserve_size': ('ship_reserve_size', 't', 10000, False),
    'optimal_mass': ('ship_optimal_mass', 't', 100000, True),
    'max_fuel_per_jump': ('ship_max_fuel', 't', 10000, True),
    'fuel_power': ('ship_fuel_power', '', 100, True),
    'fuel_multiplier': ('ship_fuel_multiplier', '', 100, True),
    'range_boost': ('ship_range_boost', 'ly', 10000, False),
}
LIVE = {'cargo', 'reserve_size'}
FSD = {'optimal_mass', 'max_fuel_per_jump', 'fuel_power', 'fuel_multiplier'}
LIVE_SECONDS = 120


def identity(state):
    loadout = getattr(state, 'ship_loadout', None)
    fid = str(getattr(state, 'commander_fid', '') or '').strip()
    sid = getattr(loadout, 'ship_id', None)
    return (fid, sid) if fid and type(sid) is int and sid >= 0 else None


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, default=str).encode()).hexdigest()


def configuration(state):
    l = state.ship_loadout
    return digest([l.ship_type, l.fsd_item, l.fsd_engineering_modifiers,
                   [(m.get('Slot'), m.get('Item'), m.get('On'), m.get('Engineering'))
                    for m in l.modules], l.guardian_fsd_boosters])


def scope(state, name):
    l = state.ship_loadout
    if name in FSD:
        item = (l.fsd_item or '').strip().casefold()
        if not item:
            return None
        engineering = digest([l.fsd_blueprint, l.fsd_engineering_level,
                              l.fsd_experimental_effect, l.fsd_engineering_modifiers])
        return [item, engineering] if name in {'optimal_mass', 'max_fuel_per_jump'} else [item]
    return [configuration(state)]


def live_binding(state):
    if not ship_context_valid(state):
        return None
    c = state.ship_cargo_context
    return digest([identity(state), c, state.ship_loadout.loadout_timestamp,
                   getattr(state, 'game_mode_timestamp', ''), configuration(state)])


def parse_number(text, name):
    text = text.strip()
    if not text:
        return None
    if not re.fullmatch(r'[+-]?(?:\d+(?:[.,]\d*)?|[.,]\d+)(?:[eE][+-]?\d+)?', text):
        raise ValueError('number')
    value = float(text.replace(',', '.'))
    validate_number(value, name)
    return value


def validate_number(value, name):
    _, _, maximum, positive = FIELDS[name]
    if type(value) not in (int, float) or not math.isfinite(value):
        raise ValueError('number')
    if value < 0 or value > maximum or (positive and value == 0):
        raise ValueError('range')


def dependencies(values, state):
    errors = {}
    reserve, capacity = values.get('reserve_size'), values.get('internal_tank_size')
    if reserve is not None and capacity is not None and reserve > capacity:
        errors['reserve_size'] = 'reserve'
    cargo, cargo_capacity = values.get('cargo'), state.ship_loadout.cargo_capacity
    if cargo is not None and cargo_capacity is not None and cargo > cargo_capacity:
        errors['cargo'] = 'cargo'
    return errors


class ManualShipData:
    def __init__(self, settings, clock=time.monotonic):
        self.settings = settings
        self.clock = clock
        self.live = {}  # Never persisted: helper restart invalidates live inputs.
        self._live_context = None

    def key(self, state):
        ident = identity(state)
        if ident is None:
            raise ValueError('identity')
        return f'ship_route/manual_v1/{digest(ident[0])}/{ident[1]}'

    def records(self, state):
        if self.settings is None or identity(state) is None:
            return {}
        try:
            raw = json.loads(self.settings.value(self.key(state), '{}'))
            if not isinstance(raw, dict):
                return {}
            result = {}
            for name, record in raw.items():
                if name in FIELDS and name not in LIVE and isinstance(record, dict):
                    try:
                        validate_number(record.get('value'), name)
                    except ValueError:
                        continue
                    result[name] = record
            return result
        except (ValueError, TypeError):
            return {}

    def resolve(self, state):
        technical = derive_ship_route_technical_data(state.ship_loadout)
        records = self.records(state)
        ident, binding, now = identity(state), live_binding(state), self.clock()
        context = (ident, binding)
        if context != self._live_context:
            self.live.clear()
            self._live_context = context
        values, sources = {}, {}
        for name in FIELDS:
            automatic = getattr(technical, name)
            # A stale Loadout cannot establish an automatic technical value.
            if technical.stale:
                automatic = None
            record = records.get(name)
            manual = None
            if name in LIVE:
                live = self.live.get((ident, name))
                if live and binding is not None and live['binding'] == binding and 0 <= now - live['at'] < LIVE_SECONDS:
                    manual = live['value']
                else:
                    self.live.pop((ident, name), None)
                if automatic is not None:
                    self.live.pop((ident, name), None)
            elif record and record.get('scope') == scope(state, name) and scope(state, name) is not None:
                manual = record['value']
            values[name] = automatic if automatic is not None else manual
            sources[name] = 'automatic' if automatic is not None else 'manual' if manual is not None else 'unknown'
        for name in dependencies(values, state):
            if sources[name] == 'manual':
                values[name], sources[name] = None, 'unknown'
        return values, sources, records

    def _write(self, state, records):
        if self.settings is None:
            raise ValueError('identity')
        key = self.key(state)
        previous = self.settings.value(key, None)
        if records:
            self.settings.setValue(key, json.dumps(records, sort_keys=True, allow_nan=False))
        else:
            self.settings.remove(key)
        self.settings.sync()
        if self.settings.status() != QSettings.NoError:
            if previous is None:
                self.settings.remove(key)
            else:
                self.settings.setValue(key, previous)
            self.settings.sync()
            raise OSError('settings')

    def save(self, state, edits):
        self.key(state)
        records = self.records(state)
        values, _, _ = self.resolve(state)
        technical = derive_ship_route_technical_data(state.ship_loadout)
        binding = live_binding(state)
        for name, value in edits.items():
            if value is not None:
                validate_number(value, name)
                if name in LIVE and binding is None:
                    raise ValueError('context')
                if name in FSD and scope(state, name) is None:
                    raise ValueError('fsd')
            if getattr(technical, name) is None or technical.stale:
                values[name] = value
        if dependencies(values, state):
            raise ValueError(next(iter(dependencies(values, state).values())))
        for name, value in edits.items():
            if name not in LIVE:
                if value is None:
                    records.pop(name, None)
                else:
                    records[name] = dict(value=value, scope=scope(state, name))
        self._write(state, records)
        for name, value in edits.items():
            if name in LIVE:
                self.live.pop((identity(state), name), None)
                if value is not None and getattr(technical, name) is None:
                    self.live[(identity(state), name)] = dict(value=value, binding=binding, at=self.clock())

    def delete(self, state):
        self._write(state, {})
        for name in LIVE:
            self.live.pop((identity(state), name), None)
