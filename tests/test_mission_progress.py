"""Structured mission facts, legacy databases and the actual mission page (offscreen)."""
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from copy import deepcopy
import sqlite3
import unittest
from unittest.mock import Mock

from cmdrhelper.database import CMDRDatabase, SCHEMA_VERSION
from cmdrhelper.i18n import _TRANSLATIONS, get_language, set_language
from cmdrhelper.journal_reader import _new_mission, _update_mission_event
from cmdrhelper.mission_manager import (normalize_missions, delivery_complete,
    mission_quantities_text, mission_display_step)
from cmdrhelper.mission_persistence import mission_details_prefix
from tests import test_current_missions as persistence_fixture
from tests.test_current_missions import event
from tests import test_missions_table_sort as ui_fixture
from cmdrhelper.ui.mission_arrival import TEAM_ROLE
from cmdrhelper.mission_arrival import ArrivalPosition


def accepted(mid=7, name='Mission_Delivery', wing=False):
    return event('MissionAccepted', MissionID=mid, Name=name, Wing=wing,
                 Commodity='$Gold_Name;', Commodity_Localised='Gold', Count=132,
                 DestinationSystem='Here', DestinationStation='Port')


def depot(second, delivered, kind='Deliver', **extra):
    return event('CargoDepot', second, MissionID=7, UpdateType=kind,
                 ItemsDelivered=delivered, TotalItemsToDeliver=132, **extra)


