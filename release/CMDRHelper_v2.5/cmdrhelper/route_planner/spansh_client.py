from __future__ import annotations

import json
import logging
import socket
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .models import CarrierRoute, CarrierRouteJump, CarrierRouteRequest

logger = logging.getLogger(__name__)

SEARCH_URL = "https://spansh.co.uk/api/search/systems"
ROUTE_URL = "https://spansh.co.uk/api/fleetcarrier/route"
RESULT_URL = "https://spansh.co.uk/api/results/{job}"
USER_AGENT = "CMDRHelper/route-planner"


class SpanshError(Exception):
    def __init__(self, code: str, detail: str = ""):
        super().__init__(detail or code)
        self.code = code
        self.detail = detail


class SpanshFleetCarrierClient:
    """Synchroner Spansh-Client; Aufrufe gehören immer in einen Worker."""

    def __init__(self, timeout=15, poll_interval=2, max_polls=60):
        self.timeout = timeout
        self.poll_interval = poll_interval
        self.max_polls = max_polls

    def calculate(self, request: CarrierRouteRequest) -> CarrierRoute:
        source_id = self._resolve_system(request.source, "source_unknown")
        destination_id = self._resolve_system(
            request.destination, "destination_unknown"
        )

        # Spansh behandelt den 1.000-t-Tank separat von der belegten
        # Carrier-Kapazität. Ohne weitere Fracht entspricht capacity_used
        # deshalb dem Tritium im Carrier-Lager, nicht Tank + Lager.
        capacity_used = request.tritium_in_storage

        # Spansh kennt für diesen Router kein Feld für eine abweichende
        # maximale Sprungreichweite. Der Carrier-Standard von 500 ly gilt dort.
        payload = {
            "source": source_id,
            "destinations": destination_id,
            "capacity": 25000,
            "mass": 25000,
            "capacity_used": capacity_used,
            "calculate_starting_fuel": 0,
            "fuel_loaded": request.tritium_in_tank,
            "tritium_stored": request.tritium_in_storage,
        }
        submitted = self._request_json(ROUTE_URL, data=payload)
        if self._has_route(submitted):
            completed = submitted
        else:
            job = submitted.get("job") if isinstance(submitted, dict) else None
            if not job:
                raise SpanshError("invalid_response", "Spansh returned no job ID")
            completed = self._poll(str(job))

        return self._parse_route(completed)

    def _resolve_system(self, name: str, error_code: str) -> int:
        query = urlencode({"q": name})
        data = self._request_json(f"{SEARCH_URL}?{query}")
        results = data.get("results") if isinstance(data, dict) else None
        if not isinstance(results, list):
            raise SpanshError("invalid_response", "Invalid system search response")
        wanted = name.strip().casefold()
        for result in results:
            if not isinstance(result, dict):
                continue
            if str(result.get("name") or "").strip().casefold() != wanted:
                continue
            try:
                return int(result["id64"])
            except (KeyError, TypeError, ValueError):
                break
        raise SpanshError(error_code)

    def _poll(self, job: str) -> dict:
        for attempt in range(self.max_polls):
            data = self._request_json(RESULT_URL.format(job=job))
            if not isinstance(data, dict):
                raise SpanshError("invalid_response")
            if data.get("status") == "ok" or data.get("state") == "completed":
                return data
            if data.get("error"):
                raise SpanshError("spansh_error", str(data["error"]))
            if data.get("state") in {"failed", "error"}:
                raise SpanshError("spansh_error")
            if attempt < self.max_polls - 1:
                time.sleep(self.poll_interval)
        raise SpanshError("timeout")

    def _request_json(self, url: str, data=None):
        body = urlencode(data).encode("utf-8") if data is not None else None
        request = Request(
            url,
            data=body,
            headers={
                "User-Agent": USER_AGENT,
                "Accept": "application/json",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            method="POST" if body is not None else "GET",
        )
        try:
            with urlopen(request, timeout=self.timeout) as response:
                raw = response.read().decode("utf-8", errors="replace")
        except HTTPError as exc:
            detail = self._http_error_detail(exc)
            logger.warning("Spansh HTTP error %s: %s", exc.code, detail)
            if exc.code >= 500:
                raise SpanshError("server_error", detail) from exc
            raise SpanshError("spansh_error", detail) from exc
        except (TimeoutError, socket.timeout) as exc:
            raise SpanshError("timeout") from exc
        except URLError as exc:
            reason = getattr(exc, "reason", exc)
            if isinstance(reason, (TimeoutError, socket.timeout)):
                raise SpanshError("timeout") from exc
            raise SpanshError("unreachable", str(reason)) from exc
        except OSError as exc:
            raise SpanshError("unreachable", str(exc)) from exc

        try:
            result = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise SpanshError("invalid_response", "Invalid JSON") from exc
        if not isinstance(result, dict):
            raise SpanshError("invalid_response", "Expected a JSON object")
        return result

    @staticmethod
    def _http_error_detail(exc: HTTPError) -> str:
        try:
            raw = exc.read().decode("utf-8", errors="replace")
            data = json.loads(raw)
            if isinstance(data, dict) and data.get("error"):
                return str(data["error"])
            return raw[:500]
        except Exception:
            return f"HTTP {exc.code}"

    @staticmethod
    def _has_route(data) -> bool:
        if not isinstance(data, dict):
            return False
        route = data.get("result", data)
        return isinstance(route, dict) and isinstance(route.get("jumps"), list)

    def _parse_route(self, data: dict) -> CarrierRoute:
        route = data.get("result", data)
        jumps_data = route.get("jumps") if isinstance(route, dict) else None
        if not isinstance(jumps_data, list):
            raise SpanshError("invalid_response", "Missing jumps")
        if not jumps_data:
            raise SpanshError("no_route")

        jumps = []
        total_distance = 0.0
        total_tritium = 0
        for item in jumps_data:
            if not isinstance(item, dict) or not str(item.get("name") or "").strip():
                raise SpanshError("invalid_response", "Invalid jump entry")
            distance = self._optional_float(item.get("distance"))
            remaining = self._optional_float(item.get("distance_to_destination"))
            tritium = self._optional_int(item.get("fuel_used"))
            if distance is not None:
                total_distance += distance
            if tritium is not None:
                total_tritium += tritium
            jumps.append(
                CarrierRouteJump(
                    system=str(item["name"]),
                    distance=distance,
                    distance_remaining=remaining,
                    tritium_used=tritium,
                    fuel_in_tank=self._optional_int(item.get("fuel_in_tank")),
                    tritium_in_market=self._optional_int(
                        item.get("tritium_in_market")
                    ),
                    has_icy_ring=self._optional_bool(item.get("has_icy_ring")),
                    is_system_pristine=self._optional_bool(
                        item.get("is_system_pristine")
                    ),
                    must_restock=self._optional_bool(item.get("must_restock")),
                )
            )
        return CarrierRoute(
            jumps=tuple(jumps),
            total_distance=total_distance,
            jump_count=max(len(jumps) - 1, 0),
            estimated_tritium=total_tritium,
        )

    @staticmethod
    def _optional_float(value):
        try:
            return float(value) if value is not None else None
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _optional_int(value):
        try:
            return int(value) if value is not None else None
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _optional_bool(value):
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)) and value in (0, 1):
            return bool(value)
        return None
