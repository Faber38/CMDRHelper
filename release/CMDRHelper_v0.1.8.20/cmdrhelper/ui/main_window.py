from __future__ import annotations

from datetime import datetime
from pathlib import Path

from cmdrhelper.ui.system_view import SystemMapWidget
from cmdrhelper.ui.body_detail_window import BodyDetailWindow
from cmdrhelper.online_services import (
    test_edsm_connection,
    test_inara_connection,
)
from cmdrhelper.version import __version__

from PySide6.QtCore import Qt
from cmdrhelper.ui.styles import DARK_STYLESHEET, LIGHT_STYLESHEET

from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QStackedWidget,
    QFileDialog,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QFormLayout,
    QLineEdit,
    QScrollArea,
    QSplitter,
    QMessageBox,
    QCheckBox,
    QRadioButton,
    QButtonGroup,
    QApplication,
)


class MainWindow(QMainWindow):
    def __init__(self, state):
        super().__init__()

        self.state = state
        self.nav_buttons = []
        self.ui_theme = str(
            self.state.settings.value(
                "ui_theme",
                "dark"
            )
        ).lower()

        self.setWindowTitle(
            f"CMDRHelper {__version__}"
        )

        self._build_ui()

        self.state.changed.connect(
            self.refresh_all
        )

        self.refresh_all()

    def _nav(self, text, idx):
        button = QPushButton(text)

        button.clicked.connect(
            lambda: self._show_page(idx)
        )

        self.nav_buttons.append(button)

        return button

    def _show_page(self, idx):
        self.pages.setCurrentIndex(idx)

        for i, button in enumerate(
            self.nav_buttons
        ):
            button.setObjectName(
                "navActive"
                if i == idx
                else ""
            )

            button.style().unpolish(button)
            button.style().polish(button)

    def _card(self, title):
        frame = QFrame(
            objectName="card"
        )

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(
            10,
            4,
            10,
            4
        )

        layout.addWidget(
            QLabel(
                title,
                objectName="sectionTitle"
            )
        )

        return frame, layout

    def _build_ui(self):
        root = QWidget()
        self.setCentralWidget(root)

        main = QHBoxLayout(root)
        main.setContentsMargins(0, 0, 0, 0)
        main.setSpacing(0)

        side_frame = QFrame(
            objectName="sidebar"
        )

        side_frame.setFixedWidth(210)

        side = QVBoxLayout(side_frame)
        side.setContentsMargins(
            12,
            12,
            12,
            12
        )

        side.addWidget(
            QLabel(
                "✦  CMDRHelper",
                objectName="appTitle"
            )
        )

        side.addWidget(
            QLabel(
                "Dein Missions- & Explorer-Tool",
                objectName="appSubTitle"
            )
        )

        side.addSpacing(20)

        side.addWidget(
            self._nav(
                "⌂  Übersicht",
                0
            )
        )

        side.addWidget(
            self._nav(
                "◎  Missionen",
                1
            )
        )

        side.addWidget(
            self._nav(
                "✦  Explorer",
                2
            )
        )

        side.addWidget(
            self._nav(
                "⚙  Einstellungen",
                3
            )
        )

        side.addStretch()

        self.sidebar_system = QLabel(
            "Aktuelles System\n–"
        )
        self.sidebar_system.setWordWrap(True)
        side.addWidget(self.sidebar_system)

        self.sidebar_body = QLabel(
            "",
            objectName="muted"
        )
        self.sidebar_body.setWordWrap(True)
        side.addWidget(self.sidebar_body)

        side.addWidget(
            QLabel(
                f"CMDRHelper {__version__}",
                objectName="appSubTitle"
            )
        )

        main.addWidget(side_frame)

        right = QWidget()

        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(
            0,
            0,
            0,
            0
        )
        right_layout.setSpacing(0)

        top_frame = QFrame(
            objectName="topbar"
        )

        top = QHBoxLayout(top_frame)

        self.commander_label = QLabel(
            "CMDR –",
            objectName="commanderTitle"
        )

        self.ship_label = QLabel(
            "",
            objectName="muted"
        )

        self.last_import_label = QLabel(
            "Letzter Journal-Eintrag: –",
            objectName="muted"
        )

        self.connection_label = QLabel(
            "● Journal nicht erkannt",
            objectName="statusWarn"
        )

        top.addWidget(
            self.commander_label
        )

        top.addWidget(
            self.ship_label
        )

        top.addStretch()

        top.addWidget(
            self.last_import_label
        )

        top.addSpacing(16)

        top.addWidget(
            self.connection_label
        )

        right_layout.addWidget(
            top_frame
        )

        self.pages = QStackedWidget()

        self.pages.addWidget(
            self._overview()
        )

        self.pages.addWidget(
            self._missions()
        )

        self.pages.addWidget(
            self._explorer()
        )

        self.pages.addWidget(
            self._settings()
        )

        right_layout.addWidget(
            self.pages,
            1
        )

        main.addWidget(
            right,
            1
        )

        self._show_page(0)

    def _overview(self):
        page = QWidget()

        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(10, 6, 10, 6)
        page_layout.setSpacing(6)

        page_layout.addWidget(
            QLabel("Übersicht", objectName="sectionTitle")
        )

        identity_row = QHBoxLayout()
        identity_row.setSpacing(6)

        identity_card, identity_layout = self._card(
            "COMMANDER & SCHIFF"
        )

        self.overview_commander = QLabel(
            "CMDR –",
            objectName="cardValue"
        )
        identity_layout.addWidget(self.overview_commander)

        self.overview_ship = QLabel("Schiff: –")
        self.overview_ship.setWordWrap(True)
        identity_layout.addWidget(self.overview_ship)

        self.overview_location = QLabel(
            "Standort: –",
            objectName="muted"
        )
        self.overview_location.setWordWrap(True)
        identity_layout.addWidget(self.overview_location)

        identity_row.addWidget(identity_card, 2)

        journal_card, journal_layout = self._card("JOURNAL")

        self.journal_count_value = QLabel(
            "0",
            objectName="cardValue"
        )
        journal_layout.addWidget(self.journal_count_value)

        journal_layout.addWidget(
            QLabel(
                "Journaldateien erkannt",
                objectName="muted"
            )
        )

        self.overview_journal_state = QLabel(
            "● nicht erkannt",
            objectName="statusWarn"
        )
        journal_layout.addWidget(self.overview_journal_state)

        identity_row.addWidget(journal_card, 1)
        page_layout.addLayout(identity_row)

        row = QHBoxLayout()
        row.setSpacing(6)

        mission_card, mission_layout = self._card("MISSIONEN")

        self.active_missions_value = QLabel(
            "0",
            objectName="cardValue"
        )
        mission_layout.addWidget(self.active_missions_value)

        self.mission_start_status = QLabel(
            "keine offenen Missionen",
            objectName="muted"
        )
        self.mission_start_status.setWordWrap(True)
        mission_layout.addWidget(self.mission_start_status)

        mission_button = QPushButton(
            "Missionen →",
            objectName="primary"
        )
        mission_button.clicked.connect(
            lambda: self._show_page(1)
        )
        mission_layout.addWidget(mission_button)

        row.addWidget(mission_card, 1)

        location_card, location_layout = self._card(
            "AKTUELLER STANDORT"
        )

        self.current_system_value = QLabel(
            "–",
            objectName="cardValue"
        )
        self.current_system_value.setWordWrap(True)
        location_layout.addWidget(self.current_system_value)

        self.current_place_value = QLabel(
            "–",
            objectName="muted"
        )
        self.current_place_value.setWordWrap(True)
        location_layout.addWidget(self.current_place_value)

        explorer_button = QPushButton(
            "System im Explorer →",
            objectName="primary"
        )
        explorer_button.clicked.connect(
            lambda: self._show_page(2)
        )
        location_layout.addWidget(explorer_button)

        row.addWidget(location_card, 1)
        page_layout.addLayout(row)

        status_card, status_layout = self._card("LETZTER STAND")

        self.overview_status = QLabel(
            "Noch keine Journaldaten erkannt."
        )
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

        page_layout.addWidget(
            QLabel("Explorer", objectName="sectionTitle")
        )

        system_card, system_layout = self._card(
            "AKTUELLES SYSTEM"
        )

        self.system_scan_header = QLabel(
            "Noch keine Systemdaten",
            objectName="muted"
        )
        self.system_scan_header.setWordWrap(True)
        system_layout.addWidget(self.system_scan_header)

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
        self.system_map.set_light_mode(
            self.ui_theme == "light"
        )
        self.system_map.bodyClicked.connect(
            self._show_body_details
        )

        scroll = QScrollArea()
        scroll.setWidgetResizable(False)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setWidget(self.system_map)

        system_layout.addWidget(scroll, 1)
        page_layout.addWidget(system_card, 1)

        return page

    def _show_body_details(self, body):
        dialog = BodyDetailWindow(
            body,
            self
        )
        dialog.exec()

    def _save_overview_splitter(self, pos, index):
        if not hasattr(self, "overview_splitter"):
            return

        self.state.settings.setValue(
            "overview_splitter_sizes",
            self.overview_splitter.sizes()
        )

    def reset_overview_splitter(self):
        if not hasattr(self, "overview_splitter"):
            return

        self.overview_splitter.setSizes(
            [220, 675]
        )

        self.state.settings.setValue(
            "overview_splitter_sizes",
            [220, 675]
        )

    def _missions(self):
        page = QWidget()

        layout = QVBoxLayout(page)
        layout.setContentsMargins(
            12,
            10,
            12,
            10
        )
        layout.setSpacing(8)

        header = QHBoxLayout()

        header.addWidget(
            QLabel(
                "Missionen",
                objectName="sectionTitle"
            )
        )

        header.addStretch()

        refresh = QPushButton(
            "Journal aktualisieren",
            objectName="primary"
        )

        refresh.clicked.connect(
            self.state.refresh
        )

        header.addWidget(refresh)

        reset_missions = QPushButton(
            "Missionen zurücksetzen"
        )
        reset_missions.clicked.connect(
            self._reset_missions
        )
        header.addWidget(reset_missions)

        layout.addLayout(header)

        card, card_layout = self._card(
            "AKTIVE MISSIONEN"
        )

        self.missions_table = QTableWidget(
            0,
            7
        )

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

        self.missions_table.setAlternatingRowColors(
            True
        )

        self.missions_table.setEditTriggers(
            QTableWidget.NoEditTriggers
        )

        self.missions_table.setSelectionBehavior(
            QTableWidget.SelectRows
        )

        self.missions_table.verticalHeader().setVisible(
            False
        )

        header_view = (
            self.missions_table.horizontalHeader()
        )

        header_view.setSectionResizeMode(
            0,
            QHeaderView.Stretch
        )

        self.missions_table.setColumnWidth(
            1,
            210
        )

        self.missions_table.setColumnWidth(
            2,
            260
        )

        self.missions_table.setColumnWidth(
            3,
            155
        )

        self.missions_table.setColumnWidth(
            4,
            300
        )

        self.missions_table.setColumnWidth(
            5,
            125
        )

        self.missions_table.setColumnWidth(
            6,
            170
        )

        self.missions_table.itemSelectionChanged.connect(
            self._mission_selection_changed
        )

        card_layout.addWidget(
            self.missions_table
        )

        layout.addWidget(
            card,
            1
        )

        detail_card, detail_layout = self._card(
            "MISSIONSDETAILS"
        )

        self.mission_detail_title = QLabel(
            "Keine Mission ausgewählt"
        )

        self.mission_detail_title.setStyleSheet(
            "font-size: 15px; font-weight: 700;"
        )

        detail_layout.addWidget(
            self.mission_detail_title
        )

        self.mission_detail_text = QLabel(
            "Wähle oben eine Mission aus."
        )

        self.mission_detail_text.setWordWrap(
            True
        )

        self.mission_detail_text.setObjectName(
            "muted"
        )

        detail_layout.addWidget(
            self.mission_detail_text
        )

        self.mission_progress_text = QLabel(
            ""
        )

        self.mission_progress_text.setWordWrap(
            True
        )

        detail_layout.addWidget(
            self.mission_progress_text
        )

        layout.addWidget(
            detail_card
        )

        return page

    def _settings(self):
        page = QWidget()

        layout = QVBoxLayout(page)
        layout.setContentsMargins(
            12,
            10,
            12,
            10
        )
        layout.setSpacing(8)

        layout.addWidget(
            QLabel(
                "Einstellungen",
                objectName="sectionTitle"
            )
        )

        card, card_layout = self._card(
            "JOURNAL"
        )

        form = QFormLayout()

        self.journal_path_edit = QLineEdit()
        self.journal_path_edit.setReadOnly(
            True
        )

        self.journal_file_count = QLabel(
            "0"
        )

        self.journal_oldest_file = QLabel("–")
        self.journal_oldest_file.setWordWrap(True)

        self.journal_newest_file = QLabel("–")
        self.journal_newest_file.setWordWrap(True)

        self.journal_newest_name = QLabel("–")
        self.journal_newest_name.setWordWrap(True)

        self.journal_last_read = QLabel("–")
        self.journal_last_read.setWordWrap(True)

        form.addRow(
            "Journalordner:",
            self.journal_path_edit
        )

        form.addRow(
            "Gefundene Journaldateien:",
            self.journal_file_count
        )

        form.addRow(
            "Älteste Journaldatei:",
            self.journal_oldest_file
        )

        form.addRow(
            "Neueste Journaldatei:",
            self.journal_newest_file
        )

        form.addRow(
            "Neueste Datei:",
            self.journal_newest_name
        )

        form.addRow(
            "Letzter gelesener Eintrag:",
            self.journal_last_read
        )

        card_layout.addLayout(form)

        buttons = QHBoxLayout()

        choose = QPushButton(
            "Journalordner wählen"
        )

        choose.clicked.connect(
            self.choose_journal_folder
        )

        buttons.addWidget(choose)

        refresh = QPushButton(
            "Jetzt einlesen",
            objectName="primary"
        )

        refresh.clicked.connect(
            self.state.refresh
        )

        buttons.addWidget(refresh)
        buttons.addStretch()

        card_layout.addLayout(
            buttons
        )

        layout.addWidget(card)

        online_card, online_layout = self._card(
            "ONLINE-DIENSTE"
        )

        online_layout.addWidget(
            QLabel(
                "Zugangsdaten werden lokal in den CMDRHelper-Einstellungen "
                "gespeichert. Die API-Schlüssel werden in der Oberfläche "
                "verdeckt angezeigt.",
                objectName="muted"
            )
        )

        # -----------------------------
        # EDSM
        # -----------------------------
        edsm_title = QLabel("EDSM")
        edsm_title.setStyleSheet(
            "font-weight: 700;"
        )
        online_layout.addWidget(edsm_title)

        edsm_form = QFormLayout()

        self.edsm_commander_edit = QLineEdit()
        self.edsm_commander_edit.setText(
            self.state.edsm_commander
        )
        self.edsm_commander_edit.setPlaceholderText(
            "Commander-Name"
        )

        self.edsm_api_key_edit = QLineEdit()
        self.edsm_api_key_edit.setText(
            self.state.edsm_api_key
        )
        self.edsm_api_key_edit.setEchoMode(
            QLineEdit.Password
        )
        self.edsm_api_key_edit.setPlaceholderText(
            "EDSM API-Schlüssel"
        )

        self.edsm_enabled_check = QCheckBox(
            "EDSM verwenden"
        )
        self.edsm_enabled_check.setChecked(
            self.state.edsm_enabled
        )

        edsm_form.addRow(
            "Commander-Name:",
            self.edsm_commander_edit
        )
        edsm_form.addRow(
            "API-Schlüssel:",
            self.edsm_api_key_edit
        )
        edsm_form.addRow(
            "",
            self.edsm_enabled_check
        )

        online_layout.addLayout(edsm_form)

        edsm_test_row = QHBoxLayout()

        self.edsm_test_button = QPushButton(
            "EDSM-Verbindung testen"
        )
        self.edsm_test_button.clicked.connect(
            self._test_edsm_connection
        )
        edsm_test_row.addWidget(
            self.edsm_test_button
        )

        self.edsm_test_status = QLabel(
            "Noch nicht getestet",
            objectName="muted"
        )
        self.edsm_test_status.setWordWrap(True)
        edsm_test_row.addWidget(
            self.edsm_test_status,
            1
        )

        online_layout.addLayout(
            edsm_test_row
        )

        # -----------------------------
        # Inara
        # -----------------------------
        inara_title = QLabel("Inara")
        inara_title.setStyleSheet(
            "font-weight: 700;"
        )
        online_layout.addWidget(inara_title)

        inara_form = QFormLayout()

        self.inara_commander_edit = QLineEdit()
        self.inara_commander_edit.setText(
            self.state.inara_commander
        )
        self.inara_commander_edit.setPlaceholderText(
            "Commander-Name"
        )

        self.inara_api_key_edit = QLineEdit()
        self.inara_api_key_edit.setText(
            self.state.inara_api_key
        )
        self.inara_api_key_edit.setEchoMode(
            QLineEdit.Password
        )
        self.inara_api_key_edit.setPlaceholderText(
            "Inara API-Schlüssel"
        )

        self.inara_enabled_check = QCheckBox(
            "Inara verwenden"
        )
        self.inara_enabled_check.setChecked(
            self.state.inara_enabled
        )

        inara_form.addRow(
            "Commander-Name:",
            self.inara_commander_edit
        )
        inara_form.addRow(
            "API-Schlüssel:",
            self.inara_api_key_edit
        )
        inara_form.addRow(
            "",
            self.inara_enabled_check
        )

        online_layout.addLayout(inara_form)

        inara_test_row = QHBoxLayout()

        self.inara_test_button = QPushButton(
            "Inara-Verbindung testen"
        )
        self.inara_test_button.clicked.connect(
            self._test_inara_connection
        )
        inara_test_row.addWidget(
            self.inara_test_button
        )

        self.inara_test_status = QLabel(
            "Noch nicht getestet",
            objectName="muted"
        )
        self.inara_test_status.setWordWrap(True)
        inara_test_row.addWidget(
            self.inara_test_status,
            1
        )

        online_layout.addLayout(
            inara_test_row
        )

        save_online = QPushButton(
            "Online-Zugänge speichern",
            objectName="primary"
        )
        save_online.clicked.connect(
            self._save_online_settings
        )
        online_layout.addWidget(save_online)

        layout.addWidget(online_card)

        database_card, database_layout = self._card(
            "DATENBANK"
        )

        database_layout.addWidget(
            QLabel(
                "CMDRHelper speichert deine eigenen Journal-Entdeckungen "
                "dauerhaft in einer lokalen SQLite-Datenbank. "
                "Der Archivimport liest vorhandene Journaldateien einmalig "
                "ein und ergänzt bekannte Systeme, Körper, Materialien "
                "sowie BIO-/GEO-Daten.",
                objectName="muted"
            )
        )

        self.database_status_label = QLabel(
            "Datenbankstatus wird geladen …",
            objectName="muted"
        )
        self.database_status_label.setWordWrap(True)
        database_layout.addWidget(
            self.database_status_label
        )

        database_buttons = QHBoxLayout()

        self.database_import_button = QPushButton(
            "Journal-Archiv importieren"
        )
        self.database_import_button.clicked.connect(
            self._import_journal_archive
        )
        database_buttons.addWidget(
            self.database_import_button
        )

        database_buttons.addStretch()
        database_layout.addLayout(
            database_buttons
        )

        layout.addWidget(database_card)

        self.state.databaseImportProgress.connect(
            self._database_import_progress
        )
        self.state.databaseImportFinished.connect(
            self._database_import_finished
        )

        self._refresh_database_status()

        ui_card, ui_layout = self._card("OBERFLÄCHE")

        theme_row = QHBoxLayout()

        theme_row.addWidget(
            QLabel("Darstellung:")
        )

        self.theme_group = QButtonGroup(self)

        self.theme_dark_radio = QRadioButton(
            "Dunkel"
        )
        self.theme_light_radio = QRadioButton(
            "Hell"
        )

        self.theme_group.addButton(
            self.theme_dark_radio
        )
        self.theme_group.addButton(
            self.theme_light_radio
        )

        if self.ui_theme == "light":
            self.theme_light_radio.setChecked(True)
        else:
            self.theme_dark_radio.setChecked(True)

        self.theme_dark_radio.toggled.connect(
            lambda checked: (
                self._set_theme("dark")
                if checked
                else None
            )
        )

        self.theme_light_radio.toggled.connect(
            lambda checked: (
                self._set_theme("light")
                if checked
                else None
            )
        )

        theme_row.addWidget(
            self.theme_dark_radio
        )
        theme_row.addWidget(
            self.theme_light_radio
        )
        theme_row.addStretch()

        ui_layout.addLayout(theme_row)

        layout.addWidget(ui_card)
        layout.addStretch()

        return page

    def _refresh_database_status(self):
        if not hasattr(
            self,
            "database_status_label"
        ):
            return

        stats = self.state.database_stats()

        self.database_status_label.setText(
            "Gespeichert: "
            f"{stats.get('systems', 0)} Systeme · "
            f"{stats.get('bodies', 0)} Körper · "
            f"{stats.get('materials', 0)} Materialien · "
            f"{stats.get('journal_imports', 0)} Journale"
        )

    def _import_journal_archive(self):
        self.database_import_button.setEnabled(
            False
        )
        self.database_status_label.setText(
            "Journal-Archiv wird eingelesen …"
        )
        self.state.import_journal_archive()

    def _database_import_progress(
        self,
        current,
        total,
        name,
    ):
        self.database_status_label.setText(
            f"Importiere Journal {current} / {total}: {name}"
        )

    def _database_import_finished(
        self,
        stats,
        error,
    ):
        self.database_import_button.setEnabled(
            True
        )

        if error:
            self.database_status_label.setText(
                f"Import fehlgeschlagen: {error}"
            )
            QMessageBox.warning(
                self,
                "Datenbank",
                f"Der Journal-Archivimport ist fehlgeschlagen.\n\n{error}"
            )
            return

        self._refresh_database_status()

        imported = int(
            stats.get("imported_journals", 0)
        )
        skipped = int(
            stats.get("skipped_journals", 0)
        )

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

        QMessageBox.information(
            self,
            "Datenbank",
            message
        )

    def _set_theme(self, theme):
        theme = (
            "light"
            if str(theme).lower() == "light"
            else "dark"
        )

        self.ui_theme = theme

        self.state.settings.setValue(
            "ui_theme",
            theme
        )

        app = QApplication.instance()

        if app is not None:
            app.setStyleSheet(
                LIGHT_STYLESHEET
                if theme == "light"
                else DARK_STYLESHEET
            )

        if hasattr(self, "system_map"):
            self.system_map.set_light_mode(
                theme == "light"
            )

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
        label.setText(
            ("✓ " if ok else "✗ ") + text
        )
        label.setObjectName(
            "statusOk"
            if ok
            else "statusWarn"
        )
        label.style().unpolish(label)
        label.style().polish(label)

    def _test_edsm_connection(self):
        self.edsm_test_button.setEnabled(False)
        self.edsm_test_status.setText(
            "Verbindung wird getestet …"
        )

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
        self.inara_test_status.setText(
            "Verbindung wird getestet …"
        )

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
            self,
            "Online-Dienste",
            "EDSM- und Inara-Einstellungen wurden gespeichert."
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

            files = [
                path
                for path in folder.glob("Journal*.log")
                if path.is_file()
            ]

            if not files:
                return None

            files.sort(
                key=lambda path: path.stat().st_mtime
            )

            oldest = files[0]
            newest = files[-1]

            oldest_dt = datetime.fromtimestamp(
                oldest.stat().st_mtime
            )
            newest_dt = datetime.fromtimestamp(
                newest.stat().st_mtime
            )

            return {
                "oldest_time": oldest_dt.strftime(
                    "%d.%m.%Y %H:%M:%S"
                ),
                "newest_time": newest_dt.strftime(
                    "%d.%m.%Y %H:%M:%S"
                ),
                "newest_name": newest.name,
            }

        except Exception as exc:
            return {
                "oldest_time": "Fehler",
                "newest_time": "Fehler",
                "newest_name": str(exc),
            }

    def choose_journal_folder(self):
        start = str(
            self.state.journal_folder
            or Path.home()
        )

        folder = QFileDialog.getExistingDirectory(
            self,
            "Elite-Dangerous-Journalordner wählen",
            start
        )

        if folder:
            self.state.set_journal_folder(
                Path(folder)
            )

    @staticmethod
    def _format_timestamp(value):
        if not value:
            return "–"

        try:
            dt = datetime.fromisoformat(
                value.replace(
                    "Z",
                    "+00:00"
                )
            )

            return dt.strftime(
                "%d.%m.%Y %H:%M:%S"
            )

        except ValueError:
            return value

    @staticmethod
    def _format_expiry(value):
        if not value:
            return "–"

        try:
            dt = datetime.fromisoformat(
                value.replace(
                    "Z",
                    "+00:00"
                )
            )

            return dt.strftime(
                "%d.%m.%Y %H:%M"
            )

        except ValueError:
            return value

    @staticmethod
    def _format_reward(value):
        return (
            f"{int(value or 0):,} Cr"
            .replace(",", ".")
        )

    @staticmethod
    def _place_text(mission):
        if mission.destination_body:
            if mission.destination_station:
                return (
                    f"{mission.destination_body} / "
                    f"{mission.destination_station}"
                )

            return mission.destination_body

        if mission.destination_station:
            return mission.destination_station

        if mission.target:
            return mission.target

        return "–"

    def _mission_selection_changed(self):
        selected = (
            self.missions_table.selectionModel()
            .selectedRows()
        )

        if not selected:
            self.mission_detail_title.setText(
                "Keine Mission ausgewählt"
            )

            self.mission_detail_text.setText(
                "Wähle oben eine Mission aus."
            )

            self.mission_progress_text.setText(
                ""
            )

            return

        row = selected[0].row()

        if row < 0 or row >= len(
            self.state.missions
        ):
            return

        mission = self.state.missions[row]

        self.mission_detail_title.setText(
            mission.name
            or "Mission"
        )

        self.mission_detail_text.setText(
            mission.summary
        )

        progress = []

        if mission.progress_text:
            progress.append(
                f"Fortschritt: {mission.progress_text}"
            )

        progress.append(
            f"Status: {mission.status}"
        )

        progress.append(
            f"Nächster Schritt: {mission.next_step}"
        )

        self.mission_progress_text.setText(
            "   ·   ".join(progress)
        )

    def refresh_all(self):
        commander = (
            self.state.commander
            or "–"
        )

        system = (
            self.state.system
            or "–"
        )

        self.commander_label.setText(
            f"CMDR {commander}"
        )

        self.ship_label.setText(
            self.state.ship
            or ""
        )

        self.last_import_label.setText(
            "Letzter Journal-Eintrag: "
            + self._format_timestamp(
                self.state.last_timestamp
            )
        )

        self.connection_label.setText(
            "● Journal erkannt"
            if self.state.connected
            else "● Journal nicht erkannt"
        )

        self.connection_label.setObjectName(
            "statusOk"
            if self.state.connected
            else "statusWarn"
        )

        self.connection_label.style().unpolish(
            self.connection_label
        )

        self.connection_label.style().polish(
            self.connection_label
        )

        self.sidebar_system.setText(
            f"Aktuelles System\n{system}"
        )

        body_station = []

        if self.state.body:
            body_station.append(
                self.state.body
            )

        if self.state.station:
            body_station.append(
                self.state.station
            )

        self.sidebar_body.setText(
            " / ".join(
                body_station
            )
        )

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

        ready_count = sum(
            1 for m in self.state.missions
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
            1
            for body in self.state.system_bodies
            if body.get("journal_scanned", True)
        )

        known_count = len(
            self.state.system_bodies
        )

        total_count = max(
            int(self.state.system_body_count or 0),
            int(getattr(self.state, "edsm_body_count", 0) or 0),
            known_count,
        )

        signal_count = self.state.system_signals_count

        # Belt Cluster können in Scan-Events auftauchen, zählen aber nicht
        # immer 1:1 zum FSS-BodyCount. Deshalb nicht irreführend >100% zeigen.
        displayed_scanned = min(scanned_count, total_count) if total_count else scanned_count

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

        scan_status = (
            f"{displayed_scanned} / {total_count} Körper selbst im Journal"
        )

        edsm_added = int(
            getattr(
                self.state,
                "edsm_added_count",
                0
            ) or 0
        )

        edsm_known = int(
            getattr(
                self.state,
                "edsm_body_count",
                0
            ) or 0
        )

        if self.state.edsm_enabled and edsm_known:
            scan_status += (
                f" · EDSM bekannt: {edsm_known}"
            )

            if edsm_added:
                scan_status += (
                    f" (+{edsm_added} ergänzt)"
                )

        if self.state.system_all_bodies_found:
            scan_status += " · alle Körper gefunden"

        if signal_count:
            scan_status += f" · {signal_count} Signale"

        if bio_body_count:
            scan_status += f" · BIO auf {bio_body_count} Körper(n)"

        if geo_body_count:
            scan_status += f" · GEO auf {geo_body_count} Körper(n)"

        scan_status += (
            f"   |   Scanwert: {self._format_reward(self.state.system_scan_value)}"
            f"   |   mit Kartographie: {self._format_reward(self.state.system_mapped_value)}"
        )

        if self.state.system_high_value_count:
            scan_status += (
                f"   |   ★ {self.state.system_high_value_count} Körper > 200.000 Cr"
            )

        self.system_scan_header.setText(scan_status)

        self.system_map.set_system(
            system,
            self.state.system_bodies
        )

        self.journal_path_edit.setText(
            str(
                self.state.journal_folder
                or ""
            )
        )

        self.journal_file_count.setText(
            str(
                self.state.journal_files
            )
        )

        diagnostics = self._journal_file_diagnostics()

        if diagnostics:
            self.journal_oldest_file.setText(
                diagnostics.get(
                    "oldest_time",
                    "–"
                )
            )
            self.journal_newest_file.setText(
                diagnostics.get(
                    "newest_time",
                    "–"
                )
            )
            self.journal_newest_name.setText(
                diagnostics.get(
                    "newest_name",
                    "–"
                )
            )
        else:
            self.journal_oldest_file.setText("–")
            self.journal_newest_file.setText("–")
            self.journal_newest_name.setText("–")

        self.journal_last_read.setText(
            self._format_timestamp(
                self.state.last_timestamp
            )
        )

        current_row = (
            self.missions_table.currentRow()
        )

        self.missions_table.setRowCount(
            len(
                self.state.missions
            )
        )

        for row, mission in enumerate(
            self.state.missions
        ):
            values = [
                mission.name,
                mission.destination_system
                or "–",
                self._place_text(mission),
                mission.status,
                mission.next_step,
                self._format_reward(
                    mission.reward
                ),
                self._format_expiry(
                    mission.expiry
                ),
            ]

            for col, value in enumerate(
                values
            ):
                item = QTableWidgetItem(
                    str(
                        value
                        or ""
                    )
                )

                if col == 3:
                    if mission.status in (
                        "Aufgabe erledigt",
                        "Daten erhalten",
                        "Am Missionsziel",
                    ):
                        item.setForeground(
                            Qt.green
                        )

                self.missions_table.setItem(
                    row,
                    col,
                    item
                )

        if (
            0 <= current_row
            < self.missions_table.rowCount()
        ):
            self.missions_table.selectRow(
                current_row
            )
        else:
            self._mission_selection_changed()
