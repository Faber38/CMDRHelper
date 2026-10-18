"""Passive GUI-thread observation. No IO, repaint requests or retained model data."""
from datetime import datetime, timezone
from itertools import islice
import platform

import PySide6
from PySide6.QtCore import QObject, QEvent, QThread, qVersion
from PySide6.QtGui import QFontInfo, QPalette
from PySide6.QtWidgets import QApplication, QStyle, QStyleOptionViewItem

from cmdrhelper.odyssey_carrier import CARRIER_CATEGORIES, material_amounts
from cmdrhelper.odyssey_display_diagnostics import COUNTER_LIMIT, ROW_LIMIT, export_snapshot
from cmdrhelper.version import __version__


def _size(size):
    return dict(width=size.width(), height=size.height())


def _rect(rect):
    return dict(x=rect.x(), y=rect.y(), **_size(rect.size()))


def _scroll(bar):
    return dict(value=bar.value(), minimum=bar.minimum(), maximum=bar.maximum(), page_step=bar.pageStep())


class OdysseyDisplayDiagnostics(QObject):
    def __init__(self, view):
        super().__init__(view)
        self.view = view
        self.snapshot = None
        self.events = dict(resize=0, scroll=0, paint=0, viewport_update_requests=0, geometry_changes=0)
        tree = view.tree
        self.viewport = tree.viewport()
        tree.installEventFilter(self)
        self.viewport.installEventFilter(self)
        for bar in (tree.horizontalScrollBar(), tree.verticalScrollBar()):
            bar.valueChanged.connect(lambda *_: self._increment('scroll'))
        tree.header().sectionResized.connect(lambda *_: self._increment('geometry_changes'))
        tree.header().sectionMoved.connect(lambda *_: self._increment('geometry_changes'))
        tree.header().geometriesChanged.connect(lambda *_: self._increment('geometry_changes'))
        tree.model().rowsInserted.connect(lambda *_: self._increment('geometry_changes'))
        tree.model().rowsRemoved.connect(lambda *_: self._increment('geometry_changes'))
        tree.expanded.connect(lambda *_: self._increment('geometry_changes'))
        tree.collapsed.connect(lambda *_: self._increment('geometry_changes'))
        for name in ('commanderIdentityChanged', 'viewedCommanderChanged'):
            signal = getattr(view.state, name, None)
            if signal is not None:
                signal.connect(self.invalidate)

    def _increment(self, key):
        self.events[key] = min(COUNTER_LIMIT, self.events[key] + 1)

    def eventFilter(self, watched, event):
        kind = event.type()
        if kind == QEvent.Type.Resize:
            self._increment('resize')
            self._increment('geometry_changes')
        elif watched is self.viewport:
            if kind == QEvent.Type.Paint:
                self._increment('paint')
            elif kind in (QEvent.Type.UpdateRequest, QEvent.Type.UpdateLater):
                self._increment('viewport_update_requests')
        return False

    def invalidate(self, *_):
        if self.snapshot is not None:
            self.snapshot = dict(status='invalidated', created_at=self.snapshot.get('created_at'))

    def capture(self):
        # Called before navigation hides the existing view, never from a worker.
        if QThread.currentThread() != self.thread():
            raise RuntimeError('Odyssey diagnostics require the GUI thread')
        if not self.view.isVisible():
            return
        if self.view._loading:
            self.invalidate()
            return
        try:
            self.snapshot = self._capture()
        except Exception:
            # Diagnosis must not break navigation or leak raw Qt/model exceptions.
            self.snapshot = {'status': 'capture_failed'}

    def _capture(self):
        view, tree = self.view, self.view.tree
        window = view.window()
        handle = window.windowHandle()
        screen = handle.screen() if handle is not None else window.screen()
        font = QFontInfo(tree.font())
        environment = dict(os=platform.system() if platform.system() in ('Linux', 'Windows', 'Darwin') else 'other',
            app_version=__version__, python_version=platform.python_version(), qt_version=qVersion(),
            pyside_version=PySide6.__version__, platform_plugin=QApplication.platformName(),
            theme='light' if view.row_delegate.light else 'dark', font_family=font.family(),
            font_point_size=max(0, font.pointSizeF()), font_pixel_size=max(0, font.pixelSize()),
            window_logical_size=_size(window.size()), window_dpr=window.devicePixelRatioF(),
            screen_available=screen is not None)
        if screen is not None:
            environment.update(screen_logical_geometry=_rect(screen.geometry()),
                screen_available_logical_geometry=_rect(screen.availableGeometry()),
                screen_dpr=screen.devicePixelRatio(), logical_dpi_x=screen.logicalDotsPerInchX(),
                logical_dpi_y=screen.logicalDotsPerInchY(), physical_dpi_x=screen.physicalDotsPerInchX(),
                physical_dpi_y=screen.physicalDotsPerInchY())
        header, fm = tree.header(), tree.fontMetrics()
        table = dict(widget_logical_size=_size(tree.size()), viewport_logical_size=_size(tree.viewport().size()),
            column_widths_logical=[tree.columnWidth(i) for i in range(7)],
            column_visual_order=[header.logicalIndex(i) for i in range(7)],
            columns_hidden=[tree.isColumnHidden(i) for i in range(7)],
            visible_row_heights_logical=[], row_heights_truncated=False,
            font_height_logical=fm.height(), font_ascent_logical=fm.ascent(), font_descent_logical=fm.descent(),
            digit_width_logical=fm.horizontalAdvance('0'),
            horizontal_scroll=_scroll(tree.horizontalScrollBar()), vertical_scroll=_scroll(tree.verticalScrollBar()),
            delegate='OdysseyRowDelegate' if type(tree.itemDelegate()).__name__ == 'OdysseyRowDelegate' else 'other',
            selected_rows=len(tree.selectionModel().selectedRows()),
            hovered_row=view.row_delegate.hovered.isValid(), pointer_inside=view.row_delegate._inside,
            visible_summary_rows=0, visible_detail_rows=0, visible_single_rows=0,
            palette_base=tree.palette().color(QPalette.ColorRole.Base).name(),
            palette_text=tree.palette().color(QPalette.ColorRole.Text).name())
        counts = dict.fromkeys(('numeric', 'zero', 'dash', 'empty', 'unknown', 'omitted_detail', 'not_applicable',
                               'other_text', 'potentially_elided', 'projection_mismatch',
                               'rows_examined', 'cells_examined'), 0)
        def examine(item, expected, kind, carrier_applicable):
            counts['rows_examined'] += 1
            rect = tree.visualItemRect(item)
            visible = not rect.isEmpty() and rect.intersects(tree.viewport().rect())
            if visible:
                table['visible_' + kind + '_rows'] += 1
                if len(table['visible_row_heights_logical']) < 256:
                    table['visible_row_heights_logical'].append(rect.height())
                else:
                    table['row_heights_truncated'] = True
            for column, value in enumerate(expected, 1):
                text = item.text(column)
                counts['cells_examined'] += 1
                numeric = text.isascii() and text.isdecimal()
                counts['numeric' if numeric else 'dash' if text == '—' else 'empty' if text == '' else 'other_text'] += 1
                if numeric and not text.strip('0'):
                    counts['zero'] += 1
                if value is None:
                    counts['omitted_detail' if kind == 'detail' and column in (3, 4)
                           else 'not_applicable' if column == 3 and not carrier_applicable else 'unknown'] += 1
                if text != ('—' if value is None else str(value)):
                    counts['projection_mismatch'] += 1
                if numeric and not tree.isColumnHidden(column):
                    index = tree.indexFromItem(item, column)
                    option = QStyleOptionViewItem()
                    option.initFrom(tree)
                    option.rect = tree.visualRect(index)
                    tree.itemDelegate().initStyleOption(option, index)
                    # Hidden/collapsed rows have no valid paint rectangle: no claim.
                    if option.rect.width() > 0:
                        text_rect = tree.style().subElementRect(QStyle.SubElement.SE_ItemViewItemText, option, tree)
                        if option.fontMetrics.horizontalAdvance(text) > max(0, text_rect.width()):
                            counts['potentially_elided'] += 1
        for identity, item in islice(getattr(view, 'summaries', {}).items(), ROW_LIMIT):
            examine(item, material_amounts(view.inventory, *identity, capacity_state=view._capacity),
                    'summary', identity[0] in CARRIER_CATEGORIES)
        inspected = 0
        for row in islice(view.rows, ROW_LIMIT):
            inspected += 1
            if counts['rows_examined'] >= ROW_LIMIT:
                break
            item = view.items.get(row.key)
            if item is None:
                continue
            detail = item.parent() is not None
            values = ((row.stock.locker, row.stock.backpack, None, None) if detail else
                      material_amounts(view.inventory, row.key.category, row.key.name, capacity_state=view._capacity))
            examine(item, values, 'detail' if detail else 'single', row.key.category in CARRIER_CATEGORIES)
        return dict(status='valid', created_at=datetime.now(timezone.utc).isoformat(),
                    environment=environment, table=table, stock_cells=counts, events=dict(self.events),
                    scan_truncated=(inspected < len(view.rows) or
                                    counts['rows_examined'] < len(view.items) + len(getattr(view, 'summaries', {}))))

    def export(self):
        return export_snapshot(self.snapshot)
