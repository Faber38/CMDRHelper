import copy
import json
import os
from pathlib import Path
from string import Formatter
from types import SimpleNamespace
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtCore import QObject, Qt, Signal, QLocale
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QLabel, QMainWindow

from cmdrhelper.help_content import HELP_LANGUAGES, help_topic
from cmdrhelper.i18n import _TRANSLATIONS, set_language, tr
from cmdrhelper.ui.analysis_view import SystemAnalysisView
from cmdrhelper.ui.main_window import MainWindow
from cmdrhelper.ui.styles import DARK_STYLESHEET, LIGHT_STYLESHEET


class State(QObject):
    changed = Signal()

    def __init__(self):
        super().__init__()
        self.database = SimpleNamespace(active_commander_id=1)
        self.system = "Plio Aip KN-B d13-201"


class AnalysisViewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        set_language("de")
        self.addCleanup(set_language, "de")
        self.fixture = json.loads((Path(__file__).parent / "fixtures/system_analysis.json").read_text())
        self.state = State()
        self.view = SystemAnalysisView(self.state, MainWindow._format_reward)
        self.view.resize(950, 800)
        self.view.show()
        self.addCleanup(self.view.close)
        self.api_patch = patch("cmdrhelper.ui.analysis_view.HierarchicalJumpTip")
        self.api = self.api_patch.start().return_value
        self.addCleanup(self.api_patch.stop)
        self.api.evaluate.return_value = self.fixture

    def analyse(self):
        self.view.system_input.setText(self.fixture["target"])
        self.view.analyze_button.click()

    def test_valid_target_and_current_system_action(self):
        self.view.current_button.click()
        self.assertEqual(self.view.system_input.text(), self.state.system)
        self.api.evaluate.assert_not_called()
        self.view.analyze_button.click()
        self.api.evaluate.assert_called_once_with(self.state.system)
        self.assertFalse(self.view.result_panel.isHidden())
        self.assertEqual(self.view.target.text(), self.fixture["target"])

    def test_enter_triggers_analysis(self):
        self.view.system_input.setText(self.state.system)
        QTest.keyClick(self.view.system_input, Qt.Key_Return)
        self.api.evaluate.assert_called_once_with(self.state.system)

    def test_empty_input_has_no_api_call(self):
        self.view.system_input.setText("   ")
        self.view.analyze_button.click()
        self.api.evaluate.assert_not_called()
        self.assertEqual(self.view.status.text(), tr("analysis.error.empty"))

    def test_unparseable_target_clears_previous_result(self):
        self.analyse()
        self.api.evaluate.return_value = {"ok": False, "reason": "unsupported_name"}
        self.view.system_input.setText("Sol")
        self.view.analyze_button.click()
        self.assertTrue(self.view.result_panel.isHidden())
        self.assertEqual(self.view.status.text(), tr("analysis.error.unsupported"))

    def test_missing_history_and_mass_data(self):
        for reason, message in [("no_qualified_observations", "no_data"), ("no_mass_observations", "mass")]:
            with self.subTest(reason=reason):
                self.api.evaluate.return_value = {"ok": False, "reason": reason}
                self.analyse()
                self.assertEqual(self.view.status.text(), tr("analysis.error." + message))
                self.assertTrue(self.view.result_panel.isHidden())

    def test_technical_error_is_not_exposed(self):
        self.api.evaluate.side_effect = RuntimeError("SELECT secret Python SQL")
        with self.assertLogs("cmdrhelper.ui.analysis_view", "ERROR"):
            self.analyse()
        self.assertEqual(self.view.status.text(), tr("analysis.error.failed"))
        self.assertTrue(self.view.analyze_button.isEnabled())

    def test_index_is_not_a_percentage_and_has_explanation(self):
        self.analyse()
        self.assertIn(str(round(self.fixture["potential_index"])), self.view.index.text())
        self.assertNotIn("%", self.view.index.text())
        self.assertEqual(self.view.index.toolTip(), tr("analysis.index_explanation"))
        self.assertEqual(self.view.index_explanation.text(), tr("analysis.index_explanation"))

    def test_all_classes_and_local_quality_are_independent(self):
        for key in ("weak", "average", "interesting", "good", "very_good"):
            r = copy.deepcopy(self.fixture)
            r["recommendation"] = key
            r["family_data_quality"] = "low"
            self.view.render(r)
            self.assertEqual(self.view.recommendation.text(), tr("analysis.class." + key).upper())
            self.assertEqual(self.view.local_quality.text(), tr("analysis.local_quality") + ": " + tr("analysis.quality.low"))

    def test_three_comparison_levels_and_local_experience(self):
        self.analyse()
        table = self.view.comparison_table
        self.assertEqual((table.rowCount(), table.columnCount()), (3, 4))
        self.assertEqual([table.horizontalHeaderItem(c).text() for c in range(4)],
                         ["Ebene", "Vergleich", "Systeme", "Datenbasis"])
        for row, level in enumerate(self.fixture["levels"]):
            self.assertEqual(table.item(row, 0).text(), tr("analysis.level." + level["kind"]))
            self.assertEqual(table.item(row, 2).text(), str(level["systems"]))
            self.assertEqual(table.item(row, 3).text(), tr("analysis.quality." + level["data_quality"]))
        family = self.fixture["levels"][-1]
        self.assertIn(tr("analysis.level.family"), self.view.scope.text())
        self.assertEqual(self.view.metric_labels["systems"].text(), str(family["systems"]))
        self.assertEqual(self.view.metric_labels["hits"].text(), str(family["hits"]))
        self.assertEqual(self.view.metric_labels["median"].text(), MainWindow._format_reward(round(family["median"])))
        self.assertEqual(self.view.metric_labels["potential"].text(), MainWindow._format_reward(round(family["adjusted_potential"])))

    def test_experience_has_two_real_columns(self):
        self.analyse()
        grid = self.view.experience_grid
        self.assertEqual(grid.itemAtPosition(0, 0).widget().text(), tr("analysis.scope_label"))
        self.assertIs(grid.itemAtPosition(0, 1).widget(), self.view.scope)
        for row, key in enumerate(("systems", "hits", "median", "potential"), 1):
            self.assertEqual(grid.itemAtPosition(row, 0).widget().text(), tr("analysis.metric." + key))
            self.assertIs(grid.itemAtPosition(row, 1).widget(), self.view.metric_labels[key])

    def test_empty_family_inherits_and_experience_identifies_region(self):
        r = copy.deepcopy(self.fixture)
        r["levels"][-1]["systems"] = 0
        r["levels"][-1]["data_quality"] = "very_low"
        r["family_data_quality"] = "very_low"
        self.view.render(r)
        self.assertIn(tr("analysis.inherited"), self.view.comparison_table.item(2, 3).text())
        self.assertIn(tr("analysis.level.sector_mass"), self.view.scope.text())
        self.assertEqual(self.view.metric_labels["systems"].text(), str(r["levels"][1]["systems"]))

    def test_only_positive_find_categories_are_shown(self):
        self.analyse()
        self.assertIn(tr("analysis.find.water_world"), self.view.finds.text())
        self.assertIn(tr("analysis.find.terraformable_hmc"), self.view.finds.text())
        self.assertNotIn(tr("analysis.find.ammonia_world"), self.view.finds.text())
        self.assertNotIn("ELW", self.view.finds.text())

    def test_bio_states_and_no_diagnostic_weights(self):
        for signals, analysed, comparable, key in [(0, 0, 0, "unknown"), (2, 0, 0, "partial"), (2, 1, 1, "covered")]:
            r = copy.deepcopy(self.fixture)
            r["levels"][-1]["bio"] = dict(signal_systems=signals, analysed_systems=analysed,
                                            comparable_systems=comparable, median_base_value=1_000_000 if comparable else None)
            self.view.render(r)
            self.assertEqual(self.view.bio.text(), tr("analysis.bio." + key, signals=signals,
                                                       analysed=analysed, count=comparable,
                                                       value=MainWindow._format_reward(1_000_000)))
            text = " ".join(label.text() for label in self.view.findChildren(QLabel))
            self.assertNotIn("80/20", text)
            self.assertNotIn("70/30", text)

    def test_endnumber_only_in_target_name(self):
        before = None
        for number in (109, 201, 227):
            r = copy.deepcopy(self.fixture)
            r["target"] = f"Plio Aip KN-B d13-{number}"
            self.view.render(r)
            texts = (self.view.recommendation.text(), self.view.index.text(),
                     self.view.comparison_table.item(2, 1).text(), self.view.scope.text())
            self.assertNotIn(f"-{number}", texts[2])
            if before is not None:
                self.assertEqual(texts, before)
            before = texts

    def test_journal_events_do_not_recalculate_but_button_does(self):
        self.analyse()
        self.state.changed.emit()
        self.api.evaluate.assert_called_once()
        self.view.analyze_button.click()
        self.assertEqual(self.api.evaluate.call_count, 2)

    def test_commander_change_discards_stale_result(self):
        self.analyse()
        self.state.database.active_commander_id = 2
        self.state.changed.emit()
        self.assertTrue(self.view.result_panel.isHidden())
        self.api.evaluate.assert_called_once()

    def test_dark_and_light_keep_subtle_text_colors(self):
        old_style = self.app.styleSheet()
        self.addCleanup(self.app.setStyleSheet, old_style)
        self.analyse()
        colors = []
        for light, style in [(False, DARK_STYLESHEET), (True, LIGHT_STYLESHEET)]:
            self.app.setStyleSheet(style)
            self.view.set_light_mode(light)
            self.app.processEvents()
            colors.append(self.view.recommendation.styleSheet())
            self.assertNotIn("background", colors[-1])
            self.assertFalse(self.view.result_panel.isHidden())
        self.assertNotEqual(*colors)

    def test_twelve_languages_have_complete_strings_placeholders_and_help(self):
        keys = [key for key in _TRANSLATIONS["de"] if key.startswith("analysis.")]
        fields = lambda text: {name for _, name, _, _ in Formatter().parse(text) if name}
        for language in HELP_LANGUAGES:
            with self.subTest(language=language):
                set_language(language)
                for key in keys:
                    self.assertIn(key, _TRANSLATIONS[language])
                    self.assertEqual(fields(_TRANSLATIONS[language][key]), fields(_TRANSLATIONS["de"][key]))
                view = SystemAnalysisView(self.state, MainWindow._format_reward)
                view.render(self.fixture)
                self.assertEqual(view.recommendation.text(), QLocale(language).toUpper(tr("analysis.class.good")))
                self.assertEqual(view.index_explanation.text(), tr("analysis.index_explanation"))
                self.assertNotIn("analysis.", " ".join(label.text() for label in view.findChildren(QLabel)))
                topic = help_topic("jump_tip", language)
                self.assertEqual(topic.area, tr("nav.jump_tip"))
                for term in ("100", "BIO", "Plio Aip KN-B d13-201", "Plio Aip KN-B d13"):
                    self.assertIn(term, topic.text)
                view.close()

    def test_historical_evidence_uses_confidence_and_preserves_hits_in_all_languages(self):
        for language in HELP_LANGUAGES:
            set_language(language)
            window = MainWindow.__new__(MainWindow)
            QMainWindow.__init__(window)
            window.state, window.ui_theme = self.state, "dark"
            rows = [dict(key="TK-C d", rank=1, systems=6, hits=3, success_text="3 / 6",
                         rate=0.5, stars=5, confidence=confidence,
                         recommendation_text="FORBIDDEN direct recommendation")
                    for confidence in ("gering", "mittel", "hoch", None)]
            with patch.object(window, "_score_analyzer") as old:
                old.return_value.available_targets.return_value = [{"key": "valuable", "label": "Valuable"}]
                old.return_value.jump_recommendations.return_value = {"recommendations": rows}
                tabs = window._score_page()
                window.setCentralWidget(tabs)
                self.app.processEvents()
                window.score_refresh_button.click()
                table = window.score_ranking_table
                self.assertEqual(table.horizontalHeaderItem(4).text(), tr("score.col_recommendation"))
                if language == "de":
                    self.assertEqual(table.horizontalHeaderItem(4).text(), "Aussagekraft")
                for row, evidence in enumerate(("low", "medium", "high", "unknown")):
                    self.assertEqual([table.item(row,c).text() for c in range(1,4)],
                                     ["TK-C d", "3 / 6", window._score_percent(0.5)])
                    self.assertEqual(table.item(row,4).text(), tr("analysis.evidence." + evidence))
                    self.assertNotIn("★", table.item(row,4).text())
                text = " ".join(label.text() for label in tabs.widget(1).findChildren(QLabel))
                self.assertIn(tr("score.intro"), text)
                self.assertNotIn("FORBIDDEN", text)
                window.close()

    def test_real_mainwindow_tabs_retain_old_controls(self):
        window = MainWindow.__new__(MainWindow)
        QMainWindow.__init__(window)
        window.state, window.ui_theme = self.state, "dark"
        with patch.object(window, "_score_analyzer") as old:
            old.return_value.available_targets.return_value = [{"key": "valuable", "label": "Valuable"}]
            old.return_value.jump_recommendations.return_value = {}
            tabs = window._score_page()
            window.setCentralWidget(tabs)
            self.app.processEvents()
            self.assertEqual([tabs.tabText(i) for i in range(tabs.count())], ["Systemanalyse", "Erfahrungsdaten"])
            self.assertIs(tabs.widget(0), window.system_analysis_view)
            tabs.setCurrentIndex(1)
            self.assertIsNotNone(window.score_ranking_table)
            window.score_refresh_button.click()
            old.return_value.jump_recommendations.assert_called()
            window.close()


if __name__ == "__main__":
    unittest.main()
