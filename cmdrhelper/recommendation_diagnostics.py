"""Bounded, price-free RAM diagnostics for a single recommendation run."""
from copy import deepcopy
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from threading import Event, Lock
from time import monotonic

from .market_data import MarketStatus, ProviderDiagnostics


class PartialReason(str, Enum):
    NONE = 'NONE'
    PROVIDER_NETWORK = 'PROVIDER_NETWORK'
    PROVIDER_TIMEOUT = 'PROVIDER_TIMEOUT'
    PROVIDER_HTTP = 'PROVIDER_HTTP'
    PROVIDER_RATE_LIMIT = 'PROVIDER_RATE_LIMIT'
    PROVIDER_INVALID_RESPONSE = 'PROVIDER_INVALID_RESPONSE'
    PROVIDER_UNKNOWN_SYSTEM = 'PROVIDER_UNKNOWN_SYSTEM'
    PROVIDER_TRUNCATED = 'PROVIDER_TRUNCATED'
    PROVIDER_PAGE_LIMIT = 'PROVIDER_PAGE_LIMIT'
    PROVIDER_RESULT_LIMIT = 'PROVIDER_RESULT_LIMIT'
    COMMODITY_ERROR = 'COMMODITY_ERROR'
    CANCELLED = 'CANCELLED'
    CONTEXT_CHANGED = 'CONTEXT_CHANGED'
    OTHER = 'OTHER'


STATUS_REASONS = {
    MarketStatus.NETWORK_ERROR: PartialReason.PROVIDER_NETWORK,
    MarketStatus.TIMEOUT: PartialReason.PROVIDER_TIMEOUT,
    MarketStatus.HTTP_ERROR: PartialReason.PROVIDER_HTTP,
    MarketStatus.RATE_LIMIT: PartialReason.PROVIDER_RATE_LIMIT,
    MarketStatus.INVALID_JSON: PartialReason.PROVIDER_INVALID_RESPONSE,
    MarketStatus.INVALID_RESPONSE: PartialReason.PROVIDER_INVALID_RESPONSE,
    MarketStatus.UNKNOWN_SYSTEM: PartialReason.PROVIDER_UNKNOWN_SYSTEM,
    MarketStatus.UNKNOWN_COMMODITY: PartialReason.COMMODITY_ERROR,
    MarketStatus.CANCELLED: PartialReason.CANCELLED,
}


class RecommendationCancellation(Event):
    """An Event with a diagnostic reason; waiting/cancellation behavior is unchanged."""
    def __init__(self):
        super().__init__()
        self.reason = PartialReason.CANCELLED
        self._reason_lock = Lock()

    def request(self, reason):
        with self._reason_lock:
            if not self.is_set():
                self.reason = reason
            self.set()


@dataclass(frozen=True)
class CommodityIdentity:
    commodity_id: int | None
    symbol: str


@dataclass
class CommodityStep:
    commodity: CommodityIdentity
    search_started: bool = False
    local_completed: bool = False
    local_combinations_checked: int = 0
    local_candidates: int = 0
    spansh_started: bool = False
    spansh_completed: bool = False
    provider_status: MarketStatus | None = None
    truncated: bool = False
    provider: ProviderDiagnostics | None = None
    checked: bool = False
    successful: bool = False
    failed: bool = False
    reasons: list[PartialReason] = field(default_factory=list)
    overlapping_market_ids: int = 0
    local_won_freshness: int = 0
    spansh_won_freshness: int = 0
    equal_timestamp_merges: int = 0


@dataclass
class RecommendationDiagnostics:
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    finished_at: datetime | None = None
    duration: float = 0.0
    planned_commodities: int = 0
    checked_commodities: int = 0
    successful_commodities: int = 0
    failed_commodities: int = 0
    skipped_commodities: int = 0
    local_target_markets: int = 0
    local_combinations_checked: int = 0
    local_candidates: int = 0
    local_recommendations: int = 0
    local_commodities_completed: int = 0
    spansh_commodities_started: int = 0
    spansh_commodities_completed: int = 0
    spansh_commodities_failed: int = 0
    http_requests: int = 0
    cache_hits: int = 0
    retries: int = 0
    last_http_status: int | None = None
    retry_after: str | None = None
    provider_truncated_count: int = 0
    provider_error_count: int = 0
    local_only: bool = False
    partial: bool = False
    partial_reason: PartialReason = PartialReason.NONE
    reasons: list[PartialReason] = field(default_factory=list)
    current_commodity: CommodityIdentity | None = None
    first_failed_commodity: CommodityIdentity | None = None
    last_completed_commodity: CommodityIdentity | None = None
    cancelled: bool = False
    overlapping_market_ids: int = 0
    local_won_freshness: int = 0
    spansh_won_freshness: int = 0
    equal_timestamp_merges: int = 0
    merge_errors: int = 0
    steps: list[CommodityStep] = field(default_factory=list)
    _started_tick: float = field(default_factory=monotonic, repr=False)

    def reason(self, reason, step=None):
        if reason not in self.reasons:
            self.reasons.append(reason)
        if self.partial_reason == PartialReason.NONE or reason in (
                PartialReason.CANCELLED, PartialReason.CONTEXT_CHANGED):
            self.partial_reason = reason
        if step is not None:
            if reason not in step.reasons:
                step.reasons.append(reason)
            if self.first_failed_commodity is None:
                self.first_failed_commodity = step.commodity

    def aggregate(self):
        self.planned_commodities = len(self.steps)
        self.checked_commodities = sum(s.checked for s in self.steps)
        self.successful_commodities = sum(s.successful for s in self.steps)
        self.failed_commodities = sum(s.failed for s in self.steps)
        self.skipped_commodities = self.planned_commodities - self.checked_commodities
        self.local_commodities_completed = sum(s.local_completed for s in self.steps)
        for name in ('local_combinations_checked', 'local_candidates', 'overlapping_market_ids',
                     'local_won_freshness', 'spansh_won_freshness', 'equal_timestamp_merges'):
            setattr(self, name, sum(getattr(s, name) for s in self.steps))
        self.spansh_commodities_started = sum(s.spansh_started for s in self.steps)
        self.spansh_commodities_completed = sum(s.spansh_completed for s in self.steps)
        self.spansh_commodities_failed = sum(s.spansh_completed and s.failed for s in self.steps)
        self.provider_truncated_count = sum(s.truncated for s in self.steps)
        self.provider_error_count = sum(s.provider_status is not None and s.provider_status not in (
            MarketStatus.OK, MarketStatus.NO_RESULTS, MarketStatus.CANCELLED) for s in self.steps)
        for name in ('http_requests', 'cache_hits', 'retries'):
            setattr(self, name, sum(getattr(s.provider, name) for s in self.steps if s.provider is not None))
        for step in self.steps:
            if step.provider is not None:
                if step.provider.last_http_status is not None:
                    self.last_http_status = step.provider.last_http_status
                if step.provider.retry_after is not None:
                    self.retry_after = step.provider.retry_after
        if self.finished_at is None:
            self.duration = max(0.0, monotonic() - self._started_tick)
        return self

    def snapshot(self):
        return deepcopy(self.aggregate())

    def finish(self, *, partial=False, cancelled=False, reason=None):
        if reason is not None:
            self.reason(reason)
        self.partial, self.cancelled = partial, cancelled
        self.aggregate()
        self.finished_at = datetime.now(timezone.utc)
        return self.snapshot()
