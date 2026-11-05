"""Possible cargo uses shared stock, with no allocations or live-data writes."""
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from copy import deepcopy
from dataclasses import replace
from string import Formatter
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QStyleOptionViewItem
from cmdrhelper.cargo import normalize_inventory
from cmdrhelper.i18n import _TRANSLATIONS, get_language, set_language, tr
from cmdrhelper.models import Mission
from cmdrhelper.ui.mission_cargo import (
    MISSION_CARGO_ROLE, POSSIBLE_MISSION_CARGO_ROLE, PossibleMissionCargo,
    current_possible_mission_cargo, possible_mission_cargo_tooltip,
)
from cmdrhelper.ui.styles import DARK_STYLESHEET, LIGHT_STYLESHEET
from tests import test_mission_cargo as existing


def mission(mid=1, total=372, delivered=0, symbol='$Silver_Name;', **kwargs):
    return Mission(mission_id=mid, internal_name='Mission_Mining',
                   commodity_symbol=symbol, required_count=total,
                   delivered_count=delivered, **kwargs)


def cargo(count, mid=None):
    return dict(Name='silver', Count=count, **({'MissionID': mid} if mid else {}))


class PossibleCargoQuantityTests(unittest.TestCase):
    def calculate(self, rows, missions):
        state = SimpleNamespace(commander_id=1, viewed_commander_id=1, missions=missions)
        snapshot = dict(inventory=normalize_inventory(rows))
        before = deepcopy((snapshot, missions))
        with patch('cmdrhelper.ui.mission_cargo.current_ship_inventory', return_value=snapshot):
            result = list(current_possible_mission_cargo(state).values())
        self.assertEqual((snapshot, missions), before)
        return result

    def test_mission_gate_skips_all_additional_cargo_validation(self):
        state=SimpleNamespace(commander_id=1,viewed_commander_id=1,missions=[])
        cases=([], [replace(mission(),internal_name='Mission_Assassinate')],
               [mission(extra={'pending_offer':True})], [mission(symbol='unknown_symbol')],
               [mission(delivered=372)], [mission(total=None)])
        with patch('cmdrhelper.ui.mission_cargo.current_ship_inventory',
                   side_effect=AssertionError('No extra cargo validation without eligible missions')) as read:
            for missions in cases:
                with self.subTest(missions=missions):
                    state.missions=missions
                    self.assertEqual(current_possible_mission_cargo(state),{})
            read.assert_not_called()

    def test_first_goods_mission_reads_once_last_completion_or_abandonment_stops(self):
        state=SimpleNamespace(commander_id=1,viewed_commander_id=1,missions=[])
        snapshot=dict(inventory=normalize_inventory([cargo(372)]))
        with patch('cmdrhelper.ui.mission_cargo.current_ship_inventory',return_value=snapshot) as read:
            self.assertEqual(current_possible_mission_cargo(state),{})
            read.assert_not_called()
            state.missions=[mission(delivered=None)]
            self.assertTrue(current_possible_mission_cargo(state))
            read.assert_called_once_with(state)
            read.reset_mock()
            state.missions=[]  # Terminal event removes the last mission.
            for _ in range(3):
                self.assertEqual(current_possible_mission_cargo(state),{})
            read.assert_not_called()
            state.missions=[mission(delivered=372)]  # Delivery done, reward still open.
            self.assertEqual(current_possible_mission_cargo(state),{})
            read.assert_not_called()

    def test_eleven_quantity_cases(self):
        cases = [
            ('purchased unknown', [cargo(372)], [mission(delivered=None)],
             [PossibleMissionCargo(372,372,0,0,0,372,1)]),
            ('shared stock', [cargo(372)], [mission(1,300), mission(2,300)],
             [PossibleMissionCargo(372,372,600,372,2,0,0)]),
            ('partial delivery', [cargo(200)], [mission(delivered=172)],
             [PossibleMissionCargo(200,200,200,200,1,0,0)]),
            ('fully delivered', [cargo(200)], [mission(delivered=372)], []),
            ('removed', [cargo(372)], [], []),
            ('mixed stock', [cargo(100,1),cargo(50)], [mission(1,100),mission(2,100)],
             [PossibleMissionCargo(150,50,200,50,2,0,0)]),
            ('other explicit mission', [cargo(100,9),cargo(50)], [mission(1,100)],
             [PossibleMissionCargo(150,50,100,50,1,0,0)]),
            ('duplicate mission', [cargo(50)], [mission(1,100),mission(1,100)],
             [PossibleMissionCargo(50,50,100,50,1,0,0)]),
            ('offer', [cargo(50)], [mission(1,100,extra={'pending_offer':True})], []),
            ('known and unknown', [cargo(50)], [mission(1,100,20),mission(2,100,None)],
             [PossibleMissionCargo(50,50,80,50,1,100,1)]),
            ('explicit stock only', [cargo(100,1)], [mission(2,100)], []),
        ]
        for name, rows, missions, expected in cases:
            with self.subTest(name=name):
                self.assertEqual(self.calculate(rows, missions), expected)

    def test_explicit_freight_covers_its_own_need_and_never_another(self):
        self.assertEqual(self.calculate([cargo(100,1),cargo(50)], [mission(1,100)]), [])
        details = self.calculate([cargo(100,1),cargo(50)], [mission(1,120),mission(2,10)])[0]
        self.assertEqual((details.remaining, details.coverable), (130,30))

    def test_invalid_unknown_and_non_goods_requirements(self):
        for m in [mission(total=None),mission(total=0),mission(total=True),
                  mission(delivered=-1),mission(delivered=373),mission(delivered=True),
                  mission(symbol='unknown_symbol'),replace(mission(),internal_name='Mission_Salvage')]:
            with self.subTest(m=m):
                self.assertEqual(self.calculate([cargo(372)], [m]), [])
        for family in ('Mission_Mining','Mission_Delivery','Mission_Collect_Industrial'):
            self.assertTrue(self.calculate([cargo(372)], [replace(mission(),internal_name=family)]))

    def test_all_twelve_translations_and_unknown_is_not_zero(self):
        self.addCleanup(set_language, get_language())
        keys = [k for k in _TRANSLATIONS['de'] if k.startswith(('trade.possible_cargo_', 'trade.cargo_legend_'))]
        self.assertEqual(len(keys), 7)
        self.assertEqual(len(_TRANSLATIONS), 12)
        for language, table in _TRANSLATIONS.items():
            set_language(language)
            for key in keys:
                self.assertIn(key, table)
                fields=lambda text:{f for _,f,_,_ in Formatter().parse(text) if f}
                self.assertEqual(fields(table[key]),fields(_TRANSLATIONS['de'][key]))
            text=possible_mission_cargo_tooltip(PossibleMissionCargo(372,372,0,0,0,372,1))
            self.assertIn(tr('trade.possible_cargo_warning'), text)
            self.assertNotIn('{', text)
            self.assertNotIn('0 t', text)


class PossibleCargoViewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        existing.MissionCargoViewTests.setUpClass()

    def setUp(self):
        self.fixture=existing.MissionCargoViewTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.state=self.fixture.state
        self.trade=self.fixture.trade
        self.market=self.fixture.market
        self.state.missions=[mission(total=100, symbol=existing.NAME)]

    def candidates(self):
        return [index.data(POSSIBLE_MISSION_CARGO_ROLE) for index in self.fixture.indices()]

    def test_mission_only_changes_keep_items_selection_results_and_running_search(self):
        self.state.missions=[]
        self.fixture.cargo([existing.item(100)])
        item=self.trade.cargo_list.item(0)
        item.setCheckState(Qt.Checked)
        results=[('sentinel', 'results')]
        self.trade._cargo_results=results
        worker=Mock()
        self.trade.worker=worker
        self.addCleanup(setattr,self.trade,'worker',None)
        generation=self.trade._generation
        with patch.object(self.trade,'cancel_search') as cancel:
            for missions, expected in (([mission(total=100,symbol=existing.NAME)],True),
                                       ([mission(total=100,delivered=50,symbol=existing.NAME)],True),
                                       ([mission(total=100,delivered=100,symbol=existing.NAME)],False),
                                       ([],False)):
                self.state.missions=missions
                self.state.changed.emit()
                self.assertEqual([bool(x) for x in self.candidates()],[expected,expected])
                self.assertIs(self.trade.cargo_list.item(0),item)
                self.assertEqual(item.checkState(),Qt.Checked)
                self.assertIs(self.trade.worker,worker)
                self.assertIs(self.trade._cargo_results,results)
                self.assertEqual(self.trade._generation,generation)
            cancel.assert_not_called()

    def test_same_quantity_new_mission_ids_do_not_rebuild_or_cancel(self):
        self.fixture.cargo([existing.item(100)])
        item=self.trade.cargo_list.item(0)
        item.setCheckState(Qt.Checked)
        generation=self.trade._generation
        with patch.object(self.trade,'cancel_search') as cancel:
            self.fixture.cargo([existing.item(30,1),existing.item(70)])
            self.assertIs(self.trade.cargo_list.item(0),item)
            self.assertEqual(item.checkState(),Qt.Checked)
            self.assertEqual(self.trade._generation,generation)
            self.assertEqual(tuple(item.data(MISSION_CARGO_ROLE)),(30,100,1))
            self.assertEqual(item.data(POSSIBLE_MISSION_CARGO_ROLE).available,70)
            cancel.assert_not_called()
        with patch.object(self.trade,'cancel_search') as cancel:
            self.fixture.cargo([existing.item(40)])
            cancel.assert_called_once()
            self.assertGreater(self.trade._generation,generation)

    def test_pink_only_render_and_market_filter_do_not_change(self):
        self.fixture.cargo([existing.item(100)])
        before=[{k:v for k,v in row.items() if k not in ('mission_cargo','possible_mission_cargo')}
                for row in self.market.goods_model.rows]
        with patch.object(self.market.goods_proxy,'invalidateFilter') as invalidate:
            self.state.missions=[]
            self.state.changed.emit()
            self.state.missions=[mission(total=100,symbol=existing.NAME)]
            self.state.changed.emit()
            invalidate.assert_not_called()
        after=[{k:v for k,v in row.items() if k not in ('mission_cargo','possible_mission_cargo')}
               for row in self.market.goods_model.rows]
        self.assertEqual(before,after)
        self.assertEqual(self.market.goods_proxy.rowCount(),1)
        for view,index in ((self.trade.cargo_list,self.fixture.indices()[0]),
                           (self.market.goods_table,self.fixture.indices()[1])):
            self.assertIsNone(index.data(MISSION_CARGO_ROLE))
            for style in (DARK_STYLESHEET,LIGHT_STYLESHEET):
                view.setStyleSheet(style)
                option=QStyleOptionViewItem();option.initFrom(view)
                delegate=view.itemDelegateForColumn(0) or view.itemDelegate()
                delegate.initStyleOption(option,index)
                self.assertEqual(option.decorationSize.width(),16)
                image=option.icon.pixmap(16,14).toImage()
                # Both globe and exclamation have visible pink pixels.
                for xs in (range(0,12),range(12,16)):
                    self.assertTrue(any(image.pixelColor(x,y).red()>image.pixelColor(x,y).green()+30
                                        for x in xs for y in range(14)))

    def test_cargo_events_wait_for_valid_snapshot_and_partial_delivery(self):
        self.fixture.cargo([existing.item(100)])
        for kind in ('MissionAccepted','CargoDepot','MissionCompleted','MissionAbandoned','MissionFailed'):
            self.fixture.fixture.feed(kind,MissionID=1)
            self.state.changed.emit()
            self.assertEqual(self.candidates(),[None,None])
            self.fixture.cargo([existing.item(100)])
            self.assertTrue(all(self.candidates()))
        self.state.missions[0].delivered_count=60
        self.fixture.cargo([existing.item(40)])
        self.assertEqual([d.coverable for d in self.candidates()],[40,40])
        self.state.missions=[]
        self.state.changed.emit()
        self.assertEqual(self.candidates(),[None,None])

    def test_commander_ship_stale_and_source_guards(self):
        self.fixture.cargo([existing.item(100)])
        for obj,field,value,signal in (
            (self.state,'commander_fid','OTHER',self.state.changed),
            (self.state,'viewed_commander_id',2,self.state.viewedCommanderChanged),
            (self.state.ship_loadout,'ship_id',8,self.state.shipLoadoutChanged),
            (self.state.ship_loadout,'loadout_stale',True,self.state.shipLoadoutChanged),
            (self.state,'_cargo_blocked',True,self.state.changed),
            (self.state,'cargo_snapshot',None,self.state.cargoSnapshotChanged),
            (self.state,'sources',object(),self.state.changed),
        ):
            with self.subTest(field=field):
                old=getattr(obj,field,None)
                setattr(obj,field,value)
                signal.emit() if signal is self.state.changed else signal.emit(None)
                self.assertEqual(self.candidates(),[None,None])
                setattr(obj,field,old)
                self.state.changed.emit()
                self.assertTrue(all(self.candidates()))

    def test_early_snapshot_does_not_attach_new_amounts_to_old_rows(self):
        self.fixture.cargo([existing.item(100)])
        old=self.state.ship_inventory
        self.fixture.cargo([existing.item(40)])
        new=self.state.ship_inventory
        self.state.ship_inventory=old
        self.state.cargoSnapshotChanged.emit(self.state.cargo_snapshot)
        self.assertIsNone(self.candidates()[0])
        self.assertEqual(self.candidates()[1].available,40)
        self.state.ship_inventory=new
        self.state.cargoSnapshotChanged.emit(new)
        self.assertEqual([d.available for d in self.candidates()],[40,40])

    def test_mixed_symbols_render_in_both_themes_and_all_languages(self):
        self.fixture.cargo([existing.item(30,1),existing.item(70)])
        self.assertEqual([d.available for d in self.candidates()],[70,70])
        for language in _TRANSLATIONS:
            set_language(language)
            self.state.changed.emit()
            for index in self.fixture.indices():
                self.assertEqual(tuple(index.data(MISSION_CARGO_ROLE)),(30,100,1))
                self.assertIn(tr('trade.possible_cargo_warning'),index.data(Qt.ToolTipRole))
            for style in (DARK_STYLESHEET,LIGHT_STYLESHEET):
                for view,index,legend in ((self.trade.cargo_list,self.fixture.indices()[0],self.trade.cargo_mission_legend),
                                          (self.market.goods_table,self.fixture.indices()[1],self.market.cargo_mission_legend)):
                    view.setStyleSheet(style)
                    legend.setStyleSheet(style)
                    legend.refresh()
                    legend.resize(300,100)
                    legend.grab()
                    self.assertIn(tr('trade.cargo_legend_pink'),legend.accessibleName())
                    option=QStyleOptionViewItem();option.initFrom(view)
                    delegate=view.itemDelegateForColumn(0) or view.itemDelegate()
                    delegate.initStyleOption(option,index)
                    self.assertEqual(option.decorationSize.width(),32)
                    image=option.icon.pixmap(32,14).toImage()
                    self.assertTrue(any(image.pixelColor(x,y).blue()>image.pixelColor(x,y).red()+30
                                        for x in range(14) for y in range(14)))
                    self.assertTrue(any(image.pixelColor(x,y).red()>image.pixelColor(x,y).green()+30
                                        for x in range(16,32) for y in range(14)))
