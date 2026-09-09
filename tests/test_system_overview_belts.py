import copy
import json
from pathlib import Path
import random
import unittest
from unittest.mock import Mock

from PySide6.QtCore import Qt

from cmdrhelper.ui.main_window import ChronicleSystemWindow
from cmdrhelper.ui.system_overview import build_layout
import test_system_overview as overview
from test_system_overview import star, planet


def belt(i, letter='A', parent=0, **extra):
    return dict(body_id=i, name=f'Test {letter} Belt Cluster {i}',
                short_name=f'{letter} Belt Cluster {i}', body_type='Belt Cluster', parent_id=parent, **extra)


def groups(nodes):
    return [n for n in nodes.values() if n.belt_members]


def plio_aip():
    return json.loads((Path(__file__).parent / 'fixtures/system_overview_plio_aip.json').read_text())


class BeltLayoutTests(unittest.TestCase):
    assert_no_overlap = overview.OverviewLayoutTests.assert_no_overlap

    def test_four_clusters_become_one_belt_without_changing_source(self):
        bodies = [star()] + [belt(i) for i in range(1, 5)]
        original = copy.deepcopy(bodies)
        nodes = build_layout(bodies)
        group, = groups(nodes)
        self.assertEqual(group.body['short_name'], 'A Belt')
        self.assertNotIn('body_id', group.body)
        self.assertEqual(group.belt_members, tuple(bodies[1:]))
        self.assertEqual(bodies, original)
        self.assertEqual(len(nodes), 2)
        self.assertEqual(group.y, nodes['body', 0].y)

    def test_single_cluster_is_still_a_non_body_belt_group(self):
        group, = groups(build_layout([star(), belt(1)]))
        self.assertEqual(len(group.belt_members), 1)
        self.assertEqual(group.body['short_name'], 'A Belt')

    def test_distinct_belts_keep_separate_horizontal_positions(self):
        nodes = build_layout([star(), belt(1), belt(2), planet(3), belt(4, 'B'), belt(5, 'C'), planet(6)])
        belts = {n.body['short_name']: n for n in groups(nodes)}
        self.assertEqual(set(belts), {'A Belt', 'B Belt', 'C Belt'})
        expected = [nodes['body', 0], belts['A Belt'], nodes['body', 3], belts['B Belt'], belts['C Belt'], nodes['body', 6]]
        self.assertEqual([n.x for n in expected], sorted(n.x for n in expected))
        self.assertEqual({n.y for n in expected}, {0})
        self.assert_no_overlap(nodes)

    def test_equal_belt_names_under_different_stars_stay_separate(self):
        nodes = build_layout([star(), star(10, 0), belt(1), belt(2), belt(11, parent=10), belt(12, parent=10)])
        self.assertEqual({n.parent for n in groups(nodes)}, {('body', 0), ('body', 10)})
        self.assertEqual([len(n.belt_members) for n in groups(nodes)], [2, 2])
        for n in groups(nodes):
            self.assertEqual(n.y, nodes[n.parent].y)
        self.assert_no_overlap(nodes)

    def test_unknown_parents_do_not_merge_identical_names(self):
        nodes = build_layout([belt(1, parent=None), belt(2, parent=None)])
        self.assertEqual(len(groups(nodes)), 2)

    def test_known_parent_groups_old_and_new_host_star_metadata(self):
        nodes = build_layout([star(), belt(1, parent_star_id=None), belt(2, parent_star_id=0)])
        group, = groups(nodes)
        self.assertEqual(group.parent, ('body', 0))
        self.assertEqual(len(group.belt_members), 2)

    def test_explicit_belt_ids_take_priority_over_names(self):
        nodes = build_layout([star(), belt(1, belt_id=70), belt(2, belt_id=80), belt(3, 'B', belt_id=70)])
        self.assertEqual(sorted(len(n.belt_members) for n in groups(nodes)), [1, 2])

    def test_ring_parent_data_identifies_one_belt_on_star_axis(self):
        first = belt(1, Parents=[{'Ring': 70}, {'Star': 0}])
        second = belt(2, 'B', Parents=[{'Ring': 70}, {'Star': 0}])
        nodes = build_layout([star(), first, second])
        group, = groups(nodes)
        self.assertEqual(len(group.belt_members), 2)
        self.assertEqual(group.parent, ('body', 0))
        self.assertEqual(group.y, nodes['body', 0].y)
        self.assert_no_overlap(nodes)

    def test_group_uses_minimum_reliable_orbit_and_stable_sort_order(self):
        bodies = [star(), belt(1, semi_major_axis=40), planet(2, semi_major_axis=20),
                  belt(3, semi_major_axis=10), belt(4, 'B', semi_major_axis=30)]
        expected = build_layout(bodies)
        a = next(n for n in groups(expected) if n.body['short_name'] == 'A Belt')
        self.assertLess(a.x, expected['body', 2].x)
        random.Random(19).shuffle(bodies)
        actual = build_layout(bodies)
        self.assertEqual({k: (n.x, n.y, n.parent, n.belt_members) for k, n in expected.items()},
                         {k: (n.x, n.y, n.parent, n.belt_members) for k, n in actual.items()})

    def test_no_generic_body_name_parent_inference(self):
        nodes = build_layout([star(), planet(1, None), dict(body_id=2, name='Unknown Belt Cluster 1', parent_id=0)])
        self.assertIsNone(nodes['body', 1].parent)
        self.assertFalse(groups(nodes))
        self.assertIn(('body', 2), nodes)

    def test_real_plio_aip_keeps_planet_two_moon_layout_exactly(self):
        system = plio_aip()
        nodes = build_layout(system['bodies'])
        self.assertEqual({n.body['short_name']: len(n.belt_members) for n in groups(nodes)}, {'A Belt': 5, 'B Belt': 10})
        self.assertEqual(len([n for n in nodes.values() if n.body is not None]), 11)
        parent = nodes['body', 19]
        for body_id, expected in system['planet_2_layout_before_belt_grouping'].items():
            node = nodes['body', int(body_id)]
            self.assertEqual(node.parent, ('body', expected['parent']))
            self.assertAlmostEqual(node.x - parent.x, expected['x'])
            self.assertAlmostEqual(node.y - parent.y, expected['y'])
            self.assertEqual(node.diameter, expected['diameter'])
        self.assert_no_overlap(nodes)


