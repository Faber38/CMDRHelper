"""Explicit mission destinations, isolated persistence and detail rendering."""
from copy import deepcopy
import unittest
from types import SimpleNamespace

from cmdrhelper import i18n
from cmdrhelper.database import CMDRDatabase, SCHEMA_VERSION
from cmdrhelper.journal_reader import _new_mission, _update_mission_event
from cmdrhelper.mission_persistence import snapshot_mission
from cmdrhelper.mission_manager import mission_detail_text, normalize_missions
from cmdrhelper.state import AppState
from tests import test_current_missions as base
from tests import test_missions_table_sort as ui_base


class DestinationSummaryTests(unittest.TestCase):
    def test_missing_targets_stay_missing(self):
        mission = _new_mission(dict(MissionID=1068930971, Name='Mission_OnFoot_Salvage_MB',
                                    LocalisedName='Insight-Datenbank von einer Absturzstelle beschaffen',
                                    Commodity_Localised='Insight-Datenbank', Count=1))
        updated = snapshot_mission({'MissionID': 1068930971}, 'later', mission)
        self.assertEqual(updated['summary'], 'Waren: Insight-Datenbank (1x)')
        for field in ('destination_system', 'destination_station', 'destination_body'):
            self.assertEqual(updated[field], '')

    def test_snapshot_updates_generated_prefix_preserving_other_details(self):
        mission = _new_mission(dict(MissionID=1, DestinationSystem='Old',
                                    DestinationSettlement='Old Port', Commodity='Gold', Count=2))
        mission.update(status='Aufgabe erledigt', progress_text='2/2 geliefert',
                       next_step='Zurück zum Missionsterminal',
                       extra={'source': 'ReceiveText+Missions', 'offer_message': 'Keep exactly'})
        mission['summary'] += ' · Individueller Hinweis'
        before = deepcopy(mission)
        updated = snapshot_mission(dict(MissionID=1, DestinationSystem='New',
                                        DestinationSettlement='New Port', DestinationBody='New 1'),
                                   'later', mission)
        self.assertEqual(updated['summary'],
                         'Zielsystem: New · Planet/Körper: New 1 · Ort: New Port'
                         ' · Waren: Gold (2x) · Individueller Hinweis')
        for field in ('status', 'progress_text', 'next_step', 'extra', 'commodity', 'count'):
            self.assertEqual(updated[field], mission[field])
        self.assertEqual(mission, before)
        again = snapshot_mission(dict(MissionID=1, DestinationSystem='Last'), 'latest', updated)
        self.assertIn('Zielsystem: Last', again['summary'])
        self.assertNotIn('Zielsystem: New', again['summary'])
        self.assertEqual(again['summary'].count('Waren:'), 1)

    def test_custom_summary_and_empty_standard_summary(self):
        for summary in ('Individuelle Journalinformation', ''):
            old = _new_mission({'MissionID': 1})
            old['summary'] = summary
            updated = snapshot_mission({'MissionID': 1, 'DestinationSystem': 'Explicit'}, '', old)
            self.assertIn('Zielsystem: Explicit', updated['summary'])
            if summary:
                self.assertTrue(updated['summary'].endswith(summary))
        old = _new_mission({'MissionID': 1})
        updated = snapshot_mission({'MissionID': 1, 'DestinationSystem': 'Explicit'}, '', old)
        self.assertEqual(updated['summary'], 'Zielsystem: Explicit')

    def test_redirect_without_old_fields_does_not_invent_origin(self):
        mission = _new_mission(dict(MissionID=1, DestinationSystem='Before'))
        _update_mission_event(mission, dict(event='MissionRedirected', MissionID=1,
                                            NewDestinationSystem='After'))
        self.assertEqual(mission['destination_system'], 'After')
        self.assertNotIn('original_destination_system', mission['extra'])

    def test_twelve_languages_present_current_and_original_separately(self):
        self.addCleanup(i18n.set_language, 'de')
        mission = normalize_missions([dict(destination_system='Tir',
                    destination_station='Dohler Depot', summary='Waren: Sample',
                    extra={'original_destination_system': 'Alberta',
                           'original_destination_station': 'Explicit site'})])[0]
        for language in i18n._TRANSLATIONS:
            i18n.set_language(language)
            text = mission_detail_text(mission)
            self.assertIn(i18n.tr('missions.current_destination') + ': Tir – Dohler Depot', text)
            self.assertIn(i18n.tr('missions.original_system') + ': Alberta', text)
            self.assertIn(i18n.tr('missions.original_place') + ': Explicit site', text)
            self.assertIn('Waren: Sample', text)
        self.assertEqual(mission.destination_system, 'Tir')


