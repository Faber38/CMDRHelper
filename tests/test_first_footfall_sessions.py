"""Synthetic, isolated regression coverage for persistent footfall evidence."""
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from cmdrhelper.database import CMDRDatabase
from cmdrhelper.journal_index import scan_journal_folder
from cmdrhelper.journal_reader import read_latest_state, read_journal_delta, _LIVE_LINE_CACHE
from cmdrhelper.state import AppState


class FirstFootfallSessionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.folder = Path(self.tmp.name)
        self.path = self.folder / 'synthetic.db'
        self.db = CMDRDatabase(self.path)
        self.a = self.db.upsert_commander('SYN-A', 'Alpha')
        self.b = self.db.upsert_commander('SYN-B', 'Bravo')

    def event(self, kind, second=2, **kw):
        return dict(event=kind, timestamp=f'2026-09-23T10:00:{second:02d}Z',
                    SystemAddress=44717991937545, BodyID=31, **kw)

    def scan(self, flag=False, second=1):
        return self.event('Scan', second, BodyName='Synthetic B 8',
                          PlanetClass='Rocky body', MassEM=1.0, WasFootfalled=flag)

    def disembark(self, second=2, **kw):
        return self.event('Disembark', second, OnPlanet=True, **kw)

    def journal(self, number, events, fid='SYN-A'):
        p = self.folder / f'Journal.2026-09-23T10000{number}.01.log'
        header = [dict(event='Commander', FID=fid, Name='Synthetic',
                       timestamp='2026-09-23T10:00:00Z'),
                  self.event('Location', 0, StarSystem='Synthetic')]
        p.write_text(''.join(json.dumps(e)+'\n' for e in header+events))
        return p

    def live(self):
        sessions = scan_journal_folder(self.db, self.folder)
        data = read_latest_state(self.folder, indexed_sessions=sessions)
        session = sessions[-1]
        events, offset = read_journal_delta(Path(session['journal_file']),
                                            session['last_read_offset'])
        self.db.apply_commander_journal_delta(session['commander_id'],
            session['journal_file'], events, offset, live_current=True)
        state = SimpleNamespace(database=self.db, commander_id=session['commander_id'],
                                system_address=data['system_address'])
        bodies = AppState._own_explorer_bodies(state, data['system_bodies'])
        self.db.store_snapshot(data, session['commander_id'])
        return bodies

    def row(self):
        with self.db._connect() as con:
            return con.execute('SELECT first_footfall,first_footfall_at FROM commander_bodies '
                'WHERE commander_id=? AND system_address=? AND body_id=31',
                (self.a, 44717991937545)).fetchone()

    def seed(self, flag=False):
        self.journal(1, [self.scan(flag)])
        self.live()
        self.db = CMDRDatabase(self.path)
        _LIVE_LINE_CACHE.clear()

    def test_false_restart_disembark_and_display_merge(self):
        self.seed()
        self.journal(2, [self.disembark()])
        bodies = self.live()
        self.assertEqual(self.row(), (1, self.disembark()['timestamp']))
        self.assertTrue(bodies[0]['first_footfall'])
        self.assertFalse(bodies[0]['was_footfalled'])
        self.assertEqual(bodies[0]['biology'], [])
        self.db = CMDRDatabase(self.path)
        self.assertTrue(self.live()[0]['first_footfall'])

    def test_negative_evidence_and_identity_matrix(self):
        for case in ('true', 'null', 'invalid', 'body', 'system', 'commander',
                     'offplanet', 'station', 'missing_body', 'invalid_body',
                     'missing_address', 'touchdown', 'embark'):
            with self.subTest(case=case):
                with tempfile.TemporaryDirectory() as tmp:
                    original = self.folder, self.path, self.db, self.a, self.b
                    self.folder = Path(tmp); self.path = self.folder/'state.db'
                    self.db = CMDRDatabase(self.path)
                    self.a = self.db.upsert_commander('SYN-A','Alpha')
                    self.b = self.db.upsert_commander('SYN-B','Bravo')
                    self.seed(True if case == 'true' else None if case == 'null' else False)
                    e = self.disembark()
                    if case == 'invalid':
                        with self.db._connect() as con:
                            con.execute('UPDATE commander_bodies SET was_footfalled_at_scan=2')
                    if case == 'body': e['BodyID'] = 32
                    if case == 'system': e['SystemAddress'] += 1
                    if case == 'offplanet': e['OnPlanet'] = False
                    if case == 'station': e['OnStation'] = True
                    if case == 'missing_body': e.pop('BodyID')
                    if case == 'invalid_body': e['BodyID'] = '31'
                    if case == 'missing_address': e.pop('SystemAddress')
                    if case == 'touchdown': e['event'] = 'Touchdown'
                    if case == 'embark': e['event'] = 'Embark'
                    self.journal(2, [e], 'SYN-B' if case == 'commander' else 'SYN-A')
                    self.live()
                    self.assertEqual(self.row(), (0, None))
                    self.folder, self.path, self.db, self.a, self.b = original

    def test_repeated_disembark_preserves_first_timestamp(self):
        self.seed()
        self.journal(2, [self.disembark(), self.disembark(3)])
        self.live(); self.live()
        self.journal(3, [self.disembark(4)])
        self.live()
        self.assertEqual(self.row(), (1, self.disembark()['timestamp']))

    def test_later_true_scan_before_disembark_blocks_inference(self):
        self.seed()
        self.journal(2, [self.scan(True), self.disembark()])
        self.live()
        self.assertEqual(self.row(), (0, None))

    def test_later_true_scan_does_not_undo_recognized_footfall(self):
        self.seed()
        self.journal(2, [self.disembark(), self.scan(True, 3), self.disembark(4)])
        self.live()
        self.assertEqual(self.row(), (1, self.disembark()['timestamp']))

    def test_same_journal_both_orders(self):
        for reverse in (False, True):
            with self.subTest(reverse=reverse):
                events = [self.scan(), self.disembark()]
                if reverse: events.reverse()
                self.journal(1, events)
                sessions = scan_journal_folder(self.db, self.folder)
                bodies = read_latest_state(self.folder,indexed_sessions=sessions)['system_bodies']
                self.assertTrue(bodies[0]['first_footfall'])

    def test_same_journal_repetitions_preserve_timestamp(self):
        self.journal(1,[self.scan(),self.disembark(),self.disembark(3),self.scan(False,4)])
        self.live()
        self.assertEqual(self.row(), (1,self.disembark()['timestamp']))

    def test_archive_together(self):
        self.journal(1,[self.scan()]); self.journal(2,[self.disembark(),self.disembark(3)])
        self.db.import_journal_archive(self.folder)
        self.assertEqual(self.row(),(1,self.disembark()['timestamp']))

    def test_archive_separate_and_repeated(self):
        self.journal(1,[self.scan()]); self.db.import_journal_archive(self.folder)
        self.assertEqual(self.row(),(0,None))
        self.journal(2,[self.disembark(),self.disembark(3)])
        self.db.import_journal_archive(self.folder)
        self.assertEqual(self.row(),(1,self.disembark()['timestamp']))
        self.db.import_journal_archive(self.folder)
        self.assertEqual(self.row(),(1,self.disembark()['timestamp']))

    def test_archive_other_commander_body_system(self):
        self.journal(1,[self.scan()]); self.db.import_journal_archive(self.folder)
        self.journal(2,[self.disembark()], 'SYN-B')
        other = self.disembark(); other['BodyID'] = 32
        other_system = self.disembark(); other_system['SystemAddress'] += 1
        self.journal(3,[other,other_system])
        self.db.import_journal_archive(self.folder)
        self.assertEqual(self.row(),(0,None))

    def test_archive_true_scan_before_disembark(self):
        self.journal(1,[self.scan()]); self.db.import_journal_archive(self.folder)
        self.journal(2,[self.scan(True),self.disembark()])
        self.db.import_journal_archive(self.folder)
        self.assertEqual(self.row(),(0,None))

    def test_archive_true_scan_after_disembark(self):
        self.journal(1,[self.scan()]); self.db.import_journal_archive(self.folder)
        self.journal(2,[self.disembark(),self.scan(True,3)])
        self.db.import_journal_archive(self.folder)
        self.assertEqual(self.row(),(1,self.disembark()['timestamp']))

    def test_explorer_badge_after_delta_without_rescan(self):
        from PySide6.QtCore import QSettings
        from PySide6.QtWidgets import QApplication
        from cmdrhelper.i18n import get_language, set_language
        from cmdrhelper.ui.explorer_status import FOOTFALL_COLOR_ROLE
        from tests.test_explorer_table_ux import ExplorerWindow
        app = QApplication.instance() or QApplication([])
        self.addCleanup(set_language, get_language())
        set_language('de')
        self.seed()
        with self.db._connect() as con:
            con.execute('UPDATE commander_bodies SET self_mapped=1')
        self.journal(2, [self.disembark()])
        bodies = self.live()
        window = ExplorerWindow(QSettings(str(self.folder/'ui.ini'), QSettings.IniFormat))
        self.addCleanup(window.close)
        self.addCleanup(window.deleteLater)
        window.state.system_bodies = bodies
        window._refresh_explorer_tables(tab=1)
        app.processEvents()
        item = window.explorer_value_table.item(0, 7)
        self.assertEqual(item.text(), 'ERSTBETRETUNG\nSELBST KARTIERT')
        self.assertEqual(item.data(FOOTFALL_COLOR_ROLE), '#ffb000')
        for commander, address in ((self.b,44717991937545),(self.a,1)):
            state = SimpleNamespace(database=self.db, commander_id=commander, system_address=address)
            self.assertEqual(AppState._own_explorer_bodies(state, []), [])

    def test_archive_missing_true_and_invalid_evidence(self):
        self.journal(1,[self.scan(True)])
        self.db.import_journal_archive(self.folder)
        self.journal(2,[self.disembark()])
        self.db.import_journal_archive(self.folder)
        self.assertEqual(self.row(),(0,None))
        for number, flag in ((3,None),(4,2)):
            with self.db._connect() as con:
                con.execute('UPDATE commander_bodies SET was_footfalled_at_scan=?',(flag,))
            self.journal(number,[self.disembark(number)])
            self.db.import_journal_archive(self.folder)
            self.assertEqual(self.row(),(0,None))

    def test_archive_nonplanetary_events(self):
        self.journal(1,[self.scan()]); self.db.import_journal_archive(self.folder)
        offplanet = self.disembark(); offplanet['OnPlanet'] = False
        station = self.disembark(OnStation=True)
        self.journal(2,[offplanet,station,self.event('Touchdown'),self.event('Embark')])
        self.db.import_journal_archive(self.folder)
        self.assertEqual(self.row(),(0,None))
