"""Canonical journal classes at the external-data boundary.

Keep aliases explicit: unknown future classes remain intact rather than being
guessed from a prefix (which could confuse dwarfs, giants and supergiants).
"""

STAR_ALIASES = {
    "O (Blue-White) Star": "O",
    "B (Blue-White) Star": "B",
    "A (Blue-White) Star": "A",
    "F (White) Star": "F",
    "G (White-Yellow) Star": "G",
    "K (Yellow-Orange) Star": "K",
    "M (Red dwarf) Star": "M",
}
PLANET_ALIASES = {
    "High metal content world": "High metal content body",
    "Metal-rich body": "Metal rich body",
    "Rocky world": "Rocky body",
    "Icy body": "Icy body",
    "Rocky Ice world": "Rocky ice body",
}


def _canonical(value, aliases):
    value = str(value or "").strip()
    lookup = {key.casefold(): result for key, result in aliases.items()}
    lookup.update({result.casefold(): result for result in aliases.values()})
    return lookup.get(value.casefold(), value)


def canonical_body_classes(body):
    """Return a copy; also supports already-normalized, older EDSM caches."""
    return {
        **body,
        "star_type": _canonical(body.get("star_type"), STAR_ALIASES),
        "planet_class": _canonical(body.get("planet_class"), PLANET_ALIASES),
    }
