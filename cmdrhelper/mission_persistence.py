"""Current mission state helpers; no terminal mission archive or schema changes."""
from datetime import datetime, timezone
import json


TERMINAL_EVENTS = frozenset(('MissionCompleted', 'MissionFailed', 'MissionAbandoned'))
MISSION_EVENTS = TERMINAL_EVENTS | {'MissionAccepted', 'MissionRedirected', 'CargoDepot', 'Missions'}
ORIGIN_FIELDS = ('original_destination_system', 'original_destination_station')


def mission_origin_prefix(con, commander_id):
    fid = con.execute('SELECT fid FROM commanders WHERE id=?', (commander_id,)).fetchone()[0]
    return 'mission_origin/' + fid + '/'


def load_mission_origins(con, commander_id):
    prefix = mission_origin_prefix(con, commander_id)
    origins = {}
    for key, value in con.execute(
            'SELECT key,value FROM app_meta WHERE substr(key,1,?)=?', (len(prefix), prefix)):
        data = json.loads(value)
        if not isinstance(data, dict) or any(
                key not in ORIGIN_FIELDS or not isinstance(value, str)
                for key, value in data.items()):
            raise ValueError('Invalid mission origin metadata')
        origins[key[len(prefix):]] = data
    return origins


def utc_stamp(value):
    try:
        dt = datetime.fromisoformat(str(value).replace('Z', '+00:00'))
        if dt.tzinfo is not None:
            return dt.astimezone(timezone.utc).isoformat(timespec='microseconds')
    except (TypeError, ValueError, OverflowError):
        pass
    return ''


def load_anchor(con, commander_id):
    fid = con.execute('SELECT fid FROM commanders WHERE id=?', (commander_id,)).fetchone()[0]
    key = 'mission_state_anchor/' + fid
    row = con.execute('SELECT value FROM app_meta WHERE key=?', (key,)).fetchone()
    if row:
        anchor = tuple(json.loads(row[0]))
        if (len(anchor) != 4 or not isinstance(anchor[0], str)
                or not isinstance(anchor[1], str)
                or not all(type(n) is int for n in anchor[2:])):
            raise ValueError('Invalid mission state anchor')
        return key, anchor
    # Bootstrap from persisted state, never replay older missions over it.
    stamps = [utc_stamp(r[0]) for r in con.execute(
        'SELECT last_updated FROM commander_missions WHERE commander_id=?', (commander_id,))]
    return key, (max(stamps, default=''), '', -1, -1)


def save_anchor(con, key, anchor):
    con.execute('INSERT INTO app_meta(key,value) VALUES(?,?) '
                'ON CONFLICT(key) DO UPDATE SET value=excluded.value',
                (key, json.dumps(anchor)))


def valid_snapshot(event):
    """An absent/malformed Active is not an authoritative empty inventory."""
    if not isinstance(event.get('Active'), list):
        return False
    for field in ('Active', 'Complete', 'Failed'):
        items = event.get(field, [])
        if not isinstance(items, list):
            return False
        for item in items:
            if not isinstance(item, dict) or type(item.get('MissionID')) is not int:
                return False
    return True


def snapshot_mission(item, timestamp, existing=None):
    from cmdrhelper.journal_reader import _new_mission
    from cmdrhelper.models import STATUS_ACCEPTED
    fresh = _new_mission(dict(item, timestamp=timestamp))
    if not existing:
        return fresh
    # Snapshot fields are intentionally sparse. Preserve progress, descriptions,
    # commodity text and encounter enrichment instead of regenerating defaults.
    mission = dict(existing)
    fields = {
        'LocalisedName': 'name', 'Name_Localised': 'name', 'Name': 'internal_name',
        'Faction': 'faction', 'DestinationSystem': 'destination_system',
        'DestinationStation': 'destination_station', 'DestinationSettlement': 'destination_station',
        'DestinationBody': 'destination_body', 'Expiry': 'expiry', 'Reward': 'reward',
        'Commodity': 'commodity', 'Commodity_Localised': 'commodity', 'Count': 'count',
    }
    for source, target in fields.items():
        if item.get(source) not in (None, '', 0):
            mission[target] = fresh[target]
    update_destination_summary(existing, mission)
    if not mission.get('is_open', True):
        mission['status'] = STATUS_ACCEPTED
    mission.update(last_update=timestamp, terminal_state='', is_open=1)
    return mission


def update_destination_summary(existing, mission):
    """Refresh only generated target text; retain the remaining description."""
    from cmdrhelper.mission_manager import build_summary
    destinations = ('destination_system', 'destination_body', 'destination_station')
    if any(mission.get(key) != existing.get(key) for key in destinations):
        old_targets = {key: existing[key] for key in destinations if existing.get(key)}
        new_targets = {key: mission[key] for key in destinations if mission.get(key)}
        summary = existing.get('summary') or ''
        # Only replace the known generated destination prefix. Persisted rows
        # need not contain commodity/target fields used to build the remaining
        # text, and encounter/custom descriptions must survive verbatim.
        if old_targets:
            prefix = build_summary(old_targets)
            if summary == prefix:
                summary = ''
            elif summary.startswith(prefix + ' · '):
                summary = summary[len(prefix + ' · '):]
        if summary == build_summary({}):
            summary = ''
        mission['summary'] = ' · '.join(
            part for part in (build_summary(new_targets), summary) if part)


def cleanup_terminal_missions(con, commander_id):
    """Explicit, caller-owned transaction. Never run automatically at startup.

    Only definite legacy terminal rows qualify. Unknown/inactive rows survive.
    Keep the commander watermark before removing its old terminal timestamps.
    """
    if not con.execute(
        "SELECT 1 FROM commander_missions WHERE commander_id=? AND is_open=0 "
        "AND terminal_state IN ('completed','failed','abandoned') LIMIT 1", (commander_id,)
    ).fetchone():
        return 0
    key, anchor = load_anchor(con, commander_id)
    save_anchor(con, key, anchor)
    return con.execute(
        "DELETE FROM commander_missions WHERE commander_id=? AND is_open=0 "
        "AND terminal_state IN ('completed','failed','abandoned')", (commander_id,)
    ).rowcount
