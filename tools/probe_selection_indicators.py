"""Isolated native-style probe: synthetic market/cargo, no AppState or journals.

Run from the extracted test build with its Python environment. All fixture stores
are temporary; screenshots and style metadata go only to --output.
"""
import argparse
import json
from pathlib import Path
import sys
from types import SimpleNamespace
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'tests')]

from PySide6 import __version__ as pyside_version
from PySide6.QtCore import QEvent, QSettings, Qt, QTimer, qVersion
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QHBoxLayout,
                              QLabel, QPushButton, QRadioButton, QScrollArea, QStyleFactory,
                              QTabWidget, QVBoxLayout, QWidget)
from cmdrhelper.ui.selection_indicators import install_selection_indicators, set_selection_indicator_theme
from cmdrhelper.ui.styles import DARK_STYLESHEET, LIGHT_STYLESHEET
from cmdrhelper.ui.screenshot_view import ScreenshotView
from cmdrhelper.route_planner.carrier_input_widget import CarrierInputWidget
from test_saved_market_cargo_filter import CargoFilterTests


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--style', choices=QStyleFactory.keys())
    parser.add_argument('--baseline', action='store_true', help='Unmodified native style for comparison')
    parser.add_argument('--theme', choices=('dark', 'light'), default='dark')
    parser.add_argument('--font-size', type=int, default=10)
    parser.add_argument('--output', type=Path, default=Path('indicator-test-results'))
    parser.add_argument('--capture-and-exit', action='store_true')
    args = parser.parse_args()
    app = QApplication([])
    app.setApplicationName('CMDRHelper-Indicator-Probe')
    if args.style:
        app.setStyle(QStyleFactory.create(args.style))
    metadata = dict(qt=qVersion(), pyside=pyside_version, platform=app.platformName(),
                    native_style=app.style().metaObject().className(),
                    factory_key=app.style().objectName(), baseline=args.baseline)
    if not args.baseline:
        install_selection_indicators(app)
    proxy = getattr(app, '_selection_indicator_style', None)
    metadata['proxy'] = type(proxy).__name__ if proxy else None
    print(json.dumps(metadata, indent=2), flush=True)
    window = QWidget()
    window.setWindowTitle('CMDRHelper – isolierter Windows-Indikatortest (keine Veröffentlichung)')
    window.resize(1024, 768)
    layout = QVBoxLayout(window)
    layout.addWidget(QLabel(f"Qt {qVersion()} | {metadata['native_style']} | Proxy: {metadata['proxy']}"))
    controls = QHBoxLayout()
    theme = QComboBox(); theme.addItems(['dark', 'light']); theme.setCurrentText(args.theme)
    font = QComboBox(); font.addItems(['10', '14', '18']); font.setCurrentText(str(args.font_size))
    capture = QPushButton('Screenshots + Stilprotokoll speichern')
    for widget in (theme, font, capture):
        controls.addWidget(widget)
    layout.addLayout(controls)
    tabs = QTabWidget(); layout.addWidget(tabs)

    def apply_theme():
        set_selection_indicator_theme(app, theme.currentText())
        sheet = LIGHT_STYLESHEET if theme.currentText() == 'light' else DARK_STYLESHEET
        app.setStyleSheet(sheet + f'\nQWidget {{font-size:{font.currentText()}pt;}}')
    apply_theme()
    fixture = CargoFilterTests()
    fixture.setUpClass(); fixture.setUp()
    fixture.view.hide()
    tabs.addTab(fixture.view, 'Markt ansehen / Fracht (synthetisch)')
    matrix = QWidget(); rows = QVBoxLayout(matrix)
    for disabled in (False, True):
        for kind, states in ((QCheckBox, (Qt.Unchecked, Qt.PartiallyChecked, Qt.Checked)),
                             (QRadioButton, (Qt.Unchecked, Qt.Checked))):
            row = QHBoxLayout()
            for state in states:
                widget = kind(f'{state.name}' + (' / deaktiviert' if disabled else ''))
                if kind == QCheckBox:
                    widget.setCheckState(state)
                else:
                    widget.setAutoExclusive(False); widget.setChecked(state == Qt.Checked)
                widget.setEnabled(not disabled); row.addWidget(widget)
            rows.addLayout(row)
    late = QPushButton('Checkbox dynamisch hinzufügen')
    late.clicked.connect(lambda: rows.addWidget(QCheckBox('Dynamische Checkbox')))
    rows.addWidget(late)
    carrier = CarrierInputWidget(SimpleNamespace())
    rows.addWidget(carrier)
    settings = QSettings(str(fixture.root / 'probe.ini'), QSettings.IniFormat)
    with patch.multiple(ScreenshotView, _load_settings=Mock(), _sync_source=Mock(),
                        _request_gallery_refresh=Mock(), _update_watch_state=Mock()):
        screenshots = ScreenshotView(SimpleNamespace(settings=settings))
    # Keep the real protected widgets, without loading folders or starting watchers.
    rows.addWidget(screenshots.auto_check); rows.addWidget(screenshots.delete_check)
    rows.addStretch()
    scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setWidget(matrix)
    tabs.addTab(scroll, 'Zustände / Sonderindikatoren')
    theme.currentTextChanged.connect(apply_theme)
    font.currentTextChanged.connect(apply_theme)

    def save():
        args.output.mkdir(parents=True, exist_ok=True)
        prefix = f"{metadata['factory_key']}-{theme.currentText()}-{font.currentText()}-{'before' if args.baseline else 'after'}"
        selected = tabs.currentIndex()
        for index in range(tabs.count()):
            tabs.setCurrentIndex(index); app.processEvents()
            if index == 0:
                fixture.view.scroll.ensureWidgetVisible(fixture.view.cargo_only)
                app.processEvents()
            window.grab().save(str(args.output / f'{prefix}-{index}.png'))
        tabs.setCurrentIndex(selected)
        record = dict(metadata, theme=theme.currentText(), font=font.currentText(),
                      screen=app.primaryScreen().size().toTuple(), window=window.size().toTuple())
        (args.output / f'{prefix}.json').write_text(json.dumps(record, indent=2), encoding='utf-8')
        print(f'Gespeichert: {args.output.resolve()} / {prefix}', flush=True)
        if args.capture_and_exit:
            app.quit()
    capture.clicked.connect(save)
    window.show()
    if args.capture_and_exit:
        QTimer.singleShot(350, save)
    try:
        return app.exec()
    finally:
        fixture.doCleanups()
        screenshots.close(); screenshots.deleteLater()
        window.close(); window.deleteLater()
        app.sendPostedEvents(None, QEvent.DeferredDelete)


if __name__ == '__main__':
    raise SystemExit(main())
