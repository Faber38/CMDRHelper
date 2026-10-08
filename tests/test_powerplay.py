import json
import os
from pathlib import Path
import struct
import tempfile
import unittest
from datetime import datetime, timedelta
from unittest.mock import patch

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from PySide6.QtCore import QObject, Signal, QLocale, QPoint
from PySide6.QtWidgets import QApplication, QHeaderView

from cmdrhelper.i18n import set_language, tr
from cmdrhelper.journal_reader import read_latest_state, classify_journal_file
from cmdrhelper.powerplay import (
    PowerplayState, PowersCache, PowerplayCacheError, _crypt, decode_powers_cache,
    powers_cache_path, context, action_token, ACTION_TOKENS,
)
from cmdrhelper.ui.powerplay_view import PowerplayView


def event(kind, **values):
    return dict(event=kind, timestamp='2026-10-06T10:14:23Z', **values)


def table_text(view):
    return '\n'.join(view.recent.item(row, col).text()
                     for row in range(view.recent.rowCount()) for col in range(5))


def cache_bytes(powers=None):
    if powers is None:
        powers = [dict(id=123, name='Test Power', ethos=dict(
            reinforcement=['$PP2_Action_BountyHunting; (Ethos-Bonus)'],
            acquisition=['$PP2_Action_SellExoticGoods;'],
            undermining=['$PP2_Action_CommitCrimes;'],
            conflict=['$PP2_Action_ScanDatalinks;']))]
    payload = json.dumps(dict(powers=powers)).encode()
    header = struct.pack('<IBH', 3, 1, 6) + b'german'
    header += struct.pack('<H', 14) + b'api.orerve.net' + struct.pack('<HHI', 0, 65535, len(payload))
    return _crypt(header + payload)


