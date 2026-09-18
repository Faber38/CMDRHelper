"""UI-only facility cards, local assets and existing image viewer."""
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import copy
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QImage, QPainterPath, QPainterPathStroker, QColor
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication
from cmdrhelper.ui import station_items, station_assets
from cmdrhelper.ui.station_details import StationDetailDialog, StationSelectionDialog
from cmdrhelper.ui.ship_widgets import ShipImageViewer
from cmdrhelper.ui.system_overview import SystemOverviewView, THEMES
from cmdrhelper.ui.system_view import SystemMapWidget
from tests.test_system_stations import BODIES, station


class StationPresentationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def tearDown(self):
        for window in self.app.topLevelWidgets(): window.close()
        self.app.processEvents()

    def test_cards_reserve_space_without_intersections(self):
        bodies = BODIES + [dict(body_id=3, name='Test 2', parent_id=0, body_type='Planet')]
        stations = [station(i, parent=p) for p in (0, 1, 2, 3) for i in range(3)]
        view = SystemOverviewView('Test', bodies, stations=stations)
        cards = [i.sceneBoundingRect() for i in view.facility_items]
        for i, rect in enumerate(cards):
            self.assertEqual(rect.width(), station_items.CARD_WIDTH)
            self.assertEqual(rect.height(), 64)
            for other in cards[i+1:]: self.assertFalse(rect.intersects(other))
            for body in view.items_by_key.values():
                self.assertFalse(rect.intersects(body.sceneBoundingRect()))
            for line in view.connections:
                # The paths must not enter the card interior.
                path = line.path() if hasattr(line, 'path') else QPainterPath()
                if hasattr(line, 'line'):
                    path.moveTo(line.line().p1()); path.lineTo(line.line().p2())
                # Open orbital paths have no fill. QGraphicsItem.shape() also
                # includes their implicit closing polygon, which is not drawn.
                stroke = QPainterPathStroker(); stroke.setWidth(line.pen().widthF())
                self.assertFalse(stroke.createStroke(path).intersects(rect.adjusted(2, 2, -2, -2)))

    def test_group_card_uses_other_title_and_count(self):
        view = SystemOverviewView('Test', BODIES, stations=[station(i, parent=None) for i in range(5)])
        self.assertEqual(len(view.facility_items), 1)
        self.assertIsNone(view.facility_footer)  # Title is inside the card.
        item = view.facility_items[0]
        self.assertEqual(station_items.card_title(item.stations), station_items.tr('facilities.other'))
        self.assertIn('5', station_items.label(item.stations))

    def test_painter_uses_existing_theme_accent_and_readable_fonts(self):
        from unittest.mock import Mock
        for light in (False, True):
            painter = Mock()
            rect = station_items.QRectF(0, 0, 252, 64)
            from PySide6.QtGui import QFont
            painter.font.return_value = QFont()
            station_items.paint_facility(painter, rect, [station()], light)
            self.assertEqual(painter.setPen.call_args_list[0].args[0].color(), QColor(THEMES[light]['selected']))
            texts = [c.args[2] for c in painter.drawText.call_args_list]
            self.assertIn('Station', texts)
            self.assertIn(station_items.tr('facilities.outpost'), texts)
            fonts = [c.args[0] for c in painter.setFont.call_args_list]
            self.assertGreaterEqual(fonts[-1].pointSizeF(), 9)

    def test_card_click_opens_large_detail_and_preserves_map(self):
        for kind, name in [('FleetCarrier', '[EOT] = RHEIN-ERFT ='), ('CraterOutpost', 'Ridorana Metalworks')]:
            facility = dict(station(name=name), station_type=kind)
            view = SystemOverviewView('Test', BODIES, stations=[facility])
            original = copy.deepcopy(view.bodies)
            view.resize(950, 650);view.show();self.app.processEvents()
            item = view.facility_items[0]
            view.centerOn(item);self.app.processEvents()
            QTest.mouseClick(view.viewport(), Qt.LeftButton, pos=view.mapFromScene(item.sceneBoundingRect().center()))
            detail = view.findChild(StationDetailDialog)
            self.assertIsNotNone(detail)
            self.assertTrue(detail.isVisible());self.assertTrue(view.isVisible())
            self.assertGreaterEqual(detail.width(), 700)
            self.assertEqual(detail.image.width(), 640)
            self.assertIn(kind, detail.info.text())
            self.assertEqual(view.bodies, original)
            detail.close();view.close();self.app.processEvents()

    def test_group_click_selection_opens_same_detail(self):
        data = [station(i, parent=None, name=f'Facility {i}') for i in range(5)]
        view = SystemOverviewView('Test', BODIES, stations=data)
        view.resize(950, 650);view.show();self.app.processEvents()
        item = view.facility_items[0];view.centerOn(item);self.app.processEvents()
        QTest.mouseClick(view.viewport(), Qt.LeftButton, pos=view.mapFromScene(item.sceneBoundingRect().center()))
        selector = view.findChild(StationSelectionDialog)
        listing = selector.listing
        QTest.mouseClick(listing.viewport(), Qt.LeftButton, pos=listing.visualItemRect(listing.item(2)).center())
        self.assertIsInstance(selector._details, StationDetailDialog)
        self.assertEqual(selector._details.windowTitle(), 'Facility 2')
        self.assertTrue(view.isVisible())

    def test_unknown_values_not_fabricated(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(station_assets, 'STATION_ASSET_DIR', Path(directory)):
            detail = StationDetailDialog({'station_name':'Unknown facility', 'station_type':'UnlistedType'}, '', light=True)
        text = detail.info.text()
        self.assertIn('UnlistedType', text)
        self.assertNotIn('MarketID', text)
        self.assertNotIn(station_items.tr('facilities.parent') + ':', text)
        self.assertFalse(detail.image.property('hasShipImage'))
        self.assertIsNone(detail.image._source_path)

    def test_all_image_classes_and_unknown_safe_fallback(self):
        for kind, expected in station_assets.IMAGE_CLASSES.items():
            self.assertEqual(station_assets.station_image_class({'station_type':kind}), expected)
        for kind in (None, 'Unknown', '../../ships/mandalay'):
            self.assertEqual(station_assets.station_image_class({'station_type':kind}), 'standard')
        self.assertIsNone(station_assets.bundled_image('../ships/mandalay'))

    def test_resolver_type_standard_placeholder_and_corrupt_file(self):
        source = Path('cmdrhelper/assets/bodies/belt_cluster.png')
        with tempfile.TemporaryDirectory() as directory, patch.object(station_assets, 'STATION_ASSET_DIR', Path(directory)):
            root = Path(directory)
            self.assertEqual(station_assets.station_preview({'station_type':'Dodec'}, 100, 100), (None, None))
            shutil.copyfile(source, root/'standard.png')
            self.assertEqual(station_assets.station_preview({'station_type':'Dodec'},100,100)[1], root/'standard.png')
            shutil.copyfile(source, root/'dodec.png')
            self.assertEqual(station_assets.station_preview({'station_type':'Dodec'},100,100)[1], root/'dodec.png')
            (root/'dodec.png').write_bytes(b'not an image')
            self.assertEqual(station_assets.station_preview({'station_type':'Dodec'},100,100)[1], root/'standard.png')
            self.assertEqual(station_assets.station_preview({'station_type':'Unknown'},100,100)[1], root/'standard.png')

    def test_double_click_reuses_existing_full_resolution_viewer(self):
        source = Path('cmdrhelper/assets/bodies/belt_cluster.png')
        with tempfile.TemporaryDirectory() as directory, patch.object(station_assets, 'STATION_ASSET_DIR', Path(directory)):
            shutil.copyfile(source, Path(directory)/'fleet_carrier.png')
            detail = StationDetailDialog(dict(station(name='Own carrier'),station_type='FleetCarrier'), 'Test')
            detail.show();self.app.processEvents()
            QTest.mouseDClick(detail.image, Qt.LeftButton)
            viewer = detail.findChild(ShipImageViewer)
            self.assertIsNotNone(viewer)
            self.assertEqual(viewer.windowTitle(), 'Own carrier')
            self.assertEqual(viewer.canvas.image.size(), QImage(str(source)).size())
            self.assertTrue(detail.isVisible())

    def test_surface_flag_does_not_override_explicit_or_orbital_types(self):
        for kind, expected in [('Planetary Construction Depot', 'surface_station'),
                               ('CraterOutpost', 'surface_station'), ('CraterPort', 'surface_station'),
                               ('OnFootSettlement', 'settlement'), ('Coriolis', 'coriolis'),
                               ('Dodec', 'dodec'), ('Outpost', 'outpost'),
                               ('FleetCarrier', 'fleet_carrier'), ('MegaShip', 'megaship'),
                               ('Space Construction Depot', 'standard'), ('Bernal', 'standard'),
                               ('AsteroidBase', 'standard')]:
            with self.subTest(kind=kind):
                self.assertEqual(station_assets.station_image_class(
                    {'station_type': kind, 'is_planetary': True}), expected)
        for kind in (None, 'Unknown'):
            self.assertEqual(station_assets.station_image_class(
                {'station_type': kind, 'is_planetary': True}), 'surface_station')
            for flag in (False, None, 'true', 1):
                self.assertEqual(station_assets.station_image_class(
                    {'station_type': kind, 'is_planetary': flag}), 'standard')

    def test_settlement_surface_standard_and_placeholder_chain(self):
        source = Path('cmdrhelper/assets/bodies/belt_cluster.png')
        with tempfile.TemporaryDirectory() as directory, patch.object(station_assets, 'STATION_ASSET_DIR', Path(directory)):
            root = Path(directory)
            facility = {'station_type': 'OnFootSettlement'}
            self.assertEqual(station_assets.station_preview(facility, 100, 100), (None, None))
            for name in ('standard', 'surface_station', 'settlement'):
                shutil.copyfile(source, root / (name + '.png'))
                self.assertEqual(station_assets.station_preview(facility, 100, 100)[1], root / (name + '.png'))
            (root / 'settlement.png').write_bytes(b'broken')
            self.assertEqual(station_assets.station_preview(facility, 100, 100)[1], root / 'surface_station.png')
            (root / 'surface_station.png').write_bytes(b'broken')
            self.assertEqual(station_assets.station_preview(facility, 100, 100)[1], root / 'standard.png')
            (root / 'standard.png').write_bytes(b'broken')
            self.assertEqual(station_assets.station_preview(facility, 100, 100), (None, None))

    def test_missing_orbital_image_ignores_planetary_flag(self):
        source = Path('cmdrhelper/assets/bodies/belt_cluster.png')
        with tempfile.TemporaryDirectory() as directory, patch.object(station_assets, 'STATION_ASSET_DIR', Path(directory)):
            root = Path(directory)
            for name in ('surface_station', 'standard'):
                shutil.copyfile(source, root / (name + '.png'))
            for kind in ('Coriolis', 'Dodec', 'Space Construction Depot', 'FleetCarrier'):
                self.assertEqual(station_assets.station_preview(
                    {'station_type': kind, 'is_planetary': True}, 100, 100)[1], root / 'standard.png')

    def test_fit_reset_hover_and_tooltip(self):
        name = 'Long facility name ' * 15
        view = SystemOverviewView('Test', BODIES, stations=[station(name=name)])
        view.resize(800,600);view.show();self.app.processEvents()
        item = view.facility_items[0]
        self.assertIn(name, item.toolTip())
        item.hoverEnterEvent(None);self.assertTrue(item.hovered)
        item.hoverLeaveEvent(None);self.assertFalse(item.hovered)
        view.fit_system();self.assertGreater(view.transform().m11(),0)
        view.reset_zoom();self.assertEqual(view.transform().m11(),1)
        for light in (False,True):
            view.set_light_mode(light);self.assertFalse(view.grab().isNull())
