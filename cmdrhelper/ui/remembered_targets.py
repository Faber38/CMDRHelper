"""Compact, session-local destination bookmarks shared by all trade tabs."""
from PySide6.QtCore import Qt, QRectF, QEvent, QSignalBlocker
from PySide6.QtGui import QBrush, QColor, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import (QApplication, QFrame, QLabel, QVBoxLayout, QHBoxLayout, QWidget, QToolButton,
    QStyledItemDelegate, QStyle, QStyleOptionViewItem, QTableWidgetItem, QSizePolicy)
from cmdrhelper.i18n import tr
from cmdrhelper.market_data import PadSize
from cmdrhelper.trade_station_body import known_station_body
from .system_clipboard import copy_system_name


def target_identity(offer):
    return (offer.system_name, offer.station_name)


class RememberedTargets(QFrame):
    def __init__(self, parent=None, *, state=None):
        super().__init__(parent)
        self.state = state
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        self.targets = {}
        self.body_labels = {}
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        self.heading = QLabel(tr('trade.remembered_targets'))
        self.heading.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        font = self.heading.font()
        font.setBold(True)
        self.heading.setFont(font)
        layout.addWidget(self.heading)
        self.entries = {}
        self.table = None
        self.column = None
        self.is_active = lambda: True
        self.hide()

    def event(self, event):
        # Let the outer scroll area accommodate wrapped text at large font sizes.
        result = super().event(event)
        if event.type() in (QEvent.Resize, QEvent.LayoutRequest):
            layout = self.layout()
            margins = layout.contentsMargins()
            width = max(1, self.width() - margins.left() - margins.right())
            height = self.heading.sizeHint().height() + margins.top() + margins.bottom()
            for entry, label, button, copy_button in self.entries.values():
                text_width = max(1, width - button.sizeHint().width() - copy_button.sizeHint().width()
                                     - 2 * entry.layout().spacing())
                text_height = max(0, label.heightForWidth(text_width))
                label.setMinimumHeight(text_height)
                row_height = max(text_height, button.sizeHint().height(), copy_button.sizeHint().height())
                entry.setFixedHeight(row_height)
                height += layout.spacing() + row_height
            self.setFixedHeight(height)
            layout.activate()
        return result

    def bind_table(self, table, column, is_active=lambda: True):
        self.table, self.column, self.is_active = table, column, is_active

    def remove(self, key):
        self.targets.pop(key, None)
        self.body_labels.pop(key, None)
        if self.table is not None and self.is_active():
            blocker = QSignalBlocker(self.table)
            for row in range(self.table.rowCount()):
                mark = self.table.item(row, self.column)
                if mark.data(Qt.UserRole + 2) == key:
                    mark.setCheckState(Qt.Unchecked)
                    for column in range(self.table.columnCount()):
                        self.table.item(row, column).setData(Qt.UserRole + 1, False)
        self.refresh()

    def text(self):
        return '\n'.join(label.text() for _, label, _, _ in self.entries.values())

    def mark(self, offer, payload=None):
        item = QTableWidgetItem()
        item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsUserCheckable)
        item.setData(Qt.UserRole, offer if payload is None else payload)
        item.setData(Qt.UserRole + 2, target_identity(offer))
        item.setToolTip(tr('trade.remembered_targets'))
        item.setCheckState(Qt.Checked if target_identity(offer) in self.targets else Qt.Unchecked)
        return item

    def changed(self, item, offer):
        key = target_identity(offer)
        if item.checkState() == Qt.Checked:
            self.targets[key] = offer
            self.body_labels[key] = known_station_body(self.state, offer)
        else:
            table = item.tableWidget()
            if not any((other := table.item(row, item.column())) is not None
                       and other.data(Qt.UserRole + 2) == key
                       and other.checkState() == Qt.Checked
                       for row in range(table.rowCount())):
                self.targets.pop(key, None)
                self.body_labels.pop(key, None)
        self.refresh()

    def clear(self):
        self.targets.clear()
        self.body_labels.clear()
        self.refresh()

    def refresh(self):
        for key in tuple(self.entries):
            if key not in self.targets:
                entry, _, _, _ = self.entries.pop(key)
                self.layout().removeWidget(entry)
                entry.hide()
                entry.deleteLater()
        for key, offer in self.targets.items():
            pad = (tr('trade.pad_' + offer.largest_pad.value)
                   if offer.largest_pad in (PadSize.SMALL, PadSize.MEDIUM, PadSize.LARGE) else '–')
            parts = [offer.system_name]
            body = self.body_labels.get(target_identity(offer))
            if body:
                parts.append(body)
            parts.extend((offer.station_name, pad))
            if key not in self.entries:
                entry = QWidget(self)
                row = QHBoxLayout(entry)
                row.setContentsMargins(0, 0, 0, 0)
                label = QLabel()
                label.setTextFormat(Qt.PlainText)
                label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
                label.setWordWrap(True)
                copy_button = QToolButton()
                copy_button.setText('⧉')
                copy_button.setAutoRaise(True)
                copy_button.setCursor(Qt.PointingHandCursor)
                copy_button.setToolTip(tr('recommend.copy_system'))
                copy_button.setAccessibleName(tr('recommend.copy_system'))
                copy_button.clicked.connect(lambda checked=False, system=key[0]: copy_system_name(system))
                button = QToolButton()
                button.setText('✕')
                button.setAutoRaise(True)
                button.setCursor(Qt.PointingHandCursor)
                button.setToolTip(tr('trade.remove_remembered_target'))
                button.setAccessibleName(tr('trade.remove_remembered_target'))
                button.clicked.connect(lambda checked=False, target=key: self.remove(target))
                row.addWidget(label, 1)
                row.addWidget(copy_button, 0, Qt.AlignTop)
                row.addWidget(button, 0, Qt.AlignTop)
                self.layout().addWidget(entry)
                self.entries[key] = (entry, label, button, copy_button)
            self.entries[key][1].setText(' · '.join(parts))
        self.setVisible(bool(self.targets))


