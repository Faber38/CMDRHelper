"""Source management; removing a configuration never removes journal data."""
from pathlib import Path
from datetime import datetime
import json
import os
from PySide6.QtCore import Qt, QTimer, QFileSystemWatcher
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QListWidget,
    QListWidgetItem, QPushButton, QFileDialog, QDialog, QDialogButtonBox,
    QFormLayout, QLineEdit, QCheckBox, QLabel, QMessageBox, QGridLayout,
    QSizePolicy)
from cmdrhelper.i18n import tr
from cmdrhelper.journal_catchup import load_sessions


def directory_reachable(path):
    try:
        with os.scandir(path):
            return True
    except OSError:
        return False


def statistics_signature(database, folder):
    """Cheap invalidation for commits (including WAL) and directory replacement.

    File contents/mtimes are covered separately by QFileSystemWatcher. Unknown
    database paths or inaccessible metadata must never validate cached results.
    """
    path = getattr(database, 'path', None)
    if path is None:
        return None
    paths = [Path(path), Path(str(path) + '-wal'), Path(folder)]
    signature = []
    for index, item in enumerate(paths):
        try:
            stat = item.stat()
            signature.append((str(item), stat.st_dev, stat.st_ino, stat.st_size,
                              stat.st_mtime_ns, stat.st_ctime_ns, stat.st_mode))
        except FileNotFoundError:
            if index != 1:  # Only an absent WAL is a known, reusable state.
                return None
            signature.append(None)
        except OSError:
            return None
    return tuple(signature)


def source_statistics(source, sessions):
    """Read-only diagnostics. Never index, import or advance a journal cursor."""
    folder = Path(source.path)
    result = dict(count='–', oldest='–', newest='–', newest_name='–', last_read='–',
                  reachable=False)
    try:
        files = sorted(((p.stat().st_mtime, p) for p in folder.iterdir()
                        if p.match('Journal.*.log') and p.is_file()),
                       key=lambda item: (item[0], item[1].name))
        result.update(reachable=True, count=str(len(files)))
        if files:
            result.update(oldest=datetime.fromtimestamp(files[0][0]).strftime('%Y-%m-%d %H:%M:%S'),
                          newest=datetime.fromtimestamp(files[-1][0]).strftime('%Y-%m-%d %H:%M:%S'),
                          newest_name=files[-1][1].name)
    except OSError:
        return result
    # Use the persisted path key, not a canonical alias or the displayed commander.
    rows = [r for r in sessions if Path(r['journal_file']).parent == folder
            and int(r.get('last_read_offset') or 0) > 0]
    stamps = []
    for row in rows:
        offset = int(row['last_read_offset'])
        if offset == row.get('last_complete_line_offset') and row.get('last_event_at'):
            stamps.append(row['last_event_at'])
            continue
        # A partially processed journal can have newer index metadata. Inspect
        # only a bounded tail ending at the committed cursor, never unread bytes.
        try:
            with Path(row['journal_file']).open('rb') as stream:
                start = max(0, offset - 65536)
                stream.seek(start)
                raw = stream.read(offset - start)
            if len(raw) != offset - start or not raw.endswith(b'\n'):
                continue
            lines = raw.splitlines()
            for line in reversed(lines[1:] if start else lines):
                try:
                    event = json.loads(line)
                except (ValueError, UnicodeDecodeError):
                    continue
                if (isinstance(event, dict) and event.get('event')
                        and isinstance(event.get('timestamp'), str) and event['timestamp']):
                    stamps.append(event['timestamp'])
                    break
        except OSError:
            continue
    if stamps:
        result['last_read'] = max(stamps)
    return result


