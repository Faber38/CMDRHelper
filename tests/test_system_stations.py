import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PySide6.QtCore import Qt, QPoint
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QDialog, QListWidget, QLabel
from cmdrhelper.database import CMDRDatabase, SCHEMA_VERSION
from cmdrhelper.stations import observation, store_observation, project_stations, load_stations
from cmdrhelper.ui.system_overview import SystemOverviewView, build_layout
from cmdrhelper.ui.system_view import SystemMapWidget
from cmdrhelper.ui import station_items

BODIES = [dict(body_id=0, name='Test', body_type='Star', star_type='G'),
          dict(body_id=1, name='Test 1', body_type='Planet', parent_id=0),
          dict(body_id=2, name='Test 1 a', body_type='Planet', parent_id=1)]


def fact(kind='Docked', second=1, **values):
    return observation(dict(event=kind, SystemAddress=1, StationName='Station',
                            MarketID=100, timestamp=f'2026-09-16T10:00:{second:02}Z', **values))


def station(market=100, parent=1, name='Station'):
    return dict(identity=f'market:{market}', station_name=name, station_type='Outpost',
                market_id=market, parent_body_id=parent, body_name='Test 1',
                last_seen='2026-09-16T10:00:00Z', source='Journal')


class StationFactsTests(unittest.TestCase):
    def project(self, *facts, carrier=None, address=1):
        return project_stations(facts, address, BODIES, carrier)

    def test_orbital_station_body_id_is_not_parent(self):
        row = fact('Location', Docked=True, StationType='Dodec', BodyID=76,
                   Body='Station', BodyType='Station')
        result = self.project(row)[0]
        self.assertEqual(result['body_id'], 76)
        self.assertIsNone(result['parent_body_id'])
        self.assertFalse(result['is_planetary'])

    def test_surface_parent_survives_later_docking_and_reversed_input(self):
        approach = fact('ApproachSettlement', Name='Station', BodyID=1, BodyName='Test 1',
                        Latitude=0., Longitude=0.)
        dock = fact(second=2, StationType='CraterOutpost')
        result = self.project(dock, approach)[0]
        self.assertEqual(result['parent_body_id'], 1)
        self.assertEqual(result['latitude'], 0)
        self.assertEqual(result['station_type'], 'CraterOutpost')
        self.assertEqual(result['last_seen'], dock['last_seen'])

    def test_missing_or_conflicting_parent_is_unknown(self):
        for body_id, name in [(999, 'Test 999'), (1, 'Wrong')]:
            row = fact('ApproachSettlement', Name='Station', BodyID=body_id, BodyName=name)
            self.assertIsNone(self.project(row)[0]['parent_body_id'])

    def test_market_identity_and_same_name_do_not_merge(self):
        a, b = fact(), fact()
        b.update(identity='market:101', market_id=101)
        self.assertEqual(len(self.project(a, b)), 2)
        newer = fact(second=2)
        newer['station_name'] = 'Renamed'
        self.assertEqual(self.project(a, newer)[0]['station_name'], 'Renamed')

    def test_no_name_only_identity_or_fss_guess(self):
        self.assertIsNone(observation(dict(event='Docked', SystemAddress=1, StationName='Name')))
        self.assertIsNone(observation(dict(event='FSSSignalDiscovered', SystemAddress=1,
                                          SignalName='Name', IsStation=True)))
        self.assertIsNone(observation(dict(event='FSDJump', SystemAddress=1, BodyID=0)))

    def test_settlement_without_market_requires_coordinates_and_body(self):
        base = dict(event='ApproachSettlement', SystemAddress=1, Name='Name', BodyID=1)
        self.assertIsNone(observation(base))
        self.assertTrue(observation(dict(base, Latitude=0, Longitude=0))['identity'].startswith('surface:'))

    def test_own_carrier_and_foreign_carrier_filter(self):
        row = fact('CarrierLocation', CarrierID=100, BodyID=0)
        self.assertEqual(self.project(row), [])
        own = dict(carrier_id=100, carrier_name='Own', system_address=1)
        result = self.project(row, carrier=own)[0]
        self.assertEqual(result['parent_body_id'], 0)
        self.assertEqual(result['station_name'], 'Own')

    def test_carrier_move_clears_body_and_old_system(self):
        old = fact('CarrierLocation', CarrierID=100, BodyID=1)
        moved = fact(second=2, StationType='FleetCarrier')
        moved['system_address'] = 2
        own = dict(carrier_id=100)
        self.assertEqual(self.project(old, moved, carrier=own), [])
        self.assertIsNone(self.project(old, moved, carrier=own, address=2)[0]['parent_body_id'])

    def test_newer_owned_carrier_record_suppresses_stale_observation(self):
        row = fact('CarrierLocation', CarrierID=100, BodyID=1)
        own = dict(carrier_id=100, system_address=2, last_updated='2026-09-17T00:00:00Z')
        self.assertEqual(self.project(row, carrier=own), [])

    def test_real_plio_journal_evidence(self):
        events = json.loads((Path(__file__).parent / 'fixtures/system_stations_plio.json').read_text())
        bodies = [dict(body_id=37, name='Plio Aihm UC-V d2-159 7 d', body_type='Planet'),
                  dict(body_id=49, name='Plio Aihm UC-V d2-159 9 g', body_type='Planet')]
        result = project_stations([observation(e) for e in events], 5474145570075, bodies,
                                  dict(carrier_id=3705965312, carrier_name='[EOT] = RHEIN-ERFT ='))
        self.assertEqual(len(result), 7)
        by_name = {s['station_name']: s for s in result}
        self.assertEqual(by_name['Ridorana Metalworks']['parent_body_id'], 49)
        self.assertEqual(by_name['[EOT] = RHEIN-ERFT =']['parent_body_id'], 37)
        self.assertIsNone(by_name['Ridorana Forge']['parent_body_id'])
        self.assertEqual(by_name['Ridorana Forge']['station_type'], 'Dodec')
        self.assertEqual(sum(s['parent_body_id'] is None for s in result), 5)

    def test_carrier_jump_request_is_not_arrival(self):
        self.assertIsNone(observation(dict(event='CarrierJumpRequest', SystemAddress=1, CarrierID=100)))


class StationDatabaseTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = CMDRDatabase(Path(self.tmp.name) / 'test.db')

    def tearDown(self):
        self.tmp.cleanup()

    def test_migration_v19_additive_and_idempotent(self):
        with self.db._connect() as con:
            con.execute('DROP TABLE station_observations')
            con.execute('PRAGMA user_version=19')
            before = con.execute('SELECT * FROM bodies').fetchall()
        self.db._maybe_migrate_v20()
        self.db._maybe_migrate_v20()
        with self.db._connect() as con:
            self.assertEqual(con.execute('PRAGMA user_version').fetchone()[0], SCHEMA_VERSION)
            self.assertEqual(con.execute('SELECT * FROM bodies').fetchall(), before)
            self.assertEqual(load_stations(con, 1, BODIES), [])

    def test_migration_rollback(self):
        with self.db._connect() as con:
            con.execute('DROP TABLE station_observations')
            con.execute('CREATE TABLE conflict_table (system_address INTEGER)')
            con.execute('CREATE INDEX idx_station_system ON conflict_table(system_address)')
            con.execute('PRAGMA user_version=19')
        # SQLite transaction must roll back an interrupted CREATE TABLE + version.
        con = sqlite3.connect(self.db.path)
        class Failing:
            def __enter__(self): return self
            def __exit__(self, *args): con.rollback(); con.close()
            def execute(self, sql):
                if 'CREATE INDEX' in sql: raise RuntimeError('interrupted')
                return con.execute(sql)
        with patch.object(self.db, '_connect', return_value=Failing()):
            with self.assertRaises(RuntimeError): self.db._maybe_migrate_v20()
        with self.db._connect() as con:
            self.assertEqual(con.execute('PRAGMA user_version').fetchone()[0], 19)
            self.assertIsNone(con.execute("SELECT name FROM sqlite_master WHERE name='station_observations'").fetchone())

    def test_idempotent_and_old_observations_do_not_replace_new(self):
        with self.db._connect() as con:
            newer = fact(second=5, StationType='Dodec')
            for row in [newer, newer, fact(second=1)]: store_observation(con, row)
            self.assertEqual(con.execute('SELECT COUNT(*) FROM station_observations').fetchone()[0], 1)
            self.assertEqual(load_stations(con, 1, BODIES)[0]['station_type'], 'Dodec')

    def test_archive_import_and_backfill_are_idempotent(self):
        from cmdrhelper.stations import plan_backfill
        from cmdrhelper.startup_repairs import run_startup_repairs
        path = Path(self.tmp.name) / 'Journal.2026-09-16T100000.01.log'
        events = [dict(event='LoadGame', FID='StationFID', Commander='StationTest',
                       timestamp='2026-09-16T10:00:00Z'),
                  dict(event='ApproachSettlement', timestamp='2026-09-16T10:00:01Z',
                       SystemAddress=1, Name='Surface port', MarketID=100,
                       BodyID=1, BodyName='Test 1', Latitude=0, Longitude=0)]
        path.write_text(''.join(json.dumps(e) + '\n' for e in events))
        self.db.import_journal_archive(Path(self.tmp.name))
        with self.db._connect() as con:
            cid = con.execute("SELECT id FROM commanders WHERE fid='StationFID'").fetchone()[0]
            self.assertEqual(load_stations(con, 1, BODIES)[0]['parent_body_id'], 1)
            con.execute('DELETE FROM station_observations')
        run_startup_repairs(self.db.path)
        self.assertEqual(self.db.system_stations(1, BODIES, cid)[0]['parent_body_id'], 1)
        with patch('cmdrhelper.stations.plan_backfill', side_effect=AssertionError('no repeat scan')):
            self.assertEqual(run_startup_repairs(self.db.path), [])

    def test_live_delta_persists_station(self):
        cid = self.db.upsert_commander('TestFID', 'Test')
        self.db.apply_commander_journal_delta(cid, 'test.log', [dict(event='Docked',
            timestamp='2026-09-16T10:00:00Z', SystemAddress=1, StarSystem='Test',
            StationName='Station', StationType='Orbis', MarketID=100)], 100)
        self.assertEqual(self.db.system_stations(1, BODIES, cid)[0]['market_id'], 100)


class StationUITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_empty_station_list_preserves_layout(self):
        view = SystemOverviewView('Test', BODIES, stations=[])
        expected = build_layout(BODIES)
        self.assertEqual([(n.x, n.y, n.layout_height) for n in view.nodes.values()],
                         [(n.x, n.y, n.layout_height) for n in expected.values()])
        self.assertEqual(view.facility_items, [])
        view.close()

    def test_many_facilities_compact_and_below_body(self):
        for count in (1, 3, 7, 200):
            view = SystemOverviewView('Test', BODIES, stations=[station(i) for i in range(count)])
            self.assertEqual(len(view.facility_items), count if count <= 3 else 1)
            item = view.facility_items[0]
            parent, moon = view.nodes['body', 1], view.nodes['body', 2]
            self.assertGreaterEqual(item.y(), parent.rect.bottom())
            self.assertLess(item.sceneBoundingRect().bottom(), moon.y)
            view.close()

    def test_unknown_parent_footer(self):
        view = SystemOverviewView('Test', BODIES, stations=[station(parent=None)])
        self.assertIsNotNone(view.facility_footer)
        self.assertGreater(view.facility_items[0].y(), max(n.rect.bottom() for n in view.nodes.values()))
        view.close()

    def test_long_name_tooltip_zoom_themes_and_body_click(self):
        name = 'Very long station name ' * 20
        view = SystemOverviewView('Test', BODIES, stations=[station(name=name)])
        view.resize(900, 600); view.show(); self.app.processEvents()
        self.assertIn(name, view.facility_items[0].toolTip())
        calls = []; view.bodyClicked.connect(calls.append)
        body_item = view.items_by_key['body', 1]
        QTest.mouseClick(view.viewport(), Qt.LeftButton,
                        pos=view.mapFromScene(body_item.sceneBoundingRect().center()))
        self.assertEqual(calls[0]['body_id'], 1)
        view.scale(1.5, 1.5)
        self.assertEqual(view.transform().m11(), 1.5)
        view.reset_zoom(); self.assertEqual(view.transform().m11(), 1)
        for light in (True, False):
            view.set_light_mode(light); view.grab()
            self.assertEqual(view.facility_items[0].light, light)
        view.close()

    def test_group_detail_selection(self):
        stations = [station(i, name=f'Facility {i}') for i in range(7)]
        dialog = station_items.show_details(None, stations, 'Test')
        listing = dialog.findChild(QListWidget)
        listing.setCurrentRow(6)
        QTest.mouseClick(listing.viewport(), Qt.LeftButton,
                         pos=listing.visualItemRect(listing.item(6)).center())
        self.assertIn('Facility 6', dialog._details.windowTitle())
        self.assertIn('MarketID: 6', dialog._details.info.text())
        dialog._details.close()
        dialog.close()

    def test_widget_facility_click_and_paint_is_io_free(self):
        widget = SystemMapWidget(); widget.set_system('Test', BODIES, [station()])
        widget.resize(widget.minimumSize()); widget.show(); self.app.processEvents()
        with patch('sqlite3.connect', side_effect=AssertionError('paint must not query')), \
             patch('urllib.request.urlopen', side_effect=AssertionError('paint must not fetch')):
            for light in (False, True):
                widget.set_light_mode(light); widget.grab()
        with patch.object(station_items, 'show_details') as details:
            QTest.mouseClick(widget, Qt.LeftButton, pos=widget._facility_blocks[0][0].center().toPoint())
            details.assert_called_once()
        widget.close()
