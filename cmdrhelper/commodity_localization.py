"""Offline display names only; never normalize identity or persist observations."""
import re
from types import MappingProxyType

from ._commodity_localization_de import GERMAN_NAMES
from .commodity_master import lookup_by_id
from .i18n import get_language, tr_for_language


def _german_index():
    names = {}
    for frontier_id, symbol, name, _source in GERMAN_NAMES:
        item = lookup_by_id(frontier_id)
        if item is None or item.symbol != symbol or frontier_id in names or not name.strip():
            raise ValueError('Invalid German commodity localization identity')
        names[frontier_id] = (symbol, name)
    return MappingProxyType(names)


_GERMAN = _german_index()


def commodity_name(item, language=None):
    """Resolve maintained locale name, then English, then a readable symbol.

    The picker owns no language-qualified Frontier observation, so this API does
    not accept unqualified Localised strings or introduce a learning cache.
    """
    language = get_language() if language is None else language
    if language == 'de':
        entry = _GERMAN.get(item.frontier_id)
        if entry and entry[0] == item.symbol:
            return entry[1]
    key = 'mining.commodity.' + item.symbol.casefold()
    translated = tr_for_language(language, key)
    if translated != key:
        return translated
    if item.english_name:
        return item.english_name
    return re.sub(r'(?<=[a-z0-9])(?=[A-Z])', ' ', item.symbol.replace('_', ' '))
