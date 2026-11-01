"""Local shortcut editor, alongside the existing global favorite editor."""
from html import escape
from PySide6.QtCore import Qt, QSize, QEvent
from PySide6.QtGui import QKeySequence, QPalette
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                              QDialog, QDialogButtonBox, QKeySequenceEdit, QMessageBox,
                              QGridLayout, QLayout, QSizePolicy, QFrame, QBoxLayout)
from cmdrhelper.i18n import tr
from cmdrhelper.shortcuts import ACTIONS, PREFIX
from .quick_favorite_settings import QuickFavoriteSettings


class ShortcutLabel(QLabel):
    """Keep the action heading readable when the application theme changes."""
    def set_content(self, title, detail):
        self.setProperty('actionTitle', title)
        self._detail = detail
        self._render()

    def _render(self):
        color = '#1565C0' if self.palette().color(QPalette.Window).lightness() > 128 else '#FFCC33'
        self.setText('<span style="color: ' + color + '">'
                     + escape(self.property('actionTitle')) + '</span><br>'
                     + escape(self._detail).replace('\n', '<br>'))

    def changeEvent(self, event):
        super().changeEvent(event)
        if event.type() == QEvent.PaletteChange and hasattr(self, '_detail'):
            self._render()


class ShortcutGrid(QWidget):
    """One to three columns, measured from the translated controls and font."""
    def __init__(self, parent):
        super().__init__(parent)
        self.cards = []
        self.columns = 0
        self.grid = QGridLayout(self)
        self.grid.setContentsMargins(0, 0, 0, 0)
        self.grid.setSpacing(8)
        self.grid.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        # The current three-column layout must not prevent shrinking to one.
        self.grid.setSizeConstraint(QLayout.SetNoConstraint)
        policy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        policy.setHeightForWidth(True)
        self.setSizePolicy(policy)

    def card_width(self):
        widths = []
        for card in self.cards:
            row = card.layout()
            controls = row.itemAt(1).layout()
            margins = row.contentsMargins()
            buttons = sum(controls.itemAt(i).widget().sizeHint().width() for i in range(2))
            label = row.itemAt(0).widget()
            name_width = label.fontMetrics().horizontalAdvance(label.property('actionTitle') or '')
            widths.append(max(name_width, label.minimumSizeHint().width(),
                              buttons + controls.spacing()) + margins.left() + margins.right())
        return max(widths, default=1)

    def columns_for_width(self, width):
        spacing = self.grid.horizontalSpacing()
        return max(1, min(3, (width + spacing) // (self.preferred_card_width() + spacing)))

    def preferred_card_width(self):
        # Allow long translations and large fonts to exceed the normal cap.
        return max(260, self.card_width())

    def cell_width(self, width):
        columns = self.columns_for_width(width)
        available = (width - (columns - 1) * self.grid.horizontalSpacing()) // columns
        return max(1, min(self.preferred_card_width(), available))

    def minimumSizeHint(self):
        widths = []
        for card in self.cards:
            row = card.layout()
            margins = row.contentsMargins()
            controls = row.itemAt(1).layout()
            widths.append(max(row.itemAt(0).widget().minimumSizeHint().width(),
                              *(controls.itemAt(i).widget().sizeHint().width() for i in range(2)))
                          + margins.left() + margins.right())
        return QSize(max(widths, default=1), 0)

    def sizeHint(self):
        width = 3 * self.preferred_card_width() + 2 * self.grid.horizontalSpacing()
        return QSize(width, self.heightForWidth(width))

    def heightForWidth(self, width):
        columns = self.columns_for_width(width)
        cell_width = self.cell_width(width)
        heights = []
        for start in range(0, len(self.cards), columns):
            heights.append(max(max(card.minimumSizeHint().height(), card.layout().heightForWidth(cell_width))
                               for card in self.cards[start:start + columns]))
        return sum(heights) + max(0, len(heights) - 1) * self.grid.verticalSpacing()

    def reflow(self):
        if not hasattr(self, 'grid'):
            return
        columns = self.columns_for_width(self.contentsRect().width())
        cell_width = self.cell_width(self.contentsRect().width())
        direction = (QBoxLayout.TopToBottom if cell_width < self.card_width()
                     else QBoxLayout.LeftToRight)
        for card in self.cards:
            card.setFixedWidth(cell_width)
            card.layout().itemAt(1).layout().setDirection(direction)
        if columns != self.columns:
            while self.grid.count():
                self.grid.takeAt(0)
            for column in range(3):
                self.grid.setColumnStretch(column, 0)
            for index, card in enumerate(self.cards):
                self.grid.addWidget(card, index // columns, index % columns)
            self.columns = columns
        self.grid.invalidate()
        self.updateGeometry()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.reflow()

    def changeEvent(self, event):
        super().changeEvent(event)
        if event.type() in (QEvent.FontChange, QEvent.StyleChange):
            self.reflow()


class ShortcutSettings(QWidget):
    def __init__(self, manager, parent=None):
        super().__init__(parent)
        self.manager = manager
        layout = QVBoxLayout(self)
        margins = layout.contentsMargins()
        layout.setContentsMargins(8, margins.top(), 8, margins.bottom())
        layout.setSizeConstraint(QLayout.SetNoConstraint)
        layout.addWidget(QLabel(tr('shortcuts.title'), objectName='sectionTitle'))
        self.summary = QLabel(tr('shortcuts.summary'))
        self.summary.setWordWrap(True)
        self.summary.setTextFormat(Qt.PlainText)
        layout.addWidget(self.summary)
        self.action_grid = ShortcutGrid(self)
        layout.addWidget(self.action_grid)
        self.rows = {}
        for action, title in ACTIONS.items():
            box = QFrame(self.action_grid, objectName='card')
            row = QVBoxLayout(box)
            row.setContentsMargins(8, 6, 8, 6)
            row.setSpacing(4)
            label = ShortcutLabel()
            label.setWordWrap(True)
            label.setTextFormat(Qt.RichText)
            row.addWidget(label)
            controls = QHBoxLayout()
            edit = QPushButton()
            remove = QPushButton(tr('shortcuts.remove'))
            for button in (edit, remove):
                button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            edit.clicked.connect(lambda checked=False, a=action: self.choose(a))
            remove.clicked.connect(lambda checked=False, a=action: self.remove(a))
            controls.addWidget(edit, 0, Qt.AlignLeft)
            controls.addWidget(remove, 0, Qt.AlignLeft)
            controls.addStretch()
            row.addLayout(controls)
            self.action_grid.cards.append(box)
            self.rows[action] = (label, edit, remove)
        self.reset_button = QPushButton(tr('shortcuts.reset'))
        self.reset_button.clicked.connect(self.reset)
        layout.addWidget(self.reset_button)
        self.error = QLabel()
        self.error.setWordWrap(True)
        self.error.setTextFormat(Qt.PlainText)
        layout.addWidget(self.error)
        self.global_settings = QuickFavoriteSettings(manager.hotkey, self)
        for label in self.global_settings.findChildren(QLabel):
            label.setWordWrap(True)
        layout.addWidget(self.global_settings)
        manager.changed.connect(self.refresh)
        self.refresh()

    def refresh(self):
        for action, (label, edit, remove) in self.rows.items():
            value = self.manager.bindings[action]
            saved = self.manager.settings.value(PREFIX + action, '')
            display = QKeySequence(value).toString(QKeySequence.NativeText) if value else tr('quick_favorite.unassigned')
            title = tr(ACTIONS[action])
            detail = display
            if action in self.manager.errors:
                detail += '\n' + self.manager.errors[action]
            label.set_content(title, detail)
            edit.setText(tr('shortcuts.change' if value else 'shortcuts.set'))
            edit.setEnabled(True)
            remove.setEnabled(bool(value or saved))
        self.action_grid.reflow()
        self._fit_global_controls()

    def _fit_global_controls(self):
        if not hasattr(self, 'global_settings'):
            return
        # Presentation only: the existing global editor and callbacks stay intact.
        controls = self.global_settings.layout().itemAt(2).layout()
        needed = (self.global_settings.edit.sizeHint().width()
                  + self.global_settings.remove.sizeHint().width() + controls.spacing())
        margins = self.global_settings.layout().contentsMargins()
        outer = self.layout().contentsMargins()
        available = self.width() - outer.left() - outer.right() - margins.left() - margins.right()
        controls.setDirection(QBoxLayout.TopToBottom if available < needed else QBoxLayout.LeftToRight)

    def minimumSizeHint(self):
        if not hasattr(self, 'global_settings'):
            return super().minimumSizeHint()
        margins = self.layout().contentsMargins()
        global_margins = self.global_settings.layout().contentsMargins()
        global_width = max(self.global_settings.edit.sizeHint().width(),
                           self.global_settings.remove.sizeHint().width()) + global_margins.left() + global_margins.right()
        width = max(self.action_grid.minimumSizeHint().width(), self.reset_button.sizeHint().width(), global_width)
        return QSize(width + margins.left() + margins.right(), 0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._fit_global_controls()

    def remove(self, action):
        if not self.manager.set_binding(action, ''):
            self.error.setText(self.manager.error)
        else:
            self.error.clear()

    def reset(self):
        if QMessageBox.question(self, tr('shortcuts.title'), tr('shortcuts.reset_confirm'),
                                QMessageBox.Yes | QMessageBox.No, QMessageBox.No) != QMessageBox.Yes:
            return
        self.error.setText('' if self.manager.reset() else self.manager.error)

    def choose(self, action):
        dialog = QDialog(self)
        dialog.setWindowTitle(tr('shortcuts.title') + ' — ' + tr(ACTIONS[action]))
        layout = QVBoxLayout(dialog)
        edit = QKeySequenceEdit(QKeySequence(self.manager.bindings[action]), dialog)
        edit.setMaximumSequenceLength(1)
        layout.addWidget(edit)
        error = QLabel()
        error.setWordWrap(True)
        error.setTextFormat(Qt.PlainText)
        layout.addWidget(error)
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Save).setText(tr('favorites.save'))
        buttons.button(QDialogButtonBox.Cancel).setText(tr('planet_nav.cancel'))
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        def save():
            value = edit.keySequence().toString(QKeySequence.PortableText)
            if self.manager.set_binding(action, value):
                dialog.accept()
            else:
                error.setText(self.manager.error)

        buttons.accepted.connect(save)
        with self.manager.recording():
            dialog.exec()
