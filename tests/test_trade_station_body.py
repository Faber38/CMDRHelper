"""Local-only body enrichment; no inference from station names or station BodyID."""
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import Mock

from PySide6.QtCore import Qt
from cmdrhelper.database import CMDRDatabase
from cmdrhelper.spansh_cache import normalize
from cmdrhelper.stations import observation, store_observation
from cmdrhelper.trade_station_body import known_station_body
from test_trade_recommendations import offer, NOW
import test_trade_remembered_targets as bookmark_tests


def cache_document(name='Synthetic Target 4 a', parent=7, planetary=True):
    return normalize({'system': {'id64': 200, 'name': 'Synthetic Target', 'bodies': [
        {'type': 'Planet', 'bodyId': parent, 'name': name, 'stations': [
            {'id': 2, 'name': 'Synthetic Port', 'type': 'Planetary Port',
             'isPlanetary': planetary}]}]}}, 200, now=NOW)


class StationBodyTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.db = CMDRDatabase(Path(self.tmp.name) / 'test.db')
        self.state = SimpleNamespace(database=self.db)
        self.offer = offer(station_type='CraterPort')
        with self.db._connect() as con:
            con.execute("INSERT INTO systems(system_address,name) VALUES(200,'Synthetic Target')")
            con.execute("""INSERT INTO bodies(system_address,body_id,name,short_name,body_type)
                           VALUES(200,7,'Synthetic Target 4 a','4 a','Planet')""")
            store_observation(con, observation(dict(event='ApproachSettlement', SystemAddress=200,
                Name='Synthetic Port', MarketID=2, BodyID=7, BodyName='Synthetic Target 4 a',
                timestamp=NOW.isoformat())))

    def test_local_journal_body_and_existing_short_name(self):
        self.assertEqual(known_station_body(self.state, self.offer), '4 a')
        with self.db._connect() as con:
            con.execute("UPDATE bodies SET short_name=name")
        self.assertEqual(known_station_body(self.state, self.offer), '4 a')
        with self.db._connect() as con:
            con.execute("UPDATE bodies SET short_name='Moon short label'")
        self.assertEqual(known_station_body(self.state, self.offer), 'Moon short label')
        self.assertEqual(known_station_body(self.state, replace(self.offer, system_id64=None)), 'Moon short label')

    def test_space_station_unknown_body_and_exact_identity(self):
        for changes in (dict(station_type='Coriolis'), dict(station_type='Orbis Starport'),
                        dict(market_id=3), dict(station_name='Similar Port'), dict(system_id64=201)):
            with self.subTest(changes=changes):
                self.assertEqual(known_station_body(self.state, replace(self.offer, **changes)), '')
        with self.db._connect() as con:
            con.execute('DELETE FROM bodies')
        self.assertEqual(known_station_body(self.state, self.offer), '')

    def test_station_bodyid_is_never_parent(self):
        with self.db._connect() as con:
            con.execute('DELETE FROM station_observations')
            store_observation(con, observation(dict(event='Location', Docked=True,
                SystemAddress=200, StationName='Synthetic Port', StationType='CraterPort',
                MarketID=2, BodyID=7, Body='Synthetic Target 4 a', BodyType='Station',
                timestamp=NOW.isoformat())))
        self.assertEqual(known_station_body(self.state, self.offer), '')

    def test_cached_explicit_parent_without_local_body_and_no_network(self):
        service = Mock(spec=['cached', 'refresh_system'])
        service.cached.return_value = cache_document()
        state = SimpleNamespace(spansh_stations=service)
        self.assertEqual(known_station_body(state, self.offer), '4 a')
        service.cached.assert_called_once_with(200)
        service.refresh_system.assert_not_called()
        for field in ('body_name', 'parent_body_id'):
            document = cache_document()
            del document['stations'][0][field]
            service.cached.return_value = document
            self.assertEqual(known_station_body(state, self.offer), '')
        service.cached.return_value = cache_document(planetary=False)
        self.assertEqual(known_station_body(state, self.offer), '')

    def test_conflicting_or_foreign_cached_body_is_not_displayed(self):
        service = Mock(spec=['cached'])
        self.state.spansh_stations = service
        for name, parent in [('Synthetic Target 4 b', 7), ('Synthetic Target 5', 8)]:
            service.cached.return_value = cache_document(name, parent)
            self.assertEqual(known_station_body(self.state, self.offer), '')
        state = SimpleNamespace(spansh_stations=service)
        document = cache_document()
        document['system_name'] = 'Another System'
        service.cached.return_value = document
        self.assertEqual(known_station_body(state, self.offer), '')


class BookmarkBodyViewTests(unittest.TestCase):
    setUpClass = bookmark_tests.RememberedTargetTests.__dict__['setUpClass']
    setUp = bookmark_tests.RememberedTargetTests.setUp
    tearDown = bookmark_tests.RememberedTargetTests.tearDown
    populate = bookmark_tests.RememberedTargetTests.populate
    panel = bookmark_tests.RememberedTargetTests.panel
    marks = bookmark_tests.RememberedTargetTests.marks
    render = bookmark_tests.RememberedTargetTests.render

    def test_all_tabs_body_fallback_multiple_selection_and_new_results(self):
        service = Mock(spec=['cached', 'refresh_system'])
        service.cached.return_value = cache_document()
        self.state.spansh_stations = service
        for tab in range(3):
            self.populate(tab, [])
            surface = offer(station_type='CraterPort', commander_buy_price=10000, supply=100)
            space = replace(surface, station_type='Coriolis', station_name='Orbital', market_id=3)
            unknown = replace(surface, station_name='Unknown Surface', market_id=4)
            self.render(tab, (surface, space, unknown))
            for mark in self.marks(tab):
                mark.setCheckState(Qt.Checked)
            panel = self.panel(tab)
            self.assertEqual(set(panel.text().splitlines()), {
                'Synthetic Target · 4 a · Synthetic Port · Groß',
                'Synthetic Target · Orbital · Groß',
                'Synthetic Target · Unknown Surface · Groß'})
            before = panel.text()
            self.render(tab, ())
            self.assertEqual(panel.text(), before)
            self.render(tab, (surface, surface, space))
            self.assertTrue(all(m.checkState() == Qt.Checked for m in self.marks(tab)))
            duplicates = [m for m in self.marks(tab) if m.data(Qt.UserRole + 2)[1] == 'Synthetic Port']
            duplicates[0].setCheckState(Qt.Unchecked)
            self.assertIn(' · 4 a · ', panel.text())
            duplicates[1].setCheckState(Qt.Unchecked)
            self.assertNotIn(' · 4 a · ', panel.text())
            self.assertEqual(len(panel.targets), 2)
        service.refresh_system.assert_not_called()
