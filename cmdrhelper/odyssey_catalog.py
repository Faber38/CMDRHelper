"""Offline Odyssey identities, names, capacities and lossless O1 projection.

Domain-owned name resources use the current CMDRHelper language when omitted.
No Qt, database, network or mutation of the existing i18n catalogs is involved.
See docs/odyssey-catalog.md for source revisions and availability limitations.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from types import MappingProxyType

from ._odyssey_catalog_data import MATERIALS, TRANSLATIONS
from .odyssey_inventory import CATEGORIES, InventoryRow, OdysseyInventory, StackKey, canonical_name

ENGINEERING_FLAGS = frozenset({"suit_upgrade", "weapon_upgrade", "suit_modification",
                               "weapon_modification", "engineer_unlock"})
SPECIAL_GROUPS = frozenset({"standard", "powerplay", "thargoid_spire", "operations", "unica"})
FILTERS = ("all", "mission", "engineering", "backpack", "locker", "empty")


@dataclass(frozen=True)
class OdysseyDefinition:
    symbol: str
    name_en: str
    category: str
    subgroup: str | None
    engineering_flags: frozenset[str]
    special_group: str
    usage_tags: frozenset[str]
    availability_status: str
    i18n_key: str

    @property
    def engineering_relevant(self):
        return bool(self.engineering_flags)


def _validate(entries):
    if len(entries) != 223 or len({m.symbol for m in entries}) != 223:
        raise ValueError("Odyssey catalog requires 223 unique identities")
    if Counter(m.category for m in entries) != dict(Items=61, Components=33, Data=123, Consumables=6):
        raise ValueError("Invalid Odyssey category distribution")
    if Counter(m.special_group for m in entries) != dict(
            standard=196, powerplay=22, thargoid_spire=2, operations=2, unica=1):
        raise ValueError("Invalid Odyssey special groups")
    if Counter(m.subgroup for m in entries if m.category == "Components") != dict(
            Chemicals=10, Circuits=12, Tech=11):
        raise ValueError("Invalid component subgroups")
    if sum(m.engineering_relevant for m in entries) != 98:
        raise ValueError("Invalid Engineering relevance count")
    excluded = {"powermegashipdata", "unknown", "none", "geographicaldata"}
    for m in entries:
        if m.symbol != canonical_name(m.symbol) or m.symbol in excluded or not m.name_en.strip():
            raise ValueError("Invalid Odyssey identity")
        if (m.category != "Components" and m.subgroup is not None
                or not m.engineering_flags <= ENGINEERING_FLAGS
                or not m.usage_tags <= {"upload"}
                or m.availability_status not in {"confirmed_identity", "context_dependent"}
                or m.i18n_key != "odyssey.material." + m.symbol):
            raise ValueError("Invalid Odyssey metadata")


_ENTRIES = tuple(OdysseyDefinition(**{**m, "engineering_flags": frozenset(m["engineering_flags"]),
                                     "usage_tags": frozenset(m["usage_tags"])}) for m in MATERIALS)
_validate(_ENTRIES)
_BY_SYMBOL = MappingProxyType({m.symbol: m for m in _ENTRIES})
_NAMES = MappingProxyType({lang: MappingProxyType(dict(names)) for lang, names in TRANSLATIONS.items()})
for _lang, _count in {"de": 221, "es": 223, "it": 217, "fr": 205}.items():
    if (len(_NAMES[_lang]) != _count or not set(_NAMES[_lang]) <= _BY_SYMBOL.keys()
            or not all(value.strip() for value in _NAMES[_lang].values())):
        raise ValueError("Invalid Odyssey name coverage")


def all_materials() -> tuple[OdysseyDefinition, ...]:
    return _ENTRIES


def get_material(symbol) -> OdysseyDefinition | None:
    try:
        return _BY_SYMBOL.get(canonical_name(symbol))
    except ValueError:
        return None


def materials_by_category(category: str) -> tuple[OdysseyDefinition, ...]:
    if category not in CATEGORIES:
        raise ValueError("Unknown Odyssey category")
    return tuple(m for m in _ENTRIES if m.category == category)


def localized_name(symbol: str, language: str | None = None) -> str:
    material = get_material(symbol)
    if material is None:
        raise KeyError(symbol)
    if language is None:
        from .i18n import get_language
        language = get_language()
    return _NAMES.get(str(language).strip().lower(), {}).get(material.symbol, material.name_en)


def translation_coverage() -> dict[str, int]:
    """Actual source names; English fallback is not counted as a translation."""
    return {lang: 223 if lang == "en" else len(_NAMES.get(lang, {})) for lang in
            ("en", "de", "es", "it", "fr", "no", "sv", "fi", "pl", "nl", "tr", "el")}


_LOCKER_CAPACITY = MappingProxyType({"Items": 1000, "Components": 1000, "Data": 1000})
_BACKPACK_CAPACITY = MappingProxyType({
    "maverick": (40, 60, 20), "artemis": (20, 40, 10),
    "dominator": (10, 20, 10), "flight_suit": (5, 10, 10),
})


def capacity(container: str, category: str, *, suit: str | None = None,
             extra_backpack: bool | None = False) -> int | None:
    """Container CATEGORY limit, never a per-item or Locker+Backpack maximum.

    Unknown suit/modifier or any Consumables capacity is None. The modifier is
    an explicit caller-supplied fact, not inferred from a suit or grade. Suit
    identifiers are canonical names below, not UI labels.
    """
    if container not in ("ShipLocker", "Backpack") or category not in CATEGORIES:
        raise ValueError("Unknown Odyssey container/category")
    if category == "Consumables":
        return None
    if container == "ShipLocker":
        return _LOCKER_CAPACITY[category]
    if suit not in _BACKPACK_CAPACITY or type(extra_backpack) is not bool:
        return None
    base = _BACKPACK_CAPACITY[suit][("Items", "Components", "Data").index(category)]
    return base * (2 if extra_backpack else 1)


@dataclass(frozen=True)
class OdysseyCatalogStock:
    commander_id: int
    fid: str
    reconstructed_at: str | None
    locker_snapshot: str | None
    backpack_snapshot: str | None
    definition: OdysseyDefinition | None
    stock: InventoryRow
    name: str
    observed: bool

    @property
    def key(self):
        return self.stock.key

    @property
    def engineering_relevant(self):
        return self.definition is not None and self.definition.engineering_relevant

    def matches_filter(self, selected: str) -> bool:
        if selected == "all":
            return True
        if selected == "mission":
            return self.observed and self.key.mission_id is not None
        if selected == "engineering":
            return self.engineering_relevant
        if selected == "backpack":
            return self.stock.backpack is not None and self.stock.backpack > 0
        if selected == "locker":
            return self.stock.locker is not None and self.stock.locker > 0
        if selected == "empty":
            return self.stock.known and self.stock.total == 0
        raise ValueError("Unknown Odyssey filter")


def merge_inventory(inventory: OdysseyInventory, language: str | None = None,
                    *, include_absent: bool = True) -> tuple[OdysseyCatalogStock, ...]:
    """Enrich O1 rows without aggregating or changing stack ownership/mission IDs.

    One catalog placeholder is supplied for each entirely absent identity, never
    an invented normal stack alongside an existing mission stack. Placeholder
    counts follow O1's known/unknown states. Unknown future symbols survive.
    Thus 223 identities need not mean exactly 223 rows when stacks are split.
    """
    rows = list(inventory.rows)
    present = {row.key.name for row in rows}
    observed_count = len(rows)
    if include_absent:
        for m in _ENTRIES:
            if m.symbol in present:
                continue
            a = inventory.count(m.symbol, "ShipLocker", m.category)
            b = inventory.count(m.symbol, "Backpack", m.category)
            rows.append(InventoryRow(StackKey(m.category, m.symbol), "", a, b,
                                     a + b if inventory.known else None,
                                     inventory.known, "unknown"))
    result = []
    for index, row in enumerate(rows):
        m = get_material(row.key.name)
        # A source category conflict cannot silently be reclassified as catalog
        # stock. Keep the original O1 row as an unresolved identity instead.
        if m is not None and m.category != row.key.category:
            m = None
        result.append(OdysseyCatalogStock(
            inventory.commander_id, inventory.fid, inventory.reconstructed_at,
            inventory.containers["ShipLocker"].snapshot_timestamp,
            inventory.containers["Backpack"].snapshot_timestamp, m, row,
            localized_name(m.symbol, language) if m else row.display_name or row.key.name,
            index < observed_count))
    return tuple(result)
