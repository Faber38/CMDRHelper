from __future__ import annotations

import json
import logging
import socket
import time
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

from .models import ShipRoute, ShipRouteJump, ShipRouteRequest
from .spansh_client import SpanshError, USER_AGENT

logger = logging.getLogger(__name__)

ROUTE_URL = "https://www.spansh.co.uk/api/generic/route"
RESULT_URL = "https://www.spansh.co.uk/api/results/{job}"
SYSTEMS_URL = "https://www.spansh.co.uk/api/systems"
ALGORITHMS = ("optimistic", "pessimistic", "fuel", "fuel_jumps", "guided")


class SpanshGalaxyClient:
    """Synchroner Galaxy-Plotter-Client; Aufrufe gehören in einen Worker."""

    def __init__(self, timeout=15, poll_interval=2, max_polls=60):
        self.timeout = timeout
        self.poll_interval = poll_interval
        self.max_polls = max_polls
        self.last_job_id: str | None = None

    def calculate(self, request: ShipRouteRequest) -> ShipRoute:
        validation_error = request.validation_error()
        if validation_error:
            raise SpanshError("invalid_input", validation_error)
        self._require_system(request.source, "source_unknown")
        self._require_system(request.destination, "destination_unknown")
        payload = {
            "source": request.source,
            "destination": request.destination,
            "is_supercharged": int(request.is_supercharged),
            "use_supercharge": int(request.use_supercharge),
            "use_injections": int(request.use_injections),
            "exclude_secondary": int(request.exclude_secondary),
            "refuel_every_scoopable": int(request.refuel_every_scoopable),
            "algorithm": request.algorithm,
            "tank_size": request.tank_size,
            "cargo": request.cargo,
            "optimal_mass": request.optimal_mass,
            "base_mass": request.base_mass,
            "internal_tank_size": request.internal_tank_size,
            "max_fuel_per_jump": request.max_fuel_per_jump,
            "range_boost": request.range_boost,
            "fuel_power": request.fuel_power,
            "fuel_multiplier": request.fuel_multiplier,
            "reserve_size": request.reserve_size,
            "supercharge_multiplier": request.supercharge_multiplier,
            "injection_multiplier": request.injection_multiplier,
            "max_time": request.max_time,
        }
        submitted = self._request_json(ROUTE_URL, payload)
        if self._has_route(submitted):
            completed = submitted
        else:
            job = submitted.get("job") if isinstance(submitted, dict) else None
            if not job:
                raise SpanshError("invalid_response", "Spansh returned no job ID")
            self.last_job_id = str(job)
            completed = self._poll(self.last_job_id)
        return self._parse_route(completed)

    def _require_system(self, name: str, error_code: str) -> None:
        query = urlencode({"q": name})
        results = self._request_json(
            f"{SYSTEMS_URL}?{query}", expected_type=list
        )
        wanted = name.strip().casefold()
        if not any(
            str(result).strip().casefold() == wanted for result in results
        ):
            raise SpanshError(error_code)

    def _poll(self, job: str) -> dict:
        url = RESULT_URL.format(job=quote(job, safe=""))
        for attempt in range(self.max_polls):
            data = self._request_json(url)
            if data.get("status") == "ok" or data.get("state") == "completed":
                return data
            if (
                data.get("error")
                or data.get("state") in {"failed", "error"}
                or data.get("status") in {"failed", "error"}
            ):
                raise SpanshError("spansh_error", str(data.get("error") or ""))
            if attempt < self.max_polls - 1:
                time.sleep(self.poll_interval)
        raise SpanshError("timeout")

    def _request_json(self, url: str, data=None, expected_type=dict):
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
            logger.warning("Spansh Galaxy HTTP error %s: %s", exc.code, detail)
            code = "server_error" if exc.code >= 500 else "spansh_error"
            raise SpanshError(code, detail) from exc
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
        if not isinstance(result, expected_type):
            expected = "object" if expected_type is dict else "list"
            raise SpanshError("invalid_response", f"Expected a JSON {expected}")
        return result

    @staticmethod
    def _http_error_detail(exc: HTTPError) -> str:
        try:
            raw = exc.read().decode("utf-8", errors="replace")
            data = json.loads(raw)
            return str(data.get("error") or raw[:500]) if isinstance(data, dict) else raw[:500]
        except Exception:
            return f"HTTP {exc.code}"

    @staticmethod
    def _has_route(data) -> bool:
        route = data.get("result", data) if isinstance(data, dict) else None
        return isinstance(route, dict) and isinstance(route.get("jumps"), list)

    def _parse_route(self, data: dict) -> ShipRoute:
        result = data.get("result", data)
        jumps_data = result.get("jumps") if isinstance(result, dict) else None
        if not isinstance(jumps_data, list):
            raise SpanshError("invalid_response", "Missing jumps")
        if not jumps_data:
            raise SpanshError("no_route")
        jumps = []
        for item in jumps_data:
            if not isinstance(item, dict) or not str(item.get("name") or "").strip():
                raise SpanshError("invalid_response", "Invalid jump entry")
            jumps.append(ShipRouteJump(
                system=str(item["name"]),
                system_address=self._optional_int(item.get("id64")),
                distance=self._optional_float(item.get("distance")),
                distance_remaining=self._optional_float(item.get("distance_to_destination")),
                fuel_in_tank=self._optional_float(item.get("fuel_in_tank")),
                fuel_used=self._optional_float(item.get("fuel_used")),
                must_refuel=self._optional_bool(item.get("must_refuel")),
                has_neutron=self._optional_bool(item.get("has_neutron")),
            ))
        return ShipRoute(tuple(jumps))

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
