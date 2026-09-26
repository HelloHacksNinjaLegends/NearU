import pytest

from app.services.time_cost import ListingCommute, TradeoffStatus, compare_time_vs_cost


def test_tradeoff_matches_demo_story():
    # Cheap listing: 45 min each way. Closer listing: 22 min, $200 more.
    # (45 - 22) x 34 trips / 60 = 13.03 hours saved; $200 / 13.03 = $15.35/hour
    cheap = ListingCommute("cheap", monthly_total=1450, one_way_minutes=45)
    close = ListingCommute("close", monthly_total=1650, one_way_minutes=22)

    result = compare_time_vs_cost(cheap, close, commute_days=17)

    assert result.status == TradeoffStatus.TRADEOFF
    assert (result.cheaper_id, result.pricier_id) == ("cheap", "close")
    assert result.extra_monthly_cost == 200.0
    assert result.monthly_hours_saved == 13.03
    assert result.cost_per_hour_saved == 15.35


def test_argument_order_does_not_matter():
    cheap = ListingCommute("cheap", 1450, 45)
    close = ListingCommute("close", 1650, 22)
    assert compare_time_vs_cost(cheap, close) == compare_time_vs_cost(close, cheap)


def test_pricier_and_slower_is_dominated():
    good = ListingCommute("good", 1400, 20)
    bad = ListingCommute("bad", 1600, 40)

    result = compare_time_vs_cost(bad, good)

    assert result.status == TradeoffStatus.DOMINATED
    assert (result.cheaper_id, result.pricier_id) == ("good", "bad")
    assert result.cost_per_hour_saved is None


@pytest.mark.parametrize(
    "a, b, better",
    [
        (ListingCommute("x", 1500, 30), ListingCommute("y", 1500, 40), "x"),  # same cost, slower
        (ListingCommute("x", 1400, 30), ListingCommute("y", 1500, 30), "x"),  # same time, pricier
    ],
)
def test_ties_are_dominated_not_divided_by_zero(a, b, better):
    result = compare_time_vs_cost(a, b)
    assert result.status == TradeoffStatus.DOMINATED
    assert result.cheaper_id == better


def test_identical_listings_are_equivalent():
    result = compare_time_vs_cost(ListingCommute("x", 1500, 30), ListingCommute("y", 1500, 30))
    assert result.status == TradeoffStatus.EQUIVALENT


def test_no_commute_days_means_no_time_saved():
    result = compare_time_vs_cost(
        ListingCommute("cheap", 1400, 45), ListingCommute("close", 1600, 20), commute_days=0
    )
    assert result.status == TradeoffStatus.DOMINATED
    assert result.cheaper_id == "cheap"


def test_missing_data_is_unavailable():
    result = compare_time_vs_cost(ListingCommute("x", None, 30), ListingCommute("y", 1500, 20))
    assert result.status == TradeoffStatus.UNAVAILABLE


def test_rejects_negative_commute_days():
    with pytest.raises(ValueError):
        compare_time_vs_cost(ListingCommute("x", 1, 1), ListingCommute("y", 2, 2), commute_days=-1)
