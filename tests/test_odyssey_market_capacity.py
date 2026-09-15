import copy
import json
from pathlib import Path
from string import Formatter
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from cmdrhelper.odyssey_market_capacity import read_reservation, usable_with_inventory
from cmdrhelper.i18n import _TRANSLATIONS


class MarketCapacityTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.folder = Path(self.tmp.name)
        self.path = self.folder / 'FCMaterials.json'
        self.data = dict(event='FCMaterials', timestamp='2026-09-15T07:14:55Z',
                         MarketID=1234567890, CarrierID='TST-001', Items=[
            dict(Name=n, Demand=d, Stock=0) for n,d in (
                ('healthmonitor',50),('suitschematic',43),('opinionpolls',5),
                ('smearcampaignplans',3),('weapontestdata',20))])

    def read(self):
        self.path.write_text(json.dumps(self.data))
        return read_reservation(self.folder,1234567890)

    def test_real_reservations_exclude_sale_stock(self):
        self.data['Items'].append(dict(Name='topographicalsurveys',Stock=8,Demand=0))
        result=self.read()
        self.assertEqual(result.reserved,121)
        self.assertEqual(result.occupancy(713),834)

    def test_zero_orders(self):
        for row in self.data['Items']:
            row['Demand']=0
            row['Stock']=99
        self.assertEqual(self.read().occupancy(713),713)
        self.data['Items']=[]
        self.assertEqual(self.read().reserved,0)

    def test_invalid_missing_wrong_carrier_and_unstable(self):
        self.assertIsNone(read_reservation(self.folder,1234567890))
        self.read()
        self.assertIsNone(read_reservation(self.folder,123))
        good=copy.deepcopy(self.data)
        for field,value in [('Demand',None),('Demand',True),('Demand',-1),('Stock',None)]:
            self.data=copy.deepcopy(good)
            self.data['Items'][0][field]=value
            self.assertIsNone(self.read())
        self.data=good
        self.read()
        original=Path.read_bytes
        def racing(path):
            raw=original(path)
            path.write_bytes(raw+b' ')
            return raw
        with patch.object(Path,'read_bytes',racing):
            self.assertIsNone(read_reservation(self.folder,1234567890))

    def test_old_market_not_combined_with_new_stock(self):
        result=self.read()
        inv=SimpleNamespace(reconstructed_at='2026-09-15T07:14:55Z',carrier_records={})
        self.assertTrue(usable_with_inventory(result,inv))
        inv.reconstructed_at='2026-09-15T10:09:32Z'
        self.assertFalse(usable_with_inventory(result,inv))
        self.assertFalse(usable_with_inventory(None,inv))

    def test_translations_and_help(self):
        import importlib
        keys=('odyssey.market_capacity','odyssey.market_reservation',
              'odyssey.market_snapshot','odyssey.market_capacity_hint')
        def fields(text):
            return {field for _,field,_,_ in Formatter().parse(text) if field}
        for lang,translations in _TRANSLATIONS.items():
            for key in keys:
                self.assertEqual(fields(translations[key]),fields(_TRANSLATIONS['en'][key]))
            source=Path(importlib.import_module('cmdrhelper.help_content.'+lang).__file__).read_text()
            self.assertIn(translations[keys[-1]],source)
