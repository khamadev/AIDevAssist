from datetime import date


def trip_duration_days(start_date: date, end_date: date) -> int:
    if end_date < start_date:
        raise ValueError("end_date must be on or after start_date")
    return (end_date - start_date).days + 1


def is_day_within_trip(day: date, start_date: date, end_date: date) -> bool:
    return start_date <= day <= end_date


def trips_overlap(
    start_a: date, end_a: date, start_b: date, end_b: date
) -> bool:
    return start_a <= end_b and start_b <= end_a
