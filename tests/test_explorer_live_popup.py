import os
import unittest
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from cmdrhelper.ui.main_window import MainWindow


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


class ExplorerLivePopupTests(unittest.TestCase):
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
