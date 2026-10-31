"""Serialized source ingestion, independent of the selected commander view."""
from pathlib import Path
from copy import deepcopy
import hashlib
import json
from .journal_catchup import capture, catch_up, load_sessions, validate_input
from .journal_index import scan_journal_folder


class SourceProcessor:
    def __init__(self, database, path):
        self.database = database
        self.path = Path(path)
        self.context = None
        self.sessions = []
        self.initialized = False
        self.repair_results = []
        self._projection = None
        self.inventory_kinds = None
        self._inventory_retry = False

    @staticmethod
    def _projection_key(rows):
        """Bind a completed projection to its identity, cursors and input files."""
        key = []
        try:
            for row in rows:
                stat = Path(row['journal_file']).stat()
                key.append((row['journal_file'], row.get('commander_id'), row.get('fid_seen'),
                    row.get('attribution_status'), row.get('last_read_offset'),
                    stat.st_dev, stat.st_ino, stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns))
        except OSError:
            return None
        return tuple(key)

    def projection_for(self, rows):
        """Copy the worker result only while all its commander inputs still match."""
        if self._projection is None or self._projection_key(rows) != self._projection[0]:
            return None
        data = deepcopy(self._projection[1])
        data['journal_files'] = len(rows)
        return data

    def process(self, *, cancel=None, enqueue_fids=(), progress=None):
        from .inventory_invalidation import KINDS, batch_kinds
        previous_sessions = deepcopy(self.sessions)
        full_inventory = not self.initialized or self._inventory_retry
        # A failure can follow committed files. Keep recovery conservative even
        # when the retry has no new applied_events for those committed bytes.
        self._inventory_retry = True
        self.inventory_kinds = set(KINDS)
        # Never publish a previous result after a partial read or failed commit.
        self._projection = None
        projection = None
        if progress:
            progress('startup.phase.preparing')
        if not self.path.is_dir():
            raise FileNotFoundError(self.path)
        if self.context is None:
            from .journal_prefix import verify_previous
            verify_previous(self.database, self.path)
            known_source = any(Path(r['journal_file']).parent == self.path and r.get('last_read_offset')
                               for r in load_sessions(self.database))
            self.context = capture(self.database, self.path, cancel=cancel)
            baseline_key = 'inara_source_baseline/v1/' + hashlib.sha256(str(self.path.resolve()).encode()).hexdigest()
            with self.database._connect() as con:
                saved = con.execute('SELECT value FROM app_meta WHERE key=?', (baseline_key,)).fetchone()
            if saved:
                self.context['inara_baselines'] = json.loads(saved[0])
            elif not known_source:
                floors = {}
                for name, baseline in self.context['baseline'].items():
                    with Path(name).open('rb') as handle:
                        raw = handle.read(baseline['signature'][2])
                    floors[name] = raw.rfind(b'\n') + 1
                self.context['inara_baselines'] = floors
                # Persist the opt-in boundary before importing history. A crash
                # halfway through initialization must not turn the remaining
                # historical files into a new upload backlog on restart.
                with self.database._connect() as con:
                    con.execute('INSERT INTO app_meta(key,value) VALUES(?,?)', (baseline_key, json.dumps(floors)))
        self.context['applied_events'] = []
        if not self.initialized:
            # Capture BEFORE the index/import can modify metadata. Existing
            # replacement guards and the archive/catch-up handoff stay intact.
            if progress:
                progress('startup.phase.index')
            sessions = scan_journal_folder(self.database, self.path,
                validate_input=lambda path: validate_input(self.context, path), cancel=cancel,
                progress_callback=(lambda _current, _total, name: progress('startup.phase.index', str(name)))
                    if progress else None)
            if progress:
                progress('startup.phase.history')
            from .startup_repairs import run_startup_repairs
            self.repair_results = run_startup_repairs(self.database.path)
            from .station_pad_store import read_local
            read_local(self.database.path, self.path, cancel=cancel)
            for cid in {row['commander_id'] for row in sessions if row.get('commander_id') is not None}:
                for feature, method in [('surface_mining', 'backfill_surface_mining'),
                        ('body_scan_attributes', 'backfill_body_scan_attributes'),
                        ('mercenary_credits', 'backfill_mercenary_credits')]:
                    if self.database.commander_state_repair_needed(cid, feature):
                        getattr(self.database, method)(cid)
                if self.database.commander_state_repair_needed(cid, 'unsold'):
                    self.database.repair_commander_state(self.path, load_sessions(self.database), cid, features=['unsold'])
                if self.database.commander_state_repair_needed(cid, 'position_gap'):
                    from .state import AppState
                    latest = next((r for r in reversed(sessions) if r.get('commander_id') == cid
                                   and r.get('attribution_status') == 'identified'), None)
                    if latest:
                        readable, position = AppState._read_latest_position_event(latest)
                        if readable:
                            self.database.repair_commander_position_gap(cid, Path(latest['journal_file']), position or {})
            self.database.import_journal_archive(self.path,
                validate_input=lambda path: validate_input(self.context, path),
                progress_callback=(lambda _current, _total, name: progress('startup.phase.history', str(name)))
                    if progress else None)
            self.initialized = True
        if progress:
            progress('startup.phase.history')
        self.sessions = catch_up(self.database, self.context, cancel=cancel,
            enqueue_fids=enqueue_fids, independent_sources=True)
        self.database.sync_powerplay(self.sessions)
        if self.sessions and self.sessions[-1].get('attribution_status') == 'identified':
            from .journal_reader import read_latest_state, verified_live_metadata
            from .startup_runtime import JournalPending
            view_rows = deepcopy(self.sessions)
            latest = self.sessions[-1]
            owned_rows = [row for row in self.sessions
                if row.get('commander_id') == latest['commander_id']
                and row.get('fid_seen') == latest['fid_seen']
                and row.get('attribution_status') == 'identified']
            projection_key = self._projection_key(owned_rows)
            data = read_latest_state(self.path, indexed_sessions=view_rows, powerplay_history=False)
            current = view_rows[-1]
            if (current.get('attribution_status') != 'identified'
                    or data.get('commander_fid') != self.sessions[-1].get('fid_seen')):
                raise JournalPending('journal_identity_changed')
            complete = current['last_complete_line_offset']
            if complete != self.sessions[-1]['last_read_offset']:
                raise JournalPending('journal_changed_during_read')
            verified_live_metadata(Path(current['journal_file']), current, complete)
            # The existing snapshot projection (FSS, geology, codex, global
            # body facts) is retryable independently of the committed delta.
            # It must run for background sources too, not only the viewed one.
            self.database.store_snapshot(data, commander_id=current['commander_id'])
            if projection_key is not None and projection_key == self._projection_key(owned_rows):
                projection = (projection_key, data)
        # Historical calibration and new sales remain explicitly commander
        # scoped, never inferred from the selected GUI commander.
        from .journal_learning import learn
        events = self.context.get('applied_events', [])
        for cid, fid in {(r['commander_id'], r['fid_seen']) for r in self.sessions
                         if r.get('attribution_status') == 'identified' and r.get('commander_id') is not None}:
            kinds = set()
            if any(f == fid and e.get('event') == 'SellOrganicData' for _, f, e in events):
                kinds.add('bio')
            if any(f == fid and e.get('event') in ('SellExplorationData', 'MultiSellExplorationData') for _, f, e in events):
                kinds.add('cartography')
            if kinds:
                learn(self.database, self.path, cid, kinds, self.sessions)
        self.context['current'] = self.sessions[-1]['journal_file'] if self.sessions else None
        self._projection = projection
        self.inventory_kinds = batch_kinds(previous_sessions, self.sessions,
            self.context.get('applied_events', []), full=full_inventory,
            indexed=load_sessions(self.database) if not full_inventory else None)
        self._inventory_retry = False
        return self.sessions
