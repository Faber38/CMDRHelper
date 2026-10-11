"""Confirmed Interstellar Factors in station headers; no network or user DB."""
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from copy import deepcopy
import unittest

from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QBoxLayout

from cmdrhelper.i18n import _TRANSLATIONS, get_language, set_language
from cmdrhelper.spansh_cache import normalize, merge_stations
from cmdrhelper.ui.stations_view import StationCard
from cmdrhelper.ui.styles import DARK_STYLESHEET, LIGHT_STYLESHEET


class StationFactorsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.addCleanup(set_language, get_language())
        self.addCleanup(self.app.setStyleSheet, self.app.styleSheet())
        set_language('en')

    def card(self, services, name='Marshall Point', light=False):
        station = dict(station_name=name, station_type='Coriolis', spansh={'services': services})
        before = deepcopy(station)
        card = StationCard(station, 'Test', light=light)
        self.addCleanup(card.deleteLater)
        self.addCleanup(card.close)
        self.assertEqual(station, before)
        return card

    def settle(self):
        for _ in range(5):
            self.app.processEvents()

    def test_actual_spansh_spellings_normalize_to_confirmed_service(self):
        for spelling in ('Interstellar Factors', 'Interstellar Factors Contact'):
            with self.subTest(spelling=spelling):
                payload = {'system': {'id64': 1, 'name': 'Test', 'stations': [
                    {'id': 100, 'name': 'Marshall Point', 'type': 'Coriolis Starport',
                     'services': [spelling]}]}}
                result = normalize(payload, 1)
                self.assertEqual(result['stations'][0]['services'], ['factors'])
                merged = merge_stations([], result, [], 1)
                card = StationCard(merged[0], 'Test')
                self.addCleanup(card.deleteLater)
                self.assertEqual(card.factors.text(), '[Interstellar Factors]')

    def test_absent_unknown_and_name_alone_never_confirm(self):
        for services in (None, [], ['market'], ['unknown'], ['not_factors']):
            for name in ('Marshall Point', 'Interstellar Factors'):
                with self.subTest(services=services, name=name):
                    self.assertIsNone(self.card(services, name).factors)
        for station in ({'station_name': 'Marshall Point'},
                        {'station_name': 'Marshall Point', 'spansh': {}},
                        {'station_name': 'Marshall Point', 'spansh': None}):
            card = StationCard(station, 'Test')
            self.addCleanup(card.deleteLater)
            self.assertIsNone(card.factors)

    def test_all_twelve_existing_translations_keep_brackets(self):
        self.assertEqual(len(_TRANSLATIONS), 12)
        for language, table in _TRANSLATIONS.items():
            set_language(language)
            card = self.card(['factors'])
            self.assertEqual(card.factors.text(), '[' + table['spansh.service.factors'] + ']')

    def test_wide_header_preserves_image_and_subtitle_positions(self):
        ordinary = self.card(['market', 'repair'], 'Fukushima Terminal')
        factors = self.card(['market', 'factors'], 'Fukushima Terminal')
        for card in (ordinary, factors):
            card.resize(1000, card.sizeHint().height())
            card.show()
        self.settle()
        self.assertEqual(ordinary.image.geometry(), factors.image.geometry())
        self.assertEqual(ordinary.subtitle.geometry(), factors.subtitle.geometry())
        self.assertEqual(ordinary.header.height(), factors.header.height())

    def test_resize_theme_toggle_and_images(self):
        for light, style, color in ((False, DARK_STYLESHEET, '#38d9d0'),
                                    (True, LIGHT_STYLESHEET, '#38d9d0')):
            self.app.setStyleSheet(style)
            for name in ('Fukushima Terminal', 'Fukushima Terminal With A Much Longer Station Name'):
                card = self.card(['market', 'factors'], name, light)
                image_path = card.image._source_path
                card.resize(1000, 300)
                card.show()
                self.settle()
                for width in (1000, 360, 280, 1000):
                    card.resize(width, card.sizeHint().height())
                    self.settle()
                    self.assertEqual(card.width(), width)
                    for expanded in (True, False):
                        QTest.mouseClick(card.header, Qt.LeftButton)
                        self.settle()
                        self.assertEqual(card.header.isChecked(), expanded)
                        self.assertEqual(card.header.arrowType(), Qt.DownArrow if expanded else Qt.RightArrow)
                        self.assertTrue(card.factors.isVisible())
                        self.assertEqual(card.factors.palette().windowText().color().name(), color)
                        self.assertEqual(card.image._source_path, image_path)
                        self.assertEqual(card.image.width(), 112)
                        self.assertFalse(card.title.geometry().intersects(card.factors.geometry()))
                        for label in (card.title, card.factors):
                            self.assertTrue(card.header.rect().contains(label.geometry()))
                            self.assertGreaterEqual(label.height(), label.heightForWidth(label.width()))
                        self.assertEqual(card.factors.alignment() & Qt.AlignLeft, Qt.AlignLeft)
                        self.assertLess(card.factors.geometry().right(), card.header.width() - 22)
                        if width == 1000:
                            self.assertEqual(card.factors.x() - (card.title.x() + card.title.width()), 12)
                            name_width = card.title.fontMetrics().horizontalAdvance(name)
                            self.assertLessEqual(abs(card.title.width() - name_width), 1)
                            self.assertEqual(card.title.y(), card.factors.y())
                        else:
                            self.assertGreater(card.factors.y(), card.title.geometry().bottom())
                            self.assertEqual(card.factors.x(), card.title.x())
                    direction = card.header.title_row.direction()
                    self.assertEqual(direction, QBoxLayout.LeftToRight if width == 1000 else QBoxLayout.TopToBottom)
                card.set_light_mode(not light)
                self.settle()
                self.assertEqual(card.factors.palette().windowText().color().name(), color)
                card.close()

    def test_layout_without_factors_in_both_themes(self):
        for light, style in ((False, DARK_STYLESHEET), (True, LIGHT_STYLESHEET)):
            self.app.setStyleSheet(style)
            card = self.card(['market'], 'Fukushima Terminal', light)
            card.show()
            for width in (1000, 360):
                card.resize(width, card.sizeHint().height())
                self.settle()
                self.assertIsNone(card.factors)
                self.assertEqual(card.width(), width)
                for expanded in (True, False):
                    QTest.mouseClick(card.header, Qt.LeftButton)
                    self.settle()
                    self.assertEqual(card.header.isChecked(), expanded)
                    self.assertEqual(card.details.isVisible(), expanded)
                    self.assertEqual(card.header.arrowType(), Qt.DownArrow if expanded else Qt.RightArrow)
                    self.assertTrue(card.title.isVisible())
                    self.assertTrue(card.header.rect().contains(card.title.geometry()))
            card.close()


if __name__ == '__main__':
    unittest.main()
