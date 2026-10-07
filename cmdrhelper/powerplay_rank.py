"""Cache-derived merit bands, kept separate from explicit journal ranks.

The cumulative interpretation was verified in Elite on 2026-10-06:
rank 5 = 15,000; rank 6 = 23,000; rank 100 = 775,000;
100+ starts at 783,000. Rank 0 was also observed with 13,336 merits.
There is no journal-rank + 1 conversion and no assignment inference.
"""
from dataclasses import dataclass
from .powerplay import amount


@dataclass(frozen=True)
class RankProgress:
    confirmed: int | None
    calculated: int
    lower: int
    upper: int
    earned: int
    needed: int
    status: str

    @property
    def span(self):
        return self.upper-self.lower


def rank_progress(power, confirmed, merits, powers):
    if not power or not isinstance(powers, dict) or power not in powers:
        return None
    thresholds = getattr(powers, 'rank_thresholds', None)
    if not isinstance(thresholds, dict) or amount(merits) is None:
        return None
    keys = ('rankTwo', 'rankThree', 'rankFour', 'rankFive', 'aboveRankFive')
    values = [amount(thresholds.get(key)) for key in keys]
    if any(v is None or v == 0 for v in values):
        return None
    lower, calculated = 0, 1
    for increment in values[:4]:
        upper = lower + increment
        if merits < upper:
            break
        lower, calculated = upper, calculated+1
    else:
        # Constant-time even for very large explicit TotalMerits. No finite
        # maximum is implied by the last perk's unlockRank or by rank 100.
        steps = (merits-lower)//values[4]
        lower += steps*values[4]
        calculated += steps
        upper = lower+values[4]
    confirmed = amount(confirmed)
    if confirmed is None:
        status = 'unconfirmed'
    elif confirmed < calculated:
        status = 'pending'
    elif confirmed > calculated:
        status = 'conflict'
    elif calculated > 100:
        status = 'beyond100'
    else:
        status = 'confirmed'
    return RankProgress(confirmed, calculated, lower, upper, merits-lower, upper-merits, status)
