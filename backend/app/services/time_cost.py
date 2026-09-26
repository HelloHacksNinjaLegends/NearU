"""Time-versus-cost trade-off between two listings.

Implements the "time versus cost" formulas from FRAMEWORK.md section 5:

    monthly_time_saved_hours = (commute_minutes_cheaper - commute_minutes_pricier)
                               x trips per month / 60
    cost_per_hour_saved = (monthly_total_pricier - monthly_total_cheaper)
                          / monthly_time_saved_hours

A listing that is no cheaper and no faster than the other is reported as
dominated instead of producing a misleading (negative or infinite) rate.
"""

from dataclasses import dataclass
from enum import Enum

from app.services.transport_cost import DEFAULT_COMMUTE_DAYS_PER_MONTH


class TradeoffStatus(str, Enum):
    TRADEOFF = "tradeoff"  # one listing is cheaper, the other is faster
    DOMINATED = "dominated"  # one listing is at least as cheap and as fast
    EQUIVALENT = "equivalent"  # same monthly cost and same commute time
    UNAVAILABLE = "unavailable"  # a monthly total or commute time is missing


@dataclass(frozen=True)
class ListingCommute:
    listing_id: str
    monthly_total: float | None
    one_way_minutes: float | None


@dataclass(frozen=True)
class TimeCostComparison:
    status: TradeoffStatus
    # For TRADEOFF: the cheaper and pricier listing. For DOMINATED: the
    # better listing and the dominated one. Otherwise None.
    cheaper_id: str | None = None
    pricier_id: str | None = None
    extra_monthly_cost: float | None = None
    monthly_hours_saved: float | None = None
    cost_per_hour_saved: float | None = None


def compare_time_vs_cost(
    a: ListingCommute,
    b: ListingCommute,
    commute_days: int = DEFAULT_COMMUTE_DAYS_PER_MONTH,
    trips_per_day: int = 2,
) -> TimeCostComparison:
    """Compare two listings on monthly cost against monthly commute hours."""
    if commute_days < 0 or trips_per_day < 0:
        raise ValueError("commute_days and trips_per_day must be non-negative")

    if None in (a.monthly_total, a.one_way_minutes, b.monthly_total, b.one_way_minutes):
        return TimeCostComparison(status=TradeoffStatus.UNAVAILABLE)

    trips = commute_days * trips_per_day
    a_hours = a.one_way_minutes * trips / 60
    b_hours = b.one_way_minutes * trips / 60
    cost_diff = round(abs(a.monthly_total - b.monthly_total), 2)
    hours_diff = round(abs(a_hours - b_hours), 2)

    if cost_diff == 0 and hours_diff == 0:
        return TimeCostComparison(status=TradeoffStatus.EQUIVALENT)

    # Order so `cheap` is the lower-cost listing (the faster one on a cost tie).
    cheap, pricey = (a, b) if (a.monthly_total, a_hours) <= (b.monthly_total, b_hours) else (b, a)
    cheap_hours, pricey_hours = (a_hours, b_hours) if cheap is a else (b_hours, a_hours)

    if cheap_hours <= pricey_hours:
        # The cheaper listing is also no slower: the other one is dominated.
        return TimeCostComparison(
            status=TradeoffStatus.DOMINATED,
            cheaper_id=cheap.listing_id,
            pricier_id=pricey.listing_id,
            extra_monthly_cost=cost_diff,
            monthly_hours_saved=0.0,
        )

    return TimeCostComparison(
        status=TradeoffStatus.TRADEOFF,
        cheaper_id=cheap.listing_id,
        pricier_id=pricey.listing_id,
        extra_monthly_cost=cost_diff,
        monthly_hours_saved=hours_diff,
        cost_per_hour_saved=round(cost_diff / hours_diff, 2),
    )
