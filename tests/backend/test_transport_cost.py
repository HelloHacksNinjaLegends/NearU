import pytest

from app.services.transport_cost import (
    CostLabel,
    TransitFares,
    monthly_car_cost,
    monthly_transit_cost,
)

FARES = TransitFares(
    single_trip={1: 2.50, 2: 3.50},
    monthly_pass={1: 100.00, 2: 140.00},
    as_of="test",
    source="test",
)


def test_transit_picks_cheaper_of_pass_and_per_trip():
    # 17 days x 2 trips x $2.50 = $85 < $100 pass
    result = monthly_transit_cost(zones=1, commute_days=17, fares=FARES)
    assert result.monthly_cost == 85.00
    assert result.label == CostLabel.ESTIMATED

    # 22 days x 2 x $2.50 = $110 > $100 pass
    result = monthly_transit_cost(zones=1, commute_days=22, fares=FARES)
    assert result.monthly_cost == 100.00


def test_transit_adds_supplement_fees():
    result = monthly_transit_cost(zones=2, commute_days=22, supplement_fees=5, fares=FARES)
    assert result.monthly_cost == 145.00


def test_upass_costs_nothing_extra():
    result = monthly_transit_cost(zones=3, has_upass=True, fares=FARES)
    assert result.monthly_cost == 0.0
    assert result.label == CostLabel.USER_PROVIDED


def test_unknown_zone_is_unavailable():
    result = monthly_transit_cost(zones=3, fares=FARES)
    assert result.monthly_cost is None
    assert result.label == CostLabel.UNAVAILABLE


def test_no_commute_days_costs_nothing():
    assert monthly_transit_cost(commute_days=0, fares=FARES).monthly_cost == 0.0
    assert monthly_car_cost(round_trip_km=20, commute_days=0).monthly_cost == 0.0


def test_car_cost_breakdown():
    # 20 km x 20 days = 400 km; 400 x 8/100 x $2 = $64 fuel; 400 x $0.10 = $40 wear
    result = monthly_car_cost(
        round_trip_km=20,
        commute_days=20,
        fuel_l_per_100km=8,
        fuel_price_per_l=2.0,
        campus_parking=50,
        tolls=0,
        wear_cost_per_km=0.10,
    )
    assert result.breakdown == {"fuel": 64.0, "campus_parking": 50, "tolls": 0, "wear": 40.0}
    assert result.monthly_cost == 154.00


@pytest.mark.parametrize("kwargs", [{"commute_days": -1}, {"supplement_fees": -5}])
def test_transit_rejects_negative_inputs(kwargs):
    with pytest.raises(ValueError):
        monthly_transit_cost(fares=FARES, **kwargs)


def test_car_rejects_negative_distance():
    with pytest.raises(ValueError):
        monthly_car_cost(round_trip_km=-3)
