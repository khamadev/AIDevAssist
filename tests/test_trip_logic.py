from datetime import date

import pytest

from app.trip_logic import is_day_within_trip, trip_duration_days, trips_overlap


def test_trip_duration_days_single_day():
    d = date(2026, 1, 1)
    assert trip_duration_days(d, d) == 1


def test_trip_duration_days_multi_day():
    assert trip_duration_days(date(2026, 1, 1), date(2026, 1, 5)) == 5


def test_trip_duration_days_raises_when_end_before_start():
    with pytest.raises(ValueError):
        trip_duration_days(date(2026, 1, 5), date(2026, 1, 1))


def test_is_day_within_trip_true_for_boundary_days():
    start, end = date(2026, 1, 1), date(2026, 1, 5)
    assert is_day_within_trip(start, start, end)
    assert is_day_within_trip(end, start, end)


def test_is_day_within_trip_false_outside_range():
    start, end = date(2026, 1, 1), date(2026, 1, 5)
    assert not is_day_within_trip(date(2026, 1, 6), start, end)


def test_trips_overlap_true_when_ranges_intersect():
    assert trips_overlap(
        date(2026, 1, 1), date(2026, 1, 5), date(2026, 1, 4), date(2026, 1, 10)
    )


def test_trips_overlap_false_when_disjoint():
    assert not trips_overlap(
        date(2026, 1, 1), date(2026, 1, 5), date(2026, 1, 6), date(2026, 1, 10)
    )
