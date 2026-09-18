"""Explorer favorites: explicit editing and private, confirmed image imports."""
from datetime import datetime
from pathlib import Path
import sqlite3
import math

from PySide6.QtCore import Qt, QSize, QRect, QTimer, QLocale, QSaveFile, QIODevice
from PySide6.QtGui import QIcon, QPixmap, QImageReader
from PySide6.QtWidgets import (QWidget, QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QTextEdit, QPushButton, QComboBox, QListWidget, QListWidgetItem,
    QDialogButtonBox, QFileDialog, QMessageBox, QLayout, QCheckBox, QDoubleSpinBox)

from cmdrhelper.favorites import (FavoriteStore, TYPES, CATEGORIES, latest_screenshot,
                                 freeze_surface_location, navigate_to_favorite,
                                 screenshot_capture_time)
from cmdrhelper.i18n import tr, get_language
from cmdrhelper.material_traders import Coordinates
from cmdrhelper.favorites_transfer import (export_package, read_package,
    prepare_import, apply_import, TransferError)


def stored_coordinates(connection, address, name):
    """Resolve known XYZ locally; an address takes precedence over a name lookup."""
    if address is not None:
        rows = connection.execute(
            'SELECT x,y,z FROM systems WHERE system_address=?', (address,))
    elif name:
        rows = connection.execute(
            'SELECT x,y,z FROM systems WHERE name=? COLLATE NOCASE', (name,))
    else:
        return None
    coordinates = []
    for row in rows:
        try:
            coordinates.append(Coordinates(*row))
        except (TypeError, ValueError):
            continue
    # Ambiguous names must never produce a guessed position.
    return coordinates[0] if coordinates and all(c == coordinates[0] for c in coordinates) else None


def preview(path, width=600, height=320):
    if not path:
        return QPixmap()
    reader = QImageReader(str(path))
    reader.setAutoTransform(True)
    size = reader.size()
    if size.isValid():
        reader.setScaledSize(size.scaled(width, height, Qt.KeepAspectRatio))
    return QPixmap.fromImage(reader.read())


def location_text(record):
    parts = [tr('favorites.type.' + record['type']), record.get('system_name') or '']
    if record.get('body_name'):
        parts.append(record['body_name'])
    if valid_surface_coordinates(record):
        parts.append(f"{record['latitude']:.6f}° / {record['longitude']:.6f}°")
    return ' · '.join(parts)


def valid_surface_coordinates(record):
    return bool(record and record.get('type') == 'surface_location' and all(
        type(record.get(key)) in (int, float) and math.isfinite(record[key])
        and -limit <= record[key] <= limit
        for key, limit in (('latitude', 90), ('longitude', 180))))


def route_system(record):
    name = record.get('system_name') if record and record.get('type') in TYPES else None
    return name.strip() if isinstance(name, str) else ''


def can_navigate(record):
    body = record.get('body_name') if record else None
    return bool(route_system(record) and isinstance(body, str) and body.strip()
                and valid_surface_coordinates(record))


def text_label(text):
    label = QLabel(text)
    label.setTextFormat(Qt.PlainText)
    label.setWordWrap(True)
    return label


