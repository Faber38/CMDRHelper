"""Read-only chronicle filter values and UTC calendar-day comparisons."""
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone


@dataclass(frozen=True)
class ChronicleFilters:
    query: str = ""
    date_from: date | None = None
    date_to: date | None = None
    planetary_mining_only: bool = False
    minimum_mining: int = 0
    personally_mined_only: bool = False
    mining_commodity: str = ""

    @property
    def has_search(self):
        return bool(self.query or self.planetary_mining_only or self.minimum_mining
                    or self.personally_mined_only or self.mining_commodity)

    def visit_bounds(self):
        if self.date_from and self.date_to and self.date_from > self.date_to:
            raise ValueError("Invalid chronicle date range")
        return {
            "visited_from": self.date_from.isoformat() if self.date_from else None,
            "visited_before": (self.date_to + timedelta(days=1)).isoformat() if self.date_to else None,
        }


def visit_utc_time(value):
    """Normalize only for querying; never rewrite journal timestamps.

    Comparing normalized timestamps preserves the last microsecond of the day,
    unlike floating-point Julian dates rounded to milliseconds by SQLite.
    Legacy malformed values remain available when no period is selected.
    """
    try:
        instant = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        if instant.tzinfo is None:
            instant = instant.replace(tzinfo=timezone.utc)
        return instant.astimezone(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")
    except (TypeError, ValueError, OverflowError):
        return None


def visit_period_sql(connection, visited_from=None, visited_before=None):
    """Return optional predicates for a system_visits table aliased as v."""
    conditions, parameters = [], []
    for bound, operator in ((visited_from, ">="), (visited_before, "<")):
        if bound is not None:
            day = date.fromisoformat(bound).isoformat()
            # A date prefix sorts before all instants on that UTC day. This
            # implements midnight-inclusive / next-midnight-exclusive bounds.
            conditions.append(f"chronicle_utc_time(v.visited_at) {operator} ?")
            parameters.append(day)
    if conditions:
        connection.create_function("chronicle_utc_time", 1, visit_utc_time, deterministic=True)
    return "".join(" AND " + item for item in conditions), parameters


def matching_visit_sql(connection, commander_id, visited_from=None, visited_before=None):
    period, parameters = visit_period_sql(connection, visited_from, visited_before)
    if not period:
        return "", []
    # A non-correlated membership subquery evaluates the period per commander,
    # rather than parsing the same visits again for every candidate body.
    # Multiple visits still produce only one matching outer result.
    return (" AND s.system_address IN (SELECT v.system_address FROM system_visits v"
            " WHERE v.commander_id=?"
            + period + ")", [commander_id, *parameters])
