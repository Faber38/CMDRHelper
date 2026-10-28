"""Synthetic source/process bindings; all settings and image writes are temporary."""
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from PIL import Image
from PySide6.QtCore import QObject, Signal, QTimer, QSettings
from PySide6.QtWidgets import QApplication
from cmdrhelper.game_instances import GameInstance, ProcessSnapshot
from cmdrhelper.screenshot_sources import (source_key, configured_source, live_context,
    migrate_legacy, screenshot_dir)
from cmdrhelper.screenshot_paths import screenshot_capture_time
from cmdrhelper.ui.screenshot_view import ScreenshotView, _ConvertWorker
from cmdrhelper.favorites import latest_screenshot
from cmdrhelper.i18n import _TRANSLATIONS, set_language, tr
from cmdrhelper.ui.styles import DARK_STYLESHEET, LIGHT_STYLESHEET


class Manager(QObject):
    changed = Signal()
    def __init__(self):
        super().__init__()
        self.timer = QTimer(self)
        self.runtimes = {}


class State(QObject):
    viewedCommanderChanged = Signal(object)


class SourcesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.settings = QSettings(str(self.root/'settings.ini'), QSettings.IniFormat)
        self.manager = Manager()
        self.state = State()
        self.state.settings = self.settings
        self.state.sources = self.manager
        self.state.viewed_commander_id = 2  # deliberately different from live
        self.state.commander_fid = 'FB'
        self.state.commander = 'TEST_BETA'
        self.state.system = 'WRONG VIEW SYSTEM'
        self.commanders = [dict(id=1, fid='FA', current_name='TEST_ALPHA'),
                           dict(id=2, fid='FB', current_name='TEST_BETA')]
        self.state.database = SimpleNamespace(list_commanders=lambda: self.commanders)
        self.data = {}
        self.paths = {}
        for sid, cid, fid, name, prefix in (
                ('steam', 1, 'FA', 'TEST_ALPHA', '.steam/steam/steamapps/compatdata/359320/pfx'),
                ('heroic', 2, 'FB', 'TEST_BETA', 'Games/Heroic/Prefixes/default/custom/pfx')):
            folder = self.root/prefix/'drive_c/users/custom-user/Saved Games/Frontier Developments/Elite Dangerous'
            folder.mkdir(parents=True)
            journal = folder/'Journal.test.log'
            journal.write_text('synthetic')
            row = dict(journal_file=str(journal), commander_id=cid, fid_seen=fid,
                       attribution_status='identified', first_event_at='2020-01-01T00:00:00Z')
            source = SimpleNamespace(id=sid, path=str(folder), enabled=True, status='ready', identities=[(fid, name)])
            self.data[sid] = dict(commander_fid=fid, commander_identity_name=name,
                                 system='HIP 60989' if sid == 'heroic' else 'Sol',
                                 last_timestamp='2020-01-01T00:00:00Z', latest_journal_session=row)
            processor = SimpleNamespace(sessions=[row], projection_for=lambda rows, sid=sid: self.data[sid])
            self.manager.runtimes[sid] = SimpleNamespace(source=source, processor=processor)
            self.paths[sid] = screenshot_dir(folder)
            self.paths[sid].mkdir(parents=True)
        self.live = 'steam'
        self.process = patch('cmdrhelper.screenshot_sources.inspect_instances', self.snapshot)
        self.process.start()
        self.addCleanup(self.process.stop)
        self.settings.setValue('screenshots/target_dir', str(self.root/'target'))
        self.settings.setValue('screenshots/auto', True)
        self.view = ScreenshotView(self.state)
        self.workers = []
        self.view.pool = SimpleNamespace(start=self.workers.append)
        self.addCleanup(self.close_view)

    def close_view(self):
        self.view.close()
        self.view.deleteLater()

    def snapshot(self):
        sids = list(self.manager.runtimes) if self.live == 'both' else [self.live] if self.live else []
        return ProcessSnapshot(True, [GameInstance(i+1, 0, journals=(self.data[sid]['latest_journal_session']['journal_file'],))
                                      for i, sid in enumerate(sids)])

    def switch(self, sid):
        self.live = sid
        self.manager.changed.emit()

    def bmp(self, sid='steam', name='Screenshot_0001.bmp'):
        path = self.paths[sid]/name
        Image.new('RGB', (5, 5), 'red').save(path, 'BMP')
        return path

    def scan_twice(self):
        self.view._scan(); self.view._scan()

    def test_live_source_overrides_view_and_switches_both_directions(self):
        timer = self.view.timer
        for sid, fid in [('steam','FA'), ('heroic','FB'), ('steam','FA')]:
            self.switch(sid)
            self.assertEqual(self.view._source(), self.paths[sid])
            self.assertEqual(self.view._source_fid, fid)
            self.assertIs(self.view.timer, timer)
            self.assertTrue(timer.isActive())
        self.state.viewedCommanderChanged.emit(2)
        path = self.bmp()
        self.scan_twice()
        worker = self.workers[-1]
        self.assertEqual(worker.source, path)
        self.assertEqual(worker.target.parent.name, 'TEST_ALPHA_FA')
        self.assertTrue(worker.target.name.startswith('Sol_TEST_ALPHA_'))
        self.assertNotIn('WRONG', worker.target.name)

    def test_manual_paths_restart_and_missing_folder(self):
        manual = self.root/'manual'
        manual.mkdir()
        self.view.source_edit.setText(str(manual)); self.view._path_edited()
        self.assertEqual(configured_source(self.settings, 'FA'), str(manual))
        self.switch('heroic')
        self.assertEqual(self.view._source(), self.paths['heroic'])
        self.switch('steam')
        self.assertEqual(self.view._source(), manual)
        self.view.close(); self.view.deleteLater()
        self.view = ScreenshotView(self.state)
        self.assertEqual(self.view._source(), manual)
        missing = self.root/'not-created'
        self.view.source_edit.setText(str(missing)); self.view._path_edited()
        self.assertFalse(missing.exists())
        self.assertFalse(self.view.timer.isActive())
        missing.mkdir()
        self.manager.timer.timeout.emit()
        self.assertTrue(self.view.timer.isActive())

    def test_folder_dialog_preserves_original_fid_during_switch(self):
        manual = self.root/'chosen-for-steam'
        manual.mkdir()
        def choose(*args):
            self.switch('heroic')
            return str(manual)
        with patch('cmdrhelper.ui.screenshot_view.QFileDialog.getExistingDirectory', side_effect=choose):
            self.view._choose_source()
        self.assertEqual(configured_source(self.settings, 'FA'), str(manual))
        self.assertEqual(configured_source(self.settings, 'FB'), '')
        self.assertEqual(self.view._source(), self.paths['heroic'])
        self.switch('steam')
        self.assertEqual(self.view._source(), manual)

    def test_ambiguous_process_or_projection_suspends(self):
        for sid in ('both', None):
            self.switch(sid)
            self.assertIsNone(self.view._context)
            self.assertFalse(self.view.timer.isActive())
            self.assertFalse(self.view.convert_button.isEnabled())
        self.switch('steam')
        self.data['steam']['commander_fid'] = 'FB'
        self.manager.changed.emit()
        self.assertIsNone(self.view._context)
        self.bmp(); self.scan_twice()
        self.assertEqual(self.workers, [])

    def test_switch_before_queue_discards_observation_and_baselines_on_return(self):
        first = self.bmp()
        self.view._scan()
        self.assertTrue(self.view._pending)
        self.switch('heroic')
        self.assertFalse(self.view._pending)
        second = self.bmp('heroic')
        self.scan_twice()
        self.assertEqual([w.source for w in self.workers], [second])
        self.switch('steam'); self.scan_twice()
        self.assertEqual(len(self.workers), 1)
        self.assertTrue(first.exists())

    def test_queue_freezes_identity_no_duplicates_and_collision(self):
        a = self.bmp(name='Screenshot_2026-10-26_19-35-42.bmp')
        self.scan_twice()
        first = self.workers[0]
        self.view._queue(a)
        self.assertEqual(len(self.workers), 1)
        self.switch('heroic')
        self.assertEqual(first.target.name, 'Sol_TEST_ALPHA_2026-10-26_19-35-42.png')
        first.run()
        self.assertTrue(first.target.exists())
        self.switch('steam')
        self.view._queue(a)
        self.assertEqual(len(self.workers), 1)
        b = self.bmp(name='HighResScreenshot_2026-10-26_19-35-42.bmp')
        self.scan_twice()
        self.assertEqual(self.workers[-1].source, b)
        self.assertEqual(self.workers[-1].target.name, 'Sol_TEST_ALPHA_2026-10-26_19-35-42_2.png')

    def test_names_timestamp_jpg_and_neutral_system(self):
        self.switch('heroic')
        self.view.format_combo.setCurrentText('JPG')
        path = self.bmp('heroic', 'Screenshot_2026-10-26_19-35-42.bmp')
        os.utime(path, (1, 1))
        self.scan_twice()
        self.assertEqual(self.workers[-1].target.name, 'HIP_60989_TEST_BETA_2026-10-26_19-35-42.jpg')
        self.data['heroic']['system'] = ''
        self.data['heroic']['commander_identity_name'] = 'A/B:*?'
        path = self.bmp('heroic', 'Screenshot_0002.bmp')
        self.scan_twice()
        self.assertTrue(self.workers[-1].target.name.startswith('UNKNOWN_SYSTEM_A-B_'))
        self.assertNotRegex(self.workers[-1].target.name, r'[<>:"/\\|?*]')
        self.assertEqual(screenshot_capture_time(path), path.stat().st_mtime)

    def test_migration_only_proved_owner_and_manual_priority(self):
        legacy = str(self.paths['heroic'])
        self.settings.setValue('screenshots/source_dir', legacy)
        migrate_legacy(self.settings, self.manager)
        self.assertEqual(configured_source(self.settings, 'FB'), legacy)
        self.assertEqual(configured_source(self.settings, 'FA'), '')
        self.settings.setValue(source_key('FB'), str(self.root/'manual'))
        migrate_legacy(self.settings, self.manager)
        self.assertEqual(configured_source(self.settings, 'FB'), str(self.root/'manual'))
        self.assertEqual(self.settings.value('screenshots/source_dir'), legacy)
        self.settings.remove(source_key('FB'))
        self.manager.runtimes['heroic'].source.identities.append(('FA', 'TEST_ALPHA'))
        migrate_legacy(self.settings, self.manager)
        self.assertEqual(configured_source(self.settings, 'FB'), '')
        self.settings.setValue('screenshots/source_dir', str(self.root/'unrelated'))
        migrate_legacy(self.settings, self.manager)
        self.assertEqual(configured_source(self.settings, 'FA'), '')

    def test_conflicting_manual_source_is_not_converted(self):
        self.view.source_edit.setText(str(self.paths['heroic']))
        self.view._path_edited()
        self.assertFalse(self.view.timer.isActive())
        self.assertIsNone(self.view._context)

    def test_gallery_root_and_favorites_new_and_old_names(self):
        self.settings.setValue(source_key('FA'), str(self.paths['steam']))
        a = self.bmp(name='Screenshot_2026-10-26_19-35-42.bmp')
        self.view.delete_check.setChecked(True)
        self.scan_twice(); worker = self.workers[0]; worker.run()
        self.assertFalse(a.exists())
        self.assertEqual(latest_screenshot(self.settings, commander_fid='FA', commander_name='TEST_ALPHA'), worker.target)
        self.assertIsNone(latest_screenshot(self.settings, commander_fid='FB', commander_name='TEST_BETA'))
        self.state.viewed_commander_id = 1
        self.assertEqual(self.view._gallery_directories(), [worker.target.parent])
        self.view.gallery_filter.setCurrentIndex(self.view.gallery_filter.findData('all'))
        self.assertEqual(self.view._gallery_directories(), [worker.target.parent])
        self.view.gallery_filter.setCurrentIndex(self.view.gallery_filter.findData('unassigned'))
        self.assertEqual(self.view._gallery_directories(), [self.root/'target'])
        old = worker.target.parent/'2026-10-27_19-35-42_TEST_ALPHA_Sol.png'
        Image.new('RGB', (4, 4)).save(old)
        self.assertEqual(latest_screenshot(self.settings, commander_fid='FA', commander_name='TEST_ALPHA'), old)

    def test_worker_failure_never_deletes_or_overwrites(self):
        source = self.bmp()
        target = self.root/'result.png'
        results = []
        worker = _ConvertWorker(source, target, 'PNG', True)
        worker.signals.finished.connect(lambda *args: results.append(args[2]))
        with patch.object(Image.Image, 'save', side_effect=OSError('disk full')):
            worker.run()
        self.assertTrue(source.exists())
        self.assertEqual(results, [False])
        target.write_bytes(b'existing')
        worker.run()
        self.assertEqual(target.read_bytes(), b'existing')
        self.assertTrue(source.exists())

    def test_changed_source_after_queue_is_preserved(self):
        source = self.bmp()
        self.view.delete_check.setChecked(True)
        self.scan_twice()
        worker = self.workers[0]
        Image.new('RGB', (9, 9), 'blue').save(source, 'BMP')
        self.switch('heroic')
        worker.run()
        self.assertTrue(source.exists())
        self.assertFalse(worker.target.exists())

    def test_transient_projection_pause_does_not_lose_new_bmp(self):
        processor = self.manager.runtimes['steam'].processor
        previous = processor.projection_for
        processor.projection_for = lambda rows: None
        self.manager.changed.emit()
        self.assertFalse(self.view.timer.isActive())
        self.assertEqual(self.view._source(), self.paths['steam'])
        source = self.bmp()
        processor.projection_for = previous
        self.manager.changed.emit()
        self.scan_twice()
        self.assertEqual([w.source for w in self.workers], [source])
        self.assertEqual(self.workers[0].target.parent.name, 'TEST_ALPHA_FA')

    def test_capture_before_session_rejected_and_later_system_not_invented(self):
        self.bmp(name='Screenshot_2019-01-01_00-00-00.bmp')
        self.scan_twice()
        self.assertEqual(self.workers, [])
        self.data['steam']['last_timestamp'] = '2026-10-27T00:00:00Z'
        self.bmp(name='Screenshot_2026-10-26_19-35-42.bmp')
        self.scan_twice()
        self.assertTrue(self.workers[-1].target.name.startswith('UNKNOWN_SYSTEM_TEST_ALPHA_'))

    def test_historical_manual_conversion_uses_neutral_system(self):
        self.bmp(name='Screenshot_2026-10-26_19-35-42.bmp')
        self.view._baseline()
        self.view._convert_existing()
        self.assertTrue(self.workers[-1].target.name.startswith('UNKNOWN_SYSTEM_TEST_ALPHA_'))

    def test_settings_options_preserved_and_source_fids_do_not_collide(self):
        self.settings.setValue('screenshots/brightness', 32)
        self.settings.setValue('screenshots/delete_bmp', True)
        self.view._load_settings()
        self.view._binding = None
        self.view._sync_source()
        self.assertEqual(self.view.brightness_slider.value(), 32)
        self.assertTrue(self.view.delete_check.isChecked())
        self.assertNotEqual(source_key('A/B'), source_key('A-B'))
        self.assertNotEqual(source_key('A/B'), source_key('A%2FB'))

    def test_dark_light_and_twelve_languages(self):
        self.switch(None)
        for style in (DARK_STYLESHEET, LIGHT_STYLESHEET):
            self.view.setStyleSheet(style)
            for language in _TRANSLATIONS:
                set_language(language)
                self.view._sync_source()
                self.assertEqual(self.view.status.text(), tr('images.identity_wait'))
                self.assertNotEqual(self.view.status.text(), 'images.identity_wait')
                self.assertIn('images.identity_wait', _TRANSLATIONS[language])
        set_language('de')


