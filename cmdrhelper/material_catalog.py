"""Offline Engineering definitions and commander-specific inventory projection.

Provenance, exclusions and capacity exceptions: docs/material-catalog.md.
No UI, database, network access or mutable commander cache lives here.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import re
from types import MappingProxyType
from typing import TYPE_CHECKING

from ._material_catalog_data import MATERIALS, LEGACY_I18N_KEYS

if TYPE_CHECKING:
    from .material_inventory import MaterialInventory


@dataclass(frozen=True)
class MaterialDefinition:
    symbol: str
    english_name: str
    category: str
    grade: int | None
    maximum: int | None
    group: str
    subgroup: str | None
    i18n_key: str


def _validate(materials):
    if len(materials) != 146 or len({m.symbol for m in materials}) != 146:
        raise ValueError("Engineering catalog must contain 146 unique symbols")
    if Counter(m.category for m in materials) != {"Raw": 28, "Manufactured": 71, "Encoded": 47}:
        raise ValueError("Invalid Engineering categories")
    if Counter(m.group for m in materials) != {"standard": 108, "guardian": 13, "thargoid": 25}:
        raise ValueError("Invalid Engineering groups")
    for material in materials:
        if not re.fullmatch(r"[a-z0-9_]+", material.symbol) or not material.english_name.strip():
            raise ValueError("Invalid material identity/name")
        if material.i18n_key != "body_detail.material." + material.symbol:
            raise ValueError("Invalid material translation key")
        if material.symbol == "tg_shipsystemsdata":
            if material.grade is not None or material.maximum is not None:
                raise ValueError("Unresolved ship systems data grade/capacity")
        elif (type(material.grade) is not int or material.grade not in range(1, 6)
              or type(material.maximum) is not int or material.maximum <= 0):
            raise ValueError("Invalid material grade/capacity")
    if any(m.symbol == "tg_structuraldata02" for m in materials):
        raise ValueError("Unconfirmed material is not part of the regular catalog")


_MATERIALS = tuple(MaterialDefinition(*row) for row in MATERIALS)
_validate(_MATERIALS)
_BY_SYMBOL = MappingProxyType({m.symbol: m for m in _MATERIALS})
# Missing translations are intentional only for these new catalog keys.
# The original 24 BodyDetail names remain mandatory in all twelve languages.
ENGLISH_FALLBACK_KEYS = frozenset(m.i18n_key for m in _MATERIALS) - LEGACY_I18N_KEYS


def all_materials() -> tuple[MaterialDefinition, ...]:
    return _MATERIALS


def get_material(symbol: str) -> MaterialDefinition | None:
    """Canonical Frontier identity only; tolerate journal casing/name wrappers."""
    if not isinstance(symbol, str):
        return None
    symbol = symbol.strip().casefold()
    if symbol.startswith("$") and symbol.endswith("_name;"):
        symbol = symbol[1:-6]
    return _BY_SYMBOL.get(symbol)


def materials_by_category(category: str) -> tuple[MaterialDefinition, ...]:
    """Categories are the canonical Raw/Manufactured/Encoded identifiers."""
    if category not in ("Raw", "Manufactured", "Encoded"):
        raise ValueError("Unknown Engineering category")
    return tuple(m for m in _MATERIALS if m.category == category)


def localized_name(symbol: str, language: str | None = None) -> str:
    from .i18n import get_language, tr_for_language

    material = get_material(symbol)
    if material is None:
        raise KeyError(symbol)
    return tr_for_language(language if language is not None else get_language(), material.i18n_key)


@dataclass(frozen=True)
class CatalogStock:
    material: MaterialDefinition
    commander_id: int
    fid: str
    snapshot_timestamp: str | None
    count: int | None
    known: bool

    @property
    def percent(self) -> float | None:
        if not self.known or self.count is None or self.material.maximum is None:
            return None
        return self.count * 100 / self.material.maximum

    @property
    def fill_state(self) -> str | None:
        """Exclusive future filter bucket; middle/unknown/over-capacity have none.

        Unknown capacity excludes even `empty`. Never clamp recorded quantities.
        Integer comparisons keep the 20/80/100 percent boundaries exact.
        """
        if self.percent is None:
            return None
        count, maximum = self.count, self.material.maximum
        if count == 0:
            return "empty"
        if 0 < count * 100 <= maximum * 20:
            return "low"
        if maximum * 80 <= count * 100 < maximum * 100:
            return "near_full"
        if count == maximum:
            return "full"
        return None


def merge_inventory(inventory: MaterialInventory) -> tuple[CatalogStock, ...]:
    """Project all 146 definitions without changing Phase 1's observed identities.

    Only a reliable complete snapshot establishes zero for absent catalog entries.
    A category conflict is unknown rather than reinterpreting a journal quantity.
    """
    rows = []
    for material in _MATERIALS:
        stock = inventory.material(material.symbol)
        known = inventory.known and stock.category in (None, material.category)
        count = (stock.count if stock.known else 0) if known else None
        rows.append(CatalogStock(material, inventory.commander_id, inventory.fid,
                                 inventory.snapshot_timestamp, count, known))
    return tuple(rows)
