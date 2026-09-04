import os
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QCheckBox, QComboBox, QLabel, QListWidget

from cmdrhelper.ui.main_window import MainWindow


class _ValueStub:
    def __init__(self, value):
        self._value = value

    def isChecked(self):
        return bool(self._value)

    def value(self):
        return int(self._value)


class _TextStub:
    def __init__(self, text):
        self._text = text

    def text(self):
        return self._text

    def clear(self):
        self._text = ""


class _MutableValueStub(_ValueStub):
    def setChecked(self, value):
        self._value = bool(value)

    def setValue(self, value):
        self._value = int(value)


class _ComboStub:
    def __init__(self, value=""):
        self._value = value

    def currentData(self):
        return self._value

    def setCurrentIndex(self, index):
        if index == 0:
            self._value = ""


class _MapStub:
    def __init__(self):
        self.systems = None

    def set_systems(self, systems):
        self.systems = systems


class _SignalStub:
    def __init__(self):
        self.slots = []

    def connect(self, slot):
        self.slots.append(slot)

    def emit(self, *args):
        for slot in tuple(self.slots):
            slot(*args)


class _SettingsStub:
    def value(self, _key, default=None):
        return default


class ChronicleMiningFilterUiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_search_button_path_runs_freetext_without_mining_filters(self):
        window = SimpleNamespace(
            chronicle_search_edit=_TextStub("Wasserwelt"),
            _run_chronicle_search=Mock(),
            _reset_chronicle_search=Mock(),
        )
        MainWindow._search_chronicle_biology(window)
        window._run_chronicle_search.assert_called_once_with("Wasserwelt")

    def test_initial_commodity_refresh_runs_after_commander_view_resolution(self):
        options = {
            1: [{"frontier_name": "copper", "display_name": "Kupfer"}],
            2: [{"frontier_name": "gold", "display_name": "Gold"}],
        }

        class DatabaseStub:
            def surface_mining_commodity_options(self, commander_id):
                return options[commander_id]

        viewed_signal = _SignalStub()
        state = SimpleNamespace(
            settings=_SettingsStub(),
            database=DatabaseStub(),
            commander_id=None,
            viewed_commander_id=None,
            initializationStarted=_SignalStub(),
            initializationProgress=_SignalStub(),
            initializationFinished=_SignalStub(),
            viewedCommanderChanged=viewed_signal,
            changed=_SignalStub(),
        )

        def build_ui(window):
            window.chronicle_mining_commodity_combo = QComboBox()
            window.chronicle_mining_commodity_combo.addItem("Alle", "")
            window.chronicle_personally_mined_check = QCheckBox()
            window.chronicle_personally_mined_check.toggled.connect(
                window._update_chronicle_mining_commodity_enabled
            )
            # Simuliert CommanderView.resolve_viewed_commander() während _build_ui().
            state.viewed_commander_id = 1

        with (
            patch.object(MainWindow, "_apply_saved_ui_font"),
            patch.object(MainWindow, "_build_ui", autospec=True, side_effect=build_ui),
            patch.object(MainWindow, "refresh_all"),
            patch("cmdrhelper.ui.main_window.QTimer.singleShot"),
        ):
            window = MainWindow(state)
        self.addCleanup(window.close)

        window.chronicle_personally_mined_check.setChecked(True)
        self.assertEqual(
            [
                (
                    window.chronicle_mining_commodity_combo.itemText(index),
                    window.chronicle_mining_commodity_combo.itemData(index),
                )
                for index in range(window.chronicle_mining_commodity_combo.count())
            ],
            [("Alle", ""), ("Kupfer", "copper")],
        )
        self.assertTrue(window.chronicle_mining_commodity_combo.isEnabled())

        state.viewed_commander_id = 2
        viewed_signal.emit(2)
        self.assertEqual(
            [
                window.chronicle_mining_commodity_combo.itemText(index)
                for index in range(window.chronicle_mining_commodity_combo.count())
            ],
            ["Alle", "Gold"],
        )

    def test_apply_button_path_runs_only_the_visible_mining_filters(self):
        window = SimpleNamespace(
            chronicle_planetary_mining_check=_ValueStub(True),
            chronicle_planetary_mining_minimum=_ValueStub(16),
            chronicle_personally_mined_check=_ValueStub(True),
            chronicle_mining_commodity_combo=_ComboStub("copper"),
            _run_chronicle_search=Mock(),
            _reset_chronicle_search=Mock(),
        )
        MainWindow._apply_chronicle_mining_filters(window)
        window._run_chronicle_search.assert_called_once_with(
            "",
            planetary_mining_only=True,
            minimum_mining=16,
            personally_mined_only=True,
            mining_commodity="copper",
        )

    def test_applied_filter_result_is_visible_in_chronicle_result_list(self):
        result = {
            "kind": "Körper",
            "system_address": 42,
            "system_name": "Prua Hypai NV-E c28-66",
            "short_name": "2",
            "planetary_mining_signals": 24,
            "personally_mined": True,
            "x": 1.0, "y": 2.0, "z": 3.0,
            "body_count": 3,
        }

        class DatabaseStub:
            def search_chronicle(self, *_args, **_kwargs):
                return [result]

        results = QListWidget()
        window = SimpleNamespace(
            state=SimpleNamespace(database=DatabaseStub()),
            chronicle_search_results=results,
            chronicle_status=QLabel(),
            chronicle_map=_MapStub(),
            _chronicle_planetary_mining_result_text=(
                MainWindow._chronicle_planetary_mining_result_text
            ),
            _chronicle_mining_commander_id=lambda: 1,
        )
        MainWindow._run_chronicle_search(
            window,
            "",
            planetary_mining_only=True,
            minimum_mining=16,
            personally_mined_only=True,
        )
        self.assertTrue(results.isVisible())
        self.assertEqual(
            results.item(0).text(),
            "Prua Hypai NV-E c28-66 / 2 — ABBAU ×24 — eigene Funde",
        )

    def test_reset_clears_freetext_and_all_mining_filters(self):
        text = _TextStub("Platin")
        mining = _MutableValueStub(True)
        minimum = _MutableValueStub(16)
        personal = _MutableValueStub(True)
        commodity = _ComboStub("copper")
        window = SimpleNamespace(
            chronicle_search_edit=text,
            chronicle_search_results=QListWidget(),
            chronicle_planetary_mining_check=mining,
            chronicle_planetary_mining_minimum=minimum,
            chronicle_personally_mined_check=personal,
            chronicle_mining_commodity_combo=commodity,
            _refresh_chronicle=Mock(),
        )
        MainWindow._reset_chronicle_search(window)
        self.assertEqual(text.text(), "")
        self.assertFalse(mining.isChecked())
        self.assertEqual(minimum.value(), 0)
        self.assertFalse(personal.isChecked())
        self.assertEqual(commodity.currentData(), "")
        window._refresh_chronicle.assert_called_once_with()

    def test_commander_switch_reloads_strictly_separated_commodity_options(self):
        options = {
            1: [{"frontier_name": "copper", "display_name": "Kupfer"}],
            2: [{"frontier_name": "gold", "display_name": "Gold"}],
        }

        class DatabaseStub:
            def surface_mining_commodity_options(self, commander_id):
                return options[commander_id]

        state = SimpleNamespace(database=DatabaseStub(), viewed_commander_id=1)
        combo = QComboBox()
        personal = QCheckBox()
        window = SimpleNamespace(
            state=state,
            chronicle_mining_commodity_combo=combo,
            chronicle_personally_mined_check=personal,
            _chronicle_mining_commander_id=lambda: state.viewed_commander_id,
            _update_chronicle_mining_commodity_enabled=lambda *_: None,
        )
        MainWindow._refresh_chronicle_mining_commodities(window)
        self.assertEqual(
            [(combo.itemText(i), combo.itemData(i)) for i in range(combo.count())],
            [("Alle", ""), ("Kupfer", "copper")],
        )
        state.viewed_commander_id = 2
        MainWindow._refresh_chronicle_mining_commodities(window)
        self.assertEqual(
            [(combo.itemText(i), combo.itemData(i)) for i in range(combo.count())],
            [("Alle", ""), ("Gold", "gold")],
        )

    def test_commodity_selection_requires_personal_filter_and_known_options(self):
        combo = QComboBox()
        combo.addItem("Alle", "")
        personal = QCheckBox()
        window = SimpleNamespace(
            chronicle_mining_commodity_combo=combo,
            chronicle_personally_mined_check=personal,
        )
        personal.setChecked(True)
        MainWindow._update_chronicle_mining_commodity_enabled(window)
        self.assertFalse(combo.isEnabled())
        combo.addItem("Kupfer", "copper")
        MainWindow._update_chronicle_mining_commodity_enabled(window)
        self.assertTrue(combo.isEnabled())
        personal.setChecked(False)
        MainWindow._update_chronicle_mining_commodity_enabled(window)
        self.assertFalse(combo.isEnabled())


if __name__ == "__main__":
    unittest.main()
