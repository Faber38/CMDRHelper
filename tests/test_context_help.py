import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import (
    QApplication,
    QDialogButtonBox,
    QScrollArea,
    QWidget,
)

from cmdrhelper.help_content import help_topic
from cmdrhelper.ui.help_dialog import HelpDialog
from cmdrhelper.ui.main_window import MainWindow


class _SignalStub:
    def connect(self, _slot):
        pass


class _SettingsStub:
    def value(self, _key, default=None):
        return default

    def setValue(self, _key, _value):
        pass


class ContextHelpTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.state = SimpleNamespace(
            settings=_SettingsStub(),
            initializationStarted=_SignalStub(),
            initializationProgress=_SignalStub(),
            initializationFinished=_SignalStub(),
            changed=_SignalStub(),
            viewedCommanderChanged=_SignalStub(),
        )
        page_methods = (
            "_overview", "_missions", "_explorer", "_chronicle",
            "_score_page", "_settings",
        )
        patches = [
            patch.object(MainWindow, "_apply_saved_ui_font"),
            patch.object(MainWindow, "refresh_all"),
            patch("cmdrhelper.ui.main_window.QTimer.singleShot"),
            patch("cmdrhelper.ui.main_window.RoutePlannerView", side_effect=lambda *_: QWidget()),
            patch("cmdrhelper.ui.main_window.ScreenshotView", side_effect=lambda *_: QWidget()),
            patch("cmdrhelper.ui.main_window.CommanderView", side_effect=lambda *_: QWidget()),
        ]
        patches.extend(
            patch.object(MainWindow, name, side_effect=lambda: QWidget())
            for name in page_methods
        )
        self._patches = patches
        for item in self._patches:
            item.start()
            self.addCleanup(item.stop)
        self.window = MainWindow(self.state)
        self.addCleanup(self.window.close)

    def test_help_button_is_above_the_complete_auto_show_area(self):
        self.assertEqual(self.window.help_button.text(), "?  Hilfe")
        self.assertEqual(self.window.help_button.objectName(), "helpButton")
        sidebar_layout = self.window.help_button.parentWidget().layout()
        help_index = sidebar_layout.indexOf(self.window.help_button)
        title_index = sidebar_layout.indexOf(self.window.auto_show_title)
        frame_index = sidebar_layout.indexOf(self.window.auto_show_frame)
        exit_index = sidebar_layout.indexOf(self.window.exit_button)
        self.assertLess(help_index, title_index)
        self.assertLess(title_index, frame_index)
        self.assertLess(frame_index, exit_index)

    def test_all_main_pages_open_the_correct_help_context(self):
        for page, context in self.window.HELP_CONTEXTS.items():
            with self.subTest(context=context):
                self.window._show_page(page)
                self.window.help_button.click()
                dialog = self.window._help_dialog
                topic = help_topic(context)
                self.assertEqual(dialog.context, context)
                self.assertEqual(dialog.windowTitle(), topic.dialog_title)
                self.assertEqual(dialog.help_text.text(), topic.text)
                dialog.close()

    def test_help_dialog_is_scrollable_and_close_button_works(self):
        dialog = HelpDialog("overview")
        self.addCleanup(dialog.close)
        dialog.show()
        self.assertIsInstance(dialog.scroll_area, QScrollArea)
        close_button = dialog.buttons.button(QDialogButtonBox.StandardButton.Close)
        close_button.click()
        self.app.processEvents()
        self.assertFalse(dialog.isVisible())

    def test_overview_help_contains_all_detailed_sections(self):
        topic = help_topic("overview")
        self.assertEqual(topic.area, "Übersicht")
        for heading in (
            "Übersicht", "Commander &amp; Schiff", "Journal",
            "Aktueller Standort", "Missionen", "Letzter Stand",
            "Letzte Systeme", "Online-Status",
            "Wichtig bei mehreren Commandern", "Tipp",
        ):
            self.assertIn(heading, topic.text)
        for passage in (
            "Die Übersicht ist die Startseite von CMDRHelper.",
            "Frontier-ID (FID)",
            "Neue vollständige Journaleinträge",
            "den genaueren Standort des Commanders",
            "derzeit bekannten offenen Missionen",
            "zuletzt bekannten persistenten Commanderzustand",
            "jüngste Reise des Commanders",
            "Ein Commander verwendet niemals automatisch den API-Key",
            "Das bloße Anzeigen eines anderen Commanders",
            "den eingestellten Journalordner prüfen",
        ):
            self.assertIn(passage, topic.text)
        self.assertEqual(topic.text.count("<h3>"), 9)

    def test_missions_help_contains_all_detailed_sections(self):
        topic = help_topic("missions")
        self.assertEqual(topic.area, "Missionen")
        for heading in (
            "Missionen", "Offene Missionen", "Missionsstatus",
            "Missionen aus dem Journal", "Ziele und Orte",
            "Persistenz und Neustart", "Mehrere Commander",
            "Verwaiste oder nicht mehr gültige Missionen",
            "Online-Dienste", "Tipp",
        ):
            self.assertIn(heading, topic.text)
        for passage in (
            "aktuell betrachteten Commanders",
            "<code>MissionAccepted</code>",
            "Eine neue Spielsitzung ohne Missionsliste",
            "Missionsziel umgeleitet",
            "autoritativer Snapshot",
            "Zielplanet beziehungsweise Body",
            "die neue Journalsitzung zunächst keine Missionsereignisse enthält",
            "Missionen werden strikt nach Commander getrennt",
            "Reset-/Bereinigungsfunktion für verwaiste Missionen",
            "Inara-Verbindung beeinflusst die lokale Missionsspeicherung nicht",
            "die das Journal tatsächlich liefert",
        ):
            self.assertIn(passage, topic.text)
        self.assertEqual(topic.text.count("<h3>"), 9)
        self.assertEqual(topic.text.count("<ul>"), 3)

    def test_explorer_help_contains_all_detailed_sections(self):
        topic = help_topic("explorer")
        self.assertEqual(topic.area, "Explorer")
        for heading in (
            "Explorer", "Aktuelles System", "Systemkarte", "BIO ×N",
            "GEO ×N", "ABBAU ×N", "Eigene Abbau-Funde",
            "Oberflächenmaterialien des Bodys", "Terraforming",
            "Erstentdeckung", "First Mapping", "Landbar",
            "Goldrahmen / wertvolle Körper", "Wertliste",
            "BIO / GEO / ABBAU", "Body-Detail", "BIO-Prognosen",
            "Noch nicht abgegeben", "Auto einblenden", "Mehrere Commander",
            "Tipp",
        ):
            self.assertIn(heading, topic.text)
        for passage in (
            "vom aktiven Commander entdeckten und gescannten Systeme",
            "möglicher Gesamtwert bei vollständiger Kartographierung",
            "Tatsächliche eigene BIO-Funde werden separat geführt",
            "24 planetare Abbaustandorte gemeldet wurden",
            "Kupfer – 56 t",
            "nicht mit den Funden anderer Commander vermischt",
            "keine belegte direkte Zuordnung",
            "First Mapping vom Commander beansprucht",
            "Goldrahmen dient als schnelle optische Orientierung",
            "persönlichen Abbau-Funde sichtbar werden",
            "Prognosen sind keine Garantie",
            "Bereits verkaufte Kartographiedaten",
            "Globale astronomische Eigenschaften eines Bodys",
        ):
            self.assertIn(passage, topic.text)
        self.assertEqual(topic.text.count("<h3>"), 20)
        self.assertEqual(topic.text.count("<ul>"), 4)

    def test_jump_tip_help_contains_all_detailed_sections(self):
        topic = help_topic("jump_tip")
        self.assertEqual(topic.area, "Sprungtipp")
        for heading in (
            "Sprungtipp", "Grundlage der Auswertung", "Systemkürzel",
            "Neu auswerten", "Ergebnisliste",
            "Wahrscheinlichkeit statt Garantie", "Eigene Datenbasis",
            "Mehrere Commander", "Verwendung in der Praxis", "Tipp",
        ):
            self.assertIn(heading, topic.text)
        for passage in (
            "als Entscheidungshilfe gedacht",
            "Kürzel statistisch auswerten",
            "erzeugt keine neuen Elite-Daten",
            "terraformierbare Körper",
            "Es handelt sich nicht um eine Garantie",
            "persönliche Datenbasis für die Auswertung",
            "Persönliche Auswertungen werden commanderbezogen behandelt",
            "Er ersetzt keinen vollständigen Routenplaner",
            "Für konkrete Streckenplanung",
            "Nicht als Vorhersage",
        ):
            self.assertIn(passage, topic.text)
        self.assertEqual(topic.text.count("<h3>"), 9)
        self.assertEqual(topic.text.count("<ul>"), 1)

    def test_route_planner_help_contains_all_detailed_sections(self):
        topic = help_topic("route_planner")
        self.assertEqual(topic.area, "Routenplaner")
        for heading in (
            "Routenplaner", "Start und Ziel", "Schiff oder Fleet Carrier",
            "Schiffsroute", "Fleet-Carrier-Route", "Spansh", "Berechnung",
            "Ergebnis", "Route und aktueller Commander", "CTSVision-Export",
            "CSV-Datei", "Fehler und externe Dienste",
            "Routenplaner und Sprungtipp", "Mehrere Commander", "Tipp",
        ):
            self.assertIn(heading, topic.text)
        for passage in (
            "normalen Schiff und mit einem Fleet Carrier",
            "FSD-Daten, Schiffsdaten, Masse, Treibstoff",
            "Spansh-Carrierplanung",
            "Anfrage wird im Hintergrund verarbeitet",
            "Treibstoff beziehungsweise Tritium",
            "Berechnete Fleet-Carrier-Routen können für CTSVision als CSV exportiert",
            "Sprungtipp bewertet mögliche interessante Explorationsziele",
            "Routenplaner berechnet eine konkrete Strecke",
            "aktiven Live-AppState",
            "Das bloße Betrachten eines anderen Commanders",
            "verfügbare Tritiumreserve",
        ):
            self.assertIn(passage, topic.text)
        self.assertEqual(topic.text.count("<h3>"), 14)
        self.assertEqual(topic.text.count("<ul>"), 2)

    def test_images_help_contains_all_implemented_sections(self):
        topic = help_topic("images")
        self.assertEqual(topic.area, "Bilder")
        for heading in (
            "Bilder", "Quellordner", "Zielordner",
            "Automatische Verarbeitung", "Bildkonvertierung",
            "Bild aufhellen", "Commanderbezogene Ablage", "Dateinamen",
            "Sichere Dateinamen", "Aufnahmezeitpunkt",
            "Mehrere Bilder in derselben Sekunde",
            "Commanderwechsel während der Verarbeitung", "Galerie",
            "Aktueller Commander", "Alle Commander", "Nicht zugeordnet",
            "Bestehende Bilder", "Bild auswählen und ansehen",
            "Bild löschen", "Zielordner öffnen", "Sicherheit der Bildpfade",
            "Wenn kein Commander erkannt wurde", "Mehrere Commander", "Tipp",
        ):
            self.assertIn(heading, topic.text)
        for passage in (
            "Ordner auf neue BMP-Dateien überwachen",
            "Zielformat kann „PNG“ oder „JPG“ gewählt werden",
            "ursprüngliche BMP-Datei erhalten",
            "Schieberegler und ein gekoppeltes Zahlenfeld von 0 bis 50 Prozent",
            "während jeder danach gestarteten Konvertierung angewendet",
            "keine reine Vorschau",
            "FABER38_F12520967/",
            "beim Einreihen aktive Journalidentität",
            "Filter „Aktueller Commander“",
            "Filter „Alle Commander“",
            "Filter „Nicht zugeordnet“",
            "Ein einfacher Klick",
            "Ein Doppelklick öffnet die Datei",
            "Ausgewählte löschen",
            "Beim Filter „Aktueller Commander“ wird dessen vorhandener",
            "Symbolische Verknüpfungen werden weder",
            "UNKNOWN_UNKNOWN/",
            "Neue Bilder speichern:",
            "Bilder anzeigen:",
        ):
            self.assertIn(passage, topic.text)
        self.assertEqual(topic.text.count("<h3>"), 23)
        self.assertEqual(topic.text.count("<ul>"), 1)

    def test_commander_view_help_contains_all_implemented_sections(self):
        topic = help_topic("commander_view")
        self.assertEqual(topic.area, "CMDR Ansicht")
        for heading in (
            "CMDR Ansicht", "Commander auswählen",
            "Betrachteter Commander und Live-Commander", "Frontier-ID (FID)",
            "Übersicht", "Vermögen / Credits", "Söldnermünzen",
            "Aktuell und Ausgaben", "Insgesamt verdient",
            "Warum keine eigene MercCoins-Bilanz?", "Missionen", "Exploration",
            "Schiffe / Flotte", "Schiffsdetails", "Fleet Carrier",
            "Persistenter Commanderzustand", "Historische Rekonstruktion",
            "Mehrere Commander", "Auswirkungen auf andere Ansichten",
            "Inara und EDSM", "Tipp",
        ):
            self.assertIn(heading, topic.text)
        for passage in (
            "entweder als „Live aktiv“ oder als „Nur Ansicht“",
            "macht ihn nicht zum aktiven Journal-Commander",
            "letzter bekannter Standort und Anzahl offener Missionen",
            "formatiert beispielsweise als <b>1.234.567 Cr</b>",
            "Statistics → Bank_Account",
            "MercCoins_Current",
            "MercCoins_Total_Spent",
            "MercCoins_Spent_On_Engineering",
            "MercCoins_Spent_On_MercGear",
            "MercCoins_Total_Earned",
            "korrigiert diese Werte nicht",
            "Status, Missionsbezeichnung, Ziel, Ablaufzeit und Belohnung",
            "First Footfalls",
            "Tab „Chronik“ innerhalb der CMDR Ansicht ist derzeit noch ein Platzhalter",
            "Schiffskennung, ShipID, Standort",
            "Carriername, Callsign, CarrierID",
            "normalen Journal-Lesepositionen nicht",
            "persönliche Mining-Rohstoffauswahl der Chronik",
            "Für Live-Uploads ist ausschließlich die aktive Journal-FID maßgeblich",
            "CMDR Ansicht = Wen möchte ich betrachten?",
        ):
            self.assertIn(passage, topic.text)
        self.assertEqual(topic.text.count("<h3>"), 20)
        self.assertEqual(topic.text.count("<ul>"), 4)

    def test_chronicle_help_contains_all_detailed_sections(self):
        topic = help_topic("chronicle")
        self.assertEqual(topic.area, "Chronik")
        for heading in (
            "Chronik", "Besuchte Systeme", "3D-Karte", "Aktuelle Position",
            "Ausrichten", "Chronik aktualisieren", "Freitextsuche",
            "Suchergebnisse", "Planetare Abbaustandorte", "Mindestens",
            "Eigene Abbau-Funde", "Rohstoff", "Gezielte Rohstoffsuche",
            "Alle Rohstoffe", "Filter kombinieren", "Anwenden",
            "Zurücksetzen", "Commander-Auswahl", "Alle Commander",
            "Suchhilfe / Legende", "Tipp",
        ):
            self.assertIn(heading, topic.text)
        for passage in (
            "persönliche Reise- und Fundhistorie des Commanders",
            "linke Maustaste gedrückt halten → Ansicht drehen",
            "Chronik durchsuchen …",
            "Button „Suchen“ führt ausschließlich diese Freitextsuche aus",
            "ABBAU-Filter werden dagegen mit „Anwenden“ ausgeführt",
            "Die Anzahl gehört zum Body selbst und ist nicht commanderbezogen",
            "Surface-Mining-Historie und wird strikt nach Commander getrennt",
            "nicht um eine theoretische Liste aller möglichen Mining-Rohstoffe",
            "Prua Hypai NV-E c28-66 / 2 — ABBAU ×24 — Kupfer 56 t",
            "ABBAU ×24 — Helium-3 18 t, Kupfer 56 t",
            "Textsuche und Mining-Filter bewusst voneinander getrennt",
            "keine Mining-Funde, die ausschließlich einem anderen Commander gehören",
            "Globale astronomische Eigenschaften eines Systems oder Bodys",
        ):
            self.assertIn(passage, topic.text)
        self.assertEqual(topic.text.count("<h3>"), 20)
        self.assertEqual(topic.text.count("<ul>"), 4)

    def test_overview_help_remains_unchanged(self):
        topic = help_topic("overview")
        self.assertEqual(topic.text.count("<h3>"), 9)
        self.assertIn("Die Übersicht ist die Startseite von CMDRHelper.", topic.text)
        self.assertIn("Ein Commander verwendet niemals automatisch den API-Key", topic.text)
        self.assertIn("den eingestellten Journalordner prüfen", topic.text)

    def test_settings_help_contains_all_implemented_sections(self):
        topic = help_topic("settings")
        self.assertEqual(topic.area, "Einstellungen")
        for heading in (
            "Einstellungen", "Journal", "Journalanzeige und Bedienung",
            "Datenbank", "Journal-Archiv importieren", "Commanderbezogene Daten",
            "Online-Dienste", "EDSM-Zugang für", "EDSM verwenden und testen",
            "Inara-Zugang für", "Inara verwenden und testen", "Inara-Outbox",
            "Online-Status im Header", "API-Key-Sicherheit",
            "Bilder / Screenshots", "Oberfläche", "Dark- und Light-Mode",
            "Sprache", "Schriftart und Schriftgröße", "Werteschwellwert",
            "Automatisch einblenden", "Updates", "Downloadfortschritt",
            "Update abbrechen", "Update unter Windows", "Neustart nach Update",
            "Mehrere Commander", "Hilfe", "Tipp",
        ):
            self.assertIn(heading, topic.text)
        for passage in (
            "Journal*.log", "„Jetzt einlesen“", "sichere Lesepositionen",
            "aktuell bearbeitete Datei angezeigt",
            "Auswahl in den Einstellungen bestimmt nur, wessen Zugang",
            "EDSM-Zugang für:", "Inara-Zugang für:",
            "Worker verarbeitet nur die Outbox",
            "EDSM aus", "EDSM wartet", "EDSM Übertragung", "EDSM Fehler",
            "kein zusätzlicher, getrennt beschrifteter Zustand „EDSM aktiv“",
            "INARA aus", "INARA bereit", "INARA Übertragung",
            "INARA aktiv", "INARA Fehler",
            "gespeichert werden sie commanderbezogen in den Anwendungseinstellungen",
            "ausschließlich im Hauptmenü „Bilder“",
            "Theme wird sofort", "anschließend ein Neustart",
            "Schriftgröße von 7 bis 24 pt", "Explorer-Werteschwellwert",
            "verzögerte automatische Prüfung", "geschätzte Restzeit",
            "Busy-Modus", "Download abbrechen", "Rollback-Sicherung",
            "prüft kurz, ob der neue Prozess stabil anläuft",
            "Aktive Journal-FID = Wer darf live senden?",
            "oberhalb von „auto einblenden“",
        ):
            self.assertIn(passage, topic.text)
        self.assertEqual(topic.text.count("<h3>"), 28)
        self.assertEqual(topic.text.count("<ul>"), 4)

    def test_no_help_topics_remain_short(self):
        for context in self.window.HELP_CONTEXTS.values():
            with self.subTest(context=context):
                topic = help_topic(context)
                self.assertIn("<h2>", topic.text)
                self.assertIn("<h3>", topic.text)

    def test_open_and_close_do_not_change_app_state_or_minimum_width(self):
        state_before = dict(vars(self.state))
        minimum_width = self.window.minimumWidth()
        self.window.help_button.click()
        self.window._help_dialog.close()
        self.app.processEvents()
        self.assertEqual(vars(self.state), state_before)
        self.assertEqual(self.window.minimumWidth(), minimum_width)
        self.assertEqual(minimum_width, 0)


if __name__ == "__main__":
    unittest.main()
