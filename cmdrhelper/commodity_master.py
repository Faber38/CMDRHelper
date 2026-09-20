"""Offline Commodity identities; no existing inventory consumer uses this module.

Symbols retain exact upstream spelling. Lookups accept casing and the complete
Frontier $..._name; wrapper only. See docs/commodity-master.md.
"""
from dataclasses import dataclass
import re
from types import MappingProxyType

from ._commodity_master_data import COMMODITIES


CATEGORIES = frozenset({
    'Chemicals', 'Consumer Items', 'Foods', 'Industrial Materials', 'Legal Drugs',
    'Machinery', 'Medicines', 'Metals', 'Minerals', 'NonMarketable', 'Salvage',
    'Slavery', 'Technology', 'Textiles', 'Waste', 'Weapons',
})


@dataclass(frozen=True)
class CommodityDefinition:
    frontier_id: int
    symbol: str
    english_name: str
    category: str
    rare: bool
    # Empty means no acquisition evidence in this snapshot, not unmineable.
    mining_origins: tuple[str, ...] = ()


def _symbol_key(value: str) -> str:
    token = value.strip()
    if token.startswith('$') and token.casefold().endswith('_name;'):
        token = token[1:-6]
    return token.casefold()


def _build_indexes(definitions):
    by_id, by_symbol = {}, {}
    for item in definitions:
        if (type(item.frontier_id) is not int or item.frontier_id <= 0
                or not re.fullmatch(r'[A-Za-z0-9_]+', item.symbol)
                or not item.english_name.strip() or item.category not in CATEGORIES
                or type(item.rare) is not bool
                or item.mining_origins not in ((), ('surface',), ('asteroid',), ('surface', 'asteroid'))):
            raise ValueError('Invalid Commodity definition')
        key = _symbol_key(item.symbol)
        if item.frontier_id in by_id or key in by_symbol:
            raise ValueError('Duplicate Commodity ID or ambiguous symbol')
        by_id[item.frontier_id] = item
        by_symbol[key] = item
    return MappingProxyType(by_id), MappingProxyType(by_symbol)


_COMMODITIES = tuple(CommodityDefinition(*row) for row in COMMODITIES)
_BY_ID, _BY_SYMBOL = _build_indexes(_COMMODITIES)


def all_commodities() -> tuple[CommodityDefinition, ...]:
    return _COMMODITIES


def lookup_by_id(frontier_id: int) -> CommodityDefinition | None:
    """Exact integer ID; booleans, floats and numeric strings are not IDs."""
    return _BY_ID.get(frontier_id) if type(frontier_id) is int else None


def lookup_by_symbol(value: str) -> CommodityDefinition | None:
    """Known symbol or complete journal token; never infer from display names."""
    return _BY_SYMBOL.get(_symbol_key(value)) if isinstance(value, str) else None


def resolve_symbol(value: str) -> str:
    """Return canonical upstream symbol, or the unknown input verbatim.

    A lookup miss never strips an unknown token, changes its case/underscores,
    or substitutes None/zero. Invalid non-string input is a caller error.
    """
    if not isinstance(value, str):
        raise TypeError('Commodity symbol must be a string')
    item = lookup_by_symbol(value)
    return item.symbol if item is not None else value
