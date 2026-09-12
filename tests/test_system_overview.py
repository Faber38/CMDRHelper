import copy
import json
import os
from pathlib import Path
import random
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from PySide6.QtCore import QEvent, QPoint, QPointF, QSettings, Qt
from PySide6.QtGui import QWheelEvent
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QLabel, QMainWindow, QPushButton

from cmdrhelper.ui.main_window import MainWindow, ChronicleSystemWindow
from cmdrhelper.ui.system_overview import (
    SystemOverviewDialog, SystemOverviewView, THEMES, build_layout, body_diameter,
)
from cmdrhelper.ui.system_view import SystemMapWidget
from cmdrhelper.ui.styles import DARK_STYLESHEET, LIGHT_STYLESHEET


def star(i=0, parent=None):
    return dict(body_id=i, name=f'Test {i}', short_name=str(i), body_type='Star',
                star_type='G', parent_id=parent, radius_m=696340000)


def planet(i=1, parent=0, **extra):
    return dict(body_id=i, name=f'Test {i}', short_name=str(i), body_type='Planet',
                planet_class='Rocky body', parent_id=parent, radius_m=2500000, **extra)


def real_systems():
    return json.loads((Path(__file__).parent / 'fixtures/system_overview_saved.json').read_text())


class OverviewLayoutTests(unittest.TestCase):
    def assert_no_overlap(self, nodes):
        visible = [n for n in nodes.values() if n.body is not None]
        for i, a in enumerate(visible):
            for b in visible[i + 1:]:
                self.assertFalse(a.rect.intersects(b.rect), (a.key, b.key, a.rect, b.rect))

    def test_single_star(self):
        nodes = build_layout([star()])
        self.assertEqual(len(nodes), 1)
        self.assertIsNone(nodes['body', 0].parent)
        self.assertGreaterEqual(nodes['body', 0].diameter, 124)

    def test_star_and_one_planet_on_horizontal_axis(self):
        nodes = build_layout([star(), planet()])
        self.assertEqual(nodes['body', 0].y, nodes['body', 1].y)
        self.assertLess(nodes['body', 0].x, nodes['body', 1].x)
        self.assertEqual(nodes['body', 1].parent, ('body', 0))
        self.assert_no_overlap(nodes)

    def test_multiple_planets_ordered_by_orbit(self):
        nodes = build_layout([star(), planet(1, semi_major_axis=300), planet(2, semi_major_axis=100)])
        self.assertLess(nodes['body', 2].x, nodes['body', 1].x)
        self.assert_no_overlap(nodes)

    def test_arrival_distance_does_not_reverse_planets_or_moons(self):
        nodes = build_layout([star(), planet(1, distance_ls=900), planet(2, distance_ls=100),
                              planet(3, 1, distance_ls=901), planet(4, 1, distance_ls=899)])
        self.assertLess(nodes['body', 1].x, nodes['body', 2].x)
        self.assertLess(nodes['body', 3].y, nodes['body', 4].y)

    def test_one_moon_below_its_planet(self):
        nodes = build_layout([star(), planet(), planet(2, 1)])
        self.assertGreater(nodes['body', 2].y, nodes['body', 1].y)
        self.assertEqual(nodes['body', 2].parent, ('body', 1))
        self.assert_no_overlap(nodes)

    def test_multiple_moons_use_bounded_columns(self):
        nodes = build_layout([star(), planet()] + [planet(i, 1) for i in range(2, 14)])
        self.assertEqual(len({nodes['body', i].x for i in range(2, 14)}), 3)
        self.assertLess(max(n.rect.bottom() for n in nodes.values()), 1100)
        self.assert_no_overlap(nodes)

    def test_moon_of_moon_retains_parent(self):
        nodes = build_layout([star(), planet(), planet(2, 1), planet(3, 2), planet(4, 1)])
        self.assertEqual(nodes['body', 3].parent, ('body', 2))
        self.assertGreater(nodes['body', 3].y, nodes['body', 2].y)
        self.assert_no_overlap(nodes)

    def test_belts_keep_parent_and_compact_layout(self):
        belts = [dict(body_id=i, name=f'Test A Belt Cluster {i}', body_type='Belt Cluster', parent_id=0)
                 for i in range(1, 11)]
        nodes = build_layout([star()] + belts)
        groups = [n for n in nodes.values() if n.belt_members]
        self.assertEqual(len(groups), 1)
        self.assertEqual(groups[0].parent, ('body', 0))
        self.assertEqual(groups[0].y, nodes['body', 0].y)
        self.assertEqual(len(groups[0].belt_members), 10)
        self.assert_no_overlap(nodes)

    def test_binary_companion_gets_separate_axis(self):
        nodes = build_layout([star(), star(10, 0)])
        self.assertEqual(nodes['body', 10].parent, ('body', 0))
        self.assertGreater(nodes['body', 10].y, nodes['body', 0].y)
        self.assertGreater(nodes['body', 10].diameter, 100)

    def test_second_star_has_its_own_planets(self):
        nodes = build_layout([star(), planet(), star(10, 0), planet(11, 10), planet(12, 11)])
        self.assertEqual(nodes['body', 11].y, nodes['body', 10].y)
        self.assertEqual(nodes['body', 12].parent, ('body', 11))
        self.assert_no_overlap(nodes)

    def test_unrelated_root_stars_are_not_invented_as_parent_child(self):
        nodes = build_layout([star(), star(10), planet(11, 10)])
        self.assertIsNone(nodes['body', 10].parent)
        self.assertGreater(nodes['body', 10].y, nodes['body', 0].y)
        self.assert_no_overlap(nodes)

    def test_raw_parents_preserve_barycentre_and_override_misleading_name(self):
        bodies = [star(), star(10), planet(11, 0), planet(12, 0)]
        bodies[0]['Parents'] = [{'Null': 99}]
        bodies[1]['Parents'] = [{'Null': 99}]
        bodies[2]['name'] = 'Test A 1'
        bodies[2]['Parents'] = [{'Star': 10}, {'Null': 99}]
        bodies[3]['Parents'] = [{'Planet': 11}, {'Star': 10}, {'Null': 99}]
        nodes = build_layout(bodies)
        self.assertEqual(nodes['body', 0].parent, ('Null', 99))
        self.assertEqual(nodes['body', 10].parent, ('Null', 99))
        self.assertEqual(nodes['body', 11].parent, ('body', 10))
        self.assertEqual(nodes['body', 12].parent, ('body', 11))
        self.assert_no_overlap(nodes)

    def test_missing_parent_remains_explicit_junction(self):
        nodes = build_layout([star(), planet(2, 77), planet(3, 77)])
        self.assertIsNone(nodes['body', 77].body)
        self.assertEqual(nodes['body', 2].parent, ('body', 77))
        self.assert_no_overlap(nodes)

    def test_stellar_parent_fallback_without_name_guessing(self):
        bodies = [star(10), planet(1, None, parent_star_id=10), planet(2, None)]
        nodes = build_layout(bodies)
        self.assertEqual(nodes['body', 1].parent, ('body', 10))
        self.assertIsNone(nodes['body', 2].parent)

    def test_corrupt_cycle_is_renderable(self):
        nodes = build_layout([planet(1, 2), planet(2, 1)])
        self.assertEqual(sum(n.parent is None for n in nodes.values()), 1)
        self.assert_no_overlap(nodes)

    def test_more_than_fifty_bodies_do_not_overlap(self):
        bodies = [star()]
        for i in range(1, 10):
            bodies.append(planet(i))
            bodies.extend(planet(i * 100 + j, i) for j in range(1, 7))
        nodes = build_layout(bodies)
        self.assertEqual(len(nodes), 64)
        self.assert_no_overlap(nodes)

    def test_order_is_stable_for_shuffled_input(self):
        bodies = [star(), star(20, 0)] + [planet(i, 0 if i < 10 else 20) for i in range(1, 20)]
        expected = {k: (n.x, n.y, n.parent) for k, n in build_layout(bodies).items()}
        random.Random(42).shuffle(bodies)
        actual = {k: (n.x, n.y, n.parent) for k, n in build_layout(bodies).items()}
        self.assertEqual(actual, expected)

    def test_body_sizes_are_bounded_and_distinct(self):
        gas = planet()
        gas['planet_class'] = 'Sudarsky class I gas giant'
        moon = planet()
        moon['radius_m'] = 100
        self.assertGreater(body_diameter(star()), body_diameter(gas))
        self.assertGreater(body_diameter(gas), body_diameter(moon))
        self.assertGreaterEqual(body_diameter(moon), 30)
        giant = star()
        giant['radius_m'] = 1e30
        self.assertLessEqual(body_diameter(giant), 148)

    def test_real_saved_systems_preserve_bodies_and_parents(self):
        for system in real_systems():
            with self.subTest(system=system['system']):
                nodes = build_layout(system['bodies'])
                represented = {body['body_id']: n for n in nodes.values() if n.body is not None
                               for body in (n.belt_members or (n.body,))}
                self.assertEqual(set(represented), {b['body_id'] for b in system['bodies']})
                for body in system['bodies']:
                    parent = body.get('parent_id')
                    if parent is not None:
                        self.assertEqual(represented[body['body_id']].parent, ('body', parent))
                self.assert_no_overlap(nodes)


class OverviewViewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.settings = QSettings(str(Path(self.tmp.name) / 'ui.ini'), QSettings.Format.IniFormat)
        self.addCleanup(self.app.setStyleSheet, self.app.styleSheet())

    def dialog(self, bodies=None, **kwargs):
        dialog = SystemOverviewDialog('Test', bodies if bodies is not None else [star(), planet()],
                                      settings=self.settings, **kwargs)
        self.addCleanup(dialog.close)
        dialog.show()
        self.app.processEvents()
        return dialog

    def click_body(self, view, key):
        item = view.items_by_key[key]
        point = view.mapFromScene(item.sceneBoundingRect().center())
        QTest.mouseClick(view.viewport(), Qt.MouseButton.LeftButton, pos=point)
        return item

    def test_body_click_uses_existing_callback_and_selects_body(self):
        callback = Mock()
        dialog = self.dialog(on_body_clicked=callback)
        item = self.click_body(dialog.preview, ('body', 1))
        callback.assert_called_once_with(item.node.body)
        self.assertTrue(item.isSelected())

    def test_existing_overview_actions_have_hand_cursor_in_both_themes(self):
        for light, style in ((False, DARK_STYLESHEET), (True, LIGHT_STYLESHEET)):
            self.app.setStyleSheet(style)
            callback = Mock()
            dialog = self.dialog(light=light, on_body_clicked=callback)
            view = dialog.preview
            layout = {key: item.sceneBoundingRect() for key, item in view.items_by_key.items()}
            for item in view.items_by_key.values():
                self.assertEqual(item.cursor().shape(), Qt.PointingHandCursor)
            for button in dialog.findChildren(QPushButton):
                self.assertEqual(button.cursor().shape(), Qt.PointingHandCursor)
            for label in dialog.findChildren(QLabel):
                self.assertEqual(label.cursor().shape(), Qt.ArrowCursor)
            for line in view.connections:
                self.assertFalse(line.hasCursor())
            self.assertEqual(dialog.cursor().shape(), Qt.ArrowCursor)
            self.click_body(view, ('body', 1))
            callback.assert_called_once_with(view.items_by_key['body', 1].node.body)
            view.scale(1.2, 1.2)
            QTest.mouseClick(dialog.reset_button, Qt.LeftButton)
            self.assertEqual(view.transform().m11(), 1.0)
            QTest.mouseClick(dialog.fit_button, Qt.LeftButton)
            self.assertLessEqual(view.transform().m11(), 1.0)
            self.assertEqual(layout, {key: item.sceneBoundingRect() for key, item in view.items_by_key.items()})
            close, = [b for b in dialog.findChildren(QPushButton)
                      if b not in (dialog.reset_button, dialog.fit_button)]
            QTest.mouseClick(close, Qt.LeftButton)
            self.assertFalse(dialog.isVisible())

    def test_snapshot_is_independent_of_current_journal_state(self):
        bodies = [star(), planet()]
        original = copy.deepcopy(bodies)
        dialog = self.dialog(bodies)
        bodies[1]['parent_id'] = 99
        bodies.clear()
        self.assertEqual(dialog.preview.bodies, original)

    def test_empty_saved_system_shows_existing_empty_message(self):
        dialog = self.dialog([])
        self.assertFalse(dialog.preview.items_by_key)
        self.assertTrue(dialog.preview.empty_label.toPlainText())

    def test_dark_and_light_background_labels_lines_hover_selection(self):
        dialog = self.dialog()
        view = dialog.preview
        for light in (False, True):
            with self.subTest(light=light):
                self.app.setStyleSheet(LIGHT_STYLESHEET if light else DARK_STYLESHEET)
                dialog.set_light_mode(light)
                self.app.processEvents()
                theme = THEMES[light]
                self.assertEqual(view.backgroundBrush().color().name(), theme['background'])
                self.assertTrue(all(line.pen().color().name() == theme['line'] for line in view.connections))
                item = view.items_by_key['body', 1]
                item.setSelected(False)
                QTest.mouseMove(view.viewport(), QPoint(3, 3))
                QTest.mouseMove(view.viewport(), view.mapFromScene(item.sceneBoundingRect().center()))
                self.assertTrue(item.hovered)
                border = view.mapFromScene(item.mapToScene(QPointF(40, 3)))
                self.assertEqual(view.viewport().grab().toImage().pixelColor(border).name(), theme['hover'])
                self.click_body(view, ('body', 1))
                self.assertTrue(item.isSelected())
                self.assertEqual(view.viewport().grab().toImage().pixelColor(border).name(), theme['selected'])
                self.assertEqual(item.light, light)
                self.assertTrue(item.name)
                self.assertTrue(item.type_text)
                self.assertFalse(view.grab().isNull())

    def test_small_systems_are_centered_at_readable_native_size(self):
        for bodies in ([star()], [star(), planet()]):
            dialog = self.dialog(bodies)
            view = dialog.preview
            center = view.mapFromScene(view.sceneRect().center())
            self.assertLess(abs(center.x() - view.viewport().width() / 2), 3)
            self.assertLess(abs(center.y() - view.viewport().height() / 2), 3)
            self.assertEqual(view.transform().m11(), 1)
            self.assertGreater(view.items_by_key['body', 0].node.diameter, 100)

    def test_large_system_is_scrollable_and_starts_at_main_star(self):
        dialog = self.dialog([star()] + [planet(i) for i in range(1, 35)])
        view = dialog.preview
        bar = view.horizontalScrollBar()
        self.assertGreater(bar.maximum(), bar.minimum())
        self.assertEqual(bar.value(), bar.minimum())
        self.assertTrue(view.viewport().rect().contains(view.mapFromScene(view.nodes['body', 0].center)))
        bar.setValue(bar.maximum())
        self.assertEqual(bar.value(), bar.maximum())

    def test_ctrl_wheel_zoom_and_reset_and_fit(self):
        dialog = self.dialog([star()] + [planet(i) for i in range(1, 35)])
        view = dialog.preview
        for _ in range(20):
            event = QWheelEvent(QPointF(200, 100), QPointF(200, 100), QPoint(), QPoint(0, 120),
                                Qt.MouseButton.NoButton, Qt.KeyboardModifier.ControlModifier,
                                Qt.ScrollPhase.NoScrollPhase, False)
            QApplication.sendEvent(view.viewport(), event)
        self.assertAlmostEqual(view.transform().m11(), 1.8)
        dialog.fit_button.click()
        self.assertLess(view.transform().m11(), 1)
        dialog.reset_button.click()
        self.assertEqual(view.transform().m11(), 1)

    def test_geometry_is_restored(self):
        dialog = self.dialog()
        dialog.resize(700, 500)
        dialog.close()
        reopened = self.dialog()
        self.assertEqual(reopened.size(), dialog.size())

    def test_shared_body_image_resolver_handles_stars_planets_and_belts(self):
        belt = dict(body_id=2, name='Test Belt Cluster 1', parent_id=0)
        dialog = self.dialog([star(), planet(), belt])
        for item in dialog.preview.items_by_key.values():
            self.assertIsNotNone(dialog.preview.resolver._body_pixmap(item.node.body))
        self.assertEqual(SystemMapWidget._body_image_name(belt), 'belt_cluster.png')

    def test_padded_star_artwork_is_sized_by_visible_content(self):
        body = star()
        body['star_type'] = 'M'
        dialog = self.dialog([body])
        item = dialog.preview.items_by_key['body', 0]
        self.assertGreater(item.image_source.width(), 0)
        self.assertLess(item.image_source.height(), item.pixmap.height())
        # The artwork is round although its original transparent canvas is tall.
        self.assertAlmostEqual(item.image_source.width() / item.image_source.height(), 1, delta=0.15)

    def test_explorer_opens_shared_view_with_its_context_and_detail_callback(self):
        window = MainWindow.__new__(MainWindow)
        QMainWindow.__init__(window)
        self.addCleanup(window.close)
        window.ui_theme = 'light'
        window.state = SimpleNamespace(system='Stored Explorer', system_address=123, commander_id=7,
                                       system_bodies=[star(), planet()], settings=self.settings)
        window._system_overview_window = None
        window._show_body_details = Mock()
        window._show_system_overview()
        dialog = window._system_overview_window
        self.addCleanup(dialog.close)
        self.app.processEvents()
        self.assertIsInstance(dialog.preview, SystemOverviewView)
        self.assertEqual((dialog.system_address, dialog.commander_id), (123, 7))
        self.assertTrue(dialog.preview.light)
        self.click_body(dialog.preview, ('body', 1))
        window._show_body_details.assert_called_once()

    def test_chronicle_button_opens_same_renderer_with_saved_context(self):
        callback = Mock()
        window = ChronicleSystemWindow('Historic system', [star(), planet()], '', callback,
                                       system_address=456, commander_id=9, settings=self.settings)
        self.addCleanup(window.close)
        before = copy.deepcopy(window.system_map.bodies)
        window.system_map.set_light_mode(True)
        window.system_overview_button.click()
        dialog = window._system_overview_window
        self.app.processEvents()
        self.assertIsInstance(dialog.preview, SystemOverviewView)
        self.assertEqual(dialog.system_name, 'Historic system')
        self.assertEqual((dialog.system_address, dialog.commander_id), (456, 9))
        self.assertTrue(dialog.preview.light)
        self.click_body(dialog.preview, ('body', 1))
        callback.assert_called_once()
        self.assertEqual(window.system_map.bodies, before)
        window.close()
        self.assertFalse(dialog.isVisible())

    def test_chronicle_entry_loads_requested_commander_not_current_system(self):
        window = MainWindow.__new__(MainWindow)
        QMainWindow.__init__(window)
        self.addCleanup(window.close)
        saved = real_systems()[0]
        database = Mock()
        database.chronicle_system_details.return_value = saved
        window.state = SimpleNamespace(database=database, commander_id=99, viewed_commander_id=99,
                                       system='Unrelated live system', settings=self.settings)
        window.ui_theme = 'dark'
        window.chronicle_detail = QLabel(window)
        window._chronicle_system_window = None
        window._show_body_details = Mock()
        window._chronicle_system_clicked(dict(name=saved['system'], system_address=saved['system_address'],
                                              detail_commander_id=saved['commander_id']))
        database.chronicle_system_details.assert_called_once_with(saved['system_address'], saved['commander_id'])
        historical = window._chronicle_system_window
        self.addCleanup(historical.close)
        historical.system_overview_button.click()
        self.app.processEvents()
        overview = historical._system_overview_window
        self.assertEqual(overview.commander_id, saved['commander_id'])
        self.assertEqual(overview.system_name, saved['system'])
        self.assertEqual(overview.preview.bodies, saved['bodies'])

    def test_reopening_chronicle_overview_replaces_previous_window(self):
        window = ChronicleSystemWindow('Test', [star()], '', Mock(), settings=self.settings)
        self.addCleanup(window.close)
        window.system_overview_button.click()
        old = window._system_overview_window
        window.system_overview_button.click()
        self.assertIsNot(window._system_overview_window, old)
        self.assertFalse(old.isVisible())
        with patch('sys.excepthook') as errors:
            QApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
            self.app.processEvents()
            errors.assert_not_called()

    def test_real_systems_render_offline_in_both_themes(self):
        for system in real_systems():
            for light in (False, True):
                with self.subTest(system=system['system'], light=light):
                    dialog = self.dialog(system['bodies'], light=light,
                                         system_address=system['system_address'], commander_id=system['commander_id'])
                    self.assertEqual(sum(len(item.node.belt_members) or 1 for item in dialog.preview.items_by_key.values()),
                                     len(system['bodies']))
                    self.assertEqual(dialog.preview.bodies, system['bodies'])
                    self.assertFalse(dialog.grab().isNull())
                    dialog.close()


if __name__ == '__main__':
    unittest.main()
