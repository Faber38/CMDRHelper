"""Local PP2 facts, independent cursors and durable deletion policies."""
from datetime import datetime, time, timedelta, timezone
import hashlib
import json
from pathlib import Path
import sqlite3

from .powerplay import PowerplayState, amount, timestamp
from .powerplay_chronicle import PowerplayChronicle, is_rare_sale, local_today

PARSER_VERSION = 1
MERIT_RECONCILIATION_KEY = 'pp2_merit_totals_v2'
NOISE = {'Music', 'Friends', 'ReceiveText'}
FACTS = {'PowerplayCollect', 'PowerplayDeliver', 'PowerplayMerits', 'Bounty', 'SearchAndRescue'}
FIELDS = {
    'event', 'timestamp', 'Power', 'Rank', 'Merits', 'TimePledged',
    'StarSystem', 'SystemAddress', 'StationName', 'MarketID', 'Docked',
    'ControllingPower', 'PowerplayState', 'Type', 'Type_Localised', 'Count',
    'MeritsGained', 'TotalMerits', 'PilotName', 'PilotName_Localised',
    'Target', 'Target_Localised', 'Ship', 'Ship_Localised', 'TotalReward',
    'VictimFaction', 'TargetLocked', 'ScanStage', 'Name', 'Name_Localised', 'Reward',
}


class PowerplayImportConflict(ValueError):
    pass


def create_schema(con):
    statements = '''
    CREATE TABLE pp2_sources (
        id INTEGER PRIMARY KEY, commander_id INTEGER NOT NULL REFERENCES commanders(id),
        source_key TEXT NOT NULL, started_at TEXT NOT NULL,
        UNIQUE(commander_id,source_key), UNIQUE(commander_id,id));
    CREATE TABLE pp2_import_checkpoints (
        commander_id INTEGER NOT NULL, journal_path TEXT NOT NULL, source_id INTEGER NOT NULL,
        signature TEXT NOT NULL, processed_offset INTEGER NOT NULL CHECK(processed_offset>=0),
        source_line INTEGER NOT NULL CHECK(source_line>=0), prefix_hash TEXT NOT NULL,
        parser_version INTEGER NOT NULL, context_json TEXT NOT NULL,
        PRIMARY KEY(commander_id,journal_path),
        FOREIGN KEY(commander_id,source_id) REFERENCES pp2_sources(commander_id,id));
    CREATE TABLE pp2_events (
        commander_id INTEGER NOT NULL, source_id INTEGER NOT NULL,
        source_line INTEGER NOT NULL CHECK(source_line>0), source_offset INTEGER NOT NULL,
        timestamp_utc TEXT NOT NULL, event_type TEXT NOT NULL, content_hash TEXT NOT NULL,
        facts_json TEXT NOT NULL, context_json TEXT NOT NULL,
        is_fact INTEGER NOT NULL CHECK(is_fact IN (0,1)),
        PRIMARY KEY(commander_id,source_id,source_line),
        FOREIGN KEY(commander_id,source_id) REFERENCES pp2_sources(commander_id,id));
    CREATE INDEX pp2_events_day ON pp2_events(commander_id,timestamp_utc);
    CREATE TABLE pp2_history_policy (
        commander_id INTEGER PRIMARY KEY REFERENCES commanders(id),
        history_from_utc TEXT NOT NULL, suppressed_before_utc TEXT NOT NULL DEFAULT '',
        revision INTEGER NOT NULL DEFAULT 0);
    CREATE TABLE pp2_merit_state (
        commander_id INTEGER PRIMARY KEY REFERENCES commanders(id),
        power TEXT NOT NULL, total_merits INTEGER NOT NULL CHECK(total_merits>=0),
        timestamp_utc TEXT NOT NULL, source_id INTEGER NOT NULL, source_line INTEGER NOT NULL,
        source_order TEXT NOT NULL,
        FOREIGN KEY(commander_id,source_id) REFERENCES pp2_sources(commander_id,id));
    '''
    for statement in statements.split(';'):
        if statement.strip():
            con.execute(statement)


def utc(value):
    at = value if isinstance(value, datetime) else timestamp(value)
    return at.astimezone(timezone.utc).isoformat(timespec='microseconds').replace('+00:00', 'Z') if at else None