class PowerplayTests(unittest.TestCase):
    def setUp(self):
        self.data = PowerplayState()

    def test_join_and_rank_reverse_order_preserves_explicit_rank(self):
        self.data.apply(event('PowerplayRank', Power='Test Power', Rank=0))
        self.data.apply(event('PowerplayJoin', Power='Test Power'))
        self.assertEqual(self.data.power, 'Test Power')
        self.assertEqual(self.data.rank, 0)
        self.assertIsNone(self.data.merits)
        self.assertEqual(self.data.joined.isoformat(), '2026-10-06T10:14:23+00:00')

    def test_snapshot_and_elapsed_pledge(self):
        self.data.apply(event('Powerplay', Power='Test Power', Rank=4, Merits=5563, TimePledged=60))
        self.assertEqual((self.data.rank, self.data.merits), (4, 5563))
        self.assertEqual(self.data.joined.isoformat(), '2026-10-06T10:13:23+00:00')
        self.assertTrue(self.data.joined_estimated)

    def test_explicit_join_wins_over_rounded_elapsed(self):
        self.data.apply(event('PowerplayJoin', Power='Test Power'))
        self.data.apply(event('Powerplay', Power='Test Power', Rank=0, Merits=0, TimePledged=60))
        self.assertEqual(self.data.joined.second, 23)
        self.assertEqual(self.data.joined.minute, 14)
        self.assertFalse(self.data.joined_estimated)

    def test_merits_use_total_not_guessed_sum(self):
        self.data.apply(event('PowerplayMerits', Power='Test Power', MeritsGained=3200, TotalMerits=5563))
        self.assertEqual(self.data.merits, 5563)
        self.assertEqual(self.data.recent[0].gained, 3200)
        self.assertNotIn('assignment', repr(self.data).lower())
        self.data.apply(event('PowerplayMerits', Power='Test Power', MeritsGained=10))
        self.assertEqual(self.data.merits, 5563)

    def test_change_and_leave_clear_personal_fields(self):
        self.data.apply(event('Powerplay', Power='Old', Rank=4, Merits=999, TimePledged=1))
        self.data.apply(event('PowerplayJoin', Power='New'))
        self.assertIsNone(self.data.rank)
        self.assertIsNone(self.data.merits)
        self.data.apply(event('PowerplayLeave', Power='New'))
        self.assertFalse(self.data.power)
        self.assertTrue(self.data.membership_known)

    def test_malformed_personal_values(self):
        self.data.apply(event('Powerplay', Power='Test', Rank=True, Merits=-1, TimePledged=2**63))
        self.assertIsNone(self.data.rank)
        self.assertIsNone(self.data.merits)
        self.assertIsNone(self.data.joined)

    def test_relationships(self):
        self.data.power = 'Test Power'
        for owner, expected in [('Test Power', ('own', 'reinforcement')), ('Other', ('opposing', 'undermining'))]:
            self.data.apply(event('FSDJump', StarSystem='Here', ControllingPower=owner, PowerplayState='Exploited'))
            self.assertEqual(context(self.data), expected)
        self.data.apply(event('FSDJump', StarSystem='Empty', PowerplayState='Unoccupied', Powers=['Test Power']))
        self.assertEqual(context(self.data), ('unoccupied', 'acquisition'))

    def test_unoccupied_requires_own_power_evidence(self):
        self.data.power = 'Test Power'
        self.data.apply(event('Location', PowerplayState='Unoccupied', Powers=['Other']))
        self.assertEqual(context(self.data), ('unoccupied', None))
        self.data.apply(event('Location', PowerplayState='Unoccupied'))
        self.assertEqual(context(self.data), ('unoccupied', None))

    def test_multiple_powers_do_not_guess_activity_category(self):
        self.data.power = 'Test Power'
        self.data.apply(event('Location', PowerplayState='Unoccupied', PowerplayConflictProgress=[
            dict(Power='Test Power', ConflictProgress=0), dict(Power='Other', ConflictProgress=.4)]))
        self.assertEqual(context(self.data), ('unoccupied', None))

    def test_missing_new_system_fields_never_inherit_old_context(self):
        self.data.power = 'Test Power'
        self.data.apply(event('Location', StarSystem='A', PowerplayState='Stronghold', ControllingPower='Test Power'))
        self.data.apply(event('FSDJump', StarSystem='B'))
        self.assertEqual(context(self.data), ('unknown', None))
        self.assertNotIn('ControllingPower', self.data.system)

    def test_no_membership_or_missing_controller_no_recommendation(self):
        self.data.apply(event('Location', PowerplayState='Fortified', ControllingPower='Other'))
        self.assertEqual(context(self.data), ('unknown', None))
        self.data.power = 'Test Power'
        self.data.apply(event('Location', PowerplayState='Exploited', Powers=['Test Power']))
        self.assertEqual(context(self.data), ('unknown', None))

    def test_commander_isolation_and_indexed_live_replay(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            a = folder / 'Journal.2026-10-05T100000.01.log'
            a.write_text(json.dumps(event('Commander', FID='A', Name='Alpha'))+'\n'+json.dumps(event('Powerplay', Power='Other', Rank=9, Merits=999))+'\n')
            b = folder / 'Journal.2026-10-06T100000.01.log'
            initial = [event('Commander', FID='B', Name='Beta'), event('PowerplayJoin', Power='Test Power'), event('PowerplayRank', Power='Test Power', Rank=0)]
            b.write_text(''.join(json.dumps(e)+'\n' for e in initial))
            sessions = [classify_journal_file(p) for p in (a, b)]
            first = read_latest_state(folder, indexed_sessions=sessions)['powerplay']
            self.assertEqual(first.power, 'Test Power')
            self.assertIsNone(first.merits)
            with b.open('a') as f:
                f.write(json.dumps(event('PowerplayMerits', Power='Test Power', MeritsGained=3200, TotalMerits=3300))+'\n')
            second = read_latest_state(folder, indexed_sessions=sessions)['powerplay']
            third = read_latest_state(folder, indexed_sessions=sessions)['powerplay']
            self.assertEqual(second.merits, 3300)
            self.assertEqual(len(second.recent), 1)
            self.assertEqual(second, third)
            self.assertEqual(read_latest_state(folder)['powerplay'].merits, 3300)


class CacheTests(unittest.TestCase):
    def test_valid_cache(self):
        self.assertEqual(decode_powers_cache(cache_bytes())['Test Power']['id'], 123)

    def test_bad_headers_lengths_json_and_shapes(self):
        good = _crypt(cache_bytes())
        variants = [b'', b'garbage', _crypt(b'\x04'+good[1:]), _crypt(good[:4]+b'\x00'+good[5:]),
                    _crypt(good[:31]+b'\x00\x00'+good[33:]), _crypt(good[:-1]),
                    _crypt(good+b'X'), _crypt(good[:37]+b'X'+good[38:]),
                    cache_bytes([]), cache_bytes([{'name':'X','id':1,'ethos':{'reinforcement':'bad'}}])]
        for raw in variants:
            with self.subTest(length=len(raw)), self.assertRaises(PowerplayCacheError):
                decode_powers_cache(raw)

    def test_missing_corrupt_replaced_and_recovered_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'powers.cache'
            cache = PowersCache()
            self.assertIsNone(cache.load(path))
            path.write_bytes(cache_bytes())
            original = path.read_bytes()
            self.assertIn('Test Power', cache.load(path))
            self.assertEqual(path.read_bytes(), original)
            path.write_bytes(b'corrupt')
            self.assertIsNone(cache.load(path))
            path.write_bytes(original)
            self.assertIn('Test Power', cache.load(path))

    def test_profile_path_and_unknown_location(self):
        profile = Path('/tmp/example-profile')
        journals = profile/'Saved Games/Frontier Developments/Elite Dangerous'
        self.assertEqual(powers_cache_path(journals), profile/'AppData/Local/Frontier Developments/Elite Dangerous/GalacticPoliticsPowers2.cache')
        self.assertIsNone(powers_cache_path(None))

    def test_tokens_and_localization(self):
        for language in ['de','en']:
            set_language(language)
            for token in ACTION_TOKENS:
                self.assertEqual(action_token('$PP2_Action_'+token+'; (Ethos-Bonus)'), token)
                self.assertNotEqual(tr('pp2.action.'+token), 'pp2.action.'+token)
        set_language('de')
        self.assertIsNone(action_token('$PP2_Action_FutureAction;'))


class ViewState(QObject):
    changed = Signal()
    cargoSnapshotChanged = Signal(object)

    def __init__(self):
        super().__init__()
        self.system = 'Here'
        self.journal_folder = None
        self.powerplay = PowerplayState()
        self.powerplay.apply(event('Powerplay', Power='Test Power', Rank=0, Merits=0, TimePledged=1))
        self.powerplay.apply(event('Location', StarSystem='Here', ControllingPower='Test Power', PowerplayState='Exploited', PowerplayStateReinforcement=0))


class PowerplayViewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        clock = patch('cmdrhelper.ui.powerplay_view.local_today', return_value=datetime(2026, 10, 6).date())
        clock.start()
        self.addCleanup(clock.stop)
        set_language('de')
        self.state = ViewState()
        self.view = PowerplayView(self.state)
        self.view.resize(1050, 900)
        self.view.show()
        self.addCleanup(self.view.close)
        self.powers = decode_powers_cache(cache_bytes())
        mock = patch.object(self.view.cache, 'load', return_value=self.powers)
        self.loader = mock.start()
        self.addCleanup(mock.stop)
        self.view.render()

    def test_live_merits_and_neutral_history(self):
        self.state.powerplay.apply(event('PowerplayMerits', Power='Test Power', MeritsGained=3200, TotalMerits=5563))
        self.state.changed.emit()
        self.assertEqual(self.view.personal['merits'].text(), '5.563')
        self.assertIn('+3.200', table_text(self.view))
        self.assertNotIn('abgeschlossen', table_text(self.view).lower())
        self.assertEqual(self.view.personal['rank'].text(), '0')

    def test_responsive_columns_and_left_personal_card(self):
        preserved = (self.view.personal_card, self.view.portrait, self.view.rank_bar,
                     self.view.system_presentation, self.view.cargo_card,
                     self.view.action_section, self.view.actions, self.view.recent)
        self.view.resize(1200, 900)
        self.app.processEvents()
        self.assertTrue(self.view._two_columns)
        left, right = self.view.left_column, self.view.right_column
        self.assertEqual(left.y(), right.y())
        self.assertGreater(right.x(), left.x() + left.width())
        self.assertGreater(right.width(), left.width())
        self.assertAlmostEqual(left.width() / (left.width() + right.width()), .4, delta=.04)
        self.assertEqual(self.view.personal_card.parentWidget(), left)
        self.assertEqual(self.view.personal_card.width(), left.width())
        self.assertEqual(self.view.personal_card.y(), 0)
        self.assertEqual(self.view.action_section.y(), 0)
        self.assertGreater(self.view.system_card.y(), self.view.personal_card.y())
        self.assertEqual(self.view.cargo_card.parentWidget(), right)
        self.assertEqual(self.view.cargo_card.width(), right.width())
        self.assertEqual(self.view.cargo_card.y(),
                         self.view.action_section.height()+right.layout().spacing())
        self.assertGreaterEqual(self.view.recent_section.y(), max(left.y()+left.height(), right.y()+right.height()))
        self.assertEqual(self.view.recent_section.width(), left.width()+right.width()+self.view.columns.spacing())
        self.assertEqual(self.view.recent_section.x(), left.x())
        self.assertLess(self.view.cargo_card.height(), left.height() / 3)
        self.assertEqual(self.view.horizontalScrollBar().maximum(), 0)
        self.view.resize(480, 900)
        self.app.processEvents()
        self.assertFalse(self.view._two_columns)
        self.assertEqual(left.x(), right.x())
        self.assertGreaterEqual(right.y(), left.y() + left.height())
        self.assertGreaterEqual(self.view.recent_section.y(), right.y()+right.height())
        self.assertEqual(self.view.horizontalScrollBar().maximum(), 0)
        self.view.resize(1200, 900)
        self.app.processEvents()
        self.assertTrue(self.view._two_columns)
        self.assertEqual(self.view.columns.count(), 2)
        self.assertEqual(preserved, (self.view.personal_card, self.view.portrait, self.view.rank_bar,
                                    self.view.system_presentation, self.view.cargo_card,
                                    self.view.action_section, self.view.actions, self.view.recent))

    def test_chronicle_header_and_remaining_height(self):
        self.view.resize(1200,900)
        self.app.processEvents()
        def top(widget):
            return widget.mapTo(self.view.widget(),QPoint(0,0)).y()
        widgets=(self.view.chronicle_title,self.view.navigation,self.view.manage_history)
        centers=[top(w)+w.height()/2 for w in widgets]
        self.assertLess(max(centers)-min(centers),3)
        self.assertGreater(top(self.view.chronicle_help),max(top(w)+w.height() for w in widgets))
        height=self.view.recent.height()
        middle=self.view.left_column.height()
        self.view.resize(1200,1100)
        self.app.processEvents()
        self.assertGreaterEqual(self.view.recent.height()-height,190)
        self.assertEqual(self.view.left_column.height(),middle)
        self.view.resize(480,900)
        self.app.processEvents()
        self.assertGreater(top(self.view.navigation),top(self.view.chronicle_title))
        self.assertGreater(top(self.view.manage_history),top(self.view.navigation))

    def test_dark_layout_preserves_full_recommendations_across_breakpoints(self):
        from cmdrhelper.ui.styles import DARK_STYLESHEET
        fixture = json.loads((Path(__file__).parent/'fixtures/powerplay_ethos_20261007.json').read_text())
        powers = {p['name']:p for p in fixture['powers']}
        self.loader.return_value = powers
        self.state.powerplay.power = 'Nakato Kaine'
        self.state.powerplay.system.update(ControllingPower='Nakato Kaine',
                                          PowerplayStateReinforcement=12000,
                                          PowerplayStateUndermining=4000)
        self.view.setStyleSheet(DARK_STYLESHEET)
        self.view.render()
        recommendations = self.view.actions.text()
        self.assertGreater(len(recommendations.splitlines()), 10)
        widgets = (self.view.personal_card, self.view.system_card, self.view.cargo_card,
                   self.view.actions, self.view.recent, self.view.navigation)
        for width in (1400, 1000, 480, 360, 1400):
            self.view.resize(width, 1000)
            for _ in range(3):
                self.app.processEvents()
            self.view.render()
            self.app.processEvents()
            with self.subTest(width=width):
                self.assertEqual(self.view.actions.text(), recommendations)
                self.assertEqual(self.view.horizontalScrollBar().maximum(), 0)
                self.assertEqual(self.view._two_columns, width >= 1000)
                self.assertEqual(self.view.cargo_card.parentWidget(), self.view.right_column)
                self.assertEqual(self.view.cargo_card.y(), self.view.action_section.height()
                                 + self.view.right_column.layout().spacing())
                for label in (self.view.actions, self.view.action_heading, self.view.notice):
                    self.assertGreaterEqual(label.height(), label.heightForWidth(label.width()))
                self.assertEqual(widgets, (self.view.personal_card, self.view.system_card,
                                          self.view.cargo_card, self.view.actions,
                                          self.view.recent, self.view.navigation))
        # Cargo follows long advice immediately, without overlapping or gaps.
        self.view.actions.setText('\n'.join([recommendations] * 4))
        for _ in range(3):
            self.app.processEvents()
        self.assertGreater(self.view.action_section.height(),
                           self.view.system_card.y()+self.view.system_card.height())
        self.assertEqual(self.view.cargo_card.y(), self.view.action_section.height()
                         + self.view.right_column.layout().spacing())
        self.assertGreaterEqual(self.view.actions.height(),
                                self.view.actions.heightForWidth(self.view.actions.width()))
        expanded = self.view.action_section.height()
        self.view.render()
        for _ in range(3):
            self.app.processEvents()
        self.assertLess(self.view.action_section.height(), expanded)
        self.assertEqual(self.view.actions.text(), recommendations)

    def test_table_details_priority_and_narrow_width(self):
        self.state.powerplay.apply(event('PowerplayDeliver',Power='Test Power',Type='item',Count=10))
        for _ in range(8):
            self.state.powerplay.apply(event('PowerplayMerits',Power='Test Power',MeritsGained=3600,TotalMerits=3600))
        self.view.render()
        for width in (1200,480,360,1200):
            self.view.resize(width,900)
            self.app.processEvents()
            table=self.view.recent
            self.assertEqual(table.horizontalHeader().sectionResizeMode(2),QHeaderView.Interactive)
            self.assertEqual(self.view.horizontalScrollBar().maximum(),0)
            self.assertEqual(table.horizontalScrollBar().maximum(),0)
            if width==1200:
                self.assertGreater(table.columnWidth(2),max(table.columnWidth(i) for i in (0,1,3,4)))

    def test_metrics_share_compact_line_without_changing_values(self):
        self.state.powerplay.system.update(PowerplayStateControlProgress=.25,
            PowerplayStateReinforcement=12345,PowerplayStateUndermining=6789)
        self.view.render()
        self.assertNotIn('\n',self.view.metrics.text())
        self.assertIn('0,25',self.view.metrics.text())
        self.assertEqual(self.view.system_presentation.strengths['reinforcement'].text(),'12.345')
        self.assertEqual(self.view.system_presentation.strengths['undermining'].text(),'6.789')

    def test_shared_themes_do_not_force_horizontal_page_scrolling(self):
        from cmdrhelper.ui.styles import DARK_STYLESHEET, LIGHT_STYLESHEET
        for theme in (DARK_STYLESHEET,LIGHT_STYLESHEET):
            self.view.setStyleSheet(theme)
            for width in (1200,480,360):
                self.view.resize(width,900)
                self.app.processEvents()
                self.assertEqual(self.view.horizontalScrollBar().maximum(),0)
                self.assertEqual(self.view.recent.horizontalScrollBar().maximum(),0)
        header=self.view.recent.horizontalHeaderItem(4)
        self.assertEqual(header.toolTip(),header.text())

    def test_activity_dates_compact_in_local_timezone(self):
        at = datetime.fromisoformat('2026-10-06T23:14:23+00:00')
        local = at.astimezone()
        locale = QLocale('de')
        self.assertEqual(self.view._activity_time(at, locale, local.date()), local.strftime('%H:%M'))
        self.assertEqual(self.view._activity_time(at, locale, local.date() + timedelta(days=1)),
                         locale.toString(local.date(), QLocale.ShortFormat) + ' ' + local.strftime('%H:%M'))

    def test_activity_tooltip_preserves_exact_timestamps_and_context(self):
        self.state.powerplay.apply(event('Docked', StarSystem='Here', StationName='Station'))
        self.state.powerplay.apply(event('PowerplayDeliver', Power='Test Power', Type='item', Count=10))
        self.state.powerplay.apply(event('PowerplayMerits', Power='Test Power', MeritsGained=48, TotalMerits=48))
        self.state.changed.emit()
        tooltip = self.view.recent.item(0, 4).toolTip()
        self.assertEqual(tooltip.count('2026-10-06T10:14:23Z'), 2)
        self.assertIn('Station · Here', tooltip)
        self.assertIn('+48 Merits', tooltip)
        self.assertIn('10 × item', tooltip)
        self.assertIn('PP2-Abgabe', tooltip)

    def test_status_translations_and_zero_metrics(self):
        for status, text in [('Exploited','Erschlossen'), ('Fortified','Verstärkt'), ('Stronghold','Hochburg'), ('POWERPLAY_STATE_UNOCCUPIED','Nicht besetzt')]:
            self.state.powerplay.system['PowerplayState'] = status
            self.view.render()
            self.assertEqual(self.view.system_labels['status'].text(), text)
        self.state.powerplay.system['PowerplayState'] = 'Exploited'
        self.view.render()
        self.assertEqual(self.view.system_presentation.strengths['reinforcement'].text(),'0')

    def test_activities_are_selected_from_actual_power(self):
        self.assertIn('Kopfgeldjagd', self.view.actions.text())
        self.state.powerplay.system['ControllingPower'] = 'Other'
        self.view.render()
        self.assertIn('Verbrechen', self.view.actions.text())
        self.assertNotIn('Kopfgeldjagd', self.view.actions.text())

    def test_missing_cache_unknown_power_and_unknown_action(self):
        self.loader.return_value = None
        self.view.render()
        self.assertIn('PP2-Daten nicht verfügbar', self.view.notice.text())
        self.assertEqual(self.view.personal['power'].text(), 'Test Power')
        self.loader.return_value = {}
        self.view.render()
        self.assertIn('Keine Aktivitätsdaten', self.view.actions.text())
        self.loader.return_value = self.powers
        self.powers['Test Power']['ethos']['reinforcement'] = ['$PP2_Action_FutureAction;']
        self.view.render()
        self.assertIn('Unbekannte Aktivität', self.view.actions.text())

    def test_no_membership_and_stale_system(self):
        self.state.powerplay.apply(event('PowerplayLeave', Power='Test Power'))
        self.view.render()
        self.assertEqual(self.view.personal['power'].text(), 'Keine Machtzugehörigkeit')
        self.assertIn('Keine Machtzugehörigkeit', self.view.actions.text())
        self.state.powerplay.power = 'Test Power'
        self.state.system = 'Elsewhere'
        self.view.render()
        self.assertEqual(self.view.system_labels['owner'].text(), 'Unbekannt')
        self.assertIn('keine eindeutige Empfehlung', self.view.actions.text())


if __name__ == '__main__':
    unittest.main()
