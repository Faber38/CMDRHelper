import copy
import subprocess
import sys
import unittest
from collections import Counter
from dataclasses import replace
from unittest.mock import patch

from PySide6.QtCore import QCollator, QLocale
from PySide6.QtGui import QPalette
from PySide6.QtWidgets import QLineEdit, QStyleOptionViewItem

from cmdrhelper.i18n import _TRANSLATIONS, get_language, set_language, tr
from cmdrhelper.odyssey_catalog import all_materials, localized_name
from cmdrhelper.odyssey_ranks import RANKS, rating, sort_priority
from cmdrhelper.ui.odyssey_cleanup import DEFAULT_SYMBOLS, save_selection
from cmdrhelper.ui.odyssey_view import OdysseyView, RANK_COLUMN, RANK_COLORS, CLEANUP_COLORS
from test_material_view import StubController
import test_odyssey_view as views


class RankCatalogTests(unittest.TestCase):
    def test_complete_unique_catalog_and_recipe_evidence(self):
        materials = all_materials()
        self.assertEqual(len(RANKS), 223)
        self.assertEqual(set(RANKS), {m.symbol for m in materials})
        self.assertEqual(Counter(m.category for m in materials),
                         dict(Items=61, Components=33, Data=123, Consumables=6))
        self.assertEqual(Counter(r.rank for r in RANKS.values()), dict(A=16, B=54, C=28, D=94, **{'?':31}))
        for m in materials:
            r = rating(m.symbol)
            self.assertEqual({f for f, recipe in r.recipes}, m.engineering_flags)
            self.assertEqual(len(r.recipes), len(set(r.recipes)))
            if 'engineer_unlock' in m.engineering_flags:
                self.assertIn(r.rank, 'AB')
            if m.engineering_flags & {'suit_upgrade', 'weapon_upgrade'}:
                self.assertEqual(r.rank, 'A')
            if r.rank == 'D':
                self.assertFalse(r.recipes)
        self.assertEqual(len(DEFAULT_SYMBOLS),81)
        self.assertTrue(all(rating(s).rank == 'D' for s in DEFAULT_SYMBOLS))

    def test_known_examples_unknown_and_category_conflict(self):
        for symbol, rank in [('suitschematic','A'),('opinionpolls','B'),('airqualityreports','C'),
                             ('accidentlogs','D'),('powerinventory','?'),('future_item','?')]:
            self.assertEqual(rating(symbol).rank,rank)
        self.assertEqual(rating('suitschematic', 'Data').rank,'?')
        for descending in (False,True):
            self.assertEqual(sorted('ABCD?',key=lambda r:sort_priority(r,descending)), list('DCBA?' if descending else 'ABCD?'))


