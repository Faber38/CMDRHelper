"""Shared, renderer-independent positions and orthogonal orbital connectors."""
from dataclasses import dataclass
from math import ceil

from cmdrhelper.belt_projection import BodyNode, build_body_nodes, node_sort_key


@dataclass
class LayoutNode(BodyNode):
    x: float = 0
    y: float = 0
    layout_width: float = 0
    layout_height: float = 0
    subtree_width: float = 0
    subtree_height: float = 0
    satellite_columns: int = 0


def build_positions(bodies, factory=LayoutNode, *, width=145, height=lambda n: 230,
                    gap=24, image_center=44, image_radius=lambda n: 30,
                    extra_height=lambda n: 0, reserved_width=lambda n: 0):
    # Parent metadata is only adapted for the existing graph builder. Restore
    # original dictionaries afterward, retaining identity for detail/navigation.
    originals = {}
    adapted = []
    for body in bodies:
        copy = dict(body)
        if isinstance(body.get('parent_path'), list):
            copy['Parents'] = body['parent_path']
            copy.pop('parents', None)
        adapted.append(copy)
        originals[id(copy)] = body
    nodes = build_body_nodes(adapted, factory)
    for node in nodes.values():
        if node.belt_members:
            node.belt_members = tuple(originals[id(b)] for b in node.belt_members)
            node.body['_belt_members'] = node.belt_members
            node.body['_belt_sort_key'] = node.sort_key[2]
            node.body['parent_id'] = node.parent[1] if node.parent and node.parent[0] == 'body' else None
        elif node.body is not None:
            node.body = originals[id(node.body)]
        node.layout_width = width if node.body is not None else 0
        node.layout_height = height(node) + extra_height(node) if node.body is not None else 0
        node.reserved_width = reserved_width(node) if node.body is not None else 0
        node.image_center_y = image_center
        node.image_radius = image_radius(node) if node.body is not None else 0

    def order(node):
        # Junction IDs are orbital identities too, not missing-body sentinels.
        if node.body is None and isinstance(node.key[1], int):
            return (True, 0, (0, node.key[1], ''), repr(node.key))
        return node_sort_key(node)

    for node in nodes.values():
        node.children.sort(key=order)
    # Cap corrupt/extreme ancestry before recursive geometry. No body is lost:
    # excessively deep branches become independent remainder groups.
    for node in nodes.values():
        parent, depth = node.parent, 0
        while parent in nodes:
            depth += 1
            if depth > 128:
                nodes[node.parent].children.remove(node)
                node.parent = None
                break
            parent = nodes[parent].parent
    roots = sorted((n for n in nodes.values() if n.parent is None), key=order)

    def shift(group, x, y):
        for item in group:
            item.x += x
            item.y += y

    def place(node, axis=False):
        group = [node]
        w, h = max(node.layout_width, node.reserved_width), node.layout_height
        if node.body is None or axis:
            cursor = w + gap if node.body is not None else 0
            child_centers = []
            for child in node.children:
                child_axis = node.parent is None and node.body is None and bool(
                    child.body and (child.body.get('star_type') or child.body.get('body_type') == 'Star'))
                members, cw, ch = place(child, child_axis)
                shift(members, cursor, 0)
                child_centers.append(child.x + child.layout_width / 2)
                group.extend(members)
                cursor += cw + gap
                h = max(h, ch)
            w = max(w, cursor - gap)
            if node.body is None:
                node.x = ((child_centers[0] + child_centers[-1]) / 2 if child_centers else 0)
                node.y = -gap / 2
        else:
            # Balanced columns: six -> 3+3, eight -> 4+4, twelve -> 4+4+4.
            count = len(node.children)
            columns = ceil(count / 4) if count else 0
            rows = ceil(count / columns) if columns else 0
            node.satellite_columns = columns
            cursor = gap
            for start in range(0, count, rows or 1):
                cw = 0
                # Every column starts at the parent, not after the previous one.
                cy = node.layout_height + gap
                for child in node.children[start:start + rows]:
                    members, sw, sh = place(child)
                    shift(members, cursor, cy)
                    group.extend(members)
                    cw = max(cw, sw)
                    cy += sh + gap
                w = max(w, cursor + cw)
                h = max(h, cy - gap)
                cursor += cw + gap
        node.subtree_width, node.subtree_height = max(w, gap), h
        return group, node.subtree_width, h

    bottom = gap * 3
    for root in roots:
        axis = bool(root.body and (root.body.get('star_type') or root.body.get('body_type') == 'Star'))
        group, w, h = place(root, axis)
        shift(group, gap, bottom)
        bottom += h + gap * 3
    return nodes


def connector_points(parent, child, gap=24):
    """Routes stay in reserved gutters, outside body/label rectangles."""
    px = parent.x + parent.layout_width / 2
    cx = child.x + child.layout_width / 2
    child_top = child.y + child.image_center_y - child.image_radius - 4 if child.body else child.y
    if parent.body is None:
        return [(px, parent.y), (cx, parent.y), (cx, child_top)]
    if child.y <= parent.y:
        parent_top = parent.y + parent.image_center_y - parent.image_radius - 4
        bus = min(parent.y, child.y, parent_top, child_top) - gap
        return [(px, parent_top), (px, bus), (cx, bus), (cx, child_top)]
    branch = parent.y + parent.layout_height + gap / 2
    gutter = child.x - gap / 2
    return [(px, parent.y + parent.layout_height), (px, branch),
            (gutter, branch), (gutter, child.y + child.image_center_y),
            (cx - child.image_radius - 4, child.y + child.image_center_y)]
