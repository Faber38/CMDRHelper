from __future__ import annotations

from collections.abc import Callable

from .models import ShipRoute


class ShipRouteController:
    """Verwaltet Fortschritt und Clipboard-Ziel einer vorhandenen Schiffsroute."""

    ACTIVE = "active"
    OFF_ROUTE = "off_route"
    COMPLETE = "complete"

    def __init__(
        self,
        copy_callback: Callable[[str], None],
        changed_callback: Callable[[], None] | None = None,
    ):
        self.copy_callback = copy_callback
        self.changed_callback = changed_callback
        self.route: ShipRoute | None = None
        self.current_system = ""
        self.current_system_address: int | None = None
        self._last_position_key = None

    @property
    def next_jump(self):
        if self.route is None or self.route.next_index is None:
            return None
        if not 0 <= self.route.next_index < len(self.route.jumps):
            return None
        return self.route.jumps[self.route.next_index]

    def set_route(
        self,
        route: ShipRoute,
        current_system: str = "",
        current_system_address: int | None = None,
    ):
        route.reached_index = None
        route.next_index = None
        route.status = self.ACTIVE
        self.route = route
        self._last_position_key = None
        self.current_system = str(current_system or "")
        self.current_system_address = current_system_address
        self._synchronize_start()
        self._last_position_key = self._position_key(
            self.current_system, self.current_system_address
        )
        self._notify_changed()

    def clear_route(self):
        self.route = None
        self._last_position_key = None
        self._notify_changed()

    def handle_position(
        self,
        system: str,
        system_address: int | None,
        event_type: str,
    ) -> bool:
        self.current_system = str(system or "")
        self.current_system_address = system_address
        position_key = self._position_key(system, system_address)

        if event_type == "CarrierJump":
            self._notify_changed()
            return False

        if event_type == "Location":
            if self.route is not None and self.route.reached_index is None:
                self._synchronize_start()
            self._last_position_key = position_key
            self._notify_changed()
            return False

        if event_type != "FSDJump":
            self._notify_changed()
            return False

        if position_key == self._last_position_key:
            return False
        self._last_position_key = position_key

        if self.route is None or not self.route.jumps:
            self._notify_changed()
            return False

        match = self._find_forward_match(system, system_address)
        if match is None:
            self.route.status = self.OFF_ROUTE
            self._notify_changed()
            return False

        previous = self.route.reached_index
        if previous is not None and match <= previous:
            self._notify_changed()
            return False

        self._set_anchor(match)
        next_jump = self.next_jump
        if next_jump is not None:
            self.copy_callback(next_jump.system)
        self._notify_changed()
        return True

    def copy_next(self) -> bool:
        jump = self.next_jump
        if jump is None:
            return False
        self.copy_callback(jump.system)
        return True

    def _synchronize_start(self):
        if self.route is None or not self.route.jumps:
            return
        match = self._find_match_from(0, self.current_system, self.current_system_address)
        if match is None:
            self.route.status = self.OFF_ROUTE
            self.route.next_index = 0
            return
        self._set_anchor(match)

    def _find_forward_match(self, system, system_address):
        start = 0
        if self.route is not None and self.route.reached_index is not None:
            start = self.route.reached_index + 1
        return self._find_match_from(start, system, system_address)

    def _find_match_from(self, start, system, system_address):
        if self.route is None:
            return None
        for index in range(max(0, start), len(self.route.jumps)):
            jump = self.route.jumps[index]
            if self._matches(jump.system, jump.system_address, system, system_address):
                return index
        return None

    def _set_anchor(self, index):
        if self.route is None:
            return
        self.route.reached_index = index
        if index + 1 < len(self.route.jumps):
            self.route.next_index = index + 1
            self.route.status = self.ACTIVE
        else:
            self.route.next_index = None
            self.route.status = self.COMPLETE

    @classmethod
    def _matches(cls, route_name, route_address, system, system_address):
        if route_address is not None and system_address is not None:
            return int(route_address) == int(system_address)
        return cls._normalize(route_name) == cls._normalize(system)

    @classmethod
    def _position_key(cls, system, system_address):
        if system_address is not None:
            return ("address", int(system_address))
        return ("name", cls._normalize(system))

    @staticmethod
    def _normalize(value):
        return str(value or "").strip().casefold()

    def _notify_changed(self):
        if self.changed_callback is not None:
            self.changed_callback()
