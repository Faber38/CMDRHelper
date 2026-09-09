"""Render reproducible offline overview screenshots from saved-system fixtures.

QT_QPA_PLATFORM=offscreen venv/bin/python tools/render_system_overview.py /tmp/system-overview
"""
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from PySide6.QtCore import QRectF
from PySide6.QtGui import QColor, QImage, QPainter
from PySide6.QtWidgets import QApplication
from cmdrhelper.i18n import set_language
from cmdrhelper.ui.styles import DARK_STYLESHEET, LIGHT_STYLESHEET
from cmdrhelper.ui.system_overview import SystemOverviewDialog, THEMES


def main():
    output = Path(sys.argv[1] if len(sys.argv) > 1 else '/tmp/cmdrhelper-system-overview')
    output.mkdir(parents=True, exist_ok=True)
    app = QApplication.instance() or QApplication([])
    set_language('de')
    systems = json.loads((ROOT / 'tests/fixtures/system_overview_saved.json').read_text())
    for label, system in zip(('small', 'complex', 'binary'), systems):
        for light in (False, True):
            theme = 'light' if light else 'dark'
            app.setStyleSheet(LIGHT_STYLESHEET if light else DARK_STYLESHEET)
            dialog = SystemOverviewDialog(system['system'], system['bodies'], light=light,
                                          system_address=system['system_address'],
                                          commander_id=system['commander_id'])
            dialog.resize(1250, 850)
            dialog.show()
            app.processEvents()
            view = dialog.preview
            dialog.grab().save(str(output / f'{label}-{theme}-window.png'))
            rect = view.sceneRect()
            image = QImage(int(rect.width()) + 1, int(rect.height()) + 1, QImage.Format.Format_ARGB32)
            image.fill(QColor(THEMES[light]['background']))
            painter = QPainter(image)
            painter.setRenderHints(QPainter.RenderHint.Antialiasing | QPainter.RenderHint.SmoothPixmapTransform)
            view.scene().render(painter, QRectF(image.rect()), rect)
            painter.end()
            image.save(str(output / f'{label}-{theme}-full.png'))
            print(f'{label}/{theme}: {system["system"]}, {len(system["bodies"])} bodies, '
                  f'{int(rect.width())} × {int(rect.height())} px')
            dialog.close()


if __name__ == '__main__':
    main()
