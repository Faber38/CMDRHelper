import os
import unittest
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from cmdrhelper.ui.main_window import MainWindow
from cmdrhelper.bio_predictor import BioCandidate, BioPrediction


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


class ExplorerLivePopupTests(unittest.TestCase):
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
