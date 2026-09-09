"""Shared synchronous Spansh transport; callers own scheduling and retry policy."""
import json
from urllib.error import HTTPError, URLError
from urllib.request import urlopen


class TransportError(Exception):
    def __init__(self, code, detail='', *, status=None, retry_after=None, response_json=None):
        super().__init__(detail or code)
        self.code, self.detail = code, detail
        self.status, self.retry_after = status, retry_after
        self.response_json = response_json


def request_json(request, *, timeout=15, opener=None):
    try:
        with (opener or urlopen)(request, timeout=timeout) as response:
            raw = response.read().decode('utf-8', errors='replace')
    except HTTPError as exc:
        retry_after = exc.headers.get('Retry-After') if exc.headers else None
        data = None
        try:
            raw = exc.read().decode('utf-8', errors='replace')
            data = json.loads(raw)
            detail = str(data.get('error') or raw[:500]) if isinstance(data, dict) else raw[:500]
        except Exception:
            detail = f'HTTP {exc.code}'
        raise TransportError('http_error', detail, status=exc.code, retry_after=retry_after,
                             response_json=data) from exc
    except TimeoutError as exc:
        raise TransportError('timeout') from exc
    except URLError as exc:
        code = 'timeout' if isinstance(exc.reason, TimeoutError) else 'network_error'
        raise TransportError(code, str(exc.reason)) from exc
    except OSError as exc:
        raise TransportError('network_error', str(exc)) from exc
    try:
        return json.loads(raw)
    except (ValueError, RecursionError) as exc:
        raise TransportError('invalid_json', 'Invalid JSON') from exc
