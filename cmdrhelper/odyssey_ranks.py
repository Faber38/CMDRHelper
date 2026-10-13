"""Static, commander-independent engineering priorities, not Elite grades."""
from dataclasses import dataclass
from types import MappingProxyType

from ._odyssey_rank_data import RATINGS
from .odyssey_catalog import all_materials, get_material


@dataclass(frozen=True)
class Rating:
    rank: str
    reason: str
    recipes: tuple[tuple[str, str], ...] = ()


RANKS = MappingProxyType({symbol: Rating(*value) for symbol, value in RATINGS.items()})
UNKNOWN = Rating("?", "unverified")
if set(RANKS) != {m.symbol for m in all_materials()}:
    raise ValueError("Odyssey rank catalog coverage mismatch")
if any(r.rank not in ("A", "B", "C", "D", "?") for r in RANKS.values()):
    raise ValueError("Invalid Odyssey rank")


def rating(symbol, category=None):
    definition = get_material(symbol)
    if definition is None or category is not None and definition.category != category:
        return UNKNOWN
    return RANKS.get(definition.symbol, UNKNOWN)


def sort_priority(rank, descending=False):
    """Unknowns remain last in both directions."""
    return ("DCBA" if descending else "ABCD").find(rank) if rank in "ABCD" else 4
