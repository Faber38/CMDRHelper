from __future__ import annotations

from datetime import datetime
from pathlib import Path
import os
import re

from cmdrhelper.ui.system_view import SystemMapWidget
from cmdrhelper.bio_valuation import base_value, species_name
from cmdrhelper.ui.body_detail_window import BodyDetailWindow
from cmdrhelper.ui.chronicle_view import ChronicleMapWidget
from cmdrhelper.ui.screenshot_view import ScreenshotView
from cmdrhelper.online_services import (
    test_edsm_connection,
    test_inara_connection,
)
from cmdrhelper.version import __version__
from cmdrhelper.update import (
    UpdateCheckWorker,
    is_newer_version,
    download_release,
    launch_installer,
)

from PySide6.QtCore import Qt, QTimer, QThreadPool, QUrl, QRectF, Signal
from cmdrhelper.ui.styles import DARK_STYLESHEET, LIGHT_STYLESHEET
from PySide6.QtGui import (
    QDesktopServices,
    QPainter,
    QColor,
    QPen,
    QBrush,
    QFont,
    QFontDatabase,
)

from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QPushButton,
    QFrame,
    QStackedWidget,
    QFileDialog,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QListWidget,
    QListWidgetItem,
    QFormLayout,
    QLineEdit,
    QScrollArea,
    QSplitter,
    QMessageBox,
    QCheckBox,
    QRadioButton,
    QButtonGroup,
    QApplication,
    QDialog,
    QProgressBar,
    QTabWidget,
    QSpinBox,
    QFontComboBox,
)


class ChronicleSystemWindow(QDialog):
    def __init__(self, system_name, bodies, header_text, body_callback, parent=None):
        super().__init__(parent)

        self.setWindowTitle(f"CMDRHelper – Chronik – {system_name}")
        self.resize(1250, 760)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(6)

        title = QLabel(system_name, objectName="sectionTitle")
        title.setStyleSheet("font-size: 18px; font-weight: 700;")
        layout.addWidget(title)

        info = QLabel(header_text, objectName="muted")
        info.setWordWrap(True)
        layout.addWidget(info)

        self.system_map = SystemMapWidget()
        self.system_map.bodyClicked.connect(body_callback)
        self.system_map.set_system(system_name, bodies)

        scroll = QScrollArea()
        scroll.setWidgetResizable(False)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setWidget(self.system_map)

        layout.addWidget(scroll, 1)

        buttons = QHBoxLayout()
        buttons.addStretch()

        close = QPushButton("Schließen")
        close.clicked.connect(self.close)
        buttons.addWidget(close)

        layout.addLayout(buttons)


class ChronicleSearchHelpDialog(QDialog):
    """
    Kompakte Suchhilfe für die Chronik.

    Kategorien sind einzeln aufklappbar. Ein Klick auf einen Begriff
    übernimmt ihn in die Chronik-Suche und startet die Suche direkt.
    """

    def __init__(self, groups, on_term_clicked, parent=None):
        super().__init__(parent)

        self._on_term_clicked = on_term_clicked
        self._groups = groups or {}

        self.setWindowTitle("CMDRHelper – Suchhilfe / Legende")
        self.resize(720, 620)

        root = QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(6)

        title = QLabel("Suchhilfe / Legende", objectName="sectionTitle")
        title.setStyleSheet("font-size: 16px; font-weight: 700;")
        root.addWidget(title)

        intro = QLabel(
            "Kategorien aufklappen und einen Begriff anklicken. "
            "Der Begriff wird direkt in die Chronik-Suche übernommen."
        )
        intro.setObjectName("muted")
        intro.setWordWrap(True)
        root.addWidget(intro)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        content = QWidget()
        self.content_layout = QVBoxLayout(content)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(4)

        for group_name, terms in self._groups.items():
            self._add_group(
                group_name,
                terms,
            )

        self.content_layout.addStretch()
        scroll.setWidget(content)
        root.addWidget(scroll, 1)

        buttons = QHBoxLayout()
        buttons.addStretch()

        close = QPushButton("Schließen")
        close.clicked.connect(self.close)
        buttons.addWidget(close)

        root.addLayout(buttons)

    def _add_group(self, group_name, terms):
        terms = [str(term) for term in (terms or []) if str(term).strip()]

        header = QPushButton(f"▸  {group_name}   ({len(terms)})")
        header.setCheckable(True)
        header.setStyleSheet("text-align:left; padding:5px 8px; font-weight:700;")

        body = QFrame()
        body.setVisible(False)

        grid = QGridLayout(body)
        grid.setContentsMargins(8, 4, 8, 6)
        grid.setHorizontalSpacing(5)
        grid.setVerticalSpacing(4)

        # Kompakter als die bisherige Darstellung.
        columns = 4

        for index, term in enumerate(terms):
            button = QPushButton(term)
            button.setToolTip(f"Nach „{term}“ suchen")
            button.setMinimumHeight(24)
            button.setStyleSheet("padding:2px 6px; text-align:left;")
            button.clicked.connect(
                lambda checked=False, value=term: self._term_clicked(value)
            )

            row = index // columns
            col = index % columns

            grid.addWidget(
                button,
                row,
                col,
            )

        header.toggled.connect(
            lambda checked, button=header, frame=body, title=group_name, count=len(
                terms
            ): self._toggle_group(
                button,
                frame,
                title,
                count,
                checked,
            )
        )

        self.content_layout.addWidget(header)
        self.content_layout.addWidget(body)

    def _toggle_group(
        self,
        button,
        frame,
        title,
        count,
        checked,
    ):
        frame.setVisible(bool(checked))

        button.setText(
            (f"▾  {title}   ({count})" if checked else f"▸  {title}   ({count})")
        )

    def _term_clicked(self, term):
        if callable(self._on_term_clicked):
            self._on_term_clicked(str(term))


class SystemOverviewMiniMap(QWidget):
    bodyClicked = Signal(object)

    def __init__(self, source_map, parent=None):
        super().__init__(parent)

        self.source_map = source_map
        self._click_rects = []

        self.setMinimumSize(600, 420)
        self.setMouseTracking(True)

    def paintEvent(self, event):
        painter = QPainter(self)

        try:
            painter.setRenderHint(
                QPainter.Antialiasing,
                True,
            )

            painter.fillRect(
                self.rect(),
                QColor("#080d12"),
            )

            self._click_rects = []

            if self.source_map is None or not self.source_map.bodies:
                painter.setPen(QColor("#8e969e"))
                painter.drawText(
                    self.rect(),
                    Qt.AlignCenter,
                    "Keine Systemdaten verfügbar.",
                )
                return

            (
                positions,
                children,
                _families,
                _used_units,
                _depth_count,
            ) = self.source_map._tree_layout()

            if not positions:
                return

            left = min(pos["x"] for pos in positions.values())
            top = min(pos["y"] for pos in positions.values())
            right = max(pos["x"] + self.source_map.BODY_W for pos in positions.values())
            bottom = max(
                pos["y"] + self.source_map.BODY_H for pos in positions.values()
            )

            source_w = max(
                1.0,
                right - left,
            )
            source_h = max(
                1.0,
                bottom - top,
            )

            margin = 22.0

            scale = min(
                max(
                    0.01,
                    (self.width() - margin * 2) / source_w,
                ),
                max(
                    0.01,
                    (self.height() - margin * 2) / source_h,
                ),
            )

            offset_x = (self.width() - source_w * scale) / 2.0

            offset_y = (self.height() - source_h * scale) / 2.0

            def map_point(x, y):
                return (
                    offset_x + (x - left) * scale,
                    offset_y + (y - top) * scale,
                )

            # Zuerst die Parent-/Child-Verbindungen zeichnen.
            painter.setPen(
                QPen(
                    QColor("#7f8993"),
                    max(1.0, 1.2 * scale),
                )
            )

            for parent_pos in positions.values():
                parent = parent_pos["body"]

                direct_children = [
                    child
                    for child in children.get(
                        parent.get("body_id"),
                        [],
                    )
                    if id(child) in positions
                ]

                if not direct_children:
                    continue

                px_raw = parent_pos["x"] + self.source_map.BODY_W / 2
                py_raw = parent_pos["y"] + self.source_map.BODY_H

                child_centers_raw = [
                    (positions[id(child)]["x"] + self.source_map.BODY_W / 2)
                    for child in direct_children
                ]

                child_tops_raw = [
                    positions[id(child)]["y"] for child in direct_children
                ]

                nearest_top = min(child_tops_raw)

                bus_y_raw = py_raw + (nearest_top - py_raw) * 0.45

                px, py = map_point(
                    px_raw,
                    py_raw,
                )
                _, bus_y = map_point(
                    px_raw,
                    bus_y_raw,
                )

                painter.drawLine(
                    int(px),
                    int(py),
                    int(px),
                    int(bus_y),
                )

                if len(child_centers_raw) > 1:
                    left_x, _ = map_point(
                        min(child_centers_raw),
                        bus_y_raw,
                    )
                    right_x, _ = map_point(
                        max(child_centers_raw),
                        bus_y_raw,
                    )

                    painter.drawLine(
                        int(left_x),
                        int(bus_y),
                        int(right_x),
                        int(bus_y),
                    )

                for child in direct_children:
                    child_pos = positions[id(child)]

                    cx_raw = child_pos["x"] + self.source_map.BODY_W / 2
                    cy_raw = child_pos["y"]

                    cx, cy = map_point(
                        cx_raw,
                        cy_raw,
                    )

                    if len(child_centers_raw) == 1 and abs(cx_raw - px_raw) > 1:
                        painter.drawLine(
                            int(px),
                            int(bus_y),
                            int(cx),
                            int(bus_y),
                        )

                    painter.drawLine(
                        int(cx),
                        int(bus_y),
                        int(cx),
                        int(cy),
                    )

            # Körper als kompakte Miniatur-Symbole.
            for pos in sorted(
                positions.values(),
                key=lambda item: (
                    item["level"],
                    item["x"],
                ),
            ):
                body = pos["body"]

                center_raw_x = pos["x"] + self.source_map.BODY_W / 2
                center_raw_y = pos["y"] + 44

                cx, cy = map_point(
                    center_raw_x,
                    center_raw_y,
                )

                is_star = bool(body.get("star_type") or body.get("body_type") == "Star")

                is_belt = self.source_map._is_belt_cluster(body)

                if is_star:
                    radius = max(
                        7.0,
                        min(
                            18.0,
                            15.0 * scale + 5.0,
                        ),
                    )
                elif is_belt:
                    radius = max(
                        3.0,
                        min(
                            7.0,
                            5.0 * scale + 2.0,
                        ),
                    )
                else:
                    radius = max(
                        4.0,
                        min(
                            11.0,
                            8.0 * scale + 3.0,
                        ),
                    )

                body_color = self.source_map._body_color(body)

                bio_count = int(body.get("biological_signals") or 0)

                geo_count = int(body.get("geological_signals") or 0)

                if bio_count > 0:
                    outline = QColor("#39ff56")
                elif geo_count > 0:
                    outline = QColor("#28c9e8")
                elif body.get("high_value"):
                    outline = QColor("#ffb000")
                else:
                    outline = QColor("#d9dde1")

                painter.setPen(
                    QPen(
                        outline,
                        2,
                    )
                )

                painter.setBrush(QBrush(body_color))

                if is_belt:
                    painter.drawEllipse(
                        QRectF(
                            cx - radius * 1.7,
                            cy - radius * 0.55,
                            radius,
                            radius,
                        )
                    )
                    painter.drawEllipse(
                        QRectF(
                            cx - radius * 0.4,
                            cy - radius,
                            radius * 1.2,
                            radius * 1.2,
                        )
                    )
                    painter.drawEllipse(
                        QRectF(
                            cx + radius * 0.8,
                            cy - radius * 0.4,
                            radius * 0.85,
                            radius * 0.85,
                        )
                    )
                else:
                    painter.drawEllipse(
                        QRectF(
                            cx - radius,
                            cy - radius,
                            radius * 2,
                            radius * 2,
                        )
                    )

                # Größerer unsichtbarer Klickbereich als das Miniatursymbol.
                click_r = max(
                    10.0,
                    radius + 5.0,
                )

                self._click_rects.append(
                    (
                        QRectF(
                            cx - click_r,
                            cy - click_r,
                            click_r * 2,
                            click_r * 2,
                        ),
                        body,
                    )
                )

        finally:
            # Wichtig: QPainter immer sauber beenden.
            painter.end()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            point = event.position()

            for rect, body in self._click_rects:
                if rect.contains(point):
                    self.bodyClicked.emit(body)
                    return

        super().mousePressEvent(event)


class SystemOverviewDialog(QDialog):
    """Sichere Miniaturübersicht ohne Rendern eines bereits sichtbaren Widgets."""

    def __init__(
        self,
        system_name,
        bodies,
        source_map,
        on_body_clicked=None,
        parent=None,
    ):
        super().__init__(parent)

        self.system_name = system_name or ""

        self.setWindowTitle(f"CMDRHelper – Alles anzeigen – {self.system_name}")

        self.resize(
            1050,
            720,
        )

        root = QVBoxLayout(self)
        root.setContentsMargins(
            10,
            10,
            10,
            10,
        )
        root.setSpacing(6)

        title = QLabel(
            self.system_name,
            objectName="sectionTitle",
        )
        title.setStyleSheet("font-size: 17px; font-weight: 700;")
        root.addWidget(title)

        hint = QLabel(
            "Komplette Systemstruktur in Miniatur · "
            "Klick auf einen Körper springt in der Hauptkarte dorthin.",
            objectName="muted",
        )
        hint.setWordWrap(True)
        root.addWidget(hint)

        self.preview = SystemOverviewMiniMap(
            source_map=source_map,
            parent=self,
        )

        if callable(on_body_clicked):
            self.preview.bodyClicked.connect(on_body_clicked)

        root.addWidget(
            self.preview,
            1,
        )

        buttons = QHBoxLayout()
        buttons.addStretch()

        close = QPushButton("Schließen")
        close.clicked.connect(self.close)
        buttons.addWidget(close)

        root.addLayout(buttons)


