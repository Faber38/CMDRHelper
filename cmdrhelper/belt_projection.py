"""UI-independent visual belt projection. Original body dictionaries stay intact."""
from __future__ import annotations

from dataclasses import dataclass, field
from math import isfinite
import re


@dataclass
class BodyNode:
    key: tuple
    body: dict | None = None
    parent: tuple | None = None
    children: list = field(default_factory=list)
    belt_members: tuple = ()
    sort_key: tuple | None = None


def _number(value):
    try:
        value = float(value)
        return value if isfinite(value) and value >= 0 else None
    except (TypeError, ValueError):
        return None


def _identifier(value):
    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def body_sort_key(body):
    body_id = body.get("body_id")

    try:
        if body_id is not None:
            return (0, int(body_id), "")
    except Exception:
        pass

    return (
        1,
        999999,
        str(
            body.get("name")
            or body.get("short_name")
            or ""
        ).lower(),
    )

def is_belt_cluster(body):
    name = (
        body.get("name")
        or body.get("short_name")
        or ""
    ).lower()

    body_type = (
        body.get("body_type")
        or ""
    ).lower()

    planet_class = (
        body.get("planet_class")
        or ""
    ).lower()

    return (
        "belt cluster" in name
        or "asteroid belt" in body_type
        or "belt cluster" in body_type
        or "asteroid belt" in planet_class
        or "belt cluster" in planet_class
    )

def node_sort_key(node):
    if node.sort_key is not None:
        return node.sort_key
    body = node.body or {}
    orbit = _number(body.get('semi_major_axis', body.get('SemiMajorAxis')))
    # Distance from arrival is not an orbital radius (especially for moons).
    # Old snapshots without orbit data retain the stable journal BodyID order.
    return (orbit is None, orbit or 0, body_sort_key(body), repr(node.key))

def _group_belts(nodes, order, node_factory):
    """Collapse only visual belt leaves; retain every original cluster dictionary."""
    groups = {}
    referenced = {node.parent for node in nodes.values()}
    for node in list(nodes.values()):
        body = node.body
        if body is None or node.key in referenced or not is_belt_cluster(body):
            continue
        # The sole name-based exception: Frontier's explicit Belt Cluster suffix.
        # It identifies a belt, never a body's parent or host star.
        name = str(body.get('name') or body.get('short_name') or '')
        match = re.fullmatch(r'(?P<belt>(?:.* )?[A-Z] Belt) Cluster [1-9]\d*', name)
        label = str(body.get('belt_name') or (match['belt'] if match else ''))
        belt_id = body.get('belt_id')
        if belt_id is not None:
            identity = ('id', str(belt_id))
        elif node.parent is not None and node.parent[0] == 'Ring':
            identity = node.parent
        elif label:
            identity = ('name', label)
        else:
            continue  # No reliable belt identity: keep the original cluster.
        # Unknown parents must not accidentally unite belts from separate stars.
        scope = node.parent if node.parent is not None else node.key
        key = ('belt', scope, identity)
        groups.setdefault(key, []).append((node, label))

    for key, entries in groups.items():
        entries.sort(key=lambda entry: order(entry[0]))
        first = entries[0][0]
        label = next((label for _, label in entries if label), 'Belt')
        short = str(first.body.get('short_name') or '')
        short_match = re.fullmatch(r'(?P<belt>(?:.* )?[A-Z] Belt) Cluster [1-9]\d*', short)
        display = dict(name=label, short_name=short_match['belt'] if short_match else label,
                       body_type='Belt Cluster')
        group = node_factory(key, display, parent=first.parent,
                             belt_members=tuple(node.body for node, _ in entries),
                             sort_key=order(first))
        for node, _ in entries:
            del nodes[node.key]
        nodes[key] = group
        # A saved ring junction containing only this belt needs no extra axis.
        parent = nodes.get(group.parent)
        if (parent is not None and parent.body is None and parent.key[0] == 'Ring'
                and all(n is group or n.parent != parent.key for n in nodes.values())):
            group.parent = parent.parent
            del nodes[parent.key]


def build_body_nodes(bodies, node_factory=BodyNode):
    """Resolve the stored forest and group only its identifiable belt leaves."""
    nodes = {}
    for body in sorted(bodies, key=body_sort_key):
        body_id = _identifier(body.get('body_id'))
        key = ('body', body_id) if body_id is not None else ('name', str(body.get('name', '')))
        # BodyID is unique within this system; ignore repeated observations.
        if key not in nodes:
            nodes[key] = node_factory(key, body)

    def junction(key):
        if key not in nodes:
            nodes[key] = node_factory(key)
        return nodes[key]

    for node in list(nodes.values()):
        body = node.body
        parents = body.get('parents', body.get('Parents'))
        if isinstance(parents, list) and parents:
            child = node
            for entry in parents:
                if not isinstance(entry, dict):
                    continue
                for kind, value in entry.items():
                    parent_id = _identifier(value)
                    if parent_id is None or kind not in ('Star', 'Planet', 'Null', 'Ring'):
                        continue
                    key = ('body', parent_id) if kind in ('Star', 'Planet') else (kind, parent_id)
                    if key == child.key:
                        continue
                    parent = junction(key)
                    if child.parent is None:
                        child.parent = key
                    child = parent
        else:
            parent_id = _identifier(body.get('parent_id'))
            if parent_id is None:
                parent_id = _identifier(body.get('parent_star_id'))
            if parent_id is not None and ('body', parent_id) != node.key:
                node.parent = junction(('body', parent_id)).key

    # Corrupt historic cycles must not hide bodies or recurse forever.
    for node in list(nodes.values()):
        seen = {node.key}
        current = node
        while current.parent in nodes:
            if current.parent in seen:
                current.parent = None
                break
            seen.add(current.parent)
            current = nodes[current.parent]

    _group_belts(nodes, node_sort_key, node_factory)

    for node in nodes.values():
        if node.parent in nodes:
            nodes[node.parent].children.append(node)
    for node in nodes.values():
        node.children.sort(key=node_sort_key)
    return nodes


def project_belts(bodies):
    """Return normal-map display bodies, preserving real objects for navigation.

    Synthetic groups contain no BodyID or valuation/marker fields. Their members
    are retained separately; only their sort position and parent are projected.
    """
    groups = [node for node in build_body_nodes(bodies).values() if node.belt_members]
    membership = {id(body): node for node in groups for body in node.belt_members}
    emitted = set()
    result = []
    for body in bodies:
        node = membership.get(id(body))
        if node is None:
            result.append(body)
        elif node.key not in emitted:
            emitted.add(node.key)
            display = dict(node.body)
            display['_belt_members'] = node.belt_members
            display['_belt_sort_key'] = min(body_sort_key(member) for member in node.belt_members)
            display['parent_id'] = node.parent[1] if node.parent and node.parent[0] == 'body' else None
            result.append(display)
    return result