def day_bounds(day, zone=None):
    def boundary(value):
        local = datetime.combine(value, time.min)
        return utc(local.replace(tzinfo=zone) if zone is not None else local.astimezone())
    return boundary(day), boundary(day + timedelta(days=1))


def packed(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))


def signature(path):
    s = path.stat()
    return packed([s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns])


def _checkpoint(con, cid, path):
    con.row_factory = sqlite3.Row
    row = con.execute('SELECT * FROM pp2_import_checkpoints WHERE commander_id=? AND journal_path=?',
                      (cid, str(path))).fetchone()
    return dict(row) if row else None


def _merit_record(cid, sid, seq, source_start, source_key, event):
    """Both journal snapshots are absolute totals; gains are never accumulated."""
    field = {'Powerplay': 'Merits', 'PowerplayMerits': 'TotalMerits'}.get(event.get('event'))
    total = amount(event.get(field)) if field else None
    stamp = utc(event.get('timestamp'))
    power = event.get('Power')
    if total is None or stamp is None or not isinstance(power, str) or not power.strip():
        return None
    order = source_start + '|' + source_key + '|' + str(seq).zfill(20)
    return (cid, power.strip(), total, stamp, sid, seq, order)


def _store_merit_record(con, record):
    return con.execute('''INSERT INTO pp2_merit_state VALUES(?,?,?,?,?,?,?)
        ON CONFLICT(commander_id) DO UPDATE SET power=excluded.power,total_merits=excluded.total_merits,
        timestamp_utc=excluded.timestamp_utc,source_id=excluded.source_id,source_line=excluded.source_line,
        source_order=excluded.source_order
        WHERE excluded.timestamp_utc>pp2_merit_state.timestamp_utc
           OR (excluded.timestamp_utc=pp2_merit_state.timestamp_utc
               AND excluded.source_order>pp2_merit_state.source_order)''', record).rowcount


def reconcile_merit_totals(db):
    """One-time, backed-up projection repair; never reimport or rewrite history."""
    with db._connect() as con:
        con.execute('BEGIN IMMEDIATE')
        if con.execute('PRAGMA user_version').fetchone()[0] != 23:
            return 0
        if con.execute('SELECT 1 FROM app_meta WHERE key=?', (MERIT_RECONCILIATION_KEY,)).fetchone():
            return 0
        current = {r[0]: tuple(r) for r in con.execute('SELECT * FROM pp2_merit_state')}
        latest = dict(current)
        for cid, sid, seq, start, key, facts in con.execute('''
                SELECT e.commander_id,e.source_id,e.source_line,s.started_at,s.source_key,e.facts_json
                FROM pp2_events e JOIN pp2_sources s
                  ON s.commander_id=e.commander_id AND s.id=e.source_id
                WHERE e.event_type IN ('Powerplay','PowerplayMerits')'''):
            event = json.loads(facts)
            record = _merit_record(cid, sid, seq, start, key, event)
            old = latest.get(cid)
            if record and (old is None or (record[3], record[6]) > (old[3], old[6])):
                latest[cid] = record
        changes = [record for cid, record in latest.items() if record != current.get(cid)]
        if changes:
            # Use the existing SQLite backup + integrity-check strategy before
            # changing derived data. A failure rolls back the marker as well.
            db._create_migration_backup(23)
            for record in changes:
                _store_merit_record(con, record)
        con.execute('INSERT INTO app_meta(key,value) VALUES(?,?)', (MERIT_RECONCILIATION_KEY, 'complete'))
        return len(changes)


