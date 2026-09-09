"""Release orchestration simulations: all git writes stay in temporary repos.

Mock git intercepts every remote operation; mock gh never contacts GitHub.
"""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('publish_release', ROOT / 'tools/publish_release.py')
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
REAL_GIT = shutil.which('git')

MOCK = r'''#!/usr/bin/env python3
import hashlib,json,os,pathlib,subprocess,sys
args=sys.argv[1:]
p=pathlib.Path(os.environ['MOCK_STATE'])
s=json.loads(p.read_text())
tool=pathlib.Path(sys.argv[0]).name
s['events'].append([tool,*args])
def save(): p.write_text(json.dumps(s))
def done(data=None, code=0):
    save()
    if data is not None: print(json.dumps(data) if not isinstance(data,str) else data)
    sys.exit(code)
def real(*cmd):
    return subprocess.check_output([os.environ['REAL_GIT'],*cmd],text=True).strip()
def asset(path):
    b=pathlib.Path(path).read_bytes()
    s['asset_bytes']=b.hex()
    return {'name':pathlib.Path(path).name,'size':len(b),'state':'uploaded','digest':'sha256:'+hashlib.sha256(b).hexdigest()}
if tool=='git':
    if args[:2]==['ls-remote','--tags']:
        done((s['remote_tag']+'\trefs/tags/v3.2') if s.get('remote_tag') else '')
    push=args[2:] if args[:1]==['-c'] else args
    if push[:1]==['push']:
        if s.get('push_fail'): done(code=1)
        if 'refs/heads/main' in push[-1]: s['remote_commit']=push[-1].split(':')[0]
        else:
            if s.get('tag_push_fail'): done(code=1)
            s['remote_tag']=real('rev-parse','refs/tags/v3.2^{commit}')
        done()
    if args[:1]==['fetch']:
        subprocess.check_call([os.environ['REAL_GIT'],'tag','v3.2',s['remote_tag']])
        done()
    save()
    os.execv(os.environ['REAL_GIT'],[os.environ['REAL_GIT'],*args])
if args[:2]==['auth','status']: done(code=1 if s.get('auth_fail') else 0)
if args[:2]==['repo','view']:
    done({'nameWithOwner':s.get('repo','Faber38/CMDRHelper'),'viewerPermission':'ADMIN','isArchived':False})
if args[:1]==['api']:
    if s.get('api_fail'): done({'status':'403'},1)
    done([s['release']] if s.get('release') else [])
if args[:2]==['release','create']:
    if s.get('create_fail'): done(code=1)
    if s.get('release'): done(code=1)
    s['notes']=pathlib.Path(args[args.index('--notes-file')+1]).read_text()
    s['release']={'tag_name':args[2],'name':'CMDRHelper '+args[2],'draft':False,'prerelease':False,'assets':[]}
    if s.get('upload_fail'):
        s['release']['draft']=True
        done(code=1)
    s['release']['assets']=[asset(args[3])]
    if s.get('wrong_uploaded_size'): s['release']['assets'][0]['size']+=1
    done()
if args[:2]==['release','upload']:
    if s.get('upload_fail'): done(code=1)
    s['release']['assets']=[asset(args[3])]
    done()
if args[:2]==['release','download']:
    d=pathlib.Path(args[args.index('--dir')+1])
    (d/'CMDRHelper_v3.2.zip').write_bytes(bytes.fromhex(s['asset_bytes']))
    done()
if args[:2]==['release','edit']:
    s['release']['draft']=False
    done()
done(code=99)
'''

BUILDER = r'''#!/usr/bin/env bash
set -euo pipefail
python3 - <<'BUILD'
import json,os,pathlib,zipfile
p=pathlib.Path(os.environ['MOCK_STATE']); s=json.loads(p.read_text())
s['events'].append(['build']); p.write_text(json.dumps(s))
if s.get('build_fail'): raise SystemExit(1)
d=pathlib.Path('release/CMDRHelper_v3.2'); d.mkdir(parents=True)
for name in ['main.py','cmdrhelper/version.py']:
    target=d/name; target.parent.mkdir(parents=True,exist_ok=True)
    target.write_bytes(pathlib.Path(name).read_bytes())
if pathlib.Path('cmdrhelper/ignored.py').exists(): raise SystemExit(9)
if not s.get('missing_zip'):
    with zipfile.ZipFile(str(d)+'.zip','w') as z:
        for f in d.rglob('*'):
            if f.is_file(): z.write(f,f.relative_to(d.parent))
if s.get('mutate_source'):
    pathlib.Path(os.environ['TEST_ROOT'],'main.py').write_text('concurrent change')
BUILD
'''


