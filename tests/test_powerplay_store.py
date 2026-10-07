"""Schema 23 and persistent PP2 replay; all writes use temporary databases."""
from datetime import date, datetime, timedelta, timezone
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch
from zoneinfo import ZoneInfo

from cmdrhelper.database import CMDRDatabase
from cmdrhelper.journal_reader import classify_journal_file
from cmdrhelper.powerplay_store import PowerplayImportConflict, day_bounds
from tests.test_powerplay_chronicle import event, bounty, scan, credit, delivery
from tests.test_powerplay_transport import real_events

DAY = date(2026, 10, 6)
ZONE = ZoneInfo('Europe/Berlin')
PP_TABLES = ('pp2_events', 'pp2_import_checkpoints', 'pp2_merit_state', 'pp2_history_policy', 'pp2_sources')


class Legacy22(CMDRDatabase):
    def _maybe_migrate_v23(self):
        pass


class MigrationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name)/'main.db'
        Legacy22(self.path)

    def test_upgrade_backup_and_second_start(self):
        db = CMDRDatabase(self.path)
        with db._connect() as con:
            self.assertEqual(con.execute('PRAGMA user_version').fetchone()[0], 23)
            self.assertEqual(con.execute('PRAGMA integrity_check').fetchone()[0], 'ok')
            for name in PP_TABLES:
                self.assertEqual(con.execute('SELECT count(*) FROM '+name).fetchone()[0], 0)
        backups = list(self.path.parent.glob('*.pre-v23-*.bak'))
        self.assertEqual(len(backups), 1)
        with sqlite3.connect(backups[0]) as con:
            self.assertEqual(con.execute('PRAGMA user_version').fetchone()[0], 22)
        CMDRDatabase(self.path)
        self.assertEqual(list(self.path.parent.glob('*.pre-v23-*.bak')), backups)

    def test_migration_rollback_and_backup_failure(self):
        from cmdrhelper.powerplay_store import create_schema
        def fail(con):
            create_schema(con)
            raise RuntimeError('abort migration')
        with patch('cmdrhelper.powerplay_store.create_schema', side_effect=fail):
            with self.assertRaises(RuntimeError):
                CMDRDatabase(self.path)
        with sqlite3.connect(self.path) as con:
            self.assertEqual(con.execute('PRAGMA user_version').fetchone()[0], 22)
            self.assertFalse(con.execute("SELECT name FROM sqlite_master WHERE name LIKE 'pp2_%'").fetchall())
        with patch.object(CMDRDatabase, '_create_migration_backup', side_effect=RuntimeError('no backup')):
            with self.assertRaises(RuntimeError):
                CMDRDatabase(self.path)
        with sqlite3.connect(self.path) as con:
            self.assertEqual(con.execute('PRAGMA user_version').fetchone()[0], 22)


class StoreTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.folder = Path(tmp.name)
        self.db = CMDRDatabase(self.folder/'main.db')
        clock = patch('cmdrhelper.powerplay_store.local_today', return_value=DAY)
        clock.start()
        self.addCleanup(clock.stop)

    def journal(self, rows, name='Journal.2026-10-06T100000.01.log', fid='A'):
        path = self.folder/name
        header = dict(event='Fileheader', timestamp=rows[0]['timestamp'], gameversion=name)
        identity = dict(event='Commander', timestamp=rows[0]['timestamp'], FID=fid, Name='Test '+fid)
        path.write_text(''.join(json.dumps(e)+'\n' for e in [header, identity, *rows]))
        session = classify_journal_file(path)
        session['commander_id'] = self.db.resolve_session_commander(session)
        return session

    def sync(self, *sessions):
        return self.db.sync_powerplay(sessions, day=DAY, zone=ZONE)

    def count(self, table='pp2_events'):
        with self.db._connect() as con:
            return con.execute('SELECT count(*) FROM '+table).fetchone()[0]

    def test_duplicate_same_second_and_restart_and_archive(self):
        s = self.journal([credit(), credit()])
        self.sync(s)
        initial = self.count()
        self.sync(s)
        self.db = CMDRDatabase(self.db.path)
        self.sync(s)
        self.db.import_journal_archive(self.folder)
        self.assertEqual(self.count(), initial)
        with self.db._connect() as con:
            self.assertEqual(con.execute("SELECT count(*) FROM pp2_events WHERE event_type='PowerplayMerits'").fetchone()[0], 2)

    def test_partial_line_append_rotation_and_source_copy(self):
        s = self.journal([delivery()])
        self.sync(s)
        p = Path(s['journal_file'])
        payload = json.dumps(credit(0,48,12831))
        with p.open('a') as f:f.write(payload[:20])
        self.sync(s)
        self.assertIsNone(self.db.powerplay_merits(s['commander_id']))
        with p.open('a') as f:f.write(payload[20:]+'\n')
        self.sync(s)
        self.assertEqual(self.db.powerplay_merits(s['commander_id']), 12831)
        before = self.count()
        copied = self.folder/'moved.01.log'
        copied.write_bytes(p.read_bytes())
        moved = dict(s,journal_file=str(copied))
        self.sync(moved)
        self.assertEqual(self.count(), before)
        second = self.journal([credit(20,3,12834)], name='Journal.2026-10-06T120000.02.log')
        self.sync(second)
        self.assertEqual(self.db.powerplay_merits(s['commander_id']),12834)

    def test_conflict_truncation_and_atomic_failure(self):
        s = self.journal([delivery(),credit(0,48,12831)])
        self.sync(s)
        p=Path(s['journal_file']); original=p.read_bytes(); before=self.count()
        p.write_bytes(original.replace(b'12831',b'12832'))
        with self.assertRaises(PowerplayImportConflict):self.sync(s)
        p.write_bytes(original[:20])
        with self.assertRaises(PowerplayImportConflict):self.sync(s)
        p.write_bytes(original)
        with self.db._connect() as con:
            con.execute("CREATE TRIGGER fail_pp2 BEFORE INSERT ON pp2_events BEGIN SELECT RAISE(ABORT,'fail'); END")
        with p.open('a') as f:f.write(json.dumps(credit(10,3,12834))+'\n')
        with self.assertRaises(sqlite3.IntegrityError):self.sync(s)
        self.assertEqual(self.count(),before)
        self.assertEqual(self.db.powerplay_merits(s['commander_id']),12831)
        with self.db._connect() as con:con.execute('DROP TRIGGER fail_pp2')
        self.sync(s)
        self.assertEqual(self.db.powerplay_merits(s['commander_id']),12834)

    def test_commander_isolation_ambiguous_and_power_change(self):
        a=self.journal([credit()],fid='A')
        b=self.journal([dict(credit(),Power='Other',TotalMerits=999)],name='Journal.2026-10-06T120000.01.log',fid='B')
        self.sync(dict(a,attribution_status='unknown'),dict(b,attribution_status='ambiguous'))
        self.assertEqual(self.count(),0)
        self.sync(a,b)
        self.assertEqual(self.db.powerplay_merits(a['commander_id']),100)
        self.assertEqual(self.db.powerplay_merits(a['commander_id'],power='Nakato Kaine'),100)
        self.assertIsNone(self.db.powerplay_merits(a['commander_id'],power='Other'))
        self.assertIsNone(self.db.powerplay_merits(a['commander_id'],power=''))
        self.assertEqual(self.db.powerplay_merits(b['commander_id']),999)
        with Path(a['journal_file']).open('a') as f:
            f.write(json.dumps(event('PowerplayDefect',2,Power='Nakato Kaine'))+'\n')
            f.write(json.dumps(dict(credit(3,1,1),Power='Other'))+'\n')
        self.sync(a)
        self.assertIsNone(self.db.powerplay_merits(a['commander_id'],power='Nakato Kaine'))
        self.assertEqual(self.db.powerplay_merits(a['commander_id'],power='Other'),1)
        groups=self.db.powerplay_day(a['commander_id'],DAY,zone=ZONE).groups
        self.assertEqual([g.power for g in groups],['Nakato Kaine','Other'])

    def test_initial_today_only_then_midnight_live(self):
        prior=dict(delivery(),timestamp='2026-10-05T21:59:59Z')
        today=dict(delivery(),timestamp='2026-10-05T22:00:00Z')
        s=self.journal([prior,today],name='Journal.2026-10-05T230000.01.log')
        self.sync(s)
        self.assertEqual(len(self.db.powerplay_day(s['commander_id'],DAY,zone=ZONE).groups),1)
        self.assertEqual(self.db.powerplay_day(s['commander_id'],DAY-timedelta(days=1),zone=ZONE).groups,[])
        with Path(s['journal_file']).open('a') as f:f.write(json.dumps(dict(delivery(),timestamp='2026-10-06T22:00:00Z'))+'\n')
        self.db.sync_powerplay([s],day=DAY+timedelta(days=1),zone=ZONE)
        self.assertEqual(len(self.db.powerplay_day(s['commander_id'],DAY+timedelta(days=1),zone=ZONE).groups),1)

    def test_day_bounds_and_dst(self):
        for day,hours in [(date(2026,3,29),23),(date(2026,10,25),25),(DAY,24),(date(2026,1,6),24)]:
            a,b=day_bounds(day,ZONE)
            self.assertEqual((datetime.fromisoformat(b)-datetime.fromisoformat(a)).total_seconds()/3600,hours)
        self.assertEqual(day_bounds(DAY,ZONE)[0],'2026-10-05T22:00:00.000000Z')
        self.assertEqual(day_bounds(date(2026,1,6),ZONE)[0],'2026-01-05T23:00:00.000000Z')

    def test_replay_transport_barrier_and_merit_total(self):
        s=self.journal([bounty(),event('Cargo'),credit(),scan(10),credit(11,10),*real_events(),credit(30000,4,13233)])
        self.sync(s)
        groups=self.db.powerplay_day(s['commander_id'],DAY,zone=ZONE).groups
        self.assertEqual(groups[0].certainty,'unknown')
        self.assertEqual(groups[1].certainty,'temporal')
        delivered=next(g for g in groups if g.action['event']=='PowerplayDeliver')
        self.assertEqual(delivered.certainty,'explicit')
        self.assertEqual([e['MeritsGained'] for e in delivered.credits],[3600,48])
        self.assertEqual(self.db.powerplay_merits(s['commander_id']),13233)

    def test_real_day_six_bounties_eight_scans_and_transport(self):
        from collections import Counter
        from cmdrhelper.powerplay_chronicle import today_groups
        fixture = json.loads((Path(__file__).parent/'fixtures/powerplay_day_20261006.json').read_text())
        sessions = []
        for source in fixture:
            path = self.folder/source['source']
            path.write_text(''.join(json.dumps(e)+'\n' for e in source['events']))
            session = classify_journal_file(path)
            session['commander_id'] = self.db.resolve_session_commander(session)
            sessions.append(session)
        self.sync(*sessions)
        cid = sessions[0]['commander_id']
        groups = today_groups(self.db.powerplay_day(cid,DAY,zone=ZONE), DAY, ZONE)
        counts = Counter(g.action['event'] for g in groups)
        self.assertEqual(counts['Bounty'],6)
        self.assertEqual(counts['ShipTargeted'],8)
        self.assertEqual(counts['SearchAndRescue'],2)
        self.assertEqual(len(groups),22)
        self.assertEqual(Counter(g.certainty for g in groups),dict(temporal=16,explicit=2,unknown=4))
        self.assertEqual([g.action['timestamp'] for g in groups],sorted([g.action['timestamp'] for g in groups],reverse=True))
        bounties = {g.action['PilotName_Localised']:(g.action['TotalReward'],g.credits[0]['MeritsGained'],g.system) for g in groups if g.action['event']=='Bounty'}
        for pilot,reward,gain in [('Jim Bell',453097,60),('Andreas Martin Clemenz',163361,21),('Jock Ripper',360818,48),('Flavio Antonietti',134247,17),('Theia Claw',279561,37),('Tiddlywinks',603200,80)]:
            self.assertEqual(bounties[pilot],(reward,gain,'HR 4827'))
        deliver=next(g for g in groups if g.action['event']=='PowerplayDeliver')
        self.assertEqual([c['MeritsGained'] for c in deliver.credits],[3600,48])
        self.assertEqual((deliver.action['Count'],deliver.system,deliver.station),(10,'HIP 70049','Mille Enterprise'))
        self.assertEqual(self.db.powerplay_merits(cid),13256)
        self.assertEqual(max(len(g.credits) for g in groups if g.certainty=='unknown'),13)

    def test_delete_all_keeps_total_and_policy_blocks_reimport(self):
        s=self.journal([delivery(),credit(0,48,12831)])
        self.sync(s)
        cid=s['commander_id']
        preview=self.db.powerplay_delete_preview(cid,now=datetime(2026,10,6,12,tzinfo=timezone.utc))
        self.assertEqual(preview['events'],2)
        self.db.delete_powerplay_history(cid,preview)
        self.assertEqual(self.count(),0)
        self.assertEqual(self.db.powerplay_merits(cid),12831)
        with self.db._connect() as con:con.execute('DELETE FROM pp2_import_checkpoints')
        self.sync(s)
        self.assertEqual(self.count(),0)
        copy=self.folder/'renamed.99.log';copy.write_bytes(Path(s['journal_file']).read_bytes())
        self.sync(dict(s,journal_file=str(copy)))
        self.assertEqual(self.count(),0)
        with patch('cmdrhelper.powerplay_store.PARSER_VERSION',2):
            self.sync(s)
        self.assertEqual(self.count(),0)
        with Path(s['journal_file']).open('a') as f:f.write(json.dumps(dict(credit(0,3,12834),timestamp='2026-10-06T12:00:01Z'))+'\n')
        self.sync(s)
        self.assertEqual(self.db.powerplay_merits(cid),12834)
        self.assertEqual(len(self.db.powerplay_day(cid,DAY,zone=ZONE).groups),1)

    def test_delete_seven_thirty_commander_guard_and_rollback(self):
        a=self.journal([delivery(),credit()]);b=self.journal([delivery()],name='Journal.2026-10-06T120000.01.log',fid='B')
        self.sync(a,b);cid=a['commander_id']
        for days in (7,30):
            retained=DAY+timedelta(days=days-1)
            self.assertEqual(self.db.powerplay_delete_preview(cid,days,day=retained,zone=ZONE)['events'],0)
            preview=self.db.powerplay_delete_preview(cid,days,day=retained+timedelta(days=1),zone=ZONE)
            self.assertEqual(preview['events'],2)
        with self.assertRaises(ValueError):self.db.delete_powerplay_history(b['commander_id'],preview)
        with self.db._connect() as con:con.execute("CREATE TRIGGER fail_delete BEFORE UPDATE ON pp2_history_policy BEGIN SELECT RAISE(ABORT,'fail'); END")
        before=self.count()
        with self.assertRaises(sqlite3.IntegrityError):self.db.delete_powerplay_history(cid,preview)
        self.assertEqual(self.count(),before)
        with self.db._connect() as con:con.execute('DROP TRIGGER fail_delete')
        self.db.delete_powerplay_history(cid,preview)
        self.assertEqual(len(self.db.powerplay_day(b['commander_id'],DAY,zone=ZONE).groups),1)

    def test_stale_delete_confirmation_is_rejected(self):
        s=self.journal([credit()]);self.sync(s);cid=s['commander_id']
        preview=self.db.powerplay_delete_preview(cid)
        with Path(s['journal_file']).open('a') as f:
            f.write(json.dumps(credit(20,3,103))+'\n')
        self.sync(s)
        with self.assertRaises(ValueError):self.db.delete_powerplay_history(cid,preview)
        self.assertEqual(self.db.powerplay_merits(cid),103)

    def test_invalid_line_is_a_replay_barrier(self):
        s=self.journal([bounty()]);self.sync(s)
        with Path(s['journal_file']).open('a') as f:
            f.write('{broken json}\n'+json.dumps(credit())+'\n')
        self.sync(s)
        groups=self.db.powerplay_day(s['commander_id'],DAY,zone=ZONE).groups
        self.assertEqual([g.certainty for g in groups],['unknown'])

    def test_rotated_parts_same_header_time_order_merit_projection(self):
        sessions=[]
        for part,total in [(1,100),(2,90)]:
            s=self.journal([credit(0,4,total)],name=f'Journal.same.{part:02}.log')
            p=Path(s['journal_file'])
            rows=[json.loads(line) for line in p.read_text().splitlines()]
            rows[0]['part']=part
            p.write_text(''.join(json.dumps(e)+'\n' for e in rows))
            sessions.append(s)
        self.sync(*reversed(sessions))
        self.assertEqual(self.db.powerplay_merits(sessions[0]['commander_id']),90)

    def test_removed_source_does_not_remove_history_or_block_live(self):
        old=self.journal([credit()]);self.sync(old)
        Path(old['journal_file']).unlink()
        new=self.journal([credit(20,4,104)],name='Journal.next.01.log')
        self.sync(old,new)
        self.assertEqual(self.db.powerplay_merits(new['commander_id']),104)
        self.assertEqual(len(self.db.powerplay_day(new['commander_id'],DAY,zone=ZONE).groups),2)
