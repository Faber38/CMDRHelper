"""Journal settings exercise only synthetic files and read-only session queries."""
import json
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from PySide6.QtCore import QObject, QSettings, QTimer, Signal, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QDialog, QScrollArea
from cmdrhelper.i18n import get_language, set_language, _TRANSLATIONS
from cmdrhelper.journal_sources import SourceRegistry
from cmdrhelper.ui.journal_sources import JournalSourcesPanel, SourceEditor, source_statistics
from cmdrhelper.journal_catchup import load_sessions
from cmdrhelper.ui.styles import DARK_STYLESHEET, LIGHT_STYLESHEET


class Manager(QObject):
    changed = Signal()

    def __init__(self, root):
        super().__init__()
        self.registry = SourceRegistry(QSettings(str(root/'settings.ini'), QSettings.IniFormat))
        self.db_path = root/'synthetic.db'
        with sqlite3.connect(self.db_path) as con:
            con.execute('CREATE TABLE journal_sessions (journal_file TEXT, last_read_offset INTEGER, last_complete_line_offset INTEGER, last_event_at TEXT)')
        self.state = SimpleNamespace(database=SimpleNamespace(path=self.db_path,
                                     _connect=lambda: sqlite3.connect(self.db_path)),
                                     commander_fid='UNCHANGED', viewed_commander_id=42)
        self.runtimes = {}
        self.request = Mock()
        self.rediscover = Mock()

    def reconcile(self):
        for runtime in self.runtimes.values():
            runtime.watcher.timer.stop()
        self.runtimes = {}
        for source in self.registry.enabled():
            timer = QTimer(self)
            timer.start(60000)
            self.runtimes[source.id] = SimpleNamespace(watcher=SimpleNamespace(timer=timer), transfer_error='')
        self.changed.emit()


class JournalSourcesUITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.manager = Manager(self.root)
        self.panel = JournalSourcesPanel(self.manager)
        self.addCleanup(self.panel.close)
        self.addCleanup(self.manager.deleteLater)
        language = get_language()
        self.addCleanup(set_language, language)
        set_language('en')
        self.panel.show()
        self.app.processEvents()

    def settle(self):
        # Deliver real filesystem notifications and their coalesced refresh.
        QTest.qWait(50)
        self.app.processEvents()

    def test_hidden_construction_and_changes_do_not_read_statistics(self):
        self.source('hidden')
        self.panel.hide()
        with patch('cmdrhelper.ui.journal_sources.load_sessions', wraps=load_sessions) as load, \
                patch('cmdrhelper.ui.journal_sources.source_statistics', wraps=source_statistics) as stats:
            panel = JournalSourcesPanel(self.manager)
            self.addCleanup(panel.close)
            self.manager.changed.emit()
            panel.refresh_visible()
            panel.selection_changed()
            load.assert_not_called()
            stats.assert_not_called()
            panel.show()
            self.assertEqual(stats.call_count, 1)
            self.assertEqual(panel.statistics['count'].text(), '1')

    def test_reopen_timer_and_status_changes_reuse_statistics(self):
        source = self.source('stable')
        self.settle()
        with patch('cmdrhelper.ui.journal_sources.load_sessions', wraps=load_sessions) as load, \
                patch('cmdrhelper.ui.journal_sources.source_statistics', wraps=source_statistics) as stats:
            for _ in range(5):
                self.panel.hide()
                self.manager.changed.emit()
                self.panel.show()
                self.panel.timer.timeout.emit()
            source.status = 'reading'
            self.manager.changed.emit()
            self.assertIn('reading', self.panel.items.currentItem().text().lower())
            # Commander identity is not part of source-local statistics.
            self.manager.state.commander_fid = 'OTHER'
            self.manager.state.viewed_commander_id = 99
            self.manager.changed.emit()
            load.assert_not_called()
            stats.assert_not_called()

    def test_source_switch_reuses_each_source_and_removal_discards_watch(self):
        first = self.source('first-cache')
        second = self.source('second-cache', 2)
        self.select(second)
        self.select(first)
        self.settle()
        with patch('cmdrhelper.ui.journal_sources.source_statistics', wraps=source_statistics) as stats:
            self.select(second)
            self.assertEqual(self.panel.statistics['count'].text(), '2')
            self.select(first)
            self.assertEqual(self.panel.statistics['count'].text(), '1')
            stats.assert_not_called()
        self.panel.remove()
        self.assertNotIn(first.id, self.panel._statistics_cache)
        self.assertEqual(self.panel.statistics['count'].text(), '2')

    def test_database_only_commit_invalidates_even_without_manager_signal(self):
        source = self.source('db-only')
        self.settle()
        with sqlite3.connect(self.manager.db_path) as con:
            con.execute("UPDATE journal_sessions SET last_event_at='2026-02-01T12:00:00Z'")
        with patch('cmdrhelper.ui.journal_sources.load_sessions', wraps=load_sessions) as load:
            self.panel.refresh_visible()
            self.assertEqual(load.call_count, 1)
            self.assertEqual(self.panel.statistics['last_read'].text(), '2026-02-01T12:00:00Z')
            self.panel.refresh_visible()
            self.assertEqual(load.call_count, 1)

    def test_wal_batch_commit_and_hidden_coalescing(self):
        self.source('wal')
        con = sqlite3.connect(self.manager.db_path)
        self.addCleanup(con.close)
        con.execute('PRAGMA journal_mode=WAL')
        self.panel.refresh_visible()
        self.settle()
        main_before = self.manager.db_path.read_bytes()
        self.panel.hide()
        with patch('cmdrhelper.ui.journal_sources.load_sessions', wraps=load_sessions) as load:
            for day in (2, 3):
                self.manager.changed.emit()  # Batch start.
                con.execute('UPDATE journal_sessions SET last_event_at=?',
                            (f'2026-02-0{day}T12:00:00Z',))
                con.commit()
                self.manager.changed.emit()  # Batch end.
            self.assertEqual(main_before, self.manager.db_path.read_bytes())
            self.panel.refresh_visible()
            load.assert_not_called()
            self.panel.show()
            self.assertEqual(load.call_count, 1)
            self.assertEqual(self.panel.statistics['last_read'].text(), '2026-02-03T12:00:00Z')
            self.panel.refresh_visible()
            self.assertEqual(load.call_count, 1)

    def test_files_created_modified_removed_while_hidden_and_disabled(self):
        source = self.source('file-changes', 2)
        self.manager.registry.update(source.id, enabled=False)
        self.manager.reconcile()
        self.settle()
        folder = Path(source.path)
        with patch('cmdrhelper.ui.journal_sources.source_statistics', wraps=source_statistics) as stats:
            self.panel.hide()
            new = folder/'Journal.2026-03-01T120000.01.log'
            new.write_text('{}\n')
            self.settle()
            stats.assert_not_called()
            self.panel.show()
            self.assertEqual(self.panel.statistics['count'].text(), '3')
            old = folder/'Journal.2026-01-01T120000.01.log'
            os.utime(old, (2000000000, 2000000000))
            self.settle()
            self.assertEqual(self.panel.statistics['newest_name'].text(), old.name)
            new.unlink()
            self.settle()
            self.assertEqual(self.panel.statistics['count'].text(), '2')
            self.assertGreaterEqual(stats.call_count, 3)

    def test_manual_read_forces_statistics_and_preserves_request(self):
        source = self.source('manual')
        self.settle()
        with patch('cmdrhelper.ui.journal_sources.source_statistics', wraps=source_statistics) as stats:
            self.panel.read_now()
            self.assertEqual(stats.call_count, 1)
        self.manager.request.assert_called_once_with(source.id)

    def test_failed_watch_or_database_read_is_not_cached(self):
        source = self.source('retry')
        self.settle()
        self.panel._discard_statistics(source.id)
        with patch('cmdrhelper.ui.journal_sources.QFileSystemWatcher.addPath', return_value=False), \
                patch('cmdrhelper.ui.journal_sources.source_statistics', wraps=source_statistics) as stats:
            self.panel.refresh_visible()
            self.panel.refresh_visible()
            self.assertEqual(stats.call_count, 2)
        self.panel._discard_statistics(source.id)
        with patch('cmdrhelper.ui.journal_sources.load_sessions', side_effect=sqlite3.OperationalError('busy')):
            self.panel.refresh_visible()
            self.assertEqual(self.panel.statistics['last_read'].text(), 'Error')
        self.panel.refresh_visible()
        self.assertEqual(self.panel.statistics['last_read'].text(), '2026-01-01T12:00:00Z')

    def test_unknown_database_path_or_partial_file_watch_never_validates_cache(self):
        source = self.source('uncertain')
        self.settle()
        del self.manager.state.database.path
        with patch('cmdrhelper.ui.journal_sources.source_statistics', wraps=source_statistics) as stats:
            self.panel.refresh_visible()
            self.panel.refresh_visible()
            self.assertEqual(stats.call_count, 2)
        self.manager.state.database.path = self.manager.db_path
        self.panel._discard_statistics(source.id)
        file = str(next(Path(source.path).glob('Journal.*.log')))
        with patch('cmdrhelper.ui.journal_sources.QFileSystemWatcher.addPaths', return_value=[file]), \
                patch('cmdrhelper.ui.journal_sources.source_statistics', wraps=source_statistics) as stats:
            self.panel.refresh_visible()
            self.panel.refresh_visible()
            self.assertEqual(stats.call_count, 2)

    def test_commit_during_statistics_read_requires_another_refresh(self):
        source = self.source('concurrent')
        self.settle()
        self.panel._discard_statistics(source.id)
        def changed_during_read(source, sessions):
            data = source_statistics(source, sessions)
            with sqlite3.connect(self.manager.db_path) as con:
                con.execute("UPDATE journal_sessions SET last_event_at='2026-04-01T12:00:00Z'")
            return data
        with patch('cmdrhelper.ui.journal_sources.source_statistics', side_effect=changed_during_read):
            self.panel.refresh_visible()
        with patch('cmdrhelper.ui.journal_sources.load_sessions', wraps=load_sessions) as load:
            self.panel.refresh_visible()
            self.assertEqual(load.call_count, 1)
            self.assertEqual(self.panel.statistics['last_read'].text(), '2026-04-01T12:00:00Z')

    def source(self, name, events=1, identities=()):
        folder = self.root/name
        folder.mkdir(parents=True)
        source = self.manager.registry.add(folder, name)
        source.identities = list(identities)
        for index in range(events):
            path = folder/f'Journal.2026-01-{index+1:02}T120000.01.log'
            data = (json.dumps(dict(timestamp=f'2026-01-{index+1:02}T12:00:00Z', event='Location'))+'\n').encode()
            path.write_bytes(data)
            os.utime(path, (1700000000+index*86400, 1700000000+index*86400))
            with sqlite3.connect(self.manager.db_path) as con:
                con.execute('INSERT INTO journal_sessions VALUES (?,?,?,?)',
                            (str(path),len(data),len(data),f'2026-01-{index+1:02}T12:00:00Z'))
        self.manager.reconcile()
        return source

    def select(self, source):
        for index in range(self.panel.items.count()):
            if self.panel.items.item(index).data(Qt.UserRole) == source.id:
                self.panel.items.setCurrentRow(index)
                return
        self.fail('source missing')

    def test_source_selection_isolated_statistics_and_no_writes(self):
        first = self.source('one', 1, [('F1','First'),('F2','Historical')])
        second = self.source('two', 2, [('F3','Second')])
        self.source('three', 3)
        before_db = self.manager.db_path.read_bytes()
        before_settings = self.manager.registry.settings.value('journal_sources/v1')
        before_files = {p: p.read_bytes() for p in self.root.rglob('*.log')}
        for source, count, timestamp in [(first,'1','2026-01-01T12:00:00Z'),(second,'2','2026-01-02T12:00:00Z')]:
            self.select(source)
            self.assertEqual(self.panel.path.text(), source.path)
            self.assertEqual(self.panel.statistics['count'].text(), count)
            self.assertEqual(self.panel.statistics['last_read'].text(), timestamp)
            self.assertEqual(self.panel.statistics['newest_name'].text(), f'Journal.{timestamp[:10]}T120000.01.log')
        self.select(first)
        self.assertIn('Historical (F2)', self.panel.items.currentItem().text())
        self.assertIn('First (F1)', self.panel.items.currentItem().text())
        self.assertEqual(self.manager.state.commander_fid, 'UNCHANGED')
        self.assertEqual(self.manager.state.viewed_commander_id,42)
        self.assertEqual(before_db,self.manager.db_path.read_bytes())
        self.assertEqual(before_settings,self.manager.registry.settings.value('journal_sources/v1'))
        self.assertEqual(before_files,{p:p.read_bytes() for p in before_files})
        self.manager.request.assert_not_called()

    def test_read_now_only_requests_selected_source_and_disabled_is_inert(self):
        self.source('one')
        second = self.source('two')
        self.select(second)
        self.panel.buttons['read'].click()
        self.manager.request.assert_called_once_with(second.id)
        self.panel.items.currentItem().setCheckState(
            Qt.Unchecked if self.panel.items.currentItem().checkState() == Qt.Checked else Qt.Checked)
        self.app.processEvents()
        self.assertFalse(self.panel.buttons['read'].isEnabled())
        self.assertEqual(self.panel.statistics['monitoring'].text(),'Monitoring inactive')
        self.panel.read_now()
        self.manager.request.assert_called_once()
        self.panel.items.currentItem().setCheckState(
            Qt.Unchecked if self.panel.items.currentItem().checkState() == Qt.Checked else Qt.Checked)
        self.app.processEvents()
        self.assertTrue(self.panel.buttons['read'].isEnabled())

    def test_add_edit_remove_and_search_use_existing_registry(self):
        self.source('one')
        folder = self.root/'added'; folder.mkdir()
        dialog = Mock()
        dialog.exec.return_value = QDialog.Accepted
        dialog.path.text.return_value = str(folder)
        dialog.name.text.return_value = 'Added'
        dialog.enabled.isChecked.return_value = True
        with patch('cmdrhelper.ui.journal_sources.SourceEditor',return_value=dialog):
            self.panel.add()
            selected = self.panel.selected_id()
            self.assertEqual(self.manager.registry.get(selected).path,str(folder))
            self.assertEqual(len(self.manager.registry.sources),2)
            dialog.name.text.return_value = 'Renamed'
            self.panel.edit()
        self.assertEqual(self.manager.registry.get(selected).name,'Renamed')
        journal = folder/'Journal.2026-01-01T120000.01.log'; journal.write_text('retained')
        before = self.manager.db_path.read_bytes()
        self.panel.remove()
        self.assertEqual(journal.read_text(),'retained')
        self.assertEqual(before,self.manager.db_path.read_bytes())
        self.assertEqual(len(self.manager.registry.sources),1)
        self.panel.buttons['search'].click()
        self.manager.rediscover.assert_called_once()

    def test_folder_picker_edits_dialog_only(self):
        source = self.source('one')
        editor = SourceEditor(self.panel,source)
        self.addCleanup(editor.close)
        with patch('cmdrhelper.ui.journal_sources.QFileDialog.getExistingDirectory',return_value=str(self.root/'other')):
            editor.browse()
        self.assertEqual(editor.path.text(),str(self.root/'other'))
        self.assertEqual(self.manager.registry.get(source.id).path,source.path)
        self.manager.request.assert_not_called()

    def test_empty_unknown_and_unreachable_sources(self):
        source = self.source('empty',0)
        self.assertEqual(self.panel.statistics['count'].text(),'0')
        self.assertEqual(self.panel.statistics['last_read'].text(),'–')
        self.assertIn('Commander identity not yet known',self.panel.items.currentItem().text())
        Path(source.path).rmdir()
        self.panel.selection_changed()
        self.assertEqual(self.panel.statistics['count'].text(),'–')
        self.assertEqual(self.panel.statistics['reachable'].text(),'Unreachable')
        self.panel.remove()
        self.assertEqual(self.panel.path.text(),'')
        self.assertFalse(self.panel.buttons['read'].isEnabled())

    def test_partial_processing_does_not_display_unread_timestamp(self):
        source = self.source('partial',0)
        path = Path(source.path)/'Journal.2026-01-01T120000.01.log'
        first = b'{"event":"Location","timestamp":"2026-01-01T12:00:00Z"}\n'
        second = b'{"event":"Location","timestamp":"2026-01-02T12:00:00Z"}\n'
        path.write_bytes(first+second+b'{"event":')
        row = dict(journal_file=str(path),last_read_offset=len(first),
                   last_complete_line_offset=len(first+second),last_event_at='2026-01-02T12:00:00Z')
        before = path.read_bytes()
        self.assertEqual(source_statistics(source,[row])['last_read'],'2026-01-01T12:00:00Z')
        self.assertEqual(path.read_bytes(),before)

    def test_long_windows_path_is_kept_in_full(self):
        source = self.source('windows-display', 0)
        source.path = 'C:\\Users\\' + ('Long Commander Directory\\' * 15) + 'Elite Dangerous'
        self.panel.refresh()
        self.assertEqual(self.panel.path.text(), source.path)
        self.assertEqual(self.panel.path.toolTip(), source.path)
        self.assertIn(source.path, self.panel.items.currentItem().toolTip())
        self.assertEqual(self.panel.statistics['reachable'].text(), 'Unreachable')

    def edit_source(self, source, *, name=None, path=None):
        self.select(source)
        dialog = Mock()
        dialog.exec.return_value = QDialog.Accepted
        dialog.path.text.return_value = path or source.path
        dialog.name.text.return_value = name or source.name
        dialog.enabled.isChecked.return_value = source.enabled
        with patch('cmdrhelper.ui.journal_sources.SourceEditor', return_value=dialog):
            self.panel.edit()

    def test_edit_automatic_and_manual_sources_preserves_id_and_history(self):
        for origin in ('automatic', 'manual'):
            source = self.source(origin)
            source.origin = origin
            before = self.manager.db_path.read_bytes()
            self.edit_source(source, name='Renamed '+origin)
            renamed = self.manager.registry.get(source.id)
            self.assertEqual(renamed.name, 'Renamed '+origin)
            self.assertEqual(renamed.origin, origin)
            destination = self.root/('new-'+origin); destination.mkdir()
            self.edit_source(renamed, path=str(destination))
            changed = self.manager.registry.get(source.id)
            self.assertEqual(changed.path, str(destination))
            self.assertEqual(changed.canonical_path, str(destination.resolve()))
            self.assertEqual(changed.identities, [])
            self.assertEqual(before, self.manager.db_path.read_bytes())
            self.assertTrue(list(Path(source.path).glob('Journal.*.log')))

    def test_invalid_duplicate_alias_and_busy_paths_are_rejected(self):
        first = self.source('first')
        other = self.source('other')
        alias = self.root/'alias'; alias.symlink_to(other.path, target_is_directory=True)
        before = self.manager.registry.settings.value('journal_sources/v1')
        with patch('cmdrhelper.ui.journal_sources.QMessageBox.warning') as warning:
            for path in (other.path, str(alias), str(self.root/'missing')):
                self.edit_source(first, path=path)
                self.assertEqual(before, self.manager.registry.settings.value('journal_sources/v1'))
            with patch('cmdrhelper.ui.journal_sources.os.access', return_value=False):
                self.edit_source(first, path=other.path)
            self.manager.running = True
            self.edit_source(first, path=other.path)
            self.assertEqual(warning.call_count, 5)
        self.assertEqual(before, self.manager.registry.settings.value('journal_sources/v1'))

    def test_checkboxes_persist_independently_and_rediscovery_keeps_disabled(self):
        first = self.source('first')
        second = self.source('second')
        before = self.manager.db_path.read_bytes()
        watcher = self.manager.runtimes[first.id].watcher
        self.select(first)
        self.panel.items.currentItem().setCheckState(Qt.Unchecked)
        self.assertFalse(self.manager.registry.get(first.id).enabled)
        self.assertFalse(watcher.timer.isActive())
        self.assertTrue(self.manager.registry.get(second.id).enabled)
        self.app.processEvents()
        restored = SourceRegistry(self.manager.registry.settings)
        restored.merge([(first.path, 'Discovered again'), (second.path, 'Again')])
        self.assertFalse(restored.get(first.id).enabled)
        self.assertTrue(restored.get(second.id).enabled)
        self.assertEqual(len(restored.sources), 2)
        self.panel.items.currentItem().setCheckState(Qt.Checked)
        self.assertTrue(self.manager.registry.get(first.id).enabled)
        self.assertEqual(before, self.manager.db_path.read_bytes())
        self.assertEqual(self.manager.state.commander_fid, 'UNCHANGED')
        self.assertEqual(self.manager.state.viewed_commander_id, 42)

    def test_double_click_opens_editor(self):
        self.source('automatic')
        with patch.object(self.panel, 'edit') as edit:
            self.panel.items.itemDoubleClicked.emit(self.panel.items.currentItem())
        edit.assert_called_once()

    def test_empty_editor_path_has_explanation_and_stays_open(self):
        editor = SourceEditor(self.panel)
        self.addCleanup(editor.close)
        with patch('cmdrhelper.ui.journal_sources.QMessageBox.warning') as warning:
            editor.accept()
        warning.assert_called_once()
        self.assertNotEqual(editor.result(), QDialog.Accepted)

    def test_narrow_layout_long_paths_both_themes_and_languages(self):
        source = self.source('/'.join(['long-directory-name']*10),0)
        for language in _TRANSLATIONS:
            set_language(language)
            panel = JournalSourcesPanel(self.manager)
            scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setWidget(panel)
            try:
                for style in (DARK_STYLESHEET,LIGHT_STYLESHEET):
                    scroll.setStyleSheet(style)
                    scroll.resize(360,600); scroll.show(); self.app.processEvents()
                    self.assertLessEqual(panel.minimumSizeHint().width(),scroll.viewport().width())
                    self.assertEqual(panel.action_columns,1)
                    self.assertEqual(panel.path.toolTip(),source.path)
                    self.assertGreater(panel.items.horizontalScrollBar().maximum(),0)
                    for button in panel.buttons.values():
                        self.assertGreaterEqual(button.geometry().left(),0)
                        self.assertLessEqual(button.geometry().right(),panel.width())
                    panel.grab()  # Exercise painting at the process's configured scale.
                scroll.resize(850,650); self.app.processEvents()
                self.assertEqual(panel.action_columns,2)
            finally:
                scroll.takeWidget()
                panel.close(); panel.deleteLater(); scroll.close()

    def test_all_languages_have_journal_directory_labels(self):
        keys=('sources.title','sources.reachability','sources.reachable','sources.monitoring',
              'sources.monitoring_active','sources.monitoring_inactive')
        for language,table in _TRANSLATIONS.items():
            for key in keys:
                self.assertTrue(table.get(key),(language,key))
        self.assertEqual(_TRANSLATIONS['de']['sources.title'],'Journalverzeichnisse')


if __name__ == '__main__':
    unittest.main()
