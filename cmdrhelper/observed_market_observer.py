"""From-now-only Market observer on JournalWatcher's existing live notifications."""
from copy import deepcopy
from datetime import timedelta
import json
import logging
from pathlib import Path
import time

from .journal_files import journal_files, journal_sort_key
from .live_journal import open_journal
from .station_context import embark_station_context
from .odyssey_sidecars import signature
from .observed_market_cache import (
    ObservedMarketCache, cache_path, normalize_observation, read_market,
    timestamp, utcnow, valid_fid, _json,
)

logger = logging.getLogger(__name__)
MAX_JOURNAL_BYTES = 64 * 1024 * 1024
MAX_LINE_BYTES = 4 * 1024 * 1024
RETRY_SECONDS = 15

# Every event handled by _event(), including context resets and departures.
MARKET_CONTEXT_EVENTS = frozenset((
    'Commander', 'LoadGame', 'Shutdown', 'Fileheader', 'Location', 'FSDJump',
    'CarrierJump', 'Docked', 'Embark', 'Undocked', 'StartJump',
    'SupercruiseEntry', 'Market',
))


def _irrelevant_journal_event(raw):
    """Classify only; never pass tolerantly decoded fields to the observer.

    Keep all top-level event values so duplicate event keys cannot disguise a
    context change. Tuples distinguish JSON objects from arrays. Broken syntax
    or a missing/ambiguous event identity must invalidate trusted context.
    """
    def event_names(pairs):
        return tuple(value for key, value in pairs if key == 'event')

    def reject_constant(value):
        raise ValueError('Non-JSON numeric constant')

    try:
        names = json.loads(raw, object_pairs_hook=event_names, parse_constant=reject_constant)
        return (isinstance(names, tuple) and len(names) == 1
                and isinstance(names[0], str) and bool(names[0])
                and names[0] not in MARKET_CONTEXT_EVENTS)
    except (ValueError, TypeError, OverflowError, RecursionError):
        return False