def sync(db, sessions, *, day=None, zone=None):
    """Same entry point for startup, archive and live; only PP2 cursors advance."""
    floor, _ = day_bounds(day or local_today(), zone)
    inserted = 0
    # The index can contain thousands of old sessions. Avoid opening a SQLite
    # connection per excluded journal on every live refresh.
    with db._connect() as con:
        floors = dict(con.execute('SELECT commander_id,history_from_utc FROM pp2_history_policy'))
        known_paths = set(con.execute('SELECT commander_id,journal_path FROM pp2_import_checkpoints'))
    for session in sessions:
        cid, fid = session.get('commander_id'), session.get('fid_seen')
        if session.get('attribution_status') != 'identified' or cid is None or not fid:
            continue
        path = Path(session['journal_file']).resolve()
        try:
            stat = path.stat()
        except FileNotFoundError:
            # Rotation/archive cleanup cannot erase persisted history or block
            # the remaining sources from advancing.
            continue
        last = utc(session.get('last_event_at'))
        if (cid, str(path)) not in known_paths and last and last < floors.get(cid, floor):
            if session.get('file_size') == stat.st_size and session.get('modified_ns') == stat.st_mtime_ns:
                continue
        with db._connect() as con:
            owner = con.execute('SELECT fid FROM commanders WHERE id=?', (cid,)).fetchone()
            if owner is None or owner[0] != fid:
                raise PowerplayImportConflict('PP2 commander/FID mismatch')
            con.execute('INSERT OR IGNORE INTO pp2_history_policy(commander_id,history_from_utc) VALUES(?,?)', (cid, floor))
            policy = con.execute('SELECT history_from_utc FROM pp2_history_policy WHERE commander_id=?', (cid,)).fetchone()[0]
            old = _checkpoint(con, cid, path)
        before = signature(path)
        if old and old['signature'] == before and old['parser_version'] == PARSER_VERSION:
            continue
        stat = path.stat()
        if (old is None and last and last < policy and session.get('file_size') == stat.st_size
                and session.get('modified_ns') == stat.st_mtime_ns):
            continue
        raw = path.read_bytes()
        if signature(path) != before:
            raise OSError('PP2 journal changed during read; retry')
        end = raw.rfind(b'\n') + 1
        # Verify the whole consumed prefix. Changed/truncated journals must not
        # masquerade as appends, even when inode and the outer 4 KiB are unchanged.
        if old and (end < old['processed_offset'] or hashlib.sha256(raw[:old['processed_offset']]).hexdigest() != old['prefix_hash']):
            raise PowerplayImportConflict('PP2 journal replaced or truncated: ' + str(path))
        if not end:
            continue
        first = json.loads(raw.splitlines()[0])
        # Fileheader includes the journal part. Paths and filenames are not
        # identity: copied or renamed journals must deduplicate as well.
        part = amount(first.get('part')) or 1
        source_key = str(part).zfill(20) + ':' + hashlib.sha256(packed([fid, first]).encode()).hexdigest()
        start = old['processed_offset'] if old and old['parser_version'] == PARSER_VERSION else 0
        line_no = old['source_line'] if start else 0
        context = json.loads(old['context_json']) if start else {}
        last_time = context.get('last_time')
        sequence = context.get('sequence', 0)
        state = PowerplayState(power=context.get('power', ''), system=context.get('system', {}), station=context.get('station', ''))
        rows, identities = [], {str(fid)} if old else set()
        offset = start
        for line in raw[start:end].splitlines(keepends=True):
            position = offset
            offset += len(line)
            line_no += 1
            try:
                event = json.loads(line)
                if not isinstance(event, dict):
                    raise ValueError('Not an event')
            except (ValueError, UnicodeError):
                event = {'event': 'InvalidJournalLine'}
            if event.get('event') in ('Commander', 'LoadGame') and event.get('FID'):
                identities.add(str(event['FID']))
            state._apply(event)
            context = dict(power=state.power, system=state.system, station=state.station, sequence=sequence)
            # Invalid timestamps become a barrier at the last known time. The
            # original timestamp remains absent/invalid in facts, never invented.
            stamp = utc(event.get('timestamp')) or last_time
            if stamp:
                context['last_time'] = stamp
                last_time = stamp
            if event.get('event') not in NOISE and stamp:
                sequence += 1
                context['sequence'] = sequence
                fact = event.get('event') in FACTS or (event.get('event') == 'ShipTargeted'
                       and event.get('TargetLocked') is True and event.get('ScanStage') == 3)
                payload = {k: v for k, v in event.items() if k in FIELDS}
                rows.append((line_no, position, stamp, str(event.get('event') or 'InvalidJournalLine'),
                             hashlib.sha256(packed(event).encode()).hexdigest(), packed(payload), packed(context), int(fact)))
        if identities != {str(fid)}:
            raise PowerplayImportConflict('PP2 commander identity is not unique: ' + str(path))
        prefix = hashlib.sha256(raw[:end]).hexdigest()
        with db._connect() as con:
            con.execute('BEGIN IMMEDIATE')
            if _checkpoint(con, cid, path) != old or signature(path) != before:
                raise OSError('Concurrent PP2 import; retry')
            con.execute('INSERT OR IGNORE INTO pp2_sources(commander_id,source_key,started_at) VALUES(?,?,?)',
                        (cid, source_key, utc(first.get('timestamp')) or ''))
            source = con.execute('SELECT id,started_at FROM pp2_sources WHERE commander_id=? AND source_key=?', (cid, source_key)).fetchone()
            sid, source_start = source
            if old and sid != old['source_id']:
                raise PowerplayImportConflict('PP2 source identity changed')
            # A moved/copied file must match already consumed bytes of its source.
            for prior in con.execute('SELECT processed_offset,prefix_hash FROM pp2_import_checkpoints WHERE commander_id=? AND source_id=?', (cid, sid)):
                if end < prior[0] or hashlib.sha256(raw[:prior[0]]).hexdigest() != prior[1]:
                    raise PowerplayImportConflict('Conflicting copy of PP2 source')
            lower, suppressed = con.execute('SELECT history_from_utc,suppressed_before_utc FROM pp2_history_policy WHERE commander_id=?', (cid,)).fetchone()
            changed = 0
            for record in rows:
                seq, pos, stamp, kind, digest, facts, ctx, is_fact = record
                existing = con.execute('SELECT content_hash FROM pp2_events WHERE commander_id=? AND source_id=? AND source_line=?', (cid, sid, seq)).fetchone()
                if existing and existing[0] != digest:
                    raise PowerplayImportConflict('Conflicting PP2 event at the same source line')
                if stamp < lower:
                    continue
                if stamp >= suppressed:
                    changed += con.execute('INSERT OR IGNORE INTO pp2_events VALUES(?,?,?,?,?,?,?,?,?,?)',
                                           (cid, sid, *record)).rowcount
                e = json.loads(facts)
                merit_record = _merit_record(cid, sid, seq, source_start, source_key, e)
                if merit_record is not None:
                    _store_merit_record(con, merit_record)
            con.execute('''INSERT INTO pp2_import_checkpoints VALUES(?,?,?,?,?,?,?,?,?)
                ON CONFLICT(commander_id,journal_path) DO UPDATE SET source_id=excluded.source_id,signature=excluded.signature,
                processed_offset=excluded.processed_offset,source_line=excluded.source_line,prefix_hash=excluded.prefix_hash,
                parser_version=excluded.parser_version,context_json=excluded.context_json''',
                (cid, str(path), sid, before, end, line_no, prefix, PARSER_VERSION, packed(context)))
            if changed:
                con.execute('UPDATE pp2_history_policy SET revision=revision+1 WHERE commander_id=?', (cid,))
            inserted += changed
    return inserted


