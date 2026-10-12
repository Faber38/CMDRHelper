"""Reusable editor for ship-specific supplements to automatic route data."""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QCheckBox, QDialog, QDialogButtonBox, QFormLayout,
    QHBoxLayout, QLabel, QLineEdit, QMessageBox, QPushButton, QScrollArea,
    QVBoxLayout, QWidget)

from cmdrhelper.i18n import tr
from .manual_ship_data import (FIELDS, LIVE, configuration, dependencies,
                               identity, live_binding, parse_number, scope)


def text(key, **values):
    return tr('route_planner.assistant_' + key, **values)


class ShipDataDialog(QDialog):
    def __init__(self, state, store, parent=None):
        super().__init__(parent)
        self.state, self.store = state, store
        self.original_identity = identity(state)
        self.original_config = configuration(state)
        self.original_binding = live_binding(state)
        self.setWindowTitle(text('title'))
        self.resize(740, 780)
        layout = QVBoxLayout(self)
        l = state.ship_loadout
        self.identity_text = text('identity', commander=getattr(state, 'commander', '') or '–',
            fid=getattr(state, 'commander_fid', '') or '–', ship=l.ship_type or '–',
            name=l.ship_name or '–', sid=l.ship_id if l.ship_id is not None else '–')
        header = QLabel(self.identity_text)
        header.setTextFormat(Qt.PlainText)
        header.setTextInteractionFlags(Qt.TextSelectableByMouse)
        layout.addWidget(header)
        fsd = QLineEdit(l.fsd_item or '')
        fsd.setReadOnly(True)
        fsd.setPlaceholderText(tr('route_planner.ship_loadout_unknown_fsd'))
        fsd.setToolTip(text('fsd_source'))
        layout.addWidget(fsd)
        explanation = QLabel(text('policy'))
        explanation.setWordWrap(True)
        layout.addWidget(explanation)
        area = QScrollArea()
        area.setWidgetResizable(True)
        content = QWidget()
        self.form = QFormLayout(content)
        area.setWidget(content)
        layout.addWidget(area)
        self.editors, self.errors, self.confirmations = {}, {}, {}
        values, sources, records = store.resolve(state)
        for field, (label_key, unit, maximum, positive) in FIELDS.items():
            row = QWidget()
            box = QVBoxLayout(row)
            box.setContentsMargins(0, 0, 0, 0)
            record = records.get(field)
            source = QLabel(text(sources[field]))
            if values[field] is not None:
                source.setText(source.text() + f': {values[field]:g} {unit}')
            box.addWidget(source)
            line = QHBoxLayout()
            editor = QLineEdit()
            editor.setAccessibleName(tr('route_planner.' + label_key))
            editable = sources[field] != 'automatic' or record is not None
            editor.setReadOnly(not editable)
            value = record['value'] if record else values[field]
            editor.setText('' if value is None else str(value))
            if editable:
                self.editors[field] = editor
            line.addWidget(editor)
            line.addWidget(QLabel(unit))
            help_button = QPushButton('ⓘ')
            help_button.setAccessibleName(text('help'))
            help_button.setToolTip(text('help_' + field))
            help_button.clicked.connect(lambda checked=False, name=field:
                QMessageBox.information(self, text('help'), text('help_' + name)))
            line.addWidget(help_button)
            box.addLayout(line)
            if record:
                compare = QLabel(text('stored', value=record['value']))
                compare.setWordWrap(True)
                box.addWidget(compare)
                if record.get('scope') != scope(state, field):
                    check = QCheckBox(text('confirm_scope'))
                    check.setToolTip(text('scope'))
                    box.addWidget(check)
                    self.confirmations[field] = check
            error = QLabel('')
            error.setWordWrap(True)
            box.addWidget(error)
            self.errors[field] = error
            editor.textChanged.connect(self.validate)
            self.form.addRow(tr('route_planner.' + label_key), row)
        self.message = QLabel('')
        self.message.setWordWrap(True)
        layout.addWidget(self.message)
        actions = QDialogButtonBox(QDialogButtonBox.Close)
        actions.button(QDialogButtonBox.Close).setText(tr('common.close'))
        self.save_button = actions.addButton(text('save'), QDialogButtonBox.ActionRole)
        self.delete_button = actions.addButton(text('delete'), QDialogButtonBox.ActionRole)
        self.save_button.clicked.connect(self.save)
        self.delete_button.clicked.connect(self.delete)
        actions.rejected.connect(self.reject)
        layout.addWidget(actions)
        self.save_button.setEnabled(self.original_identity is not None and store.settings is not None)
        self.delete_button.setEnabled(self.save_button.isEnabled())
        if not self.save_button.isEnabled():
            self.message.setText(text('identity_error'))

    def validate(self):
        edits, errors = {}, {}
        current, sources, records = self.store.resolve(self.state)
        for name, editor in self.editors.items():
            try:
                value = parse_number(editor.text(), name)
                check = self.confirmations.get(name)
                if check is not None and value is not None and not check.isChecked():
                    if value != records.get(name, {}).get('value'):
                        errors[name] = 'scope'
                    continue  # Keep incompatible stored data unchanged, not active.
                edits[name] = value
                if sources[name] != 'automatic':
                    current[name] = value
                if value is not None and name in LIVE and live_binding(self.state) is None:
                    errors[name] = 'context'
                if value is not None and name not in LIVE and scope(self.state, name) is None:
                    errors[name] = 'fsd_error'
            except ValueError as exc:
                errors[name] = str(exc)
        errors.update(dependencies(current, self.state))
        for name, label in self.errors.items():
            code = errors.get(name)
            label.setText(text(code, maximum=FIELDS[name][2],
                               minimum='> 0' if FIELDS[name][3] else '≥ 0') if code else '')
        return edits, errors

    def save(self):
        if (identity(self.state) != self.original_identity
                or configuration(self.state) != self.original_config):
            self.message.setText(text('changed'))
            return
        edits, errors = self.validate()
        if any(name in LIVE and value is not None for name, value in edits.items()):
            if live_binding(self.state) != self.original_binding:
                self.message.setText(text('changed'))
                return
        if errors:
            self.message.setText(text('invalid'))
            return
        try:
            self.store.save(self.state, edits)
        except (OSError, ValueError):
            self.message.setText(text('save_error'))
            return
        self.accept()

    def delete(self):
        if identity(self.state) != self.original_identity:
            self.message.setText(text('changed'))
            return
        if QMessageBox.question(self, text('delete'), text('delete_confirm') + '\n\n' + self.identity_text,
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No) != QMessageBox.Yes:
            return
        try:
            self.store.delete(self.state)
        except (OSError, ValueError):
            self.message.setText(text('save_error'))
            return
        self.accept()
