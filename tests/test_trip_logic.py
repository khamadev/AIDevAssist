from datetime import date

import pytest

from app.trip_logic import is_day_within_trip, trip_duration_days


def test_trip_duration_days_single_day():
    d = date(2026, 1, 1)
    assert trip_duration_days(d, d) == 1


def test_trip_duration_days_multi_day():
    assert trip_duration_days(date(2026, 1, 1), date(2026, 1, 5)) == 5


def test_trip_duration_days_raises_when_end_before_start():
    with pytest.raises(ValueError):
        trip_duration_days(date(2026, 1, 5), date(2026, 1, 1))


def test_is_day_within_trip_true_for_a_day_inside_range():
    assert is_day_within_trip(date(2026, 1, 3), date(2026, 1, 1), date(2026, 1, 5))
