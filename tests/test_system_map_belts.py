import copy
import os
import random
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from PySide6.QtCore import QPoint, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget

from cmdrhelper.belt_projection import project_belts
from cmdrhelper.ui.main_window import ChronicleSystemWindow, MainWindow
from cmdrhelper.ui.system_view import SystemMapWidget
from cmdrhelper.ui.system_overview import build_layout
from test_system_overview import star, planet
from test_system_overview_belts import belt, plio_aip


def groups(widget):
    return [b for b in widget._display_bodies if b.get('_belt_members')]


class NormalMapBeltTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def widget(self, bodies):
        widget = SystemMapWidget()
        widget.set_system('Test', bodies)
        self.addCleanup(widget.close)
        return widget

    def test_four_a_clusters_become_one_element(self):
        widget = self.widget([star()] + [belt(i) for i in range(1, 5)])
        group, = groups(widget)
        self.assertEqual(group['short_name'], 'A Belt')
        self.assertEqual(len(group['_belt_members']), 4)
        self.assertEqual(len(widget._tree_layout()[0]), 2)

    def test_b_clusters_become_one_element(self):
        group, = groups(self.widget([star(), belt(1, 'B'), belt(2, 'B')]))
        self.assertEqual(group['short_name'], 'B Belt')
        self.assertEqual(len(group['_belt_members']), 2)

    def test_single_cluster_has_no_arbitrary_body_or_values(self):
        group, = groups(self.widget([star(), belt(1, estimated_value=100)]))
        self.assertNotIn('body_id', group)
        self.assertNotIn('estimated_value', group)
        self.assertEqual(group['short_name'], 'A Belt')

    def test_distinct_belts_remain_separate(self):
        widget = self.widget([star(), belt(1), belt(2), belt(3, 'B'), belt(4, 'C')])
        self.assertEqual({b['short_name'] for b in groups(widget)}, {'A Belt', 'B Belt', 'C Belt'})

    def test_same_name_under_different_stars_remains_separate(self):
        widget = self.widget([star(), star(10, 0), belt(1), belt(2), belt(11, parent=10), belt(12, parent=10)])
        self.assertEqual({b['parent_id'] for b in groups(widget)}, {0, 10})
        self.assertEqual(sorted(len(b['_belt_members']) for b in groups(widget)), [2, 2])

    def test_real_data_and_original_body_objects_are_preserved(self):
        bodies = plio_aip()['bodies']
        before = copy.deepcopy(bodies)
        widget = self.widget(bodies)
        self.assertEqual(bodies, before)
        self.assertEqual(len(widget.bodies), 24)
        self.assertTrue(all(a is b for a, b in zip(widget.bodies, bodies)))
        rendered = [b for b in widget._display_bodies if not b.get('_belt_members')]
        members = [b for g in groups(widget) for b in g['_belt_members']]
        self.assertEqual({id(b) for b in rendered + members}, {id(b) for b in bodies})
        self.assertEqual({b['short_name']: len(b['_belt_members']) for b in groups(widget)}, {'A Belt': 5, 'B Belt': 10})

    def test_real_planet_two_moon_offsets_remain_unchanged(self):
        widget = self.widget(plio_aip()['bodies'])
        positions = {p['body'].get('body_id'): p for p in widget._tree_layout()[0].values()}
        parent = positions[19]
        # Recorded from the normal map before belt projection was introduced.
        for body_id, dx in zip((22, 23, 24, 25, 26), (-338, -169, 0, 169, 338)):
            pos = positions[body_id]
            self.assertEqual(pos['body']['parent_id'], 19)
            self.assertEqual((pos['x'] - parent['x'], pos['y'] - parent['y']), (dx, 272))

    def test_no_belt_preserves_objects_hierarchy_and_submoons(self):
        bodies = [star(), planet(1), planet(2, 1), planet(3, 2)]
        self.assertEqual(project_belts(bodies), bodies)
        widget = self.widget(bodies)
        positions = widget._tree_layout()[0]
        for level, body in enumerate(bodies):
            self.assertIs(positions[id(body)]['body'], body)
            self.assertEqual(positions[id(body)]['level'], level)

    def test_order_is_stable_when_input_is_shuffled(self):
        bodies = plio_aip()['bodies']
        def layout(source):
            widget = self.widget(source)
            return {p['body']['short_name']: (p['x'], p['y']) for p in widget._tree_layout()[0].values()}
        expected = layout(bodies)
        random.Random(31).shuffle(bodies)
        self.assertEqual(layout(bodies), expected)

    def test_normal_body_clicks_and_belt_artwork_dark_light(self):
        for light in (False, True):
            with self.subTest(light=light):
                body = planet(3)
                widget = self.widget([star(), belt(1), belt(2), body])
                widget.set_light_mode(light)
                widget.resize(widget.sizeHint())
                widget.show()
                self.app.processEvents()
                callback = Mock()
                widget.bodyClicked.connect(callback)
                group, = groups(widget)
                self.assertIsNotNone(widget._body_pixmap(group))
                self.assertTrue(all(b is not group for _, b in widget._body_rects))
                for target in (group, body):
                    x, y = widget.body_center(target)
                    QTest.mouseClick(widget, Qt.LeftButton, pos=QPoint(int(x), int(y)))
                    if target is group:
                        callback.assert_not_called()
                callback.assert_called_once_with(body)
                self.assertFalse(widget.grab().isNull())
                widget.close()

    def test_overview_and_normal_map_share_identical_membership(self):
        bodies = plio_aip()['bodies']
        expected = {n.body['short_name']: n.belt_members for n in build_layout(bodies).values() if n.belt_members}
        actual = {b['short_name']: b['_belt_members'] for b in groups(self.widget(bodies))}
        self.assertEqual(actual, expected)

    def test_explorer_and_chronicle_use_same_normal_renderer(self):
        system = plio_aip()
        window = MainWindow.__new__(MainWindow)
        QMainWindow.__init__(window)
        # Construct the actual Explorer page, isolating its unrelated favorites UI.
        window.ui_theme = 'dark'
        window.state = SimpleNamespace(settings=Mock(value=Mock(return_value=None)))
        window._favorite_navigator = Mock()
        window._quick_favorite_hotkey = None
        with patch('cmdrhelper.ui.favorites_view.FavoritesView', return_value=QWidget()):
            page = window._explorer()
        self.addCleanup(page.close)
        window.system_map.set_system(system['system'], system['bodies'])
        chronicle = ChronicleSystemWindow(system['system'], system['bodies'], '', Mock())
        self.addCleanup(chronicle.close)
        self.assertIs(type(window.system_map), type(chronicle.system_map))
        self.assertEqual(window.system_map._display_bodies, chronicle.system_map._display_bodies)
        self.assertEqual(len(chronicle.system_map.bodies), 24)
        window._favorites_window.close()
        window.deleteLater()

    def test_explicit_ring_parent_uses_shared_grouping(self):
        bodies = [star(), belt(1, Parents=[{'Ring': 70}, {'Star': 0}]),
                  belt(2, 'B', Parents=[{'Ring': 70}, {'Star': 0}])]
        group, = groups(self.widget(bodies))
        self.assertEqual(group['parent_id'], 0)
        self.assertEqual(len(group['_belt_members']), 2)