class RankViewTests(unittest.TestCase):
    setUpClass = classmethod(views.OdysseyViewTests.setUpClass.__func__)
    setUp = views.OdysseyViewTests.setUp
    set_inventory = views.OdysseyViewTests.set_inventory
    rows = views.OdysseyViewTests.rows

    def test_rank_sorts_all_categories_ties_and_no_reconstruction(self):
        original=copy.deepcopy(self.view.inventory)
        for category in range(4):
            self.view.tabs.setCurrentIndex(category)
            existing=dict(self.view.items)
            for mode in ('rank_asc','rank_desc'):
                with patch.object(self.view,'begin_loading',side_effect=AssertionError('inventory reload')):
                    self.view.sort_order.setCurrentIndex(self.view.sort_order.findData(mode))
                collator=QCollator(QLocale(get_language()))
                actual=[k for k,v in sorted(self.view.items.items(),key=lambda p:self.view.tree.indexOfTopLevelItem(p[1]))]
                expected=sorted(actual,key=lambda k:(sort_priority(rating(k.name,k.category).rank,mode=='rank_desc'),
                                                     collator.sortKey(localized_name(k.name)),k.name,repr(k)))
                self.assertEqual(actual,expected)
                self.assertTrue(all(self.view.items[k] is v for k,v in existing.items()))
                self.assertEqual(self.view.inventory,original)
                self.assertFalse(self.view.loading_state.pending)
        # Two unknown Powerplay goods have identical localized names: stable ID tie.
        self.view.tabs.setCurrentIndex(0)
        with patch('cmdrhelper.ui.odyssey_view.merge_inventory',return_value=tuple(
                replace(r,name='Gleich') for r in self.view.rows)):
            self.view.render()
        order=[k.name for k,v in sorted(self.view.items.items(),key=lambda p:self.view.tree.indexOfTopLevelItem(p[1]))]
        unknown=[s for s in order if rating(s).rank=='?']
        self.assertEqual(unknown,sorted(unknown))

    def test_colors_tooltips_cleanup_independence_and_languages(self):
        save_selection(self.state.settings,self.view._cleanup_key,{'suitschematic'})
        self.set_inventory(self.view.inventory)
        for light in (False,True):
            self.view.set_light_mode(light)
            for category in range(4):
                self.view.tabs.setCurrentIndex(category)
                for key,item in self.view.items.items():
                    rank=rating(key.name).rank
                    self.assertEqual(item.text(RANK_COLUMN),rank)
                    self.assertIn(tr('odyssey.rank.'+rank),item.toolTip(RANK_COLUMN))
                    option=QStyleOptionViewItem()
                    self.view.row_delegate.initStyleOption(option,self.view.tree.indexFromItem(item,RANK_COLUMN))
                    self.assertEqual(option.palette.color(QPalette.ColorRole.Text).name(),RANK_COLORS[light][rank])
                    if key.name=='suitschematic':
                        self.assertEqual(option.backgroundBrush.color().name(),CLEANUP_COLORS[light][0])
        for language,translations in _TRANSLATIONS.items():
            set_language(language)
            self.view.render()
            self.assertEqual(self.view.tree.headerItem().text(RANK_COLUMN),translations['odyssey.rank'])
            for suffix in ('A','B','C','D','?','own','keep','reduce','sell'):
                self.assertTrue(translations['odyssey.rank.'+suffix])
            for mode in ('rank_asc','rank_desc'):
                self.assertEqual(self.view.sort_order.itemText(self.view.sort_order.findData(mode)),translations['odyssey.sort.'+mode])
        self.assertEqual(self.view._cleanup_symbols,{'suitschematic'})

    def test_rank_persists_commander_navigation_and_process(self):
        for mode in ('rank_asc','rank_desc'):
            self.view.sort_order.setCurrentIndex(self.view.sort_order.findData(mode))
            self.set_inventory(views.inventory([],cid=2))
            self.page.tabs.setCurrentIndex(0)
            self.page.tabs.setCurrentIndex(3)
            self.assertEqual(self.view.sort_order.currentData(),mode)
            reopened=OdysseyView(self.state,QLineEdit(),controller=StubController())
            self.addCleanup(reopened.close)
            self.assertEqual(reopened.sort_order.currentData(),mode)
            self.assertEqual(reopened.tree.header().visualIndex(RANK_COLUMN)+1,reopened.tree.header().visualIndex(0))
            result=subprocess.run([sys.executable,'-B','-c',
                'import sys; from PySide6.QtCore import QSettings; print(QSettings(sys.argv[1],QSettings.IniFormat).value("materials/odyssey/sort"))',
                self.state.settings.fileName()],capture_output=True,text=True,check=True,timeout=20)
            self.assertEqual(result.stdout.strip(),mode)

    def test_summaries_updates_and_unknown_observed_rows(self):
        self.set_inventory(views.inventory(views.pair()))
        summary=self.view.summaries[('Items','vehicleschematic')]
        self.assertEqual(summary.text(RANK_COLUMN),'D')
        self.assertTrue(all(i.text(RANK_COLUMN)=='D' for k,i in self.rows('vehicleschematic')))
        self.view.sort_order.setCurrentIndex(2)
        self.assertIs(self.view.summaries[('Items','vehicleschematic')],summary)
        self.set_inventory(views.inventory([views.snapshot('ShipLocker',Items=[views.item('future_item',7)]),views.snapshot('Backpack')]))
        item=self.rows('future_item')[0][1]
        self.assertEqual(item.text(RANK_COLUMN),'?')
        self.assertEqual(item.text(1),'7')


if __name__=='__main__':
    unittest.main()
