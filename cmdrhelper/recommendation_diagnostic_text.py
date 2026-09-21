"""Explicit, price-free text projection of an already completed RAM diagnostic."""
from datetime import datetime
from email.utils import parsedate_to_datetime
from enum import Enum
import re

from .recommendation_diagnostics import PartialReason


def _value(value):
    if value is None:
        return 'none'
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


def _commodity(value):
    if value is None:
        return 'none'
    symbol = value.symbol
    if not isinstance(symbol, str) or not re.fullmatch(r'[A-Za-z0-9_$;]{1,160}', symbol):
        symbol = '[invalid_symbol]'
    identity = value.commodity_id if type(value.commodity_id) is int else None
    return f'{_value(identity)}:{symbol}'


def _retry_after(value):
    if value is None:
        return 'none'
    # A server header is not a free-form diagnostic message. Never export URLs,
    # response fragments or injected extra lines from an unexpected header.
    value = str(value).strip()
    if re.fullmatch(r'[0-9]{1,20}', value):
        return value
    if len(value) <= 80 and re.fullmatch(r'[A-Za-z0-9, :+\-]+', value):
        try:
            parsedate_to_datetime(value)
            return value
        except (ValueError, TypeError, OverflowError):
            pass
    return '[invalid_retry_after]'


def format_recommendation_diagnostic(diagnostic):
    """No aggregation, mutation, cache access, lookup, persistence or clipboard IO."""
    lines = ['CMDRHelper trade recommendation diagnostic']

    def add(key, value):
        lines.append(f'{key}={_value(value)}')

    for name in ('started_at', 'finished_at'):
        add(name, getattr(diagnostic, name))
    add('duration_seconds', diagnostic.duration)
    for name in (
        'planned_commodities', 'checked_commodities', 'successful_commodities',
        'failed_commodities', 'skipped_commodities', 'spansh_commodities_started',
        'spansh_commodities_completed', 'spansh_commodities_failed', 'http_requests',
        'cache_hits', 'retries', 'local_only', 'partial', 'partial_reason', 'provider_truncated_count',
        'provider_error_count', 'last_http_status', 'local_target_markets',
        'local_combinations_checked', 'local_commodities_completed', 'local_candidates',
        'local_recommendations', 'overlapping_market_ids', 'local_won_freshness',
        'spansh_won_freshness', 'equal_timestamp_merges', 'merge_errors', 'cancelled',
    ):
        add(name, getattr(diagnostic, name))
    add('retry_after', _retry_after(diagnostic.retry_after))
    add('context_changed', diagnostic.partial_reason == PartialReason.CONTEXT_CHANGED
        or PartialReason.CONTEXT_CHANGED in diagnostic.reasons)
    add('reasons', ','.join(reason.value for reason in diagnostic.reasons) or 'none')
    for name in ('current_commodity', 'first_failed_commodity', 'last_completed_commodity'):
        add(name, _commodity(getattr(diagnostic, name)))
    first = next((step for step in diagnostic.steps
                  if step.commodity == diagnostic.first_failed_commodity), None)
    if first is not None:
        add('first_failed.provider_status', first.provider_status)
        add('first_failed.truncated', first.truncated)
        add('first_failed.reasons', ','.join(reason.value for reason in first.reasons) or 'none')
        if first.provider is not None:
            for name in ('pages_started', 'pages_completed', 'page_limit', 'result_limit',
                         'page_limit_reached', 'result_limit_reached', 'last_http_status'):
                add('first_failed.' + name, getattr(first.provider, name))
            add('first_failed.retry_after', _retry_after(first.provider.retry_after))
    return '\n'.join(lines)