class FavoriteDialog(QDialog):
    def __init__(self, store, state, record, parent=None):
        super().__init__(parent)
        self.store, self.state = store, state
        self.record = dict(record)  # Frozen values, never a reference to live state.
        self.image_source = None
        self.remove_image = False
        self.saved = None
        self.setWindowTitle(tr('favorites.edit'))
        self.resize(640, 540)
        root = QVBoxLayout(self)
        root.addWidget(text_label(location_text(record)))
        form = QFormLayout()
        self.name = QLineEdit(record.get('name', ''))
        self.category = QComboBox()
        for category in CATEGORIES:
            self.category.addItem(tr('favorites.category.' + category), category)
        self.category.setCurrentIndex(max(0, self.category.findData(record.get('category','other'))))
        self.note = QTextEdit(record.get('note',''))
        self.note.setAcceptRichText(False)
        form.addRow(tr('favorites.name'), self.name)
        form.addRow(tr('favorites.category'), self.category)
        form.addRow(tr('favorites.note'), self.note)
        root.addLayout(form)
        self.image = QLabel()
        self.image.setAlignment(Qt.AlignCenter)
        self.image.setMinimumHeight(100)
        root.addWidget(self.image)
        self._show_image(store.image_file(record.get('image_path','')))
        row = QHBoxLayout()
        for key, callback in [('latest',self._latest),('choose_image',self._choose),('remove_image',self._remove)]:
            button = QPushButton(tr('favorites.' + key)); button.clicked.connect(callback); row.addWidget(button)
        root.addLayout(row)
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Save).setText(tr('favorites.save'))
        buttons.button(QDialogButtonBox.Cancel).setText(tr('planet_nav.cancel'))
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)
        signal = getattr(state, 'commanderIdentityChanged', None)
        if signal is not None:
            signal.connect(self._commander_changed)
            self.finished.connect(lambda _: signal.disconnect(self._commander_changed))

    def _commander_changed(self, *_):
        if self.state.commander_id != self.record['commander_id']:
            self.reject()

    def _show_image(self, path):
        pixmap = preview(path, 560, 200)
        self.image.setPixmap(pixmap)
        if pixmap.isNull():
            self.image.setText(tr('favorites.no_image'))

    def _choose(self):
        filename, _ = QFileDialog.getOpenFileName(self, tr('favorites.choose_image'), '',
                                                 tr('favorites.image_filter'))
        if filename:
            self.select_image(Path(filename))

    def select_image(self, path):
        if preview(path).isNull():
            QMessageBox.information(self, tr('favorites.title'), tr('favorites.image_error'))
            return
        self.image_source, self.remove_image = Path(path), False
        self._show_image(path)

    def _latest(self):
        path = latest_screenshot(
            self.state.settings,
            commander_fid=getattr(self.state, 'commander_fid', ''),
            commander_name=getattr(self.state, 'commander', ''))
        if path is None:
            QMessageBox.information(self, tr('favorites.title'), tr('favorites.no_screenshot'))
            return
        try:
            converted = not path.stem.lower().startswith(('screenshot', 'highresscreenshot'))
            date = datetime.fromtimestamp(screenshot_capture_time(path, converted=converted)).astimezone().strftime('%Y-%m-%d %H:%M:%S %Z')
        except OSError:
            QMessageBox.information(self, tr('favorites.title'), tr('favorites.no_screenshot'))
            return
        dialog = QDialog(self)
        dialog.setWindowTitle(tr('favorites.confirm_image'))
        layout = QVBoxLayout(dialog)
        layout.addWidget(text_label(path.name + '\n' + date))
        image = QLabel(); image.setPixmap(preview(path)); layout.addWidget(image)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Ok).setText(tr('favorites.use_image'))
        buttons.button(QDialogButtonBox.Cancel).setText(tr('planet_nav.cancel'))
        buttons.accepted.connect(dialog.accept); buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        if dialog.exec() == QDialog.Accepted:
            self.select_image(path)

    def _remove(self):
        self.image_source, self.remove_image = None, True
        self._show_image(None)

    def _save(self):
        if self.state.commander_id != self.record['commander_id']:
            QMessageBox.information(self, tr('favorites.title'), tr('favorites.commander_changed'))
            self.reject()
            return
        values = dict(self.record, name=self.name.text(), category=self.category.currentData(), note=self.note.toPlainText())
        try:
            self.saved = self.store.save(self.record['commander_id'], values, self.record.get('id'),
                                         self.image_source, self.remove_image)
        except (OSError, ValueError, sqlite3.Error):
            QMessageBox.warning(self, tr('favorites.title'), tr('favorites.save_error'))
            return
        self.accept()