class ObservedMarketObserver:
    def __init__(self, cache=None, *, clock=utcnow, monotonic=time.monotonic, on_changed=None, use_market_store=False):
        self._cache = cache
        self.use_market_store = use_market_store
        self.writer = None
        self._writes = []
        self._closing = False
        self.on_changed = on_changed
        if cache is not None and on_changed is not None:
            cache.on_changed = on_changed
        self.clock, self.monotonic = clock, monotonic
        self.folder = self.path = self.boundary = None
        self.pending = None
        self.context = {}
        self.last_error = None
        self.armed = False

    @property
    def cache(self):
        if self._cache is None:
            from .market_migration import database_authoritative
            path = cache_path()
            self._cache = ObservedMarketCache(path, clock=self.clock, on_changed=self.on_changed,
                load=not (self.use_market_store and database_authoritative(path.parent / 'markets.db')))
        if self.use_market_store and self.writer is None and not self._closing:
            from .market_writer import MarketWriteWorker
            self._cache.sqlite_writer_enabled = True
            self.writer = MarketWriteWorker(
                self._cache.path, self._cache.path.parent / 'markets.db', clock=self.clock,
                on_loaded=self._cache.install_headers, on_committed=self._cache.apply_committed_header,
                on_status=lambda _: self.on_changed() if self.on_changed is not None else None)
            self._cache.store_writer = self.writer
        return self._cache

    def close(self):
        self._closing = True
        if self.writer is not None:
            return self.writer.close()
        return True

    def _poll_writes(self):
        remaining = []
        for snapshot, future in self._writes:
            if not future.done():
                remaining.append((snapshot, future))
            else:
                try:
                    future.result()
                except Exception as exc:
                    self._diagnose('Market SQLite write failed: ' + str(exc))
                    if not self._closing:
                        remaining.append((snapshot, self.writer.record(snapshot)))
        self._writes = remaining
        if not remaining and self.writer is not None and self.writer.last_error is None:
            self.last_error = None
        return not remaining

    def set_folder(self, folder):
        self.folder = Path(folder) if folder else None
        self.path = self.boundary = self.pending = None
        self.context = {}
        self.armed = False
        self.started_at = self.clock()
        self._offset, self._sig, self._baseline = 0, None, 0
        self._blocked = False
        self._market_stamps = set()
        try:
            # Load/physically prune only our existing cache; never backfill it.
            self.cache.cleanup()
            if self.folder is not None:
                files = journal_files(self.folder)
                if files:
                    self.path = files[-1]
                    self.boundary = journal_sort_key(self.path)
                    self._sig = signature(self.path)
                    self._baseline = self._sig[2]
                self.armed = True
        except OSError as exc:
            self._diagnose(str(exc))

    def _diagnose(self, reason):
        if reason != self.last_error:
            logger.warning('Local market observation rejected: %s', reason)
        self.last_error = reason

    def _event(self, event, live):
        kind = event.get('event')
        if kind in ('Commander', 'LoadGame'):
            fid = event.get('FID')
            if not valid_fid(fid):
                self.context = {}
                self.pending = None
            elif self.context.get('FID') != fid or kind == 'LoadGame':
                self.context = {'FID': fid}
                self.pending = None
            return
        if kind in ('Shutdown', 'Fileheader'):
            self.pending = None
            if kind == 'Shutdown':
                self.context = {}
        if kind in ('Location', 'FSDJump', 'CarrierJump', 'Docked'):
            fid = self.context.get('FID')
            self.context = {'FID': fid} if valid_fid(fid) else {}
            for name in ('StarSystem', 'SystemAddress'):
                if name in event:
                    self.context[name] = event[name]
            if kind == 'Docked' or event.get('Docked') is True:
                for name in ('MarketID', 'StationName', 'StationType'):
                    if name in event:
                        self.context[name] = event[name]
            self.pending = None
        elif kind == 'Embark':
            station = embark_station_context(event, self.context)
            self.pending = None
            if station is not None:
                self.context.update(station)
        elif kind in ('Undocked', 'StartJump', 'SupercruiseEntry'):
            self.pending = None
            self.context = {key: value for key, value in self.context.items() if key == 'FID'}
        elif kind == 'Market':
            self.pending = None
            if not live:
                return
            stamp = timestamp(event.get('timestamp'))
            if stamp in self._market_stamps:
                self._diagnose('Ambiguous repeated Market timestamp')
                return
            self._market_stamps.add(stamp)
            if stamp < self.started_at - timedelta(seconds=1):
                self._diagnose('Market event predates live observation boundary')
                return
            if not valid_fid(self.context.get('FID')):
                self._diagnose('Market event lacks trusted FID')
                return
            self.pending = (deepcopy(event), deepcopy(self.context), self.monotonic() + RETRY_SECONDS)

    def _read_journal(self, path):
        before = signature(path)
        if self.path != path:
            # Only consecutive numbered parts of the SAME session inherit FID.
            same_session = (self.path is not None
                and path.name.rsplit('.', 2)[0] == self.path.name.rsplit('.', 2)[0]
                and journal_sort_key(path)[2] == journal_sort_key(self.path)[2] + 1
                and not self._blocked)
            self.context = self.context if same_session else {}
            self.path, self._sig, self._offset, self._baseline = path, None, 0, 0
            self._blocked, self.pending = False, None
            self._market_stamps.clear()
        if self._blocked:
            # File integrity/size failures require a new file or explicit rearm;
            # isolated bad events only invalidate context and advance the cursor.
            return
        if self._sig is not None and (before[:2] != self._sig[:2] or before[2] < self._offset
                or before[2] < self._sig[2] or before != self._sig and before[2] == self._sig[2]):
            self._blocked, self.pending, self.context = True, None, {}
            self._diagnose('Journal replaced/truncated/rewritten; awaiting new session')
            return
        if before[2] > MAX_JOURNAL_BYTES:
            self._blocked, self.pending, self.context = True, None, {}
            self._diagnose('Active journal exceeds safety limit')
            return
        events = []
        offset = self._offset
        with open_journal(path) as stream:
            stream.seek(offset)
            while True:
                start = stream.tell()
                line = stream.readline()
                if len(line) > MAX_LINE_BYTES:
                    raise ValueError('Journal line exceeds safety limit')
                if not line or not line.endswith(b'\n'):
                    break
                diagnosis = None
                try:
                    event = _json(line)
                    if not isinstance(event, dict):
                        raise ValueError('Invalid journal object')
                except (ValueError, TypeError, OverflowError, RecursionError):
                    if _irrelevant_journal_event(line):
                        event = {}  # No-op; retain context and pending capture.
                        diagnosis = 'Invalid irrelevant journal event skipped for market observation'
                    else:
                        event = None
                        diagnosis = 'Invalid market/context journal event; market context invalidated'
                events.append((event, start >= self._baseline, diagnosis))
                offset = stream.tell()
        if signature(path) != before:
            raise OSError('Journal changed during market capture')
        for event, live, diagnosis in events:
            if diagnosis is not None:
                self._diagnose(diagnosis)
            if event is None:
                self.pending, self.context = None, {}
                continue
            try:
                self._event(event, live)
            except (ValueError, TypeError, OverflowError, RecursionError):
                self.pending, self.context = None, {}
                self._diagnose('Invalid market/context journal event; market context invalidated')
        self._offset, self._sig = offset, before

    def consume(self, paths):
        writes_done = self._poll_writes()
        if self._closing:
            return False
        if not self.armed:
            return writes_done
        candidates = [Path(p) for p in paths if self.boundary is None or journal_sort_key(Path(p)) >= self.boundary]
        if self.path is not None:
            candidates.append(self.path)
        if not candidates:
            return writes_done
        current = max(candidates, key=journal_sort_key)
        try:
            self._read_journal(current)
        except OSError as exc:
            self._diagnose(str(exc))
            return False
        except (ValueError, TypeError, OverflowError, RecursionError) as exc:
            self._blocked, self.pending, self.context = True, None, {}
            self._diagnose(str(exc))
        if self.pending is None:
            return writes_done
        event, context, deadline = self.pending
        if self.monotonic() >= deadline:
            self.pending = None
            self._diagnose('Market capture retry deadline exceeded')
            return writes_done
        try:
            data, sidecar_sig = read_market(current.parent / 'Market.json')
            snapshot = normalize_observation(event, data, fid=context['FID'], context=context,
                                            mtime=sidecar_sig[3] / 1e9, now=self.clock())
            if signature(current) != self._sig or signature(current.parent / 'Market.json') != sidecar_sig:
                raise OSError('Journal/sidecar changed before market commit')
            if self.use_market_store:
                self.cache  # Ensure writer exists before enqueueing.
                self._writes.append((snapshot, self.writer.record(snapshot)))
                self.pending = None
                return False  # Watcher retries until the actual COMMIT completes.
            if not self.cache.put(snapshot):
                self._diagnose('Market cache write rejected: ' + str(self.cache.last_error))
                return False
            self.pending, self.last_error = None, None
            return True
        except (OSError, ValueError, TypeError, OverflowError, RecursionError) as exc:
            self._diagnose(str(exc))
            # Reuse the existing watcher retry flag: no additional timer/poller.
            return False
