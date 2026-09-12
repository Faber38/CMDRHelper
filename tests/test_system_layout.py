"""Shared-layout regressions using the real, repaired Plio parent paths."""
import copy
import json
from pathlib import Path
import random
import unittest

from PySide6.QtCore import QRectF, Qt
from PySide6.QtWidgets import QApplication
from cmdrhelper.body_parents import parent_metadata
from cmdrhelper.ui.system_layout import build_positions, connector_points
from cmdrhelper.ui.system_overview import build_layout, SystemOverviewView
from cmdrhelper.ui.system_view import SystemMapWidget


def plio():
    events = json.loads((Path(__file__).parent / 'fixtures/plio_parent_scans.json').read_text())
    scans = {e['BodyID']: e for e in events if e['event'] == 'Scan'}
    return [dict(body_id=e['BodyID'], name=e['BodyName'],
                 short_name=e['BodyName'].removeprefix('Plio Aihm UC-V d2-159 ').strip(),
                 body_type='Star' if e.get('StarType') else 'Planet',
                 star_type=e.get('StarType', ''), planet_class=e.get('PlanetClass', ''),
                 **parent_metadata(e.get('Parents'), 'Journal'))
            for e in scans.values()]


class SharedLayoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_plio_structure_and_balanced_satellites(self):
        nodes=build_layout(plio())
        for parent, children in [(15,[17]),(20,[23]),(25,[28,29]),
                                 (31,list(range(34,40))),(41,[*range(43,50),51])]:
            p=nodes['body',parent]
            for body_id in children:
                child=nodes['body',body_id]
                self.assertEqual(child.parent,p.key)
                self.assertGreater(child.y,p.y)
            counts={x:sum(nodes['body',i].x==x for i in children)
                    for x in {nodes['body',i].x for i in children}}
            self.assertEqual(sorted(counts.values()), {15:[1],20:[1],25:[2],31:[3,3],41:[4,4]}[parent])
        self.assertEqual(nodes['body',15].y,nodes['body',0].y)
        for bary, children in [(1,[2,3]),(19,[20,25]),(30,[31,40])]:
            self.assertIsNone(nodes['Null',bary].body)
            self.assertEqual({n.key for n in nodes['Null',bary].children},{('body',i) for i in children})
        belts=[n for n in nodes.values() if n.belt_members]
        self.assertEqual(len(belts),1)
        self.assertEqual(len(belts[0].belt_members),9)

    def test_renderers_share_positions_with_native_metrics_and_keep_identity(self):
        bodies=plio();before=copy.deepcopy(bodies)
        widget=SystemMapWidget();self.addCleanup(widget.close)
        widget.set_system('Plio Aihm UC-V d2-159',bodies)
        expected=build_positions(bodies,width=widget.BODY_W,height=lambda n:widget.BODY_H,
                                 gap=widget.X_GAP,image_radius=lambda n:widget._visual_body_size(n.body)/2)
        self.assertEqual({k:(n.x,n.y,n.parent) for k,n in widget._layout_nodes.items()},
                         {k:(n.x,n.y,n.parent) for k,n in expected.items()})
        for b in bodies:
            if b['body_id'] not in range(6,15):
                self.assertIs(widget._layout_nodes['body',b['body_id']].body,b)
        self.assertEqual(bodies,before)
        self.assertLess(widget.minimumWidth(),3939)

    def test_no_overlap_and_order_independent(self):
        bodies=plio()
        for build in (build_positions,build_layout):
            nodes=build(bodies)
            rects=[(n.key,QRectF(n.x,n.y,n.layout_width,n.layout_height))
                   for n in nodes.values() if n.body is not None]
            for i,(key,rect) in enumerate(rects):
                for other,other_rect in rects[i+1:]:
                    self.assertFalse(rect.intersects(other_rect),(key,other))
            random.Random(7).shuffle(bodies)
            self.assertEqual({k:(n.x,n.y,n.parent) for k,n in nodes.items()},
                             {k:(n.x,n.y,n.parent) for k,n in build(bodies).items()})

    def test_lines_do_not_cross_images(self):
        for build in (build_positions,build_layout):
            nodes=build(plio())
            images=[QRectF(n.x+n.layout_width/2-n.image_radius,n.y+n.image_center_y-n.image_radius,
                          n.image_radius*2,n.image_radius*2)
                    for n in nodes.values() if n.body is not None]
            for n in nodes.values():
                if n.parent not in nodes:continue
                points=connector_points(nodes[n.parent],n,26 if build is build_layout else 24)
                for a,b in zip(points,points[1:]):
                    for rect in images:
                        if a[0]==b[0]:
                            crosses=(rect.left()<a[0]<rect.right() and max(a[1],b[1])>rect.top() and min(a[1],b[1])<rect.bottom())
                        else:
                            crosses=(rect.top()<a[1]<rect.bottom() and max(a[0],b[0])>rect.left() and min(a[0],b[0])<rect.right())
                        self.assertFalse(crosses,(n.key,a,b,rect))

    def test_bad_and_deep_hierarchy_keeps_bodies(self):
        for bodies in ([dict(body_id=1,parent_id=2),dict(body_id=2,parent_id=1)],
                       [dict(body_id=1,parent_id='invalid'),dict(body_id=2,parent_id=77)],
                       [dict(body_id=i,parent_id=i-1 if i else None) for i in range(350)]):
            nodes=build_positions(bodies)
            self.assertEqual(len([n for n in nodes.values() if n.body is not None]),len(bodies))

    def test_plio_dark_light_interaction_and_view_controls(self):
        for light in (False,True):
            view=SystemOverviewView('Plio Aihm UC-V d2-159',plio(),light=light)
            self.addCleanup(view.close)
            view.resize(800,600);view.show();self.app.processEvents()
            self.assertGreater(view.horizontalScrollBar().maximum(),0)
            self.assertGreater(view.verticalScrollBar().maximum(),0)
            self.assertEqual(view.items_by_key['body',17].cursor().shape(),Qt.PointingHandCursor)
            self.assertNotIn(('Null',19),view.items_by_key)
            view.scale(1.2,1.2);view.reset_zoom()
            self.assertEqual(view.transform().m11(),1)
            self.assertFalse(view.grab().isNull())