class BeltViewTests(unittest.TestCase):
    setUpClass = classmethod(overview.OverviewViewTests.setUpClass.__func__)
    setUp = overview.OverviewViewTests.setUp
    dialog = overview.OverviewViewTests.dialog
    click_body = overview.OverviewViewTests.click_body

    def test_group_not_clickable_normal_planet_remains_clickable_dark_light(self):
        for light in (False, True):
            callback = Mock()
            dialog = self.dialog([star(), belt(1), belt(2), planet(3)], light=light, on_body_clicked=callback)
            view = dialog.preview
            group_item, = [i for i in view.items_by_key.values() if i.node.belt_members]
            self.assertEqual(group_item.acceptedMouseButtons(), Qt.MouseButton.NoButton)
            self.click_body(view, group_item.node.key)
            self.assertFalse(group_item.isSelected())
            callback.assert_not_called()
            self.click_body(view, ('body', 3))
            callback.assert_called_once_with(view.nodes['body', 3].body)
            self.assertEqual(len(view.bodies), 4)
            self.assertEqual(group_item.name, 'A Belt')
            self.assertIsNotNone(group_item.pixmap)
            self.assertFalse(view.grab().isNull())
            dialog.close()

    def test_explorer_and_chronicle_share_identical_belt_projection(self):
        system = plio_aip()
        explorer = self.dialog(system['bodies'])
        chronicle = ChronicleSystemWindow(system['system'], system['bodies'], '', Mock(), settings=self.settings)
        self.addCleanup(chronicle.close)
        chronicle.system_overview_button.click()
        self.app.processEvents()
        historic = chronicle._system_overview_window
        self.assertIs(type(explorer.preview), type(historic.preview))
        project = lambda view: {k: (n.x, n.y, n.parent, n.belt_members) for k, n in view.nodes.items()}
        self.assertEqual(project(explorer.preview), project(historic.preview))
        self.assertEqual(chronicle.system_map.bodies, system['bodies'])
        self.assertEqual(len(explorer.preview.bodies), 24)