def read_day(db, cid, day, *, zone=None):
    lower, upper = day_bounds(day, zone)
    with db._connect() as con:
        rows = _day_rows(con, cid, lower, upper)
    return _decode_day(rows)


def _day_rows(con, cid, lower, upper):
    return con.execute('''SELECT e.source_id,e.facts_json,e.context_json FROM pp2_events e
            JOIN pp2_sources s ON s.id=e.source_id AND s.commander_id=e.commander_id
            WHERE e.commander_id=? AND e.timestamp_utc>=? AND e.timestamp_utc<?
            ORDER BY s.started_at,s.source_key,e.source_line''', (cid, lower, upper)).fetchall()


def _decode_day(rows):
    result = PowerplayChronicle()
    previous = last_sequence = None
    for sid, facts, context in rows:
        if sid != previous:
            result.reset_candidates()
            previous = sid
        e, c = json.loads(facts), json.loads(context)
        sequence = c.get('sequence')
        if last_sequence is not None and sequence != last_sequence + 1:
            result.reset_candidates()
        result.apply(e, system=c.get('system', {}).get('StarSystem', ''), station=c.get('station', ''), power=c.get('power', ''))
        last_sequence = sequence
    return result


class DayCache:
    """One view's current day; no writes, persistent revisions or polling timer.

    data_version is meaningful only on the same connection. Every commit on
    another connection invalidates the probe, including in-place corrections.
    Compare ordered raw rows before replaying: unrelated commits need no replay.
    """

    def __init__(self):
        self.close()

    def close(self):
        con = getattr(self, '_con', None)
        if con is not None:
            con.close()
        self._con = self._binding = self._request = None
        self._content_key = self._rows = self._chronicle = self._token = None

    def load(self, db, cid, day, fid=None):
        path = getattr(db, 'path', None)
        if not isinstance(path, (str, Path)):
            self.close()
            return db.powerplay_day(cid, day), None
        try:
            path = Path(path).resolve()
            stat = path.stat()
            # Inode identity detects replacement; size/mtime never prove validity.
            binding = (db, path, stat.st_dev, stat.st_ino)
            if binding != self._binding:
                self.close()
                self._con = sqlite3.connect(path.as_uri() + '?mode=ro', uri=True)
                self._binding = binding
            bounds = day_bounds(day)
            revision = self._con.execute('PRAGMA data_version').fetchone()[0]
            request = (cid, fid, bounds, revision)
            if request != self._request:
                identity = self._con.execute('SELECT fid FROM commanders WHERE id=?', (cid,)).fetchone()
                key = (cid, fid, identity, bounds)
                rows = _day_rows(self._con, cid, *bounds)
                if key != self._content_key or rows != self._rows:
                    chronicle = _decode_day(rows)
                    self._content_key, self._rows, self._chronicle = key, rows, chronicle
                    self._token = object()
                # Bind to the revision BEFORE reading. A concurrent commit can
                # cause one extra reload next time, never a falsely fresh cache.
                self._request = request
            return self._chronicle, self._token
        except (OSError, sqlite3.Error):
            # If the probe cannot establish validity, use the existing reader.
            self.close()
            return db.powerplay_day(cid, day), None


