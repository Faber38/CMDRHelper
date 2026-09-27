"""Ephemeral, journal-bound ship totals, independent of commodity inventory.

Never persist Status as an inventory. Event order (including repeated switches in
one second) identifies cargo; timestamps only gate the unlabelled Status sidecar.
"""
from datetime import datetime, timezone
import math

from .ship_identity import is_definite_non_ship
from .status_reader import utc_timestamp

STATUS_MAX_AGE_SECONDS = 120

# These may change quantity or its interpretation. Wait for authoritative Cargo
# or a later Status rather than trying to apply an incomplete commodity ledger.
CARGO_MUTATIONS = {
    'MarketBuy', 'MarketSell', 'CollectCargo', 'EjectCargo', 'MiningRefined',
    'CargoTransfer', 'BuyDrones', 'SellDrones', 'CargoDepot', 'MissionCompleted',
    'MissionAccepted', 'MissionAbandoned', 'MissionFailed', 'EngineerContribution',
    'SearchAndRescue', 'CarrierDepositFuel', 'EjectTacticalCore', 'PowerplayCollect',
    'PowerplayDeliver', 'PowerplayFastTrack', 'Synthesis', 'LaunchDrone',
    'TechnologyBroker', 'ScientificResearch',
}


def utc_now():
    return datetime.now(timezone.utc)


class ShipCargoTracker:
    """Consume only chronologically ordered events from an identified journal."""
    def __init__(self):
        self.context = {}
        self.last_cargo_context = None
        self.sequence = 0

    def _invalidate(self, timestamp):
        self.context.update(total=None, barrier=timestamp, generation=self.sequence)

    def apply(self, event, fid, journal):
        self.sequence += 1
        et, ts = event.get('event'), event.get('timestamp', '')
        c = self.context
        if c.get('fid') != fid or c.get('journal') != str(journal):
            c.clear()
            c.update(fid=fid, journal=str(journal), ship_id=None, vessel=None,
                     session_start=ts, session_generation=self.sequence,
                     loadout_seen=False, active=True)
            self._invalidate(ts)
        if et == 'LoadGame':
            c.update(ship_id=None, vessel=None, session_start=ts,
                     session_generation=self.sequence, loadout_seen=False, active=True)
            self._invalidate(ts)
            if not is_definite_non_ship(event.get('Ship')):
                c.update(ship_id=event.get('ShipID'), vessel='Ship')
            else:
                c['vessel'] = 'SRV'
        elif et in ('ShipyardSwap', 'ShipyardBuy', 'ShipyardNew'):
            self._invalidate(ts)
            c.update(ship_id=event.get('NewShipID') if et == 'ShipyardNew' else event.get('ShipID'),
                     vessel='Ship', loadout_seen=False)
        elif et == 'Loadout' and not is_definite_non_ship(event.get('Ship')):
            if c.get('ship_id') != event.get('ShipID') or c.get('vessel') != 'Ship':
                self._invalidate(ts)
            c.update(ship_id=event.get('ShipID'), vessel='Ship', loadout_seen=True)
        elif et in ('Died', 'Resurrect', 'ClearSavedGame', 'Shutdown'):
            self._invalidate(ts)
            c.update(ship_id=None, vessel=None, loadout_seen=False,
                     active=et != 'Shutdown')
        elif et in ('LaunchSRV', 'LaunchFighter') and event.get('PlayerControlled', True):
            self._invalidate(ts)
            c['vessel'] = 'SRV' if et == 'LaunchSRV' else None
        elif et in ('DockSRV', 'DockFighter', 'SRVDestroyed'):
            self._invalidate(ts)
            c['vessel'] = 'Ship'
        elif et == 'Disembark':
            self._invalidate(ts)
            c['vessel'] = None
        elif et == 'Embark':
            self._invalidate(ts)
            c['vessel'] = None if any(event.get(k) for k in ('SRV', 'Taxi', 'Multicrew')) else 'Ship'
        elif et in CARGO_MUTATIONS:
            self._invalidate(ts)
        elif et == 'Cargo':
            # The origin is captured now, never supplied by a later Loadout.
            vessel = str(event.get('Vessel', '')).casefold()
            self._invalidate(ts)
            origin = dict(fid=fid, journal=str(journal), generation=c['generation'],
                          ship_id=c.get('ship_id') if vessel == 'ship' else None,
                          session_start=c['session_start'], session_generation=c['session_generation'],
                          vessel='Ship' if vessel == 'ship' else 'SRV', timestamp=ts)
            self.last_cargo_context = origin
            count = event.get('Count')
            if (vessel == 'ship' and c.get('vessel') == 'Ship'
                    and type(c.get('ship_id')) is int and type(count) is int and count >= 0):
                # Reject malformed inline inventory, but a count-only Cargo is
                # authoritative for total occupancy without a matching sidecar.
                from .cargo import _valid_sidecar_inventory
                if 'Inventory' not in event or _valid_sidecar_inventory(event):
                    c['total'] = dict(origin, count=count, source='journal')