class SourceEditor(QDialog):
    def __init__(self, parent, source=None):
        super().__init__(parent)
        self.setWindowTitle(tr('sources.edit') if source else tr('sources.add'))
        layout = QVBoxLayout(self)
        form = QFormLayout()
        form.setRowWrapPolicy(QFormLayout.WrapAllRows)
        self.name = QLineEdit(source.name if source else '')
        self.path = QLineEdit(source.path if source else '')
        self.enabled = QCheckBox(tr('sources.enabled'))
        self.enabled.setChecked(source.enabled if source else True)
        browse = QPushButton(tr('settings.choose_journal_folder'))
        browse.clicked.connect(self.browse)
        form.addRow(tr('sources.name'), self.name)
        form.addRow(tr('settings.journal_folder'), self.path)
        form.addRow(browse)
        form.addRow(self.enabled)
        layout.addLayout(form)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def browse(self):
        folder = QFileDialog.getExistingDirectory(self, tr('settings.choose_journal_folder'), self.path.text())
        if folder:
            self.path.setText(folder)

    def accept(self):
        if not self.path.text().strip():
            QMessageBox.warning(self, tr('sources.title'), tr('sources.invalid_path'))
            return
        super().accept()


class JournalSourcesPanel(QWidget):
    def __init__(self, manager, parent=None):
        super().__init__(parent)
        self.manager = manager
        self._changing_check = False
        self._statistics_cache = {}
        self._refresh_pending = True
        # Coalesce filesystem notifications; never do I/O in a hidden panel.
        self._file_refresh = QTimer(self)
        self._file_refresh.setSingleShot(True)
        self._file_refresh.timeout.connect(self.refresh_visible)
        layout = QVBoxLayout(self)
        title = QLabel(tr('sources.title'))
        title.setWordWrap(True)
        layout.addWidget(title)
        self.items = QListWidget()
        self.items.setTextElideMode(Qt.ElideNone)
        self.items.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.items.setMinimumWidth(0)
        self.items.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Expanding)
        self.items.setMinimumHeight(self.fontMetrics().height() * 8)
        self.items.setMaximumHeight(self.fontMetrics().height() * 14)
        self.items.currentItemChanged.connect(self.selection_changed)
        self.items.itemChanged.connect(self.monitoring_changed)
        self.items.itemDoubleClicked.connect(lambda *_: self.edit())
        layout.addWidget(self.items)
        actions = QGridLayout()
        self.actions = actions
        self.action_columns = 1
        self.buttons = {}
        for key, callback in [('add', self.add), ('edit', self.edit),
                              ('remove', self.remove), ('search', manager.rediscover),
                              ('read', self.read_now)]:
            button = QPushButton(tr('settings.read_now') if key == 'read' else tr('sources.'+key))
            button.clicked.connect(callback)
            index = len(self.buttons)
            self.buttons[key] = button
            actions.addWidget(button, index, 0)
        layout.addLayout(actions)
        note = QLabel(tr('sources.remove_note'))
        note.setWordWrap(True)
        layout.addWidget(note)
        self.path = QLineEdit()
        self.path.setReadOnly(True)
        self.path.setMinimumWidth(0)
        self.path.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Fixed)
        form = QFormLayout()
        form.setRowWrapPolicy(QFormLayout.WrapAllRows)
        self.statistics_form = form
        form.addRow(tr('settings.journal_folder'), self.path)
        self.statistics = {}
        for key, label in [('count', 'settings.journal_files_found'),
                           ('oldest', 'settings.oldest_journal'),
                           ('newest', 'settings.newest_journal'),
                           ('newest_name', 'settings.newest_file'),
                           ('last_read', 'settings.last_read_entry'),
                           ('reachable', 'sources.reachability'),
                           ('monitoring', 'sources.monitoring')]:
            value = QLineEdit() if key == 'newest_name' else QLabel('–')
            if isinstance(value, QLineEdit):
                value.setReadOnly(True)
                value.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Fixed)
            else:
                value.setWordWrap(True)
                value.setTextFormat(Qt.PlainText)
                value.setTextInteractionFlags(Qt.TextSelectableByMouse)
            self.statistics[key] = value
            form.addRow(tr(label), value)
        layout.addLayout(form)
        manager.changed.connect(self.refresh)
        self.timer = QTimer(self)
        self.timer.setInterval(3000)
        self.timer.timeout.connect(self.refresh_visible)
        self.timer.start()
        self.refresh()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        columns = 2 if self.width() >= 520 else 1
        self.statistics_form.setRowWrapPolicy(
            QFormLayout.WrapLongRows if columns == 2 else QFormLayout.WrapAllRows)
        if columns != self.action_columns:
            self.action_columns = columns
            for button in self.buttons.values():
                self.actions.removeWidget(button)
            for index, button in enumerate(self.buttons.values()):
                self.actions.addWidget(button, index // columns, index % columns)

    def refresh(self):
        self._refresh_pending = True
        if not self.isVisible():
            return
        if self._changing_check:
            return
        sources = {source.id: source.path for source in self.manager.registry.sources}
        for identity, cached in list(self._statistics_cache.items()):
            if sources.get(identity) != cached['path']:
                self._discard_statistics(identity)
        self._refresh_pending = False
        selected = self.selected_id()
        self.items.blockSignals(True)
        self.items.clear()
        for source in self.manager.registry.sources:
            identities = ', '.join(f'{name or fid} ({fid})' for fid, name in source.identities)
            status = tr('sources.status.'+source.status)
            enabled = tr('sources.monitoring_active' if source.enabled else 'sources.monitoring_inactive')
            reachable = tr('sources.reachable' if directory_reachable(source.path) else 'sources.status.unreachable')
            text = f'{source.name} — {enabled} — {reachable} — {status}\n{source.path}\n{identities or tr("sources.identity_unknown")}'
            runtime = self.manager.runtimes.get(source.id)
            if runtime and runtime.transfer_error:
                text += '\n' + tr('sources.upload_pending')
            item = QListWidgetItem(text)
            item.setToolTip(text)
            item.setData(Qt.UserRole, source.id)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Checked if source.enabled else Qt.Unchecked)
            self.items.addItem(item)
            if source.id == selected:
                self.items.setCurrentItem(item)
        if self.items.currentRow() < 0 and self.items.count():
            self.items.setCurrentRow(0)
        self.items.blockSignals(False)
        self.selection_changed()

    def refresh_visible(self):
        if self.isVisible():
            self.refresh()

    def showEvent(self, event):
        super().showEvent(event)
        if self._refresh_pending:
            self.refresh()
        else:
            self.selection_changed()

    def _discard_statistics(self, identity):
        cached = self._statistics_cache.pop(identity, None)
        if cached is not None:
            watcher = cached['watcher']
            paths = watcher.files() + watcher.directories()
            if paths:
                watcher.removePaths(paths)
            watcher.deleteLater()

    def _files_changed(self, identity, watcher):
        cached = self._statistics_cache.get(identity)
        if cached is None or cached['watcher'] is not watcher:
            return  # A queued notification from an already replaced watch.
        cached['dirty'] = True
        self._refresh_pending = True
        if self.isVisible():
            self._file_refresh.start(0)

    def _statistics_for(self, source):
        database = self.manager.state.database
        signature = statistics_signature(database, source.path)
        cached = self._statistics_cache.get(source.id)
        if (cached is not None and not cached['dirty'] and signature is not None
                and cached['signature'] == signature):
            return cached['data']

        self._discard_statistics(source.id)
        watcher = QFileSystemWatcher(self)
        watcher.directoryChanged.connect(lambda _path: self._files_changed(source.id, watcher))
        watcher.fileChanged.connect(lambda _path: self._files_changed(source.id, watcher))
        # Register before reading. Watch every matching file, including old and
        # disabled-source journals: a directory watch alone misses file appends.
        watched = watcher.addPath(source.path)
        try:
            files = [str(p) for p in Path(source.path).iterdir() if p.match('Journal.*.log')]
            if files and watcher.addPaths(files):
                watched = False
        except OSError:
            watched = False
        cached = dict(path=source.path, watcher=watcher, dirty=True,
                      signature=signature, data=None)
        self._statistics_cache[source.id] = cached
        failed = False
        try:
            sessions = load_sessions(database)
        except Exception:
            sessions = []
            failed = True
        data = source_statistics(source, sessions)
        if failed:
            data['last_read'] = tr('common.error')
        cached['data'] = data
        # Failed watches/reads and concurrent commits are retried on the next
        # visible refresh, rather than treating an uncertain snapshot as valid.
        cached['dirty'] = (failed or not watched or not data['reachable']
                           or signature is None
                           or signature != statistics_signature(database, source.path))
        return data

    def selection_changed(self, *_):
        if not self.isVisible():
            self._refresh_pending = True
            return
        identity = self.selected_id()
        source = self.manager.registry.get(identity) if identity else None
        for key in ('edit', 'remove'):
            self.buttons[key].setEnabled(source is not None)
        runtime = self.manager.runtimes.get(identity)
        self.buttons['read'].setEnabled(bool(source and source.enabled and runtime))
        self.path.setText(source.path if source else '')
        self.path.setToolTip(self.path.text())
        self.path.setCursorPosition(0)
        for value in self.statistics.values():
            value.setText('–')
            value.setToolTip('')
        if source is None:
            return
        data = self._statistics_for(source)
        for key in ('count', 'oldest', 'newest', 'newest_name', 'last_read'):
            self.statistics[key].setText(data[key])
            self.statistics[key].setToolTip(data[key])
        self.statistics['newest_name'].setCursorPosition(0)
        self.statistics['reachable'].setText(tr('sources.reachable' if data['reachable'] else 'sources.status.unreachable'))
        watching = bool(runtime and runtime.watcher.timer.isActive())
        self.statistics['monitoring'].setText(tr('sources.monitoring_active' if watching else 'sources.monitoring_inactive'))

    def read_now(self):
        identity = self.selected_id()
        source = self.manager.registry.get(identity) if identity else None
        if source and source.enabled and identity in self.manager.runtimes:
            self._discard_statistics(identity)
            self.manager.request(identity)
            self.refresh()

    def selected_id(self):
        item = self.items.currentItem()
        return item.data(Qt.UserRole) if item else None

    def add(self):
        self._edit(None)

    def edit(self):
        identity = self.selected_id()
        if identity:
            self._edit(self.manager.registry.get(identity))

    def _edit(self, source):
        dialog = SourceEditor(self, source)
        if dialog.exec() != QDialog.Accepted:
            return
        try:
            path = dialog.path.text().strip()
            path_changed = source is None or path != source.path
            if path_changed:
                # A running batch keeps its original directory. Do not replace
                # that runtime from a modal editor while it is still working.
                if source is not None and getattr(self.manager, 'running', False):
                    QMessageBox.warning(self, tr('sources.title'), tr('sources.edit_busy'))
                    return
                try:
                    resolved = Path(path).expanduser().resolve(strict=True)
                    if (not resolved.is_dir() or not os.access(resolved, os.R_OK | os.X_OK)
                            or not directory_reachable(resolved)):
                        raise OSError('unreadable directory')
                except (OSError, RuntimeError, ValueError):
                    QMessageBox.warning(self, tr('sources.title'), tr('sources.invalid_path'))
                    return
            if source is None:
                from cmdrhelper.journal_sources import canonical
                if any(s.canonical_path == canonical(dialog.path.text().strip())
                       for s in self.manager.registry.sources):
                    raise ValueError('duplicate')
                source = self.manager.registry.add(dialog.path.text().strip(), dialog.name.text().strip())
            self.manager.registry.update(source.id, path=dialog.path.text().strip(),
                name=dialog.name.text().strip(), enabled=dialog.enabled.isChecked())
            self.manager.reconcile()
            for index in range(self.items.count()):
                if self.items.item(index).data(Qt.UserRole) == source.id:
                    self.items.setCurrentRow(index)
                    break
        except ValueError:
            QMessageBox.warning(self, tr('sources.title'), tr('sources.duplicate'))

    def monitoring_changed(self, item):
        identity = item.data(Qt.UserRole)
        source = self.manager.registry.get(identity)
        enabled = item.checkState() == Qt.Checked
        if enabled == source.enabled:
            return
        self._changing_check = True
        try:
            self.manager.registry.update(identity, enabled=enabled)
            self.manager.reconcile()
        finally:
            self._changing_check = False
            # Never delete the emitting QListWidgetItem during its mouse event.
            QTimer.singleShot(0, self.refresh)

    def remove(self):
        identity = self.selected_id()
        if identity:
            self.manager.registry.remove(identity)
            self.manager.reconcile()
