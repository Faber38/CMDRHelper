"""Local commodity selection: a responsive, painted grid, without network/state IO."""
import math

from PySide6.QtCore import QAbstractListModel, QModelIndex, QPointF, QSize, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPen, QTextLayout, QTextOption
from PySide6.QtWidgets import (
    QAbstractItemView, QDialog, QDialogButtonBox, QLabel, QLineEdit, QListView,
    QPushButton, QStyle, QStyledItemDelegate, QVBoxLayout,
)

from cmdrhelper.commodity_master import all_commodities, lookup_by_id
from cmdrhelper.commodity_localization import commodity_name
from cmdrhelper.i18n import tr


COMMODITY_ID_ROLE = Qt.ItemDataRole.UserRole
CHOSEN_ROLE = Qt.ItemDataRole.UserRole + 1


class CommodityModel(QAbstractListModel):
    def __init__(self, selected_id=None, parent=None):
        super().__init__(parent)
        self.selected_id = selected_id
        # Derived display/search data only; the master remains the sole catalogue.
        self.entries = sorted(
            ((item, commodity_name(item)) for item in all_commodities()),
            key=lambda entry: entry[1].casefold(),
        )
        self.search_terms = [' '.join((name, item.english_name, item.symbol)).casefold()
                             for item, name in self.entries]
        self.rows = list(range(len(self.entries)))

    def rowCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self.rows)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or not 0 <= index.row() < len(self.rows):
            return None
        item, name = self.entries[self.rows[index.row()]]
        if role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.AccessibleTextRole):
            return name
        if role == Qt.ItemDataRole.ToolTipRole:
            return f'{name}\n{item.english_name} · {item.symbol}'
        if role == COMMODITY_ID_ROLE:
            return item.frontier_id
        if role == CHOSEN_ROLE:
            return item.frontier_id == self.selected_id
        return None

    def filter(self, text):
        needle = text.strip().casefold()
        self.beginResetModel()
        self.rows = [i for i, terms in enumerate(self.search_terms) if needle in terms]
        self.endResetModel()

    def index_for_id(self, commodity_id):
        for row, entry in enumerate(self.rows):
            if self.entries[entry][0].frontier_id == commodity_id:
                return self.index(row)
        return QModelIndex()


def text_layout(text, font, width):
    layout = QTextLayout(text, font)
    options = QTextOption(Qt.AlignmentFlag.AlignHCenter)
    options.setWrapMode(QTextOption.WrapMode.WrapAtWordBoundaryOrAnywhere)
    layout.setTextOption(options)
    height = 0
    layout.beginLayout()
    while True:
        line = layout.createLine()
        if not line.isValid():
            break
        line.setLineWidth(max(1, width))
        line.setPosition(QPointF(0, height))
        height += line.height()
    layout.endLayout()
    return layout, math.ceil(height)


class CommodityTileDelegate(QStyledItemDelegate):
    MARGIN = 4
    PADDING = 9

    def paint(self, painter, option, index):
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        tile = option.rect.adjusted(self.MARGIN, self.MARGIN, -self.MARGIN, -self.MARGIN)
        palette = option.palette
        light = palette.window().color().lightness() > 128
        background = QColor('#f7f9fb' if light else '#111820')
        chosen = bool(index.data(CHOSEN_ROLE))
        focused = bool(option.state & QStyle.StateFlag.State_HasFocus)
        hovered = bool(option.state & QStyle.StateFlag.State_MouseOver)
        if chosen:
            background = QColor('#f4e6c9' if light else '#322817')
        elif hovered or option.state & QStyle.StateFlag.State_Selected:
            background = QColor('#fff3db' if light else '#23271e')
        painter.setBrush(background)
        painter.setPen(QPen(QColor('#b47613' if light else '#ad7927'), 1))
        painter.drawRoundedRect(tile, 4, 4)
        if chosen:
            painter.fillRect(tile.left() + 1, tile.top() + 5, 3, max(0, tile.height() - 10), QColor('#c57a00'))
        if focused:
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(QPen(QColor('#995600' if light else '#ffc65c'), 1, Qt.PenStyle.DashLine))
            painter.drawRoundedRect(tile.adjusted(3, 3, -3, -3), 3, 3)
        painter.setPen(palette.windowText().color())
        inner = tile.adjusted(self.PADDING, self.PADDING, -self.PADDING, -self.PADDING)
        layout, height = text_layout(index.data(), option.font, inner.width())
        painter.setClipRect(inner)
        layout.draw(painter, QPointF(inner.left(), inner.top() + (inner.height() - height) / 2))
        painter.restore()

    def sizeHint(self, option, index):
        return self.parent().gridSize()


