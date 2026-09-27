"""One ordered SQLite writer; futures acknowledge COMMIT, never queue admission."""
from concurrent.futures import Future
from copy import deepcopy
import logging
from pathlib import Path
from queue import Queue
from threading import Lock, Thread

from .market_migration import migrate_market_cache, database_authoritative
from .market_store import MarketStore, decode_u64, _datetime
from .observed_market_cache import utcnow

logger = logging.getLogger(__name__)


class MarketWriteWorker:
    def __init__(self, source, destination, *, clock=utcnow, on_loaded=None, on_committed=None, on_status=None):
        self.source, self.destination = Path(source), Path(destination)
        self.clock = clock
        self.on_loaded, self.on_committed = on_loaded, on_committed
        self.on_status = on_status
        self.station_count = 0
        self.authoritative = database_authoritative(self.destination)
        self.last_error = None
        self._failures = {}
        self.status = 'starting'
        self._queue, self._lock = Queue(), Lock()
        self._closed = False
        self._store = None
        self.ready = Future()
        self._queue.put(('initialize', None, self.ready))
        self._thread = Thread(target=self._run, name='MarketStoreWriter', daemon=False)
        self._thread.start()

    def _submit(self, kind, value=None):
        future = Future()
        with self._lock:
            if self._closed:
                raise RuntimeError('Market writer is closing')
            self._queue.put((kind, value, future))
        return future

    def record(self, observation):
        return self._submit('record', deepcopy(observation))

    @property
    def activated(self):
        """Read-side handoff flag; inspecting it never touches the connection."""
        return self._store is not None

    def cleanup(self, *, cancel=None):
        return self._submit('cleanup', cancel)

    def retry_initialization(self):
        return self._submit('initialize')

    def close(self):
        """Stop admission, drain accepted work, join; do not discard queued writes.

        Call outside callbacks. The application shutdown may wait for disk I/O.
        Failures remain on their futures and last_error; no false success.
        """
        with self._lock:
            if not self._closed:
                self._closed = True
                self._queue.put(None)
        self._thread.join()
        if self.last_error is not None:
            logger.error('Market writer stopped with unconfirmed work: %s', self.last_error)
        return self.last_error is None

    def _notify(self, callback, value):
        if callback is not None:
            try:
                callback(value)
            except Exception:
                # Persistence success must not turn into a retry because a
                # notification subscriber failed after COMMIT.
                logger.exception('Market commit notification failed')

    def _initialize(self):
        if self._store is not None:
            return
        self.status = 'migrating'
        migrate_market_cache(self.source, self.destination, clock=self.clock)
        self.authoritative = True
        store = MarketStore(self.destination, clock=self.clock)
        try:
            # Only identity/age headers for the docked recommendation origin.
            # Build away from GUI, then publish one immutable-by-convention dict.
            projection, after = {}, 0
            while True:
                rows = store._con.execute('''SELECT o.* FROM current_markets c JOIN market_observations o
                    ON o.observation_id=c.observation_id
                    WHERE c.observation_id>? ORDER BY c.observation_id LIMIT 500''',
                    (after,)).fetchall()
                if not rows:
                    break
                for row in rows:
                    value = dict(fid=row['fid'], market_id=decode_u64(row['market_id']),
                        source=row['source'], station_name=row['station_name'],
                        system_name=row['system_name'], observed_at=_datetime(row['observed_at']).isoformat())
                    if row['system_address'] is not None:
                        value['system_address'] = decode_u64(row['system_address'])
                    if row['station_type'] is not None:
                        value['station_type'] = row['station_type']
                    projection[value['market_id']] = value
                after = rows[-1]['observation_id']
            self.station_count = store.storage_stats()[0]
            self._store = store
            self._notify(self.on_loaded, projection)
            self.status = 'active'
        except BaseException:
            store.close()
            raise

    def _run(self):
        try:
            while True:
                item = self._queue.get()
                if item is None:
                    break
                kind, value, future = item
                key = (kind,)
                if kind == 'record' and isinstance(value, dict):
                    key += tuple(repr(value.get(k)) for k in ('fid', 'market_id', 'observed_at'))
                # Explicit cancellation before execution is not a saved observation.
                if not future.set_running_or_notify_cancel():
                    # Cancellation before execution is explicit, never saved.
                    continue
                try:
                    self._initialize()
                    if kind == 'record':
                        result = self._store.record_observation(value)
                        self.station_count = self._store.storage_stats()[0]
                        if result.current_changed:
                            self._notify(self.on_committed, value)
                    elif kind == 'cleanup':
                        result = self._store.cleanup(cancel=value)
                        # SQLite 3.45 optimize is opportunistic and bounded by
                        # analysis_limit, only after explicitly scheduled maintenance.
                        self._store._con.execute('PRAGMA analysis_limit=400')
                        self._store._con.execute('PRAGMA optimize')
                    else:
                        # Explicit startup maintenance, after verified activation.
                        result = self._store.cleanup()
                    self._failures.pop(key, None)
                    # Initialization may also have recovered on a record retry.
                    self._failures.pop(('initialize',), None)
                    self.last_error = next(iter(self._failures.values()), None)
                    self.status = 'write_error' if self.last_error else 'active'
                    self._notify(self.on_status, None)
                    future.set_result(result)
                except Exception as exc:
                    self.authoritative = self.authoritative or database_authoritative(self.destination)
                    self._failures[key] = str(exc)
                    self.last_error = str(exc)
                    self.status = 'write_error' if self._store is not None else 'migration_error'
                    logger.warning('Local market persistence failed: %s', exc)
                    self._notify(self.on_status, None)
                    future.set_exception(exc)
        finally:
            if self._store is not None:
                self._store.close()
            self.status = 'closed'
