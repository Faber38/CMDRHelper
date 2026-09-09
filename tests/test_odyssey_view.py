import copy
import json
from pathlib import Path
import sqlite3
import tempfile
import threading
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from PySide6.QtCore import QSettings, QTimer, Qt, QPoint, QEvent
from PySide6.QtGui import QPalette
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QStyleOptionViewItem, QStyle

from cmdrhelper.i18n import set_language, get_language, _TRANSLATIONS
from cmdrhelper.odyssey_inventory import OdysseyInventory, OdysseyReducer
from cmdrhelper.odyssey_controller import OdysseyController
from cmdrhelper.ui.material_view import MaterialView
from cmdrhelper.ui.material_row_style import THEMES, COLLECTED_ROLE
from cmdrhelper.ui.odyssey_view import STOCK_TEXT_COLORS
from cmdrhelper.ui.styles import DARK_STYLESHEET, LIGHT_STYLESHEET
from test_material_view import State, StubController
from test_odyssey_inventory import event, item, snapshot


def inventory(records=(), cid=1):
    reducer = OdysseyReducer(cid, f'F{cid}')
    for i, record in enumerate(records):
        reducer.apply(record, ('journal', i))
    return reducer.result


def pair():
    return [snapshot('ShipLocker', Components=[item(count=10)],
                     Items=[item('vehicleschematic', 1, MissionID=42), item('vehicleschematic', 2)]),
            snapshot('Backpack', Components=[item(count=2)])]


class OdysseyViewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.addCleanup(set_language, get_language())
        set_language('de')
        self.addCleanup(self.app.setStyleSheet, self.app.styleSheet())
        self.state = SimpleNamespace(settings=QSettings(str(Path(self.tmp.name)/'ui.ini'), QSettings.Format.IniFormat))
        self.controller = StubController()
        self.page = MaterialView(self.state, controller=StubController(), odyssey_controller=self.controller)
        self.addCleanup(self.page.close)
        self.page.resize(1100, 750)
        self.page.show()
        self.page.tabs.setCurrentIndex(3)
        self.view = self.page.odyssey
        self.set_inventory(inventory([snapshot('ShipLocker'), snapshot('Backpack')]))
        self.app.processEvents()

    def set_inventory(self, inv):
        self.controller.ready.emit(copy.deepcopy(inv), f'Commander {inv.commander_id}')

    def rows(self, name):
        return [(key, value) for key, value in self.view.items.items() if key.name == name]

    def select_filter(self, key):
        self.view.filter.setCurrentIndex(self.view.filter.findData(key))

    def test_four_main_tabs_gold_and_four_flat_categories(self):
        self.assertEqual(self.page.tabs.count(), 4)
        self.assertEqual(self.page.tabs.tabText(3), 'Odyssey')
        self.assertEqual(self.view.tabs.count(), 4)
        self.assertFalse(self.page.tree.isVisible())
        for index, count in enumerate((61, 33, 123, 6)):
            self.view.tabs.setCurrentIndex(index)
            self.assertEqual(len(self.view.items), count)
            self.assertEqual(self.view.tree.topLevelItemCount(), count)
            self.assertTrue(all(v.childCount() == 0 for v in self.view.items.values()))
        for light in (False, True):
            self.page.set_light_mode(light)
            self.assertEqual(self.page.tabs.active_border_color.name(), '#9a620e' if light else '#c57a00')
            self.assertEqual(self.view.tabs.light, light)

    def test_search_localized_english_and_combined_filter(self):
        self.set_inventory(inventory(pair()))
        for query in ('Fahrzeugplan', 'Vehicle Schematic'):
            self.page.search.setText(query)
            self.assertEqual(len(self.view.items), 2)
            self.select_filter('mission')
            self.assertEqual(len(self.view.items), 1)
            self.assertEqual(next(iter(self.view.items)).mission_id, 42)
            self.select_filter('all')
        self.page.search.setText('no such item')
        self.assertFalse(self.view.items)

    def test_six_filters_with_known_and_unknown_counts(self):
        self.set_inventory(inventory(pair()))
        self.assertEqual(self.view.filter.count(), 6)
        for key, expected in (('all', 62), ('mission', 1), ('engineering', None), ('backpack', 0), ('locker', 2), ('empty', 60)):
            self.select_filter(key)
            if expected is not None:
                self.assertEqual(len(self.view.items), expected, key)
            else:
                self.assertTrue(self.view.items)
                self.assertTrue(all('Engineering' in v.text(4) for v in self.view.items.values()))
        self.set_inventory(OdysseyInventory(1, 'F1'))
        self.assertFalse(self.view.items)
        self.select_filter('all')
        self.assertEqual(len(self.view.items), 61)
        self.assertTrue(all(v.text(3) == '?' for v in self.view.items.values()))

    def test_separate_mission_completed_owner_and_stolen_stacks(self):
        records = pair() + [event('MissionCompleted', 1, MissionID=42)]
        self.set_inventory(inventory(records))
        mission = [(k, v) for k, v in self.rows('vehicleschematic') if k.mission_id][0]
        self.assertEqual(mission[1].text(3), '1')
        self.assertIn('Mission', mission[1].text(4))
        self.assertIn('42: abgeschlossen', mission[1].toolTip(4))
        normal = [(k, v) for k, v in self.rows('vehicleschematic') if not k.mission_id][0]
        self.assertEqual(normal[1].text(3), '2')
        self.assertNotIn('Mission', normal[1].text(4))
        records = [snapshot('ShipLocker', Items=[dict(Name='vehicleschematic', Count=3, OwnerID=7, Stolen=True),
                                               dict(Name='vehicleschematic', Count=4, OwnerID=8)]), snapshot('Backpack')]
        self.set_inventory(inventory(records))
        self.assertEqual(len(self.rows('vehicleschematic')), 2)
        self.assertTrue(any('Gestohlen' in v.text(4) for k,v in self.rows('vehicleschematic')))

    def test_engineering_tooltip_and_special_groups(self):
        self.view.tabs.setCurrentIndex(1)
        row = self.rows('graphene')[0][1]
        self.assertIn('Engineering', row.text(4))
        self.assertTrue('Modifikation' in row.toolTip(4) or 'Upgrade' in row.toolTip(4))
        seen = set()
        for index in range(4):
            self.view.tabs.setCurrentIndex(index)
            for row in self.view.rows:
                if row.definition and row.definition.special_group != 'standard' and row.key in self.view.items:
                    seen.add(row.definition.special_group)
                    self.assertTrue(self.view.items[row.key].text(4))
        self.assertEqual(seen, {'powerplay', 'thargoid_spire', 'operations', 'unica'})

    def test_only_usage_column_centered_in_all_categories_and_themes(self):
        self.set_inventory(inventory(pair() + [snapshot('ShipLocker', 1, Items=[
            item('vehicleschematic', 1, MissionID=42, Stolen=True),
        ])]))
        horizontal = Qt.AlignmentFlag.AlignHorizontal_Mask
        for light in (False, True):
            self.app.setStyleSheet(LIGHT_STYLESHEET if light else DARK_STYLESHEET)
            self.page.set_light_mode(light)
            seen = set()
            for category in range(4):
                with self.subTest(light=light, category=category):
                    self.view.tabs.setCurrentIndex(category)
                    header = self.view.tree.headerItem()
                    self.assertEqual(header.textAlignment(4) & horizontal, Qt.AlignmentFlag.AlignHCenter)
                    for col in range(4):
                        self.assertIsNone(header.data(col, Qt.ItemDataRole.TextAlignmentRole))
                    for row in self.view.items.values():
                        seen.update(row.text(4).split(' · '))
                        self.assertEqual(row.textAlignment(4) & horizontal, Qt.AlignmentFlag.AlignHCenter)
                        self.assertIsNone(row.data(0, Qt.ItemDataRole.TextAlignmentRole))
                        for col in (1, 2, 3):
                            self.assertEqual(row.textAlignment(col),
                                             Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.assertTrue({'Engineering', 'Powerplay', 'Mission', 'Gestohlen'} <= seen, seen)

    def test_stock_text_colors_in_both_themes_and_row_states(self):
        def style(row, column, selected=False):
            option = QStyleOptionViewItem()
            option.initFrom(self.view.tree)
            if selected:
                option.state |= QStyle.StateFlag.State_Selected
            self.view.row_delegate.initStyleOption(option, self.view.tree.indexFromItem(row, column))
            return option

        self.set_inventory(inventory(pair()))
        self.view.tabs.setCurrentIndex(1)
        for light in (False, True):
            with self.subTest(light=light):
                self.app.setStyleSheet(LIGHT_STYLESHEET if light else DARK_STYLESHEET)
                self.page.set_light_mode(light)
                self.app.processEvents()
                row = self.rows('graphene')[0][1]
                self.assertEqual([row.text(col) for col in (1, 2, 3)], ['10', '2', '12'])
                for col in (1, 2, 3):
                    option = style(row, col)
                    self.assertEqual(option.palette.color(QPalette.ColorRole.Text).name(),
                                     STOCK_TEXT_COLORS[light])
                for col in (0, 4):
                    option = style(row, col)
                    self.assertEqual(option.palette.color(QPalette.ColorRole.Text).name(),
                                     THEMES[light]['text'])
                QTest.mouseMove(self.view.tree.header().viewport(), QPoint(10, 5))
                QTest.mouseMove(self.view.tree.viewport(), self.view.tree.visualItemRect(row).center())
                for col in (1, 2, 3):
                    hovered = style(row, col)
                    self.assertEqual(hovered.backgroundBrush.color().name(), THEMES[light]['hover'])
                    self.assertEqual(hovered.palette.color(QPalette.ColorRole.Text).name(), STOCK_TEXT_COLORS[light])
                    selected = style(row, col, selected=True)
                    self.assertEqual(selected.backgroundBrush.color().name(), THEMES[light]['selected'])
                    self.assertEqual(selected.palette.color(QPalette.ColorRole.Text).name(), THEMES[light]['selected_text'])

    def test_zero_and_unknown_stock_keep_normal_text_and_tooltips(self):
        for inv, expected in ((inventory([snapshot('ShipLocker'), snapshot('Backpack')]), '0'),
                              (OdysseyInventory(1, 'F1'), '?')):
            self.set_inventory(inv)
            for light in (False, True):
                self.app.setStyleSheet(LIGHT_STYLESHEET if light else DARK_STYLESHEET)
                self.page.set_light_mode(light)
                for row in self.view.items.values():
                    for col in (1, 2, 3):
                        with self.subTest(value=expected, light=light, column=col):
                            self.assertEqual(row.text(col), expected)
                            option = QStyleOptionViewItem()
                            option.initFrom(self.view.tree)
                            self.view.row_delegate.initStyleOption(option, self.view.tree.indexFromItem(row, col))
                            self.assertEqual(option.palette.color(QPalette.ColorRole.Text).name(), THEMES[light]['text'])
                            self.assertEqual(row.toolTip(col), _TRANSLATIONS['de']['materials.unknown_stock'] if expected == '?' else '')

    def test_containers_totals_and_no_per_item_bars(self):
        self.set_inventory(inventory(pair()))
        self.view.tabs.setCurrentIndex(1)
        row = self.rows('graphene')[0][1]
        self.assertEqual([row.text(i) for i in (1,2,3)], ['10','2','12'])
        self.assertIn('10 / 1000', self.view.status.text())
        self.assertTrue(all(self.view.tree.itemWidget(row, i) is None for i in range(5)))
        self.view.tabs.setCurrentIndex(3)
        self.assertNotIn('/ 1000', self.view.status.text())

    def test_stale_backpack_and_disembark_remain_unknown(self):
        self.set_inventory(inventory(pair() + [event('Embark', 1), snapshot('ShipLocker', 2, Components=[item(count=12)])]))
        self.view.tabs.setCurrentIndex(1)
        row = self.rows('graphene')[0][1]
        self.assertEqual([row.text(i) for i in (1,2,3)], ['12','0','12'])
        self.set_inventory(inventory(pair() + [event('Disembark', 1)]))
        row = self.rows('graphene')[0][1]
        self.assertEqual([row.text(i) for i in (1,2,3)], ['?','?','?'])
        self.select_filter('empty')
        self.assertFalse(self.view.items)

    def test_commander_switch_clears_immediately(self):
        self.set_inventory(inventory(pair()))
        self.view.tabs.setCurrentIndex(1)
        self.page.search.setText('graphene')
        self.controller.loading.emit()
        self.assertEqual(self.rows('graphene')[0][1].text(3), '?')
        self.assertFalse(self.view.commander_label.text())
        other = inventory([snapshot('ShipLocker', Components=[item(count=80)]), snapshot('Backpack')], 2)
        self.set_inventory(other)
        self.assertEqual(self.rows('graphene')[0][1].text(3), '80')
        self.assertEqual(self.page.search.text(), 'graphene')
        self.assertFalse(self.view.highlight)
        self.set_inventory(inventory(pair()))
        self.assertEqual(self.rows('graphene')[0][1].text(3), '12')

    def test_live_collection_deduplicated_expires_consumption_and_transfer(self):
        self.view.tabs.setCurrentIndex(1)
        self.set_inventory(inventory(pair()))
        pickup = [event('CollectItems', 1, Name='graphene', Type='Component', Count=1, OwnerID=0),
                  event('BackpackChange', 1, Added=[item(count=1, Type='Component')])]
        result = inventory(pair() + pickup)
        self.view.highlight_timer.setInterval(30)
        self.set_inventory(result)
        self.assertEqual(self.rows('graphene')[0][1].text(3), '13')
        self.assertIn('+1', self.rows('graphene')[0][1].text(0))
        self.assertEqual(len(self.view.highlight), 1)
        QTest.qWait(60)
        self.set_inventory(result)
        self.assertFalse(self.view.highlight)
        self.set_inventory(inventory(pair()+pickup+[event('BackpackChange', 2, Removed=[item(count=1, Type='Component')])]))
        self.assertFalse(self.view.highlight)
        self.set_inventory(inventory(pair()+pickup+[event('TransferMicroResources', 3)]))
        self.assertFalse(self.view.highlight)

    def test_historical_change_not_flashed_on_first_load(self):
        self.set_inventory(OdysseyInventory(1, 'F1'))
        self.set_inventory(inventory(pair()+[event('BackpackChange', 1, Added=[item(count=1, Type='Component')])]))
        self.assertFalse(self.view.highlight)

    def test_persist_tabs_filter_widths_order_and_engineering_isolation(self):
        self.view.tabs.setCurrentIndex(2)
        self.select_filter('locker')
        header = self.view.tree.header()
        header.resizeSection(0, 421)
        header.moveSection(4,1)
        self.assertIsNone(self.state.settings.value('materials/columns'))
        self.page.tabs.setCurrentIndex(0)
        self.page.tabs.setCurrentIndex(3)
        self.assertEqual(header.sectionSize(0), 421)
        self.assertEqual(header.logicalIndex(1), 4)
        settings = QSettings(self.state.settings.fileName(), QSettings.Format.IniFormat)
        restarted = MaterialView(SimpleNamespace(settings=settings), controller=StubController(), odyssey_controller=StubController())
        self.addCleanup(restarted.close)
        self.assertEqual(restarted.tabs.currentIndex(), 3)
        self.assertEqual(restarted.odyssey.tabs.currentIndex(), 2)
        self.assertEqual(restarted.odyssey.filter.currentData(), 'locker')
        self.assertEqual(restarted.odyssey.tree.columnWidth(0), 421)
        self.assertEqual(restarted.odyssey.tree.header().logicalIndex(1), 4)
        self.assertFalse(restarted.odyssey.inventory.known)
        restarted.resize(600,500)
        self.app.processEvents()
        self.assertEqual(restarted.odyssey.tree.columnWidth(0), 421)

    def test_invalid_layout_defaults_no_hidden_columns(self):
        for bad in ({'widths':[0]*5}, {'widths':[300]*5, 'order':[0]*5}):
            saved = dict(version=1, columns=['name','locker','backpack','total','usage'], widths=[300]*5, order=list(range(5)))
            saved.update(bad)
            self.state.settings.setValue('materials/odyssey/columns', saved)
            restarted = MaterialView(self.state, controller=StubController(), odyssey_controller=StubController())
            self.addCleanup(restarted.close)
            header = restarted.odyssey.tree.header()
            self.assertEqual([header.sectionSize(i) for i in range(5)], [340,105,105,95,220])
            self.assertEqual([header.logicalIndex(i) for i in range(5)], list(range(5)))
            self.assertTrue(all(not header.isSectionHidden(i) for i in range(5)))

    def test_mouse_header_resize_and_reorder_saved(self):
        header = self.view.tree.header()
        start = QPoint(header.sectionSize(0)-1, header.height()//2)
        QTest.mousePress(header.viewport(), Qt.MouseButton.LeftButton, pos=start)
        QTest.mouseMove(header.viewport(), start+QPoint(55,0), 20)
        QTest.mouseRelease(header.viewport(), Qt.MouseButton.LeftButton, pos=start+QPoint(55,0))
        self.assertGreater(header.sectionSize(0),340)
        self.assertEqual(self.state.settings.value('materials/odyssey/columns')['widths'][0],header.sectionSize(0))
        start = QPoint(header.sectionViewportPosition(1)+20, header.height()//2)
        target = QPoint(header.sectionViewportPosition(3)+header.sectionSize(3)-15,start.y())
        QTest.mousePress(header.viewport(),Qt.MouseButton.LeftButton,pos=start)
        QTest.mouseMove(header.viewport(),start+QPoint(25,0),30)
        QTest.mouseMove(header.viewport(),target,30)
        QTest.mouseRelease(header.viewport(),Qt.MouseButton.LeftButton,pos=target)
        self.assertEqual([header.logicalIndex(i) for i in range(5)],[0,2,3,1,4])
        self.assertEqual(self.state.settings.value('materials/odyssey/columns')['order'],[0,2,3,1,4])

    def test_five_colors_selection_live_hover_dark_light(self):
        for light in (False, True):
            self.app.setStyleSheet(LIGHT_STYLESHEET if light else DARK_STYLESHEET)
            self.page.set_light_mode(light)
            self.app.processEvents()
            QApplication.sendEvent(self.view.tree.viewport(), QEvent(QEvent.Type.Leave))
            def color(row):
                option = QStyleOptionViewItem()
                option.initFrom(self.view.tree)
                if row.isSelected(): option.state |= QStyle.StateFlag.State_Selected
                self.view.row_delegate.initStyleOption(option, self.view.tree.indexFromItem(row))
                return option.backgroundBrush.color().name()
            rows = list(self.view.items.values())[:6]
            self.assertEqual([color(r) for r in rows], list(THEMES[light]['rows'])+[THEMES[light]['rows'][0]])
            r = rows[0]
            r.setData(0,COLLECTED_ROLE,True)
            self.assertEqual(color(r),THEMES[light]['live'])
            r.setSelected(True)
            self.assertEqual(color(r),THEMES[light]['selected'])
            r.setSelected(False)
            r.setData(0,COLLECTED_ROLE,False)
            QTest.mouseMove(self.view.tree.header().viewport(), QPoint(10,5))
            QTest.mouseMove(self.view.tree.viewport(), self.view.tree.visualItemRect(r).center())
            self.assertEqual(color(r),THEMES[light]['hover'])

    def test_english_fallback_and_all_ui_languages(self):
        keys = {k for k in _TRANSLATIONS['en'] if k.startswith('odyssey.')}
        self.assertEqual(len(keys), 31)
        for lang, translations in _TRANSLATIONS.items():
            self.assertTrue(all(translations.get(k) for k in keys), lang)
        set_language('fi')
        self.view.render()
        self.assertEqual(self.rows('powerinventory')[0][1].text(0), 'Inventory Record')

    def test_real_faber38_pair_and_embarked_mission_survives(self):
        records = json.loads((Path(__file__).parent/'fixtures/odyssey_faber38.json').read_text())
        for cutoff, expected in (('2026-09-08T14:58:01Z',(3131,8,3139)), ('2026-09-08T14:58:26Z',(3139,0,3139))):
            inv = inventory([e for e in records if e['timestamp'] <= cutoff])
            self.set_inventory(inv)
            observed = [r for r in self.view.rows if r.observed]
            self.assertEqual(tuple(sum(getattr(r.stock,k) for r in observed) for k in ('locker','backpack','total')), expected)
            vehicle = self.rows('vehicleschematic')[0]
            self.assertEqual(vehicle[0].mission_id,1064707191)
            self.assertEqual(vehicle[1].text(3),'1')
            self.assertIn('abgeschlossen', vehicle[1].toolTip(4))
            for cat, symbols in ((1,{'graphene':3,'microelectrode':113}), (2,{'manufacturinginstructions':68,'weapontestdata':34}), (3,{'healthpack':100,'energycell':100})):
                self.view.tabs.setCurrentIndex(cat)
                for symbol,count in symbols.items():
                    self.assertEqual(sum(int(v.text(3)) for k,v in self.rows(symbol)),count)
            self.view.tabs.setCurrentIndex(0)


class OdysseyControllerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name)
        self.db = self.path/'test.db'
        with sqlite3.connect(self.db) as con:
            con.execute('CREATE TABLE commanders(id INTEGER, fid TEXT, current_name TEXT)')
            con.execute('CREATE TABLE journal_sessions(commander_id INTEGER, fid_seen TEXT, journal_file TEXT, attribution_status TEXT)')
            for cid, amount in ((1,10),(2,80)):
                file = self.path/f'{cid}.log'
                records = [event('Commander', FID=f'F{cid}'), snapshot('ShipLocker', Components=[item(count=amount)]), snapshot('Backpack')]
                file.write_text(''.join(json.dumps(e)+'\n' for e in records))
                con.execute('INSERT INTO commanders VALUES(?,?,?)',(cid,f'F{cid}',f'Commander {cid}'))
                con.execute('INSERT INTO journal_sessions VALUES(?,?,?,?)',(cid,f'F{cid}',str(file),'identified'))
        self.state = State()
        self.state.commander_id = self.state.viewed_commander_id = 1
        self.state.commander_fid = 'F1'
        self.state.database = SimpleNamespace(path=self.db)
        self.state.settings = QSettings(str(self.path/'ui.ini'), QSettings.Format.IniFormat)
        self.controller = OdysseyController(self.state)
        self.page = MaterialView(self.state, controller=StubController(), odyssey_controller=self.controller)
        self.page.tabs.setCurrentIndex(3)
        self.view = self.page.odyssey
        self.view.tabs.setCurrentIndex(1)
        self.addCleanup(self.cleanup_worker)

    def cleanup_worker(self):
        self.controller.timer.stop()
        self.controller.pool.waitForDone(10000)
        self.app.processEvents()
        self.controller.timer.stop()
        self.page.close()
        self.controller.deleteLater()
        self.app.processEvents()

    def wait_until(self, predicate):
        deadline = time.monotonic()+8
        while not predicate() and time.monotonic()<deadline:
            QTest.qWait(15)
        self.assertTrue(predicate())

    def test_two_commanders_and_live_delta_reader_reuse(self):
        self.wait_until(lambda: self.view.inventory.known)
        reader = self.controller.reader
        self.assertEqual(self.view.inventory.total_count,10)
        with (self.path/'1.log').open('a') as f:
            for e in [event('CollectItems',1,Name='graphene',Type='Component',Count=1,OwnerID=0),
                      event('BackpackChange',1,Added=[item(count=1,Type='Component')])]:
                f.write(json.dumps(e)+'\n')
        self.state.changed.emit()
        self.wait_until(lambda: self.view.inventory.total_count==11)
        self.assertEqual(sum(self.view.highlight.values()),1)
        self.state.viewed_commander_id=2
        self.state.viewedCommanderChanged.emit(2)
        self.assertFalse(self.view.inventory.known)
        self.wait_until(lambda: self.view.inventory.total_count==80)
        self.assertFalse(self.view.highlight)
        self.state.viewed_commander_id=1
        self.state.viewedCommanderChanged.emit(1)
        self.wait_until(lambda: self.view.inventory.total_count==11)
        self.assertFalse(self.view.highlight)
        self.assertIs(self.controller.reader,reader)

    def test_late_result_rejected_gui_responsive(self):
        entered, release = threading.Event(), threading.Event()
        self.addCleanup(release.set)
        original=self.controller.reader.reconstruct
        def slow(*args):
            entered.set()
            release.wait(4)
            return original(*args)
        with patch.object(self.controller.reader,'reconstruct',side_effect=slow):
            self.wait_until(entered.is_set)
            self.state.viewed_commander_id=2
            self.state.viewedCommanderChanged.emit(2)
            seen=[]
            self.controller.ready.connect(lambda inv,_:seen.append(inv.commander_id))
            tick=[]
            QTimer.singleShot(10,lambda:tick.append(True))
            self.wait_until(lambda:bool(tick))
            self.assertFalse(self.view.inventory.known)
            release.set()
            self.wait_until(lambda:self.view.inventory.known)
            self.assertEqual(seen,[2])
            self.assertEqual(self.view.inventory.total_count,80)
