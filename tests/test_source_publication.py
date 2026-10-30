"""Committed local publication while the serialized transfer is still running."""
from pathlib import Path
import threading
import time
import unittest
from unittest.mock import patch
import test_source_manager
from test_import_catchup import append, event
from cmdrhelper.edsm_system_status import EdsmSystemStatus
from cmdrhelper import startup_runtime
from cmdrhelper.source_transfers import transfer as real_transfer


class PublicationTests(unittest.TestCase):
    setUpClass = classmethod(test_source_manager.ManagerTests.setUpClass.__func__)
    setUp = test_source_manager.ManagerTests.setUp
    shutdown = test_source_manager.ManagerTests.shutdown
    drain = test_source_manager.ManagerTests.drain

    def wait(self, condition):
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            self.app.processEvents()
            if condition():
                return
            time.sleep(.005)
        self.fail('condition timed out')

    def runtime(self):
        r = next(iter(self.state.sources.runtimes.values()))
        self.state.select_viewed_commander(r.processor.sessions[-1]['commander_id'])
        return r

    def jump(self, runtime, name, address):
        append(Path(runtime.processor.sessions[-1]['journal_file']),
               event('FSDJump', StarSystem=name, SystemAddress=address))
        runtime.watcher.check_now()

    def status(self, fetch):
        status = EdsmSystemStatus(self.settings, fetch=fetch)
        status.set_enabled(True)
        self.state.journalPositionsReady.connect(status.observe)
        self.state.commanderIdentityChanged.connect(lambda cid, fid, name: status.observe([], fid))
        self.addCleanup(status.pool.waitForDone)
        return status

    def test_local_position_and_status_precede_upload_without_second_publication(self):
        r = self.runtime()
        entered, release, requested = threading.Event(), threading.Event(), threading.Event()
        status = self.status(lambda *_: requested.set() or 'known')
        notices, positions = [], []
        status.notice.connect(notices.append)
        self.state.journalPositionsReady.connect(lambda events, fid: positions.extend(
            e['StarSystem'] for e in events if e.get('event') == 'FSDJump'))
        revisions = dict(self.state._inventory_revisions)
        def transfer(database, source, rows, configs, settings, **kwargs):
            self.assertNotEqual(threading.get_ident(), self.gui_thread)
            self.assertEqual(source.id, r.source.id)
            self.assertEqual(rows[-1]['fid_seen'], 'TEST-Steam')
            self.assertEqual(database.commander_summary(rows[-1]['commander_id'])['persistent_location']['system_name'], 'A')
            entered.set()
            release.wait(5)
            return {}
        self.gui_thread = threading.get_ident()
        try:
            with patch('cmdrhelper.source_transfers.transfer', side_effect=transfer) as upload:
                self.jump(r, 'A', 101)
                self.wait(lambda: entered.is_set() and requested.is_set() and bool(notices))
                self.assertTrue(self.state.sources.running)
                self.assertFalse(release.is_set())
                self.assertEqual(self.state.system, 'A')
                self.assertEqual(positions, ['A'])
                release.set()
                self.drain()
                self.assertEqual(upload.call_count, 1)
                self.assertEqual(positions, ['A'])
                self.assertEqual(self.state._inventory_revisions, revisions)
        finally:
            release.set()
            self.drain()

    def test_local_failure_never_publishes_or_starts_transfer(self):
        r = self.runtime()
        calls = []
        self.status(lambda *args: calls.append(args) or 'known')
        before = self.state.system
        with patch.object(r.processor, 'process', side_effect=OSError('local failure')), \
             patch('cmdrhelper.source_transfers.transfer') as transfer:
            self.jump(r, 'Rejected', 101)
            self.drain()
            transfer.assert_not_called()
        self.assertEqual(calls, [])
        self.assertEqual(self.state.system, before)
        self.assertEqual(r.source.status, 'error')

    def test_slow_then_failed_transfer_preserves_queue_and_order(self):
        r = self.runtime()
        entered, release = threading.Event(), threading.Event()
        calls, positions = [], []
        self.state.journalPositionsReady.connect(lambda events, fid: positions.extend(
            e['StarSystem'] for e in events if e.get('event') == 'FSDJump'))
        def transfer(database, source, rows, *args, **kwargs):
            calls.append((source.id, rows[-1]['last_read_offset']))
            if len(calls) == 1:
                entered.set()
                release.wait(5)
                raise TimeoutError('controlled upload timeout')
            return {}
        try:
            with patch('cmdrhelper.source_transfers.transfer', side_effect=transfer):
                self.jump(r, 'A', 101)
                self.wait(lambda: entered.is_set() and self.state.system == 'A')
                self.jump(r, 'B', 102)
                self.jump(r, 'C', 103)
                self.app.processEvents()
                self.assertEqual(len(calls), 1)  # Queue remains serialized through transfer.
                self.assertEqual(self.state.system, 'A')
                release.set()
                self.drain()
                self.assertEqual(self.state.system, 'C')
                self.assertEqual(positions, ['A', 'B', 'C'])
                self.assertEqual(len(calls), 2)
                self.assertLess(calls[0][1], calls[1][1])
                self.assertEqual(r.transfer_error, '')
        finally:
            release.set()
            self.drain()

    def test_source_switch_same_fid_retires_old_result_during_transfer(self):
        r = self.runtime()
        other = next(rt for rt in self.state.sources.runtimes.values() if rt is not r)
        path = Path(other.source.path) / 'Journal.2026-09-15T120000.01.log'
        append(path, event('Commander', FID='TEST-Steam', Name='Steam'),
               event('Location', StarSystem='A', SystemAddress=101))
        other.watcher.check_now()
        self.drain()
        self.state.sources.preferred_source = r.source.id
        self.state.sources.refresh_selected()
        entered, release, fetch_started, fetch_release = [threading.Event() for _ in range(4)]
        fetches = []
        def fetch(*args):
            fetches.append(args)
            if len(fetches) == 1:
                fetch_started.set()
                fetch_release.wait(5)
                return 'unknown'
            return 'known'
        status = self.status(fetch)
        def transfer(*args, **kwargs):
            entered.set()
            release.wait(5)
            return {}
        try:
            with patch('cmdrhelper.source_transfers.transfer', side_effect=transfer):
                self.jump(r, 'A', 101)
                self.wait(lambda: entered.is_set() and fetch_started.is_set() and self.state.system == 'A')
                old_generation = status.generation
                self.state.sources.preferred_source = other.source.id
                self.assertTrue(self.state.sources.refresh_selected())
                self.assertGreater(status.generation, old_generation)
                self.wait(lambda: status.status == 'known')
                fetch_release.set()
                status.pool.waitForDone(3000)
                self.app.processEvents()
                self.assertEqual(status.status, 'known')
                self.assertEqual(self.state.sources.projected_source, other.source.id)
                release.set()
                self.drain()
                self.assertEqual(self.state.sources.projected_source, other.source.id)
        finally:
            release.set(); fetch_release.set()
            self.drain()

    def test_shutdown_keeps_inflight_transfer_owned_and_discards_publication(self):
        r = self.runtime()
        entered, release = threading.Event(), threading.Event()
        authorization = []
        def transfer(*args, **kwargs):
            authorization.append(kwargs['is_current']())
            entered.set()
            release.wait(5)
            authorization.append(kwargs['is_current']())
            return {}
        try:
            with patch('cmdrhelper.source_transfers.transfer', side_effect=transfer):
                self.jump(r, 'A', 101)
                self.wait(lambda: entered.is_set() and self.state.system == 'A')
                self.state.sources.stop()
                self.assertFalse(startup_runtime.shutdown(self.state, timeout=0))
                before = dict(self.state._inventory_revisions)
                release.set()
                self.assertTrue(startup_runtime.shutdown(self.state, timeout=3))
                self.app.processEvents()
                self.assertEqual(authorization, [True, False])
                self.assertEqual(self.state._inventory_revisions, before)
        finally:
            release.set()

    def test_real_inara_path_acknowledges_original_owner_once_after_switch(self):
        r = self.runtime()
        cid = self.state.commander_id
        prefix = 'inara/commanders/TEST-Steam'
        for key, value in [('enabled', True), ('api_key', 'synthetic'), ('commander', 'Steam')]:
            self.settings.setValue(prefix + '/' + key, value)
        self.settings.sync()
        entered, release = threading.Event(), threading.Event()
        sent = []
        def upload(key, name, fid, rows):
            self.assertEqual((key, fid), ('synthetic', 'TEST-Steam'))
            entered.set()
            release.wait(5)
            sent.extend(row['id'] for row in rows)
            return [row['id'] for row in rows], {}
        try:
            with patch('cmdrhelper.source_transfers.transfer', side_effect=real_transfer), \
                 patch('cmdrhelper.source_transfers.upload_batch', side_effect=upload) as send:
                self.jump(r, 'Uploaded A', 101)
                self.wait(lambda: entered.is_set() and self.state.system == 'Uploaded A')
                self.assertTrue(self.db.inara_pending(cid))
                other = next(rt for rt in self.state.sources.runtimes.values() if rt is not r)
                self.state.select_viewed_commander(other.processor.sessions[-1]['commander_id'])
                self.assertEqual(self.state.commander_fid, 'TEST-Heroic')
                release.set()
                self.drain()
                self.assertFalse(self.db.inara_pending(cid))
                self.assertTrue(sent)
                self.assertEqual(len(sent), len(set(sent)))
                self.state.sources.request(r.source.id)
                self.drain()
                self.assertEqual(send.call_count, 1)
                with self.db._connect() as con:
                    rows = con.execute('SELECT commander_id,status FROM inara_outbox WHERE id IN (' +
                        ','.join('?' for _ in sent) + ')', sent).fetchall()
                self.assertEqual(rows, [(cid, 'sent')] * len(sent))
        finally:
            release.set()
            self.drain()

    def test_removing_source_during_transfer_retires_its_status(self):
        r = self.runtime()
        entered, release, fetch_started, fetch_release = [threading.Event() for _ in range(4)]
        notices = []
        def fetch(*args):
            fetch_started.set()
            fetch_release.wait(5)
            return 'known'
        status = self.status(fetch)
        status.notice.connect(notices.append)
        current = []
        def transfer(*args, **kwargs):
            entered.set()
            release.wait(5)
            current.append(kwargs['is_current']())
            return {}
        try:
            with patch('cmdrhelper.source_transfers.transfer', side_effect=transfer):
                self.jump(r, 'A', 101)
                self.wait(lambda: entered.is_set() and fetch_started.is_set() and self.state.system == 'A')
                self.state.sources.registry.remove(r.source.id)
                self.state.sources.reconcile()
                fetch_release.set()
                status.pool.waitForDone(3000)
                self.app.processEvents()
                self.assertEqual(notices, [])
                release.set()
                self.drain()
                self.assertEqual(current, [False])
        finally:
            release.set(); fetch_release.set()
            self.drain()

    def test_commander_switch_while_ingesting_retires_old_status_before_new_projection(self):
        r = self.runtime()
        fetch_started, fetch_release, entered, release = [threading.Event() for _ in range(4)]
        notices = []
        def fetch(*args):
            fetch_started.set()
            fetch_release.wait(5)
            return 'known'
        status = self.status(fetch)
        status.notice.connect(notices.append)
        try:
            self.jump(r, 'A', 101)
            self.drain()
            self.wait(fetch_started.is_set)
            process = r.processor.process
            def blocked(**kwargs):
                entered.set()
                release.wait(5)
                return process(**kwargs)
            with patch.object(r.processor, 'process', side_effect=blocked):
                self.jump(r, 'B', 102)
                self.wait(entered.is_set)
                other = next(rt for rt in self.state.sources.runtimes.values() if rt is not r)
                self.state.select_viewed_commander(other.processor.sessions[-1]['commander_id'])
                fetch_release.set()
                status.pool.waitForDone(3000)
                self.app.processEvents()
                self.assertEqual(notices, [])
                release.set()
                self.drain()
                self.assertEqual(self.state.commander_fid, 'TEST-Heroic')
        finally:
            release.set(); fetch_release.set()
            self.drain()