def ship_context_valid(state):
    c = getattr(state, 'ship_cargo_context', None)
    loadout = getattr(state, 'ship_loadout', None)
    sessions = getattr(state, '_journal_index_sessions', None) or []
    session = sessions[-1] if sessions else {}
    return bool(
        not getattr(state, '_cargo_blocked', False)
        and isinstance(c, dict) and c.get('active') and c.get('vessel') == 'Ship'
        and c.get('loadout_seen') and loadout is not None
        and type(loadout.ship_id) is int and loadout.ship_id >= 0
        and c.get('ship_id') == loadout.ship_id
        and loadout.ship_type and not is_definite_non_ship(loadout.ship_type)
        and loadout.loadout_complete and not loadout.loadout_stale
        and type(loadout.cargo_capacity) is int and loadout.cargo_capacity >= 0
        and c.get('fid') and c['fid'] == getattr(state, 'commander_fid', '')
        and session.get('attribution_status') == 'identified'
        and session.get('commander_id') is not None
        and session['commander_id'] == getattr(state, 'commander_id', None)
        and session.get('fid_seen') == c['fid']
        and session.get('journal_file') == c.get('journal')
    )


def status_ship_count(state, status, *, now=None):
    """Shared HUD/trade validation. Status has neither FID nor ShipID.

    Require an identified current game, its complete Loadout, ship flags, and a
    Status strictly AFTER the last ambiguous transition/mutation. Equal-second
    timestamps cannot establish event order. A two-minute TTL expires even when
    no more journal/sidecar writes occur.
    """
    if not ship_context_valid(state) or not isinstance(status, dict) or status.get('event') != 'Status':
        return None
    flags, flags2 = status.get('Flags'), status.get('Flags2', 0)
    if (any(type(v) is not int or v < 0 for v in (flags, flags2))
            or not flags & (1 << 24) or flags & ((1 << 25) | (1 << 26))
            or flags2 & 0b111 or getattr(state, 'active_srv_type', '')):
        return None
    c, loadout = state.ship_cargo_context, state.ship_loadout
    try:
        stamp = utc_timestamp(status.get('timestamp'))
        age = ((now or utc_now()) - stamp).total_seconds()
        if not -5 <= age <= STATUS_MAX_AGE_SECONDS:
            return None
        if not utc_timestamp(c['session_start']) <= utc_timestamp(loadout.loadout_timestamp) <= stamp:
            return None
        if stamp <= utc_timestamp(c['barrier']):
            return None
        # Optional DB metadata can strengthen, but never replace, the live
        # session start (newly indexed sessions may have first_event_at=None).
        session = state._journal_index_sessions[-1]
        for boundary in (session.get('first_event_at'), getattr(state, 'game_mode_timestamp', '')):
            if boundary and utc_timestamp(loadout.loadout_timestamp) < utc_timestamp(boundary):
                return None
    except (ValueError, TypeError, KeyError, OverflowError):
        return None
    used = status.get('Cargo')
    if (type(used) not in (int, float)
            or (type(used) is float and (not math.isfinite(used) or not used.is_integer()))
            or not 0 <= used <= loadout.cargo_capacity):
        return None
    return int(used)


def current_ship_cargo(state, *, now=None):
    """Return a total with provenance, without manufacturing an inventory."""
    if not ship_context_valid(state):
        return None
    c, loadout = state.ship_cargo_context, state.ship_loadout
    snapshot = getattr(state, 'cargo_snapshot', None)
    if isinstance(snapshot, dict):
        origin = snapshot.get('context') or {}
        if (origin.get('fid') == c['fid'] and origin.get('journal') == c['journal']
                and origin.get('generation') == c['generation']
                and origin.get('session_start') == c.get('session_start')
                and origin.get('session_generation') == c.get('session_generation')
                and origin.get('ship_id') == loadout.ship_id and origin.get('vessel') == 'Ship'
                and origin.get('timestamp') == snapshot.get('timestamp')
                and snapshot.get('fid') == c['fid'] and snapshot.get('vessel') == 'Ship'
                and snapshot.get('ship_id') == loadout.ship_id
                and type(snapshot.get('count')) is int
                and 0 <= snapshot['count'] <= loadout.cargo_capacity):
            return dict(origin, count=snapshot['count'], source='snapshot')
    total = c.get('total')
    if (isinstance(total, dict) and total.get('fid') == c['fid']
            and total.get('journal') == c['journal']
            and total.get('session_start') == c.get('session_start')
            and total.get('session_generation') == c.get('session_generation')
            and total.get('ship_id') == loadout.ship_id
            and total.get('generation') == c['generation'] and total.get('vessel') == 'Ship'
            and type(total.get('count')) is int and 0 <= total['count'] <= loadout.cargo_capacity):
        return dict(total)
    status = getattr(state, '_cargo_status', None)
    count = status_ship_count(state, status, now=now)
    if count is None:
        return None
    return dict(fid=c['fid'], ship_id=loadout.ship_id, vessel='Ship', count=count,
                timestamp=status['timestamp'], source='status')