class DestinationPersistenceTests(unittest.TestCase):
    setUp = base.CurrentMissionsTests.setUp
    apply = base.CurrentMissionsTests.apply
    rows = base.CurrentMissionsTests.rows

    def test_original_case_snapshot_details_after_restart(self):
        self.apply(base.event('MissionAccepted', 1, MissionID=1068930971,
                              Name='Mission_OnFoot_Salvage_MB', Commodity='Sample', Count=1),
                   base.event('MissionAccepted', 2, MissionID=2, DestinationSystem='Other'),
                   base.event('Missions', 3, Active=[
                       dict(MissionID=1068930971, DestinationSystem='Later', DestinationSettlement='Site'),
                       dict(MissionID=2)]))
        self.db = CMDRDatabase(self.db.path)
        rows = {r['mission_id']: r for r in self.rows()}
        self.assertEqual(rows[1068930971]['destination_system'], 'Later')
        self.assertEqual(rows[1068930971]['summary'],
                         'Zielsystem: Later · Ort: Site · Waren: Sample (1x)')
        self.assertEqual(rows[2]['destination_system'], 'Other')
        self.assertEqual(SCHEMA_VERSION, 23)
        with self.db._connect() as con:
            self.assertEqual(con.execute('PRAGMA user_version').fetchone()[0], 23)

    def test_redirect_restart_multiple_redirects_and_commander_isolation(self):
        mid = 1062276997
        self.db.store_commander_missions(self.b, [dict(mission_id=mid, destination_system='B',
            extra={'original_destination_system': 'B origin'})])
        self.apply(base.event('MissionAccepted', 1, MissionID=mid, Name='Mission_OnFoot_Salvage_MB'),
                   base.event('MissionRedirected', 2, MissionID=mid, OldDestinationSystem='Alberta',
                              NewDestinationSystem='Tir', NewDestinationStation='Dohler Depot'))
        self.db = CMDRDatabase(self.db.path)
        row = self.rows()[0]
        self.assertEqual(row['extra'], {'original_destination_system': 'Alberta'})
        self.assertEqual((row['destination_system'], row['destination_station']), ('Tir', 'Dohler Depot'))
        self.apply(base.event('MissionRedirected', 3, MissionID=mid,
                              OldDestinationSystem='Tir', OldDestinationStation='Dohler Depot',
                              NewDestinationSystem='Next', NewDestinationStation='Next Port'),
                   base.event('Missions', 4, Active=[dict(MissionID=mid)]))
        host = SimpleNamespace(database=self.db, commander_id=self.a)
        mission = AppState._visible_commander_missions(host)[0]
        self.assertEqual(mission.extra['original_destination_system'], 'Alberta')
        self.assertNotIn('original_destination_station', mission.extra)
        self.assertEqual(mission.destination_system, 'Next')
        host.commander_id = self.b
        other = AppState._visible_commander_missions(host)[0]
        self.assertEqual(other.extra['original_destination_system'], 'B origin')
        self.assertEqual(other.destination_system, 'B')
        self.apply(base.event('MissionCompleted', 5, MissionID=mid))
        self.assertEqual(self.rows(), [])
        with self.db._connect() as con:
            self.assertIsNone(con.execute("SELECT value FROM app_meta WHERE key=?",
                                          ('mission_origin/A/' + str(mid),)).fetchone())
        self.assertEqual(self.db.commander_missions(self.b)[0]['destination_system'], 'B')

    def test_explicit_original_settlement_is_preserved(self):
        self.apply(base.event('MissionAccepted', 1, MissionID=1062535650,
                              DestinationSystem='Colonia', DestinationSettlement='Fiorentino Hydroponics Estate'),
                   base.event('MissionRedirected', 2, MissionID=1062535650,
                              OldDestinationSystem='Colonia', OldDestinationStation='Fiorentino Hydroponics Estate',
                              NewDestinationSystem='Colonia', NewDestinationStation='Colonia Orbital'))
        self.db = CMDRDatabase(self.db.path)
        row = self.rows()[0]
        self.assertEqual(row['extra']['original_destination_station'], 'Fiorentino Hydroponics Estate')
        self.assertEqual(row['destination_station'], 'Colonia Orbital')
        self.assertNotIn('Ort: Fiorentino Hydroponics Estate', row['summary'])

    def test_metadata_and_mission_rollback_together_and_large_ids(self):
        mid = 2**64 + 1
        mission = dict(mission_id=mid, destination_system='Current',
                       extra={'original_destination_system': 'Origin'})
        with self.assertRaises(RuntimeError):
            with self.db._connect() as con:
                self.db.store_commander_missions(self.a, [mission], _con=con)
                raise RuntimeError('rollback')
        self.assertEqual(self.rows(), [])
        with self.db._connect() as con:
            self.assertIsNone(con.execute("SELECT value FROM app_meta WHERE key=?",
                                         ('mission_origin/A/' + str(mid),)).fetchone())
        self.db.store_commander_missions(self.a, [mission])
        self.assertEqual(self.rows()[0]['extra']['original_destination_system'], 'Origin')
        self.db.store_commander_missions(self.a, [], [dict(mission_id=mid)])
        self.assertEqual(self.rows(), [])


class DestinationDetailViewTests(unittest.TestCase):
    setUpClass = classmethod(ui_base.MissionTableSortTests.setUpClass.__func__)
    setUp = ui_base.MissionTableSortTests.setUp
    make_host = ui_base.MissionTableSortTests.make_host

    def test_actual_details_after_sort_keep_current_target(self):
        missions = normalize_missions([
            dict(mission_id=1, name='Zulu', destination_system='Tir', destination_station='Dohler Depot',
                 extra={'original_destination_system': 'Alberta'}),
            dict(mission_id=2, name='Alpha', destination_system='Other')])
        self.host.state.missions = missions
        self.host._refresh_missions_table()
        self.host.missions_table.horizontalHeader().sectionClicked.emit(0)
        self.host.missions_table.selectRow(1)
        text = self.host.mission_detail_text.text()
        self.assertIn('Aktuelles Ziel: Tir – Dohler Depot', text)
        self.assertIn('Ursprüngliches Zielsystem: Alberta', text)
        self.assertEqual(self.host.missions_table.item(1, 1).text(), 'Tir')
        self.assertEqual(self.host.missions_table.columnCount(), 7)