class MissionProgressTests(unittest.TestCase):
    def setUp(self):
        self.addCleanup(set_language, get_language())
        set_language("de")
        persistence_fixture.CurrentMissionsTests.setUp(self)

    apply = persistence_fixture.CurrentMissionsTests.apply
    rows = persistence_fixture.CurrentMissionsTests.rows

    def model(self):
        return normalize_missions(self.rows())[0]

    def test_goods_families_partial_complete_restart_and_terminal(self):
        for name in ('Mission_Delivery', 'Mission_Mining', 'Mission_Collect_Industrial'):
            with self.subTest(name=name):
                # Independent source/DB per family, retaining real source attribution.
                self.setUp()
                self.apply(accepted(name=name, wing=True), depot(2, 50))
                self.assertIn('82 t fehlen', mission_quantities_text(self.model()))
                self.assertFalse(delivery_complete(self.model()))
                self.db = CMDRDatabase(self.db.path)
                m = self.model()
                self.assertEqual((m.commodity_symbol, m.required_count, m.delivered_count, m.wing),
                                 ('$Gold_Name;', 132, 50, True))
                self.apply(depot(3, 132, 'WingUpdate'))
                self.assertTrue(delivery_complete(self.model()))
                self.assertEqual(mission_display_step(self.model()), 'Belohnung abholen')
                self.assertTrue(self.rows()[0]['is_open'])
                self.apply(event('MissionCompleted', 4, MissionID=7))
                self.assertEqual(self.rows(), [])
                with self.db._connect() as con:
                    key = mission_details_prefix(con, self.a) + '7'
                    self.assertIsNone(con.execute('SELECT value FROM app_meta WHERE key=?', (key,)).fetchone())

    def test_collect_wingupdate_sparse_snapshot_and_zero_are_distinct(self):
        self.apply(accepted(wing=False))
        self.assertIn('Lieferstand unbekannt', mission_quantities_text(self.model()))
        self.apply(depot(2, 0, 'Collect', ItemsCollected=132, Count=132))
        self.assertEqual(self.model().status, 'Ware aufgenommen')
        self.assertIn('132 t fehlen', mission_quantities_text(self.model()))
        self.apply(depot(3, 50, 'WingUpdate'), depot(4, 50, 'WingUpdate'))
        self.assertEqual(self.model().delivered_count, 50)
        self.apply(event('Missions', 5, Active=[{'MissionID': 7}]))
        self.assertEqual(self.model().wing, False)
        self.assertEqual(self.model().delivered_count, 50)
        self.assertEqual(self.model().commodity_symbol, '$Gold_Name;')
        self.apply(event('CargoDepot', 6, MissionID=7, UpdateType='WingUpdate', ItemsDelivered=90))
        self.assertIn('42 t fehlen', mission_quantities_text(self.model()))
        self.apply(depot(2, 10))  # Out-of-order events cannot regress the state.
        self.assertEqual(self.model().delivered_count, 90)

    def test_invalid_depot_reports_never_create_completion(self):
        base = _new_mission(accepted())
        _update_mission_event(base, depot(2, 50))
        for values in ({'ItemsDelivered': True}, {'ItemsDelivered': '132'},
                       {'ItemsDelivered': -1}, {'ItemsDelivered': 133},
                       {'TotalItemsToDeliver': 0}, {'ItemsCollected': -1}):
            m = deepcopy(base); e = depot(3, 132); e.update(values)
            _update_mission_event(m, e)
            self.assertEqual(m, base)
        m = _new_mission(dict(event='CargoDepot', MissionID=7, Count=50))
        self.assertNotIn('required_count', m)
        self.assertFalse(delivery_complete(normalize_missions([m])[0]))

    def test_legacy_rows_unknown_types_and_non_goods_never_claim_rewards(self):
        self.db.store_commander_missions(self.a, [dict(mission_id=7, name='132 Gold',
            summary='Gold (132x)', progress_text='50/132 geliefert', status='Aufgabe erledigt')])
        self.db = CMDRDatabase(self.db.path)
        self.assertIsNone(self.model().required_count)
        self.assertIsNone(self.model().wing)
        self.assertEqual(mission_quantities_text(self.model()), '')
        self.assertNotEqual(mission_display_step(self.model()), 'Belohnung abholen')
        for name in ('Mission_Courier', 'Mission_Altruism', 'Mission_Massacre', 'Mission_Unknown'):
            raw = _new_mission(accepted(name=name)); _update_mission_event(raw, depot(2, 132))
            self.assertEqual(mission_display_step(normalize_missions([raw])[0]), 'Mission prüfen')

    def test_abandon_failed_and_commander_isolation(self):
        for terminal in ('MissionAbandoned', 'MissionFailed'):
            self.setUp()
            self.apply(accepted(wing=True), depot(2, 50))
            self.db.store_commander_missions(self.b, [dict(mission_id=7, wing=False, required_count=10)])
            self.apply(event(terminal, 3, MissionID=7))
            self.assertEqual(self.rows(), [])
            other = normalize_missions(self.db.commander_missions(self.b))[0]
            self.assertEqual((other.required_count, other.wing), (10, False))
            with self.db._connect() as con:
                self.assertEqual(con.execute('PRAGMA user_version').fetchone()[0], SCHEMA_VERSION)
                self.assertEqual(con.execute('PRAGMA integrity_check').fetchone()[0], 'ok')

    def test_metadata_failure_rolls_back_mission_and_cursor(self):
        with self.db._connect() as con:
            con.execute("CREATE TRIGGER reject_mission_details BEFORE INSERT ON app_meta "
                        "WHEN NEW.key LIKE 'mission_details/v1/%' BEGIN SELECT RAISE(ABORT,'synthetic'); END")
        with self.assertRaises(sqlite3.IntegrityError):
            self.apply(accepted(wing=True))
        self.assertEqual(self.rows(), [])
        with self.db._connect() as con:
            self.assertEqual(con.execute('SELECT last_read_offset FROM journal_sessions').fetchone()[0], 0)

    def test_cleanup_copy_preserves_open_inactive_and_other_metadata(self):
        from tools.check_mission_cleanup import check_copy
        self.apply(accepted(wing=True), depot(2, 50))
        self.db.store_commander_missions(self.a, [dict(mission_id=8, required_count=12, wing=False)])
        with self.db._connect() as con:
            con.execute("UPDATE commander_missions SET is_open=0,terminal_state='completed' WHERE mission_id=8")
        report = check_copy(self.db.path, self.folder / 'cleaned.db', clean=True)
        self.assertTrue(report['other_meta_including_pending_unchanged'])
        self.assertTrue(report['schema_unchanged'])
        copy = CMDRDatabase(self.folder / 'cleaned.db')
        self.assertEqual(copy.commander_missions(self.a)[0]['delivered_count'], 50)
        self.assertEqual(len(self.rows()), 2)  # Source untouched.

    def test_sparse_depot_without_acceptance_and_invalid_metadata(self):
        self.apply(depot(2, 50, 'WingUpdate'))
        m = self.model()
        self.assertEqual((m.required_count, m.delivered_count, m.wing), (132, 50, None))
        self.assertIn('82 t fehlen', mission_quantities_text(m))
        self.apply(depot(3, 132, 'WingUpdate'))
        self.assertEqual(mission_display_step(self.model()), 'Mission prüfen')
        with self.db._connect() as con:
            key = mission_details_prefix(con, self.a) + '7'
            con.execute('UPDATE app_meta SET value=? WHERE key=?', ('not JSON', key))
        self.assertIsNone(self.model().required_count)

    def test_all_twelve_translations_have_matching_placeholders(self):
        from string import Formatter
        keys = [k for k in _TRANSLATIONS['de'] if k.startswith('missions.quantity_')]
        keys += ['missions.team_capable', 'missions.team_capable_tooltip', 'missions.delivery_complete',
                 'missions.claim_reward', 'missions.check_delivery', 'missions.delivery_unknown',
                 'missions.legend_arrival', 'missions.legend_accepted', 'missions.legend_progress']
        self.assertEqual(len(_TRANSLATIONS), 12)
        for key in keys:
            fields = lambda text: {f for _, f, _, _ in Formatter().parse(text) if f}
            for language, table in _TRANSLATIONS.items():
                self.assertIn(key, table, language)
                self.assertEqual(fields(table[key]), fields(_TRANSLATIONS['de'][key]))

    def test_commodity_names_use_existing_catalog_not_frontier_tokens(self):
        raw = _new_mission({**accepted(), 'Commodity': '$DomesticAppliances_Name;',
                            'Commodity_Localised': 'Haushaltsgeräte'})
        m = normalize_missions([raw])[0]
        self.assertIn('Haushaltsgeräte', mission_quantities_text(m))
        set_language('en')
        self.assertIn('Domestic Appliances', mission_quantities_text(m))


class MissionProgressUiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        ui_fixture.MissionTableSortTests.setUpClass()
        cls.app = ui_fixture.MissionTableSortTests.app

    def setUp(self):
        self.addCleanup(set_language, get_language())
        self.fixture = ui_fixture.MissionTableSortTests(); self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.host = self.fixture.host
        self.controller = self.host.mission_arrival
        self.controller.source = Mock()
        self.identity = ('source', 1, 1, 'A')
        self.position = ArrivalPosition(system='Here', station='Port', kind='station', evidence=(1,))
        self.controller.source.snapshot.side_effect = lambda state: (self.identity, self.position, set())

    def test_real_table_details_team_and_arrival_without_blink_or_database_mutation(self):
        from PySide6.QtWidgets import QStyleOptionViewItem
        from cmdrhelper.ui.styles import DARK_STYLESHEET, LIGHT_STYLESHEET
        raw = _new_mission(accepted(wing=True)); _update_mission_event(raw, depot(2, 50))
        m = normalize_missions([raw])[0]; before = deepcopy(m)
        self.host.state.missions = [m]
        for theme in (DARK_STYLESHEET, LIGHT_STYLESHEET):
            self.host.page.setStyleSheet(theme)
            self.host._refresh_missions_table(); self.host.missions_table.selectRow(0)
            self.assertTrue(self.host.missions_table.item(0, 0).data(TEAM_ROLE))
            self.assertIn('Am Missionsziel', self.host.missions_table.item(0, 2).text())
            self.assertIn('82 t fehlen', self.host.mission_progress_text.text())
            for _ in range(6):
                self.controller.advance()
                self.assertIn('Am Missionsziel', self.host.mission_progress_text.text())
            index = self.host.missions_table.model().index(0, 0)
            option = QStyleOptionViewItem()
            self.host.missions_table.itemDelegate().initStyleOption(option, index)
            self.assertFalse(option.icon.isNull())
            self.host.missions_table.viewport().grab()  # Exercise decorated arrival drawing offscreen.
        self.assertEqual(m, before)
        self.position.clear_arrival(); self.controller.update()
        self.assertNotIn('Am Missionsziel', self.host.mission_progress_text.text())
        self.assertNotIn('Am Missionsziel', self.host.missions_table.item(0, 2).text())
        self.position.kind = 'station'; self.position.station = 'Port'; self.position.evidence = (2,)
        self.controller.update()
        _update_mission_event(raw, depot(3, 132, 'WingUpdate'))
        self.host.state.missions = normalize_missions([raw]); self.host._refresh_missions_table()
        self.assertIn('Lieferung abgeschlossen – Belohnung abholen', self.host.mission_progress_text.text())
        self.assertEqual(self.host.missions_table.columnCount(), 7)
        self.controller.source.snapshot.return_value = None
        self.controller.source.snapshot.side_effect = None
        self.controller.update()
        self.assertNotIn('Am Missionsziel', self.host.mission_progress_text.text())

    def test_all_languages_and_normal_mission_without_team_icon(self):
        from cmdrhelper.i18n import tr
        raw = _new_mission(accepted(wing=False)); _update_mission_event(raw, depot(2, 132))
        self.host.state.missions = normalize_missions([raw])
        for language in _TRANSLATIONS:
            set_language(language)
            self.host._refresh_missions_table(); self.host.missions_table.selectRow(0)
            self.assertFalse(self.host.missions_table.item(0, 0).data(TEAM_ROLE))
            self.assertIn(tr('missions.delivery_complete') + ' – ' + tr('missions.claim_reward'),
                          self.host.mission_progress_text.text())
            self.assertIn(tr('mission_state.at_destination'), self.host.missions_table.item(0, 2).text())

    def test_legend_wraps_and_explains_only_real_semantics_in_all_languages(self):
        from PySide6.QtCore import QUrl
        from PySide6.QtGui import QTextDocument
        from cmdrhelper.i18n import tr
        from cmdrhelper.ui.styles import DARK_STYLESHEET, LIGHT_STYLESHEET
        legend = self.host.mission_legend
        for language in _TRANSLATIONS:
            set_language(language)
            for light, style in ((False, DARK_STYLESHEET), (True, LIGHT_STYLESHEET)):
                self.host.page.setStyleSheet(style)
                legend.set_light_mode(light)
                self.host._refresh_missions_table()
                text = legend.document.toPlainText()
                for key in ('legend_arrival', 'legend_accepted', 'legend_progress', 'team_capable'):
                    self.assertIn(tr('missions.' + key), text)
                html = legend.document.toHtml().lower()
                self.assertIn('#226626' if light else '#65d067', html)
                self.assertIn('#765400' if light else '#ffb000', html)
                self.assertGreater(legend.heightForWidth(400), legend.heightForWidth(1800))
                self.assertFalse(legend.document.resource(QTextDocument.ImageResource,
                                                          QUrl('mission:team')).isNull())
                self.host.page.resize(900, 700)
                self.app.processEvents()
                self.assertGreaterEqual(legend.height(), legend.heightForWidth(legend.width()))
                legend.grab()
        set_language('de'); legend.refresh()
        text = legend.document.toPlainText()
        self.assertNotIn('Auswahl', text)
        self.assertNotIn('Hover', text)
        self.assertIn('Aufgabe/Lieferung erledigt', text)
