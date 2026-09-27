"""Shared, read-only local cache summary for trade and recommendations."""
from PySide6.QtCore import QLocale
from cmdrhelper.i18n import get_language, tr


def format_cache_size(size):
    locale = QLocale(get_language())
    if size < 1024:
        return locale.toString(size) + ' B'
    if size < 1024 * 1024:
        return locale.toString(size / 1024, 'f', 0) + ' KiB'
    value = round(size / (1024 * 1024), 1)
    return locale.toString(value, 'f', 0 if value.is_integer() else 1) + ' MiB'


def observed_market_text(state):
    observer = getattr(state, 'observed_markets', None)
    try:
        count, size = observer.cache.storage_stats() if observer is not None else (0, 0)
    except (OSError, RuntimeError) as exc:
        return f'markets.db: {exc}'
    return tr('trade.observed_one' if count == 1 else 'trade.observed_many',
              count=count, size=format_cache_size(size))
