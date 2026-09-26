"""Monthly transportation cost for a listing-to-campus commute.

Implements the transit and driving formulas from FRAMEWORK.md section 5.
Functions are pure: route inputs (fare zones, distance) come from
OpenTripPlanner results, and prices come from the assumption tables below
or from user overrides.
"""

from dataclasses import dataclass, field
from enum import Enum


class CostLabel(str, Enum):
    CONFIRMED = "confirmed"
    ESTIMATED = "estimated"
    USER_PROVIDED = "user-provided"
    UNAVAILABLE = "unavailable"


@dataclass(frozen=True)
class TransitFares:
    single_trip: dict[int, float]  # fare zones -> adult Compass stored-value fare
    monthly_pass: dict[int, float]  # fare zones -> adult monthly pass
    as_of: str
    source: str


# TODO(verify): confirm current prices on the source page before the demo.
TRANSLINK_FARES = TransitFares(
    single_trip={1: 2.60, 2: 3.75, 3: 5.10},
    monthly_pass={1: 106.75, 2: 143.25, 3: 193.00},
    as_of="2024-07-01",
    source="https://www.translink.ca/transit-fares/pricing-and-fare-zones",
)

DEFAULT_COMMUTE_DAYS_PER_MONTH = 17  # ~4 campus days a week
DEFAULT_FUEL_L_PER_100KM = 8.9  # compact car, combined cycle
DEFAULT_FUEL_PRICE_PER_L = 1.80  # Metro Vancouver regular, CAD


@dataclass(frozen=True)
class TransportCost:
    mode: str
    monthly_cost: float | None
    label: CostLabel
    breakdown: dict[str, float] = field(default_factory=dict)
    assumptions: list[str] = field(default_factory=list)


def _require_non_negative(**values: float) -> None:
    for name, value in values.items():
        if value < 0:
            raise ValueError(f"{name} must be non-negative, got {value}")


def monthly_transit_cost(
    zones: int = 1,
    commute_days: int = DEFAULT_COMMUTE_DAYS_PER_MONTH,
    trips_per_day: int = 2,
    has_upass: bool = False,
    supplement_fees: float = 0.0,
    fares: TransitFares = TRANSLINK_FARES,
) -> TransportCost:
    """min(monthly_pass, trips x single_fare) + supplement_fees.

    `zones` is the highest fare zone count on the commute. Buses are always
    1 zone; zones only apply to SkyTrain/SeaBus on weekdays before 6:30pm.
    """
    _require_non_negative(
        commute_days=commute_days, trips_per_day=trips_per_day, supplement_fees=supplement_fees
    )

    if has_upass:
        # U-Pass BC is charged through student fees whatever the address, so
        # it adds nothing to the difference between listings.
        return TransportCost(
            mode="transit",
            monthly_cost=0.0,
            label=CostLabel.USER_PROVIDED,
            assumptions=["Covered by U-Pass BC (paid through student fees)"],
        )

    if zones not in fares.single_trip or zones not in fares.monthly_pass:
        return TransportCost(
            mode="transit",
            monthly_cost=None,
            label=CostLabel.UNAVAILABLE,
            assumptions=[f"No fare data for {zones} zone(s)"],
        )

    trips = commute_days * trips_per_day
    pay_per_trip = trips * fares.single_trip[zones]
    monthly_pass = fares.monthly_pass[zones]
    fare_cost = min(pay_per_trip, monthly_pass)
    fare_type = "monthly pass" if monthly_pass <= pay_per_trip else "pay per trip"

    return TransportCost(
        mode="transit",
        monthly_cost=round(fare_cost + supplement_fees, 2),
        label=CostLabel.ESTIMATED,
        breakdown={
            "pay_per_trip": round(pay_per_trip, 2),
            "monthly_pass": monthly_pass,
            "supplement_fees": supplement_fees,
        },
        assumptions=[
            f"{trips} trips/month ({commute_days} days x {trips_per_day})",
            f"{zones}-zone fare, {fare_type} is cheaper",
            f"Fares as of {fares.as_of}",
        ],
    )


def monthly_car_cost(
    round_trip_km: float,
    commute_days: int = DEFAULT_COMMUTE_DAYS_PER_MONTH,
    fuel_l_per_100km: float = DEFAULT_FUEL_L_PER_100KM,
    fuel_price_per_l: float = DEFAULT_FUEL_PRICE_PER_L,
    campus_parking: float = 0.0,
    tolls: float = 0.0,
    wear_cost_per_km: float = 0.0,
) -> TransportCost:
    """Fuel + campus parking + tolls + optional wear, per month.

    `campus_parking` is the monthly cost of parking at campus. Parking at
    the listing belongs in the listing's own monthly total, not here.
    """
    _require_non_negative(
        round_trip_km=round_trip_km,
        commute_days=commute_days,
        fuel_l_per_100km=fuel_l_per_100km,
        fuel_price_per_l=fuel_price_per_l,
        campus_parking=campus_parking,
        tolls=tolls,
        wear_cost_per_km=wear_cost_per_km,
    )

    monthly_km = round_trip_km * commute_days
    fuel = monthly_km * fuel_l_per_100km / 100 * fuel_price_per_l
    wear = monthly_km * wear_cost_per_km

    return TransportCost(
        mode="drive",
        monthly_cost=round(fuel + campus_parking + tolls + wear, 2),
        label=CostLabel.ESTIMATED,
        breakdown={
            "fuel": round(fuel, 2),
            "campus_parking": campus_parking,
            "tolls": tolls,
            "wear": round(wear, 2),
        },
        assumptions=[
            f"{monthly_km:.1f} km/month ({round_trip_km} km x {commute_days} days)",
            f"{fuel_l_per_100km} L/100km at ${fuel_price_per_l:.2f}/L",
        ],
    )