@unittest.skipUnless(REAL_GIT and shutil.which('zip') and shutil.which('unzip'), 'requires git and zip tools')
class PublishTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.root = self.base / 'repo'
        self.root.mkdir()
        self.state_path = self.base / 'state.json'
        self.state_path.write_text(json.dumps({'events': []}))
        self.env = dict(os.environ, MOCK_STATE=str(self.state_path), REAL_GIT=REAL_GIT, TEST_ROOT=str(self.root),
                        GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM='1', GIT_TERMINAL_PROMPT='0')
        # No inherited injected Git configuration/credentials in fixture commands.
        for key in list(self.env):
            if key.startswith('GIT_CONFIG_KEY_') or key.startswith('GIT_CONFIG_VALUE_') or key in ('GIT_CONFIG_COUNT','GIT_DIR','GIT_WORK_TREE','GIT_INDEX_FILE'):
                self.env.pop(key)
        self.git('init', '-b', 'main')
        self.git('config', 'user.email', 'fixture@example.invalid')
        self.git('config', 'user.name', 'Fixture')
        self.git('remote', 'add', 'origin', 'https://github.com/Faber38/CMDRHelper.git')
        self.write('github.sh', (ROOT / 'github.sh').read_text())
        self.write('tools/publish_release.py', (ROOT / 'tools/publish_release.py').read_text())
        self.write('create_release.sh', BUILDER)
        self.write('.gitignore', '/release/CMDRHelper_v*/\n*.zip\ncmdrhelper/ignored.py\n')
        self.write('main.py', '# committed source\n')
        self.write('cmdrhelper/version.py', '__version__ = "3.2"\n')
        self.write('cmdrhelper/__init__.py', (ROOT / 'cmdrhelper/__init__.py').read_text())
        self.write('cmdrhelper/release_summaries.py', (ROOT / 'cmdrhelper/release_summaries.py').read_text())
        for lang in 'de en fr it no sv fi pl nl es tr el'.split():
            self.write(f'cmdrhelper/i18n/{lang}.py', (ROOT / f'cmdrhelper/i18n/{lang}.py').read_text())
        self.git('add', '.')
        self.git('commit', '-m', 'fixture')
        self.head = self.git('rev-parse', 'HEAD')
        bin_dir = self.base / 'bin'
        bin_dir.mkdir()
        for tool in ('git', 'gh'):
            path = bin_dir / tool
            path.write_text(MOCK)
            path.chmod(0o755)
        self.env['PATH'] = str(bin_dir) + os.pathsep + self.env['PATH']

    def git(self, *args):
        return subprocess.check_output([REAL_GIT, *args], cwd=self.root, env=self.env, text=True, stderr=subprocess.DEVNULL).strip()

    def write(self, name, content):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
        return path

    def state(self, **updates):
        state = json.loads(self.state_path.read_text())
        state.update(updates)
        self.state_path.write_text(json.dumps(state))
        return state

    def publish(self, success=True):
        result = subprocess.run(['bash','github.sh'], cwd=self.root, env=self.env, input='ja\nfinal fixture\n',
                                text=True,capture_output=True,timeout=30)
        self.assertEqual(result.returncode == 0, success, result.stdout + result.stderr)
        return result

    def mutations(self):
        return [e for e in self.state()['events'] if e[0] == 'git' and ('push' in e or 'tag' in e or 'commit' in e)
                or e[:2] == ['gh','release'] and e[2] in ('create','upload','edit')]

    def existing_release(self, **kwargs):
        release = {'tag_name':'v3.2','name':'CMDRHelper v3.2','draft':False,'prerelease':False,'assets':[]}
        release.update(kwargs)
        self.state(remote_tag=self.head, release=release)

    def test_normal_build_before_push_correct_zip_notes_and_final_verification(self):
        result = self.publish()
        state = self.state()
        events = state['events']
        build = events.index(['build'])
        pushes = [i for i,e in enumerate(events) if e[0]=='git' and 'push' in e]
        self.assertTrue(all(i > build for i in pushes))
        create = next(e for e in events if e[:3] == ['gh','release','create'])
        self.assertIn('--verify-tag', create)
        self.assertEqual(create[create.index('--repo')+1], 'Faber38/CMDRHelper')
        self.assertEqual(Path(create[4]).name, 'CMDRHelper_v3.2.zip')
        self.assertIn('erfolgreich veröffentlicht', result.stdout)
        self.assertEqual(state['release']['assets'][0]['size'], (self.root/'release/CMDRHelper_v3.2.zip').stat().st_size)
        self.assertEqual(len([l for l in state['notes'].splitlines() if l.startswith('- ')]), 6)
        self.assertIn('Erweiterte Materialverwaltung',state['notes'])
        self.assertIn('cmdrhelper-update-summary',state['notes'])

    def test_build_failure_and_missing_zip_do_not_push_or_tag(self):
        for failure in ('build_fail','missing_zip'):
            with self.subTest(failure=failure):
                self.state(events=[], build_fail=failure=='build_fail', missing_zip=failure=='missing_zip')
                self.publish(False)
                self.assertEqual(self.mutations(),[])

    def test_push_failure_does_not_create_tag_or_release(self):
        self.state(push_fail=True)
        self.publish(False)
        self.assertEqual(self.git('tag','--list'), '')
        self.assertIsNone(self.state().get('release'))

    def test_local_tag_resume(self):
        self.git('tag','-a','v3.2','-m','fixture')
        self.publish()
        self.assertFalse(any(e[:2]==['git','tag'] for e in self.state()['events']))

    def test_remote_tag_resume_fetches_existing_tag(self):
        self.state(remote_tag=self.head)
        self.publish()
        self.assertTrue(any(e[:2]==['git','fetch'] for e in self.state()['events']))
        self.assertFalse(any(e[0]=='git' and 'push' in e and 'refs/tags/' in e[-1] for e in self.state()['events']))

    def test_wrong_remote_tag_aborts_before_any_mutation(self):
        self.state(remote_tag='0'*40)
        self.publish(False)
        self.assertEqual(self.mutations(),[])

    def test_wrong_local_tag_aborts_before_any_mutation(self):
        self.git('tag','v3.2')
        self.write('main.py','# newer\n')
        self.git('add','main.py'); self.git('commit','-m','newer')
        self.publish(False)
        self.assertEqual(self.mutations(),[])

    def test_existing_release_missing_asset_uploads_without_create(self):
        self.existing_release()
        self.publish()
        self.assertTrue(any(e[:3]==['gh','release','upload'] for e in self.state()['events']))
        self.assertFalse(any(e[:3]==['gh','release','create'] for e in self.state()['events']))

    def test_repeat_success_reuses_identical_asset_without_commit_or_upload(self):
        self.publish()
        digest=hashlib.sha256((self.root/'release/CMDRHelper_v3.2.zip').read_bytes()).hexdigest()
        self.state(events=[])
        self.publish()
        self.assertEqual(hashlib.sha256((self.root/'release/CMDRHelper_v3.2.zip').read_bytes()).hexdigest(), digest)
        self.assertFalse(any(e[:3] in (['gh','release','create'],['gh','release','upload']) or e[:2]==['git','commit'] for e in self.state()['events']))
        self.assertEqual(self.git('status','--porcelain'), '')

    def test_upload_failure_then_retry_completes_draft(self):
        self.state(upload_fail=True)
        self.publish(False)
        self.assertTrue(self.state()['release']['draft'])
        self.state(upload_fail=False, events=[])
        self.publish()
        self.assertFalse(self.state()['release']['draft'])
        self.assertTrue(any(e[:3]==['gh','release','upload'] for e in self.state()['events']))

    def test_tag_push_failure_then_retry(self):
        self.state(tag_push_fail=True)
        self.publish(False)
        self.assertEqual(self.git('tag','--list'), 'v3.2')
        self.state(tag_push_fail=False, events=[])
        self.publish()

    def test_create_failure_then_retry(self):
        self.state(create_fail=True)
        self.publish(False)
        self.state(create_fail=False)
        self.publish()

    def test_asset_size_mismatch_fails_remote_verification(self):
        self.state(wrong_uploaded_size=True)
        result=self.publish(False)
        self.assertNotIn('erfolgreich veröffentlicht',result.stdout)

    def test_existing_asset_wrong_digest_not_overwritten(self):
        self.publish()
        state=self.state(); state['release']['assets'][0]['digest']='sha256:wrong'
        self.state(release=state['release'],events=[])
        self.publish(False)
        self.assertEqual(self.mutations(),[])

    def test_asset_without_api_digest_is_downloaded_and_checked(self):
        self.publish()
        state=self.state(); state['release']['assets'][0].pop('digest')
        self.state(release=state['release'],events=[])
        self.publish()
        self.assertTrue(any(e[:3]==['gh','release','download'] for e in self.state()['events']))

    def test_wrong_release_tag_or_title_aborts(self):
        self.existing_release(name='Wrong release title')
        self.publish(False)
        self.assertEqual(self.mutations(),[])

    def test_preflight_auth_repo_branch_and_api_failures(self):
        for key,value in [('auth_fail',True),('repo','wrong/repo'),('api_fail',True)]:
            self.state(**{key:value},events=[])
            self.publish(False)
            self.assertEqual(self.mutations(),[])
            self.state(**{key: False if key!='repo' else 'Faber38/CMDRHelper'})
        self.git('checkout','-b','other')
        self.publish(False)
        self.assertEqual(self.mutations(),[])

    def test_generated_release_not_committed_and_ignored_source_not_built(self):
        self.write('release/CMDRHelper_v3.2/old.txt','old generated output')
        self.write('cmdrhelper/ignored.py','local ignored contamination')
        self.write('main.py','# final source\n')
        self.publish()
        self.assertEqual(self.git('ls-files','release'), '')
        self.assertEqual(self.git('show','HEAD:main.py'),'# final source')
        with zipfile.ZipFile(self.root/'release/CMDRHelper_v3.2.zip') as archive:
            self.assertEqual(archive.read('CMDRHelper_v3.2/main.py'),b'# final source\n')

    def test_staged_historical_release_is_preserved_and_rejected(self):
        self.write('release/CMDRHelper_v2.0/old.txt','history')
        self.git('add','-f','release/CMDRHelper_v2.0/old.txt')
        before=self.git('diff','--cached')
        self.publish(False)
        self.assertEqual(self.git('diff','--cached'),before)
        self.assertEqual(self.mutations(),[])

    def test_source_change_during_build_prevents_push(self):
        self.state(mutate_source=True)
        self.publish(False)
        self.assertEqual(self.mutations(),[])

    def test_version_and_notes_share_application_sources(self):
        import cmdrhelper
        from cmdrhelper.version import __version__
        self.assertEqual(cmdrhelper.__version__,__version__)
        self.assertEqual(MODULE.version_at(ROOT),__version__)
        from cmdrhelper.i18n import tr_for_language
        from cmdrhelper.release_summaries import RELEASE_SUMMARIES
        notes=MODULE.release_notes(ROOT,'3.2')
        for key in RELEASE_SUMMARIES['3.2']:
            self.assertIn('- '+tr_for_language('de',key),notes)
        self.assertIn('Weitere Verbesserungen',MODULE.release_notes(ROOT,'9.9'))

    def test_real_builder_on_committed_fixture_and_repeat(self):
        # Run the real builder only in the helper's temporary commit export.
        from test_release_packaging import REQUIRED
        self.write('create_release.sh', (ROOT / 'create_release.sh').read_text())
        for name in REQUIRED:
            if not (self.root / name).exists():
                self.write(name, 'fixture\n')
        self.git('add', '.')
        self.git('commit', '-m', 'real builder fixture')
        self.publish()
        first = (self.root / 'release/CMDRHelper_v3.2.zip').read_bytes()
        self.publish()
        self.assertEqual(first, (self.root / 'release/CMDRHelper_v3.2.zip').read_bytes())
        self.assertFalse((self.root / 'release/CMDRHelper_v3.2/tools').exists())

    def test_decline_performs_no_mutations(self):
        result = subprocess.run(['bash','github.sh'], cwd=self.root, env=self.env,
                                input='nein\n', text=True, capture_output=True, timeout=30)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(self.mutations(), [])
        self.assertNotIn(['build'], self.state()['events'])

    def test_tagged_dirty_source_is_rejected_without_commit(self):
        self.git('tag', 'v3.2')
        self.write('main.py', 'changed after tag')
        self.publish(False)
        self.assertEqual(self.mutations(), [])

    def test_wrong_remote_url_aborts_without_mutations(self):
        self.git('remote', 'set-url', 'origin', 'https://github.com/other/repo.git')
        self.publish(False)
        self.assertEqual(self.mutations(), [])

    def test_readme_version_fixture_changes_when_central_version_changes(self):
        result = subprocess.check_output(
            ['python3', '-B', '-c', 'import cmdrhelper; print(cmdrhelper.__version__)'],
            cwd=self.root, env=self.env, text=True)
        self.assertEqual(result.strip(), '3.2')
