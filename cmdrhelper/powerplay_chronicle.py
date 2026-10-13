"""Ephemeral PP2 display groups; proximity never proves a cause."""
from dataclasses import dataclass, field
from datetime import datetime


def is_market_sale(event):
    """Recognize a journal sale using offline commodity identity, not its label."""
    from .commodity_master import lookup_by_symbol
    from .powerplay import amount, timestamp
    if event.get("event") != "MarketSell":
        return False
    count = amount(event.get("Count"))
    commodity = lookup_by_symbol(event.get("Type"))
    return (count is not None and count > 0 and commodity is not None
            and timestamp(event.get("timestamp")) is not None)


def is_rare_sale(event):
    from .commodity_master import lookup_by_symbol
    return is_market_sale(event) and lookup_by_symbol(event["Type"]).rare


def local_today():
    return datetime.now().astimezone().date()


def local_event_day(value, zone=None):
    from .powerplay import timestamp
    at = timestamp(value)
    # Convert each instant separately: the current UTC offset is not a timezone
    # and must not be reused for timestamps on the other side of a DST change.
    return at.astimezone(zone).date() if at else None


def today_groups(chronicle, day=None, zone=None):
    from .powerplay import timestamp
    day = day or local_today()
    return sorted((g for g in chronicle.groups
                   if local_event_day(g.action.get("timestamp"), zone) == day),
                  key=lambda g: timestamp(g.action["timestamp"]), reverse=True)


def chronicle_for_day(events, day, zone=None):
    """Replay the same correlations, keeping pre-midnight location context only."""
    from .powerplay import PowerplayState
    state = PowerplayState()
    chronicle = PowerplayChronicle()
    for event in events:
        state._apply(event)
        if local_event_day(event.get("timestamp"), zone) == day:
            chronicle.apply(event, system=state.system.get("StarSystem", ""),
                            station=state.station, power=state.power)
        else:
            # A day boundary cannot leave a stale candidate/block open.
            chronicle.pending = chronicle.active = None
            chronicle.ambiguous = False
    return chronicle


@dataclass
class ChronicleGroup:
    action: dict
    certainty: str
    system: str = ""
    station: str = ""
    power: str = ""
    credits: list[dict] = field(default_factory=list)
    # Ephemeral alternatives, consulted only for sequences involving a sale.
    competitors: list["ChronicleGroup"] = field(default_factory=list, repr=False)
    # Delivery-only evidence travels with the active group, so existing source,
    # sequence and day resets also discard it. Credits do not consume causes.
    delivery_competitors: list["ChronicleGroup"] = field(default_factory=list, repr=False)
    last_delivery_event: dict | None = field(default=None, repr=False)
    locker_seen: bool = False
    delivery_blocked: bool = False
    last_sale_event: dict | None = field(default=None, repr=False)


