import io,json,unittest,webbrowser,subprocess,http.cookiejar
from datetime import datetime,timedelta,timezone
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError
from PySide6.QtGui import QDesktopServices
from cmdrhelper.inara_uploader import upload_batch,INARA_API_URL
from cmdrhelper.online_services import test_inara_connection
from tests import test_inara_uploader as fixtures

class InaraSafetyTests(unittest.TestCase):
    rows=fixtures.InaraTransportTests.rows
    def reply(self,events=None,header=200):
        return fixtures.Reply({'header':{'eventStatus':header},'events':events if events is not None else [{'eventStatus':200,'eventCustomID':r['id']} for r in self.rows]})
    def test_success_and_no_browser_cookie_file_or_process_access(self):
        def opener(req,timeout):
            self.assertEqual(req.full_url,INARA_API_URL)
            self.assertEqual(req.get_method(),'POST')
            self.assertFalse(any(k.lower() in ('cookie','authorization') for k in req.headers))
            data=json.loads(req.data)
            self.assertEqual(data['header']['APIkey'],'synthetic-key')
            return self.reply()
        with patch('builtins.open',side_effect=AssertionError('file access')), patch.object(Path,'open',side_effect=AssertionError('file access')), patch.object(webbrowser,'open',side_effect=AssertionError('browser')), patch.object(subprocess,'Popen',side_effect=AssertionError('process')), patch.object(http.cookiejar.CookieJar,'add_cookie_header',side_effect=AssertionError('cookies')), patch.object(http.cookiejar.CookieJar,'extract_cookies',side_effect=AssertionError('cookies')), patch.object(QDesktopServices,'openUrl',side_effect=AssertionError('desktop')):
            self.assertEqual(upload_batch('synthetic-key','Synthetic','TEST-A',self.rows,opener=opener),([1,2],{}))
            with patch('cmdrhelper.online_services.urlopen',side_effect=opener):
                self.assertTrue(test_inara_connection('Synthetic','synthetic-key')[0])
    def test_http_auth_rate_limit_timeout_invalid_key_and_bad_json(self):
        for code in (401,403,429):
            with self.subTest(code=code),self.assertRaises(RuntimeError):
                upload_batch('synthetic','Synthetic','TEST-A',self.rows,opener=lambda *a,**k: (_ for _ in ()).throw(HTTPError(INARA_API_URL,code,'synthetic',{'Retry-After':'3600'},None)))
        with self.assertRaises(RuntimeError):
            upload_batch('synthetic','Synthetic','TEST-A',self.rows,opener=lambda *a,**k:self.reply(header=400))
        with self.assertRaises(RuntimeError):
            upload_batch('synthetic','Synthetic','TEST-A',self.rows,opener=lambda *a,**k:io.BytesIO(b'{broken'))
        with self.assertRaises(RuntimeError):
            upload_batch('synthetic','Synthetic','TEST-A',self.rows,opener=lambda *a,**k: (_ for _ in ()).throw(TimeoutError()))
    def test_custom_ids_match_when_reordered(self):
        sent,failed=upload_batch('synthetic','Synthetic','TEST-A',self.rows,opener=lambda *a,**k:self.reply([{'eventCustomID':2,'eventStatus':200},{'eventCustomID':1,'eventStatus':400}]))
        self.assertEqual(sent,[2])
        self.assertEqual(set(failed),{1})
    def test_malformed_object_shape_is_controlled_error(self):
        for reply in (None,[],{'header':{'eventStatus':'invalid'}},{'header':{'eventStatus':200},'events':[42,42]}):
            with self.subTest(kind=type(reply).__name__),self.assertRaises(RuntimeError):
                upload_batch('synthetic','Synthetic','TEST-A',self.rows,opener=lambda *a,**k:fixtures.Reply(reply))
    def fixture(self):
        box=fixtures.InaraOutboxTests();box.setUp();self.addCleanup(box.tearDown)
        case=fixtures.InaraCommanderSettingsTests();case.setUp();self.addCleanup(case.tearDown)
        state=case.state;state.database=box.db
        state.set_inara_settings('Same','synthetic-A',True,fid='F-A')
        state.set_inara_settings('Same','synthetic-B',True,fid='F-B')
        state.commander='Same'
        box.db.apply_commander_journal_delta(1,'a.log',[box.event()],100,enqueue_inara=True)
        return state,box.db
    def switch(self,state,cid):
        state._invalidate_inara_worker();state.commander_id=cid;state.commander_fid='F-A' if cid==1 else 'F-B';state._load_live_inara_settings()
    def test_inflight_ack_completes_original_event_without_retry(self):
        state,db=self.fixture();calls=[]
        class Immediate:
            def __init__(self,target,**kw):self.target=target
            def start(self):self.target()
        def upload(key,name,fid,rows):
            self.assertEqual((key,fid),('synthetic-A','F-A'))
            calls.append([r['id'] for r in rows])
            if len(calls)==1:self.switch(state,2)
            return [r['id'] for r in rows],{}
        with patch('cmdrhelper.state.threading.Thread',Immediate),patch('cmdrhelper.state.upload_batch',side_effect=upload):
            state._upload_pending_to_inara()
            self.assertEqual(len(db.inara_pending(1)),0)
            self.assertEqual(db.inara_pending(2),[])
            self.switch(state,1);state._upload_pending_to_inara()
            self.assertEqual(len(calls),1)
            self.assertEqual(db.inara_pending(1),[])
            state._upload_pending_to_inara();self.assertEqual(len(calls),1)
    def test_429_retry_after_respected_and_retry_ceiling(self):
        state,db=self.fixture()
        class Immediate:
            def __init__(self,target,**kw):self.target=target
            def start(self):self.target()
        def fail(*args):
            return upload_batch(*args,opener=lambda *a,**k: (_ for _ in ()).throw(HTTPError(INARA_API_URL,429,'synthetic',{'Retry-After':'3600'},None)))
        with patch('cmdrhelper.state.threading.Thread',Immediate),patch('cmdrhelper.state.upload_batch',side_effect=fail):state._upload_pending_to_inara()
        self.assertEqual(db.inara_pending(1),[])
        for age,expected in ((31,0),(61,0)):
            with db._connect() as con:con.execute('UPDATE inara_outbox SET last_attempt_at=?',((datetime.now(timezone.utc)-timedelta(seconds=age)).isoformat(),))
            self.assertEqual(len(db.inara_pending(1)),expected)
        with db._connect() as con:con.execute("UPDATE inara_outbox SET retry_count=8,last_attempt_at='2000-01-01T00:00:00+00:00'")
        self.assertEqual(db.inara_pending(1),[])
    def test_running_worker_suppresses_parallel_duplicate_and_missing_fid(self):
        state,db=self.fixture();queued=[]
        class Queued:
            def __init__(self,target,**kw):self.target=target
            def start(self):queued.append(self.target)
        with patch('cmdrhelper.state.threading.Thread',Queued):
            state._upload_pending_to_inara();state._upload_pending_to_inara()
            self.assertEqual(len(queued),1)
            state._invalidate_inara_worker();state.commander_fid=''
            state._upload_pending_to_inara();self.assertEqual(len(queued),1)
    def test_same_names_two_fids_use_separate_keys_and_outbox(self):
        state,db=self.fixture()
        with db._connect() as con:
            con.execute("UPDATE commanders SET current_name='Same'")
            con.execute("INSERT INTO journal_sessions(journal_file,commander_id,fid_seen,attribution_status,last_read_offset) VALUES('b.log',2,'F-B','identified',0)")
        db.apply_commander_journal_delta(2,'b.log',[{'event':'FSDJump','timestamp':'2026-10-18T00:00:00Z','StarSystem':'Synthetic B'}],100,enqueue_inara=True)
        calls=[]
        class Immediate:
            def __init__(self,target,**kw):self.target=target
            def start(self):self.target()
        def upload(key,name,fid,rows):
            self.assertEqual(key, 'synthetic-A' if fid=='F-A' else 'synthetic-B')
            self.assertEqual(name,'Same')
            calls.append((fid,{r['id'] for r in rows}))
            return [r['id'] for r in rows],{}
        with patch('cmdrhelper.state.threading.Thread',Immediate),patch('cmdrhelper.state.upload_batch',side_effect=upload):
            state._upload_pending_to_inara();self.switch(state,2);state._upload_pending_to_inara()
        self.assertEqual([c[0] for c in calls],['F-A','F-B'])
        self.assertTrue(calls[0][1].isdisjoint(calls[1][1]))
        self.assertEqual(db.inara_pending(1)+db.inara_pending(2),[])
    def test_retry_after_seconds_dates_invalid_and_shorter_backoff(self):
        from email.utils import format_datetime
        from cmdrhelper.inara_uploader import retry_after_seconds, InaraUploadError
        now=datetime(2026,10,18,tzinfo=timezone.utc)
        for value,expected in [('120',120),(' 7200 ',7200),
                (format_datetime(now+timedelta(seconds=900),usegmt=True),900),
                (format_datetime(now-timedelta(seconds=10),usegmt=True),0),
                (None,0),('',0),('-1',0),('1.5',0),('NaN',0),('invalid',0),('9'*5000,0)]:
            with self.subTest(value_type=type(value).__name__):
                self.assertEqual(retry_after_seconds(value,now),expected)
        for value in ('1',None,'invalid'):
            state,db=self.fixture()
            row=db.inara_pending(1)[0]
            db.update_inara_outbox(errors={row['id']:'Inara: http_error'},retry_seconds=retry_after_seconds(value),commander_id=1,fid='F-A',expected_rows=[row])
            with db._connect() as con:
                con.execute('UPDATE inara_outbox SET last_attempt_at=?',((datetime.now(timezone.utc)-timedelta(seconds=31)).isoformat(),))
            self.assertEqual(db.inara_pending(1),[])
        date=format_datetime(datetime.now(timezone.utc)+timedelta(hours=2),usegmt=True)
        with self.assertRaises(InaraUploadError) as caught:
            upload_batch('synthetic','Synthetic','TEST-A',self.rows,opener=lambda *a,**k: (_ for _ in ()).throw(HTTPError(INARA_API_URL,429,'synthetic',{'Retry-After':date},None)))
        self.assertGreaterEqual(caught.exception.retry_seconds,7198)

    def test_response_validation_matrix(self):
        from copy import deepcopy
        base={'header':{'eventStatus':200},'events':[{'eventCustomID':1,'eventStatus':200},{'eventCustomID':2,'eventStatus':202}]}
        cases=[None,[],{}, {'header':None},{'header':[]},{'header':{}},
               {'header':{'eventStatus':200}},dict(base,events=None),dict(base,events={}),dict(base,events=[])]
        for field,values in [('eventCustomID',[None,True,'1',1.0,[],999,2]),
                             ('eventStatus',[None,True,'200',200.0,[],0,999]),
                             ('eventStatusText',[None,[],42])]:
            for value in values:
                reply=deepcopy(base);reply['events'][0][field]=value;cases.append(reply)
        for field in ('eventCustomID','eventStatus'):
            reply=deepcopy(base);del reply['events'][0][field];cases.append(reply)
        for value in (None,[],True,1,'text'):
            reply=deepcopy(base);reply['events'][0]=value;cases.append(reply)
        for value in (True,'200',[],None):
            reply=deepcopy(base);reply['header']['eventStatus']=value;cases.append(reply)
        for reply in cases:
            with self.subTest(case=cases.index(reply)),self.assertRaises(RuntimeError):
                upload_batch('synthetic','Synthetic','TEST-A',self.rows,opener=lambda *a,**k:fixtures.Reply(reply))
        for body in (b'',b'{broken'):
            with self.assertRaises(RuntimeError):
                upload_batch('synthetic','Synthetic','TEST-A',self.rows,opener=lambda *a,**k:io.BytesIO(body))
        self.assertEqual(upload_batch('synthetic','Synthetic','TEST-A',self.rows,opener=lambda *a,**k:fixtures.Reply(base)),([1,2],{}))

    def test_late_failure_updates_original_owner_only(self):
        from cmdrhelper.inara_uploader import InaraUploadError
        state,db=self.fixture();state.viewed_commander_id=2
        class Immediate:
            def __init__(self,target,**kw):self.target=target
            def start(self):self.target()
        def upload(*args):
            self.switch(state,2)
            raise InaraUploadError('http_error',http_status=429,retry_seconds=900)
        with patch('cmdrhelper.state.threading.Thread',Immediate),patch('cmdrhelper.state.upload_batch',side_effect=upload):state._upload_pending_to_inara()
        self.assertEqual((state.commander_id,state.commander_fid,state.viewed_commander_id),(2,'F-B',2))
        self.assertEqual(state.inara_upload_status,'waiting')
        with db._connect() as con:
            self.assertEqual(con.execute('SELECT commander_id,status,retry_count FROM inara_outbox').fetchall(),[(1,'error',1)])
        self.assertEqual(db.inara_pending(1),[])

    def test_generation_and_identity_mutation_cannot_acknowledge(self):
        class Immediate:
            def __init__(self,target,**kw):self.target=target
            def start(self):self.target()
        for mutation in ('generation','fid','owner','source','payload'):
            with self.subTest(mutation=mutation):
                state,db=self.fixture()
                def upload(*args):
                    if mutation=='generation':state._inara_jobs['F-A']=object()
                    else:
                        with db._connect() as con:
                            if mutation=='fid':con.execute("UPDATE commanders SET fid='F-CONFLICT' WHERE id=1")
                            elif mutation=='owner':con.execute('UPDATE inara_outbox SET commander_id=2')
                            elif mutation=='source':con.execute("UPDATE inara_outbox SET source_key='changed'")
                            elif mutation=='payload':con.execute("UPDATE inara_outbox SET event_data_json='{}'")
                    return [args[3][0]['id']],{}
                with patch('cmdrhelper.state.threading.Thread',Immediate),patch('cmdrhelper.state.upload_batch',side_effect=upload):state._upload_pending_to_inara()
                with db._connect() as con:self.assertEqual(con.execute('SELECT status,retry_count FROM inara_outbox').fetchall(),[('pending',0)])

    def test_bound_update_is_atomic_and_rejects_foreign_ids(self):
        state,db=self.fixture();rows=db.inara_pending(1)
        before=db.path.read_bytes()
        with self.assertRaises(ValueError):
            db.update_inara_outbox([rows[0]['id'],999],commander_id=1,fid='F-A',expected_rows=rows)
        self.assertEqual(db.path.read_bytes(),before)
        for fid in ('','F-B'):
            with self.assertRaises(ValueError):
                db.update_inara_outbox([rows[0]['id']],commander_id=1,fid=fid,expected_rows=rows)
        self.assertEqual(db.path.read_bytes(),before)
        db.update_inara_outbox([rows[0]['id']],commander_id=1,fid='F-A',expected_rows=rows)
        with self.assertRaises(ValueError):
            db.update_inara_outbox([rows[0]['id']],commander_id=1,fid='F-A',expected_rows=rows)

    def test_retry_persists_and_blocks_new_rows_without_schema_change(self):
        from cmdrhelper.database import CMDRDatabase
        state,db=self.fixture();row=db.inara_pending(1)[0]
        with db._connect() as con:version=con.execute('PRAGMA user_version').fetchone()[0]
        db.update_inara_outbox(errors={row['id']:'Inara: http_error'},retry_seconds=7200,commander_id=1,fid='F-A',expected_rows=[row])
        db.apply_commander_journal_delta(1,'a.log',[{'event':'FSDJump','timestamp':'2026-10-18T01:00:00Z','StarSystem':'Synthetic New'}],200,enqueue_inara=True)
        self.assertEqual(CMDRDatabase(db.path).inara_pending(1),[])
        with db._connect() as con:
            self.assertEqual(con.execute('PRAGMA user_version').fetchone()[0],version)
            con.execute("UPDATE inara_outbox SET last_attempt_at='2000-01-01T00:00:00+00:00',last_error='legacy error'")
        self.assertEqual(len(db.inara_pending(1)),2)

    def test_privacy_and_approved_diagnostics(self):
        import logging
        from cmdrhelper.logging_config import PrivacyFormatter
        record=logging.LogRecord('cmdrhelper.state',logging.WARNING,'',0,'Inara upload rejected',(),None)
        record.diagnostic_fields={'http_status':429,'inara_retry_seconds':7200,'inara_error':'http_error',
            'api_key':'private-key','fid':'private-fid','body':'private-body'}
        rendered=PrivacyFormatter().format(record)
        for value in ('429','7200','http_error'):self.assertIn(value,rendered)
        self.assertNotIn('private-',rendered)
        record.diagnostic_fields={'inara_error':'private-token','inara_retry_seconds':'private-key'}
        self.assertNotIn('private-',PrivacyFormatter().format(record))
    def test_return_to_original_commander_while_request_is_running(self):
        state,db=self.fixture();calls=[]
        class Immediate:
            def __init__(self,target,**kw):self.target=target
            def start(self):self.target()
        def upload(*args):
            calls.append(1)
            self.switch(state,2);self.switch(state,1)
            state._upload_pending_to_inara()
            return [r['id'] for r in args[3]],{}
        with patch('cmdrhelper.state.threading.Thread',Immediate),patch('cmdrhelper.state.upload_batch',side_effect=upload):state._upload_pending_to_inara()
        self.assertEqual(len(calls),1)
        self.assertEqual(db.inara_pending(1),[])

    def test_repeated_rate_limits_keep_backoff_and_stop_at_eight(self):
        from cmdrhelper.inara_uploader import InaraUploadError
        state,db=self.fixture()
        class Immediate:
            def __init__(self,target,**kw):self.target=target
            def start(self):self.target()
        with patch('cmdrhelper.state.threading.Thread',Immediate),patch('cmdrhelper.state.upload_batch',side_effect=InaraUploadError('http_error',http_status=429,retry_seconds=1)) as upload:
            for attempt in range(1,9):
                state._upload_pending_to_inara()
                with db._connect() as con:
                    count,stamp,metadata=con.execute('SELECT retry_count,last_attempt_at,last_error FROM inara_outbox').fetchone()
                    self.assertEqual(count,attempt)
                    wait=(datetime.fromisoformat(json.loads(metadata)['inara_retry_not_before'])-datetime.fromisoformat(stamp)).total_seconds()
                    self.assertEqual(wait,min(3600,30*2**attempt))
                    con.execute("UPDATE inara_outbox SET last_attempt_at='2000-01-01T00:00:00+00:00',last_error='expired synthetic error'")
            state._upload_pending_to_inara()
            self.assertEqual(upload.call_count,8)

    def test_partial_acknowledgement_commits_by_id_and_keeps_offsets(self):
        state,db=self.fixture()
        db.apply_commander_journal_delta(1,'a.log',[{'event':'FSDJump','timestamp':'2026-10-18T02:00:00Z','StarSystem':'Synthetic Two'}],200,enqueue_inara=True)
        rows=db.inara_pending(1)
        sent,failed=upload_batch('synthetic','Same','F-A',rows,opener=lambda *a,**k:self.reply([
            {'eventCustomID':rows[1]['id'],'eventStatus':200},
            {'eventCustomID':rows[0]['id'],'eventStatus':400,'eventStatusText':'private-response-content'}]))
        db.update_inara_outbox(sent,failed,commander_id=1,fid='F-A',expected_rows=rows)
        with db._connect() as con:
            self.assertEqual(con.execute('SELECT status,retry_count FROM inara_outbox ORDER BY id').fetchall(),[('error',1),('sent',0)])
            self.assertEqual(con.execute('SELECT last_read_offset FROM journal_sessions').fetchone()[0],200)
            self.assertNotIn('private-response-content',str(con.execute('SELECT last_error FROM inara_outbox').fetchall()))

    def test_worker_rejects_mismatched_database_identity_before_request(self):
        state,db=self.fixture()
        with db._connect() as con:con.execute("UPDATE commanders SET fid='F-OTHER' WHERE id=1")
        class Immediate:
            def __init__(self,target,**kw):self.target=target
            def start(self):self.target()
        with patch('cmdrhelper.state.threading.Thread',Immediate),patch('cmdrhelper.state.upload_batch') as upload:
            state._upload_pending_to_inara();upload.assert_not_called()
        self.assertEqual(state.inara_upload_status,'error')
        with db._connect() as con:self.assertEqual(con.execute('SELECT status,retry_count FROM inara_outbox').fetchall(),[('pending',0)])