class CommodityGrid(QListView):
    chooseRequested = Signal(QModelIndex)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.columns = 1
        self.setViewMode(QListView.ViewMode.IconMode)
        self.setFlow(QListView.Flow.LeftToRight)
        self.setWrapping(True)
        self.setResizeMode(QListView.ResizeMode.Adjust)
        self.setMovement(QListView.Movement.Static)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setUniformItemSizes(True)
        self.setSpacing(0)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        # Reserve the scrollbar width to avoid column reflow at the overflow threshold.
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.setMouseTracking(True)
        self.setItemDelegate(CommodityTileDelegate(self))
        self.clicked.connect(self.chooseRequested)

    def reflow(self):
        model = self.model()
        if model is None:
            return
        width = max(1, self.viewport().width())
        target = max(170, self.fontMetrics().horizontalAdvance('M') * 16)
        self.columns = max(1, min(6, width // target))
        # QListView wraps at an exact right-edge boundary; leave one pixel spare.
        cell_width = max(1, (width - 1) // self.columns)
        inset = 2 * (CommodityTileDelegate.MARGIN + CommodityTileDelegate.PADDING)
        # Measure the whole local catalogue, so filtering never makes tile heights jump.
        text_height = max(text_layout(name, self.font(), cell_width - inset)[1]
                          for _item, name in model.entries)
        size = QSize(cell_width, max(self.fontMetrics().height() * 2, text_height) + inset)
        if self.gridSize() != size:
            self.setGridSize(size)
            self.doItemsLayout()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.reflow()

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Space):
            if self.currentIndex().isValid():
                self.chooseRequested.emit(self.currentIndex())
            event.accept()
            return
        super().keyPressEvent(event)

    def focusInEvent(self, event):
        super().focusInEvent(event)
        # Mouse focus arrives before QListView resolves the pressed index.
        # Scrolling to the old selection here moves another tile under the
        # pointer. Only keyboard focus should reveal/initialize that selection.
        if event.reason() not in (Qt.FocusReason.TabFocusReason, Qt.FocusReason.BacktabFocusReason,
                                  Qt.FocusReason.ShortcutFocusReason):
            return
        if not self.currentIndex().isValid() and self.model().rowCount():
            self.setCurrentIndex(self.model().index(0))
        self.scrollTo(self.currentIndex())


class CommodityPicker(QDialog):
    def __init__(self, selected_id=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr('trade.commodity'))
        self.commodity_id = selected_id
        layout = QVBoxLayout(self)
        self.search = QLineEdit()
        self.search.setPlaceholderText(tr('trade.commodity_search'))
        self.search.setAccessibleName(tr('trade.commodity_search'))
        self.search.setClearButtonEnabled(True)
        layout.addWidget(self.search)
        self.model = CommodityModel(selected_id, self)
        self.grid = CommodityGrid()
        self.grid.setAccessibleName(tr('trade.commodity'))
        self.grid.setModel(self.model)
        layout.addWidget(self.grid, 1)
        self.empty = QLabel(tr('trade.no_commodity_matches'))
        self.empty.setWordWrap(True)
        self.empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty.hide()
        layout.addWidget(self.empty)
        self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel)
        cancel = self.buttons.button(QDialogButtonBox.StandardButton.Cancel)
        cancel.setText(tr('trade.cancel'))
        cancel.setAutoDefault(False)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)
        self.search.textChanged.connect(self._filter)
        self.grid.chooseRequested.connect(self._choose)
        self.setTabOrder(self.search, self.grid)
        self.setTabOrder(self.grid, cancel)
        available = (parent.screen() if parent else self.screen()).availableGeometry()
        self.setMinimumSize(min(300, available.width()), min(240, available.height()))
        self.resize(min(1100, available.width() - 32), min(720, available.height() - 64))
        self.move(available.center() - self.rect().center())
        self.grid.setCurrentIndex(self.model.index_for_id(selected_id))

    def showEvent(self, event):
        super().showEvent(event)
        self.grid.reflow()
        self.grid.scrollTo(self.grid.currentIndex())
        self.search.setFocus(Qt.FocusReason.OtherFocusReason)

    def _filter(self, text):
        self.model.filter(text)
        empty = self.model.rowCount() == 0
        self.empty.setVisible(empty)
        self.grid.setVisible(not empty)
        self.grid.setCurrentIndex(self.model.index_for_id(self.commodity_id))
        if not empty:
            self.grid.reflow()
            self.grid.scrollToTop()

    def _choose(self, index):
        if index.isValid():
            self.commodity_id = index.data(COMMODITY_ID_ROLE)
            self.accept()


class CommodityField(QPushButton):
    """One field in the trade form; commit selection only on dialog acceptance."""
    commodityChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._commodity_id = None
        self._picker = None
        self.setStyleSheet('text-align: left;')
        self._update_text()
        self.clicked.connect(self.open_picker)

    def currentData(self):
        return self._commodity_id

    def currentText(self):
        item = lookup_by_id(self._commodity_id)
        return commodity_name(item) if item else tr('trade.choose_commodity')

    def set_commodity(self, commodity_id):
        if commodity_id is not None and lookup_by_id(commodity_id) is None:
            return False
        if self._commodity_id != commodity_id:
            self._commodity_id = commodity_id
            self._update_text()
            self.commodityChanged.emit()
        return True

    def _update_text(self):
        text = self.currentText()
        self.setText(text.replace('&', '&&') + '  ▾')
        self.setAccessibleName(tr('trade.commodity') + ': ' + text)

    def open_picker(self):
        if self._picker is not None:
            self._picker.raise_()
            return
        self._picker = CommodityPicker(self._commodity_id, self)
        self._picker.finished.connect(self._picker_finished)
        self._picker.open()

    def _picker_finished(self, result):
        picker = self._picker
        self._picker = None
        if result == QDialog.DialogCode.Accepted:
            self.set_commodity(picker.commodity_id)
        picker.deleteLater()
        self.setFocus(Qt.FocusReason.OtherFocusReason)
