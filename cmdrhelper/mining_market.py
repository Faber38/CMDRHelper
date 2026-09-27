"""Bounded read-only own-market information; fixed mining references stay separate."""
from dataclasses import dataclass
from pathlib import Path

from .market_store import CommodityRef, MarketStore
from .mining_catalog import MINING_COMMODITIES
from .observed_market_cache import utcnow


@dataclass(frozen=True)
class MiningPrices:
    quotes: tuple = ()
    status: str = 'ok'


def read_mining_prices(market_path, max_age, *,
                       commodities=MINING_COMMODITIES, clock=utcnow, cancel=None):
    """One bounded batch of installation-wide observations, read only in a worker.

    Positive demand is required for a usable sale. Unknown demand cannot be
    confirmed by the current observation schema and yields no usable quote.
    No history, JSON fallback, writer, schema changes or online providers.
    """
    if cancel is not None and cancel.is_set():
        return MiningPrices(status='cancelled')
    if not Path(market_path).exists():
        return MiningPrices(status='missing')
    refs = tuple(CommodityRef(None, c.symbol) for c in commodities)
    with MarketStore(market_path, read_only=True, clock=clock) as store:
        store._con.set_progress_handler(lambda: int(cancel is not None and cancel.is_set()), 1000)
        try:
            quotes = store.best_sell_prices(refs, scope='current', max_age=max_age, min_demand=1)
        finally:
            store._con.set_progress_handler(None, 0)
    return MiningPrices(quotes)
