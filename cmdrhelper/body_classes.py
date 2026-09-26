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
    "L (Brown dwarf) Star": "L",
    "T (Brown dwarf) Star": "T",
    "Y (Brown dwarf) Star": "Y",
    "T Tauri Star": "TTS",
    "Herbig Ae/Be Star": "AeBe",
    "K (Yellow-Orange giant) Star": "K_OrangeGiant",
    "M (Red giant) Star": "M_RedGiant",
    "M (Red super giant) Star": "M_RedSuperGiant",
    "B (Blue-White super giant) Star": "B_BlueWhiteSuperGiant",
    "A (Blue-White super giant) Star": "A_BlueWhiteSuperGiant",
    "F (White super giant) Star": "F_WhiteSuperGiant",
    "G (White-Yellow super giant) Star": "G_WhiteSuperGiant",
    "Neutron Star": "N",
    "Black Hole": "H",
    "Supermassive Black Hole": "SupermassiveBlackHole",
    "Wolf-Rayet Star": "W",
    "Wolf-Rayet N Star": "WN",
    "Wolf-Rayet NC Star": "WNC",
    "Wolf-Rayet C Star": "WC",
    "Wolf-Rayet O Star": "WO",
    "C Star": "C",
    "CS Star": "CS",
    "CN Star": "CN",
    "CJ Star": "CJ",
    "CHd Star": "CHd",
    "MS-type Star": "MS",
    "S-type Star": "S",
    **{f"White Dwarf ({kind}) Star": kind for kind in (
        "D", "DA", "DAB", "DAO", "DAZ", "DAV", "DB", "DBZ", "DBV",
        "DO", "DOV", "DQ", "DC", "DCV", "DX",
    )},
}
PLANET_ALIASES = {
    "High metal content world": "High metal content body",
    "Metal-rich body": "Metal rich body",
    "Rocky world": "Rocky body",
    "Icy body": "Icy body",
    "Rocky Ice world": "Rocky ice body",
    "Earth-like world": "Earthlike body",
    "Gas giant with water-based life": "Gas giant with water based life",
    "Gas giant with ammonia-based life": "Gas giant with ammonia based life",
    "Helium-rich gas giant": "Helium rich gas giant",
    **{f"Class {kind} gas giant": f"Sudarsky class {kind} gas giant"
       for kind in ("I", "II", "III", "IV", "V")},
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