def delete_preview(db, cid, days=None, *, day=None, zone=None, now=None):
    if days not in (None, 7, 30):
        raise ValueError('Unsupported PP2 retention period')
    cutoff = utc((now or datetime.now(timezone.utc)) + timedelta(microseconds=1)) if days is None else day_bounds((day or local_today())-timedelta(days=days-1), zone)[0]
    with db._connect() as con:
        if days is None:
            latest = con.execute('SELECT MAX(timestamp_utc) FROM pp2_events WHERE commander_id=?', (cid,)).fetchone()[0]
            if latest and latest >= cutoff:
                cutoff = utc(timestamp(latest) + timedelta(microseconds=1))
        revision = con.execute('SELECT revision FROM pp2_history_policy WHERE commander_id=?', (cid,)).fetchone()
        # Older and current imports retain MarketSell as is_fact=0. Derive the
        # display fact without rewriting history or advancing import cursors.
        stamps = [stamp for stamp, fact, facts in con.execute(
            '''SELECT timestamp_utc,is_fact,facts_json FROM pp2_events
               WHERE commander_id=? AND timestamp_utc<? AND (is_fact=1 OR event_type='MarketSell')''',
            (cid, cutoff)) if fact or is_rare_sale(json.loads(facts))]
        first, last = con.execute('SELECT MIN(timestamp_utc),MAX(timestamp_utc) FROM pp2_events WHERE commander_id=? AND timestamp_utc<?', (cid,cutoff)).fetchone()
    dates = {timestamp(s).astimezone(zone).date() for s in stamps}
    return dict(commander_id=cid, cutoff=cutoff, revision=revision[0] if revision else None,
                events=len(stamps), days=len(dates), has_history=first is not None,
                first=timestamp(first).astimezone(zone).date().isoformat() if first else '',
                last=timestamp(last).astimezone(zone).date().isoformat() if last else '')


def delete_history(db, cid, preview):
    if preview['commander_id'] != cid:
        raise ValueError('PP2 commander mismatch')
    with db._connect() as con:
        con.execute('BEGIN IMMEDIATE')
        row = con.execute('SELECT revision FROM pp2_history_policy WHERE commander_id=?', (cid,)).fetchone()
        if row is None or row[0] != preview['revision']:
            raise ValueError('PP2 history changed; request confirmation again')
        con.execute('DELETE FROM pp2_events WHERE commander_id=? AND timestamp_utc<?', (cid, preview['cutoff']))
        con.execute('UPDATE pp2_history_policy SET suppressed_before_utc=MAX(suppressed_before_utc,?),revision=revision+1 WHERE commander_id=?',
                    (preview['cutoff'], cid))