class ExplorerLiveListWindow(QDialog):
    """Kleines frei positionierbares Live-Fenster für Explorer-Hinweise."""

    def __init__(self, title, headers, settings, geometry_key, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.geometry_key = geometry_key
        self.setWindowTitle(title)
        self.setWindowFlags(self.windowFlags() | Qt.Window)
        self.resize(620, 260)

        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(5)

        self.system_label = QLabel("–", objectName="sectionTitle")
        self.system_label.setStyleSheet("font-size: 14px; font-weight: 700;")
        root.addWidget(self.system_label)

        self.table = QTableWidget(0, len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setStretchLastSection(True)
        root.addWidget(self.table, 1)

        geometry = self.settings.value(self.geometry_key)
        if geometry is not None:
            try:
                self.restoreGeometry(geometry)
            except Exception:
                pass

    def _save_geometry(self):
        self.settings.setValue(self.geometry_key, self.saveGeometry())
        self.settings.sync()

    def moveEvent(self, event):
        super().moveEvent(event)
        self._save_geometry()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._save_geometry()

    def closeEvent(self, event):
        self._save_geometry()
        super().closeEvent(event)

    def set_rows(self, system_name, rows):
        self.system_label.setText(system_name or "–")
        self.table.setRowCount(len(rows))
        for row_index, row_values in enumerate(rows):
            for col, value in enumerate(row_values):
                item = QTableWidgetItem(str(value))
                self.table.setItem(row_index, col, item)


class MainWindow(QMainWindow):
    def __init__(self, state):
        super().__init__()

        self.state = state
        self.nav_buttons = []

        self.update_thread_pool = QThreadPool.globalInstance()
        self._update_check_running = False
        self._update_notice_shown = False
        self._update_worker = None
        self._chronicle_system_window = None
        self._chronicle_search_help_window = None
        self._system_overview_window = None
        self._explorer_value_live_window = None
        self._explorer_bio_live_window = None
        self._explorer_live_system = None
        self.ui_theme = str(self.state.settings.value("ui_theme", "dark")).lower()

        # Gespeicherte Anwendungsschrift bereits vor dem Aufbau der
        # Oberfläche anwenden, damit alle Widgets sofort korrekt erscheinen.
        self._apply_saved_ui_font()

        self.setWindowTitle(f"CMDRHelper {__version__}")

        self._build_ui()

        self.state.changed.connect(self.refresh_all)

        self.refresh_all()

        # Updateprüfung bewusst leicht verzögert starten, damit das
        # Hauptfenster zuerst vollständig erscheinen kann.
        QTimer.singleShot(1500, lambda: self._check_for_updates(automatic=True))

    def _nav(self, text, idx):
        button = QPushButton(text)

        button.clicked.connect(lambda: self._show_page(idx))

        self.nav_buttons.append(button)

        return button

    def _show_page(self, idx):
        self.pages.setCurrentIndex(idx)

        for i, button in enumerate(self.nav_buttons):
            button.setObjectName("navActive" if i == idx else "")

            button.style().unpolish(button)
            button.style().polish(button)

    def _card(self, title):
        frame = QFrame(objectName="card")

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(10, 4, 10, 4)

        layout.addWidget(QLabel(title, objectName="sectionTitle"))

        return frame, layout

    def _build_ui(self):
        root = QWidget()
        self.setCentralWidget(root)

        main = QHBoxLayout(root)
        main.setContentsMargins(0, 0, 0, 0)
        main.setSpacing(0)

        side_frame = QFrame(objectName="sidebar")

        side_frame.setFixedWidth(210)

        side = QVBoxLayout(side_frame)
        side.setContentsMargins(12, 12, 12, 12)

        side.addWidget(QLabel("✦  CMDRHelper", objectName="appTitle"))

        side.addWidget(
            QLabel("Dein Missions- & Explorer-Tool", objectName="appSubTitle")
        )

        side.addSpacing(20)

        side.addWidget(self._nav("⌂  Übersicht", 0))

        side.addWidget(self._nav("◎  Missionen", 1))

        side.addWidget(self._nav("✦  Explorer", 2))

        side.addWidget(self._nav("↝  Chronik", 3))

        side.addWidget(self._nav("▣  Bilder", 4))

        side.addWidget(self._nav("⚙  Einstellungen", 5))

        side.addStretch()

        exit_button = QPushButton("⏻  Beenden")
        exit_button.setToolTip("CMDRHelper beenden")
        exit_button.clicked.connect(self.close)
        side.addWidget(exit_button)

        side.addSpacing(10)

        self.sidebar_system = QLabel("Aktuelles System\n–")
        self.sidebar_system.setWordWrap(True)
        side.addWidget(self.sidebar_system)

        self.sidebar_body = QLabel("", objectName="muted")
        self.sidebar_body.setWordWrap(True)
        side.addWidget(self.sidebar_body)

        side.addWidget(QLabel(f"CMDRHelper {__version__}", objectName="appSubTitle"))

        main.addWidget(side_frame)

        right = QWidget()

        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        top_frame = QFrame(objectName="topbar")

        top = QHBoxLayout(top_frame)

        self.commander_label = QLabel("CMDR –", objectName="commanderTitle")

        self.ship_label = QLabel("", objectName="muted")

        self.last_import_label = QLabel(
            "Letzter Journal-Eintrag: –", objectName="muted"
        )

        self.connection_label = QLabel(
            "● Journal nicht erkannt", objectName="statusWarn"
        )

        self.edsm_upload_label = QLabel("● EDSM wartet", objectName="muted")
        self.edsm_upload_label.setToolTip(
            "Status der automatischen EDSM-Journalübertragung"
        )

        self.inara_upload_label = QLabel("● INARA wartet", objectName="muted")
        self.inara_upload_label.setToolTip(
            "INARA ist vorbereitet; automatische Journalübertragung folgt."
        )

        top.addWidget(self.commander_label)

        top.addWidget(self.ship_label)

        top.addStretch()

        top.addWidget(self.last_import_label)

        top.addSpacing(16)

        top.addWidget(self.connection_label)

        top.addSpacing(16)

        top.addWidget(self.edsm_upload_label)

        top.addSpacing(16)

        top.addWidget(self.inara_upload_label)

        right_layout.addWidget(top_frame)

        self.pages = QStackedWidget()

        self.pages.addWidget(self._overview())

        self.pages.addWidget(self._missions())

        self.pages.addWidget(self._explorer())

        self.pages.addWidget(self._chronicle())

        self.screenshot_view = ScreenshotView(
            self.state.settings,
            self,
        )
        self.pages.addWidget(self.screenshot_view)

        self.pages.addWidget(self._settings())

        right_layout.addWidget(self.pages, 1)

        main.addWidget(right, 1)

        self._show_page(0)

    def _overview(self):
        page = QWidget()

        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(10, 6, 10, 6)
        page_layout.setSpacing(6)

        page_layout.addWidget(QLabel("Übersicht", objectName="sectionTitle"))

        identity_row = QHBoxLayout()
        identity_row.setSpacing(6)

        identity_card, identity_layout = self._card("COMMANDER & SCHIFF")

        self.overview_commander = QLabel("CMDR –", objectName="cardValue")
        identity_layout.addWidget(self.overview_commander)

        self.overview_ship = QLabel("Schiff: –")
        self.overview_ship.setWordWrap(True)
        identity_layout.addWidget(self.overview_ship)

        self.overview_location = QLabel("Standort: –", objectName="muted")
        self.overview_location.setWordWrap(True)
        identity_layout.addWidget(self.overview_location)

        identity_row.addWidget(identity_card, 2)

        journal_card, journal_layout = self._card("JOURNAL")

        self.journal_count_value = QLabel("0", objectName="cardValue")
        journal_layout.addWidget(self.journal_count_value)

        journal_layout.addWidget(QLabel("Journaldateien erkannt", objectName="muted"))

        self.overview_journal_state = QLabel("● nicht erkannt", objectName="statusWarn")
        journal_layout.addWidget(self.overview_journal_state)

        identity_row.addWidget(journal_card, 1)
        page_layout.addLayout(identity_row)

        row = QHBoxLayout()
        row.setSpacing(6)

        mission_card, mission_layout = self._card("MISSIONEN")

        self.active_missions_value = QLabel("0", objectName="cardValue")
        mission_layout.addWidget(self.active_missions_value)

        self.mission_start_status = QLabel(
            "keine offenen Missionen", objectName="muted"
        )
        self.mission_start_status.setWordWrap(True)
        mission_layout.addWidget(self.mission_start_status)

        mission_button = QPushButton("Missionen →", objectName="primary")
        mission_button.clicked.connect(lambda: self._show_page(1))
        mission_layout.addWidget(mission_button)

        row.addWidget(mission_card, 1)

        location_card, location_layout = self._card("AKTUELLER STANDORT")

        self.current_system_value = QLabel("–", objectName="cardValue")
        self.current_system_value.setWordWrap(True)
        location_layout.addWidget(self.current_system_value)

        self.current_place_value = QLabel("–", objectName="muted")
        self.current_place_value.setWordWrap(True)
        location_layout.addWidget(self.current_place_value)

        explorer_button = QPushButton("System im Explorer →", objectName="primary")
        explorer_button.clicked.connect(lambda: self._show_page(2))
        location_layout.addWidget(explorer_button)

        row.addWidget(location_card, 1)
        page_layout.addLayout(row)

        status_card, status_layout = self._card("LETZTER STAND")

        self.overview_status = QLabel("Noch keine Journaldaten erkannt.")
        self.overview_status.setWordWrap(True)
        status_layout.addWidget(self.overview_status)

        page_layout.addWidget(status_card)
        page_layout.addStretch()

        return page

    def _explorer(self):
        page = QWidget()

        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(10, 6, 10, 6)
        page_layout.setSpacing(6)

        page_layout.addWidget(QLabel("Explorer", objectName="sectionTitle"))

        system_card, system_layout = self._card("AKTUELLES SYSTEM")

        self.system_scan_header = QLabel("Noch keine Systemdaten", objectName="muted")
        self.system_scan_header.setWordWrap(True)
        self.system_scan_header.setToolTip(
            "Kartographie wird getrennt von BIO berechnet. "
            "Nur Scans zeigt den reinen Scanwert. "
            "Aktuell erreicht berücksichtigt bereits selbst kartographierte Körper. "
            "Komplett kartiert zeigt den geschätzten Zielwert bei vollständiger "
            "und effizienter DSS-Kartographie."
        )
        system_layout.addWidget(self.system_scan_header)

        self.system_bio_header = QLabel(
            "BIO: noch keine vollständigen Proben", objectName="muted"
        )
        self.system_bio_header.setWordWrap(True)
        self.system_bio_header.setToolTip(
            "BIO wird getrennt von Kartographie berechnet. "
            "First Logged zeigt den möglichen 5-fachen Gesamtwert; "
            "ob der Bonus tatsächlich gewährt wird, steht erst beim Verkauf fest."
        )
        system_layout.addWidget(self.system_bio_header)

        self.unsold_explorer_header = QLabel(
            "Noch nicht abgegeben: Kartographie 0 Cr   |   BIO 0 Cr", objectName="muted"
        )
        self.unsold_explorer_header.setWordWrap(True)
        # Offene, noch nicht verkaufte Explorer-Werte deutlich hervorheben.
        self.unsold_explorer_header.setStyleSheet("color: #ffb000; font-weight: 700;")
        self.unsold_explorer_header.setToolTip(
            "Gesamtschätzung über alle Systeme seit dem letzten Verkauf. "
            "Kartographie wird bei Universal Cartographics zurückgesetzt; "
            "BIO bei Vista Genomics. Beide Zähler arbeiten unabhängig."
        )
        system_layout.addWidget(self.unsold_explorer_header)

        overview_row = QHBoxLayout()
        overview_row.addStretch()

        self.system_overview_button = QPushButton("Alles anzeigen")
        self.system_overview_button.setToolTip(
            "Komplette Systemstruktur als Miniatur anzeigen"
        )
        self.system_overview_button.clicked.connect(self._show_system_overview)
        overview_row.addWidget(self.system_overview_button)

        system_layout.addLayout(overview_row)

        legend_frame = QFrame()
        legend_frame.setObjectName("card")

        legend_layout = QHBoxLayout(legend_frame)
        legend_layout.setContentsMargins(12, 7, 12, 7)
        legend_layout.setSpacing(18)

        legend_items = [
            ("BIO ×N", "biologische Signale", "#66e36a"),
            ("GEO ×N", "geologische Signale", "#28c9e8"),
            ("T", "Terraforming", "#4bb8ff"),
            ("★", "Erstentdeckung möglich", "#ffae28"),
            ("◉", "First Mapping möglich", "#68c7ff"),
            ("◉✓", "First Mapping beansprucht", "#68c7ff"),
            ("◎", "selbst kartographiert", "#65d067"),
            ("⌄", "landbar", "#d8dde3"),
            ("★", "Goldrahmen > 200.000 Cr", "#ffb000"),
        ]

        for symbol, text, color in legend_items:
            item = QLabel(
                f'<span style="color:{color}; font-size:14px; '
                f'font-weight:700;">{symbol}</span> '
                f'<span style="font-size:11px;">{text}</span>'
            )
            item.setTextFormat(Qt.RichText)
            item.setWordWrap(False)
            legend_layout.addWidget(item)

        legend_layout.addStretch()
        system_layout.addWidget(legend_frame)

        self.system_map = SystemMapWidget()
        self.system_map.set_light_mode(self.ui_theme == "light")
        self.system_map.bodyClicked.connect(self._show_body_details)

        self.system_scroll = QScrollArea()
        self.system_scroll.setWidgetResizable(False)
        self.system_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.system_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.system_scroll.setFrameShape(QFrame.NoFrame)
        self.system_scroll.setWidget(self.system_map)

        # Neben der grafischen Karte zwei kompakte Textansichten:
        # - Werte: Planeten/Monde nach aktuellem Kartographiewert
        # - BIO: alle Körper mit biologischen Signalen und Besuchsstatus
        self.explorer_tabs = QTabWidget()
        self.explorer_tabs.addTab(self.system_scroll, "Systemkarte")

        self.explorer_value_table = QTableWidget(0, 7)
        self.explorer_value_table.setHorizontalHeaderLabels(
            [
                "Körper",
                "Typ",
                "Entfernung",
                "Scanwert",
                "Aktueller Wert",
                "Kartierung",
                "Status",
            ]
        )
        self.explorer_value_table.setAlternatingRowColors(True)
        self.explorer_value_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.explorer_value_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.explorer_value_table.setSelectionMode(QTableWidget.SingleSelection)
        self.explorer_value_table.verticalHeader().setVisible(False)
        self.explorer_value_table.setSortingEnabled(False)
        self.explorer_value_table.itemDoubleClicked.connect(
            self._explorer_table_body_activated
        )
        value_header = self.explorer_value_table.horizontalHeader()
        value_header.setSectionResizeMode(QHeaderView.Interactive)
        value_header.setStretchLastSection(True)
        self.explorer_value_table.setColumnWidth(0, 180)
        self.explorer_value_table.setColumnWidth(1, 210)
        self.explorer_value_table.setColumnWidth(2, 105)
        self.explorer_value_table.setColumnWidth(3, 125)
        self.explorer_value_table.setColumnWidth(4, 145)
        self.explorer_value_table.setColumnWidth(5, 100)

        self.explorer_tabs.addTab(
            self.explorer_value_table,
            "Wertliste",
        )

        self.explorer_bio_table = QTableWidget(0, 9)
        self.explorer_bio_table.setHorizontalHeaderLabels(
            [
                "Körper",
                "Typ",
                "BIO",
                "BIO-Funde",
                "BIO-Wert",
                "Entfernung",
                "Besucht",
                "Analyse",
                "Status",
            ]
        )
        self.explorer_bio_table.setAlternatingRowColors(True)
        self.explorer_bio_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.explorer_bio_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.explorer_bio_table.setSelectionMode(QTableWidget.SingleSelection)
        self.explorer_bio_table.verticalHeader().setVisible(False)
        self.explorer_bio_table.setSortingEnabled(False)
        self.explorer_bio_table.itemDoubleClicked.connect(
            self._explorer_table_body_activated
        )
        bio_header = self.explorer_bio_table.horizontalHeader()
        bio_header.setSectionResizeMode(QHeaderView.Interactive)
        bio_header.setStretchLastSection(True)
        self.explorer_bio_table.setColumnWidth(0, 140)
        self.explorer_bio_table.setColumnWidth(1, 160)
        self.explorer_bio_table.setColumnWidth(2, 50)
        self.explorer_bio_table.setColumnWidth(3, 330)
        self.explorer_bio_table.setColumnWidth(4, 130)
        self.explorer_bio_table.setColumnWidth(5, 100)
        self.explorer_bio_table.setColumnWidth(6, 95)
        self.explorer_bio_table.setColumnWidth(7, 110)

        self.explorer_tabs.addTab(
            self.explorer_bio_table,
            "BIO-Planeten",
        )

        system_layout.addWidget(self.explorer_tabs, 1)
        page_layout.addWidget(system_card, 1)

        return page

    @staticmethod
    def _explorer_body_name(body):
        return body.get("short_name") or body.get("name") or "?"

    @staticmethod
    def _explorer_distance_text(body):
        value = body.get("distance_ls")
        if value is None:
            return "–"
        try:
            return (
                f"{float(value):,.1f} ls".replace(",", "X")
                .replace(".", ",")
                .replace("X", ".")
            )
        except Exception:
            return "–"

    @staticmethod
    def _explorer_body_visited(body):
        """
        'Besucht' bedeutet hier: CMDRHelper hat eigene Journaldaten zu
        diesem Körper. Reine EDSM-Ergänzungen gelten nicht als besucht.
        """
        return bool(body.get("journal_scanned", False))

    @staticmethod
    def _explorer_bio_progress(body):
        """
        BIO-Fortschritt direkt aus den am Körper gespeicherten Journaldaten
        ableiten. Dadurch aktualisiert sich die BIO-Liste unmittelbar nach
        SAASignalsFound/FSSBodySignals und später nach ScanOrganic.
        """
        biology = list(body.get("biology") or [])

        found = len(biology)
        completed = 0

        for entry in biology:
            if not isinstance(entry, dict):
                continue

            scan_type = (
                str(entry.get("scan_type") or entry.get("ScanType") or "")
                .strip()
                .casefold()
            )

            if scan_type in ("analyse", "analyze"):
                completed += 1

        # Fallback für ältere/ergänzte Datenstände.
        found = max(
            found,
            int(
                body.get("bio_found_count")
                or body.get("biology_found_count")
                or body.get("bio_species_count")
                or 0
            ),
        )

        completed = max(
            completed,
            int(
                body.get("bio_completed_count")
                or body.get("biology_completed_count")
                or body.get("bio_analyzed_count")
                or body.get("bio_analysed_count")
                or 0
            ),
        )

        analysed = bool(
            completed > 0
            or body.get("bio_complete")
            or body.get("biology_complete")
            or body.get("bio_analyzed")
            or body.get("bio_analysed")
        )

        return found, completed, analysed

    @staticmethod
    def _explorer_bio_names(body):
        """
        BIO-Namen samt aktuellem Genetic-Sampler-Schritt liefern.

        Frontier verwendet bei ScanOrganic:
        - Log      = 1. Probe
        - Sample   = 2. Probe
        - Analyse/Analyze = 3. Probe, vollständig

        Noch nicht beprobte DSS-Genuses bekommen einen leeren Scan-Typ.
        """
        entries = []
        seen = set()

        for entry in body.get("biology") or []:
            if not isinstance(entry, dict):
                continue

            name = (
                entry.get("variant") or entry.get("species") or entry.get("genus") or ""
            )
            name = str(name or "").strip()

            if not name or name in seen:
                continue

            scan_type = str(
                entry.get("scan_type") or entry.get("ScanType") or ""
            ).strip()

            entries.append((name, scan_type))
            seen.add(name)

        # DSS/FSS kann bereits alle Genuses kennen, obwohl noch keine
        # ScanOrganic-Probe genommen wurde. Diese ergänzen wir zusätzlich.
        for name in body.get("bio_genuses") or []:
            name = str(name or "").strip()

            if name and name not in seen:
                entries.append((name, ""))
                seen.add(name)

        return entries

    @staticmethod
    def _explorer_bio_names_html(entries):
        """
        Farbcodierung je BIO-Fund:
        grau  = nur per DSS bekannt, noch nicht beprobt
        weiß  = 1. Probe (Log)
        gelb  = 2. Probe (Sample)
        grün  = 3. Probe / Analyse vollständig
        """
        from html import escape

        parts = []

        for name, scan_type in entries:
            scan_key = str(scan_type or "").strip().casefold()

            if scan_key in ("analyse", "analyze"):
                color = "#65d067"
                title = "3. Probe bestätigt"
            elif scan_key == "sample":
                color = "#ffb000"
                title = "2. Probe genommen"
            elif scan_key == "log":
                color = "#f1f3f5"
                title = "1. Probe genommen"
            else:
                color = "#8e969e"
                title = "Nur per DSS/FSS bekannt"

            parts.append(
                f'<span style="color:{color};" title="{escape(title)}">'
                f"{escape(str(name))}</span>"
            )

        return ", ".join(parts) if parts else "–"

    def _explorer_bio_known_value(self, body, learned_values=None):
        """
        Summiert die bereits eindeutig bestimmten BIO-Arten dieses Körpers.

        Schon nach der ersten ScanOrganic-Probe kennt Elite die Art/Variante,
        daher kann der Basiswert sofort angezeigt werden. Nur per DSS bekannte
        Gattungen haben noch keinen eindeutigen Artenwert.

        Eigene aus SellOrganicData gelernte Werte haben Vorrang vor der
        statischen Referenztabelle.
        """
        learned_values = learned_values or {}
        learned_folded = {
            str(key).casefold(): int(value or 0)
            for key, value in learned_values.items()
        }

        total = 0
        seen = set()

        for entry in body.get("biology") or []:
            if not isinstance(entry, dict):
                continue

            canonical = str(species_name(entry) or "").strip()
            if not canonical:
                continue

            key = canonical.casefold()
            if key in seen:
                continue
            seen.add(key)

            value = int(learned_folded.get(key, 0) or 0)
            if value <= 0:
                value = int(base_value(entry) or 0)

            total += max(0, value)

        return int(total)

    def _explorer_table_body_activated(self, item):
        body = item.data(Qt.UserRole)
        if isinstance(body, dict):
            self._show_body_details(body)

    def _refresh_explorer_tables(self):
        bodies = list(getattr(self.state, "system_bodies", None) or [])

        # Sterne und Belt Cluster sind für die gewünschte Wertliste nicht
        # relevant. Planeten und Monde nach aktuellem Wert absteigend.
        value_bodies = [
            body
            for body in bodies
            if not body.get("star_type")
            and body.get("body_type") != "Star"
            and not SystemMapWidget._is_belt_cluster(body)
        ]
        value_bodies.sort(
            key=lambda body: (
                -int(body.get("current_value") or 0),
                str(self._explorer_body_name(body)).lower(),
            )
        )

        self.explorer_value_table.setRowCount(len(value_bodies))

        for row, body in enumerate(value_bodies):
            visited = self._explorer_body_visited(body)
            self_mapped = bool(body.get("self_mapped"))
            current_value = int(body.get("current_value") or 0)

            was_mapped = body.get("was_mapped")

            # Frontier liefert WasMapped beim Scan als Zustand VOR unserer
            # eigenen DSS-Kartierung. self_mapped zeigt dagegen, dass wir
            # später selbst SurfaceScanComplete erhalten haben.
            if self_mapped:
                mapping_text = "✓ selbst kartiert"
                status = "Gescannt · selbst kartiert"
            elif was_mapped is True:
                mapping_text = "bereits kartiert"
                status = (
                    "Gescannt · bereits kartiert" if visited else "Bereits kartiert"
                )
            elif was_mapped is False:
                mapping_text = "○ First Mapping möglich"
                status = (
                    "Gescannt · First Mapping möglich"
                    if visited
                    else "First Mapping möglich"
                )
            else:
                mapping_text = "–"
                status = "Gescannt" if visited else "Nicht gescannt"

            values = [
                self._explorer_body_name(body),
                SystemMapWidget._type_text(body),
                self._explorer_distance_text(body),
                self._format_reward(body.get("scan_value", 0)),
                self._format_reward(current_value),
                mapping_text,
                status,
            ]

            for col, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                item.setData(Qt.UserRole, body)

                # Zahlenwerte auch intern numerisch hinterlegen.
                if col == 4:
                    item.setData(Qt.UserRole + 1, current_value)

                # Grün ist bewusst ausschließlich für den aktuell erreichten
                # Credit-Wert reserviert. So springt die wichtigste Zahl ins Auge.
                if col == 4:
                    yellow_threshold = self._explorer_value_yellow_threshold()

                    if yellow_threshold > 0 and current_value >= yellow_threshold:
                        item.setForeground(QColor("#ffb000"))
                        item.setToolTip(
                            "Aktuell erreichter geschätzter Kartographiewert · "
                            f"Gelb ab {self._format_reward(yellow_threshold)}"
                        )
                    else:
                        item.setForeground(QColor("#65d067"))
                        item.setToolTip(
                            "Aktuell erreichter geschätzter Kartographiewert"
                        )
                elif col == 5:
                    if self_mapped:
                        item.setForeground(QColor("#65d067"))
                    elif was_mapped is False:
                        item.setForeground(QColor("#68c7ff"))
                    elif was_mapped is True:
                        item.setForeground(QColor("#9aa3ab"))
                elif col == 6:
                    if not visited:
                        item.setForeground(QColor("#9aa3ab"))

                self.explorer_value_table.setItem(row, col, item)

        # BIO-Körper separat. Noch nicht besuchte zuerst, danach nach
        # Signalzahl und Wert. So springen offene Ziele sofort ins Auge.
        bio_bodies = [
            body
            for body in value_bodies
            if int(body.get("biological_signals") or 0) > 0
        ]
        bio_bodies.sort(
            key=lambda body: (
                self._explorer_body_visited(body),
                -int(body.get("biological_signals") or 0),
                -int(body.get("current_value") or 0),
                str(self._explorer_body_name(body)).lower(),
            )
        )

        self.explorer_bio_table.setRowCount(len(bio_bodies))

        try:
            learned_bio_values = self.state.database.learned_bio_values()
        except Exception:
            learned_bio_values = {}

        for row, body in enumerate(bio_bodies):
            visited = self._explorer_body_visited(body)
            signals = int(body.get("biological_signals") or 0)
            found, completed, analysed = self._explorer_bio_progress(body)
            bio_names = self._explorer_bio_names(body)
            bio_names_text = self._explorer_bio_names_html(bio_names)
            known_bio_value = self._explorer_bio_known_value(
                body,
                learned_bio_values,
            )
            bio_value_text = (
                self._format_reward(known_bio_value) if known_bio_value > 0 else "–"
            )

            if analysed:
                analysis_text = (
                    f"{completed} vollständig" if completed else "vollständig"
                )
                status = "✓ BIO analysiert"
            elif visited:
                analysis_text = f"{found} erfasst" if found else "offen"
                status = "! besucht · BIO offen"
            else:
                # Direkt nach dem DSS-/Signalscan steht die Anzahl der
                # biologischen Signale bereits fest, auch wenn der Körper
                # noch nicht angeflogen wurde.
                analysis_text = f"{signals} Signal(e)"
                status = "○ BIO gefunden · noch nicht besucht"

            values = [
                self._explorer_body_name(body),
                SystemMapWidget._type_text(body),
                str(signals),
                bio_names_text,
                bio_value_text,
                self._explorer_distance_text(body),
                "Besucht" if visited else "Offen",
                analysis_text,
                status,
            ]

            for col, value in enumerate(values):
                # BIO-Funde brauchen Rich Text, damit jeder Name einzeln
                # entsprechend seinem Scan-Fortschritt eingefärbt werden kann.
                if col == 3:
                    label = QLabel()
                    label.setTextFormat(Qt.RichText)
                    label.setText(str(value))
                    label.setTextInteractionFlags(Qt.NoTextInteraction)
                    label.setContentsMargins(8, 0, 4, 0)
                    label.setToolTip(
                        "Grau: nur DSS/FSS bekannt · "
                        "Weiß: 1. Probe · Gelb: 2. Probe · "
                        "Grün: 3. Probe bestätigt"
                    )
                    self.explorer_bio_table.setCellWidget(row, col, label)
                    continue

                item = QTableWidgetItem(str(value))

                if col == 4 and known_bio_value > 0:
                    item.setToolTip(
                        "Bekannter Vista-Genomics-Basiswert der bereits "
                        "eindeutig bestimmten BIO-Art(en). "
                        "Möglicher First-Logged-Gesamtwert: "
                        + self._format_reward(known_bio_value * 5)
                    )
                item.setData(Qt.UserRole, body)

                if analysed:
                    item.setForeground(QColor("#65d067"))
                elif visited:
                    item.setForeground(QColor("#ffb000"))
                else:
                    item.setForeground(QColor("#d9dde1"))

                self.explorer_bio_table.setItem(row, col, item)

        self.explorer_tabs.setTabText(
            1,
            f"Wertliste ({len(value_bodies)})",
        )
        self.explorer_tabs.setTabText(
            2,
            f"BIO-Planeten ({len(bio_bodies)})",
        )

    def _ensure_explorer_live_windows(self):
        if self._explorer_value_live_window is None:
            self._explorer_value_live_window = ExplorerLiveListWindow(
                "CMDRHelper – Wertvolle Körper",
                ["Körper", "Typ", "Wert", "Kartierung"],
                self.state.settings,
                "explorer_live/value_geometry",
                self,
            )

        if self._explorer_bio_live_window is None:
            self._explorer_bio_live_window = ExplorerLiveListWindow(
                "CMDRHelper – BIO gefunden",
                ["Körper", "BIO", "Funde", "BIO-Wert"],
                self.state.settings,
                "explorer_live/bio_geometry",
                self,
            )

    def _refresh_explorer_live_windows(self):
        """Aktualisiert die beiden kleinen Explorer-Livefenster."""
        system_name = str(getattr(self.state, "system", "") or "")
        bodies = list(getattr(self.state, "system_bodies", None) or [])

        # Beim Systemwechsel alte Treffer sofort ausblenden. Erst neue
        # qualifizierende Scans lassen die Fenster wieder erscheinen.
        system_changed = self._explorer_live_system != system_name
        self._explorer_live_system = system_name

        threshold = self._explorer_value_yellow_threshold()
        valuable_rows = []
        for body in bodies:
            if body.get("star_type") or body.get("body_type") == "Star":
                continue
            if SystemMapWidget._is_belt_cluster(body):
                continue

            value = int(body.get("current_value") or 0)
            if threshold <= 0 or value < threshold:
                continue

            if body.get("self_mapped"):
                mapping = "selbst kartiert"
            elif body.get("was_mapped") is True:
                mapping = "bereits kartiert"
            elif body.get("was_mapped") is False:
                mapping = "First Mapping möglich"
            else:
                mapping = "–"

            valuable_rows.append(
                (
                    self._explorer_body_name(body),
                    SystemMapWidget._type_text(body),
                    self._format_reward(value),
                    mapping,
                )
            )

        valuable_rows.sort(
            key=lambda row: -int(str(row[2]).replace(" Cr", "").replace(".", "") or 0)
        )

        try:
            learned_bio_values = self.state.database.learned_bio_values()
        except Exception:
            learned_bio_values = {}

        bio_rows = []
        for body in bodies:
            signals = int(body.get("biological_signals") or 0)
            if signals <= 0:
                continue

            names = self._explorer_bio_names(body)
            names_text = ", ".join(name for name, _scan_type in names) or "noch unbekannt"
            known_value = self._explorer_bio_known_value(body, learned_bio_values)
            bio_rows.append(
                (
                    self._explorer_body_name(body),
                    str(signals),
                    names_text,
                    self._format_reward(known_value) if known_value > 0 else "–",
                )
            )

        self._ensure_explorer_live_windows()

        self._explorer_value_live_window.set_rows(system_name, valuable_rows)
        self._explorer_bio_live_window.set_rows(system_name, bio_rows)

        if valuable_rows:
            if not self._explorer_value_live_window.isVisible():
                self._explorer_value_live_window.show()
                self._explorer_value_live_window.raise_()
        elif system_changed and self._explorer_value_live_window.isVisible():
            self._explorer_value_live_window.hide()

        if bio_rows:
            if not self._explorer_bio_live_window.isVisible():
                self._explorer_bio_live_window.show()
                self._explorer_bio_live_window.raise_()
        elif system_changed and self._explorer_bio_live_window.isVisible():
            self._explorer_bio_live_window.hide()

    def _show_system_overview(self):
        bodies = list(
            getattr(
                self.state,
                "system_bodies",
                None,
            )
            or []
        )

        if not bodies:
            QMessageBox.information(
                self,
                "Alles anzeigen",
                "Für das aktuelle System liegen noch keine Körperdaten vor.",
            )
            return

        if self._system_overview_window is not None:
            try:
                self._system_overview_window.close()
            except Exception:
                pass

        self._system_overview_window = SystemOverviewDialog(
            system_name=(
                getattr(
                    self.state,
                    "system",
                    None,
                )
                or "Aktuelles System"
            ),
            bodies=bodies,
            source_map=self.system_map,
            on_body_clicked=self._focus_system_body,
            parent=self,
        )

        self._system_overview_window.show()
        self._system_overview_window.raise_()
        self._system_overview_window.activateWindow()

    def _focus_system_body(self, body):
        if not hasattr(
            self,
            "system_scroll",
        ):
            return

        (
            positions,
            _children,
            _families,
            _used_units,
            _depth_count,
        ) = self.system_map._tree_layout()

        body_pos = positions.get(id(body))

        if body_pos is None:
            return

        center_x = float(body_pos["x"]) + float(self.system_map.BODY_W) / 2.0

        center_y = float(body_pos["y"]) + float(self.system_map.BODY_H) / 2.0

        viewport = self.system_scroll.viewport()

        self.system_scroll.horizontalScrollBar().setValue(
            int(center_x - viewport.width() / 2.0)
        )

        self.system_scroll.verticalScrollBar().setValue(
            int(center_y - viewport.height() / 2.0)
        )

    def _chronicle(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(10, 6, 10, 6)
        layout.setSpacing(6)

        header = QHBoxLayout()
        header.addWidget(QLabel("Chronik", objectName="sectionTitle"))

        self.chronicle_search_edit = QLineEdit()
        self.chronicle_search_edit.setPlaceholderText(
            "Chronik durchsuchen, z. B. Hirnbaum, Wasserwelt, Tellur …"
        )
        self.chronicle_search_edit.setMinimumWidth(280)
        self.chronicle_search_edit.returnPressed.connect(self._search_chronicle_biology)
        header.addWidget(self.chronicle_search_edit)

        search_button = QPushButton("Suchen")
        search_button.clicked.connect(self._search_chronicle_biology)
        header.addWidget(search_button)

        reset_button = QPushButton("Zurücksetzen")
        reset_button.clicked.connect(self._reset_chronicle_search)
        header.addWidget(reset_button)

        align_button = QPushButton("Ausrichten")
        align_button.clicked.connect(self._align_chronicle_galaxy)
        header.addWidget(align_button)

        self.chronicle_legend_button = QPushButton("Suchhilfe / Legende")
        self.chronicle_legend_button.clicked.connect(self._open_chronicle_search_help)
        header.addWidget(self.chronicle_legend_button)

        header.addStretch()

        refresh = QPushButton("Chronik aktualisieren", objectName="primary")
        refresh.clicked.connect(self._refresh_chronicle)
        header.addWidget(refresh)

        layout.addLayout(header)

        map_card, map_layout = self._card("BESUCHTE SYSTEME")

        self.chronicle_status = QLabel("", objectName="muted")
        self.chronicle_status.setWordWrap(True)
        map_layout.addWidget(self.chronicle_status)

        self.chronicle_map = ChronicleMapWidget()
        self.chronicle_map.systemClicked.connect(self._chronicle_system_clicked)
        map_layout.addWidget(self.chronicle_map, 1)

        self.chronicle_detail = QLabel("Kein System ausgewählt.", objectName="muted")
        self.chronicle_detail.setWordWrap(True)
        map_layout.addWidget(self.chronicle_detail)

        # BIO-Suchergebnisse bleiben bewusst in der Chronik.
        self.chronicle_search_results = QListWidget()
        self.chronicle_search_results.setVisible(False)
        self.chronicle_search_results.setMaximumHeight(190)
        self.chronicle_search_results.itemClicked.connect(
            self._chronicle_search_result_clicked
        )
        map_layout.addWidget(self.chronicle_search_results)

        layout.addWidget(map_card, 1)

        QTimer.singleShot(0, self._refresh_chronicle)

        return page

    def _refresh_chronicle(self):
        if hasattr(self, "chronicle_search_results"):
            self.chronicle_search_results.clear()
            self.chronicle_search_results.setVisible(False)

        try:
            systems = self.state.database.chronicle_systems()
        except Exception as exc:
            systems = []
            self.chronicle_status.setText(f"Chronik konnte nicht geladen werden: {exc}")
        else:
            self.chronicle_status.setText(
                f"{len(systems)} besuchte Systeme mit Koordinaten · "
                "Mausrad: Zoom · Ziehen: Karte verschieben · Klick: System auswählen"
            )
        self.chronicle_map.set_systems(systems)

    def _align_chronicle_galaxy(self):
        if hasattr(self, "chronicle_map"):
            self.chronicle_map.align_galaxy()

    def _open_chronicle_search_help(self):
        try:
            groups = self.state.database.chronicle_search_terms()
        except Exception as exc:
            QMessageBox.warning(
                self,
                "Suchhilfe / Legende",
                ("Die Suchhilfe konnte nicht geladen werden.\n\n" f"{exc}"),
            )
            return

        # Feste Schnellsuchen vor die dynamischen Datenbank-Kategorien setzen.
        merged = {
            "Schnellsuche": [
                "Terraforming",
                "BIO",
                "GEO",
                "Water world",
                "Earthlike",
                "Ammonia world",
                "FSS-Signal",
            ]
        }

        merged.update(groups or {})

        # Vorhandenes Fenster wiederverwenden, wenn es schon offen ist.
        if self._chronicle_search_help_window is not None:
            try:
                self._chronicle_search_help_window.close()
            except Exception:
                pass

        self._chronicle_search_help_window = ChronicleSearchHelpDialog(
            groups=merged,
            on_term_clicked=self._chronicle_search_term_clicked,
            parent=self,
        )

        # Nicht modal: Chronik bleibt weiter bedienbar.
        self._chronicle_search_help_window.show()
        self._chronicle_search_help_window.raise_()
        self._chronicle_search_help_window.activateWindow()

    def _chronicle_search_term_clicked(
        self,
        term,
    ):
        self.chronicle_search_edit.setText(str(term))
        self._search_chronicle_biology()

    def _search_chronicle_biology(self):
        query = self.chronicle_search_edit.text().strip()

        if not query:
            self._reset_chronicle_search()
            return

        try:
            results = self.state.database.search_chronicle(query)
        except Exception as exc:
            self.chronicle_status.setText(f"Chronik-Suche fehlgeschlagen: {exc}")
            return

        self.chronicle_search_results.clear()

        if not results:
            self.chronicle_search_results.setVisible(False)
            self.chronicle_status.setText(f'Keine Treffer für "{query}".')
            # Die normale Reisekarte bleibt sichtbar.
            return

        systems_by_address = {}

        for result in results:
            address = result.get("system_address")

            if address in systems_by_address:
                continue

            systems_by_address[address] = {
                "system_address": address,
                "name": result.get("system_name") or "",
                "x": result.get("x"),
                "y": result.get("y"),
                "z": result.get("z"),
                "first_seen": result.get("system_first_seen") or "",
                "last_seen": result.get("system_last_seen") or "",
                "body_count": int(result.get("body_count") or 0),
                "visits": 0,
            }

        matching_systems = [
            system
            for system in systems_by_address.values()
            if (
                system.get("x") is not None
                and system.get("y") is not None
                and system.get("z") is not None
            )
        ]

        # Während der Suche zeigt die Karte ausschließlich die Systeme
        # mit passenden biologischen Funden.
        self.chronicle_map.set_systems(matching_systems)

        for result in results:
            kind = result.get("kind") or "Treffer"
            match_name = result.get("match_name") or result.get("detail") or "Treffer"

            system_name = result.get("system_name") or "Unbekannt"

            body_name = result.get("short_name") or result.get("body_name") or ""

            parts = [f"[{kind}]", system_name]

            if body_name:
                parts.append(body_name)

            parts.append(str(match_name))

            item = QListWidgetItem("  ·  ".join(parts))

            item.setData(Qt.UserRole, result)

            self.chronicle_search_results.addItem(item)

        self.chronicle_search_results.setVisible(True)

        self.chronicle_status.setText(
            f"{len(results)} Treffer in "
            f"{len(systems_by_address)} System(en) "
            f'für "{query}".'
        )

    def _reset_chronicle_search(self):
        if hasattr(self, "chronicle_search_edit"):
            self.chronicle_search_edit.clear()

        if hasattr(self, "chronicle_search_results"):
            self.chronicle_search_results.clear()
            self.chronicle_search_results.setVisible(False)

        self._refresh_chronicle()

    def _chronicle_search_result_clicked(
        self,
        item,
    ):
        result = item.data(Qt.UserRole)

        if not isinstance(result, dict):
            return

        system = {
            "system_address": result.get("system_address"),
            "name": (result.get("system_name") or ""),
            "x": result.get("x"),
            "y": result.get("y"),
            "z": result.get("z"),
            "first_seen": result.get("system_first_seen") or "",
            "last_seen": result.get("system_last_seen") or "",
            "body_count": int(result.get("body_count") or 0),
            "visits": 0,
        }

        body_name = result.get("short_name") or result.get("body_name") or ""

        match_name = result.get("match_name") or result.get("detail") or "Treffer"

        kind = result.get("kind") or "Treffer"

        hit_parts = [kind]

        if body_name:
            hit_parts.append(body_name)

        hit_parts.append(str(match_name))

        self._chronicle_system_clicked(
            system,
            hit_text="Treffer: " + " – ".join(hit_parts),
        )

    def _chronicle_system_clicked(
        self,
        system,
        hit_text="",
    ):
        name = system.get("name") or "Unbekannt"
        address = system.get("system_address")

        self.chronicle_detail.setText(
            f"{name}   ·   "
            f"Besuche: {system.get('visits', 0)}   ·   "
            f"Körper: {system.get('body_count', 0)}   ·   "
            f"Erster Besuch: "
            f"{self._format_timestamp(system.get('first_seen'))}   ·   "
            f"Letzter Besuch: "
            f"{self._format_timestamp(system.get('last_seen'))}   ·   "
            f"Position: X {float(system.get('x') or 0):.1f} / "
            f"Y {float(system.get('y') or 0):.1f} / "
            f"Z {float(system.get('z') or 0):.1f} ly"
        )

        try:
            details = self.state.database.chronicle_system_details(address)
        except Exception as exc:
            QMessageBox.warning(
                self,
                "Chronik",
                (
                    f"{name}\n\n"
                    "Systemdaten konnten nicht geladen werden.\n\n"
                    f"{exc}"
                ),
            )
            return

        bodies = details.get("bodies") or []

        bio_bodies = sum(
            1 for body in bodies if int(body.get("biological_signals") or 0) > 0
        )

        geo_bodies = sum(
            1 for body in bodies if int(body.get("geological_signals") or 0) > 0
        )

        header_text = (
            f"{len(bodies)} gespeicherte Körper"
            + (f" · BIO auf {bio_bodies} Körper(n)" if bio_bodies else "")
            + (f" · GEO auf {geo_bodies} Körper(n)" if geo_bodies else "")
        )

        if hit_text:
            header_text += f" · {hit_text}"

        header_text += " · Klick auf einen Körper öffnet die Detailansicht"

        # Vorheriges Chronik-Systemfenster schließen, damit immer nur
        # ein historisches Systemfenster gleichzeitig offen bleibt.
        if self._chronicle_system_window is not None:
            try:
                self._chronicle_system_window.close()
            except Exception:
                pass

        self._chronicle_system_window = ChronicleSystemWindow(
            system_name=name,
            bodies=bodies,
            header_text=header_text,
            body_callback=self._show_body_details,
            parent=self,
        )

        self._chronicle_system_window.system_map.set_light_mode(
            self.ui_theme == "light"
        )

        # Nicht modal: Die Chronik-Karte bleibt weiter bedienbar.
        self._chronicle_system_window.show()
        self._chronicle_system_window.raise_()
        self._chronicle_system_window.activateWindow()

    def _show_body_details(self, body):
        dialog = BodyDetailWindow(body, self)
        dialog.exec()

    def _save_overview_splitter(self, pos, index):
        if not hasattr(self, "overview_splitter"):
            return

        self.state.settings.setValue(
            "overview_splitter_sizes", self.overview_splitter.sizes()
        )

    def reset_overview_splitter(self):
        if not hasattr(self, "overview_splitter"):
            return

        self.overview_splitter.setSizes([220, 675])

        self.state.settings.setValue("overview_splitter_sizes", [220, 675])

    def _missions(self):
        page = QWidget()

        layout = QVBoxLayout(page)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(8)

        header = QHBoxLayout()

        header.addWidget(QLabel("Missionen", objectName="sectionTitle"))

        header.addStretch()

        refresh = QPushButton("Journal aktualisieren", objectName="primary")

        refresh.clicked.connect(self.state.refresh)

        header.addWidget(refresh)

        reset_missions = QPushButton("Missionen zurücksetzen")
        reset_missions.clicked.connect(self._reset_missions)
        header.addWidget(reset_missions)

        layout.addLayout(header)

        card, card_layout = self._card("AKTIVE MISSIONEN")

        mission_summary_row = QHBoxLayout()

        self.mission_total_reward_label = QLabel(
            "Gesamtbelohnung: 0 Cr", objectName="cardValue"
        )
        self.mission_total_reward_label.setToolTip(
            "Summe der Credit-Belohnungen aller aktuell offenen Missionen"
        )

        mission_summary_row.addWidget(self.mission_total_reward_label)
        mission_summary_row.addStretch()

        card_layout.addLayout(mission_summary_row)

        self.missions_table = QTableWidget(0, 7)

        self.missions_table.setHorizontalHeaderLabels(
            [
                "Mission",
                "System",
                "Planet / Ort",
                "Status",
                "Nächster Schritt",
                "Belohnung",
                "Frist",
            ]
        )

        self.missions_table.setAlternatingRowColors(True)

        self.missions_table.setEditTriggers(QTableWidget.NoEditTriggers)

        self.missions_table.setSelectionBehavior(QTableWidget.SelectRows)

        self.missions_table.verticalHeader().setVisible(False)

        header_view = self.missions_table.horizontalHeader()

        # Alle Missionsspalten dürfen vom Benutzer mit der Maus
        # frei in der Breite verändert werden.
        header_view.setSectionResizeMode(QHeaderView.Interactive)
        header_view.setStretchLastSection(False)

        self.missions_table.setColumnWidth(0, 260)

        self.missions_table.setColumnWidth(1, 210)

        self.missions_table.setColumnWidth(2, 260)

        self.missions_table.setColumnWidth(3, 155)

        self.missions_table.setColumnWidth(4, 300)

        self.missions_table.setColumnWidth(5, 125)

        self.missions_table.setColumnWidth(6, 170)

        # Gespeicherte Spaltenbreiten nach den Standardwerten
        # wiederherstellen. saveState() speichert die komplette
        # Header-Konfiguration robust als QByteArray.
        saved_header_state = self.state.settings.value("missions_table_header_state")
        if saved_header_state is not None:
            try:
                header_view.restoreState(saved_header_state)
            except Exception:
                pass

        # Jede Änderung durch Ziehen einer Spaltengrenze sofort speichern.
        header_view.sectionResized.connect(self._save_missions_header_state)

        self.missions_table.itemSelectionChanged.connect(
            self._mission_selection_changed
        )

        card_layout.addWidget(self.missions_table)

        layout.addWidget(card, 1)

        detail_card, detail_layout = self._card("MISSIONSDETAILS")

        self.mission_detail_title = QLabel("Keine Mission ausgewählt")

        self.mission_detail_title.setStyleSheet("font-size: 15px; font-weight: 700;")

        detail_layout.addWidget(self.mission_detail_title)

        self.mission_detail_text = QLabel("Wähle oben eine Mission aus.")

        self.mission_detail_text.setWordWrap(True)

        self.mission_detail_text.setObjectName("muted")

        detail_layout.addWidget(self.mission_detail_text)

        self.mission_progress_text = QLabel("")

        self.mission_progress_text.setWordWrap(True)

        detail_layout.addWidget(self.mission_progress_text)

        layout.addWidget(detail_card)

        return page

    def _save_missions_header_state(self, logical_index, old_size, new_size):
        if not hasattr(self, "missions_table"):
            return

        self.state.settings.setValue(
            "missions_table_header_state",
            self.missions_table.horizontalHeader().saveState(),
        )

    def _settings(self):
        # Die Einstellungsseite kann inzwischen höher als das Hauptfenster
        # werden. Deshalb liegt der komplette Inhalt in einem Scrollbereich.
        page = QWidget()

        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(0, 0, 0, 0)
        page_layout.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(8)

        layout.addWidget(QLabel("Einstellungen", objectName="sectionTitle"))

        card, card_layout = self._card("JOURNAL")

        form = QFormLayout()

        self.journal_path_edit = QLineEdit()
        self.journal_path_edit.setReadOnly(True)

        self.journal_file_count = QLabel("0")

        self.journal_oldest_file = QLabel("–")
        self.journal_oldest_file.setWordWrap(True)

        self.journal_newest_file = QLabel("–")
        self.journal_newest_file.setWordWrap(True)

        self.journal_newest_name = QLabel("–")
        self.journal_newest_name.setWordWrap(True)

        self.journal_last_read = QLabel("–")
        self.journal_last_read.setWordWrap(True)

        form.addRow("Journalordner:", self.journal_path_edit)

        form.addRow("Gefundene Journaldateien:", self.journal_file_count)

        form.addRow("Älteste Journaldatei:", self.journal_oldest_file)

        form.addRow("Neueste Journaldatei:", self.journal_newest_file)

        form.addRow("Neueste Datei:", self.journal_newest_name)

        form.addRow("Letzter gelesener Eintrag:", self.journal_last_read)

        card_layout.addLayout(form)

        buttons = QHBoxLayout()

        choose = QPushButton("Journalordner wählen")

        choose.clicked.connect(self.choose_journal_folder)

        buttons.addWidget(choose)

        refresh = QPushButton("Jetzt einlesen", objectName="primary")

        refresh.clicked.connect(self.state.refresh)

        buttons.addWidget(refresh)
        buttons.addStretch()

        card_layout.addLayout(buttons)

        layout.addWidget(card)

        online_card, online_layout = self._card("ONLINE-DIENSTE")

        online_layout.addWidget(
            QLabel(
                "Zugangsdaten werden lokal in den CMDRHelper-Einstellungen "
                "gespeichert. Die API-Schlüssel werden in der Oberfläche "
                "verdeckt angezeigt.",
                objectName="muted",
            )
        )

        # -----------------------------
        # EDSM
        # -----------------------------
        edsm_title = QLabel("EDSM")
        edsm_title.setStyleSheet("font-weight: 700;")
        online_layout.addWidget(edsm_title)

        edsm_form = QFormLayout()

        self.edsm_commander_edit = QLineEdit()
        self.edsm_commander_edit.setText(self.state.edsm_commander)
        self.edsm_commander_edit.setPlaceholderText("Commander-Name")

        self.edsm_api_key_edit = QLineEdit()
        self.edsm_api_key_edit.setText(self.state.edsm_api_key)
        self.edsm_api_key_edit.setEchoMode(QLineEdit.Password)
        self.edsm_api_key_edit.setPlaceholderText("EDSM API-Schlüssel")

        self.edsm_enabled_check = QCheckBox("EDSM verwenden")
        self.edsm_enabled_check.setChecked(self.state.edsm_enabled)

        edsm_form.addRow("Commander-Name:", self.edsm_commander_edit)
        edsm_form.addRow("API-Schlüssel:", self.edsm_api_key_edit)
        edsm_form.addRow("", self.edsm_enabled_check)

        online_layout.addLayout(edsm_form)

        edsm_test_row = QHBoxLayout()

        self.edsm_test_button = QPushButton("EDSM-Verbindung testen")
        self.edsm_test_button.clicked.connect(self._test_edsm_connection)
        edsm_test_row.addWidget(self.edsm_test_button)

        self.edsm_test_status = QLabel("Noch nicht getestet", objectName="muted")
        self.edsm_test_status.setWordWrap(True)
        edsm_test_row.addWidget(self.edsm_test_status, 1)

        online_layout.addLayout(edsm_test_row)

        # -----------------------------
        # Inara
        # -----------------------------
        inara_title = QLabel("Inara")
        inara_title.setStyleSheet("font-weight: 700;")
        online_layout.addWidget(inara_title)

        inara_form = QFormLayout()

        self.inara_commander_edit = QLineEdit()
        self.inara_commander_edit.setText(self.state.inara_commander)
        self.inara_commander_edit.setPlaceholderText("Commander-Name")

        self.inara_api_key_edit = QLineEdit()
        self.inara_api_key_edit.setText(self.state.inara_api_key)
        self.inara_api_key_edit.setEchoMode(QLineEdit.Password)
        self.inara_api_key_edit.setPlaceholderText("Inara API-Schlüssel")

        self.inara_enabled_check = QCheckBox("Inara verwenden")
        self.inara_enabled_check.setChecked(self.state.inara_enabled)

        inara_form.addRow("Commander-Name:", self.inara_commander_edit)
        inara_form.addRow("API-Schlüssel:", self.inara_api_key_edit)
        inara_form.addRow("", self.inara_enabled_check)

        online_layout.addLayout(inara_form)

        inara_test_row = QHBoxLayout()

        self.inara_test_button = QPushButton("Inara-Verbindung testen")
        self.inara_test_button.clicked.connect(self._test_inara_connection)
        inara_test_row.addWidget(self.inara_test_button)

        self.inara_test_status = QLabel("Noch nicht getestet", objectName="muted")
        self.inara_test_status.setWordWrap(True)
        inara_test_row.addWidget(self.inara_test_status, 1)

        online_layout.addLayout(inara_test_row)

        save_online = QPushButton("Online-Zugänge speichern", objectName="primary")
        save_online.clicked.connect(self._save_online_settings)
        online_layout.addWidget(save_online)

        layout.addWidget(online_card)

        database_card, database_layout = self._card("DATENBANK")

        database_layout.addWidget(
            QLabel(
                "CMDRHelper speichert deine eigenen Journal-Entdeckungen "
                "dauerhaft in einer lokalen SQLite-Datenbank. "
                "Der Archivimport liest vorhandene Journaldateien einmalig "
                "ein und ergänzt bekannte Systeme, Körper, Materialien "
                "sowie BIO-/GEO-Daten.",
                objectName="muted",
            )
        )

        self.database_status_label = QLabel(
            "Datenbankstatus wird geladen …", objectName="muted"
        )
        self.database_status_label.setWordWrap(True)
        database_layout.addWidget(self.database_status_label)

        self.database_progress_bar = QProgressBar()
        self.database_progress_bar.setRange(0, 100)
        self.database_progress_bar.setValue(0)
        self.database_progress_bar.setTextVisible(True)
        self.database_progress_bar.setFormat("Bereit")
        self.database_progress_bar.setVisible(False)
        database_layout.addWidget(self.database_progress_bar)

        self.database_progress_file = QLabel("", objectName="muted")
        self.database_progress_file.setWordWrap(True)
        self.database_progress_file.setVisible(False)
        database_layout.addWidget(self.database_progress_file)

        database_buttons = QHBoxLayout()

        self.database_import_button = QPushButton("Journal-Archiv importieren")
        self.database_import_button.clicked.connect(self._import_journal_archive)
        database_buttons.addWidget(self.database_import_button)

        database_buttons.addStretch()
        database_layout.addLayout(database_buttons)

        layout.addWidget(database_card)

        self.state.databaseImportProgress.connect(self._database_import_progress)
        self.state.databaseImportFinished.connect(self._database_import_finished)

        self._refresh_database_status()

        update_card, update_layout = self._card("UPDATE")

        update_form = QFormLayout()

        self.update_current_version = QLabel(__version__)
        self.update_status_label = QLabel("Noch nicht geprüft", objectName="muted")
        self.update_status_label.setWordWrap(True)

        update_form.addRow("Installierte Version:", self.update_current_version)
        update_form.addRow("GitHub-Status:", self.update_status_label)

        update_layout.addLayout(update_form)

        update_row = QHBoxLayout()

        self.update_check_button = QPushButton("Jetzt prüfen")
        self.update_check_button.clicked.connect(
            lambda: self._check_for_updates(automatic=False)
        )
        update_row.addWidget(self.update_check_button)
        update_row.addStretch()

        update_layout.addLayout(update_row)

        layout.addWidget(update_card)

        ui_card, ui_layout = self._card("OBERFLÄCHE")

        theme_row = QHBoxLayout()

        theme_row.addWidget(QLabel("Darstellung:"))

        self.theme_group = QButtonGroup(self)

        self.theme_dark_radio = QRadioButton("Dunkel")
        self.theme_light_radio = QRadioButton("Hell")

        self.theme_group.addButton(self.theme_dark_radio)
        self.theme_group.addButton(self.theme_light_radio)

        if self.ui_theme == "light":
            self.theme_light_radio.setChecked(True)
        else:
            self.theme_dark_radio.setChecked(True)

        self.theme_dark_radio.toggled.connect(
            lambda checked: (self._set_theme("dark") if checked else None)
        )

        self.theme_light_radio.toggled.connect(
            lambda checked: (self._set_theme("light") if checked else None)
        )

        theme_row.addWidget(self.theme_dark_radio)
        theme_row.addWidget(self.theme_light_radio)
        theme_row.addStretch()

        ui_layout.addLayout(theme_row)

        font_row = QHBoxLayout()
        font_row.addWidget(QLabel("Schriftart:"))

        self.ui_font_combo = QFontComboBox()
        self.ui_font_combo.setMinimumWidth(260)
        self.ui_font_combo.setToolTip(
            "Schriftart für die gesamte CMDRHelper-Oberfläche"
        )

        app = QApplication.instance()
        current_font = app.font() if app is not None else QFont()

        saved_family = str(
            self.state.settings.value(
                "ui_font_family",
                current_font.family(),
            )
            or current_font.family()
        ).strip()

        saved_size = self._saved_ui_font_size(current_font.pointSize())

        self.ui_font_combo.setCurrentFont(QFont(saved_family))

        font_row.addWidget(self.ui_font_combo)

        font_row.addSpacing(12)
        font_row.addWidget(QLabel("Größe:"))

        self.ui_font_size_spin = QSpinBox()
        self.ui_font_size_spin.setRange(7, 24)
        self.ui_font_size_spin.setSuffix(" pt")
        self.ui_font_size_spin.setValue(saved_size)
        self.ui_font_size_spin.setToolTip(
            "Schriftgröße für die gesamte CMDRHelper-Oberfläche"
        )
        font_row.addWidget(self.ui_font_size_spin)

        self.ui_font_save_button = QPushButton("Schrift speichern")
        self.ui_font_save_button.clicked.connect(self._save_ui_font_settings)
        font_row.addWidget(self.ui_font_save_button)

        self.ui_font_status = QLabel("", objectName="muted")
        font_row.addWidget(self.ui_font_status)

        font_row.addStretch()
        ui_layout.addLayout(font_row)

        self.ui_font_restart_hint = QLabel(
            "Hinweis: Änderungen an Schriftart und Schriftgröße "
            "werden erst nach einem Neustart von CMDRHelper wirksam."
        )
        self.ui_font_restart_hint.setWordWrap(True)
        self.ui_font_restart_hint.setStyleSheet("color: #ffb000; font-weight: 600;")
        ui_layout.addWidget(self.ui_font_restart_hint)

        value_threshold_row = QHBoxLayout()
        value_threshold_row.addWidget(QLabel("Planeten-Wertliste gelb ab:"))

        self.explorer_value_threshold_spin = QSpinBox()
        self.explorer_value_threshold_spin.setRange(0, 2_000_000_000)
        self.explorer_value_threshold_spin.setSingleStep(50_000)
        self.explorer_value_threshold_spin.setSuffix(" Cr")
        self.explorer_value_threshold_spin.setMinimumWidth(160)

        try:
            threshold = int(
                self.state.settings.value(
                    "explorer_value_yellow_threshold",
                    200_000,
                )
                or 200_000
            )
        except (TypeError, ValueError):
            threshold = 200_000

        self.explorer_value_threshold_spin.setValue(max(0, threshold))
        self.explorer_value_threshold_spin.setToolTip(
            "Aktuelle Kartographiewerte ab diesem Betrag werden "
            "in der Explorer-Wertliste gelb hervorgehoben."
        )
        self.explorer_value_threshold_spin.valueChanged.connect(
            self._set_explorer_value_threshold
        )

        value_threshold_row.addWidget(self.explorer_value_threshold_spin)
        value_threshold_row.addStretch()
        ui_layout.addLayout(value_threshold_row)

        layout.addWidget(ui_card)
        layout.addStretch()

        scroll.setWidget(content)
        page_layout.addWidget(scroll, 1)

        return page

    def _refresh_database_status(self):
        if not hasattr(self, "database_status_label"):
            return

        stats = self.state.database_stats()

        self.database_status_label.setText(
            "Gespeichert: "
            f"{stats.get('systems', 0)} Systeme · "
            f"{stats.get('bodies', 0)} Körper · "
            f"{stats.get('materials', 0)} Materialien · "
            f"{stats.get('biology', 0)} BIO-Funde · "
            f"{stats.get('codex_entries', 0)} Codex/Phänomene · "
            f"{stats.get('journal_imports', 0)} Journale"
        )

    def _import_journal_archive(self):
        self.database_import_button.setEnabled(False)

        self.database_status_label.setText("Journal-Archiv wird eingelesen …")

        self.database_progress_bar.setRange(0, 100)
        self.database_progress_bar.setValue(0)
        self.database_progress_bar.setFormat("Vorbereitung …")
        self.database_progress_bar.setVisible(True)

        self.database_progress_file.setText("Journaldateien werden vorbereitet …")
        self.database_progress_file.setVisible(True)

        self.state.import_journal_archive()

    def _database_import_progress(
        self,
        current,
        total,
        name,
    ):
        try:
            current = int(current)
        except Exception:
            current = 0

        try:
            total = int(total)
        except Exception:
            total = 0

        if total > 0:
            percent = int(round((current / total) * 100))
            percent = max(0, min(100, percent))
        else:
            percent = 0

        self.database_status_label.setText(
            f"Journal-Archiv wird eingelesen … " f"{current} / {total}"
        )

        self.database_progress_bar.setRange(0, 100)
        self.database_progress_bar.setValue(percent)
        self.database_progress_bar.setFormat(f"{percent} %   ·   {current} / {total}")
        self.database_progress_bar.setVisible(True)

        self.database_progress_file.setText(f"Aktuell: {name}")
        self.database_progress_file.setVisible(True)

    def _database_import_finished(
        self,
        stats,
        error,
    ):
        self.database_import_button.setEnabled(True)

        if error:
            self.database_progress_bar.setRange(0, 100)
            self.database_progress_bar.setValue(0)
            self.database_progress_bar.setFormat("Import fehlgeschlagen")
            self.database_progress_bar.setVisible(True)
            self.database_progress_file.setText("")
            self.database_progress_file.setVisible(False)

            self.database_status_label.setText(f"Import fehlgeschlagen: {error}")
            QMessageBox.warning(
                self,
                "Datenbank",
                f"Der Journal-Archivimport ist fehlgeschlagen.\n\n{error}",
            )
            return

        self._refresh_database_status()

        self.database_progress_bar.setRange(0, 100)
        self.database_progress_bar.setValue(100)
        self.database_progress_bar.setFormat("100 %   ·   Import abgeschlossen")
        self.database_progress_bar.setVisible(True)

        self.database_progress_file.setText("")
        self.database_progress_file.setVisible(False)

        imported = int(stats.get("imported_journals", 0))
        skipped = int(stats.get("skipped_journals", 0))

        if imported == 0:
            message = (
                "Keine neuen Journal-Daten gefunden.\n\n"
                f"Unverändert übersprungen: {skipped}\n"
                f"Systeme: {stats.get('systems', 0)}\n"
                f"Körper: {stats.get('bodies', 0)}\n"
                f"Materialien: {stats.get('materials', 0)}\n"
                f"Journale: {stats.get('journal_imports', 0)}"
            )
        else:
            message = (
                "Journal-Archiv erfolgreich aktualisiert.\n\n"
                f"Neu/geändert importiert: {imported}\n"
                f"Unverändert übersprungen: {skipped}\n"
                f"Systeme: {stats.get('systems', 0)}\n"
                f"Körper: {stats.get('bodies', 0)}\n"
                f"Materialien: {stats.get('materials', 0)}\n"
                f"Journale: {stats.get('journal_imports', 0)}"
            )

        QMessageBox.information(self, "Datenbank", message)

    def _release_update_worker(self):
        self._update_worker = None

    def _set_update_status(
        self,
        text,
        ok=None,
    ):
        if not hasattr(self, "update_status_label"):
            return

        self.update_status_label.setText(str(text))

        if ok is True:
            self.update_status_label.setObjectName("statusOk")
        elif ok is False:
            self.update_status_label.setObjectName("statusWarn")
        else:
            self.update_status_label.setObjectName("muted")

        self.update_status_label.style().unpolish(self.update_status_label)
        self.update_status_label.style().polish(self.update_status_label)

    @staticmethod
    def _release_requires_database_update(result):
        """
        Ein GitHub-Release kann in den Release-Notes mit

            DB-UPDATE: <Version>

        markieren, dass nach diesem Programmupdate die lokale
        CMDRHelper-Datenbank einmalig neu aufgebaut/aktualisiert wird.

        Ohne diesen Marker erscheint kein Datenbank-Hinweis.
        """
        notes = str((result or {}).get("release_notes") or "")

        return bool(
            re.search(
                r"(?im)^\\s*DB-UPDATE\\s*:\\s*\\d+\\s*$",
                notes,
            )
        )

    def _update_question_text(
        self,
        result,
        latest,
    ):
        text = (
            "Eine neue Version von CMDRHelper ist verfügbar.\n\n"
            f"Installiert: {__version__}\n"
            f"Verfügbar: {latest}"
        )

        if self._release_requires_database_update(result):
            text += (
                "\n\n"
                "DATENBANK-AKTUALISIERUNG\n"
                "Dieses Update erweitert die CMDRHelper-Datenbank.\n"
                "Nach der Installation wird das Journal-Archiv einmal "
                "neu ausgewertet. Je nach Umfang des Archivs kann dies "
                "einige Minuten dauern.\n"
                "Deine vorhandenen Daten bleiben erhalten."
            )

        text += "\n\n" "Möchtest du das Update jetzt installieren?"

        return text

    def _check_for_updates(
        self,
        automatic=False,
    ):
        if self._update_check_running:
            return

        self._update_check_running = True

        if hasattr(self, "update_check_button"):
            self.update_check_button.setEnabled(False)

        if not automatic:
            self._set_update_status("GitHub wird geprüft …")

        # Worker als Instanzvariable halten. So bleibt das Python-Objekt
        # garantiert bis zum Ende der GitHub-Anfrage erhalten.
        self._update_worker = UpdateCheckWorker(
            owner="Faber38",
            repository="CMDRHelper",
            current_version=__version__,
        )

        self._update_worker.signals.finished.connect(
            lambda result: self._update_check_finished(result, automatic)
        )

        self.update_thread_pool.start(self._update_worker)

    def _update_check_finished(
        self,
        result,
        automatic=False,
    ):
        self._update_check_running = False

        # Erst nach Rückkehr in die Qt-Ereignisschleife freigeben.
        # So wird der Worker nicht während seines finished-Signals zerstört.
        QTimer.singleShot(0, self._release_update_worker)

        if hasattr(self, "update_check_button"):
            self.update_check_button.setEnabled(True)

        if not isinstance(result, dict):
            self._set_update_status("Updateprüfung fehlgeschlagen.", False)
            return

        if not result.get("ok"):
            # Beim automatischen Startcheck keine störende Fehlermeldung
            # anzeigen. Der Status bleibt unter Einstellungen sichtbar.
            error = result.get("error") or "GitHub konnte nicht geprüft werden."

            self._set_update_status(error, False)

            if not automatic:
                QMessageBox.warning(self, "Updateprüfung", error)
            return

        latest = result.get("version") or ""

        if latest and is_newer_version(
            latest,
            __version__,
        ):
            text = f"Update verfügbar: {latest} " f"(installiert: {__version__})"

            self._set_update_status(text, False)

            if automatic and not self._update_notice_shown:
                self._update_notice_shown = True

                answer = QMessageBox.question(
                    self,
                    "CMDRHelper – Update verfügbar",
                    self._update_question_text(
                        result,
                        latest,
                    ),
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.Yes,
                )

                if answer == QMessageBox.Yes:
                    self._install_update(result)

            elif not automatic:
                answer = QMessageBox.question(
                    self,
                    "CMDRHelper – Update verfügbar",
                    self._update_question_text(
                        result,
                        latest,
                    ),
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.Yes,
                )

                if answer == QMessageBox.Yes:
                    self._install_update(result)

            return

        self._set_update_status(f"CMDRHelper {__version__} ist aktuell.", True)

        if not automatic:
            QMessageBox.information(
                self,
                "Updateprüfung",
                (f"CMDRHelper {__version__} " "ist auf dem aktuellen Stand."),
            )

    def _install_update(self, result):
        latest = str(result.get("version") or "").strip()

        asset_name = str(result.get("asset_name") or "").strip()

        asset_url = str(result.get("asset_url") or "").strip()

        if not asset_url:
            QMessageBox.warning(
                self,
                "CMDRHelper – Update",
                (
                    f"Für Version {latest} wurde kein passendes "
                    "CMDRHelper-ZIP im GitHub-Release gefunden.\n\n"
                    "Bitte das Release-ZIP auf GitHub prüfen."
                ),
            )
            return

        self._set_update_status(f"Update {latest} wird heruntergeladen …")

        if hasattr(self, "update_check_button"):
            self.update_check_button.setEnabled(False)

        QApplication.processEvents()

        try:
            zip_path = download_release(result)

            # main_window.py liegt unter cmdrhelper/ui/.
            # Zwei Ebenen höher liegt das Installationsverzeichnis.
            install_dir = Path(__file__).resolve().parents[2]

            launch_installer(
                zip_path=zip_path,
                install_dir=install_dir,
                current_version=__version__,
                latest_version=latest,
                parent_pid=os.getpid(),
            )

        except Exception as exc:
            if hasattr(self, "update_check_button"):
                self.update_check_button.setEnabled(True)

            self._set_update_status(f"Update fehlgeschlagen: {exc}", False)

            QMessageBox.critical(
                self,
                "CMDRHelper – Update fehlgeschlagen",
                (
                    "Das Update konnte nicht vorbereitet werden.\n\n"
                    f"{exc}\n\n"
                    "CMDRHelper wurde nicht verändert."
                ),
            )
            return

        install_message = (
            f"CMDRHelper {latest} wurde heruntergeladen.\n\n"
            "CMDRHelper wird jetzt beendet. "
            "Der Updater erstellt zuerst ein Backup der bisherigen "
            "Programmversion und installiert danach das neue Release.\n\n"
            "Der Ordner data/ mit deiner Datenbank bleibt unangetastet."
        )

        if self._release_requires_database_update(result):
            install_message += (
                "\n\n"
                "Nach dem Neustart wird die Datenbank einmalig "
                "aktualisiert und das Journal-Archiv neu ausgewertet."
            )

        QMessageBox.information(self, "CMDRHelper – Update", install_message)

        QApplication.quit()

    def _saved_ui_font_size(self, fallback=10):
        try:
            value = int(
                self.state.settings.value(
                    "ui_font_size",
                    fallback if fallback and fallback > 0 else 10,
                )
                or fallback
                or 10
            )
        except (TypeError, ValueError):
            value = fallback if fallback and fallback > 0 else 10

        return max(7, min(24, int(value)))

    def _font_stylesheet_suffix(self, family=None, size=None):
        """
        Ergänzt die Theme-QSS um die vom Benutzer gewählte Basisschrift.

        QApplication.setFont() allein reicht hier nicht zuverlässig aus,
        weil das CMDRHelper-Stylesheet eigene Font-Angaben enthalten kann.
        Die Theme-Datei setzt die Grundgröße explizit auf QWidget.
        Deshalb muss die Benutzergröße ebenfalls über QWidget gesetzt werden.
        Die Titelgrößen werden proportional zur gewählten Grundgröße angepasst.
        """
        app = QApplication.instance()

        if family is None:
            family = getattr(self, "_active_ui_font_family", "")
        if size is None:
            size = getattr(self, "_active_ui_font_size", 0)

        if not family and app is not None:
            family = app.font().family()

        try:
            size = int(size)
        except (TypeError, ValueError):
            size = 10

        size = max(7, min(24, size or 10))
        safe_family = str(family or "").replace("\\", "\\\\").replace('"', '\\"')

        # WICHTIG:
        # Das Theme setzt seine Grundgröße über "QWidget { font-size: 12px; }".
        # Ein nachgestelltes "*"-Rule ist in Qt nicht spezifisch genug, um
        # diese QWidget-Regel zuverlässig zu überschreiben. Deshalb setzen
        # wir die Benutzergröße ebenfalls explizit auf QWidget.
        #
        # Spezielle Titelregeln (appTitle, commanderTitle, sectionTitle,
        # cardValue) bleiben absichtlich relativ größer als die Grundschrift.
        title_size = max(size + 5, int(round(size * 1.45)))
        section_size = max(size + 1, int(round(size * 1.10)))

        return (
            "\n\n/* CMDRHelper Benutzer-Schrift */\n"
            f'QWidget {{ font-family: "{safe_family}"; font-size: {size}pt; }}\n'
            f'QToolTip {{ font-family: "{safe_family}"; font-size: {size}pt; }}\n'
            f'QLabel#appTitle {{ font-family: "{safe_family}"; '
            f"font-size: {title_size}pt; }}\n"
            f'QLabel#commanderTitle {{ font-family: "{safe_family}"; '
            f"font-size: {title_size}pt; }}\n"
            f'QLabel#cardValue {{ font-family: "{safe_family}"; '
            f"font-size: {title_size}pt; }}\n"
            f'QLabel#sectionTitle {{ font-family: "{safe_family}"; '
            f"font-size: {section_size}pt; }}\n"
        )

    def _apply_saved_ui_font(self):
        app = QApplication.instance()
        if app is None:
            return

        default_font = app.font()

        family = str(
            self.state.settings.value(
                "ui_font_family",
                default_font.family(),
            )
            or default_font.family()
        ).strip()

        size = self._saved_ui_font_size(default_font.pointSize())

        # Aktiver Wert wird beim Programmstart eingefroren. Änderungen in
        # den Einstellungen gelten bewusst erst nach dem nächsten Neustart.
        self._active_ui_font_family = family
        self._active_ui_font_size = size

        app.setFont(QFont(family, size))

        base_stylesheet = (
            LIGHT_STYLESHEET if self.ui_theme == "light" else DARK_STYLESHEET
        )
        app.setStyleSheet(base_stylesheet + self._font_stylesheet_suffix(family, size))

    def _save_ui_font_settings(self):
        family = self.ui_font_combo.currentFont().family()
        size = int(self.ui_font_size_spin.value())

        self.state.settings.setValue("ui_font_family", family)
        self.state.settings.setValue("ui_font_size", size)
        self.state.settings.sync()

        # Nicht sofort anwenden: Einige QSS-Regeln übersteuern die Qt-
        # Standardschrift. Ein sauberer kompletter Neuaufbau beim Neustart
        # vermeidet Mischzustände in bereits existierenden Widgets.
        self.ui_font_status.setText("✓ gespeichert · Neustart erforderlich")
        self.ui_font_status.setStyleSheet("color: #ffb000; font-weight: 600;")

    def _set_theme(self, theme):
        theme = "light" if str(theme).lower() == "light" else "dark"

        self.ui_theme = theme

        self.state.settings.setValue("ui_theme", theme)

        app = QApplication.instance()

        if app is not None:
            base_stylesheet = LIGHT_STYLESHEET if theme == "light" else DARK_STYLESHEET
            app.setStyleSheet(base_stylesheet + self._font_stylesheet_suffix())

        if hasattr(self, "system_map"):
            self.system_map.set_light_mode(theme == "light")

        if self._chronicle_system_window is not None and hasattr(
            self._chronicle_system_window, "system_map"
        ):
            self._chronicle_system_window.system_map.set_light_mode(theme == "light")

    def _set_explorer_value_threshold(self, value):
        value = max(0, int(value or 0))
        self.state.settings.setValue(
            "explorer_value_yellow_threshold",
            value,
        )
        self.state.settings.sync()

        if hasattr(self, "explorer_value_table"):
            self._refresh_explorer_tables()

    def _explorer_value_yellow_threshold(self):
        try:
            return max(
                0,
                int(
                    self.state.settings.value(
                        "explorer_value_yellow_threshold",
                        200_000,
                    )
                    or 200_000
                ),
            )
        except (TypeError, ValueError):
            return 200_000

    def _reset_missions(self):
        answer = QMessageBox.question(
            self,
            "Missionen zurücksetzen",
            (
                "Soll die bisherige Missionshistorie in CMDRHelper "
                "wirklich zurückgesetzt werden?\n\n"
                "Alte Missionen vor diesem Zeitpunkt werden danach "
                "nicht mehr aus dem Journal übernommen."
            ),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if answer == QMessageBox.Yes:
            self.state.reset_missions()

    def _set_service_test_status(
        self,
        label,
        ok,
        text,
    ):
        label.setText(("✓ " if ok else "✗ ") + text)
        label.setObjectName("statusOk" if ok else "statusWarn")
        label.style().unpolish(label)
        label.style().polish(label)

    def _test_edsm_connection(self):
        self.edsm_test_button.setEnabled(False)
        self.edsm_test_status.setText("Verbindung wird getestet …")

        try:
            ok, text = test_edsm_connection(
                self.edsm_commander_edit.text(),
                self.edsm_api_key_edit.text(),
            )
            self._set_service_test_status(
                self.edsm_test_status,
                ok,
                text,
            )
        finally:
            self.edsm_test_button.setEnabled(True)

    def _test_inara_connection(self):
        self.inara_test_button.setEnabled(False)
        self.inara_test_status.setText("Verbindung wird getestet …")

        try:
            ok, text = test_inara_connection(
                self.inara_commander_edit.text(),
                self.inara_api_key_edit.text(),
            )
            self._set_service_test_status(
                self.inara_test_status,
                ok,
                text,
            )
        finally:
            self.inara_test_button.setEnabled(True)

    def _save_online_settings(self):
        self.state.set_edsm_settings(
            commander=self.edsm_commander_edit.text(),
            api_key=self.edsm_api_key_edit.text(),
            enabled=self.edsm_enabled_check.isChecked(),
        )

        self.state.set_inara_settings(
            commander=self.inara_commander_edit.text(),
            api_key=self.inara_api_key_edit.text(),
            enabled=self.inara_enabled_check.isChecked(),
        )

        self.state.refresh()

        QMessageBox.information(
            self, "Online-Dienste", "EDSM- und Inara-Einstellungen wurden gespeichert."
        )

    def _journal_file_diagnostics(self):
        """
        Diagnose direkt aus dem gewählten Journalordner.
        Zeigt, ob neuere Dateien vorhanden sind als der letzte
        von CMDRHelper gelesene Journal-Eintrag.
        """
        folder = self.state.journal_folder

        if not folder:
            return None

        try:
            folder = Path(folder)

            if not folder.is_dir():
                return None

            files = [path for path in folder.glob("Journal*.log") if path.is_file()]

            if not files:
                return None

            files.sort(key=lambda path: path.stat().st_mtime)

            oldest = files[0]
            newest = files[-1]

            oldest_dt = datetime.fromtimestamp(oldest.stat().st_mtime)
            newest_dt = datetime.fromtimestamp(newest.stat().st_mtime)

            return {
                "oldest_time": oldest_dt.strftime("%d.%m.%Y %H:%M:%S"),
                "newest_time": newest_dt.strftime("%d.%m.%Y %H:%M:%S"),
                "newest_name": newest.name,
            }

        except Exception as exc:
            return {
                "oldest_time": "Fehler",
                "newest_time": "Fehler",
                "newest_name": str(exc),
            }

    def choose_journal_folder(self):
        start = str(self.state.journal_folder or Path.home())

        folder = QFileDialog.getExistingDirectory(
            self, "Elite-Dangerous-Journalordner wählen", start
        )

        if folder:
            self.state.set_journal_folder(Path(folder))

    @staticmethod
    def _format_timestamp(value):
        if not value:
            return "–"

        try:
            dt = datetime.fromisoformat(value.replace("Z", "+00:00"))

            return dt.strftime("%d.%m.%Y %H:%M:%S")

        except ValueError:
            return value

    @staticmethod
    def _format_expiry(value):
        if not value:
            return "–"

        try:
            dt = datetime.fromisoformat(value.replace("Z", "+00:00"))

            return dt.strftime("%d.%m.%Y %H:%M")

        except ValueError:
            return value

    @staticmethod
    def _format_reward(value):
        return f"{int(value or 0):,} Cr".replace(",", ".")

    @staticmethod
    def _place_text(mission):
        if mission.destination_body:
            if mission.destination_station:
                return f"{mission.destination_body} / " f"{mission.destination_station}"

            return mission.destination_body

        if mission.destination_station:
            return mission.destination_station

        if mission.target:
            return mission.target

        return "–"

    def _mission_selection_changed(self):
        selected = self.missions_table.selectionModel().selectedRows()

        if not selected:
            self.mission_detail_title.setText("Keine Mission ausgewählt")

            self.mission_detail_text.setText("Wähle oben eine Mission aus.")

            self.mission_progress_text.setText("")

            return

        row = selected[0].row()

        if row < 0 or row >= len(self.state.missions):
            return

        mission = self.state.missions[row]

        self.mission_detail_title.setText(mission.name or "Mission")

        self.mission_detail_text.setText(mission.summary)

        progress = []

        if mission.progress_text:
            progress.append(f"Fortschritt: {mission.progress_text}")

        progress.append(f"Status: {mission.status}")

        progress.append(f"Nächster Schritt: {mission.next_step}")

        self.mission_progress_text.setText("   ·   ".join(progress))

    def refresh_all(self):
        commander = self.state.commander or "–"

        system = self.state.system or "–"

        self.commander_label.setText(f"CMDR {commander}")

        self.ship_label.setText(self.state.ship or "")

        self.last_import_label.setText(
            "Letzter Journal-Eintrag: "
            + self._format_timestamp(self.state.last_timestamp)
        )

        self.connection_label.setText(
            "● Journal erkannt" if self.state.connected else "● Journal nicht erkannt"
        )

        self.connection_label.setObjectName(
            "statusOk" if self.state.connected else "statusWarn"
        )

        self.connection_label.style().unpolish(self.connection_label)

        self.connection_label.style().polish(self.connection_label)

        edsm_status = getattr(
            self.state,
            "edsm_upload_status",
            "disabled",
        )
        edsm_message = getattr(
            self.state,
            "edsm_upload_message",
            "",
        )

        if edsm_status == "ok":
            self.edsm_upload_label.setText("● EDSM Übertragung")
            self.edsm_upload_label.setObjectName("statusOk")
        elif edsm_status == "error":
            self.edsm_upload_label.setText("● EDSM Fehler")
            self.edsm_upload_label.setObjectName("statusWarn")
        elif edsm_status == "waiting":
            self.edsm_upload_label.setText("● EDSM wartet")
            self.edsm_upload_label.setObjectName("muted")
        else:
            self.edsm_upload_label.setText("● EDSM aus")
            self.edsm_upload_label.setObjectName("muted")

        self.edsm_upload_label.setToolTip(
            edsm_message or "Status der automatischen EDSM-Journalübertragung"
        )
        self.edsm_upload_label.style().unpolish(self.edsm_upload_label)
        self.edsm_upload_label.style().polish(self.edsm_upload_label)

        # INARA-Anzeige vorbereiten. Bis der automatische INARA-Uploader
        # eingebaut ist, zeigt sie nur Aktiv/Inaktiv an.
        if getattr(self.state, "inara_enabled", False):
            self.inara_upload_label.setText("● INARA wartet")
            self.inara_upload_label.setObjectName("muted")
            self.inara_upload_label.setToolTip(
                "INARA ist aktiviert. Automatische Journalübertragung folgt."
            )
        else:
            self.inara_upload_label.setText("● INARA aus")
            self.inara_upload_label.setObjectName("muted")
            self.inara_upload_label.setToolTip(
                "INARA ist in den Einstellungen deaktiviert."
            )

        self.inara_upload_label.style().unpolish(self.inara_upload_label)
        self.inara_upload_label.style().polish(self.inara_upload_label)

        self.sidebar_system.setText(f"Aktuelles System\n{system}")

        body_station = []

        if self.state.body:
            body_station.append(self.state.body)

        if self.state.station:
            body_station.append(self.state.station)

        self.sidebar_body.setText(" / ".join(body_station))

        self.current_system_value.setText(system)

        place_parts = []
        if self.state.body:
            place_parts.append(self.state.body)
        if self.state.station:
            place_parts.append(self.state.station)
        place_text = " / ".join(place_parts) if place_parts else "–"
        self.current_place_value.setText(place_text)

        self.overview_commander.setText(f"CMDR {commander}")

        ship_text = self.state.ship or "–"
        self.overview_ship.setText(f"Schiff: {ship_text}")
        self.overview_location.setText(
            f"Standort: {system}" + (f" · {place_text}" if place_text != "–" else "")
        )

        mission_count = len(self.state.missions)
        self.active_missions_value.setText(str(mission_count))

        mission_total_reward = sum(
            int(getattr(mission, "reward", 0) or 0) for mission in self.state.missions
        )

        if hasattr(self, "mission_total_reward_label"):
            self.mission_total_reward_label.setText(
                "Gesamtbelohnung: " + self._format_reward(mission_total_reward)
            )

        ready_count = sum(
            1
            for m in self.state.missions
            if m.status in ("Aufgabe erledigt", "Daten erhalten")
            or "Missionsterminal" in (m.next_step or "")
        )

        if mission_count == 0:
            self.mission_start_status.setText("keine offenen Missionen")
        elif ready_count:
            still_active = mission_count - ready_count
            parts = [f"{ready_count} bereit zur Abgabe"]
            if still_active:
                parts.append(f"{still_active} noch aktiv")
            self.mission_start_status.setText(" · ".join(parts))
        else:
            self.mission_start_status.setText(f"{mission_count} noch aktiv")

        self.journal_count_value.setText(str(self.state.journal_files))

        if self.state.connected:
            self.overview_journal_state.setText("● erkannt / Live-Überwachung aktiv")
            self.overview_journal_state.setObjectName("statusOk")
        else:
            self.overview_journal_state.setText("● nicht erkannt")
            self.overview_journal_state.setObjectName("statusWarn")
        self.overview_journal_state.style().unpolish(self.overview_journal_state)
        self.overview_journal_state.style().polish(self.overview_journal_state)

        if self.state.connected:
            self.overview_status.setText(
                f"Journaldaten erkannt. "
                f"Commander: {commander} · "
                f"System: {system} · "
                f"{len(self.state.missions)} "
                f"aktive Mission(en)."
            )

        else:
            self.overview_status.setText(
                "Noch keine Elite-Dangerous-"
                "Journaldaten erkannt. "
                "Bitte unter Einstellungen "
                "den Journalordner prüfen."
            )

        scanned_count = sum(
            1 for body in self.state.system_bodies if body.get("journal_scanned", True)
        )

        known_count = len(self.state.system_bodies)

        total_count = max(
            int(self.state.system_body_count or 0),
            int(getattr(self.state, "edsm_body_count", 0) or 0),
            known_count,
        )

        signal_count = self.state.system_signals_count

        # Belt Cluster können in Scan-Events auftauchen, zählen aber nicht
        # immer 1:1 zum FSS-BodyCount. Deshalb nicht irreführend >100% zeigen.
        displayed_scanned = (
            min(scanned_count, total_count) if total_count else scanned_count
        )

        bio_body_count = sum(
            1
            for body in self.state.system_bodies
            if int(body.get("biological_signals") or 0) > 0
        )

        geo_body_count = sum(
            1
            for body in self.state.system_bodies
            if int(body.get("geological_signals") or 0) > 0
        )

        scan_status = f"{displayed_scanned} / {total_count} Körper selbst im Journal"

        edsm_added = int(getattr(self.state, "edsm_added_count", 0) or 0)

        edsm_known = int(getattr(self.state, "edsm_body_count", 0) or 0)

        if self.state.edsm_enabled and edsm_known:
            scan_status += f" · EDSM bekannt: {edsm_known}"

            if edsm_added:
                scan_status += f" (+{edsm_added} ergänzt)"

        if self.state.system_all_bodies_found:
            scan_status += " · alle Körper gefunden"

        if signal_count:
            scan_status += f" · {signal_count} Signale"

        if bio_body_count:
            scan_status += f" · BIO auf {bio_body_count} Körper(n)"

        if geo_body_count:
            scan_status += f" · GEO auf {geo_body_count} Körper(n)"

        current_value = int(getattr(self.state, "system_current_value", 0) or 0)

        scan_status += (
            f"   |   Nur Scans: "
            f"{self._format_reward(self.state.system_scan_value)}"
            f"   |   Aktuell erreicht: "
            f"{self._format_reward(current_value)}"
            f"   |   Komplett kartiert: "
            f"{self._format_reward(self.state.system_mapped_value)}"
        )

        if self.state.system_high_value_count:
            scan_status += (
                f"   |   ★ {self.state.system_high_value_count} Körper > 200.000 Cr"
            )

        self.system_scan_header.setText(scan_status)

        bio_count = int(getattr(self.state, "system_bio_completed_count", 0) or 0)
        bio_value = int(getattr(self.state, "system_bio_value", 0) or 0)
        bio_first_logged = int(
            getattr(self.state, "system_bio_first_logged_value", 0) or 0
        )
        bio_unknown = list(getattr(self.state, "system_bio_unknown", []) or [])

        if bio_count:
            bio_status = (
                f"BIO vollständig: {bio_count}"
                f"   |   Basiswert: {self._format_reward(bio_value)}"
                f"   |   bei First Logged ×5: "
                f"{self._format_reward(bio_first_logged)}"
            )

            if bio_unknown:
                bio_status += f"   |   ⚠ {len(bio_unknown)} Art(en) ohne Wert"
        else:
            bio_status = "BIO: noch keine vollständig analysierten Proben"

        self.system_bio_header.setText(bio_status)

        unsold_cartography = int(
            getattr(self.state, "unsold_cartography_value", 0) or 0
        )
        unsold_cartography_count = int(
            getattr(self.state, "unsold_cartography_count", 0) or 0
        )
        unsold_bio = int(getattr(self.state, "unsold_bio_value", 0) or 0)
        unsold_bio_first = int(
            getattr(self.state, "unsold_bio_first_logged_value", 0) or 0
        )
        unsold_bio_count = int(getattr(self.state, "unsold_bio_count", 0) or 0)
        unsold_bio_unknown = list(getattr(self.state, "unsold_bio_unknown", []) or [])

        open_status = (
            "Noch nicht abgegeben   |   "
            f"Kartographie: {self._format_reward(unsold_cartography)} "
            f"({unsold_cartography_count} Körper)   |   "
            f"BIO: {self._format_reward(unsold_bio)} "
            f"({unsold_bio_count} Probe(n))"
        )
        if unsold_bio:
            open_status += (
                "   |   BIO bei First Logged ×5: "
                f"{self._format_reward(unsold_bio_first)}"
            )
        if unsold_bio_unknown:
            open_status += f"   |   ⚠ {len(unsold_bio_unknown)} BIO-Art(en) ohne Wert"

        self.unsold_explorer_header.setText(open_status)

        self.system_map.set_system(system, self.state.system_bodies)

        if hasattr(self, "explorer_value_table"):
            self._refresh_explorer_tables()
            self._refresh_explorer_live_windows()

        self.journal_path_edit.setText(str(self.state.journal_folder or ""))

        self.journal_file_count.setText(str(self.state.journal_files))

        diagnostics = self._journal_file_diagnostics()

        if diagnostics:
            self.journal_oldest_file.setText(diagnostics.get("oldest_time", "–"))
            self.journal_newest_file.setText(diagnostics.get("newest_time", "–"))
            self.journal_newest_name.setText(diagnostics.get("newest_name", "–"))
        else:
            self.journal_oldest_file.setText("–")
            self.journal_newest_file.setText("–")
            self.journal_newest_name.setText("–")

        self.journal_last_read.setText(
            self._format_timestamp(self.state.last_timestamp)
        )

        current_row = self.missions_table.currentRow()

        self.missions_table.setRowCount(len(self.state.missions))

        for row, mission in enumerate(self.state.missions):
            values = [
                mission.name,
                mission.destination_system or "–",
                self._place_text(mission),
                mission.status,
                mission.next_step,
                self._format_reward(mission.reward),
                self._format_expiry(mission.expiry),
            ]

            for col, value in enumerate(values):
                item = QTableWidgetItem(str(value or ""))

                if col == 3:
                    if mission.status in (
                        "Aufgabe erledigt",
                        "Daten erhalten",
                        "Am Missionsziel",
                    ):
                        item.setForeground(Qt.green)

                self.missions_table.setItem(row, col, item)

        if 0 <= current_row < self.missions_table.rowCount():
            self.missions_table.selectRow(current_row)
        else:
            self._mission_selection_changed()