class _SaveActionsLayout(QLayout):
    """Equal-width save actions, wrapping without forcing a wide window."""
    def __init__(self):
        super().__init__()
        self._items = []
        self.setContentsMargins(0, 0, 0, 0)
        self.setSpacing(8)

    def addItem(self, item):
        self._items.append(item)
        self.invalidate()

    def count(self):
        return len(self._items)

    def itemAt(self, index):
        return self._items[index] if 0 <= index < self.count() else None

    def takeAt(self, index):
        return self._items.pop(index) if 0 <= index < self.count() else None

    def expandingDirections(self):
        return Qt.Horizontal

    def hasHeightForWidth(self):
        return True

    def minimumSize(self):
        size = QSize()
        for item in self._items:
            size = size.expandedTo(item.sizeHint())
        return size

    def sizeHint(self):
        return self.minimumSize()

    def _columns(self, width):
        cell = max(1, self.minimumSize().width())
        return max(1, min(self.count(), (width + self.spacing()) // (cell + self.spacing())))

    def heightForWidth(self, width):
        columns = self._columns(width)
        rows = (self.count() + columns - 1) // columns
        return rows * self.minimumSize().height() + max(0, rows - 1) * self.spacing()

    def setGeometry(self, rect):
        super().setGeometry(rect)
        columns = self._columns(rect.width())
        width = (rect.width() - (columns - 1) * self.spacing()) // columns
        height = self.minimumSize().height()
        for index, item in enumerate(self._items):
            row, column = divmod(index, columns)
            item.setGeometry(QRect(rect.x() + column * (width + self.spacing()),
                                   rect.y() + row * (height + self.spacing()), width, height))


class FavoritesView(QWidget):
    def __init__(self, state, navigator_callback, explorer_callback, parent=None,
                 *, location_controller_callback=None, quick_favorite_hotkey=None,
                 configure_hotkey_callback=None, route_callback=None):
        super().__init__(parent)
        self.state = state
        self.store = FavoriteStore(state.database)
        self.navigator_callback, self.explorer_callback = navigator_callback, explorer_callback
        self.route_callback = route_callback
        self._location_controller_callback = location_controller_callback
        self._quick_favorite_hotkey = quick_favorite_hotkey
        self._configure_hotkey_callback = configure_hotkey_callback
        self._commander = None
        self._details = None
        self._favorite_target = None
        root = QVBoxLayout(self)
        row = _SaveActionsLayout()
        for key, callback in [('save_system',self.save_system),('save_body',self.save_body)]:
            button = QPushButton(tr('favorites.' + key)); button.clicked.connect(callback); row.addWidget(button)
        self.save_location_button = QPushButton(tr('favorites.save_surface'))
        self.save_location_button.setEnabled(False)
        self.save_location_button.clicked.connect(self._save_current_location)
        row.addWidget(self.save_location_button)
        root.addLayout(row)
        filters = QHBoxLayout()
        self.search = QLineEdit(); self.search.setPlaceholderText(tr('favorites.search'))
        self.kind = QComboBox(); self.kind.addItem(tr('favorites.all_types'), '')
        for kind in TYPES:self.kind.addItem(tr('favorites.type.'+kind),kind)
        self.category = QComboBox(); self.category.addItem(tr('favorites.all_categories'),'')
        for category in CATEGORIES:self.category.addItem(tr('favorites.category.'+category),category)
        filters.addWidget(self.search,1); filters.addWidget(self.kind); filters.addWidget(self.category)
        root.addLayout(filters)
        distance_filters = QHBoxLayout()
        self.distance_filter = QCheckBox(tr('favorites.distance_filter'))
        enabled = state.settings.value('favorites/distance_filter_enabled', False)
        self.distance_filter.setChecked(str(enabled).lower() in ('true', '1'))
        self.max_distance = QDoubleSpinBox()
        self.max_distance.setLocale(QLocale(get_language()))
        self.max_distance.setRange(1, 100000)
        self.max_distance.setDecimals(1)
        self.max_distance.setSuffix(' ' + tr('favorites.distance_unit'))
        try:
            maximum = float(state.settings.value('favorites/max_distance_ly', 500))
        except (TypeError, ValueError):
            maximum = 500
        self.max_distance.setValue(maximum if math.isfinite(maximum) else 500)
        self.max_distance.setEnabled(self.distance_filter.isChecked())
        distance_label = QLabel(tr('favorites.max_distance'))
        distance_label.setBuddy(self.max_distance)
        distance_filters.addWidget(self.distance_filter)
        distance_filters.addWidget(distance_label)
        distance_filters.addWidget(self.max_distance)
        distance_filters.addStretch()
        root.addLayout(distance_filters)
        self.distance_status = text_label('')
        self.distance_status.setObjectName('muted')
        root.addWidget(self.distance_status)
        self.list = QListWidget(); self.list.setIconSize(QSize(80,60)); self.list.setUniformItemSizes(True)
        root.addWidget(self.list,1)
        self.empty = text_label(tr('favorites.empty')); root.addWidget(self.empty)
        actions = QHBoxLayout(); self.action_buttons = []
        for key, callback in [('open',self.open_selected),('edit',self.edit_selected),('delete',self.delete_selected),('route',self.route_selected),('navigate',self.navigate_selected)]:
            button = QPushButton(tr('favorites.'+key)); button.clicked.connect(callback); actions.addWidget(button)
            if key in ('route', 'navigate'):
                button.setObjectName('favoriteNavigate')
            self.action_buttons.append(button)
        root.addLayout(actions)
        transfer_actions = QHBoxLayout()
        transfer_actions.addStretch()
        self.export_button = QPushButton(tr('favorites.transfer.export'))
        self.import_button = QPushButton(tr('favorites.transfer.import'))
        self.export_button.clicked.connect(self.export_favorites)
        self.import_button.clicked.connect(self.import_favorites)
        transfer_actions.addWidget(self.export_button)
        transfer_actions.addWidget(self.import_button)
        root.addLayout(transfer_actions)
        self.route_button, self.coordinates_button = self.action_buttons[-2:]
        self.quick_favorite_hint = QWidget()
        hint_layout = QHBoxLayout(self.quick_favorite_hint)
        hint_layout.setContentsMargins(0, 8, 0, 0)
        hint_text = QVBoxLayout()
        hint_text.setSpacing(3)
        title = QLabel(tr('quick_favorite.title'), objectName='muted')
        description = text_label(tr('quick_favorite.hint'))
        description.setObjectName('muted')
        hint_text.addWidget(title)
        hint_text.addWidget(description)
        hint_layout.addLayout(hint_text, 1)
        self.quick_favorite_setup_button = QPushButton(tr('quick_favorite.set'))
        if configure_hotkey_callback is not None:
            self.quick_favorite_setup_button.clicked.connect(configure_hotkey_callback)
        hint_layout.addWidget(self.quick_favorite_setup_button)
        root.addWidget(self.quick_favorite_hint)
        if quick_favorite_hotkey is not None:
            quick_favorite_hotkey.changed.connect(self._refresh_quick_favorite_hint)
        self._refresh_quick_favorite_hint()
        self.search.textChanged.connect(self.refresh)
        self.kind.currentIndexChanged.connect(self.refresh)
        self.category.currentIndexChanged.connect(self.refresh)
        self.distance_filter.toggled.connect(self._distance_filter_changed)
        self.max_distance.valueChanged.connect(self._distance_filter_changed)
        self.list.currentItemChanged.connect(self._selection_changed)
        self.list.itemDoubleClicked.connect(self.open_selected)
        signal = getattr(state,'commanderIdentityChanged',None)
        if signal is not None:signal.connect(self.sync_commander)
        # Position signals can precede store_snapshot; defer until state processing
        # has finished, and coalesce positionChanged + changed from the same jump.
        self._distance_refresh_timer = QTimer(self)
        self._distance_refresh_timer.setSingleShot(True)
        self._distance_refresh_timer.timeout.connect(self.refresh)
        for name in ('positionChanged', 'changed'):
            signal = getattr(state, name, None)
            if signal is not None:
                signal.connect(self._schedule_distance_refresh)
        self._location_controller = None
        self.sync_commander()

    def showEvent(self, event):
        super().showEvent(event)
        self.refresh()
        self._refresh_quick_favorite_hint()
        if self._location_controller_callback is not None and self._location_controller is None:
            self._location_controller = self._location_controller_callback()
            self._location_controller.changed.connect(self._refresh_location_availability)
            self._location_controller.consumer_acquire("favorites")
        self._refresh_location_availability()

    def hideEvent(self, event):
        if self._location_controller is not None:
            self._location_controller.changed.disconnect(self._refresh_location_availability)
            self._location_controller.consumer_release("favorites")
            self._location_controller = None
        super().hideEvent(event)

    def _refresh_quick_favorite_hint(self):
        self.quick_favorite_hint.setVisible(
            self._quick_favorite_hotkey is not None
            and self._configure_hotkey_callback is not None
            and not self._quick_favorite_hotkey.active)

    def _refresh_location_availability(self, *_):
        available = False
        if self._location_controller is not None:
            try:
                # Use the exact same validity and identity checks as saving.
                freeze_surface_location(self._location_controller, refresh=False)
                available = True
            except ValueError:
                pass
        self.save_location_button.setEnabled(available)

    def _save_current_location(self):
        if self._location_controller_callback is not None:
            # Re-read and freeze at click time, never reuse the availability sample.
            self.save_surface(self._location_controller_callback())

    def sync_commander(self, *_):
        self._refresh_location_availability()
        current = getattr(self.state,'commander_id',None)
        if current != self._commander:
            self.save_location_button.setEnabled(False)
            if self._favorite_target is not None:
                controller, target = self._favorite_target
                if self._target_key(controller.target) == target:
                    controller.stop_target()
                self._favorite_target = None
            if self._details is not None:self._details.close()
            self._commander = current
            self.refresh()

    def _schedule_distance_refresh(self, *_):
        if self.isVisible():
            self._distance_refresh_timer.start(0)
        # showEvent always reloads the current records and distances.

    def _distance_filter_changed(self, *_):
        enabled = self.distance_filter.isChecked()
        self.max_distance.setEnabled(enabled)
        self.state.settings.setValue('favorites/distance_filter_enabled', enabled)
        self.state.settings.setValue('favorites/max_distance_ly', self.max_distance.value())
        self.refresh()

    def _distances(self, records):
        with self.state.database._connect() as connection:
            reference = stored_coordinates(connection, getattr(self.state, 'system_address', None),
                                           getattr(self.state, 'system', ''))
            distances = {}
            cache = {}
            for record in records:
                key = (record.get('system_address'), record.get('system_name'))
                if key not in cache:
                    target = stored_coordinates(connection, *key) if reference is not None else None
                    cache[key] = reference.distance_to(target) if target is not None else None
                distances[record['id']] = cache[key]
        return reference, distances

    def refresh(self, *_):
        self._refresh_quick_favorite_hint()
        for button in (self.export_button, self.import_button):
            button.setEnabled(bool(getattr(self.state, 'commander_id', None)))
        selected = self.list.currentItem()
        favorite_id = selected.data(Qt.UserRole) if selected else None
        self.list.clear()
        records = self.store.list(getattr(self.state,'commander_id',None), self.search.text(),
                                  self.kind.currentData(),self.category.currentData())
        reference, distances = self._distances(records)
        enabled = self.distance_filter.isChecked()
        self.distance_status.setText(tr('favorites.distance_reference_unknown'))
        self.distance_status.setVisible(enabled and reference is None)
        locale = QLocale(get_language())
        for record in records:
            distance = distances[record['id']]
            if enabled and distance is not None and distance > self.max_distance.value():
                continue
            distance_text = ('—' if distance is None else
                             locale.toString(distance, 'f', 1) + ' ' + tr('favorites.distance_unit'))
            item = QListWidgetItem(record['name']+'\n'+location_text(record)+'\n'+
                                   tr('favorites.category.'+record['category'])+' · '+distance_text)
            item.setData(Qt.UserRole,record['id'])
            pixmap = preview(self.store.image_file(record['image_path']),80,60)
            if not pixmap.isNull():item.setIcon(QIcon(pixmap))
            self.list.addItem(item)
            if record['id'] == favorite_id:self.list.setCurrentItem(item)
        self.empty.setVisible(self.list.count()==0)
        self._selection_changed()

    def selected(self):
        item = self.list.currentItem()
        if item is None:return None
        try:return self.store.get(getattr(self.state,'commander_id',None),item.data(Qt.UserRole))
        except ValueError:return None

    def _transfer_error(self, error):
        key = str(error) if isinstance(error, TransferError) else 'io_error'
        QMessageBox.warning(self, tr('favorites.title'), tr('favorites.transfer.' + key))

    def export_favorites(self):
        commander = getattr(self.state, 'commander_id', None)
        if not commander:
            return
        filename, _ = QFileDialog.getSaveFileName(
            self, tr('favorites.transfer.export'),
            'CMDRHelper_Favoriten_' + datetime.now().strftime('%Y-%m-%d') + '.zip',
            'ZIP (*.zip)')  # Qt's overwrite confirmation remains enabled.
        if not filename or commander != self.state.commander_id:
            return
        try:
            data, result = export_package(self.store, commander)
            target = QSaveFile(filename)
            if not target.open(QIODevice.WriteOnly):
                raise OSError(target.errorString())
            if target.write(data) != len(data):
                target.cancelWriting()
                raise OSError(target.errorString())
            if not target.commit():
                raise OSError(target.errorString())
        except (OSError, ValueError, sqlite3.Error) as exc:
            self._transfer_error(exc)
            return
        QMessageBox.information(self, tr('favorites.title'),
                                tr('favorites.transfer.exported', **result))

    def _confirm_import(self, plan):
        dialog = QDialog(self)
        dialog.setWindowTitle(tr('favorites.transfer.import'))
        layout = QVBoxLayout(dialog)
        layout.addWidget(text_label(tr('favorites.transfer.summary', count=len(plan.records),
                                      new=plan.new_count, duplicates=plan.duplicate_count)))
        layout.addWidget(text_label(tr('favorites.transfer.images', missing=plan.missing_images)))
        policy = QComboBox()
        if plan.duplicate_count:
            layout.addWidget(text_label(tr('favorites.transfer.duplicates')))
            for key in ('skip', 'replace', 'new'):
                policy.addItem(tr('favorites.transfer.' + key), key)
            layout.addWidget(policy)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Ok).setText(tr('favorites.transfer.import'))
        buttons.button(QDialogButtonBox.Cancel).setText(tr('planet_nav.cancel'))
        buttons.button(QDialogButtonBox.Cancel).setDefault(True)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        if dialog.exec() != QDialog.Accepted:
            return None
        return policy.currentData() or 'skip'

    def import_favorites(self):
        commander = getattr(self.state, 'commander_id', None)
        if not commander:
            return
        filename, _ = QFileDialog.getOpenFileName(
            self, tr('favorites.transfer.import'), '', 'ZIP (*.zip)')
        if not filename:
            return
        try:
            records, images, missing = read_package(filename)
            plan = prepare_import(self.store, commander, records, images, missing)
            if commander != self.state.commander_id:
                raise TransferError('commander_changed')
            policy = self._confirm_import(plan)
            if policy is None:
                return
            if commander != self.state.commander_id:
                raise TransferError('commander_changed')
            result = apply_import(self.store, plan, policy)
        except (OSError, ValueError, sqlite3.Error) as exc:
            self._transfer_error(exc)
            return
        self.refresh()
        QMessageBox.information(self, tr('favorites.title'),
                                tr('favorites.transfer.imported', **result))

    def _selection_changed(self, *_):
        record = self.selected()
        for button in self.action_buttons:button.setEnabled(record is not None)
        for button, available, tooltip in (
            (self.route_button, bool(route_system(record) and self.route_callback), 'route_tooltip'),
            (self.coordinates_button, can_navigate(record), 'coordinates_tooltip'),
        ):
            button.setVisible(available)
            button.setEnabled(available)
            button.setToolTip(tr('favorites.' + tooltip) if available else '')

    def route_selected(self):
        system = route_system(self.selected())
        if system and self.route_callback is not None:
            self.route_callback(system)

    def edit_record(self, record):
        dialog = FavoriteDialog(self.store,self.state,record,self)
        if dialog.exec() == QDialog.Accepted:self.refresh()

    def _base(self, kind):
        if not getattr(self.state,'commander_id',None) or not getattr(self.state,'system',None):
            QMessageBox.information(self,tr('favorites.title'),tr('favorites.no_location')); return None
        return dict(commander_id=self.state.commander_id,type=kind,system_name=self.state.system,
                    system_address=getattr(self.state,'system_address',None),name=self.state.system,
                    category='other',note='')

    def save_system(self):
        record = self._base('system')
        if record:self.edit_record(record)

    def save_body(self):
        record = self._base('body')
        if not record:return
        bodies = [dict(b) for b in getattr(self.state,'system_bodies',[]) if b.get('body_type')=='Planet' and b.get('name')]
        if not bodies:
            QMessageBox.information(self,tr('favorites.title'),tr('favorites.no_body')); return
        dialog = QDialog(self); dialog.setWindowTitle(tr('favorites.save_body'))
        layout = QVBoxLayout(dialog); selector = QComboBox()
        for body in sorted(bodies,key=lambda b:b['name'].casefold()):selector.addItem(body['name'],body)
        layout.addWidget(selector)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok|QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Ok).setText(tr('favorites.select'))
        buttons.button(QDialogButtonBox.Cancel).setText(tr('planet_nav.cancel'))
        buttons.accepted.connect(dialog.accept); buttons.rejected.connect(dialog.reject); layout.addWidget(buttons)
        if dialog.exec()==QDialog.Accepted and self.state.commander_id==record['commander_id']:
            body=selector.currentData()
            self.edit_record(dict(record,body_name=body['name'],body_id=body.get('body_id'),name=body['name']))

    def save_surface(self, controller):
        try:record=freeze_surface_location(controller)
        except ValueError:
            QMessageBox.information(self,tr('favorites.title'),tr('favorites.no_position')); return
        self.edit_record(record)

    def edit_selected(self):
        record=self.selected()
        if record:self.edit_record(record)

    def delete_selected(self):
        record=self.selected()
        if not record:return
        box=QMessageBox(QMessageBox.Question,tr('favorites.delete'),tr('favorites.confirm_delete',name=record['name']),parent=self)
        box.setTextFormat(Qt.PlainText)
        yes=box.addButton(tr('favorites.delete'),QMessageBox.AcceptRole)
        cancel=box.addButton(tr('planet_nav.cancel'),QMessageBox.RejectRole); box.setDefaultButton(cancel)
        box.exec()
        if box.clickedButton()==yes and self.state.commander_id==record['commander_id']:
            try:self.store.delete(record['commander_id'],record['id'])
            except (OSError,ValueError,sqlite3.Error):
                QMessageBox.warning(self,tr('favorites.title'),tr('favorites.save_error'))
            self.refresh()

    def open_selected(self, *_):
        record=self.selected()
        if not record:return
        dialog=QDialog(self); self._details=dialog; dialog.setWindowTitle(record['name']); dialog.resize(700,500)
        layout=QVBoxLayout(dialog)
        layout.addWidget(text_label(location_text(record)))
        layout.addWidget(text_label(tr('favorites.category.'+record['category'])))
        note=QTextEdit(); note.setReadOnly(True); note.setPlainText(record['note']); layout.addWidget(note)
        image=QLabel(); pixmap=preview(self.store.image_file(record['image_path']))
        if pixmap.isNull():image.setText(tr('favorites.no_image'))
        else:image.setPixmap(pixmap)
        layout.addWidget(image)
        button=QPushButton(tr('favorites.show_explorer')); layout.addWidget(button)
        def show():
            if self.state.commander_id==record['commander_id']:self.explorer_callback(record)
        button.clicked.connect(show)
        if can_navigate(record):
            target=QPushButton(tr('favorites.navigate'), objectName='favoriteNavigate'); layout.addWidget(target)
            target.setToolTip(tr('favorites.coordinates_tooltip'))
            target.clicked.connect(lambda:self._navigate(record))
        dialog.exec(); self._details=None

    def _navigate(self, record):
        if self.state.commander_id!=record['commander_id']:return
        try:
            record = self.store.get(self.state.commander_id, record['id'])
            if not can_navigate(record):return
            controller=self.navigator_callback()
            navigate_to_favorite(self.store,self.state.commander_id,record['id'],controller)
            self._favorite_target = (controller, self._target_key(controller.target))
        except ValueError:
            QMessageBox.information(self,tr('favorites.title'),tr('favorites.commander_changed'))

    def navigate_selected(self):
        record=self.selected()
        if record:self._navigate(record)

    @staticmethod
    def _target_key(target):
        if target is None:
            return None
        return (target.binding.body_name, target.latitude, target.longitude, target.name)
