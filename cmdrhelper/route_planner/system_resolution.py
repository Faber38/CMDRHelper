"""Validated Spansh system identities shared by ship and carrier routing."""
from urllib.parse import urlencode
from cmdrhelper.spansh_transport import TransportError

SYSTEMS_URL = "https://www.spansh.co.uk/api/search/systems"
SYSTEM_URL = "https://www.spansh.co.uk/api/system/{id64}"


class SpanshError(Exception):
    def __init__(self, code: str, detail: str = ""):
        super().__init__(detail or code)
        self.code = code
        self.detail = detail


def valid_id64(value):
    return type(value) is int and 0 < value < 2**64

def resolve_system(request_json, name: str, id64: int | None, error_code: str) -> int:
    """Require an exact identity, independent of the website autocomplete."""
    wanted = name.strip().casefold()
    if id64 is None:
        data = request_json(f"{SYSTEMS_URL}?{urlencode({'q': name.strip()})}")
        results = data.get("results")
        if not isinstance(results, list) or any(not isinstance(r, dict) for r in results):
            raise SpanshError("invalid_response", "Invalid system search results")
        matches = [r for r in results if isinstance(r.get("name"), str)
                   and r["name"].strip().casefold() == wanted]
        if len(matches) != 1:
            raise SpanshError(error_code)
        id64 = matches[0].get("id64")
    if not valid_id64(id64):
        raise SpanshError(error_code)
    try:
        data = request_json(SYSTEM_URL.format(id64=id64))
    except SpanshError as exc:
        if isinstance(exc.__cause__, TransportError) and exc.__cause__.status == 404:
            raise SpanshError(error_code) from exc
        raise
    record = data.get("record")
    if not isinstance(record, dict):
        raise SpanshError("invalid_response", "Missing system record")
    if (not valid_id64(record.get("id64")) or record["id64"] != id64
            or not isinstance(record.get("name"), str)
            or record["name"].strip().casefold() != wanted):
        raise SpanshError(error_code)
    return id64

