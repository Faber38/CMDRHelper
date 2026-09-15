"""Manual baselines, projected quantities, identity isolation and safe totals."""
from copy import deepcopy
from pathlib import Path
import sqlite3
from string import Formatter
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication, QLineEdit, QDialog

from cmdrhelper.i18n import _TRANSLATIONS, get_language, set_language
from cmdrhelper.odyssey_carrier import OdysseyCarrierStore, material_amounts, owned_carrier, carrier_capacity
from cmdrhelper.odyssey_catalog import all_materials
from cmdrhelper.odyssey_controller import OdysseyController
from cmdrhelper.ui.odyssey_view import OdysseyView, COLUMNS
from cmdrhelper.ui.odyssey_carrier_dialog import OdysseyCarrierDialog, carrier_tooltip
from test_material_view import State
from test_odyssey_view import inventory
from test_odyssey_inventory import event, item, snapshot


class OdysseyCarrierTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.settings = QSettings(str(self.root/'settings.ini'), QSettings.IniFormat)
        self.store = OdysseyCarrierStore(self.settings)
        self.db = self.root/'test.db'
        with sqlite3.connect(self.db) as con:
            con.execute('CREATE TABLE commanders(id INTEGER, fid TEXT)')
            con.execute('CREATE TABLE commander_carriers(commander_id INTEGER, carrier_id INTEGER)')
            con.executemany('INSERT INTO commanders VALUES (?,?)', [(1,'F1'),(2,'F2')])
            con.executemany('INSERT INTO commander_carriers VALUES (?,?)', [(1,123),(2,456)])
        self.state = State()
        self.state.settings = self.settings
        self.state.database = SimpleNamespace(path=self.db)
        self.state.commander_id = self.state.viewed_commander_id = 1
        self.state.commander_fid = 'F1'
        self.state.refresh = Mock(side_effect=AssertionError('global refresh is forbidden'))
        self.controller = OdysseyController(self.state)
        self.search = QLineEdit()
        self.view = OdysseyView(self.state, self.search, controller=self.controller)
        # These unit tests deliver worker results directly; no background I/O.
        self.controller._start = Mock()
        self.addCleanup(self.cleanup)
        self.deliver()
        self.view.tabs.setCurrentIndex(1)
        self.addCleanup(set_language, get_language())
        set_language('de')

    def cleanup(self):
        self.controller.timer.stop()
        self.controller.pool.waitForDone()
        self.view.close()
        self.view.deleteLater()
        self.controller.deleteLater()
        self.app.processEvents()

    def deliver(self, inv=None, carrier_id=123):
        inv = inv or inventory([snapshot('ShipLocker', Components=[item('chemicalcatalyst',3)]), snapshot('Backpack')])
        inv.carrier_id = carrier_id
        self.controller._finished(self.controller._generation, inv, 'Commander')
        return inv

    def confirm(self, amount, cat='Components', name='chemicalcatalyst'):
        self.controller.confirm_carrier(cat, name, amount, (1,'F1',123))

    def row(self, name='chemicalcatalyst'):
        return next(v for k,v in self.view.items.items() if k.name == name)

    def test_unknown_zero_positive_total_correction_and_reset(self):
        self.assertEqual([self.row().text(i) for i in (1,2,3,4)], ['3','0','—','—'])
        for amount, total in [(0,'3'), (4,'7'), (9,'12')]:
            self.confirm(amount)
            self.assertEqual(self.row().text(3), str(amount))
            self.assertEqual(self.row().text(4), total)
        timestamp = self.view.inventory.carrier_records['Components/chemicalcatalyst']['confirmed_at']
        self.confirm(None)
        record = self.store.load('F1',123)['records']['Components/chemicalcatalyst']
        self.assertEqual((record['current_amount'],record['last_confirmed_amount'],record['status']), (None,9,'unknown'))
        self.assertEqual(record['confirmed_at'],timestamp)
        self.assertEqual(self.row().text(4),'—')
        self.assertIn('9',self.row().toolTip(3))
        self.assertIn('nicht in Gesamt',self.row().toolTip(3))
        self.state.refresh.assert_not_called()

    def test_restart_settings_and_view(self):
        self.confirm(4)
        other = OdysseyCarrierStore(QSettings(self.settings.fileName(), QSettings.IniFormat))
        self.assertEqual(other.load('F1',123)['records']['Components/chemicalcatalyst']['current_amount'],4)
        controller = OdysseyController(self.state)
        controller._start = Mock()
        self.addCleanup(controller.deleteLater)
        self.addCleanup(controller.timer.stop)
        view = OdysseyView(self.state,QLineEdit(),controller=controller)
        self.addCleanup(view.close)
        inv = inventory([snapshot('ShipLocker', Components=[item('chemicalcatalyst',3)]), snapshot('Backpack')])
        inv.carrier_id = 123
        controller._finished(controller._generation, inv, 'Commander')
        view.tabs.setCurrentIndex(1)
        self.assertEqual(next(v for k,v in view.items.items() if k.name=='chemicalcatalyst').text(3),'4')

    def test_tracked_tooltip_and_old_worker_cannot_overwrite_manual_confirmation(self):
        self.confirm(4)
        ledger=self.store.load('F1',123)
        ledger['records']['Components/chemicalcatalyst'].update(status='tracked',current_amount=8)
        self.store.save('F1',123,ledger)
        self.deliver()
        self.assertEqual(self.row().text(3),'8')
        self.assertIn('Automatisch fortgeschrieben',self.row().toolTip(3))
        stale=deepcopy(self.controller._last_inventory)
        self.confirm(9)
        self.controller._finished(self.controller._generation,stale,'Commander')
        self.assertEqual(self.row().text(3),'9')
        self.assertEqual(self.store.load('F1',123)['records']['Components/chemicalcatalyst']['status'],'manual')

    def test_phase_one_ledger_loads_without_losing_confirmation(self):
        self.confirm(4)
        ledger=self.store.load('F1',123)
        ledger['version']=1
        self.settings.setValue(self.store.key('F1',123),ledger)
        self.assertEqual(self.store.load('F1',123)['records']['Components/chemicalcatalyst']['current_amount'],4)
        self.confirm(9)
        self.assertEqual(self.settings.value(self.store.key('F1',123))['version'],2)

    def test_identity_and_category_isolation(self):
        for fid,cid,cat,amount in [('F1',123,'Items',1),('F1',123,'Components',4),
                ('F1',123,'Data',8),('F2',123,'Components',12),('F1',456,'Components',16)]:
            self.store.confirm(fid,cid,cat,'same_symbol',amount)
        for fid,cid,cat,amount in [('F1',123,'Items',1),('F1',123,'Components',4),
                ('F1',123,'Data',8),('F2',123,'Components',12),('F1',456,'Components',16)]:
            self.assertEqual(self.store.load(fid,cid)['records'][f'{cat}/same_symbol']['current_amount'],amount)
        self.assertEqual(self.store.load('F2',456)['records'],{})
        self.assertNotEqual(self.store.key('A/B',123),self.store.key('A%2FB',123))

    def test_canonical_symbol_and_invalid_input(self):
        self.store.confirm('F1',123,'Components','$ChemicalCatalyst_name;',4)
        self.assertIn('Components/chemicalcatalyst',self.store.load('F1',123)['records'])
        for amount in [-1,True,1.2,'4',2_147_483_648]:
            with self.assertRaises(ValueError): self.confirm(amount)
        with self.assertRaises(ValueError): self.confirm(4,'Consumables')
        for cid in [None,True,0,-1,'123']:
            with self.assertRaises(ValueError): self.store.load('F1',cid)

    def test_missing_owner_and_stale_dialog_identity(self):
        self.confirm(4)
        with sqlite3.connect(self.db) as con: con.execute('DELETE FROM commander_carriers WHERE commander_id=1')
        with self.assertRaises(ValueError): self.confirm(9)
        self.deliver()
        self.assertIsNone(self.view.inventory.carrier_id)
        self.assertEqual(self.row().text(3),'—')
        self.assertEqual(owned_carrier(self.db,1,'F2'),None)
        self.assertEqual(self.store.load('F1',123)['records']['Components/chemicalcatalyst']['current_amount'],4)

    def test_commander_and_carrier_changes_do_not_expose_other_confirmation(self):
        self.confirm(4)
        self.state.commander_id = self.state.viewed_commander_id = 2
        self.state.commander_fid = 'F2'
        with self.assertRaises(ValueError): self.confirm(9)
        self.deliver(inventory([snapshot('ShipLocker'), snapshot('Backpack')],cid=2),456)
        self.assertEqual(self.row().text(3),'—')
        self.state.commander_id = self.state.viewed_commander_id = 1
        self.state.commander_fid = 'F1'
        with sqlite3.connect(self.db) as con: con.execute('UPDATE commander_carriers SET carrier_id=789 WHERE commander_id=1')
        self.deliver(carrier_id=789)
        self.assertEqual(self.row().text(3),'—')

    def test_multiple_stacks_carrier_once_and_filter_does_not_change_summary(self):
        inv=inventory([snapshot('ShipLocker',Components=[item('chemicalcatalyst',3),
            item('chemicalcatalyst',2,MissionID=7),dict(item('chemicalcatalyst',1),OwnerID=8,Stolen=True)]),snapshot('Backpack')])
        self.deliver(inv)
        self.confirm(4)
        summary=self.view.summaries[('Components','chemicalcatalyst')]
        self.assertEqual([summary.text(i) for i in (1,2,3,4)],['6','0','4','10'])
        self.assertEqual(summary.childCount(),3)
        self.assertTrue(all(summary.child(i).text(3)=='—' and summary.child(i).text(4)=='—' for i in range(3)))
        self.assertEqual(len([k for k in self.view.items if k.name=='chemicalcatalyst']),3)
        self.view.filter.setCurrentIndex(self.view.filter.findData('mission'))
        self.assertEqual(self.view.summaries[('Components','chemicalcatalyst')].text(4),'10')

    def test_personal_unknown_and_incoherence_block_total_not_manual_stock(self):
        self.confirm(4)
        inv=inventory([snapshot('ShipLocker',Components=[item('chemicalcatalyst',3)]),
                       snapshot('Backpack',1)])
        self.assertFalse(inv.known)
        self.deliver(inv)
        self.assertEqual([self.row().text(i) for i in (3,4)],['4','—'])

    def test_inventory_reader_does_not_double_book_carrier_or_use_market_stock(self):
        self.confirm(4)
        policy = self.settings.value(self.store.key('F1',123))['tracking_policy']
        self.assertEqual(policy['mode'],'own_carrier_locker_projection')
        self.assertTrue(policy['requires_verified_own_carrier_stay'])
        self.assertFalse(policy['standalone_shiplocker_delta_is_transfer_evidence'])
        self.assertFalse(policy['standalone_backpack_change_is_transfer_evidence'])
        for e in [event('ShipLocker'),event('FCMaterials',Stock=99,Demand=88,Price=1),
                event('BuyMicroResources',Name='chemicalcatalyst',Category='Component',Count=4),
                event('SellMicroResources',Name='chemicalcatalyst',Category='Component',Count=2),
                event('TransferMicroResources'),event('BackpackChange',Added=[item('chemicalcatalyst',4,Type='Component')])]:
            before=deepcopy(self.settings.value(self.store.key('F1',123)))
            self.deliver(inventory([snapshot('ShipLocker',Components=[item('chemicalcatalyst',7)]),snapshot('Backpack'),e]))
            self.assertEqual(self.row().text(3),'4')
            self.assertEqual(self.settings.value(self.store.key('F1',123)),before)

    def test_dialog_validation_unknown_zero_cancel_and_accept(self):
        dialog=OdysseyCarrierDialog('Material',{},True)
        self.addCleanup(dialog.close)
        for value in ['','-1','1.5','abc','+4','2147483648','²']:
            dialog.input.setText(value); dialog._apply()
            self.assertNotEqual(dialog.result(),QDialog.Accepted)
        dialog.input.setText('0'); dialog._apply()
        self.assertEqual(dialog.amount,0)
        dialog._reset(); self.assertIsNone(dialog.amount)
        with patch('cmdrhelper.ui.odyssey_view.OdysseyCarrierDialog') as factory:
            factory.return_value.exec.return_value=QDialog.Rejected
            self.view._edit_carrier(self.row(),3)
            self.assertEqual(self.store.load('F1',123)['records'],{})
            factory.return_value.exec.return_value=QDialog.Accepted
            factory.return_value.amount=4
            self.view._edit_carrier(self.row(),3)
            self.assertEqual(self.row().text(4),'7')

    def test_legacy_layout_migration_preserves_widths_and_order(self):
        old=['name','locker','backpack','total','usage']
        widths=[410,80,90,100,220];order=[4,0,2,1,3]
        self.settings.setValue('materials/odyssey/columns',dict(version=1,columns=old,widths=widths,order=order))
        view=OdysseyView(self.state,QLineEdit(),controller=self.controller)
        self.addCleanup(view.close)
        header=view.tree.header()
        self.assertEqual([COLUMNS[header.logicalIndex(i)] for i in range(6)],['usage','name','backpack','carrier','locker','total'])
        for name,width in zip(old,widths): self.assertEqual(header.sectionSize(COLUMNS.index(name)),width)
        self.assertEqual(self.settings.value('materials/odyssey/columns')['columns'],list(COLUMNS))

    def test_unknown_reset_survives_restart_and_future_status_fails_closed(self):
        self.confirm(4);self.confirm(None)
        ledger=self.store.load('F1',123)
        self.assertEqual(ledger['records']['Components/chemicalcatalyst']['last_confirmed_amount'],4)
        ledger['records']['Components/chemicalcatalyst'].update(status='future_status',current_amount=8)
        self.settings.setValue(self.store.key('F1',123),ledger)
        self.deliver()
        self.assertEqual(self.row().text(3),'—')

    def test_translations_placeholders_and_consumables(self):
        keys={k for k in _TRANSLATIONS['en'] if k.startswith('odyssey.carrier')}
        self.assertEqual(len(keys),25)
        fields=lambda s: sorted(f for _,f,_,_ in Formatter().parse(s) if f is not None)
        for lang,table in _TRANSLATIONS.items():
            for key in keys:
                self.assertTrue(table.get(key),(lang,key))
                self.assertEqual(fields(table[key]),fields(_TRANSLATIONS['en'][key]))
        self.view.tabs.setCurrentIndex(3)
        row=next(iter(self.view.items.values()))
        self.assertEqual([row.text(i) for i in (3,4)],['—','0'])
        with patch('cmdrhelper.ui.odyssey_view.OdysseyCarrierDialog') as factory:
            self.view._edit_carrier(row,3);factory.assert_not_called()

    def test_confirmed_stock_and_total_explain_bartender_uncertainty(self):
        from cmdrhelper.help_content import help_topic
        self.confirm(4)
        timestamp = self.view.inventory.carrier_records['Components/chemicalcatalyst']['confirmed_at']
        for column in (3, 4):
            tip = self.row().toolTip(column)
            self.assertIn(timestamp, tip)
            self.assertIn('Barkeeper', tip)
            self.assertIn('andere Spieler', tip)
            self.assertIn('nicht automatisch', tip)
        self.assertIn('zuletzt bestätigten', self.row().toolTip(4))
        for lang, table in _TRANSLATIONS.items():
            self.assertIn(table['odyssey.carrier_hint'], help_topic('materials', lang).text)
            self.assertIn(table['odyssey.carrier_total'], help_topic('materials', lang).text)

    def test_shared_capacity_boundaries_and_confirmed_zero_positions(self):
        records = {f'{m.category}/{m.symbol}': {'current_amount': 0}
                   for m in all_materials() if m.category != 'Consumables'}
        self.assertEqual(carrier_capacity(records).known_amount, 0)
        self.assertTrue(carrier_capacity(records).complete)
        keys = [next(k for k in records if k.startswith(cat+'/')) for cat in ('Items','Components','Data')]
        for total, last in [(999,333),(1000,334),(1001,335)]:
            for key, amount in zip(keys, (333,333,last)):
                records[key]['current_amount'] = amount
            result = carrier_capacity(records)
            self.assertEqual(result.known_amount,total)
            self.assertTrue(result.complete)
            self.assertEqual(result.limit,1000)
            self.assertEqual(result.inconsistent,total > 1000)
        records['Consumables/healthpack'] = {'current_amount': 9999}
        self.assertEqual(carrier_capacity(records).known_amount,1001)

    def test_capacity_unknown_positions_are_a_lower_bound(self):
        records = {f'{m.category}/{m.symbol}': {'current_amount': 0}
                   for m in all_materials() if m.category != 'Consumables'}
        records['Components/chemicalcatalyst']['current_amount'] = 599
        unknown = next(k for k in records if k.startswith('Data/'))
        records[unknown]['current_amount'] = None
        result = carrier_capacity(records)
        self.assertEqual((result.known_amount,result.unknown_positions,result.complete),(599,1,False))
        records[unknown]['current_amount'] = 0
        self.assertTrue(carrier_capacity(records).complete)
        result = carrier_capacity(records,[('Data','new_material'),('Data','new_material')])
        self.assertEqual(result.unknown_positions,1)
        records['Data/new_material'] = {'current_amount': 0}
        self.assertTrue(carrier_capacity(records).complete)
        records['Data/new_material']['current_amount'] = True
        self.assertFalse(carrier_capacity(records).complete)

    def test_capacity_ui_overflow_preserves_entries_and_is_shared_across_tabs(self):
        self.confirm(599)
        self.assertIn('Carrierbestand: ≥ 599 · Lager: — / 1.000',self.view.carrier_status.text())
        self.assertIn('Mindestbestand',self.view.carrier_status.toolTip())
        other = next(m for m in all_materials() if m.category == 'Items')
        self.confirm(402,other.category,other.symbol)
        self.assertEqual(self.store.load('F1',123)['records'][f'Items/{other.symbol}']['current_amount'],402)
        self.assertIn('≥ 1.001 / 1.000',self.view.carrier_status.text())
        self.assertIn('INKONSISTENT',self.view.carrier_status.text())
        self.assertTrue(self.view.carrier_status.font().bold())
        self.assertEqual(self.row().text(3),'599')
        self.assertEqual(self.row().text(4),'—')
        before = self.view.carrier_status.text()
        for tab in range(4):
            self.view.tabs.setCurrentIndex(tab)
            self.search.setText('not_a_visible_material')
            self.assertEqual(self.view.carrier_status.text(),before)
        self.confirm(1001)
        self.assertEqual(self.store.load('F1',123)['records']['Components/chemicalcatalyst']['current_amount'],1001)
        self.state.refresh.assert_not_called()

    def test_capacity_exact_persisted_confirmations_and_reset(self):
        ledger = self.store.load('F1',123)
        for m in all_materials():
            if m.category != 'Consumables':
                ledger['records'][f'{m.category}/{m.symbol}'] = dict(category=m.category,name=m.symbol,
                    current_amount=0,last_confirmed_amount=0,status='manual',confirmed_at='2026-09-15T08:00:00+00:00')
        self.settings.setValue(self.store.key('F1',123),ledger)
        self.settings.sync()
        self.deliver()
        for cat in ('Items','Components','Data'):
            material = next(m for m in all_materials() if m.category == cat)
            self.confirm(333,cat,material.symbol)
        self.assertIn('Carrierbestand: 999 · Lager: — / 1.000',self.view.carrier_status.text())
        self.assertNotIn('≥',self.view.carrier_status.text())
        self.assertIn('vollständig bestätigter Stand',self.view.carrier_status.toolTip())
        self.deliver()
        self.assertTrue(self.view._capacity.complete)
        self.confirm(None)
        self.assertFalse(self.view._capacity.complete)
        self.assertIn('Mindestbestand',self.view.carrier_status.toolTip())


if __name__=='__main__':
    unittest.main()