class FavoriteSourceOwnershipTests(unittest.TestCase):
    """Originals need an unambiguous source; private conversions retain ownership."""

    def setUp(self):
        temporary = TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.settings = QSettings(str(self.root / 'settings.ini'), QSettings.IniFormat)
        self.manager = SimpleNamespace(runtimes={})

    def source(self, key, fid, *, enabled=True):
        journal = self.root / key / 'drive_c/users/test-user/Saved Games/Frontier Developments/Elite Dangerous'
        source = SimpleNamespace(id=key, path=str(journal), enabled=enabled,
                                 identities=[(fid, 'TEST_COMMANDER')])
        self.manager.runtimes[key] = SimpleNamespace(
            source=source, processor=SimpleNamespace(sessions=[]))
        folder = screenshot_dir(journal)
        folder.mkdir(parents=True)
        return folder

    def image(self, folder, name='Screenshot_0001.bmp'):
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / name
        Image.new('RGB', (3, 3)).save(path)
        return path

    def latest(self, fid, *, manager=True):
        return latest_screenshot(self.settings, commander_fid=fid,
                                 commander_name='TEST_COMMANDER',
                                 sources=self.manager if manager else None)

    def test_shared_manual_folder_rejected_with_and_without_manager(self):
        folder = self.root / 'shared'
        self.image(folder)
        self.settings.setValue(source_key('FA'), str(folder))
        self.settings.setValue(source_key('FB'), str(folder / '..' / 'shared'))
        for manager in (True, False):
            for fid in ('FA', 'FB'):
                with self.subTest(manager=manager, fid=fid):
                    self.assertIsNone(self.latest(fid, manager=manager))

    def test_unique_manual_folder_works_without_manager(self):
        own = self.image(self.root / 'own')
        self.settings.setValue(source_key('FA'), str(own.parent))
        self.assertEqual(self.latest('FA', manager=False), own)

    def test_distinct_steam_heroic_journals_use_fid_not_commander_name(self):
        steam = self.image(self.source('steam', 'FA'))
        heroic = self.image(self.source('heroic', 'FB'))
        self.assertEqual(self.latest('FA'), steam)
        self.assertEqual(self.latest('FB'), heroic)

    def test_manual_source_cannot_override_other_journal_owner(self):
        self.source('steam', 'FA')
        foreign = self.image(self.source('heroic', 'FB', enabled=False))
        self.settings.setValue(source_key('FA'), str(foreign.parent))
        self.assertIsNone(self.latest('FA'))

    def test_shared_journal_identity_is_ambiguous_even_with_manual_mapping(self):
        folder = self.source('steam', 'FA')
        self.image(folder)
        self.manager.runtimes['steam'].source.identities.append(('FB', 'TEST_OTHER'))
        self.assertIsNone(self.latest('FA'))
        self.settings.setValue(source_key('FA'), str(folder))
        self.assertIsNone(self.latest('FA'))

    def test_missing_fid_unassigned_legacy_and_multiple_sources_do_not_guess(self):
        foreign = self.image(self.source('heroic', 'FB'))
        self.settings.setValue('screenshots/source_dir', str(foreign.parent))
        self.assertIsNone(self.latest(''))
        self.assertIsNone(self.latest('FA'))
        first = self.image(self.source('steam', 'FA'))
        self.image(self.source('another-steam', 'FA'))
        self.assertIsNone(self.latest('FA'))
        self.settings.setValue(source_key('FA'), str(first.parent))
        self.assertEqual(self.latest('FA'), first)

    def test_conflicting_original_does_not_hide_owned_old_or_new_conversions(self):
        shared = self.root / 'shared'
        self.image(shared, 'Screenshot_2030-01-01_12-00-00.bmp')
        for fid in ('FA', 'FB'):
            self.settings.setValue(source_key(fid), str(shared))
        target = self.root / 'target'
        self.settings.setValue('screenshots/target_dir', str(target))
        foreign = self.image(target / 'TEST_COMMANDER_FB',
                             'Sol_TEST_COMMANDER_2029-01-01_12-00-00.png')
        for name in ('2026-01-01_12-00-00_TEST_COMMANDER_Sol.png',
                     'Sol_TEST_COMMANDER_2026-01-01_12-00-00.png'):
            with self.subTest(name=name):
                own = self.image(target / 'TEST_COMMANDER_FA', name)
                before = {key: self.settings.value(key) for key in self.settings.allKeys()}
                self.assertEqual(self.latest('FA'), own)
                self.assertEqual(self.latest('FB'), foreign)
                self.assertEqual(before, {key: self.settings.value(key) for key in self.settings.allKeys()})
                own.unlink()
        self.assertIsNone(self.latest('FA'))


if __name__ == '__main__':
    unittest.main()
