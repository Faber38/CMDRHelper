"""Provider-independent, transient market search contracts. No UI or persistence."""
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from threading import Event
from typing import Protocol


class TradeSide(str, Enum):
    BUY = 'buy'
    SELL = 'sell'


class PadSize(str, Enum):
    ANY = 'any'
    SMALL = 'small'
    MEDIUM = 'medium'
    LARGE = 'large'


class MarketStatus(str, Enum):
    OK = 'ok'
    NO_RESULTS = 'no_results'
    UNKNOWN_COMMODITY = 'unknown_commodity'
    UNKNOWN_SYSTEM = 'unknown_system'
    INVALID_QUERY = 'invalid_query'
    NETWORK_ERROR = 'network_error'
    TIMEOUT = 'timeout'
    HTTP_ERROR = 'http_error'
    RATE_LIMIT = 'rate_limit'
    INVALID_JSON = 'invalid_json'
    INVALID_RESPONSE = 'invalid_response'
    CANCELLED = 'cancelled'


@dataclass(frozen=True)
class MarketSearch:
    # Exact master ID or symbol/journal token, never a localized display name.
    commodity: int | str
    reference_system: str
    radius_ly: float = 100
    minimum_quantity: int | None = None
    max_age: timedelta = timedelta(hours=24)
    include_fleet_carriers: bool = False
    required_pad: PadSize = PadSize.ANY
    max_distance_to_arrival_ls: float | None = None
    limit: int = 20


@dataclass(frozen=True)
class MarketOffer:
    commodity_id: int | None
    commodity_symbol: str
    commodity_name: str
    system_name: str
    system_id64: int | None
    station_name: str
    market_id: int
    station_type: str
    distance_ly: float | None
    distance_to_arrival_ls: float | None
    largest_pad: PadSize | None
    is_fleet_carrier: bool | None
    carrier_docking_access: str | None
    commander_buy_price: int | None
    commander_sell_price: int | None
    supply: int | None
    demand: int | None
    market_updated_at: datetime
    retrieved_at: datetime
    provider: str


@dataclass(frozen=True)
class ProviderDiagnostics:
    """One provider call, including transport attempts; never prices or URLs."""
    http_requests: int = 0
    cache_hits: int = 0
    retries: int = 0
    last_http_status: int | None = None
    retry_after: str | None = None
    pages_started: int = 0
    pages_completed: int = 0
    page_limit: int = 0
    result_limit: int = 0
    page_limit_reached: bool = False
    result_limit_reached: bool = False


@dataclass(frozen=True)
class MarketSearchResult:
    status: MarketStatus
    offers: tuple[MarketOffer, ...] = ()
    # Original query preserves unknown future raw commodity identifiers.
    query: MarketSearch | None = None
    http_status: int | None = None
    retry_after: str | None = None
    # True means bounded search, not an exhaustive global best-price claim.
    truncated: bool = False
    from_cache: bool = False
    diagnostics: ProviderDiagnostics | None = field(default=None, compare=False)
    # Usable local results despite a failed community search; unrelated to limits.
    community_failure: MarketStatus | None = None


class MarketDataProvider(Protocol):
    def search_sell(self, query: MarketSearch, *, cancel: Event | None = None) -> MarketSearchResult: ...

    def search_buy(self, query: MarketSearch, *, cancel: Event | None = None) -> MarketSearchResult: ...
