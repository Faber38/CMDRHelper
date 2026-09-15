"""Serial historical learning; immutable requests and queued GUI completion."""
from copy import copy, deepcopy
import logging

from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal

from .valuation import calculate_body_values

logger = logging.getLogger(__name__)


def learn(database, folder, commander_id, kinds, sessions):
    results = {}
    for kind in kinds:
        try:
            if kind == 'bio':
                results[kind] = database.learn_bio_values_from_journals(
                    folder, commander_id=commander_id, indexed_sessions=sessions)
            elif kind == 'cartography':
                results[kind] = database.learn_cartography_values_from_journals(
                    folder, commander_id=commander_id, indexed_sessions=sessions,
                    valuation_func=calculate_body_values)
        except Exception:
            logger.exception('Historical %s learning failed', kind)
    return results


def context(state):
    sessions = getattr(state, '_journal_index_sessions', None) or ()
    live = sessions[-1] if sessions else {}
    return (str(state.database.path), str(state.journal_folder), state.commander_id,
            state.commander_fid, state.system_address, state.body, state.last_timestamp,
            getattr(state, "system", ""),
            live.get('journal_file'), live.get('last_read_offset'),
            live.get('fid_seen'), live.get('attribution_status'), id(sessions), len(sessions),
            getattr(state, '_database_import_running', False),
            getattr(state, '_journal_catchup_running', False))


class _Signals(QObject):
    finished = Signal(object, object, object)


class _Learn(QRunnable):
    def __init__(self, database, folder, cid, kinds, sessions, token, signals):
        super().__init__()
        self.database, self.folder, self.cid = database, folder, cid
        self.kinds, self.sessions, self.token, self.signals = kinds, sessions, token, signals

    def run(self):
        result = None
        try:
            result = learn(self.database, self.folder, self.cid, self.kinds, self.sessions)
        except Exception:
            logger.exception('Historical journal learning failed')
        self.signals.finished.emit(self.token, self.kinds, result)


class JournalLearningController(QObject):
    ready = Signal(object)

    def __init__(self, state):
        super().__init__(state)
        self.state = state
        self.pool = QThreadPool.globalInstance()
        self.signals = _Signals(self)
        self.signals.finished.connect(self._finished)
        self.running = False
        self.pending = None
        self.completed = None
        self.active = None
        self.refresh_pending = False

    def request(self, kinds):
        token = context(self.state)
        signature = (token, frozenset(kinds))
        if self.completed and self.completed[0][:4] != token[:4]:
            self.refresh_pending = False
        if signature == self.completed or signature == self.active:
            return
        if self.pending and self.pending[0] == token:
            kinds = set(kinds) | self.pending[1]
        self.pending = (token, frozenset(kinds), deepcopy(self.state._journal_index_sessions or []))
        self._start()

    def _start(self):
        if self.running or self.pending is None:
            return
        token, kinds, sessions = self.pending
        self.pending = None
        # A shallow copy carries configuration/caches, never a SQLite connection.
        # Every learner opens its own connections and gets an explicit commander ID.
        database = copy(self.state.database)
        if token[:4] != context(self.state)[:4]:
            return
        self.running = True
        self.active = (token, kinds)
        self.pool.start(_Learn(database, token[1], token[2], kinds, sessions, token, self.signals))

    def _finished(self, token, kinds, result):
        self.running = False
        self.active = None
        if result is not None:
            if set(result) == set(kinds):
                self.completed = (token, kinds)
            current = context(self.state)
            changed = any(item.get('values_changed') or item.get('sales_stored')
                          for item in result.values())
            if token == current:
                if self.refresh_pending:
                    result = {**result, 'refresh': {'values_changed': 1}}
                    self.refresh_pending = False
                self.ready.emit(result)
            elif token[:4] == current[:4] and changed:
                # A fresh job validates the new session/location before asking
                # AppState to reread its own current values from the database.
                self.refresh_pending = True
                self.request(kinds)
        self._start()