@dataclass
class PowerplayChronicle:
    groups: list[ChronicleGroup] = field(default_factory=list)
    pending: ChronicleGroup | None = None
    active: ChronicleGroup | None = None
    ambiguous: bool = False

    def _append(self, group):
        self.groups.append(group)
        self.active = group

    @staticmethod
    def _gap(first, second):
        from .powerplay import timestamp
        a, b = timestamp(first.get("timestamp")), timestamp(second.get("timestamp"))
        return (b - a).total_seconds() if a is not None and b is not None else None

    @staticmethod
    def _window(group):
        return {"ShipTargeted": 3, "MarketSell": 2}.get(group.action.get("event"), 1)

    @staticmethod
    def _sale_related(group):
        return group is not None and any(g.action.get("event") == "MarketSell"
                                         for g in [group, *group.competitors])

    @classmethod
    def _cause_window(cls, group):
        # Delivery already has a three-second matching window. Sales must not
        # discard that alternative merely because their own window is shorter.
        return 3 if group.action.get("event") == "PowerplayDeliver" else cls._window(group)

    def _sale_competitors(self, previous, event, *, keep_candidates=False):
        """Carry alternatives through credits, never through a reset/barrier.

        Unknown credits may retain an earlier action for a subsequent
        sale; this does not change matching between other activity types.
        """
        if previous is None:
            return []
        recent = []
        for group in [previous, *previous.competitors]:
            gap = self._gap(group.action, event)
            if (group.certainty != "unknown" and gap is not None
                    and 0 <= gap <= self._cause_window(group)
                    and all(group is not other for other in recent)):
                recent.append(group)
        if keep_candidates or is_market_sale(event) or any(g.action.get("event") == "MarketSell" for g in recent):
            return recent
        return []

    def _delivery_causes(self, previous, event):
        if previous is None:
            return []
        result = []
        for group in [previous, *previous.delivery_competitors, *previous.competitors]:
            kind = group.action.get("event")
            if kind not in ("PowerplayDeliver", "Bounty", "SearchAndRescue", "ShipTargeted", "MarketSell"):
                continue
            gap = self._gap(group.action, event)
            window = self._cause_window(group)
            if (gap is not None and 0 <= gap <= window
                    and all(group is not other for other in result)):
                result.append(group)
        return result

    def _delivery_context(self, group, event, system, station, power):
        gap = self._gap(group.last_delivery_event or group.action, event)
        return (not group.delivery_blocked and gap is not None and gap >= 0
                and local_event_day(group.action.get("timestamp")) == local_event_day(event.get("timestamp"))
                and group.power == power and group.system == system and group.station == station
                and all(isinstance(v, str) and v.strip() for v in (power, system, station)))

    def apply(self, event, *, system="", station="", power=""):
        previous = self.pending or self.active
        kind = event.get("event")
        causes = self._delivery_causes(previous, event)
        if previous and previous.action.get("event") == "PowerplayDeliver":
            valid_context = self._delivery_context(previous, event, system, station, power)
            if not valid_context:
                previous.delivery_blocked = True
            if (kind == "ShipLocker" and valid_context and not previous.locker_seen
                    and not previous.credits and any(previous is g for g in causes)):
                previous.locker_seen = True
                previous.last_delivery_event = dict(event)
                return
        self._apply(event, system=system, station=station, power=power)
        current = self.pending or self.active
        if kind == "DeliverPowerMicroResources" and causes:
            # Still a barrier to matching. Retain ONLY ambiguity evidence for
            # the next Deliver, including earlier deliveries already credited.
            current = ChronicleGroup(dict(event), "unknown", system, station, power)
            self.active = current
        if current is not None:
            current.delivery_competitors = [g for g in causes if g is not current]
            if kind == "PowerplayDeliver":
                current.delivery_blocked = (not event.get("Count")
                                            or not self._delivery_context(current, event, system, station, power))
                if previous is not None:
                    gap = self._gap(previous.last_delivery_event or previous.action, event)
                    if gap is None or gap < 0:
                        current.delivery_blocked = True
            current.last_delivery_event = dict(event)
            if self._sale_related(current):
                current.last_sale_event = dict(event)

    def _apply(self, event, *, system="", station="", power=""):
        from .powerplay import amount
        kind = event.get("event")
        previous = self.pending or self.active
        if kind == "MarketSell" and not is_rare_sale(event) and previous is not None:
            gap = self._gap(previous.last_sale_event or previous.last_delivery_event or previous.action, event)
            if gap is None or gap < 0:
                self.pending = self.active = None
                self.ambiguous = False
                return
        if self._sale_related(previous):
            gap = self._gap(previous.last_sale_event or previous.action, event)
            if (gap is None or gap < 0 or (previous.system, previous.station, previous.power)
                    != (system, station, power)):
                self.pending = self.active = None
                self.ambiguous = False
                previous = None
        # A cargo snapshot reports inventory, not another PP2 action. Retain a
        # sale candidate only; other activity types keep their existing rules.
        if kind == "Cargo" and self._sale_related(previous):
            return
        if kind == "MarketSell":
            competitors = self._sale_competitors(self.pending or self.active, event)
            # Rare sales remain visible on their own. Ordinary sales enter the
            # PP2 display only when a single credit can be plausibly linked.
            self.pending = self.active = None
            self.ambiguous = False
            if is_market_sale(event):
                rare = is_rare_sale(event)
                group = ChronicleGroup(dict(event), "explicit" if rare else "temporal", system, station, power,
                                       competitors=competitors)
                if rare:
                    self.groups.append(group)
                if all(isinstance(v, str) and v.strip() for v in (power, system, station)):
                    if rare:
                        self.active = group
                    else:
                        self.pending = group
            return
        if kind in ("Music", "Friends", "ReceiveText"):
            return
        # Target loss is part of the observed Bounty sequence, not another scan.
        if (kind == "ShipTargeted" and event.get("TargetLocked") is False
                and self.pending and self.pending.action["event"] == "Bounty"):
            return
        explicit = kind in ("PowerplayCollect", "PowerplayDeliver")
        candidate = kind in ("Bounty", "SearchAndRescue") or (
            kind == "ShipTargeted" and event.get("TargetLocked") is True
            and type(event.get("ScanStage")) is int and event["ScanStage"] == 3)
        if explicit or candidate:
            competitors = self._sale_competitors(self.pending or self.active, event)
            previous = self.pending or (self.active if self.active and not self.active.credits else None)
            gap = self._gap(previous.action, event) if previous else None
            self.ambiguous = bool(previous and gap is not None
                                  and 0 <= gap <= self._window(previous))
            self.pending = self.active = None
            if explicit and (not isinstance(event.get("Power"), str) or not event["Power"].strip()
                             or not isinstance(event.get("Type"), str) or not event["Type"].strip()
                             or amount(event.get("Count")) is None):
                return
            group = ChronicleGroup(dict(event), "explicit" if explicit else "temporal",
                                   system, station, event.get("Power", power), competitors=competitors)
            if explicit:
                self.ambiguous = False
                self._append(group)
            else:
                self.pending = group
            return
        if kind != "PowerplayMerits":
            # Unknown events, movements and other actions are
            # barriers. Do not grow a permissive list of ignored gameplay events.
            self.pending = self.active = None
            self.ambiguous = False
            return
        if (amount(event.get("MeritsGained")) is None
                or not isinstance(event.get("Power"), str) or not event["Power"].strip()):
            self.pending = self.active = None
            return
        group = self.pending or self.active
        matched = False
        if group and not self.ambiguous and group.power in ("", event["Power"]):
            gap = self._gap(group.action, event)
            action = group.action.get("event")
            if gap is not None:
                if action == "PowerplayDeliver":
                    matched = (0 <= gap <= 3
                               and self._delivery_context(group, event, system, station, power)
                               and len(self._delivery_causes(group, event)) == 1)
                elif action == "MarketSell":
                    matched = (0 <= gap <= 2 and group.power == power == event["Power"]
                               and (is_rare_sale(group.action) or
                                    (not group.credits and event["MeritsGained"] > 0))
                               and group.system == system and group.station == station
                               and all(isinstance(v, str) and v.strip()
                                       for v in (power, system, station)))
                elif action in ("Bounty", "SearchAndRescue", "ShipTargeted"):
                    matched = 0 <= gap <= self._window(group)
                    if action == "ShipTargeted":
                        matched = matched and event["MeritsGained"] == 10 and not group.credits
                elif group.certainty == "unknown" and group.credits:
                    last_gap = self._gap(group.credits[-1], event)
                    matched = 0 <= gap <= 10 and last_gap is not None and 0 <= last_gap <= 3
        if group and group.certainty != "unknown" and group.competitors:
            if group.action.get("event") == "MarketSell" and not is_rare_sale(group.action):
                # Evaluate alternatives at the credit's time, not the later
                # sale's time. An already credited action can still compete;
                # a credit is not proof that a cause has been consumed.
                matched = matched and not any(
                    (gap := self._gap(other.action, event)) is not None
                    and 0 <= gap <= self._cause_window(other) for other in group.competitors)
            else:
                matched = False
        if matched:
            if self.pending is not None:
                self._append(group)
            group.power = event["Power"]
            group.credits.append(dict(event))
            if group.action.get("event") in ("MarketSell", "PowerplayDeliver"):
                group.certainty = "temporal"
        else:
            competitors = self._sale_competitors(group, event, keep_candidates=True)
            group = ChronicleGroup(dict(event), "unknown", system, station, event["Power"],
                                   [dict(event)], competitors=competitors)
            self._append(group)
        self.pending = None
        self.ambiguous = False