class RememberedTargetDelegate(QStyledItemDelegate):
    """Remembered rows remain visible independently of selection and focus."""
    def __init__(self, parent=None, column=0):
        super().__init__(parent)
        self.column = column

    def initStyleOption(self, option, index):
        super().initStyleOption(option, index)
        if index.data(Qt.ItemDataRole.UserRole + 1):
            base = option.palette.base().color()
            accent = option.palette.highlight().color()
            option.backgroundBrush = QBrush(QColor(
                *[round(base.getRgb()[i] * .8 + accent.getRgb()[i] * .2) for i in range(3)]))
            option.state &= ~QStyle.StateFlag.State_Selected

    def paint(self, painter, option, index):
        if index.column() != self.column:
            return super().paint(painter, option, index)
        option = QStyleOptionViewItem(option)
        self.initStyleOption(option, index)
        if not option.features & QStyleOptionViewItem.ViewItemFeature.HasCheckIndicator:
            return super().paint(painter, option, index)
        style = option.widget.style() if option.widget else QApplication.style()
        indicator = style.subElementRect(QStyle.SubElement.SE_ItemViewItemCheckIndicator,
                                        option, option.widget)
        # Keep the native indicator geometry, hit target and row sizing. Only
        # replace its paint; selection/focus and the remembered row stay native.
        option.features &= ~QStyleOptionViewItem.ViewItemFeature.HasCheckIndicator
        style.drawControl(QStyle.ControlElement.CE_ItemViewItem, option, painter, option.widget)
        light = option.palette.base().color().lightness() > 128
        enabled = bool(option.state & QStyle.StateFlag.State_Enabled)
        emphasized = enabled and bool(option.state & (
            QStyle.StateFlag.State_MouseOver | QStyle.StateFlag.State_HasFocus))
        checked = option.checkState == Qt.CheckState.Checked
        accent = QColor('#b47613' if light else '#ffb000')
        border = QColor('#995600' if light else '#ffc65c') if emphasized else accent
        fill = QColor('#c57a00' if light else '#ffb000')
        tick = QColor('#080d12')
        if not enabled:
            border = fill = QColor('#a0a8af' if light else '#58636d')
            tick = QColor('#edf1f5' if light else '#b8c0c8')
        painter.save()
        painter.setClipRect(option.rect)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        box = QRectF(indicator).adjusted(.5, .5, -.5, -.5)
        painter.setPen(QPen(border, 1.6 if emphasized else 1.0))
        painter.setBrush(QBrush(fill) if checked else Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(box, 1.5, 1.5)
        if checked:
            path = QPainterPath()
            path.moveTo(box.left() + box.width() * .22, box.top() + box.height() * .50)
            path.lineTo(box.left() + box.width() * .43, box.top() + box.height() * .72)
            path.lineTo(box.left() + box.width() * .80, box.top() + box.height() * .27)
            painter.setPen(QPen(tick, 1.8, Qt.PenStyle.SolidLine,
                                Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
            painter.drawPath(path)
        painter.restore()
