"""Single-line PP2 presentation with synthetic groups only."""
import copy
import unittest

from PySide6.QtCore import Qt

from cmdrhelper.powerplay_chronicle import ChronicleGroup
from cmdrhelper.ui.styles import DARK_STYLESHEET, LIGHT_STYLESHEET
from tests import test_powerplay as base


class CompactChronicleTests(unittest.TestCase):
    setUpClass = classmethod(base.PowerplayViewTests.setUpClass.__func__)
    setUp = base.PowerplayViewTests.setUp

    def populate(self):
        events = [
            ('ShipTargeted', dict(PilotName_Localised='Justice', Ship_Localised='Type-6 Transporter')),
            ('ShipTargeted', dict(PilotName_Localised='Schiff der Systembehörden', Ship_Localised='Viper Mk III')),
            ('PowerplayMerits', {}),
            ('MarketSell', dict(Type='silver', Type_Localised='Silber', Count=43)),
            ('PowerplayCollect', dict(Type_Localised='Berichte', Count=10)),
            ('PowerplayDeliver', dict(Type_Localised='Berichte', Count=10)),
            ('SearchAndRescue', dict(Name_Localised='Rettungskapseln', Count=2)),
            ('Bounty', dict(Target_Localised='Viper Mk III', TotalReward=10000)),
            ('ShipTargeted', dict(PilotName_Localised='Long pilot ' * 30, Ship_Localised='Long ship ' * 30)),
            ('ShipTargeted', dict(PilotName_Localised='First line\n\nSecond line', Ship_Localised='Ship')),
        ]
        groups = []
        for index, (kind, fields) in enumerate(events):
            stamp = f'2026-10-06T10:{index:02}:00Z'
            groups.append(ChronicleGroup(
                dict(timestamp=stamp, event=kind, **fields),
                'unknown' if kind == 'PowerplayMerits' else 'explicit',
                system='Col 285 Sector OF-R b20-0',
                station='Stronghold Carrier' if kind == 'MarketSell' else '',
                credits=[dict(timestamp=stamp, MeritsGained=index + 1, TotalMerits=12345)]))
        self.state.powerplay.chronicle.groups = groups
        return groups

    def test_all_supported_details_are_single_line_and_complete(self):
        self.populate()
        self.view.render()
        table = self.view.recent
        details = [table.item(row, 2).text() for row in range(table.rowCount())]
        self.assertIn('Justice · Type-6 Transporter | Col 285 Sector OF-R b20-0', details)
        self.assertIn('Schiff der Systembehörden · Viper Mk III | Col 285 Sector OF-R b20-0', details)
        self.assertIn('43 t Silber | Stronghold Carrier · Col 285 Sector OF-R b20-0', details)
        for row, text in enumerate(details):
            self.assertNotIn('\n', text)
            self.assertNotIn('\r', text)
            self.assertIn(' | ', text)
            self.assertIn(text, table.item(row, 2).toolTip())
        self.assertIn('First line | Second line · Ship', details[0])

    def test_widths_themes_elision_heights_order_and_merits(self):
        groups = self.populate()
        before = copy.deepcopy(groups)
        self.view.render()
        totals = tuple(self.view.personal[key].text() for key in ('rank', 'merits'))
        table = self.view.recent
        baseline = [tuple(table.item(row, col).text() for col in (0, 1, 3, 4))
                    for row in range(table.rowCount())]
        for theme in (DARK_STYLESHEET, LIGHT_STYLESHEET):
            self.view.setStyleSheet(theme)
            for width in (480, 1600):
                with self.subTest(theme=theme[:30], width=width):
                    self.view.resize(width, 1000)
                    self.app.processEvents()
                    self.view.render()
                    self.app.processEvents()
                    self.assertFalse(table.wordWrap())
                    self.assertEqual(table.textElideMode(), Qt.ElideRight)
                    self.assertEqual(len({table.rowHeight(row) for row in range(table.rowCount())}), 1)
                    self.assertEqual(baseline, [tuple(table.item(row, col).text() for col in (0, 1, 3, 4))
                                               for row in range(table.rowCount())])
                    long = table.item(1, 2)
                    elided = table.fontMetrics().elidedText(long.text(), table.textElideMode(), table.columnWidth(2))
                    self.assertTrue(elided.endswith('…'))
                    self.assertIn(long.text(), long.toolTip())
                    if width == 1600:
                        short = table.item(table.rowCount() - 1, 2).text()
                        self.assertEqual(table.fontMetrics().elidedText(short, Qt.ElideRight, table.columnWidth(2)), short)
                    self.assertFalse(table.grab().isNull())
        self.assertEqual(groups, before)
        self.assertEqual(tuple(self.view.personal[key].text() for key in ('rank', 'merits')), totals)
