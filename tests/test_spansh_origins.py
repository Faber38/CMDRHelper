"""Offline batch identity lookup and partial-cache/UI contracts."""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import Mock
from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QApplication

from cmdrhelper.commodity_master import lookup_by_symbol
from cmdrhelper.commodity_origin import OriginResolver
from cmdrhelper.spansh_cache import SystemCache, normalize
from cmdrhelper.spansh_origins import OriginLookup, LookupWorker, lookup_documents
from cmdrhelper.spansh_stations import SpanshStations
from cmdrhelper.ui.trade_view import TradeView
from cmdrhelper.i18n import get_language, set_language

NOW=datetime(2026,10,6,17,tzinfo=timezone.utc)
EXAMPLES=[('BlueMilk',128639992,'George Lucas','Leesti',3932277478114),
          ('LavianBrandy',128106744,'Lave Station','Lave',633742594786),
          ('SoontillRelics',3225348096,'Cheranovsky City','Ngurii',1458510467810),
          ('JaquesQuinentianStill',128667761,'Jaques Station','Colonia',3238296097059),
          ('CrystallineSpheres',128059402,'Snow Moon','Bento',633675420370)]


def row(example=EXAMPLES[0]):
    _,mid,name,system,address=example
    xyz = {128639992:(72.75,48.75,68.25),128106744:(75.75,48.75,70.75),
           3225348096:(169.5,-42.34375,87.0625),128667761:(-9530.5,-910.28125,19808.125),
           128059402:(16.46875,-31.0625,1.46875)}[mid]
    return dict(market_id=mid,name=name,system_name=system,system_id64=address,
                system_x=xyz[0],system_y=xyz[1],system_z=xyz[2],type='Coriolis Starport',
                small_pads=8,medium_pads=13,large_pads=5,
                services=[{'name':'Market'},{'name':'Dock'},{'name':'Repair'}],
                updated_at='2026-10-06T15:10:39Z',market=[{'buy_price':4708,'supply':42}])


def response(rows): return dict(count=len(rows),results=rows)


class Provider:
    def __init__(self, rows=None, error=None):
        self.rows=[row()] if rows is None else rows
        self.calls=[];self.error=error
    def _request(self,path,payload,cancel):
        self.calls.append((path,payload))
        if self.error: raise self.error
        return response(deepcopy(self.rows))


class State(QObject):
    changed=Signal()
    system='Col 285 Sector VU-O d6-68'
    system_address=2346956392827


class LookupTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.app=QApplication.instance() or QApplication([])

    def setUp(self):
        temp=TemporaryDirectory();self.addCleanup(temp.cleanup);self.root=Path(temp.name)
        self.cache=SystemCache(root=self.root/'cache',now=lambda:NOW)
        self.provider=Provider();self.pool=Mock()
        self.service=OriginLookup(self.cache,provider=self.provider,pool=self.pool)
        self.addCleanup(self.service.timer.stop)

    def run_pending(self):
        self.service.timer.stop();self.service.flush()
        worker=self.service.worker
        if worker: worker.run()

    def test_five_controls_single_batch_and_whitelisted_persistence(self):
        self.provider.rows=[row(e) for e in EXAMPLES]
        for _,mid,*_ in EXAMPLES:self.service.request(mid)
        self.run_pending()
        self.assertEqual(len(self.provider.calls),1)
        path,payload=self.provider.calls[0]
        self.assertEqual(path,'/stations/search')
        self.assertEqual(set(payload['filters']),{'market_id'})
        self.assertEqual(len(payload['filters']['market_id']['value']),5)
        r=OriginResolver(spansh_folder=self.cache.root)
        for _,mid,name,system,address in EXAMPLES:
            o=r.resolve(mid)
            self.assertEqual((o.station_name,o.system_name,o.system_address),(name,system,address))
            data=self.cache.read(address)
            self.assertEqual(data['coverage'],'partial')
            self.assertNotIn('market',data['stations'][0])
            self.assertFalse(self.cache.fresh(data))
            self.assertFalse(self.cache.fetched_today(data))
            self.assertEqual(data['stations'][0]['landing_pads']['large'],5)
            self.assertEqual(data['stations'][0]['services'],['market','repair'])

    def test_shared_id_deduplicated_pending_and_inflight(self):
        a=lookup_by_symbol('BlueMilk').origin_market_id
        b=lookup_by_symbol('LeestianEvilJuice').origin_market_id
        self.assertEqual(a,b)
        self.service.request(a);self.service.request(b)
        self.service.timer.stop();self.service.flush()
        self.service.request(b)
        self.service.worker.run()
        self.service.request(a);self.run_pending()
        self.assertEqual(len(self.provider.calls),1)

    def test_batch_bound_and_no_unsolicited_prefetch(self):
        self.assertFalse(self.service.timer.isActive())
        self.assertEqual(self.provider.calls,[])
        self.provider.rows=[]
        for mid in range(1,13): self.service.request(mid)
        for _ in range(3):self.run_pending()
        self.assertEqual([len(p['filters']['market_id']['value']) for _,p in self.provider.calls],[5,5,2])
        self.assertFalse(self.service.timer.isActive())

    def test_partial_response_missing_id_cached_for_session(self):
        self.service.request(EXAMPLES[0][1]);self.service.request(EXAMPLES[1][1]);self.run_pending()
        self.assertIsNotNone(self.cache.read(EXAMPLES[0][4]))
        self.assertIsNone(self.cache.read(EXAMPLES[1][4]))
        self.service.request(EXAMPLES[1][1]);self.run_pending()
        self.assertEqual(len(self.provider.calls),1)

    def test_timeout_unknown_and_failure_no_refresh_loop(self):
        for error in (TimeoutError(),OSError('offline'),None):
            provider=Provider(rows=[],error=error)
            service=OriginLookup(self.cache,provider=provider,pool=Mock())
            for _ in range(4):
                service.request(EXAMPLES[0][1]);service.timer.stop();service.flush()
                if service.worker:service.worker.run()
            self.assertEqual(len(provider.calls),1)
            self.assertFalse(service.timer.isActive())
            self.assertIsNone(self.cache.read(EXAMPLES[0][4]))

    def test_unrequested_conflicting_and_invalid_records_rejected(self):
        original=row();mid=original['market_id']
        cases=[[dict(original,market_id=7)], [original,dict(original,name='Wrong')],
               [dict(original,system_id64=True)], [dict(original,system_x=float('nan'))],
               [dict(original,large_pads=-1)], [dict(original,updated_at='bad')]]
        for rows in cases:
            self.assertEqual(lookup_documents(response(rows),{mid},NOW),[])
        # A bad unsolicited row does not discard an unrelated valid requested identity.
        self.assertEqual(len(lookup_documents(response([original,dict(original,market_id=7)]),{mid},NOW)),1)

    def test_full_cache_metadata_and_stations_preserved(self):
        raw=row();address=raw['system_id64']
        old=normalize({'system':{'id64':address,'name':raw['system_name'],
            'stations':[{'id':99,'name':'Other Port','type':'Outpost'}]}},address,NOW-timedelta(days=8))
        self.cache.write(old)
        self.cache.merge_lookup(lookup_documents(response([raw]),{raw['market_id']},NOW)[0])
        data=self.cache.read(address)
        self.assertEqual(data.get('coverage','full'),'full')
        self.assertEqual(data['fetched_at'],old['fetched_at'])
        self.assertEqual({r['market_id'] for r in data['stations']},{99,raw['market_id']})
        self.assertFalse(self.cache.fresh(data))

    def test_partial_does_not_block_automatic_or_manual_full_fetch(self):
        raw=row();address=raw['system_id64']
        partial=lookup_documents(response([raw]),{raw['market_id']},NOW)[0]
        for mode in ('automatic','manual'):
            cache=SystemCache(root=self.root/mode,now=lambda:NOW,
                fetch=Mock(return_value={'system':{'id64':address,'name':'Leesti','stations':[]}}))
            cache.write(partial)
            full,success=cache.request(address,**{mode:True})
            self.assertTrue(success);cache.fetch.assert_called_once_with(address)
            self.assertTrue(cache.fresh(full));self.assertTrue(cache.fetched_today(full))
            self.assertEqual(full.get('coverage','full'),'full')

    def test_conflicting_existing_cache_never_overwritten(self):
        raw=row();address=raw['system_id64'];mid=raw['market_id']
        doc=lookup_documents(response([raw]),{mid},NOW)[0];self.cache.write(doc)
        other=lookup_documents(response([dict(raw,name='Wrong')]),{mid},NOW)[0]
        with self.assertRaises(ValueError):self.cache.merge_lookup(other)
        self.assertEqual(self.cache.read(address),doc)

    def make_view(self):
        old=get_language();self.addCleanup(set_language,old);set_language('de')
        db=self.root/'systems.db'
        if not db.exists():
            with sqlite3.connect(db) as con:
                con.execute('CREATE TABLE systems(system_address INTEGER,name TEXT,x REAL,y REAL,z REAL)')
                con.execute('INSERT INTO systems VALUES(?,?,?,?,?)',(State.system_address,State.system,80.125,213.28125,167.46875))
        state=State();state.database=SimpleNamespace(path=db)
        state.spansh_stations=SpanshStations(SimpleNamespace(value=lambda *args:False),cache=self.cache,pool=Mock())
        state.spansh_stations.origins.provider=self.provider
        state.spansh_stations.origins.pool=Mock()
        self.addCleanup(state.spansh_stations.origins.timer.stop)
        view=TradeView(state,provider=Mock(),pool=Mock());view.show();self.addCleanup(view.close)
        view.tabs.setCurrentIndex(1);view.local_only.setChecked(True)
        view.commodity.set_commodity(lookup_by_symbol('BlueMilk').frontier_id)
        view._origin_worker.run()
        return state,view

    def test_ui_live_update_local_only_restart_and_one_request(self):
        state,view=self.make_view()
        self.assertIn('128639992',view.origin_info.text())
        origins=state.spansh_stations.origins
        origins.timer.stop();origins.flush();origins.worker.run()
        view._origin_worker.run()
        text=view.origin_info.text()
        self.assertIn('George Lucas · Leesti',text)
        self.assertIn('192,3 ly',text)
        self.assertIn('nicht bestätigt',text)
        self.assertNotIn('4.708',text);self.assertNotIn('42',text)
        self.assertEqual(view.offers,());self.assertEqual(view.table.rowCount(),0)
        self.assertEqual(len(self.provider.calls),1)
        # New view, service, and local resolver reuse the persisted partial cache.
        self.provider=Provider(error=AssertionError('network on restart'))
        state2,view2=self.make_view()
        self.assertIn('George Lucas · Leesti',view2.origin_info.text())
        self.assertFalse(state2.spansh_stations.origins.timer.isActive())
        self.assertEqual(self.provider.calls,[])
        view2.invalidate_origin();view2._origin_worker.run()
        self.assertEqual(self.provider.calls,[])

    def test_local_database_origin_does_not_schedule_network(self):
        db=self.root/'systems.db'
        with sqlite3.connect(db) as con:
            con.executescript('''CREATE TABLE systems(system_address INTEGER,name TEXT,x REAL,y REAL,z REAL);
                CREATE TABLE station_observations(market_id INTEGER,station_name TEXT,system_address INTEGER);''')
            con.execute('INSERT INTO systems VALUES(?,?,?,?,?)',(EXAMPLES[0][4],'Leesti',72.75,48.75,68.25))
            con.execute('INSERT INTO station_observations VALUES(?,?,?)',(EXAMPLES[0][1],'George Lucas',EXAMPLES[0][4]))
        state,view=self.make_view()
        self.assertIn('George Lucas · Leesti',view.origin_info.text())
        self.assertFalse(state.spansh_stations.origins.timer.isActive())
        self.assertEqual(self.provider.calls,[])
