import os
import unittest
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from cmdrhelper.ui.main_window import ExplorerLiveListWindow, MainWindow
from cmdrhelper.bio_predictor import BioCandidate, BioPrediction
from cmdrhelper.i18n import tr


class _LiveWindowStub:
    def __init__(self):
        self.rows = []
        self.visible = False

    def set_rows(self, _system_name, rows):
        self.rows = list(rows)

    def isVisible(self):
        return self.visible

    def show(self):
        self.visible = True

    def hide(self):
        self.visible = False

    def raise_(self):
        pass


class _DatabaseStub:
    @staticmethod
    def learned_bio_values():
        return {}

    @staticmethod
    def biology_predictor():
        class Predictor:
            @staticmethod
            def predict(_body, _known, limit=8):
                return BioPrediction(
                    candidates=(BioCandidate(
                        name="Stratum Tectonicas", genus="Stratum",
                        kind="species", confidence="high", support=44,
                        score=1.0, habitat_score=0.9, low_data=False,
                        reasons=("Atmosphäre", "PlanetClass"),
                    ),),
                    identified_count=0, completed_count=0,
                    expected_signals=3, open_signals=3,
                )
        return Predictor()


class _SettingsStub:
    def value(self, _key):
        return None

    def setValue(self, _key, _value):
        pass

    def sync(self):
        pass


class ExplorerLivePopupTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    @staticmethod
    def _candidate(name):
        return BioCandidate(
            name=name, genus=name.split()[0], kind="species",
            confidence="high", support=44, score=1.0,
            habitat_score=0.9, low_data=False, reasons=(),
        )

    def _render_bio(self, *, signals, species, predictions, open_signals):
        window = ExplorerLiveListWindow(
            "BIO", ("Body", "Find", "Progress", "Value"),
            _SettingsStub(), "test_bio_geometry", window_kind="bio",
        )
        window.set_rows("Test System", [{
            "body_name": "Test System 2",
            "signals": signals,
            "species": species,
            "predictions": predictions,
            "identified_count": len(species),
            "completed_count": sum(
                entry.get("scan_type") in ("Analyse", "Analyze")
                for entry in species
            ),
            "open_signals": open_signals,
        }])
        texts = []
        plain_cells = []
        for row in range(window.table.rowCount()):
            row_cells = [
                window.table.item(row, column).text()
                for column in range(window.table.columnCount())
                if window.table.item(row, column) is not None
            ]
            texts.extend(row_cells)
            plain_cells.extend(row_cells)
            widget = window.table.cellWidget(row, 1)
            if widget is not None:
                texts.append(widget.text())
        window.close()
        return "\n".join(texts), window.table.rowCount(), plain_cells

    def test_single_open_signal_shows_predictions(self):
        text, row_count, _plain_cells = self._render_bio(
            signals=1, species=[],
            predictions=[self._candidate("Bacterium Tela")], open_signals=1,
        )
        self.assertIn("Bacterium Tela", text)
        self.assertEqual(row_count, 2)

    def test_single_known_signal_hides_all_prediction_ui_but_keeps_log(self):
        text, row_count, plain_cells = self._render_bio(
            signals=1,
            species=[{"name": "Bacterium Tela – Grün", "scan_type": "Log"}],
            predictions=[self._candidate("Bacterium Nebulus")], open_signals=0,
        )
        self.assertIn("Bacterium Tela – Grün", text)
        self.assertIn(tr("bio_prediction.identified"), text)
        self.assertIn(tr("explorer.sample_one"), text)
        self.assertNotIn("Bacterium Nebulus", text)
        self.assertNotIn(tr("bio_prediction.possible_more"), text)
        self.assertNotIn(tr("bio_prediction.more_candidates"), text)
        self.assertNotIn(
            tr("bio_prediction.progress", identified=1, total=1, completed=0),
            text,
        )
        self.assertNotIn(tr("bio_prediction.open_signals", count=0), text)
        self.assertNotIn(tr("bio_prediction.identified"), plain_cells)
        self.assertEqual(row_count, 2)

    def test_known_species_is_filtered_while_other_candidates_remain(self):
        text, row_count, plain_cells = self._render_bio(
            signals=3,
            species=[{"name": "Bacterium Tela – Grün", "scan_type": "Sample"}],
            predictions=[
                self._candidate("Bacterium Tela"),
                self._candidate("Bacterium Nebulus"),
            ],
            open_signals=2,
        )
        self.assertEqual(text.count("Bacterium Tela"), 1)
        self.assertIn("Bacterium Nebulus", text)
        self.assertNotIn(
            tr("bio_prediction.progress", identified=1, total=3, completed=0),
            text,
        )
        self.assertNotIn(tr("bio_prediction.open_signals", count=2), text)
        self.assertNotIn(tr("bio_prediction.identified"), plain_cells)
        self.assertEqual(row_count, 3)

    def test_all_known_signals_hide_predictions_but_keep_analyzed_findings(self):
        text, _row_count, _plain_cells = self._render_bio(
            signals=3,
            species=[
                {"name": "Bacterium Tela", "scan_type": "Analyze"},
                {"name": "Bacterium Nebulus", "scan_type": "Log"},
                {"name": "Bacterium Verrata", "scan_type": "Sample"},
            ],
            predictions=[self._candidate("Stratum Tectonicas")],
            open_signals=0,
        )
        self.assertNotIn("Stratum Tectonicas", text)
        self.assertIn("Bacterium Tela", text)
        self.assertIn(tr("bio_prediction.found"), text)
        self.assertIn("Bacterium Nebulus", text)
        self.assertIn("Bacterium Verrata", text)
        self.assertIn(tr("bio_prediction.identified"), text)
        self.assertIn(tr("explorer.sample_one"), text)
        self.assertIn(tr("explorer.sample_two"), text)

    def test_bio_rows_receive_predictions_and_progress(self):
        window = MainWindow.__new__(MainWindow)
        window.state = SimpleNamespace(
            system="Test System", system_address=42,
            system_bodies=[{
                "body_id": 2, "name": "Test System 2", "body_type": "Planet",
                "planet_class": "High metal content body",
                "atmosphere": "thin carbon dioxide atmosphere",
                "biological_signals": 3, "biology": [],
            }],
            database=_DatabaseStub(),
        )
        window._explorer_live_system = "Test System"
        window._explorer_value_live_window = _LiveWindowStub()
        window._explorer_bio_live_window = _LiveWindowStub()
        window._explorer_value_yellow_threshold = lambda: 200_000
        window._ensure_explorer_live_windows = lambda: None
        window._explorer_live_window_enabled = lambda _kind: True
        window._format_reward = lambda value: f"{int(value)} Cr"

        MainWindow._refresh_explorer_live_windows(window)

        row = window._explorer_bio_live_window.rows[0]
        self.assertEqual(row["predictions"][0].name, "Stratum Tectonicas")
        self.assertEqual((row["identified_count"], row["completed_count"],
                          row["open_signals"]), (0, 0, 3))

    def test_valuable_rows_include_known_mapping_states_and_apply_filters(self):
        bodies = [
            {
                "name": "First mapping",
                "body_type": "Planet",
                "possible_value": 300_000,
                "was_mapped": False,
            },
            {
                "name": "Already mapped",
                "body_type": "Planet",
                "possible_value": 250_000,
                "was_mapped": True,
            },
            {
                "name": "Self mapped",
                "body_type": "Planet",
                "possible_value": 400_000,
                "self_mapped": True,
                "was_mapped": False,
            },
            {
                "name": "Below threshold",
                "body_type": "Planet",
                "possible_value": 199_999,
                "was_mapped": False,
            },
        ]
        window = MainWindow.__new__(MainWindow)
        window.state = SimpleNamespace(
            system="Test System",
            system_bodies=bodies,
            database=_DatabaseStub(),
        )
        window._explorer_live_system = "Test System"
        window._explorer_value_live_window = _LiveWindowStub()
        window._explorer_bio_live_window = _LiveWindowStub()
        window._explorer_value_yellow_threshold = lambda: 200_000
        window._ensure_explorer_live_windows = lambda: None
        window._explorer_live_window_enabled = lambda _kind: True
        window._format_reward = lambda value: f"{int(value)} Cr"

        MainWindow._refresh_explorer_live_windows(window)

        names = [row[0] for row in window._explorer_value_live_window.rows]
        self.assertEqual(names, ["First mapping", "Already mapped"])


if __name__ == "__main__":
    unittest.main()
